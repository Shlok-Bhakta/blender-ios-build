#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Convert iOS Python extension modules into App Store-compliant frameworks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
from typing import Sequence


def framework_name(extension: Path, import_root: Path) -> str:
    """Return the fully-qualified import name encoded by an extension path."""
    relative = extension.relative_to(import_root)
    if relative.parts[0] == "lib-dynload":
        relative = Path(*relative.parts[1:])
    # Strip the ABI tag and extension suffix, for example:
    # ``foo/_bar.cpython-313-iphonesimulator.so`` -> ``foo._bar``.
    module_path = os.fspath(relative).split(".", 1)[0]
    return ".".join(Path(module_path).parts)


def framework_plist(
    executable: str, bundle_identifier: str, platform: str, minimum_os: str
) -> dict[str, object]:
    return {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleExecutable": executable,
        "CFBundleIdentifier": bundle_identifier,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundlePackageType": "FMWK",
        "CFBundleShortVersionString": "1.0",
        "CFBundleSupportedPlatforms": [platform],
        "MinimumOSVersion": minimum_os,
        "CFBundleVersion": "1",
    }


def package_extension(
    extension: Path,
    *,
    app_bundle: Path,
    import_root: Path,
    bundle_identifier: str,
    platform: str,
    minimum_os: str,
) -> Path:
    module_name = framework_name(extension, import_root)
    if not module_name or not re.fullmatch(r"[A-Za-z0-9_.-]+", module_name):
        raise ValueError(f"invalid Python extension module name: {extension}")

    frameworks = app_bundle / "Frameworks"
    framework = frameworks / f"{module_name}.framework"
    binary = framework / module_name
    marker = extension.with_suffix(".fwork")
    origin = framework / f"{module_name}.origin"

    # CMake install is deliberately repeatable. A later install copies the
    # source extension back into the import tree, so replace our prior output.
    if framework.exists():
        if not framework.is_dir():
            raise FileExistsError(f"Python framework output is not a directory: {framework}")
        shutil.rmtree(framework)
    if marker.exists():
        marker.unlink()

    framework.mkdir(parents=True)
    shutil.move(os.fspath(extension), os.fspath(binary))
    binary.chmod(binary.stat().st_mode | 0o111)
    subprocess.run(
        [
            "xcrun",
            "install_name_tool",
            "-id",
            f"@rpath/{framework.name}/{module_name}",
            str(binary),
        ],
        check=True,
    )

    relative_binary = binary.relative_to(app_bundle)
    relative_marker = marker.relative_to(app_bundle)
    marker.write_text(f"{relative_binary.as_posix()}\n", encoding="utf-8")
    origin.write_text(f"{relative_marker.as_posix()}\n", encoding="utf-8")

    identifier = f"{bundle_identifier}.{module_name}".replace("_", "-")
    with (framework / "Info.plist").open("wb") as handle:
        plistlib.dump(
            framework_plist(module_name, identifier, platform, minimum_os),
            handle,
            sort_keys=True,
        )
    return framework


def package_tree(
    *,
    app_bundle: Path,
    import_root: Path,
    bundle_identifier: str,
    platform: str,
    minimum_os: str,
) -> list[Path]:
    app_bundle = app_bundle.resolve()
    import_root = import_root.resolve()
    if not import_root.is_dir():
        raise FileNotFoundError(f"Python import root does not exist: {import_root}")
    if app_bundle not in import_root.parents:
        raise ValueError(f"Python import root must be inside the app bundle: {import_root}")

    extensions = sorted(path for path in import_root.rglob("*.so") if path.is_file())
    modules: dict[str, Path] = {}
    for extension in extensions:
        module_name = framework_name(extension, import_root)
        if previous := modules.get(module_name):
            raise ValueError(
                "duplicate Python extension module "
                f"{module_name!r}: {previous.relative_to(import_root)} and "
                f"{extension.relative_to(import_root)}"
            )
        modules[module_name] = extension

    # Remove outputs from the previous install only after the new tree passes
    # duplicate validation. The .origin sidecar identifies frameworks owned by
    # this tool, so unrelated application frameworks remain untouched.
    frameworks_root = app_bundle / "Frameworks"
    if frameworks_root.is_dir():
        for framework in frameworks_root.glob("*.framework"):
            if (framework / f"{framework.stem}.origin").is_file():
                shutil.rmtree(framework)
    for marker in import_root.rglob("*.fwork"):
        marker.unlink()

    # Wheels may contain static development libraries (NumPy installs
    # libnpymath.a and libnpyrandom.a). They cannot be imported at runtime,
    # cannot be linked on-device under iOS code-signing policy, and would put
    # Mach-O code outside the application Frameworks directory.
    for archive in import_root.rglob("*.a"):
        if archive.is_file():
            archive.unlink()

    return [
        package_extension(
            extension,
            app_bundle=app_bundle,
            import_root=import_root,
            bundle_identifier=bundle_identifier,
            platform=platform,
            minimum_os=minimum_os,
        )
        for extension in extensions
    ]


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-bundle", required=True, type=Path)
    parser.add_argument("--import-root", required=True, type=Path)
    parser.add_argument("--bundle-identifier", required=True)
    parser.add_argument("--platform", choices=("iPhoneOS", "iPhoneSimulator"), required=True)
    parser.add_argument("--minimum-os", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    frameworks = package_tree(
        app_bundle=arguments.app_bundle,
        import_root=arguments.import_root,
        bundle_identifier=arguments.bundle_identifier,
        platform=arguments.platform,
        minimum_os=arguments.minimum_os,
    )
    print(f"Packaged {len(frameworks)} Python extension frameworks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
