# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import tempfile
import unittest

from build_files.ios.package_gltf_bridges import BRIDGE_NAMES, package_bridges


class PackageGltfBridgesTests(unittest.TestCase):
    def test_relocates_bridges_and_keeps_addon_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "Blender.app"
            addon = bundle / "Assets/5.2/scripts/addons_core/io_scene_gltf2"
            addon.mkdir(parents=True)
            for index, name in enumerate(BRIDGE_NAMES):
                (addon / name).write_bytes(f"bridge-{index}".encode())

            relocated = package_bridges(bundle, addon)

            self.assertEqual(len(relocated), 2)
            for index, name in enumerate(BRIDGE_NAMES):
                link = addon / name
                destination = bundle / "Frameworks" / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve(), destination.resolve())
                self.assertEqual(destination.read_bytes(), f"bridge-{index}".encode())

            self.assertEqual(package_bridges(bundle, addon), relocated)


if __name__ == "__main__":
    unittest.main()
