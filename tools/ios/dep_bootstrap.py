#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

KEY_SCHEMA_VERSION = 3

# Upstream fork expected extra ios cmake under build_environment; this repo may omit them.
# Only existing files participate in cache keys (see compute_metadata).
COMMON_KEY_FILES = [
    Path("build_files/build_environment/CMakeLists.txt"),
    Path("build_files/build_environment/cmake/options.cmake"),
]


def ios_deps_build_root() -> Path:
    """CMake build tree for Apple cross-deps (e.g. build/ios-deps/ios_simulator)."""
    return Path(
        os.environ.get("APPLE_IOS_DEPS_BUILD_ROOT", "build/ios-deps/ios_simulator")
    )


def apple_sdk_name() -> str:
    """xcrun --sdk value: iphoneos or iphonesimulator."""
    override = os.environ.get("DEP_APPLE_SDK", "").strip()
    if override:
        return override
    device = os.environ.get("APPLE_TARGET_DEVICE", "ios-simulator").strip().lower()
    if device in ("ios-simulator", "iphonesimulator"):
        return "iphonesimulator"
    if device in ("ios", "iphoneos"):
        return "iphoneos"
    return "iphonesimulator"


def apple_platform_asset_slug() -> str:
    """Human-readable slice label embedded in release asset filenames."""
    sdk = apple_sdk_name()
    if sdk == "iphonesimulator":
        return "iphonesimulator"
    return "iphoneos"


