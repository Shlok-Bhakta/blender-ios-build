#!/usr/bin/env python3
"""Render Blender's default cube inside booted iOS Simulators.

Background mode bypasses first-run UI while retaining Blender's offscreen Metal render context.
The harness installs the real application, renders Blender's factory-startup scene with EEVEE,
waits for the authoritative ``Saved:`` message, and validates the PNG in the app container.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import selectors
import struct
import subprocess
import sys
import tempfile
import time
import zlib


OUTPUT_STEM = "blender-ios-eevee-smoke-"
OUTPUT_NAME = f"{OUTPUT_STEM}0001.png"
OUTPUT_SIZE = (1920, 1080)


class SmokeFailure(RuntimeError):
    pass


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def booted_devices() -> list[tuple[str, str]]:
    result = run("xcrun", "simctl", "list", "devices", "booted", "--json")
    devices: list[tuple[str, str]] = []
    for runtime_devices in json.loads(result.stdout)["devices"].values():
        for device in runtime_devices:
            name = device["name"]
            if device["state"] == "Booted" and ("iPhone" in name or "iPad" in name):
                devices.append((device["udid"], name))
    return devices


def png_pixels(path: Path) -> tuple[int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SmokeFailure(f"not a PNG: {path}")

    offset = 8
    compressed = bytearray()
    width = height = 0
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", payload[:10])
            if depth != 8 or color_type != 6:
                raise SmokeFailure(f"expected an 8-bit RGBA PNG, got depth={depth} type={color_type}")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break

    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    raw = zlib.decompress(compressed)
    expected_size = height * (stride + 1)
    if len(raw) != expected_size:
        raise SmokeFailure(f"unexpected PNG payload size {len(raw)} (expected {expected_size})")

    rows: list[bytearray] = []
    for y in range(height):
        row_start = y * (stride + 1)
        filter_type = raw[row_start]
        encoded = raw[row_start + 1 : row_start + 1 + stride]
        previous = rows[y - 1] if y else bytearray(stride)
        decoded = bytearray(stride)

        for x, value in enumerate(encoded):
            left = decoded[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
            up = previous[x]
            up_left = previous[x - bytes_per_pixel] if x >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
            else:
                raise SmokeFailure(f"unsupported PNG filter {filter_type}")
            decoded[x] = (value + predictor) & 0xFF
        rows.append(decoded)

    pixels = [
        bytes(row[x : x + bytes_per_pixel])
        for row in rows
        for x in range(0, stride, bytes_per_pixel)
    ]
    return width, height, pixels


def validate_render(path: Path) -> None:
    width, height, pixels = png_pixels(path)
    if (width, height) != OUTPUT_SIZE:
        raise SmokeFailure(f"unexpected render dimensions: {width}x{height}")
    if len(set(pixels)) < 8:
        raise SmokeFailure("render is blank or nearly uniform")
    if all(pixel[3] == 0 for pixel in pixels):
        raise SmokeFailure("render is fully transparent")


def validate_screenshot(path: Path) -> None:
    width, height, pixels = png_pixels(path)
    if width < 320 or height < 320:
        raise SmokeFailure(f"unexpected simulator screenshot dimensions: {width}x{height}")
    if len(set(pixels)) < 32:
        raise SmokeFailure("simulator screenshot is blank or nearly uniform")


def blender_arguments(output_prefix: Path) -> list[str]:
    return [
        "--background",
        "--factory-startup",
        "--engine",
        "BLENDER_EEVEE",
        "--render-output",
        str(output_prefix),
        "--render-format",
        "PNG",
        "--render-frame",
        "1",
    ]


def terminate_app(udid: str, bundle_id: str) -> None:
    run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)


def rendered_viewport_expression(marker: Path) -> str:
    return (
        "import bpy;"
        "bpy.context.scene.render.engine='BLENDER_EEVEE';"
        "changed=[setattr(area.spaces.active.shading,'type','RENDERED') "
        "for window in bpy.context.window_manager.windows "
        "for area in window.screen.areas if area.type=='VIEW_3D'];"
        f"open({str(marker)!r},'w').write(str(len(changed)))"
    )


def prepare_user_preferences(bundle_id: str, udid: str, name: str) -> None:
    result = run(
        "xcrun",
        "simctl",
        "launch",
        "--terminate-running-process",
        "--console-pty",
        udid,
        bundle_id,
        "--background",
        "--factory-startup",
        "--python-exit-code",
        "7",
        "--python-expr",
        "import bpy; bpy.ops.wm.save_userpref()",
    )
    output = result.stdout + result.stderr
    if "Error: script failed" in output or "Writing user preferences:" not in output:
        raise SmokeFailure(f"{name} could not prepare clean user preferences\n{output}")


def exercise_rendered_viewport(
    container: Path, bundle_id: str, udid: str, name: str, dwell: float
) -> None:
    marker = container / "tmp" / "blender-ios-rendered-viewport-ready.txt"
    marker.unlink(missing_ok=True)
    launch = run(
        "xcrun",
        "simctl",
        "launch",
        "--terminate-running-process",
        udid,
        bundle_id,
        "--python-exit-code",
        "7",
        "--python-expr",
        rendered_viewport_expression(marker),
    )

    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline and not marker.is_file():
        time.sleep(0.25)
    if not marker.is_file() or marker.read_text() != "1":
        terminate_app(udid, bundle_id)
        raise SmokeFailure(f"{name} did not activate its 3D rendered viewport\n{launch.stdout}")

    time.sleep(dwell)
    with tempfile.TemporaryDirectory(prefix="blender-ios-viewport-") as directory:
        screenshot = Path(directory) / "rendered-viewport.png"
        run("xcrun", "simctl", "io", udid, "screenshot", str(screenshot))
        validate_screenshot(screenshot)

    termination = run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)
    if termination.returncode != 0:
        raise SmokeFailure(f"{name} exited while rendered shading was active")
    print(f"[{name}] PASS: rendered viewport remained active for {dwell:g}s")


def render_on_device(
    app: Path, bundle_id: str, udid: str, name: str, timeout: float, viewport_dwell: float
) -> None:
    terminate_app(udid, bundle_id)
    run("xcrun", "simctl", "install", udid, str(app))
    container = Path(
        run("xcrun", "simctl", "get_app_container", udid, bundle_id, "data").stdout.strip()
    )
    output = container / "tmp" / OUTPUT_NAME
    output.unlink(missing_ok=True)
    output_prefix = output.with_name(OUTPUT_STEM)

    command = [
        "xcrun",
        "simctl",
        "launch",
        "--terminate-running-process",
        "--console-pty",
        udid,
        bundle_id,
        *blender_arguments(output_prefix),
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    log: list[str] = []
    saved = False

    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                remainder = process.stdout.read()
                if remainder:
                    log.append(remainder.decode("utf-8", errors="replace"))
                break
            for key, _ in selector.select(timeout=0.25):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    continue
                output_text = chunk.decode("utf-8", errors="replace").replace("\r", "")
                log.append(output_text)
                sys.stdout.write(f"[{name}] {output_text}")
                sys.stdout.flush()
                if "Saved:" in "".join(log[-4:]) and OUTPUT_NAME in "".join(log[-4:]):
                    saved = True
                    break
            if saved:
                break
    finally:
        selector.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            terminate_app(udid, bundle_id)
            process.terminate()
            process.wait(timeout=5)

    if not saved:
        detail = "".join(log[-80:])
        raise SmokeFailure(f"{name} did not finish its EEVEE render\n{detail}")
    validate_render(output)
    print(f"[{name}] PASS: {output} ({output.stat().st_size} bytes)")
    prepare_user_preferences(bundle_id, udid, name)
    exercise_rendered_viewport(container, bundle_id, udid, name, viewport_dwell)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path, help="Simulator Blender.app")
    parser.add_argument("--device", action="append", default=[], help="Booted simulator UDID")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--viewport-dwell",
        type=float,
        default=15.0,
        help="Seconds rendered viewport must remain alive",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = args.app.resolve()
    info_plist = app / "Info.plist"
    if not info_plist.is_file():
        raise SmokeFailure(f"missing app Info.plist: {info_plist}")
    with info_plist.open("rb") as handle:
        bundle_id = plistlib.load(handle)["CFBundleIdentifier"]

    known_devices = dict(booted_devices())
    selected = args.device or list(known_devices)
    if not selected:
        raise SmokeFailure("no booted iPhone or iPad Simulator found")

    for udid in selected:
        render_on_device(
            app,
            bundle_id,
            udid,
            known_devices.get(udid, udid),
            args.timeout,
            args.viewport_dwell,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SmokeFailure, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
