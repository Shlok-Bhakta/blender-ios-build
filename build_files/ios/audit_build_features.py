#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Reject packaged Blender executables with missing requested feature code."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


OPENSUBDIV_MARKERS = (
    b"bpy.app.opensubdiv",
    b"OpenSubdiv library information backend",
)
OPENSUBDIV_DISABLED_MARKER = b"Disabled, built without OpenSubdiv"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--require-opensubdiv", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    contents = arguments.executable.read_bytes()
    findings: list[str] = []

    if arguments.require_opensubdiv:
        for marker in OPENSUBDIV_MARKERS:
            if marker not in contents:
                findings.append(f"missing OpenSubdiv marker: {marker.decode()}")
        if OPENSUBDIV_DISABLED_MARKER in contents:
            findings.append("OpenSubdiv disabled modifier branch is present")

    if findings:
        for finding in findings:
            print(f"FEATURE-AUDIT: {finding}", file=sys.stderr)
        return 1

    print(f"Feature audit passed: {arguments.executable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
