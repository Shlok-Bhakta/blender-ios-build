#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

COMMON_KEY_FILES = [
    Path("tools/ios/build_deps.py"),
    Path("tools/ios/dep_bootstrap.py"),
    Path("tools/ios/run_release_cached_dep.sh"),
    Path("build_files/build_environment/CMakeLists.txt"),
    Path("build_files/build_environment/cmake/options.cmake"),
    Path("build_files/build_environment/cmake/platform/ios/apple_target_device.cmake"),
    Path("build_files/build_environment/cmake/platform/ios/options_ios.cmake"),
    Path("build_files/build_environment/cmake/platform/ios/options_apple_ios.cmake"),
    Path("build_files/cmake/platform/platform_apple_xcode.cmake"),
    Path("build_files/cmake/platform/ios/platform_apple_xcode_ios.cmake"),
]

DEP_CONFIG = {
    "zlib": {
        "build_dir": Path("build/ios-deps/ios/build/zlib"),
        "cmake_prefixes": ["ZLIB"],
        "release_dir": Path("build/ios-deps/ios/Release/zlib"),
        "key_files": [
            Path("build_files/build_environment/cmake/zlib.cmake"),
        ],
    },
    "png": {
        "build_dir": Path("build/ios-deps/ios/build/png"),
        "cmake_prefixes": ["PNG", "ZLIB"],
        "release_dir": Path("build/ios-deps/ios/Release/png"),
        "key_files": [
            Path("build_files/build_environment/cmake/png.cmake"),
            Path("build_files/build_environment/cmake/zlib.cmake"),
        ],
    },
    "jpeg": {
        "build_dir": Path("build/ios-deps/ios/build/jpeg"),
        "cmake_prefixes": ["JPEG"],
        "release_dir": Path("build/ios-deps/ios/Release/jpeg"),
        "key_files": [
            Path("build_files/build_environment/cmake/jpeg.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/cmake_policy_compat.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/jpeg_ios.cmake"),
        ],
    },
    "deflate": {
        "build_dir": Path("build/ios-deps/ios/build/deflate"),
        "cmake_prefixes": ["DEFLATE"],
        "release_dir": Path("build/ios-deps/ios/Release/deflate"),
        "key_files": [
            Path("build_files/build_environment/cmake/deflate.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/deflate_ios.cmake"),
        ],
    },
    "fmt": {
        "build_dir": Path("build/ios-deps/ios/build/fmt"),
        "cmake_prefixes": ["FMT"],
        "release_dir": Path("build/ios-deps/ios/Release/fmt"),
        "key_files": [
            Path("build_files/build_environment/cmake/fmt.cmake"),
        ],
    },
    "robinmap": {
        "build_dir": Path("build/ios-deps/ios/build/robinmap"),
        "cmake_prefixes": ["ROBINMAP"],
        "release_dir": Path("build/ios-deps/ios/Release/robinmap"),
        "key_files": [
            Path("build_files/build_environment/cmake/robinmap.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/cmake_policy_compat.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/robinmap_ios.cmake"),
        ],
    },
    "pugixml": {
        "build_dir": Path("build/ios-deps/ios/build/pugixml"),
        "cmake_prefixes": ["PUGIXML"],
        "release_dir": Path("build/ios-deps/ios/Release/pugixml"),
        "key_files": [
            Path("build_files/build_environment/cmake/pugixml.cmake"),
        ],
    },
}

VERSIONS_CMAKE = REPO_ROOT / "build_files/build_environment/cmake/versions.cmake"
SET_PATTERN = re.compile(r"^set\((?P<name>[A-Z0-9_]+)\s+(?P<value>.+?)\)$")
VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Z0-9_]+)\}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage per-dependency iOS release bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser("metadata", help="Write dependency bundle metadata.")
    metadata.add_argument("--branch", required=True)
    metadata.add_argument("--dep", choices=sorted(DEP_CONFIG), required=True)
    metadata.add_argument("--output", type=Path, required=True)

    bundle = subparsers.add_parser("bundle", help="Create a dependency bundle tarball.")
    bundle.add_argument("--branch", required=True)
    bundle.add_argument("--dep", choices=sorted(DEP_CONFIG), required=True)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--metadata-output", type=Path, required=True)

    extract = subparsers.add_parser("extract", help="Extract a dependency bundle tarball.")
    extract.add_argument("--input", type=Path, required=True)

    return parser.parse_args()


