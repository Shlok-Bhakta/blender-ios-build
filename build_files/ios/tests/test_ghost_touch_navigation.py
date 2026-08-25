#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"
EVENT_SOURCE = (
    REPOSITORY / "source" / "blender" / "windowmanager" / "intern" / "wm_event_system.cc"
)


class GhostTouchNavigationTests(unittest.TestCase):
    def test_three_finger_pan_is_registered_and_released(self) -> None:
        source = WINDOW_SOURCE.read_text()

        self.assertIn("pan3f_gesture_recognizer", source)
        self.assertIn("@selector(handlePan3f:)", source)
        self.assertIn("pan3f_gesture_recognizer.minimumNumberOfTouches = 3;", source)
        self.assertIn("pan3f_gesture_recognizer.maximumNumberOfTouches = 3;", source)
        self.assertIn(
            "[self releaseGestureRecognizer:pan3f_gesture_recognizer fromView:input_view];",
            source,
        )

    def test_three_finger_pan_reuses_incremental_trackpad_translation(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[source.index("- (void)handlePan3f:") : source.index("- (void)handleEdgeSwipe:")]

        self.assertIn("getRelativeTranslation", handler)
        self.assertIn("PAN_GESTURE_THREE_FINGERS", handler)
        self.assertIn("setCachedTranslation:CGPointMake(0.0f, 0.0f)", handler)

    def test_three_finger_trackpad_event_selects_blender_pan_keymap(self) -> None:
        source = EVENT_SOURCE.read_text()
        trackpad_case = source[
            source.index("case GHOST_kEventTrackpad:") : source.index("/* Mouse button. */")
        ]

        self.assertIn("pd->numFingers == 3", trackpad_case)
        self.assertIn("event.modifier |= KM_SHIFT", trackpad_case)
        self.assertIn("#if defined(WITH_APPLE_CROSSPLATFORM)", trackpad_case)


if __name__ == "__main__":
    unittest.main()
