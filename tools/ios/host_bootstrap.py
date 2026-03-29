#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import platform
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

KEY_FILES = [
    Path("tools/ios/build_deps.py"),
    Path("tools/ios/host_bootstrap.py"),
    Path("build_files/build_environment/cmake/versions.cmake"),
    Path("build_files/build_environment/cmake/llvm.cmake"),
    Path("build_files/build_environment/cmake/ispc.cmake"),
    Path("build_files/build_environment/cmake/python.cmake"),
    Path("build_files/build_environment/cmake/python_site_packages.cmake"),
    Path("build_files/build_environment/patches/llvm.diff"),
]

STAGE_PATHS = {
    "python-llvm": [
        Path("build/ios-deps/host/CMakeCache.txt"),
        Path("build/ios-deps/host/CMakeFiles"),
        Path("build/ios-deps/host/build.ninja"),
        Path("build/ios-deps/host/cmake_install.cmake"),
        Path("build/ios-deps/host/Release/python"),
        Path("build/ios-deps/host/Release/llvm"),
        Path("build/ios-deps/host/build/python/src/external_python-stamp"),
        Path(
            "build/ios-deps/host/build/site_packages/src/external_python_site_packages-stamp"
        ),
        Path("build/ios-deps/host/build/ll/src/ll-stamp"),
    ],
}

STAGE_ASSET_PREFIX = {
    "python-llvm": "host-python-llvm-buildtree",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage host tool bootstrap bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser(
        "metadata", help="Write release/bootstrap metadata."
    )
    metadata.add_argument("--branch", required=True)
    metadata.add_argument("--stage", choices=sorted(STAGE_PATHS), required=True)
    metadata.add_argument("--output", type=Path, required=True)

    bundle = subparsers.add_parser("bundle", help="Create a bootstrap bundle tarball.")
    bundle.add_argument("--branch", required=True)
    bundle.add_argument("--stage", choices=sorted(STAGE_PATHS), required=True)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--metadata-output", type=Path, required=True)

    extract = subparsers.add_parser(
        "extract", help="Extract a bootstrap bundle tarball."
    )
    extract.add_argument("--input", type=Path, required=True)

    return parser.parse_args()


def read_command_output(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def detect_xcode_version() -> str:
    override = os.environ.get("HOST_BOOTSTRAP_XCODE_VERSION")
    if override:
        return override
    try:
        return read_command_output(["xcodebuild", "-version"]).replace("\n", " ")
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown-xcode"


def relpath(path: Path) -> str:
    return path.as_posix()


def compute_metadata(branch: str, stage: str) -> dict[str, object]:
    digester = hashlib.sha256()
    file_hashes: dict[str, str] = {}
    for relative_path in KEY_FILES:
        absolute_path = REPO_ROOT / relative_path
        file_digest = hashlib.sha256(absolute_path.read_bytes()).hexdigest()
        key = relpath(relative_path)
        file_hashes[key] = file_digest
        digester.update(key.encode("ascii"))
        digester.update(file_digest.encode("ascii"))

    machine = platform.machine()
    xcode_version = detect_xcode_version()
    digester.update(branch.encode("ascii"))
    digester.update(stage.encode("ascii"))
    digester.update(machine.encode("ascii"))
    digester.update(xcode_version.encode("utf-8"))
    short_key = digester.hexdigest()[:16]

    release_tag = f"{branch}-deps"
    asset_prefix = STAGE_ASSET_PREFIX[stage]
    asset_stem = f"{asset_prefix}-macos-{machine}"
    return {
        "asset_name": f"{asset_stem}.tar.gz",
        "branch": branch,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "key": short_key,
        "key_files": file_hashes,
        "machine": machine,
        "manifest_asset_name": f"{asset_stem}.json",
        "release_tag": release_tag,
        "repo_root": str(REPO_ROOT),
        "stage": stage,
        "xcode_version": xcode_version,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )


def existing_stage_paths(stage: str) -> list[Path]:
    paths: list[Path] = []
    for relative_path in STAGE_PATHS[stage]:
        absolute_path = REPO_ROOT / relative_path
        if absolute_path.exists():
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
    write_json(args.output, compute_metadata(args.branch, args.stage))
    return 0


def command_bundle(args: argparse.Namespace) -> int:
    metadata = compute_metadata(args.branch, args.stage)
    included_paths = existing_stage_paths(args.stage)
    if not included_paths:
        raise FileNotFoundError(f"No stage paths exist for {args.stage}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, mode="w:gz") as archive:
        for relative_path in included_paths:
            archive.add(REPO_ROOT / relative_path, arcname=relpath(relative_path))

    metadata["bundle_created_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
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
