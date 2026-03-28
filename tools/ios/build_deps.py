#!/usr/bin/env python3

import argparse
import json
import os
import platform
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_ENV_SOURCE = REPO_ROOT / "build_files" / "build_environment"
BUILD_ENV_CMAKELISTS = BUILD_ENV_SOURCE / "CMakeLists.txt"

MODE_CONFIG = {
    "host": {
        "apple_target_device": "macos",
        "sdk": "macosx",
        "requires_apple_target_support": False,
    },
    "ios": {
        "apple_target_device": "ios",
        "sdk": "iphoneos",
        "requires_apple_target_support": True,
    },
    "ios-simulator": {
        "apple_target_device": "ios-simulator",
        "sdk": "iphonesimulator",
        "requires_apple_target_support": True,
    },
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thin entrypoint for Blender Apple dependency configure/build runs.",
    )
    parser.add_argument("--mode", choices=sorted(MODE_CONFIG), required=True)
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=REPO_ROOT / "build" / "ios-deps" / "host",
        help="Build directory to configure into.",
    )
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=REPO_ROOT / "build" / "ios-deps" / "install" / "host",
        help="Install prefix for the dependency build.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=REPO_ROOT / "build" / "ios-deps" / "logs" / "host",
        help="Directory for configure/build logs.",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=REPO_ROOT / "build" / "ios-deps" / "host-manifest.json",
        help="Path to the generated manifest JSON.",
    )
    parser.add_argument(
        "--generator",
        default="Ninja",
        help="CMake generator for dependency configure/build.",
    )
    parser.add_argument(
        "--cmake-arg",
        action="append",
        default=[],
        help="Additional raw CMake argument to append.",
    )
    parser.add_argument(
        "--build-target",
        default="",
        help="Optional explicit build target for `cmake --build`.",
    )
    parser.add_argument(
        "--configure-only",
        action="store_true",
        help="Only run the CMake configure step.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print and record commands without executing them.",
    )
    return parser.parse_args()


