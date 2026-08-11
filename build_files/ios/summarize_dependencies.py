#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Combine audited dependency manifests into one reproducible packet report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


def summarize(paths: Sequence[Path], packet: str = "N111") -> dict[str, object]:
    if not paths:
        raise ValueError("at least one dependency manifest is required")
    manifests = [json.loads(path.read_text()) for path in paths]
    cache_keys = {item.get("cache_key") for item in manifests}
    targets = {item.get("target") for item in manifests}
    families = [str(item.get("family", "")) for item in manifests]
    if len(cache_keys) != 1 or None in cache_keys:
        raise ValueError("dependency manifests do not share one cache key")
    if len(targets) != 1 or None in targets:
        raise ValueError("dependency manifests do not share one target")
    if any(item.get("status") != "GREEN" for item in manifests):
        raise ValueError("all dependency manifests must be GREEN")
    if "" in families or len(families) != len(set(families)):
        raise ValueError("dependency family names must be present and unique")

    return {
        "schema_version": 1,
        "packet": packet,
        "status": "GREEN",
        "target": targets.pop(),
        "cache_key": cache_keys.pop(),
        "families": [
            {
                "family": item["family"],
                "manifest": str(path),
                "file_count": len(item.get("files", [])),
            }
            for path, item in sorted(zip(paths, manifests), key=lambda pair: pair[1]["family"])
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", required=True, type=Path)
    parser.add_argument("--packet", default="N111")
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = summarize(arguments.manifest, arguments.packet)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"dependency summary failed: {error}", file=sys.stderr)
        return 1
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "GREEN", "output": str(arguments.output)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
