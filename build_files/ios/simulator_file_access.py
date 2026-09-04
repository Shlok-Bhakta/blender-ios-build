#!/usr/bin/env python3
"""Exercise the native folder-access control in a booted iOS Simulator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile


ADD_LOCATION_BUTTON_ID = "blender_file_browser_add_location"
CLOSE_BUTTON_ID = "blender_child_window_close"


class FileAccessFailure(RuntimeError):
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


def maestro_flow() -> str:
    return f"""- extendedWaitUntil:
    visible:
      id: {CLOSE_BUTTON_ID}
    timeout: 120000
- extendedWaitUntil:
    visible:
      id: {ADD_LOCATION_BUTTON_ID}
    timeout: 30000
- startRecording: blender-ios-file-access
- tapOn:
    id: {ADD_LOCATION_BUTTON_ID}
- extendedWaitUntil:
    visible: Cancel
    timeout: 30000
- takeScreenshot: blender-ios-folder-picker
- stopRecording
"""


def exercise_device(app: Path, bundle_id: str, udid: str, name: str) -> None:
    run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)
    run("xcrun", "simctl", "install", udid, str(app))

    with tempfile.TemporaryDirectory(prefix="blender-ios-file-access-") as directory:
        flow = Path(directory) / "file-access.yaml"
        flow.write_text(f"appId: {bundle_id}\n---\n{maestro_flow()}")
        run(
            "xcrun",
            "simctl",
            "launch",
            "--terminate-running-process",
            udid,
            bundle_id,
            "--factory-startup",
            "--python-expr",
            "import bpy; bpy.ops.wm.open_mainfile('INVOKE_DEFAULT')",
        )
        try:
            result = run("maestro", "--device", udid, "test", str(flow), check=False)
            if result.returncode != 0:
                raise FileAccessFailure(
                    f"{name} native folder picker failed\n{result.stdout}\n{result.stderr}"
                )
            print(f"[{name}] PASS: file browser opened the native folder picker")
        finally:
            run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path, help="Simulator Blender.app")
    parser.add_argument("--device", action="append", default=[], help="Booted simulator UDID")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = args.app.resolve()
    info_plist = app / "Info.plist"
    if not info_plist.is_file():
        raise FileAccessFailure(f"missing app Info.plist: {info_plist}")
    with info_plist.open("rb") as handle:
        bundle_id = plistlib.load(handle)["CFBundleIdentifier"]

    known_devices = dict(booted_devices())
    selected = args.device or list(known_devices)
    if not selected:
        raise FileAccessFailure("no booted iPhone or iPad Simulator found")
    for udid in selected:
        exercise_device(app, bundle_id, udid, known_devices.get(udid, udid))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileAccessFailure, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1)
