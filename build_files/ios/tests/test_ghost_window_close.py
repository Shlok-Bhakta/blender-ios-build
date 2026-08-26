#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.hh"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


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

    def test_only_child_windows_receive_a_native_close_control(self) -> None:
        source = WINDOW_SOURCE.read_text()
        registration = source[
            source.rindex("- (void)registerWindowControls") : source.rindex(
                "- (void)handleCloseWindow"
            )
        ]

        self.assertIn("window->hasParentWindow()", registration)
        self.assertIn("close_window_button", registration)
        self.assertIn('accessibilityIdentifier = @"blender_child_window_close";', registration)

    def test_native_close_control_uses_blenders_window_close_event(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[
            source.rindex("- (void)handleCloseWindow") : source.rindex(
                "- (void)generateUserInputEvents:"
            )
        ]

        self.assertIn("window->hasParentWindow()", handler)
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


if __name__ == "__main__":
    unittest.main()
