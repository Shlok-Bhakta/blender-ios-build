#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2011-2022 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = ("main",)

import os
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path


def remove_if_exists(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def add_path_to_zip(archive: zipfile.ZipFile, path: Path, archive_name: str) -> None:
    path_stat = path.lstat()

    if stat.S_ISLNK(path_stat.st_mode):
        zip_info = zipfile.ZipInfo(archive_name)
        zip_info.create_system = 3
        zip_info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(zip_info, os.readlink(path), compress_type=zipfile.ZIP_STORED)
        return

    if path.is_dir():
        dir_name = archive_name.rstrip("/") + "/"
        zip_info = zipfile.ZipInfo(dir_name)
        zip_info.create_system = 3
        zip_info.external_attr = (path_stat.st_mode & 0xFFFF) << 16
        archive.writestr(zip_info, b"", compress_type=zipfile.ZIP_STORED)

        for child in sorted(path.iterdir(), key=lambda item: item.name):
            add_path_to_zip(archive, child, f"{dir_name}{child.name}")
        return

    archive.write(
        path, archive_name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
    )


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write(
            "Expected arguments: ./build_ipa.py package_name app_bundle output_dir\n"
        )
        return 1

    package_name = sys.argv[1]
    app_bundle = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])
    package_archive = output_dir / f"{package_name}.ipa"

    if not app_bundle.is_dir():
        sys.stderr.write(f"App bundle does not exist: {app_bundle}\n")
        return 1

    if app_bundle.suffix != ".app":
        sys.stderr.write(f"Expected an .app bundle, got: {app_bundle}\n")
        return 1

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        if package_archive.exists():
            package_archive.unlink()
    except Exception as ex:
        sys.stderr.write(f"Failed to prepare output directory: {ex}\n")
        return 1

    staging_dir = Path(tempfile.mkdtemp(prefix="blender-ipa-", dir=os.getcwd()))

    try:
        payload_dir = staging_dir / "Payload"
        payload_dir.mkdir()

        staged_bundle = payload_dir / app_bundle.name
        shutil.copytree(app_bundle, staged_bundle, symlinks=True)

        for relative_name in (
            "_CodeSignature",
            "embedded.mobileprovision",
            "CodeResources",
        ):
            for candidate in staged_bundle.rglob(relative_name):
                remove_if_exists(candidate)

        with zipfile.ZipFile(
            package_archive,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            add_path_to_zip(archive, payload_dir, "Payload")
    except Exception as ex:
        sys.stderr.write(f"Failed to create IPA package: {ex}\n")
        return 1
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
