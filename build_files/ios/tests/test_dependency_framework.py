# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import json
from pathlib import Path
import subprocess
import sys
import unittest

from build_files.ios.configure_dependencies import cache_key_for_inputs, find_build_python


REPOSITORY = Path(__file__).resolve().parents[3]
CONFIGURATOR = REPOSITORY / "build_files" / "ios" / "configure_dependencies.py"


class CacheKeyTests(unittest.TestCase):
    def test_key_is_stable_for_mapping_order(self) -> None:
        first = cache_key_for_inputs({"sdk": "26.5", "target": "ios-simulator"})
        second = cache_key_for_inputs({"target": "ios-simulator", "sdk": "26.5"})
        self.assertEqual(first, second)

    def test_key_changes_with_toolchain(self) -> None:
        first = cache_key_for_inputs({"sdk": "26.5", "target": "ios-simulator"})
        second = cache_key_for_inputs({"sdk": "26.6", "target": "ios-simulator"})
        self.assertNotEqual(first, second)


class ConfigurePlanTests(unittest.TestCase):
    def test_native_build_python_matches_blender_minor_version(self) -> None:
        path, version = find_build_python()
        self.assertTrue(path.is_file())
        self.assertTrue(version.startswith("3.13."), version)

    def test_plan_routes_every_bulk_path_to_external_volume(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CONFIGURATOR),
                "--repository",
                str(REPOSITORY),
                "--print-plan",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        plan = json.loads(result.stdout)
        bulk_prefix = "/Volumes/BlenderBuild/blender-ios/"
        for key in (
            "build_directory",
            "install_directory",
            "download_directory",
            "package_directory",
            "temporary_directory",
        ):
            self.assertTrue(plan[key].startswith(bulk_prefix), (key, plan[key]))
        self.assertEqual(plan["cache_inputs"]["target"], "ios-simulator")
        self.assertEqual(
            plan["cache_inputs"]["target_triple"], "arm64-apple-ios18.0-simulator"
        )
        self.assertTrue(plan["cache_inputs"]["build_python_version"].startswith("3.13."))


class PythonFrameworkRecipeTests(unittest.TestCase):
    def test_supported_platform_array_is_replaced_instead_of_partially_edited(self) -> None:
        recipe = (
            REPOSITORY
            / "build_files"
            / "ios"
            / "build_environment"
            / "cmake"
            / "python.cmake"
        ).read_text()
        self.assertIn("-remove CFBundleSupportedPlatforms", recipe)
        self.assertIn("-insert CFBundleSupportedPlatforms", recipe)
        self.assertNotIn("-replace CFBundleSupportedPlatforms.0", recipe)


if __name__ == "__main__":
    unittest.main()