DEP_CONFIG = {
    "zlib": {
        "folder": "zlib",
        "cmake_prefixes": ["ZLIB"],
        "key_files": [
            Path("build_files/build_environment/cmake/zlib.cmake"),
        ],
    },
    "openal": {
        "folder": "openal",
        "cmake_prefixes": ["OPENAL"],
        "key_files": [
            Path("build_files/build_environment/cmake/openal.cmake"),
        ],
    },
    "blosc": {
        "folder": "blosc",
        "cmake_prefixes": ["BLOSC"],
        "key_files": [
            Path("build_files/build_environment/cmake/blosc.cmake"),
        ],
    },
    "png": {
        "folder": "png",
        "cmake_prefixes": ["PNG", "ZLIB"],
        "key_files": [
            Path("build_files/build_environment/cmake/png.cmake"),
            Path("build_files/build_environment/cmake/zlib.cmake"),
        ],
    },
    "jpeg": {
        "folder": "jpeg",
        "cmake_prefixes": ["JPEG"],
        "key_files": [
            Path("build_files/build_environment/cmake/jpeg.cmake"),
            Path(
                "build_files/build_environment/cmake/install_libjpeg_turbo_cmake.cmake"
            ),
        ],
    },
    "tiff": {
        "folder": "tiff",
        "cmake_prefixes": ["TIFF", "ZLIB", "JPEG"],
        "key_files": [
            Path("build_files/build_environment/cmake/tiff.cmake"),
        ],
    },
    "imath": {
        "folder": "imath",
        "cmake_prefixes": ["IMATH"],
        "key_files": [
            Path("build_files/build_environment/cmake/imath.cmake"),
        ],
    },
    "openjph": {
        "folder": "openjph",
        "cmake_prefixes": ["OPENJPH"],
        "key_files": [
            Path("build_files/build_environment/cmake/openjph.cmake"),
        ],
    },
    "openexr": {
        "folder": "openexr",
        "cmake_prefixes": ["OPENEXR", "IMATH"],
        "key_files": [
            Path("build_files/build_environment/cmake/openexr.cmake"),
        ],
    },
    "brotli": {
        "folder": "brotli",
        "cmake_prefixes": ["BROTLI"],
        "key_files": [
            Path("build_files/build_environment/cmake/brotli.cmake"),
        ],
    },
    "freetype": {
        "folder": "freetype",
        "cmake_prefixes": ["FREETYPE", "BROTLI", "ZLIB"],
        "key_files": [
            Path("build_files/build_environment/cmake/freetype.cmake"),
        ],
    },
    "bzip2": {
        "folder": "bzip2",
        "cmake_prefixes": ["BZIP2"],
        "key_files": [
            Path("build_files/build_environment/cmake/bzip2.cmake"),
        ],
    },
    "lzma": {
        "folder": "lzma",
        "cmake_prefixes": ["LZMA"],
        "key_files": [
            Path("build_files/build_environment/cmake/lzma.cmake"),
        ],
    },
    "deflate": {
        "folder": "deflate",
        "cmake_prefixes": ["DEFLATE"],
        "key_files": [
            Path("build_files/build_environment/cmake/deflate.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/deflate_ios.cmake"),
        ],
    },
    "fmt": {
        "folder": "fmt",
        "cmake_prefixes": ["FMT"],
        "key_files": [
            Path("build_files/build_environment/cmake/fmt.cmake"),
        ],
    },
    "robinmap": {
        "folder": "robinmap",
        "cmake_prefixes": ["ROBINMAP"],
        "key_files": [
            Path("build_files/build_environment/cmake/robinmap.cmake"),
            Path("build_files/build_environment/cmake/platform/ios/robinmap_ios.cmake"),
        ],
    },
    "pugixml": {
        "folder": "pugixml",
        "cmake_prefixes": ["PUGIXML"],
        "key_files": [
            Path("build_files/build_environment/cmake/pugixml.cmake"),
        ],
    },
    "xml2": {
        "folder": "xml2",
        "cmake_prefixes": ["XML2", "ZLIB", "LZMA"],
        "key_files": [
            Path("build_files/build_environment/cmake/xml2.cmake"),
        ],
    },
    "expat": {
        "folder": "expat",
        "cmake_prefixes": ["EXPAT"],
        "key_files": [
            Path("build_files/build_environment/cmake/expat.cmake"),
        ],
    },
    "pystring": {
        "folder": "pystring",
        "cmake_prefixes": ["PYSTRING"],
        "key_files": [
            Path("build_files/build_environment/cmake/pystring.cmake"),
        ],
    },
    "yamlcpp": {
        "folder": "yamlcpp",
        "cmake_prefixes": ["YAMLCPP"],
        "key_files": [
            Path("build_files/build_environment/cmake/yamlcpp.cmake"),
        ],
    },
    "minizipng": {
        "folder": "minizipng",
        "cmake_prefixes": ["MINIZIPNG", "ZLIB", "LZMA"],
        "key_files": [
            Path("build_files/build_environment/cmake/minizipng.cmake"),
        ],
    },
    "ffi": {
        "folder": "ffi",
        "cmake_prefixes": ["FFI"],
        "key_files": [
            Path("build_files/build_environment/cmake/ffi.cmake"),
        ],
    },
    "alembic": {
        "folder": "alembic",
        "cmake_prefixes": ["ALEMBIC", "IMATH", "OPENEXR"],
        "key_files": [
            Path("build_files/build_environment/cmake/alembic.cmake"),
        ],
    },
    "openjpeg": {
        "folder": "openjpeg",
        "cmake_prefixes": ["OPENJPEG"],
        "key_files": [
            Path("build_files/build_environment/cmake/openjpeg.cmake"),
        ],
    },
    "webp": {
        "folder": "webp",
        "cmake_prefixes": ["WEBP", "ZLIB"],
        "key_files": [
            Path("build_files/build_environment/cmake/webp.cmake"),
        ],
    },
    "flac": {
        "folder": "flac",
        "cmake_prefixes": ["FLAC", "OGG"],
        "key_files": [
            Path("build_files/build_environment/cmake/flac.cmake"),
        ],
    },
    "sndfile": {
        "folder": "sndfile",
        "cmake_prefixes": ["SNDFILE", "FLAC", "VORBIS", "OGG"],
        "key_files": [
            Path("build_files/build_environment/cmake/sndfile.cmake"),
        ],
    },
    "gmp": {
        "folder": "gmp",
        "cmake_prefixes": ["GMP"],
        "key_files": [
            Path("build_files/build_environment/cmake/gmp.cmake"),
        ],
    },
    "tbb": {
        "folder": "tbb",
        "cmake_prefixes": ["TBB"],
        "key_files": [
            Path("build_files/build_environment/cmake/tbb.cmake"),
        ],
    },
    "opensubdiv": {
        "folder": "opensubdiv",
        "cmake_prefixes": ["OPENSUBDIV", "TBB"],
        "key_files": [
            Path("build_files/build_environment/cmake/opensubdiv.cmake"),
            Path(
                "build_files/build_environment/cmake/platform/ios/opensubdiv_ios.cmake"
            ),
            Path("build_files/build_environment/cmake/tbb.cmake"),
        ],
    },
    "potrace": {
        "folder": "potrace",
        "cmake_prefixes": ["POTRACE"],
        "key_files": [
            Path("build_files/build_environment/cmake/potrace.cmake"),
            Path("build_files/build_environment/patches/cmakelists_potrace.txt"),
        ],
    },
    "sse2neon": {
        "folder": "sse2neon",
        "cmake_prefixes": ["SSE2NEON"],
        "key_files": [
            Path("build_files/build_environment/cmake/sse2neon.cmake"),
        ],
    },
    "embree": {
        "folder": "embree",
        "cmake_prefixes": ["EMBREE", "TBB"],
        "key_files": [
            Path("build_files/build_environment/cmake/embree.cmake"),
            Path("build_files/build_environment/cmake/tbb.cmake"),
            Path("build_files/build_environment/patches/embree_ios.diff"),
        ],
    },
    "fftw": {
        "folder": "fftw3",
        "cmake_prefixes": ["FFTW"],
        "key_files": [
            Path("build_files/build_environment/cmake/fftw.cmake"),
        ],
    },
    "opus": {
        "folder": "opus",
        "cmake_prefixes": ["OPUS"],
        "key_files": [
            Path("build_files/build_environment/cmake/opus.cmake"),
        ],
    },
    "vorbis": {
        "folder": "vorbis",
        "cmake_prefixes": ["VORBIS", "OGG"],
        "key_files": [
            Path("build_files/build_environment/cmake/vorbis.cmake"),
        ],
    },
    "ogg": {
        "folder": "ogg",
        "cmake_prefixes": ["OGG"],
        "key_files": [
            Path("build_files/build_environment/cmake/ogg.cmake"),
        ],
    },
    "x264": {
        "folder": "x264",
        "cmake_prefixes": ["X264"],
        "key_files": [
            Path("build_files/build_environment/cmake/x264.cmake"),
        ],
    },
    "x265": {
        "folder": "x265",
        "cmake_prefixes": ["X265"],
        "key_files": [
            Path("build_files/build_environment/cmake/x265.cmake"),
        ],
    },
    "vpx": {
        "folder": "vpx",
        "cmake_prefixes": ["VPX"],
        "key_files": [
            Path("build_files/build_environment/cmake/vpx.cmake"),
        ],
    },
    "lame": {
        "folder": "lame",
        "cmake_prefixes": ["LAME"],
        "key_files": [
            Path("build_files/build_environment/cmake/lame.cmake"),
        ],
    },
    "libheif": {
        "folder": "libheif",
        "cmake_prefixes": ["LIBHEIF"],
        "key_files": [
            Path("build_files/build_environment/cmake/libheif.cmake"),
        ],
    },
    "aom": {
        "folder": "aom",
        "cmake_prefixes": ["AOM"],
        "key_files": [
            Path("build_files/build_environment/cmake/aom.cmake"),
        ],
    },
    "ffmpeg": {
        "folder": "ffmpeg",
        "cmake_prefixes": [
            "FFMPEG",
            "OPUS",
            "VORBIS",
            "OGG",
            "X264",
            "X265",
            "VPX",
            "LAME",
            "AOM",
        ],
        "key_files": [
            Path("build_files/build_environment/cmake/ffmpeg.cmake"),
        ],
    },
    "pybind11": {
        "folder": "pybind11",
        "cmake_prefixes": ["PYBIND11"],
        "key_files": [
            Path("build_files/build_environment/cmake/pybind11.cmake"),
        ],
    },
    "nanobind": {
        "folder": "nanobind",
        "cmake_prefixes": ["NANOBIND"],
        "key_files": [
            Path("build_files/build_environment/cmake/nanobind.cmake"),
        ],
    },
    "manifold": {
        "folder": "manifold",
        "cmake_prefixes": ["MANIFOLD"],
        "key_files": [
            Path("build_files/build_environment/cmake/manifold.cmake"),
        ],
    },
    "opencolorio": {
        "folder": "opencolorio",
        "cmake_prefixes": ["OPENCOLORIO", "EXPAT", "PYSTRING", "YAMLCPP", "OPENEXR"],
        "key_files": [
            Path("build_files/build_environment/cmake/opencolorio.cmake"),
        ],
    },
    "openimageio": {
        "folder": "openimageio",
        "cmake_prefixes": [
            "OPENIMAGEIO",
            "OPENEXR",
            "OPENJPEG",
            "TIFF",
            "WEBP",
            "ZLIB",
            "FMT",
            "PYSTRING",
            "BLOSC",
            "ROBINMAP",
        ],
        "key_files": [
            Path("build_files/build_environment/cmake/openimageio.cmake"),
        ],
    },
    "openvdb": {
        "folder": "openvdb",
        "cmake_prefixes": ["OPENVDB", "TBB", "OPENEXR", "BLOSC", "ZLIB"],
        "key_files": [
            Path("build_files/build_environment/cmake/openvdb.cmake"),
        ],
    },
    "python": {
        "folder": "python",
        "cmake_prefixes": ["PYTHON"],
        "key_files": [
            Path("build_files/build_environment/cmake/python.cmake"),
        ],
    },
    "openimagedenoise": {
        "folder": "openimagedenoise",
        "cmake_prefixes": ["OIDN", "TBB", "PYTHON", "ISPC"],
        "key_files": [
            Path("build_files/build_environment/cmake/openimagedenoise.cmake"),
            Path("build_files/build_environment/cmake/tbb.cmake"),
            Path("build_files/build_environment/cmake/python.cmake"),
            Path("build_files/build_environment/cmake/ispc.cmake"),
            Path("build_files/build_environment/patches/oidn.diff"),
        ],
    },
    "cython": {
        "folder": "cython",
        "cmake_prefixes": ["CYTHON", "PYTHON"],
        "key_files": [
            Path("build_files/build_environment/cmake/cython.cmake"),
        ],
    },
    "numpy": {
        "folder": "numpy",
        "cmake_prefixes": ["NUMPY", "PYTHON"],
        "key_files": [
            Path("build_files/build_environment/cmake/numpy.cmake"),
        ],
    },
    "shaderc": {
        "folder": "shaderc",
        "cmake_prefixes": ["SHADERC"],
        "key_files": [
            Path("build_files/build_environment/cmake/shaderc.cmake"),
        ],
    },
    "spirv-reflect": {
        "folder": "spirv_reflect",
        "cmake_prefixes": ["SPIRV_REFLECT"],
        "key_files": [
            Path("build_files/build_environment/cmake/spirv-reflect.cmake"),
        ],
    },
}

