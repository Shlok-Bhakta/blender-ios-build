# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
SYSTEM_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
CONTEXT_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_ContextIOS.mm"


class GhostSceneTests(unittest.TestCase):
    def test_window_is_attached_to_the_active_uiwindow_scene(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("initWithWindowScene", source)

    def test_geometry_and_scale_do_not_read_the_process_main_screen(self) -> None:
        source = SYSTEM_SOURCE.read_text() + WINDOW_SOURCE.read_text() + CONTEXT_SOURCE.read_text()
        self.assertNotIn("[UIScreen mainScreen]", source)

    def test_scene_delegate_owns_active_lifecycle_events(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("@interface IOSSceneDelegate", source)
        self.assertIn("- (void)sceneDidBecomeActive:(UIScene *)scene", source)
        self.assertIn("- (void)sceneWillResignActive:(UIScene *)scene", source)

    def test_drawable_resize_updates_the_ghost_window(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("handleWindowEvent(GHOST_kEventWindowSize", source)

    def test_screen_and_client_coordinates_use_the_scene_coordinate_space(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("fromCoordinateSpace:window_scene.coordinateSpace", source)
        self.assertIn("toCoordinateSpace:window_scene.coordinateSpace", source)

    def test_cursor_state_converts_between_scene_screen_and_client_coordinates(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        self.assertIn("window->clientToScreen(cursor_x_, cursor_y_, x, y);", source)
        self.assertIn("window->screenToClient(x, y, client_x, client_y);", source)
        self.assertIn("updateCursorPositionState(client_x, client_y);", source)

    def test_metal_framebuffer_follows_the_current_drawable(self) -> None:
        source = CONTEXT_SOURCE.read_text()
        self.assertIn("const CGSize drawable_size = metal_view_.drawableSize;", source)
        self.assertIn("if (width == 0 || height == 0)", source)

    def test_client_bounds_match_the_metal_drawable_pixels(self) -> None:
        source = WINDOW_SOURCE.read_text()
        method = source[
            source.index("void GHOST_WindowIOS::getClientBounds") : source.index(
                "GHOST_TSuccess GHOST_WindowIOS::setClientWidth"
            )
        ]

        self.assertIn("const CGSize drawable_size = metal_view_.drawableSize;", method)
        self.assertIn("bounds.r_ = std::lround(drawable_size.width);", method)
        self.assertIn("bounds.b_ = std::lround(drawable_size.height);", method)
        self.assertNotIn("screen.scale", method)

    def test_window_bounds_use_the_actual_view_backing_scale(self) -> None:
        source = WINDOW_SOURCE.read_text()
        method = source[
            source.index("void GHOST_WindowIOS::getWindowBounds") : source.index(
                "void GHOST_WindowIOS::getClientBounds"
            )
        ]

        self.assertIn("getWindowScaleFactor()", method)
        self.assertNotIn("windowScene.screen.scale", method)

    def test_window_scale_comes_from_the_actual_view_backing(self) -> None:
        source = WINDOW_SOURCE.read_text()
        method = source[
            source.index("float GHOST_WindowIOS::getWindowScaleFactor") : source.index(
                "void GHOST_WindowIOS::requestToActivateWindow"
            )
        ]

        self.assertIn("metal_view_.drawableSize", method)
        self.assertIn("metal_view_.bounds.size", method)
        self.assertNotIn("window_scene.screen.scale", method)

    def test_metal_view_does_not_force_the_logical_screen_scale(self) -> None:
        source = WINDOW_SOURCE.read_text()
        view_setup = source[source.index("- (void)viewDidLoad") : source.index("- (void)handleGesture:")]

        self.assertNotIn("_view.contentScaleFactor = _screen.scale;", view_setup)

    def test_metal_view_tracks_the_scene_window_bounds(self) -> None:
        source = WINDOW_SOURCE.read_text()

        self.assertIn("metal_view_.frame = rootWindow.bounds;", source)
        self.assertIn("UIViewAutoresizingFlexibleWidth", source)
        self.assertIn("UIViewAutoresizingFlexibleHeight", source)

    def test_offscreen_context_does_not_assume_a_device_display_size(self) -> None:
        source = CONTEXT_SOURCE.read_text()
        self.assertIn("CGRectMake(0, 0, 1, 1)", source)
        self.assertNotIn("2532", source)
        self.assertNotIn("1170", source)


if __name__ == "__main__":
    unittest.main()
