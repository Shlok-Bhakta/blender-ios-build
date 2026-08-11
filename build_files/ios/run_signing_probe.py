#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Build and audit tiny simulator and unsigned-device iOS applications."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Sequence


CANONICAL_BULK_ROOT = Path("/Volumes/BlenderBuild/blender-ios")
SIGNING_OVERRIDES = (
    "CODE_SIGNING_ALLOWED=NO",
    "CODE_SIGNING_REQUIRED=NO",
    "CODE_SIGN_STYLE=Manual",
)


class CommandFailure(RuntimeError):
    def __init__(self, command: Sequence[str], log: Path, returncode: int):
        super().__init__(f"command failed with exit {returncode}: {shlex.join(command)}")
        self.command = list(command)
        self.log = log
        self.returncode = returncode


def run_logged(command: Sequence[str], log: Path, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    output = f"$ {shlex.join(command)}\n{result.stdout}{result.stderr}"
    log.write_text(output)
    if result.returncode != 0:
        raise CommandFailure(command, log, result.returncode)
    return output


def git_output(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def find_bundle(build_directory: Path, sdk_suffix: str) -> Path:
    matches = sorted(build_directory.glob(f"**/Release-{sdk_suffix}/SigningProbe.app"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {sdk_suffix} bundle, found {matches}")
    return matches[0]


def codesign_state(bundle: Path, log: Path) -> dict[str, object]:
    result = subprocess.run(
        ["codesign", "--display", "--verbose=4", str(bundle)],
        check=False,
        capture_output=True,
        text=True,
    )
    log.write_text(
        f"$ codesign --display --verbose=4 {shlex.quote(str(bundle))}\n"
        f"{result.stdout}{result.stderr}"
    )
    return {
        "codesign_display_exit": result.returncode,
        "code_signature_directory": (bundle / "_CodeSignature").exists(),
        "embedded_profile": (bundle / "embedded.mobileprovision").exists(),
        "description": (result.stdout + result.stderr).strip(),
    }


def build_lane(
    repository: Path,
    probe_source: Path,
    build_root: Path,
    artifact_root: Path,
    lane: str,
) -> dict[str, object]:
    if lane == "simulator":
        sysroot = "iphonesimulator"
        sdk_suffix = "iphonesimulator"
        audit_target = "ios-simulator"
        bundle_lane = "simulator"
    else:
        sysroot = "iphoneos"
        sdk_suffix = "iphoneos"
        audit_target = "ios-device"
        bundle_lane = "device-unsigned"

    lane_build = build_root / lane
    lane_build.mkdir(parents=True, exist_ok=True)
    configure_command = [
        "cmake",
        "-S",
        str(probe_source),
        "-B",
        str(lane_build),
        "-G",
        "Xcode",
        "-DCMAKE_SYSTEM_NAME=iOS",
        f"-DCMAKE_OSX_SYSROOT={sysroot}",
        "-DCMAKE_OSX_ARCHITECTURES=arm64",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=18.0",
    ]
    run_logged(configure_command, artifact_root / f"{lane}-configure.log")

    build_command = [
        "cmake",
        "--build",
        str(lane_build),
        "--config",
        "Release",
        "--target",
        "SigningProbe",
        "--",
        "-sdk",
        sysroot,
        *SIGNING_OVERRIDES,
    ]
    run_logged(build_command, artifact_root / f"{lane}-build.log")
    bundle = find_bundle(lane_build, sdk_suffix)
    executable = bundle / "SigningProbe"

    audit_script = repository / "build_files" / "ios" / "audit.py"
    bundle_command = [
        sys.executable,
        str(audit_script),
        "bundle",
        str(bundle),
        "--lane",
        bundle_lane,
    ]
    bundle_audit = json.loads(
        run_logged(bundle_command, artifact_root / f"{lane}-bundle-audit.json")
        .split("\n", 1)[1]
    )
    abi_command = [
        sys.executable,
        str(audit_script),
        "abi",
        str(executable),
        "--target",
        audit_target,
        "--arch",
        "arm64",
    ]
    abi_audit = json.loads(
        run_logged(abi_command, artifact_root / f"{lane}-abi-audit.json").split("\n", 1)[1]
    )
    signature = codesign_state(bundle, artifact_root / f"{lane}-codesign.log")
    if lane == "device" and (
        signature["code_signature_directory"] or signature["embedded_profile"]
    ):
        raise RuntimeError("device lane contains signing contamination")

    return {
        "lane": lane,
        "sysroot": sysroot,
        "bundle": str(bundle),
        "executable": str(executable),
        "build_overrides": list(SIGNING_OVERRIDES),
        "bundle_audit": bundle_audit,
        "abi_audit": abi_audit,
        "signature": signature,
    }


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--bulk-root", type=Path, default=CANONICAL_BULK_ROOT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    repository = arguments.repository.resolve()
    bulk_root = arguments.bulk_root.resolve()
    if bulk_root != CANONICAL_BULK_ROOT:
        raise SystemExit(f"bulk root must be exactly {CANONICAL_BULK_ROOT}")
    if not os.path.ismount(CANONICAL_BULK_ROOT.parent):
        raise SystemExit(f"bulk volume is not mounted: {CANONICAL_BULK_ROOT.parent}")

    baseline = git_output(repository, "rev-parse", "v5.2.0")
    donor = git_output(repository, "rev-parse", "origin/ios")
    short_sha = git_output(repository, "rev-parse", "--short=12", "HEAD")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{short_sha}-signing-probe"
    artifact_root = bulk_root / "artifacts" / run_id
    build_root = bulk_root / "build" / "signing-probe" / run_id
    artifact_root.mkdir(parents=True, exist_ok=False)
    build_root.mkdir(parents=True, exist_ok=False)

    report: dict[str, object] = {
        "schema_version": 1,
        "run_id": run_id,
        "packet": "N040",
        "baseline_sha": baseline,
        "donor_sha": donor,
        "status": "RUNNING",
        "artifact_root": str(artifact_root),
        "build_root": str(build_root),
        "lanes": [],
    }
    report_path = artifact_root / "signing-report.json"
    try:
        probe_source = repository / "build_files" / "ios" / "signing_probe"
        lanes = [
            build_lane(repository, probe_source, build_root, artifact_root, "simulator"),
            build_lane(repository, probe_source, build_root, artifact_root, "device"),
        ]
        report["lanes"] = lanes
        report["status"] = "GREEN"
    except Exception as ex:
        report["status"] = "RED"
        report["error"] = str(ex)
        if isinstance(ex, CommandFailure):
            report["failure"] = {
                "code": "SIGNING-EXPERIMENT-COMMAND",
                "command": shlex.join(ex.command),
                "returncode": ex.returncode,
                "log": str(ex.log),
            }
    finally:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(json.dumps({"status": report["status"], "report": str(report_path)}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
