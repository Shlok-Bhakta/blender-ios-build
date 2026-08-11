#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Extract the public dependency target DAG from a generated Ninja graph."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Sequence


PUBLIC_TARGET = re.compile(r"^build (external_[^ :]+): phony ")
CMAKE_TARGET = re.compile(r"^build CMakeFiles/(external_[^ |:]+)(?: \| [^:]+)?: phony ")


def parse_ninja_graph(contents: str) -> dict[str, list[str]]:
    targets: set[str] = set()
    dependencies: dict[str, set[str]] = {}
    for line in contents.splitlines():
        public_match = PUBLIC_TARGET.match(line)
        if public_match:
            targets.add(public_match.group(1))
        cmake_match = CMAKE_TARGET.match(line)
        if not cmake_match:
            continue
        target = cmake_match.group(1)
        dependencies.setdefault(target, set())
        if " || " in line:
            order_only = line.split(" || ", 1)[1].split()
            dependencies[target].update(item for item in order_only if item.startswith("external_"))

    return {target: sorted(dependencies.get(target, set())) for target in sorted(targets)}


def transitive_dependencies(graph: dict[str, list[str]], target: str) -> list[str]:
    visited: set[str] = set()

    def visit(item: str) -> None:
        for dependency in graph.get(item, []):
            if dependency not in visited:
                visited.add(dependency)
                visit(dependency)

    visit(target)
    return sorted(visited)


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-directory", type=Path, required=True)
    parser.add_argument("--cache-key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    ninja_file = arguments.build_directory / "build.ninja"
    if not ninja_file.is_file():
        raise SystemExit(f"missing generated graph: {ninja_file}")
    graph = parse_ninja_graph(ninja_file.read_text())
    if not graph:
        raise SystemExit("no external dependency targets found")

    bootstrap_targets = (
        "external_zlib",
        "external_bzip2",
        "external_lzma",
        "external_ssl",
        "external_sqlite",
        "external_xml2",
        "external_brotli",
        "external_deflate",
    )
    missing_bootstrap = sorted(set(bootstrap_targets).difference(graph))
    if missing_bootstrap:
        raise SystemExit(f"missing bootstrap targets: {missing_bootstrap}")

    document = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": "ios-simulator-arm64",
        "cache_key": arguments.cache_key,
        "target_count": len(graph),
        "edge_count": sum(len(items) for items in graph.values()),
        "root_targets": sorted(target for target, deps in graph.items() if not deps),
        "bootstrap_queue": [
            {
                "target": target,
                "direct_dependencies": graph[target],
                "transitive_dependencies": transitive_dependencies(graph, target),
            }
            for target in bootstrap_targets
        ],
        "targets": graph,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "target_count": document["target_count"],
                "edge_count": document["edge_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
