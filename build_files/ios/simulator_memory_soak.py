#!/usr/bin/env python3
"""Exercise Blender's rendered viewport and measure simulator-process memory stability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import tempfile
import time
from typing import NamedTuple


class SoakFailure(RuntimeError):
    pass


class MemoryAnalysis(NamedTuple):
    growth_kib: int
    slope_kib_per_sample: float
    minimum_kib: int
    maximum_kib: int


class LeakScan(NamedTuple):
    count: int
    leaked_bytes: int
    root_types: tuple[str, ...]
    output: str


class LeakAnalysis(NamedTuple):
    growth_bytes: int
    root_types: tuple[str, ...]


def run(*args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True, env=env)


def booted_devices() -> list[tuple[str, str]]:
    result = run("xcrun", "simctl", "list", "devices", "booted", "--json")
    devices: list[tuple[str, str]] = []
    for runtime_devices in json.loads(result.stdout)["devices"].values():
        for device in runtime_devices:
            name = device["name"]
            if device["state"] == "Booted" and ("iPhone" in name or "iPad" in name):
                devices.append((device["udid"], name))
    return devices


def analyze_samples(
    samples: list[int], *, max_growth_kib: int, max_slope_kib: int
) -> MemoryAnalysis:
    """Check the latter half after caches have had time to warm up."""
    if len(samples) < 6:
        raise SoakFailure("memory analysis needs at least six samples")

    plateau = samples[(len(samples) - 1) // 2 :]
    growth = max(0, plateau[-1] - plateau[0])
    x_mean = (len(plateau) - 1) / 2.0
    y_mean = sum(plateau) / len(plateau)
    denominator = sum((index - x_mean) ** 2 for index in range(len(plateau)))
    slope = sum(
        (index - x_mean) * (sample - y_mean) for index, sample in enumerate(plateau)
    ) / denominator

    if growth > max_growth_kib or slope > max_slope_kib:
        raise SoakFailure(
            "sustained memory growth after warm-up: "
            f"growth={growth / 1024:.1f} MiB, slope={slope / 1024:.2f} MiB/sample"
        )
    return MemoryAnalysis(growth, slope, min(samples), max(samples))


def viewport_soak_expression(marker: Path) -> str:
    source = f"""import bpy
from mathutils import Quaternion
areas = [area for window in bpy.context.window_manager.windows for area in window.screen.areas if area.type == 'VIEW_3D']
for area in areas:
    area.spaces.active.shading.type = 'RENDERED'
state = {{'step': 0}}
def ios_memory_soak_tick():
    state['step'] += 1
    angle = state['step'] * 0.0125
    for area in areas:
        region = area.spaces.active.region_3d
        region.view_rotation = Quaternion((0.0, 0.0, 1.0), angle) @ Quaternion((1.0, 0.0, 0.0), 1.05)
        region.view_distance = 10.0 + 0.5 * ((state['step'] % 80) / 80.0)
        area.tag_redraw()
    return 0.1