VERSIONS_CMAKE = REPO_ROOT / "build_files/build_environment/cmake/versions.cmake"
SET_PATTERN = re.compile(r"^set\((?P<name>[A-Z0-9_]+)\s+(?P<value>.+?)\)$")
VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Z0-9_]+)\}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage per-dependency iOS release bundles."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser(
        "metadata", help="Write dependency bundle metadata."
    )
    metadata.add_argument("--branch", required=True)
    metadata.add_argument("--dep", choices=sorted(DEP_CONFIG), required=True)
    metadata.add_argument("--output", type=Path, required=True)

    bundle = subparsers.add_parser("bundle", help="Create a dependency bundle tarball.")
    bundle.add_argument("--branch", required=True)
    bundle.add_argument("--dep", choices=sorted(DEP_CONFIG), required=True)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--metadata-output", type=Path, required=True)

    extract = subparsers.add_parser(
        "extract", help="Extract a dependency bundle tarball."
    )
    extract.add_argument("--input", type=Path, required=True)

    matches = subparsers.add_parser(
        "matches",
        help="Check whether a cached manifest is compatible with expected metadata.",
    )
    matches.add_argument("--expected", type=Path, required=True)
    matches.add_argument("--cached", type=Path, required=True)

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
        return read_command_output(
            ["xcrun", "--sdk", apple_sdk_name(), "--show-sdk-version"]
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown-sdk"


def relpath(path: Path) -> str:
    if path.is_absolute():
        try:
            return path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix().lstrip("/")
    return path.as_posix()


def dep_stage_paths(dep: str) -> list[Path]:
    root = ios_deps_build_root()
    folder = DEP_CONFIG[dep]["folder"]
    return [root / "build" / folder, root / "Release" / folder]


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
        updated = VAR_PATTERN.sub(
            lambda match: values.get(match.group("name"), match.group(0)), expanded
        )
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
    digester.update(f"schema:{KEY_SCHEMA_VERSION}".encode("ascii"))
    for relative_path in dep_key_files(dep):
        absolute_path = REPO_ROOT / relative_path
        if not absolute_path.is_file():
            continue
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
    sdk_name = apple_sdk_name()
    platform_slug = apple_platform_asset_slug()
    sdk_version = detect_sdk_version()
    digester.update(branch.encode("ascii"))
    digester.update(dep.encode("ascii"))
    digester.update(machine.encode("ascii"))
    digester.update(xcode_version.encode("utf-8"))
    digester.update(sdk_name.encode("ascii"))
    digester.update(sdk_version.encode("ascii"))
    digester.update(relpath(ios_deps_build_root()).encode("ascii"))
    short_key = digester.hexdigest()[:16]
    primary_package = packages[0]
    source_hash_label = primary_package["hash_type"].lower()
    source_hash_value = primary_package["hash"]

    asset_stem = f"ios-dep-{dep}-{source_hash_label}-{source_hash_value}-{platform_slug}-{machine}"
    legacy_asset_stem = f"{asset_stem}-{short_key}"

    release_tag = os.environ.get("IOS_DEPS_RELEASE_TAG", f"{branch}-deps")

    return {
        "apple_sdk": sdk_name,
        "apple_target_device": os.environ.get("APPLE_TARGET_DEVICE", ""),
        "asset_name": f"{asset_stem}.tar.gz",
        "branch": branch,
        "deps_build_root": relpath(ios_deps_build_root()),
        "key_schema_version": KEY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dep": dep,
        "key": short_key,
        "key_files": file_hashes,
        "legacy_asset_name": f"{legacy_asset_stem}.tar.gz",
        "source_file": primary_package["file"],
        "source_hash": source_hash_value,
        "source_hash_type": primary_package["hash_type"],
        "source_packages": source_identity,
        "machine": machine,
        "manifest_asset_name": f"{asset_stem}.json",
        "platform_slug": platform_slug,
        "release_tag": release_tag,
        "repo_root": str(REPO_ROOT),
        "sdk_version": sdk_version,
        "stage_paths": [relpath(path) for path in dep_stage_paths(dep)],
        "xcode_version": xcode_version,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )


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
        if member.type == tarfile.SYMTYPE and member_linkpath_is_absolute(member):
            raise ValueError(
                f"Refusing to extract unsafe symlink: {member.name} -> {member.linkname}"
            )
        approved.append(member)
    return approved


def member_linkpath_is_absolute(member: tarfile.TarInfo) -> bool:
    if member.linkname:
        linkname = Path(member.linkname)
        return linkname.is_absolute() or ".." in linkname.parts
    return False


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

    metadata["bundle_created_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    metadata["bundle_path"] = str(args.output)
    metadata["included_paths"] = [relpath(path) for path in included_paths]
    write_json(args.metadata_output, metadata)
    return 0


def command_extract(args: argparse.Namespace) -> int:
    import subprocess

    result = subprocess.run(
        ["tar", "-xzf", str(args.input), "-C", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"tar extraction failed: {result.stderr}", file=sys.stderr)
        return 1
    return 0


def manifests_match(
    expected: dict[str, object], cached: dict[str, object]
) -> str | None:
    comparable_fields = (
        "apple_sdk",
        "deps_build_root",
        "machine",
        "platform_slug",
        "sdk_version",
        "source_file",
        "source_hash",
        "source_hash_type",
        "source_packages",
        "xcode_version",
    )

    for field in comparable_fields:
        if expected.get(field) != cached.get(field):
            return None

    expected_key_files = expected.get("key_files", {})
    cached_key_files = cached.get("key_files", {})
    if not isinstance(expected_key_files, dict) or not isinstance(
        cached_key_files, dict
    ):
        return None

    for path, digest in expected_key_files.items():
        if cached_key_files.get(path) != digest:
            return None

    if expected.get("key") == cached.get("key"):
        return "exact"

    return "compatible"


def command_matches(args: argparse.Namespace) -> int:
    expected = json.loads(args.expected.read_text(encoding="ascii"))
    cached = json.loads(args.cached.read_text(encoding="ascii"))
    match_type = manifests_match(expected, cached)
    if match_type is None:
        return 1
    print(match_type)
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "metadata":
        return command_metadata(args)
    if args.command == "bundle":
        return command_bundle(args)
    if args.command == "extract":
        return command_extract(args)
    if args.command == "matches":
        return command_matches(args)
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
