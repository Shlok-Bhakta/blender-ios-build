# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
CONFIG_DIRECTORY = REPOSITORY / "build_files" / "cmake" / "config"
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


if __name__ == "__main__":
    unittest.main()
