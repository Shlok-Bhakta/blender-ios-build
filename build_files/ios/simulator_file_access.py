#!/usr/bin/env python3
"""Select a real Files folder and verify Blender survives slow bookmark I/O.

The simulator-only library sets the picker's starting directory and optionally
holds NSURL's bookmark operation. Selection still goes through UIKit's Open
button, the production delegate, Foundation, and Blender's real System menu.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import threading
import time

ADD_LOCATION_BUTTON_ID = "blender_file_browser_add_location"
CLOSE_BUTTON_ID = "blender_child_window_close"
FIXTURE_SOURCE = Path(__file__).with_name("file_access_provider_fixture.mm")


class FileAccessFailure(RuntimeError):
    pass


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def booted_devices() -> list[tuple[str, str]]:
    devices = json.loads(run("xcrun", "simctl", "list", "devices", "booted", "--json").stdout)
    return [(d["udid"], d["name"]) for group in devices["devices"].values()
            for d in group if d["state"] == "Booted" and ("iPhone" in d["name"] or "iPad" in d["name"])]


def state_source(directory: Path, folder: Path, fixture: Path, slow: bool) -> str:
    return f'''import bpy, ctypes, json
from pathlib import Path
root = Path({str(directory)!r})
fixture = ctypes.CDLL({str(fixture)!r})
fixture.blender_test_set_picker_directory.argtypes = [ctypes.c_char_p]
fixture.blender_test_set_picker_directory({str(folder).encode()!r})
fixture.blender_test_delay_next_bookmark.argtypes = [ctypes.c_char_p]
if {slow!r}:
    fixture.blender_test_delay_next_bookmark({str(directory).encode()!r})
state = {{'ticks': 0, 'bookmarks': [], 'windows': 0}}
def file_access_tick():
    state['ticks'] += 1
    state['windows'] = len(bpy.context.window_manager.windows)
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'FILE_BROWSER':
                state['bookmarks'] = [entry.path for entry in area.spaces.active.system_bookmarks]
    temporary = root / 'state.tmp'
    temporary.write_text(json.dumps(state))
    temporary.replace(root / 'state.json')
    return 0.1
bpy.app.timers.register(file_access_tick, first_interval=0.1)
bpy.ops.wm.open_mainfile('INVOKE_DEFAULT')
'''


def maestro_flow(phone: bool = False, probe_url: str = "http://127.0.0.1:0/after-close") -> str:
    # iOS 26's remote Files view omits its controls from XCTest's accessibility
    # tree on this runtime. Only its Open button needs a coordinate fallback.
    # The fixture opens the chosen folder directly, independent of Files history.
    open_point = "94%,12%" if phone else "84%,29%"
    orientation = "LANDSCAPE_LEFT" if phone else "PORTRAIT"
    flow = f'''- setOrientation: {orientation}
- waitForAnimationToEnd
- extendedWaitUntil:
    visible:
      id: {CLOSE_BUTTON_ID}
    timeout: 120000
- extendedWaitUntil:
    visible:
      id: {ADD_LOCATION_BUTTON_ID}
    timeout: 30000
- startRecording: blender-ios-file-access
'''
    for _ in range(3):
        flow += f'''- tapOn:
    id: {ADD_LOCATION_BUTTON_ID}
- extendedWaitUntil:
    visible: Cancel
    timeout: 30000
- waitForAnimationToEnd
- takeScreenshot: blender-ios-folder-picker
- tapOn:
    point: {open_point}
- extendedWaitUntil:
    visible:
      id: {ADD_LOCATION_BUTTON_ID}
    timeout: 30000
'''
    flow += f'''- tapOn:
    id: {CLOSE_BUTTON_ID}
- extendedWaitUntil:
    notVisible:
      id: {CLOSE_BUTTON_ID}
    timeout: 30000
- assertTrue: ${{json(http.get('{probe_url}').body).ok}}
- stopRecording
'''
    return flow


def read_state(directory: Path) -> dict:
    path = directory / "state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def validate_outcome(before: dict, after: dict, folder: Path) -> None:
    if after.get("ticks", 0) < before.get("ticks", 0) + 3:
        raise FileAccessFailure(f"Blender main loop stopped: {after}")
    if after.get("windows") != 1:
        raise FileAccessFailure(f"file browser did not close: {after}")
    matches = [p for p in after.get("bookmarks", []) if Path(p) == folder]
    if len(matches) != 1:
        raise FileAccessFailure(f"selected folder must appear exactly once in System: {after}")


def wait_until(predicate, description: str, timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.1)
    raise FileAccessFailure(f"timed out waiting for {description}")


def start_liveness_server(directory: Path, folder: Path, output: Path):
    """Keep the final liveness assertion inside Maestro, before it backgrounds the app."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            try:
                before = read_state(directory)
                wait_until(lambda: read_state(directory).get("ticks", 0) >=
                           before.get("ticks", 0) + 3, "post-close ticks", 8)
                after = read_state(directory)
                validate_outcome(before, after, folder)
                (output / "result.json").write_text(json.dumps(after, indent=2))
                result = {"ok": True}
            except FileAccessFailure as error:
                result = {"ok": False, "error": str(error)}
            body = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def exercise_device(app: Path, bundle_id: str, udid: str, name: str,
                    output: Path, slow: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)
    run("xcrun", "simctl", "uninstall", udid, bundle_id, check=False)
    run("xcrun", "simctl", "install", udid, str(app))
    container = Path(run("xcrun", "simctl", "get_app_container", udid, bundle_id, "data").stdout.strip())
    groups = run("xcrun", "simctl", "get_app_container", udid, "com.apple.DocumentsApp", "groups").stdout
    storage = next(Path(line.split("\t", 1)[1]) for line in groups.splitlines()
                   if line.startswith("group.com.apple.FileProvider.LocalStorage\t"))
    folder = storage / "File Provider Storage" / "BlenderFolderRegression"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sentinel.txt").write_text("external folder regression fixture\n")
    directory = Path(tempfile.mkdtemp(prefix="file-access-", dir=container / "tmp"))
    fixture = directory / "provider.dylib"
    run("xcrun", "--sdk", "iphonesimulator", "clang++", "-std=c++17", "-dynamiclib",
        "-target", "arm64-apple-ios18.0-simulator", "-framework", "Foundation",
        "-framework", "UIKit", str(FIXTURE_SOURCE), "-o", str(fixture))
    run("codesign", "-s", "-", str(fixture))
    server = start_liveness_server(directory, folder, output)
    probe_url = f"http://127.0.0.1:{server.server_port}/after-close"
    flow = output / "file-access.yaml"
    flow.write_text(f"appId: {bundle_id}\n---\n{maestro_flow('iPhone' in name, probe_url)}")
    source = state_source(directory, folder, fixture, slow)
    (output / "probe.py").write_text(source)
    result = run("xcrun", "simctl", "launch", "--terminate-running-process",
                 f"--stdout={output / 'app-stdout.txt'}", f"--stderr={output / 'app-stderr.txt'}",
                 udid, bundle_id,
                 "--factory-startup", "--python-exit-code", "7", "--python-expr", f"exec({source!r})")
    (output / "launch.txt").write_text(result.stdout + result.stderr)
    process = None
    try:
        wait_until(lambda: read_state(directory).get("ticks", 0) > 3, "Blender startup", 120)
        before = read_state(directory)
        with (output / "maestro.txt").open("w") as log:
            process = subprocess.Popen(["maestro", "--device", udid, "test", "--test-output-dir",
                                        str(output), str(flow)], stdout=log, stderr=subprocess.STDOUT)
            if slow:
                claim = directory / "grant-claim"
                entered = directory / "provider-entered"

                def provider_started():
                    if process.poll() is not None:
                        raise FileAccessFailure(f"Maestro stopped before selection, see {output / 'maestro.txt'}")
                    return entered.exists()

                wait_until(lambda: claim.exists(),
                           "folder permission claimed during the picker callback", 240)
                claim_thread = claim.read_text()
                (output / "grant-claim.txt").write_text(claim_thread)
                if claim_thread != "main":
                    raise FileAccessFailure(
                        f"folder permission was not claimed during the picker callback: {claim_thread}")
                wait_until(provider_started, "real folder selection reaching bookmark I/O", 240)
                thread = entered.read_text()
                (output / "provider-thread.txt").write_text(thread)
                if thread == "main":
                    raise FileAccessFailure("folder selection blocked the main thread in bookmark I/O")
                ticks = read_state(directory).get("ticks", 0)
                wait_until(lambda: read_state(directory).get("ticks", 0) >= ticks + 3,
                           "fresh Blender ticks while the provider is blocked")
                (directory / "provider-release").touch()
            code = process.wait(timeout=360)
            if code:
                raise FileAccessFailure(f"Maestro failed, see {output / 'maestro.txt'}")
        # Maestro validated these ticks while Blender was still foregrounded.
        # Its runner may return to the Home Screen when the flow finishes.
        after = json.loads((output / "result.json").read_text())
        validate_outcome(before, after, folder)
        # Relaunch without granting anything: the System entry must come from the
        # saved Foundation bookmark, and startup must continue while it restores.
        run("xcrun", "simctl", "terminate", udid, bundle_id)
        (directory / "state.json").unlink()
        restored_source = state_source(directory, folder, fixture, False)
        run("xcrun", "simctl", "launch", udid, bundle_id, "--factory-startup",
            "--python-exit-code", "7", "--python-expr", f"exec({restored_source!r})")
        wait_until(lambda: any(Path(p) == folder for p in
                               read_state(directory).get("bookmarks", [])),
                   "saved folder restored after relaunch", 120)
        ticks = read_state(directory).get("ticks", 0)
        wait_until(lambda: read_state(directory).get("ticks", 0) >= ticks + 3,
                   "fresh ticks after bookmark restoration")
        (output / "restored.json").write_text(json.dumps(read_state(directory), indent=2))
        print(f"[{name}] PASS: 3 real selections, one bookmark, fresh ticks, restored after relaunch")
    except FileAccessFailure:
        pid = result.stdout.strip().rsplit(":", 1)[-1].strip()
        if pid.isdigit():
            run("sample", pid, "1", "-file", str(output / "failure-sample.txt"), check=False)
        run("xcrun", "simctl", "io", udid, "screenshot", str(output / "failure.png"), check=False)
        raise
    finally:
        server.shutdown()
        server.server_close()
        (directory / "provider-release").touch()
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=40)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
        if (directory / "state.json").exists():
            shutil.copy(directory / "state.json", output / "last-state.json")
        run("xcrun", "simctl", "terminate", udid, bundle_id, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--device", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--slow-provider", action="store_true")
    args = parser.parse_args()
    app = args.app.resolve()
    with (app / "Info.plist").open("rb") as handle:
        bundle_id = plistlib.load(handle)["CFBundleIdentifier"]
    devices = dict(booted_devices())
    selected = args.device or list(devices)
    if not selected:
        raise FileAccessFailure("no booted iPhone or iPad Simulator found")
    for udid in selected:
        exercise_device(app, bundle_id, udid, devices[udid], args.output.resolve() / udid,
                        args.slow_provider)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileAccessFailure, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}")
        raise SystemExit(1)
