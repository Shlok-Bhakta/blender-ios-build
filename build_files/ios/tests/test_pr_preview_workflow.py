# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WORKFLOW = REPOSITORY / ".github" / "workflows" / "ios-pr-preview.yml"
HOST_PROFILE = (
    REPOSITORY / "build_files" / "cmake" / "config" / "blender_ios_host_tools.cmake"
)
DEPENDENCY_DOWNLOADS = (
    REPOSITORY / "build_files" / "build_environment" / "cmake" / "download.cmake"
)


class PrPreviewWorkflowTests(unittest.TestCase):
    def test_uses_github_hosted_arm_runner_and_content_addressed_caches(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn("runs-on: macos-15", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertIn("actions/cache", workflow)
        self.assertIn("dependency-cache-key", workflow)
        self.assertIn("host-tool-cache-key", workflow)
        self.assertNotIn("github.workspace }}/../", workflow)

    def test_hydrates_required_lfs_files_from_public_blender_upstream(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn("lfs: false", workflow)
        self.assertNotIn("lfs: true", workflow)
        self.assertIn("https://projects.blender.org/blender/blender.git/info/lfs", workflow)
        self.assertIn("release/datafiles/**", workflow)
        self.assertIn("scripts/**", workflow)

    def test_downloads_only_the_cached_ios_dependency_closure(self) -> None:
        workflow = WORKFLOW.read_text()
        downloads = DEPENDENCY_DOWNLOADS.read_text()
        self.assertIn("-DPACKAGE_USE_UPSTREAM_SOURCES=OFF", workflow)
        self.assertIn("-DBLENDER_DEPENDENCY_DOWNLOADS=", workflow)
        self.assertIn("BLENDER_DEPENDENCY_DOWNLOADS", downloads)
        self.assertIn("IN_LIST BLENDER_DEPENDENCY_DOWNLOADS", downloads)

    def test_publishes_exact_pr_release_contract(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn("gh release delete", workflow)
        self.assertIn("--cleanup-tag", workflow)
        self.assertIn("gh release create", workflow)
        self.assertIn("--prerelease", workflow)
        self.assertIn("DevBlender-test.blenderfoundation.blender.ios-unsigned.ipa", workflow)
        self.assertIn("application/octet-stream", workflow)
        self.assertIn("gh pr comment", workflow)
        self.assertIn("marginally-better-apps.github.io/Autoloader", workflow)
        self.assertNotIn("planista.shloklab.us", workflow.lower())

    def test_write_lane_excludes_forks(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)
        self.assertIn("startsWith(github.head_ref, 'story/')", workflow)

    def test_host_tools_match_the_device_generator_features(self) -> None:
        profile = HOST_PROFILE.read_text()
        self.assertIn("include(\"${CMAKE_CURRENT_LIST_DIR}/blender_lite.cmake\")", profile)
        for feature in ("WITH_CYCLES", "WITH_METAL_BACKEND", "WITH_PYTHON", "WITH_TBB"):
            self.assertIn(f"set({feature}", profile)
            self.assertIn("ON CACHE BOOL", profile)

    def test_host_library_checkout_overrides_the_disabled_submodule_policy(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertIn("submodule.lib/macos_arm64.update=checkout", workflow)


if __name__ == "__main__":
    unittest.main()