def read_command_output(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def detect_xcode_version() -> str:
    override = os.environ.get("DEP_BOOTSTRAP_XCODE_VERSION")
    if override:
        return override
    try:
        return read_command_output(["xcodebuild", "-version"]).replace("\n", " ")
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown-xcode"


def detect_sdk_version() -> str:
    override = os.environ.get("DEP_BOOTSTRAP_SDK_VERSION")
    if override:
        return override
    try:
        return read_command_output(["xcrun", "--sdk", "iphoneos", "--show-sdk-version"])
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown-sdk"


def relpath(path: Path) -> str:
    return path.as_posix()


def dep_stage_paths(dep: str) -> list[Path]:
    config = DEP_CONFIG[dep]
    return [config["build_dir"], config["release_dir"]]


def dep_key_files(dep: str) -> list[Path]:
    return COMMON_KEY_FILES + DEP_CONFIG[dep]["key_files"]


def load_versions_map() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in VERSIONS_CMAKE.read_text(encoding="utf-8").splitlines():
        match = SET_PATTERN.match(line.strip())
        if not match:
            continue
        value = match.group("value").strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        values[match.group("name")] = value
    return values


def expand_value(value: str, values: dict[str, str]) -> str:
    expanded = value
    for _ in range(8):
        updated = VAR_PATTERN.sub(lambda match: values.get(match.group("name"), match.group(0)), expanded)
        if updated == expanded:
            return expanded
        expanded = updated
    return expanded


def source_packages(dep: str, versions_map: dict[str, str]) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    for prefix in DEP_CONFIG[dep]["cmake_prefixes"]:
        hash_key = f"{prefix}_HASH"
        hash_type_key = f"{prefix}_HASH_TYPE"
        file_key = f"{prefix}_FILE"
        try:
            package_hash = versions_map[hash_key]
            package_hash_type = versions_map[hash_type_key]
            package_file = expand_value(versions_map[file_key], versions_map)
        except KeyError as exc:
            raise KeyError(f"Missing {exc.args[0]} in {VERSIONS_CMAKE}") from exc

        packages.append(
            {
                "file": package_file,
                "hash": package_hash,
                "hash_type": package_hash_type,
                "prefix": prefix,
            }
        )
    return packages


def compute_metadata(branch: str, dep: str) -> dict[str, object]:
    digester = hashlib.sha256()
    file_hashes: dict[str, str] = {}
    versions_map = load_versions_map()
    packages = source_packages(dep, versions_map)
    for relative_path in dep_key_files(dep):
        absolute_path = REPO_ROOT / relative_path
        file_digest = hashlib.sha256(absolute_path.read_bytes()).hexdigest()
        key = relpath(relative_path)
        file_hashes[key] = file_digest
        digester.update(key.encode("ascii"))
        digester.update(file_digest.encode("ascii"))

    source_identity = []
    for package in packages:
        source_identity.append(
            f"{package['prefix']}:{package['hash_type'].lower()}:{package['hash']}:{package['file']}"
        )
        digester.update(package["prefix"].encode("ascii"))
        digester.update(package["hash_type"].encode("ascii"))
        digester.update(package["hash"].encode("ascii"))
        digester.update(package["file"].encode("utf-8"))

    machine = platform.machine()
    xcode_version = detect_xcode_version()
    sdk_version = detect_sdk_version()
    digester.update(branch.encode("ascii"))
    digester.update(dep.encode("ascii"))
    digester.update(machine.encode("ascii"))
    digester.update(xcode_version.encode("utf-8"))
    digester.update(sdk_version.encode("ascii"))
    short_key = digester.hexdigest()[:16]
    primary_package = packages[0]
    source_hash_label = primary_package["hash_type"].lower()
    source_hash_value = primary_package["hash"]

    asset_stem = (
        f"ios-dep-{dep}-{source_hash_label}-{source_hash_value}-iphoneos-{machine}-{short_key}"
    )
    return {
        "asset_name": f"{asset_stem}.tar.gz",
        "branch": branch,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dep": dep,
        "key": short_key,
        "key_files": file_hashes,
        "source_file": primary_package["file"],
        "source_hash": source_hash_value,
        "source_hash_type": primary_package["hash_type"],
        "source_packages": source_identity,
        "machine": machine,
        "manifest_asset_name": f"{asset_stem}.json",
        "release_tag": f"{branch}-deps",
        "repo_root": str(REPO_ROOT),
        "sdk_version": sdk_version,
        "stage_paths": [relpath(path) for path in dep_stage_paths(dep)],
        "xcode_version": xcode_version,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="ascii")


def existing_stage_paths(dep: str) -> list[Path]:
    paths: list[Path] = []
    for relative_path in dep_stage_paths(dep):
        if (REPO_ROOT / relative_path).exists():
            paths.append(relative_path)
    return paths


def safe_members(members: Iterable[tarfile.TarInfo]) -> list[tarfile.TarInfo]:
    approved: list[tarfile.TarInfo] = []
    for member in members:
        member_path = Path(member.name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise ValueError(f"Refusing to extract unsafe path: {member.name}")
        approved.append(member)
    return approved


def command_metadata(args: argparse.Namespace) -> int:
    write_json(args.output, compute_metadata(args.branch, args.dep))
    return 0


def command_bundle(args: argparse.Namespace) -> int:
    metadata = compute_metadata(args.branch, args.dep)
    included_paths = existing_stage_paths(args.dep)
    if not included_paths:
        raise FileNotFoundError(f"No stage paths exist for dependency {args.dep}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, mode="w:gz") as archive:
        for relative_path in included_paths:
            archive.add(REPO_ROOT / relative_path, arcname=relpath(relative_path))

    metadata["bundle_created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metadata["bundle_path"] = str(args.output)
    metadata["included_paths"] = [relpath(path) for path in included_paths]
    write_json(args.metadata_output, metadata)
    return 0


def command_extract(args: argparse.Namespace) -> int:
    with tarfile.open(args.input, mode="r:gz") as archive:
        archive.extractall(REPO_ROOT, members=safe_members(archive.getmembers()))
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "metadata":
        return command_metadata(args)
    if args.command == "bundle":
        return command_bundle(args)
    if args.command == "extract":
        return command_extract(args)
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
