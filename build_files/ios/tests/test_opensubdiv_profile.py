# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
CONFIG_DIRECTORY = REPOSITORY / "build_files" / "cmake" / "config"
APPLE_PLATFORM = (
    REPOSITORY / "build_files" / "ios" / "cmake" / "platform_ios.cmake"
)
GPU_EVAL_OUTPUT = (
    REPOSITORY
    / "intern"
    / "opensubdiv"
    / "internal"
    / "evaluator"
    / "eval_output_gpu.h"
)
GPU_COMPUTE_EVALUATOR = GPU_EVAL_OUTPUT.with_name("gpu_compute_evaluator.cc")
OPENSUBDIV_CMAKE = GPU_EVAL_OUTPUT.parents[2] / "CMakeLists.txt"
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
        self.assertIn('set(OPENSUBDIV_ROOT_DIR "${LIBDIR}/opensubdiv")', platform)
        self.assertIn("find_package(OpenSubdiv REQUIRED)", platform)

    def test_gpu_eval_output_does_not_require_opengl_adapter_headers(self) -> None:
        header = GPU_EVAL_OUTPUT.read_text()
        self.assertNotIn("opensubdiv/osd/glPatchTable.h", header)
        self.assertNotIn("opensubdiv/osd/glVertexBuffer.h", header)

    def test_gpu_compute_evaluator_uses_backend_neutral_gpu_api(self) -> None:
        source = GPU_COMPUTE_EVALUATOR.read_text()
        cmake = OPENSUBDIV_CMAKE.read_text()
        self.assertNotIn("epoxy/gl.h", source)
        self.assertNotIn("bf::dependencies::epoxy", cmake)

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
