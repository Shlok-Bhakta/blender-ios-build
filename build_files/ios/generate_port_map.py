#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Generate the classified v5.1.2-to-iOS donor map."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Sequence, TextIO


FIELDS = (
    "path",
    "change",
    "packet",
    "action",
    "owner_tier",
    "status",
    "test",
    "notes",
)


@dataclass(frozen=True)
class Classification:
    packet: str
    action: str
    owner: str
    test: str
    notes: str


DEPENDENCY_FAMILIES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "P111",
        (
            "brotli",
            "bzip2",
            "deflate",
            "fftw",
            "gmp",
            "lzma",
            "sqlite",
            "ssl",
            "xml2",
            "zlib",
            "libb2",
        ),
        "bootstrap compression, XML, SQLite, and crypto family",
    ),
    ("P112", ("freetype", "fribidi", "harfbuzz"), "text and font family"),
    (
        "P113",
        (
            "aom",
            "ffmpeg",
            "flac",
            "lame",
            "openal",
            "opus",
            "rubberband",
            "sndfile",
            "theora",
            "x264",
            "x265",
        ),
        "audio and media family",
    ),
    (
        "P114",
        (
            "imath",
            "opencolorio",
            "openimagedenoise",
            "openimageio",
            "png",
            "thorvg",
            "tiff",
        ),
        "color and image family",
    ),
    (
        "P115",
        (
            "alembic",
            "ceres",
            "eigen",
            "embree",
            "manifold",
            "materialx",
            "opensubdiv",
            "openvdb",
            "usd",
        ),
        "geometry and scene family",
    ),
    ("P116", ("ispc", "llvm", "osl"), "LLVM, ISPC, and OSL family"),
    ("P117", ("ffi", "nasm", "numpy", "python"), "Python and host-generator family"),
)


def classification(
    packet: str, action: str, owner: str, test: str, notes: str
) -> Classification:
    return Classification(packet, action, owner, test, notes)


def classify_dependency(path: str) -> Classification:
    name = Path(path).name.lower()
    for packet, tokens, description in DEPENDENCY_FAMILIES:
        if any(token in name for token in tokens):
            owner = "S" if packet in {"P111", "P112"} else "M"
            if packet in {"P116", "P117"}:
                owner = "F"
            return classification(
                packet,
                "adapt",
                owner,
                "T3 per-library ABI audit",
                description,
            )
    return classification(
        "P110",
        "adapt",
        "F",
        "T0 cache-key contract and T3 ABI harness",
        "generic iOS dependency framework",
    )


def classify_ghost(path: str, change: str) -> Classification:
    name = Path(path).name
    action = "rewrite" if change == "A" else "adapt"
    if "EventTouch" in name or "EventTrackpad" in name or name == "GHOST_Types.hh":
        return classification(
            "P310", action, "M", "T1 touch and pointer translator tests", "input event seam"
        )
    if "ContextIOS" in name:
        return classification(
            "P230", "rewrite", "F", "T2 context compile and T4 metal_context marker", "Metal context"
        )
    if "WindowIOS" in name or "WindowCocoa" in name or "WindowViewCocoa" in name:
        return classification(
            "P240", action, "F", "T2 window compile and T4 window_created marker", "window seam"
        )
    if (
        "SystemIOS" in name
        or "ISystem" in name
        or "SystemPathsCocoa" in name
        or "SystemHeadless" in name
    ):
        return classification(
            "P220", action, "F", "T2 system compile and T4 ghost_system marker", "GHOST system seam"
        )
    return classification(
        "P210", action, "F", "T2 GHOST backend registration compile", "platform registration"
    )


