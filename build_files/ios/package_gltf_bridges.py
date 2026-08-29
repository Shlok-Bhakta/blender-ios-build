#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Relocate glTF bridge dylibs into an iOS app's Frameworks directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence


BRIDGE_NAMES = (
    "libbf_intern_draco_bridge.dylib",
    "libbf_intern_meshopt_bridge.dylib",
)


def package_bridges(app_bundle: Path, addon_directory: Path) -> list[Path]:
    frameworks = app_bundle / "Frameworks"
    frameworks.mkdir(parents=True, exist_ok=True)
    relocated: list[Path] = []

    for name in BRIDGE_NAMES:
        source = addon_directory / name
        destination = frameworks / name
        if source.is_symlink():
            if source.resolve() != destination.resolve() or not destination.is_file():
                raise RuntimeError(f"invalid existing glTF bridge link: {source}")
            relocated.append(destination)
            continue
        if not source.is_file():
            continue

        destination.unlink(missing_ok=True)
        source.replace(destination)
        relative_destination = os.path.relpath(destination, start=source.parent)
        source.symlink_to(relative_destination)
        relocated.append(destination)

    return relocated


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-bundle", required=True, type=Path)
    parser.add_argument("--addon-directory", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    package_bridges(arguments.app_bundle, arguments.addon_directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
