# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
SYSTEM_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostSceneTests(unittest.TestCase):
    def test_window_is_attached_to_the_active_uiwindow_scene(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("initWithWindowScene", source)

    def test_geometry_and_scale_do_not_read_the_process_main_screen(self) -> None:
        source = SYSTEM_SOURCE.read_text() + WINDOW_SOURCE.read_text()
        self.assertNotIn("[UIScreen mainScreen]", source)

    def test_scene_delegate_owns_active_lifecycle_events(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("@interface IOSSceneDelegate", source)
        self.assertIn("- (void)sceneDidBecomeActive:(UIScene *)scene", source)
        self.assertIn("- (void)sceneWillResignActive:(UIScene *)scene", source)

    def test_drawable_resize_updates_the_ghost_window(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("handleWindowEvent(GHOST_kEventWindowSize", source)


if __name__ == "__main__":
    unittest.main()
