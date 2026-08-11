#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Configure a content-addressed Blender dependency tree for iOS."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shlex
import subprocess
import sys
from typing import Mapping, Sequence


CANONICAL_VOLUME = Path("/Volumes/BlenderBuild")
CANONICAL_BULK = CANONICAL_VOLUME / "blender-ios"
EXPECTED_VOLUME_UUID = "EC4DA5DD-B2A4-4056-934E-5B703096BEF1"
TOOL_PATHS = (
    "/opt/homebrew/opt/bison/bin",
    "/opt/homebrew/opt/flex/bin",
    "/opt/homebrew/opt/libtool/libexec/gnubin",
    "/opt/homebrew/bin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
)


def checked_output(command: Sequence[str], cwd: Path | None = None) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(file_digest(path).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def cache_key_for_inputs(inputs: Mapping[str, str]) -> str:
    payload = json.dumps(dict(inputs), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def volume_uuid() -> str:
    result = subprocess.run(
        ["diskutil", "info", "-plist", str(CANONICAL_VOLUME)],
        check=True,
        capture_output=True,
    )
    document = plistlib.loads(result.stdout)
    return str(document.get("VolumeUUID", ""))


def build_inputs(repository: Path, target: str, deployment_target: str, profile: str) -> dict[str, str]:
    sdk = "iphonesimulator" if target == "ios-simulator" else "iphoneos"
    dependency_root = repository / "build_files" / "build_environment"
    framework_paths = list((dependency_root / "patches").glob("*ios*.diff"))
    framework_paths.extend(
        (
            dependency_root / "CMakeLists.txt",
            dependency_root / "cmake" / "options.cmake",
            dependency_root / "cmake" / "ios_platform.cmake",
            Path(__file__),
            Path(__file__).with_name("audit.py"),
        )
    )
    xcode_lines = checked_output(["xcodebuild", "-version"]).splitlines()
    return {
        "baseline_sha": checked_output(["git", "rev-parse", "v5.2.0"], repository),
        "dependency_versions_sha256": file_digest(dependency_root / "cmake" / "versions.cmake"),
        "ios_framework_sha256": tree_digest(framework_paths),
        "xcode": " / ".join(xcode_lines),
        "sdk": checked_output(["xcrun", "--sdk", sdk, "--show-sdk-version"]),
        "target": target,
        "target_triple": (
            f"arm64-apple-ios{deployment_target}-simulator"
            if target == "ios-simulator"
            else f"arm64-apple-ios{deployment_target}"
        ),
        "deployment_target": deployment_target,
        "cmake": checked_output(["cmake", "--version"]).splitlines()[0],
        "feature_profile": profile,
    }


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--bulk-root", type=Path, default=CANONICAL_BULK)
    parser.add_argument("--target", choices=("ios-simulator", "ios-device"), default="ios-simulator")
    parser.add_argument("--deployment-target", default="18.0")
    parser.add_argument("--feature-profile", default="ios_sim_minimal")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--print-plan", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    repository = arguments.repository.resolve()
    bulk_root = arguments.bulk_root.resolve()
    if bulk_root != CANONICAL_BULK:
        raise SystemExit(f"bulk root must be exactly {CANONICAL_BULK}")
    if not os.path.ismount(CANONICAL_VOLUME):
        raise SystemExit(f"bulk volume is not mounted: {CANONICAL_VOLUME}")
    actual_uuid = volume_uuid()
    if actual_uuid != EXPECTED_VOLUME_UUID:
        raise SystemExit(f"bulk volume UUID changed: {actual_uuid}")
    if arguments.threads < 1 or arguments.threads > 2:
        raise SystemExit("dependency configure permits 1 or 2 threads on this host")

    inputs = build_inputs(
        repository, arguments.target, arguments.deployment_target, arguments.feature_profile
    )
    cache_key = cache_key_for_inputs(inputs)
    target_directory = arguments.target
    build_directory = bulk_root / "deps" / "build" / target_directory / cache_key
    install_directory = bulk_root / "deps" / "install" / target_directory / cache_key
    download_directory = bulk_root / "cache" / "downloads"
    package_directory = bulk_root / "cache" / "packages"
    host_tools_directory = repository.parent / "build_blender_ios_host_tools"
    sdk = "iphonesimulator" if arguments.target == "ios-simulator" else "iphoneos"
    sdk_path = checked_output(["xcrun", "--sdk", sdk, "--show-sdk-path"])
    apple_target = "ios-simulator" if arguments.target == "ios-simulator" else "ios"
    short_sha = checked_output(["git", "rev-parse", "--short=12", "HEAD"], repository)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{short_sha}-deps-configure"
    artifact_directory = bulk_root / "artifacts" / run_id
    temporary_directory = bulk_root / "tmp" / run_id

    plan = {
        "schema_version": 1,
        "run_id": run_id,
        "packet": "N100",
        "baseline_sha": inputs["baseline_sha"],
        "donor_sha": checked_output(["git", "rev-parse", "origin/ios"], repository),
        "target": "ios-simulator-arm64" if arguments.target == "ios-simulator" else "ios-device-arm64",
        "feature_profile": arguments.feature_profile,
        "signing_mode": "SIMULATOR_LOCAL" if arguments.target == "ios-simulator" else "UNSIGNED",
        "paths": {
            "source": str(repository),
            "bulk": str(bulk_root),
            "artifact": str(artifact_directory),
        },
        "cache_key": cache_key,
        "cache_inputs": inputs,
        "build_directory": str(build_directory),
        "install_directory": str(install_directory),
        "download_directory": str(download_directory),
        "package_directory": str(package_directory),
        "host_tools_directory": str(host_tools_directory),
        "temporary_directory": str(temporary_directory),
    }
    if arguments.print_plan:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    for path in (
        build_directory,
        install_directory,
        download_directory,
        package_directory,
        artifact_directory,
        temporary_directory,
    ):
        path.mkdir(parents=True, exist_ok=True)
    request_path = artifact_directory / "request.json"
    request_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")

    command = [
        "cmake",
        "-S",
        str(repository / "build_files" / "build_environment"),
        "-B",
        str(build_directory),
        "-G",
        "Ninja",
        f"-DAPPLE_TARGET_DEVICE={apple_target}",
        "-DCMAKE_SYSTEM_NAME=iOS",
        f"-DCMAKE_OSX_SYSROOT={sdk_path}",
        "-DCMAKE_OSX_ARCHITECTURES=arm64",
        f"-DCMAKE_OSX_DEPLOYMENT_TARGET={arguments.deployment_target}",
        "-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY",
        f"-DCMAKE_DEPS_HOST_TOOLS_DIR={host_tools_directory}",
        f"-DDOWNLOAD_DIR={download_directory}",
        f"-DPACKAGE_DIR={package_directory}",
        f"-DHARVEST_TARGET={install_directory}",
        f"-DMAKE_THREADS={arguments.threads}",
    ]
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(TOOL_PATHS)
    environment["TMPDIR"] = str(temporary_directory)
    result = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
    configure_log = artifact_directory / "configure.log"
    configure_log.write_text(f"$ {shlex.join(command)}\n{result.stdout}{result.stderr}")

    report = {
        "schema_version": 1,
        "run_id": run_id,
        "packet": "N100",
        "status": "GREEN" if result.returncode == 0 else "RED",
        "cache_key": cache_key,
        "configure_command": command,
        "configure_log": str(configure_log),
        "request": str(request_path),
        "returncode": result.returncode,
    }
    result_path = artifact_directory / "result.json"
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "result": str(result_path)}, indent=2))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