def classify(path: str, change: str) -> Classification:
    if path.startswith("build_files/build_environment/"):
        return classify_dependency(path)

    if path in {".gitattributes", ".gitignore"}:
        return classification(
            "P000", "adapt", "S", "T0 static path contract", "repository metadata"
        )
    if path == ".gitmodules":
        return classification(
            "P110", "adapt", "S", "T0 dependency source contract", "dependency source metadata"
        )
    if path in {"CMakeLists.txt", "GNUmakefile"} or path.startswith(
        "build_files/cmake/platform/"
    ):
        return classification(
            "P100", "adapt", "F", "T0 iOS configure contract", "platform configuration"
        )
    if path in {"build_files/cmake/testing.cmake", "build_files/utils/make_update.py"}:
        return classification(
            "P100", "adapt", "M", "T0 iOS configure contract", "build support"
        )

    if path.startswith("extern/draco/"):
        return classification(
            "P115", "adapt", "M", "T2 geometry dependency compile", "target compatibility"
        )
    if path.startswith("extern/quadriflow/"):
        return classification(
            "P150", "adapt", "M", "T2 reduced target link", "target compiler compatibility"
        )
    if path.startswith("intern/cycles/"):
        return classification(
            "P540", "defer", "F", "T6 named Cycles feasibility smoke", "after Workbench first pixel"
        )
    if path.startswith("intern/ghost/"):
        return classify_ghost(path, change)
    if path.startswith("intern/opensubdiv/"):
        return classification(
            "P510", "defer", "M", "T6 OpenSubdiv smoke", "after Workbench first pixel"
        )
    if path == "lib/ios_arm64":
        return classification(
            "P110",
            "drop",
            "S",
            "T0 storage path contract",
            "source-tree install link conflicts with external immutable prefixes",
        )

    if path.startswith("release/darwin/"):
        return classification(
            "P140", "drop", "S", "T3 bundle resource audit", "desktop asset churn is not required"
        )
    if path.startswith("release/ios/Blender.app/Assets/") or path in {
        "release/ios/background.tif",
        "release/ios/buildbot/background.tif",
    }:
        return classification(
            "P140", "reuse", "S", "T3 bundle resource audit", "donor bundle asset"
        )
    if path == "release/ios/entitlements.plist":
        return classification(
            "P130",
            "rewrite",
            "F",
            "T0/T3 unsigned signing contamination audit",
            "owner entitlements are excluded from unsigned staging",
        )
    if path == "release/ios/README.md":
        return classification(
            "P140", "drop", "S", "T0 documentation audit", "superseded by port handoff documentation"
        )
    if path.startswith("release/ios/"):
        return classification(
            "P200", "adapt", "F", "T3 bundle audit and T4 scene_connected marker", "UIKit app shell"
        )

    if path.startswith("scripts/modules/rna_keymap_ui.py") or path.endswith(
        "space_userpref.py"
    ):
        return classification(
            "P350", "adapt", "M", "T1 keymap and preference tests", "input preference UI"
        )
    if path.endswith("space_topbar.py"):
        return classification(
            "P420", "adapt", "M", "T5 simulator open/save smoke", "sandbox file UI"
        )
    if path.startswith("scripts/"):
        return classification(
            "P310", "adapt", "M", "T1 touch translator and keymap tests", "touch operator and keymap"
        )

    host_tool_paths = (
        "source/blender/blendthumb/CMakeLists.txt",
        "source/blender/blentranslation/msgfmt/CMakeLists.txt",
        "source/blender/datatoc/CMakeLists.txt",
        "source/blender/gpu/shader_tool/CMakeLists.txt",
        "source/blender/makesdna/intern/CMakeLists.txt",
        "source/blender/makesrna/intern/CMakeLists.txt",
    )
    if path in host_tool_paths:
        return classification(
            "P120", "adapt", "F", "T2 host-tool execution and target-output audit", "host/target split"
        )
    if path.endswith("blenkernel/intern/appdir.cc") or path.endswith(
        "blentranslation/intern/messages_apple.mm"
    ):
        return classification(
            "P400", "adapt", "M", "T4 bundled resource path smoke", "bundle resource path"
        )
    if path.endswith("blenlib/intern/storage_apple.mm") or "/space_file/" in path:
        action = "rewrite" if change == "A" else "adapt"
        return classification(
            "P410", action, "M", "T1 URL ownership and T5 file round-trip", "sandbox file access"
        )
    if path.startswith("source/blender/python/"):
        return classification(
            "P430", "adapt", "F", "T4/T6 bundled Python startup smoke", "target Python runtime"
        )
    if path.startswith("source/blender/gpu/metal/") or path.endswith(
        "gpu_framebuffer_private.hh"
    ):
        return classification(
            "P500", "rewrite", "F", "T6 Metal clear and Workbench frame", "current Metal backend seam"
        )
    if "/eevee/" in path:
        return classification(
            "P520", "defer", "F", "T6 EEVEE smoke", "after Workbench first pixel"
        )
    if path == "source/creator/CMakeLists.txt":
        return classification(
            "P130", "rewrite", "F", "T0/T3 signing-mode audit", "isolate donor automatic codesigning"
        )
    if path == "source/creator/creator.cc":
        return classification(
            "P200", "adapt", "F", "T4 blender_main marker", "UIKit process entry"
        )
    if path.startswith("source/blender/"):
        return classification(
            "P300", "adapt", "M", "T1 input/coordinate seam regression", "window-manager and editor integration"
        )

    raise ValueError(f"no classification rule for {path}")


def donor_changes(repository: Path, base: str, donor: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(repository), "diff", "--name-status", f"{base}..{donor}"],
        check=True,
        capture_output=True,
        text=True,
    )
    changes: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        change = fields[0]
        if change.startswith("R"):
            path = fields[2]
            change = "R"
        else:
            path = fields[1]
        changes.append((change, path))
    return changes


def write_map(handle: TextIO, changes: Sequence[tuple[str, str]]) -> None:
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(FIELDS)
    for change, path in changes:
        item = classify(path, change)
        writer.writerow(
            (
                path,
                change,
                item.packet,
                item.action,
                item.owner,
                "mapped",
                item.test,
                item.notes,
            )
        )


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="v5.1.2")
    parser.add_argument("--donor", default="a1de44dd54af75a4c8c4a29a5fed2a1334a87446")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    changes = donor_changes(arguments.repository, arguments.base, arguments.donor)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        with arguments.output.open("w", newline="") as handle:
            write_map(handle, changes)
    else:
        write_map(sys.stdout, changes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