def command_output(command: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "ok": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    except subprocess.CalledProcessError as exc:
        return {
            "ok": False,
            "returncode": exc.returncode,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }


def run_logged(command: list[str], log_path: Path, dry_run: bool) -> int:
    quoted = shlex.join(command)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="ascii", errors="replace") as handle:
        handle.write(f"$ {quoted}\n")
        if dry_run:
            handle.write("[dry-run]\n")
            return 0

        process = subprocess.run(
            command,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        handle.write(f"\n[exit-code] {process.returncode}\n")
        return process.returncode


def supports_apple_target_selection() -> bool:
    if not BUILD_ENV_CMAKELISTS.exists():
        return False
    return "APPLE_TARGET_DEVICE" in BUILD_ENV_CMAKELISTS.read_text(encoding="utf-8")


def normalize_paths(args: argparse.Namespace) -> None:
    mode_slug = args.mode.replace("-", "_")
    if args.build_dir == REPO_ROOT / "build" / "ios-deps" / "host":
        args.build_dir = REPO_ROOT / "build" / "ios-deps" / mode_slug
    if args.install_dir == REPO_ROOT / "build" / "ios-deps" / "install" / "host":
        args.install_dir = REPO_ROOT / "build" / "ios-deps" / "install" / mode_slug
    if args.log_dir == REPO_ROOT / "build" / "ios-deps" / "logs" / "host":
        args.log_dir = REPO_ROOT / "build" / "ios-deps" / "logs" / mode_slug
    if args.manifest_path == REPO_ROOT / "build" / "ios-deps" / "host-manifest.json":
        args.manifest_path = (
            REPO_ROOT / "build" / "ios-deps" / f"{mode_slug}-manifest.json"
        )


def collect_tool_info(mode: str) -> dict[str, object]:
    mode_config = MODE_CONFIG[mode]
    git_sha = command_output(["git", "rev-parse", "HEAD"])
    cmake_version = command_output(["cmake", "--version"])
    xcode_version = command_output(["xcodebuild", "-version"])
    sdk_version = command_output(
        ["xcrun", "--sdk", mode_config["sdk"], "--show-sdk-version"]
    )
    sdk_path = command_output(["xcrun", "--sdk", mode_config["sdk"], "--show-sdk-path"])

    return {
        "git_sha": git_sha,
        "cmake_version": cmake_version,
        "xcode_version": xcode_version,
        "sdk": {
            "name": mode_config["sdk"],
            "version": sdk_version,
            "path": sdk_path,
        },
    }


def write_manifest(manifest_path: Path, data: dict[str, object]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="ascii") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def print_inputs(args: argparse.Namespace, manifest: dict[str, object]) -> None:
    print(f"mode={args.mode}")
    print(f"source_dir={BUILD_ENV_SOURCE}")
    print(f"build_dir={args.build_dir}")
    print(f"install_dir={args.install_dir}")
    print(f"log_dir={args.log_dir}")
    print(f"manifest_path={args.manifest_path}")
    print(f"generator={args.generator}")
    print(f"dry_run={args.dry_run}")
    print(f"configure_only={args.configure_only}")
    print(f"apple_target_support={manifest['supports_apple_target_selection']}")


def main() -> int:
    args = parse_arguments()
    normalize_paths(args)

    mode_config = MODE_CONFIG[args.mode]
    manifest: dict[str, object] = {
        "mode": args.mode,
        "apple_target_device": mode_config["apple_target_device"],
        "build_dir": str(args.build_dir),
        "build_root_exists": args.build_dir.exists(),
        "cmake_args": list(args.cmake_arg),
        "configure_only": args.configure_only,
        "dry_run": args.dry_run,
        "generator": args.generator,
        "install_dir": str(args.install_dir),
        "log_dir": str(args.log_dir),
        "manifest_generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "platform": {
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "system": platform.system(),
        },
        "repo_root": str(REPO_ROOT),
        "source_dir": str(BUILD_ENV_SOURCE),
        "status": "planned",
        "supports_apple_target_selection": supports_apple_target_selection(),
        "tool_info": collect_tool_info(args.mode),
    }

    args.log_dir.mkdir(parents=True, exist_ok=True)
    args.build_dir.mkdir(parents=True, exist_ok=True)
    args.install_dir.mkdir(parents=True, exist_ok=True)

    print_inputs(args, manifest)

    if (
        mode_config["requires_apple_target_support"]
        and not manifest["supports_apple_target_selection"]
    ):
        manifest["status"] = "blocked"
        manifest["blocked_reason"] = (
            "Requested target mode before build_files/build_environment exposes APPLE_TARGET_DEVICE. "
            "Port Apple target selection first, then rerun this entrypoint."
        )
        write_manifest(args.manifest_path, manifest)
        print(manifest["blocked_reason"], file=sys.stderr)
        return 2

    if args.mode != "host" and platform.system() != "Darwin" and not args.dry_run:
        manifest["status"] = "blocked"
        manifest["blocked_reason"] = (
            "Target iOS dependency configure/build currently requires macOS."
        )
        write_manifest(args.manifest_path, manifest)
        print(manifest["blocked_reason"], file=sys.stderr)
        return 2

    configure_command = [
        "cmake",
        "-S",
        str(BUILD_ENV_SOURCE),
        "-B",
        str(args.build_dir),
        "-G",
        args.generator,
        f"-DCMAKE_INSTALL_PREFIX={args.install_dir}",
        f"-DAPPLE_TARGET_DEVICE={mode_config['apple_target_device']}",
    ]

    if args.mode == "host":
        configure_command.append("-DWITH_APPLE_CROSSPLATFORM=OFF")
    else:
        configure_command.extend(
            [
                "-DWITH_APPLE_CROSSPLATFORM=ON",
                "-DCMAKE_OSX_ARCHITECTURES=arm64",
            ]
        )

    configure_command.extend(args.cmake_arg)

    build_command = ["cmake", "--build", str(args.build_dir)]
    if args.build_target:
        build_command.extend(["--target", args.build_target])

    manifest["configure_command"] = configure_command
    manifest["build_command"] = build_command
    write_manifest(args.manifest_path, manifest)

    configure_rc = run_logged(
        configure_command, args.log_dir / "configure.log", args.dry_run
    )
    manifest["configure_returncode"] = configure_rc
    if configure_rc != 0:
        manifest["status"] = "configure_failed"
        write_manifest(args.manifest_path, manifest)
        return configure_rc

    if args.configure_only:
        manifest["status"] = "configure_only_complete"
        write_manifest(args.manifest_path, manifest)
        return 0

    build_rc = run_logged(build_command, args.log_dir / "build.log", args.dry_run)
    manifest["build_returncode"] = build_rc
    manifest["status"] = "complete" if build_rc == 0 else "build_failed"
    write_manifest(args.manifest_path, manifest)
    return build_rc


if __name__ == "__main__":
    raise SystemExit(main())
