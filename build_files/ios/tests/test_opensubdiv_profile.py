# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
CONFIG_DIRECTORY = REPOSITORY / "build_files" / "cmake" / "config"
APPLE_PLATFORM = (
    REPOSITORY / "build_files" / "cmake" / "platform" / "platform_apple.cmake"
)
WORKFLOW = REPOSITORY / ".github" / "workflows" / "ios-pr-preview.yml"


class OpenSubdivProfileTests(unittest.TestCase):
    def test_device_and_simulator_enable_opensubdiv(self) -> None:
        for filename in ("blender_ios_sim.cmake", "blender_ios_device.cmake"):
            with self.subTest(filename=filename):
                profile = (CONFIG_DIRECTORY / filename).read_text()
                self.assertIn(
                    'set(WITH_OPENSUBDIV ON CACHE BOOL "" FORCE)',
                    profile,
                )

    def test_native_generator_tools_match_the_opensubdiv_feature(self) -> None:
        profile = (CONFIG_DIRECTORY / "blender_ios_host_tools.cmake").read_text()
        self.assertIn(
            'set(WITH_OPENSUBDIV           ON CACHE BOOL "" FORCE)',
            profile,
        )

    def test_ios_platform_resolves_opensubdiv_from_dependency_sysroot(self) -> None:
        platform = APPLE_PLATFORM.read_text()
        ios_branch = platform.split(
            "if(WITH_APPLE_CROSSPLATFORM)", 1
        )[1].split("  return()", 1)[0]
        self.assertIn('set(OPENSUBDIV_ROOT_DIR "${LIBDIR}/opensubdiv")', ios_branch)
        self.assertIn("find_package(OpenSubdiv REQUIRED)", ios_branch)

    def test_preview_builds_and_audits_the_opensubdiv_dependency(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn(";OPENSUBDIV;", workflow)
        self.assertIn("external_opensubdiv", workflow)
        for library in ("libosdCPU.a", "libosdGPU.a"):
            self.assertIn(
                f'test -s "$DEPS_INSTALL/opensubdiv/lib/{library}"',
                workflow,
            )
        self.assertIn(
            'test -f "$DEPS_INSTALL/opensubdiv/include/opensubdiv/version.h"',
            workflow,
        )
        self.assertIn("::error::Missing cached file:", workflow)
        self.assertIn("::error::Missing or empty cached file:", workflow)


if __name__ == "__main__":
    unittest.main()
