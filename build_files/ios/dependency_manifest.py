#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Audit one harvested dependency prefix and emit its immutable manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from build_files.ios.audit import Finding, audit_abi, audit_paths, binary_platforms


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def tool_output(command: Sequence[str]) -> str:
    return subprocess.run(
        command, check=False, capture_output=True, text=True
    ).stdout.strip()


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--cache-key", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--target", choices=("ios-simulator", "ios-device"), required=True)
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    prefix = arguments.prefix.resolve()
    findings = audit_abi(prefix, arguments.target, "arm64") + audit_paths([prefix])
    for expected in arguments.expect:
        expected_path = prefix / expected
        if not expected_path.is_file():
            findings.append(
                Finding(
                    "DEPS-HARVEST",
                    f"expected harvested file is missing: {expected}",
                    str(expected_path),
                )
            )

    files: list[dict[str, object]] = []
    for path in sorted(item for item in prefix.rglob("*") if item.is_file()):
        relative = path.relative_to(prefix).as_posix()
        file_description = tool_output(["/usr/bin/file", "-b", str(path)])
        item: dict[str, object] = {
            "path": relative,
            "size": path.stat().st_size,
            "sha256": digest(path),
            "file": file_description,
        }
        if "Mach-O" in file_description or "current ar archive" in file_description:
            item["architectures"] = tool_output(["xcrun", "lipo", "-archs", str(path)]).split()
            item["platforms"] = sorted(binary_platforms(path))
        files.append(item)

    document = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "family": arguments.family,
        "target": arguments.target,
        "cache_key": arguments.cache_key,
        "prefix": str(prefix),
        "status": "GREEN" if not findings else "RED",
        "expected_files": arguments.expect,
        "files": files,
        "findings": [
            {"code": item.code, "message": item.message, "path": item.path} for item in findings
        ],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": document["status"], "output": str(arguments.output)}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
