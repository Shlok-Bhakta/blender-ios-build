# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import tempfile
import unittest

from build_files.ios.dependency_manifest import digest


class DependencyManifestTests(unittest.TestCase):
    def test_digest_is_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact"
            path.write_bytes(b"first")
            first = digest(path)
            path.write_bytes(b"second")
            self.assertNotEqual(first, digest(path))


if __name__ == "__main__":
    unittest.main()