bpy.app.timers.register(ios_memory_soak_tick, first_interval=0.1, persistent=True)
open({str(marker)!r}, 'w').write(str(len(areas)))
"""
    return f"exec({source!r})"


def process_rss_kib(pid: int) -> int:
    result = run("/bin/ps", "-o", "rss=", "-p", str(pid), check=False)
    value = result.stdout.strip()
    if result.returncode != 0 or not value:
        raise SoakFailure(f"Blender process {pid} exited during the memory soak")
    return int(value)


def parse_leak_report(output: str) -> LeakScan:
    matches = re.findall(r"(\d+) leaks? for (\d+) total leaked bytes", output)
    if not matches:
        raise SoakFailure("leaks output did not contain a summary")
    count, leaked_bytes = (int(value) for value in matches[-1])
    root_types = tuple(sorted(set(re.findall(r"ROOT LEAK: <([^ >]+)", output))))
    return LeakScan(count, leaked_bytes, root_types, output)


def inspect_leaks(pid: int) -> LeakScan:
    result = run("/usr/bin/leaks", "--quiet", "--nostacks", str(pid), check=False)
    output = result.stdout + result.stderr
    try:
        return parse_leak_report(output)
    except SoakFailure:
        tail = "\n".join(output.splitlines()[-20:])
        raise SoakFailure(f"leaks could not inspect Blender process {pid}\n{tail}")


def analyze_leak_scans(baseline: LeakScan, final: LeakScan) -> LeakAnalysis:
    root_types = tuple(sorted(set(baseline.root_types + final.root_types)))
    application_types = tuple(
        root_type
        for root_type in root_types
        if not root_type.startswith(("_MTL", "MTL", "Metal"))
    )
    if application_types:
        raise SoakFailure(
            "leak scan found application-owned root types: " + ", ".join(application_types)
        )

    growth_bytes = max(0, final.leaked_bytes - baseline.leaked_bytes)
    if final.count > baseline.count or growth_bytes:
        raise SoakFailure(
            "simulator Metal leak roots grew during the soak: "
            f"count {baseline.count}->{final.count}, bytes "
            f"{baseline.leaked_bytes}->{final.leaked_bytes}"
        )
    return LeakAnalysis(growth_bytes, root_types)


def launch_soak(bundle_id: str, udid: str, name: str, marker: Path) -> int:
    run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)
    marker.unlink(missing_ok=True)
    result = run(
        "xcrun",
        "simctl",
        "launch",
        "--terminate-running-process",
        "--checked-allocations",
        udid,
        bundle_id,
        "--factory-startup",
        "--python-exit-code",
        "7",
        "--python-expr",
        viewport_soak_expression(marker),
    )
    match = re.search(r":\s*(\d+)\s*$", result.stdout)
    if not match:
        raise SoakFailure(f"could not read {name} Blender PID from simctl output: {result.stdout}")
    return int(match.group(1))


def soak_device(
    app: Path,
    bundle_id: str,
    udid: str,
    name: str,
    duration: float,
    warmup: float,
    interval: float,
    max_growth_mib: float,
    max_slope_mib: float,
) -> None:
    run("xcrun", "simctl", "install", udid, str(app))
    container = Path(
        run("xcrun", "simctl", "get_app_container", udid, bundle_id, "data").stdout.strip()
    )
    marker = container / "tmp" / "blender-ios-memory-soak-ready.txt"
    pid = launch_soak(bundle_id, udid, name, marker)
    try:
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline and not marker.is_file():
            time.sleep(0.25)
        if not marker.is_file() or marker.read_text() != "1":
            raise SoakFailure(f"{name} did not activate exactly one rendered 3D viewport")

        print(f"[{name}] rendered viewport ready; warming caches for {warmup:g}s", flush=True)
        time.sleep(warmup)
        baseline_leaks = inspect_leaks(pid)
        print(
            f"[{name}] baseline leak scan: {baseline_leaks.count} allocations / "
            f"{baseline_leaks.leaked_bytes} bytes / roots={baseline_leaks.root_types or ('none',)}",
            flush=True,
        )
        samples: list[int] = []
        sample_count = max(6, int(duration / interval) + 1)
        for index in range(sample_count):
            rss = process_rss_kib(pid)
            samples.append(rss)
            print(
                f"[{name}] sample {index + 1}/{sample_count}: RSS={rss / 1024:.1f} MiB",
                flush=True,
            )
            if index + 1 != sample_count:
                time.sleep(interval)

        analysis = analyze_samples(
            samples,
            max_growth_kib=int(max_growth_mib * 1024),
            max_slope_kib=int(max_slope_mib * 1024),
        )
        final_leaks = inspect_leaks(pid)
        try:
            leak_analysis = analyze_leak_scans(baseline_leaks, final_leaks)
        except SoakFailure as error:
            with tempfile.NamedTemporaryFile(
                mode="w", prefix="blender-ios-leaks-", suffix=".txt", delete=False
            ) as report:
                report.write("BASELINE\n")
                report.write(baseline_leaks.output)
                report.write("\nFINAL\n")
                report.write(final_leaks.output)
            raise SoakFailure(f"{name} leak scan failed: {error}; report: {report.name}")
        print(
            f"[{name}] PASS: RSS range {analysis.minimum_kib / 1024:.1f}-"
            f"{analysis.maximum_kib / 1024:.1f} MiB; plateau growth "
            f"{analysis.growth_kib / 1024:.1f} MiB; application leak roots=0; "
            f"stable simulator Metal roots={final_leaks.leaked_bytes} bytes; "
            f"leak growth={leak_analysis.growth_bytes} bytes",
            flush=True,
        )
    finally:
        run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path, help="Simulator Blender.app")
    parser.add_argument("--device", action="append", default=[], help="Booted simulator UDID")
    parser.add_argument("--duration", type=float, default=300.0, help="Sampling duration in seconds")
    parser.add_argument("--warmup", type=float, default=60.0, help="Cache warm-up in seconds")
    parser.add_argument("--interval", type=float, default=15.0, help="Seconds between RSS samples")
    parser.add_argument("--max-growth-mib", type=float, default=64.0)
    parser.add_argument("--max-slope-mib", type=float, default=4.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = args.app.resolve()
    info_plist = app / "Info.plist"
    if not info_plist.is_file():
        raise SoakFailure(f"missing app Info.plist: {info_plist}")
    with info_plist.open("rb") as handle:
        bundle_id = plistlib.load(handle)["CFBundleIdentifier"]

    known_devices = dict(booted_devices())
    selected = args.device or list(known_devices)
    if not selected:
        raise SoakFailure("no booted iPhone or iPad Simulator found")
    for udid in selected:
        soak_device(
            app,
            bundle_id,
            udid,
            known_devices.get(udid, udid),
            args.duration,
            args.warmup,
            args.interval,
            args.max_growth_mib,
            args.max_slope_mib,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SoakFailure, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
