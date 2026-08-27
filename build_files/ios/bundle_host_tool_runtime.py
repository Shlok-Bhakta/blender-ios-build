# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Bundle the macOS dylibs needed by cached iOS generator tools."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path
import shutil
import subprocess


SYSTEM_LIBRARY_PREFIXES = ("/System/", "/usr/lib/")


def parse_otool_libraries(output: str) -> tuple[str, ...]:
    """Return dependency install names from ``otool -L`` output."""
    dependencies = []
    for line in output.splitlines()[1:]:
        install_name = line.strip().partition(" (")[0]
        if install_name:
            dependencies.append(install_name)
    return tuple(dependencies)


def linked_libraries(binary: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["otool", "-L", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_otool_libraries(result.stdout)


def find_library(library_root: Path, install_name: str) -> Path:
    name = Path(install_name).name
    matches = sorted(path for path in library_root.rglob(name) if path.is_file())
    if not matches:
        raise FileNotFoundError(f"cannot resolve host-tool dependency {install_name}")
    if len(matches) != 1:
        locations = ", ".join(str(path) for path in matches)
        raise RuntimeError(f"ambiguous host-tool dependency {install_name}: {locations}")
    return matches[0]


def bundle_runtime(
    tools: Iterable[Path],
    library_root: Path,
    destination: Path,
) -> tuple[Path, ...]:
    """Copy the recursive non-system dylib closure for ``tools``."""
    destination.mkdir(parents=True, exist_ok=True)
    pending = list(tools)
    processed = set()
    bundled = {}

    while pending:
        binary = pending.pop()
        binary_key = binary.resolve()
        if binary_key in processed:
            continue
        processed.add(binary_key)

        for install_name in linked_libraries(binary):
            if install_name.startswith(SYSTEM_LIBRARY_PREFIXES):
                continue

            name = Path(install_name).name
            if name in bundled:
                continue

            source = find_library(library_root, install_name)
            target = destination / name
            shutil.copy2(source, target)
            with target.open("rb") as handle:
                is_lfs_pointer = handle.read(42) == b"version https://git-lfs.github.com/spec/v1"
            if is_lfs_pointer:
                raise RuntimeError(f"unhydrated LFS host-tool dependency: {source}")
            bundled[name] = target
            pending.append(target)

    return tuple(bundled[name] for name in sorted(bundled))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("tools", nargs="+", type=Path)
    arguments = parser.parse_args()

    libraries = bundle_runtime(
        arguments.tools,
        arguments.library_root,
        arguments.destination,
    )
    for library in libraries:
        print(library)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
