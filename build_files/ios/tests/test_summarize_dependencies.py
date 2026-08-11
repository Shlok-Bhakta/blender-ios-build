# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import json
from pathlib import Path
import sys
import tempfile
import unittest

IOS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IOS_DIR))

from summarize_dependencies import summarize  # noqa: E402


class DependencySummaryTests(unittest.TestCase):
    def write_manifest(self, root: Path, family: str, cache_key: str = "key") -> Path:
        path = root / f"{family}.json"
        path.write_text(
            json.dumps(
                {
                    "status": "GREEN",
                    "family": family,
                    "target": "ios-simulator",
                    "cache_key": cache_key,
                    "files": [{"path": "lib/example.a"}],
                }
            )
        )
        return path

    def test_combines_one_cache_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = summarize(
                [self.write_manifest(root, "zlib"), self.write_manifest(root, "ssl")]
            )
        self.assertEqual(report["status"], "GREEN")
        self.assertEqual([item["family"] for item in report["families"]], ["ssl", "zlib"])

    def test_rejects_mixed_cache_generations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [
                self.write_manifest(root, "zlib", "one"),
                self.write_manifest(root, "ssl", "two"),
            ]
            with self.assertRaisesRegex(ValueError, "cache key"):
                summarize(paths)


if __name__ == "__main__":
    unittest.main()
