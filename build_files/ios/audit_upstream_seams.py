#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Measure the port's edits to files that existed in an upstream Blender tree."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Audit:
    base: str
    target: str
    changed_paths: int
    upstream_files_modified: int
    port_owned_files: int
    upstream_additions: int
    upstream_deletions: int
    upstream_churn: int
    upstream_paths: list[str]


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def audit(base: str, target: str | None) -> Audit:
    revision_range = (base, target) if target else (base,)
    paths = git("diff", "--no-renames", "--name-only", *revision_range, "--").stdout.splitlines()
    upstream_paths = [
        path for path in paths if git("cat-file", "-e", f"{base}:{path}", check=False).returncode == 0
    ]

    additions = 0
    deletions = 0
    upstream_path_set = set(upstream_paths)
    numstat = git("diff", "--no-renames", "--numstat", *revision_range, "--").stdout.splitlines()
    for row in numstat:
        added, deleted, path = row.split("\t", 2)
        if path not in upstream_path_set:
            continue
        if added.isdecimal():
            additions += int(added)
        if deleted.isdecimal():
            deletions += int(deleted)

    return Audit(
        base=git("rev-parse", base).stdout.strip(),
        target=git("rev-parse", target or "HEAD").stdout.strip() if target else "working-tree",
        changed_paths=len(paths),
        upstream_files_modified=len(upstream_paths),
        port_owned_files=len(paths) - len(upstream_paths),
        upstream_additions=additions,
        upstream_deletions=deletions,
        upstream_churn=additions + deletions,
        upstream_paths=upstream_paths,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Upstream Blender baseline revision")
    parser.add_argument("--target", help="Target revision; omit to include the working tree")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    arguments = parser.parse_args()

    result = audit(arguments.base, arguments.target)
    if arguments.json:
        print(json.dumps(asdict(result), indent=2))
        return

    print(f"base: {result.base}")
    print(f"target: {result.target}")
    print(f"changed paths: {result.changed_paths}")
    print(f"upstream files modified: {result.upstream_files_modified}")
    print(f"port-owned files: {result.port_owned_files}")
    print(
        "upstream LOC: "
        f"+{result.upstream_additions} -{result.upstream_deletions} "
        f"({result.upstream_churn} churn)"
    )
    print("upstream paths:")
    for path in result.upstream_paths:
        print(f"  {path}")


if __name__ == "__main__":
    main()
