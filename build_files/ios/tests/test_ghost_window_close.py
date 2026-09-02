#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.hh"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
SYSTEM_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"


class GhostWindowCloseTests(unittest.TestCase):
    def test_dialog_state_is_initialized_from_the_window_request(self) -> None:
        header = WINDOW_HEADER.read_text()
        source = WINDOW_SOURCE.read_text()

        self.assertIn("bool is_dialog,", header)
        constructor = source[
            source.index("GHOST_WindowIOS::GHOST_WindowIOS(") : source.index(
                "GHOST_WindowIOS::~GHOST_WindowIOS()"
            )
        ]
        self.assertIn("bool is_dialog,", constructor)
        self.assertIn("is_dialog_(is_dialog)", constructor)

    def test_every_non_main_window_receives_the_native_close_control(self) -> None:
        source = WINDOW_SOURCE.read_text()
        registration = source[
            source.rindex("- (void)registerWindowControls") : source.rindex(
                "- (void)handleCloseWindow"
            )
        ]

        self.assertIn("window->isMainWindow()", registration)
        self.assertNotIn("window->hasParentWindow()", registration)
        self.assertIn("close_window_button", registration)
        self.assertIn('accessibilityIdentifier = @"blender_child_window_close";', registration)
        self.assertNotIn("Blender Render", registration)
        self.assertNotIn("Preferences", registration)

    def test_main_window_identity_does_not_depend_on_parent_or_title(self) -> None:
        header = WINDOW_HEADER.read_text()
        source = SYSTEM_SOURCE.read_text()
        create_window = source[
            source.index("GHOST_IWindow *GHOST_SystemIOS::createWindow"):
            source.index("GHOST_IContext *GHOST_SystemIOS::createOffscreenContext")
        ]

        self.assertIn("bool is_main_window,", header)
        self.assertIn("bool isMainWindow() const", header)
        self.assertIn("window_manager_->getWindows().empty()", create_window)
        self.assertIn("is_main_window", create_window)
        self.assertNotIn('STREQ(title, "Blender Render")', create_window)

    def test_toplevel_secondary_window_returns_to_the_active_ios_window(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        create_window = source[
            source.index("GHOST_IWindow *GHOST_SystemIOS::createWindow"):
            source.index("GHOST_IContext *GHOST_SystemIOS::createOffscreenContext")
        ]

        self.assertIn("close_return_window", create_window)
        self.assertIn("parent_window ?", create_window)
        self.assertIn("window_manager_->getActiveWindow()", create_window)
        self.assertIn("(GHOST_WindowIOS *)close_return_window", create_window)

    def test_native_close_control_uses_blenders_window_close_event(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[
            source.rindex("- (void)handleCloseWindow") : source.rindex(
                "- (void)generateUserInputEvents:"
            )
        ]

        self.assertIn("window->isMainWindow()", handler)
        self.assertNotIn("window->hasParentWindow()", handler)
        self.assertIn("handleWindowEvent(GHOST_kEventWindowClose, window)", handler)

    def test_close_control_is_detached_before_window_teardown(self) -> None:
        source = WINDOW_SOURCE.read_text()
        invalidation = source[
            source.rindex("- (void)invalidateInput") : source.rindex("- (void)dealloc")
        ]

        self.assertIn("[close_window_button removeTarget:self", invalidation)
        self.assertIn("[close_window_button removeFromSuperview]", invalidation)
        self.assertIn("[close_window_button release]", invalidation)
        self.assertIn("close_window_button = nil;", invalidation)

    def test_destroyed_window_is_hidden_before_uikit_releases_it(self) -> None:
        source = WINDOW_SOURCE.read_text()
        destructor = source[
            source.index("GHOST_WindowIOS::~GHOST_WindowIOS()"):
            source.index("#pragma mark accessors")
        ]

        hide = destructor.index("rootWindow.hidden = YES;")
        release = destructor.index("[rootWindow release]")
        self.assertLess(hide, release)

    def test_deactivation_resigns_native_key_window_status(self) -> None:
        source = WINDOW_SOURCE.read_text()
        resign = source[
            source.index("void GHOST_WindowIOS::resignKeyWindow()"):
            source.index("CGPoint GHOST_WindowIOS::scalePointToWindow")
        ]

        self.assertIn("[rootWindow resignKeyWindow]", resign)


if __name__ == "__main__":
    unittest.main()
