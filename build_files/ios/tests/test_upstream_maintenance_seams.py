# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]


class UpstreamMaintenanceSeamsTests(unittest.TestCase):
    def test_dependency_build_uses_ios_owned_entrypoint(self) -> None:
        configure_script = (
            REPOSITORY / "build_files" / "ios" / "configure_dependencies.py"
        ).read_text()

        self.assertIn(
            'repository / "build_files" / "ios" / "build_environment"',
            configure_script,
        )

    def test_upstream_dependency_recipes_have_no_ios_policy(self) -> None:
        dependency_root = REPOSITORY / "build_files" / "build_environment"
        offenders = []
        for cmake_file in sorted(dependency_root.rglob("*.cmake")):
            contents = cmake_file.read_text()
            if "WITH_APPLE_CROSSPLATFORM" in contents or "BLENDER_IOS_" in contents:
                offenders.append(cmake_file.relative_to(REPOSITORY).as_posix())

        self.assertEqual([], offenders)

    def test_ios_dependency_reports_resolve_upstream_templates_explicitly(self) -> None:
        ios_cmake_root = (
            REPOSITORY / "build_files" / "ios" / "build_environment" / "cmake"
        )

        for recipe in ("deps_md.cmake", "cve_check.cmake"):
            contents = (ios_cmake_root / recipe).read_text()
            self.assertIn("BLENDER_UPSTREAM_DEPS_ROOT", contents)
            self.assertNotIn("${CMAKE_SOURCE_DIR}/cmake", contents)

    def test_ios_dependency_recipes_do_not_assume_owned_companion_files(self) -> None:
        ssl_recipe = (
            REPOSITORY
            / "build_files"
            / "ios"
            / "build_environment"
            / "cmake"
            / "ssl.cmake"
        ).read_text()

        self.assertIn("${BLENDER_UPSTREAM_DEPS_ROOT}/cmake/ssl.conf", ssl_recipe)
        self.assertNotIn("${CMAKE_CURRENT_SOURCE_DIR}/cmake/ssl.conf", ssl_recipe)

        offenders = []
        ios_recipe_root = (
            REPOSITORY / "build_files" / "ios" / "build_environment" / "cmake"
        )
        for recipe_path in sorted(ios_recipe_root.glob("*.cmake")):
            contents = recipe_path.read_text()
            if "CMAKE_SOURCE_DIR" in contents or "include(../" in contents:
                offenders.append(recipe_path.relative_to(REPOSITORY).as_posix())

        self.assertEqual([], offenders)

    def test_apple_platform_file_only_dispatches_to_ios(self) -> None:
        platform_file = (
            REPOSITORY / "build_files" / "cmake" / "platform" / "platform_apple.cmake"
        ).read_text()
        ios_platform = (
            REPOSITORY / "build_files" / "ios" / "cmake" / "platform_ios.cmake"
        )

        self.assertTrue(ios_platform.is_file())
        self.assertLessEqual(platform_file.count("WITH_APPLE_CROSSPLATFORM"), 1)
        self.assertNotIn("IOS_HOST_TOOLS_DIR", platform_file)

    def test_http_downloader_delegates_platform_worker_selection(self) -> None:
        downloader = (
            REPOSITORY / "scripts" / "modules" / "_bpy_internal" / "http" / "downloader.py"
        ).read_text()
        worker_context = (
            REPOSITORY / "scripts" / "modules" / "_bpy_internal" / "http" / "worker_context.py"
        ).read_text()

        self.assertIn("from .worker_context import", downloader)
        self.assertNotIn("sys.platform", downloader)
        self.assertIn("sys.platform == 'ios'", worker_context)


if __name__ == "__main__":
    unittest.main()
