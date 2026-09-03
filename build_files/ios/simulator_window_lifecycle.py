#!/usr/bin/env python3
"""Exercise repeated native close/return cycles in a booted iOS Simulator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import time


CLOSE_BUTTON_ID = "blender_child_window_close"
WINDOW_CYCLES = 3
MAIN_LOOP_SETTLE_TICKS = 12
WINDOW_KINDS = {
    "render": "bpy.ops.render.render('INVOKE_DEFAULT')",
    "main": "bpy.ops.wm.window_new_main()",
}


class LifecycleFailure(RuntimeError):
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


def lifecycle_source(marker: Path, window_kind: str = "render") -> str:
    open_window = WINDOW_KINDS[window_kind]
    return f"""import bpy
from pathlib import Path
marker = Path({str(marker)!r})
state = {{'stage': 0, 'single_window_ticks': 0}}
bpy.context.preferences.view.render_display_type = 'WINDOW'
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 64
bpy.context.scene.render.resolution_y = 64
bpy.context.scene.render.resolution_percentage = 100
def ios_window_lifecycle_tick():
    windows = len(bpy.context.window_manager.windows)
    if windows == 1:
        state['single_window_ticks'] += 1
    else:
        state['single_window_ticks'] = 0
    marker.write_text(
        f"stage={{state['stage']}} windows={{windows}} ticks={{state['single_window_ticks']}}"
    )
    if state['single_window_ticks'] < {MAIN_LOOP_SETTLE_TICKS}:
        return 0.5
    state['single_window_ticks'] = 0
    if state['stage'] < {WINDOW_CYCLES}:
        state['stage'] += 1
        {open_window}
        return 0.5
    marker.write_text('PASS')
    return None
bpy.app.timers.register(ios_window_lifecycle_tick, first_interval=0.5)
"""


def lifecycle_expression(marker: Path, window_kind: str = "render") -> str:
    return f"exec({lifecycle_source(marker, window_kind)!r})"


def maestro_flow(cycles: int = WINDOW_CYCLES) -> str:
    commands: list[str] = []
    for _ in range(cycles):
        commands.extend(
            [
                "- extendedWaitUntil:",
                "    visible:",
                f"      id: {CLOSE_BUTTON_ID}",
                "    timeout: 120000",
                "- tapOn:",
                f"    id: {CLOSE_BUTTON_ID}",
                "- extendedWaitUntil:",
                "    notVisible:",
                f"      id: {CLOSE_BUTTON_ID}",
                "    timeout: 30000",
            ]
        )
    return "\n".join(commands) + "\n"


def exercise_device(app: Path, bundle_id: str, udid: str, name: str, window_kind: str) -> None:
    run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)
    run("xcrun", "simctl", "install", udid, str(app))
    container = Path(
        run("xcrun", "simctl", "get_app_container", udid, bundle_id, "data").stdout.strip()
    )
    marker = container / "tmp" / f"blender-ios-{window_kind}-window-lifecycle.txt"
    marker.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="blender-ios-window-lifecycle-") as directory:
        flow = Path(directory) / "window-lifecycle.yaml"
        flow.write_text(f"appId: {bundle_id}\n---\n{maestro_flow()}")
        run(
            "xcrun",
            "simctl",
            "launch",
            "--terminate-running-process",
            udid,
            bundle_id,
            "--factory-startup",
            "--python-exit-code",
            "7",
            "--python-expr",
            lifecycle_expression(marker, window_kind),
        )
        try:
            result = run("maestro", "--device", udid, "test", str(flow), check=False)
            if result.returncode != 0:
                raise LifecycleFailure(f"{name} close cycle failed\n{result.stdout}\n{result.stderr}")

            deadline = time.monotonic() + 30.0
            while time.monotonic() < deadline:
                if marker.is_file() and marker.read_text() == "PASS":
                    print(f"[{name}] PASS: {WINDOW_CYCLES} {window_kind}-window close cycles")
                    return
                time.sleep(0.25)
            state = marker.read_text() if marker.is_file() else "marker missing"
            raise LifecycleFailure(f"{name} main window stopped after close: {state}")
        finally:
            run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path, help="Simulator Blender.app")
    parser.add_argument("--device", action="append", default=[], help="Booted simulator UDID")
    parser.add_argument(
        "--window-kind",
        action="append",
        choices=sorted(WINDOW_KINDS),
        default=[],
        help="Window lifecycle to test. By default both render and main windows are tested.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = args.app.resolve()
    info_plist = app / "Info.plist"
    if not info_plist.is_file():
        raise LifecycleFailure(f"missing app Info.plist: {info_plist}")
    with info_plist.open("rb") as handle:
        bundle_id = plistlib.load(handle)["CFBundleIdentifier"]

    known_devices = dict(booted_devices())
    selected = args.device or list(known_devices)
    if not selected:
        raise LifecycleFailure("no booted iPhone or iPad Simulator found")
    for udid in selected:
        for window_kind in args.window_kind or list(WINDOW_KINDS):
            exercise_device(app, bundle_id, udid, known_devices.get(udid, udid), window_kind)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LifecycleFailure, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1)
