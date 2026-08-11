#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Fail-closed environment preflight for Blender's iOS build packets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
from typing import Sequence


BULK_VOLUME = Path("/Volumes/BlenderBuild")
BULK_ROOT = BULK_VOLUME / "blender-ios"
EXPECTED_VOLUME_UUID = "EC4DA5DD-B2A4-4056-934E-5B703096BEF1"
BASELINE_SHA = "fbe6228777e7d9afefcd61a413844e790ae75db7"
DONOR_SHA = "a1de44dd54af75a4c8c4a29a5fed2a1334a87446"
MINIMUM_BULK_FREE_GIB = 100
MINIMUM_INTERNAL_FREE_GIB = 20
REQUIRED_TOOLS = ("cmake", "ninja", "xcodebuild", "xcrun", "git", "patch", "make", "perl")


def run(command: Sequence[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def add(checks: list[dict[str, object]], name: str, passed: bool, detail: object) -> None:
    checks.append({"name": name, "status": "GREEN" if passed else "RED", "detail": detail})


def free_gib(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return round(usage.free / (1024**3), 1)


def collect(repository: Path) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    mounted = os.path.ismount(BULK_VOLUME)
    add(checks, "bulk-volume-mounted", mounted, str(BULK_VOLUME))

    actual_uuid = ""
    if mounted:
        info = subprocess.run(
            ["diskutil", "info", "-plist", str(BULK_VOLUME)], capture_output=True, check=False
        )
        if info.returncode == 0:
            actual_uuid = str(plistlib.loads(info.stdout).get("VolumeUUID", ""))
    add(checks, "bulk-volume-uuid", actual_uuid == EXPECTED_VOLUME_UUID, actual_uuid)
    writable = mounted and os.access(BULK_VOLUME, os.W_OK)
    add(checks, "bulk-volume-writable", writable, str(BULK_VOLUME))
    if mounted:
        available = free_gib(BULK_VOLUME)
        add(checks, "bulk-free-space", available >= MINIMUM_BULK_FREE_GIB, f"{available} GiB")

    internal_available = free_gib(repository)
    add(
        checks,
        "internal-free-space",
        internal_available >= MINIMUM_INTERNAL_FREE_GIB,
        f"{internal_available} GiB",
    )

    for tool in REQUIRED_TOOLS:
        location = shutil.which(tool)
        add(checks, f"tool-{tool}", location is not None, location or "missing")

    sdk = run(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"])
    sdk_path = sdk.stdout.strip()
    add(checks, "simulator-sdk", sdk.returncode == 0 and Path(sdk_path).exists(), sdk_path)

    for reference, expected in (("v5.2.0", BASELINE_SHA), ("origin/ios", DONOR_SHA)):
        result = run(["git", "rev-parse", reference], repository)
        actual = result.stdout.strip()
        add(checks, f"git-{reference}", result.returncode == 0 and actual == expected, actual)

    power = run(["pmset", "-g", "batt"])
    power_detail = power.stdout.strip()
    add(checks, "ac-power", "AC Power" in power_detail, power_detail)

    status = "GREEN" if all(item["status"] == "GREEN" for item in checks) else "RED"
    return {
        "schema_version": 1,
        "packet": "N000",
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(repository),
        "bulk_root": str(BULK_ROOT),
        "checks": checks,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    report = collect(arguments.repository.resolve())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "output": str(arguments.output)}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
