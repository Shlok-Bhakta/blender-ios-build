#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostTouchPolishTests(unittest.TestCase):
    def test_one_finger_drag_is_only_a_left_button_drag(self) -> None:
        source = WINDOW_SOURCE.read_text()
        handler = source[
            source.rindex("- (void)handlePan:") : source.rindex("- (void)handlePan2f:")
        ]

        self.assertIn("LEFT_BUTTON_DOWN", handler)
        self.assertIn("LEFT_BUTTON_UP", handler)
        self.assertIn("CURSOR_MOVE", handler)
        self.assertIn("getScaledInitialTouchPoint", handler)
        self.assertNotIn("PAN_GESTURE", handler)

    def test_only_two_finger_pan_can_run_with_pinch(self) -> None:
        source = WINDOW_SOURCE.read_text()
        delegate = source[
            source.rindex("shouldRecognizeSimultaneouslyWithGestureRecognizer:") : source.rindex(
                "- (void)updateTabletDataFromTouch:"
            )
        ]

        self.assertIn("gestureRecognizer == pan2f_gesture_recognizer", delegate)
        self.assertNotIn("gestureRecognizer == pan_gesture_recognizer", delegate)

    def test_double_tap_right_click_is_anchored_to_the_first_tap(self) -> None:
        source = WINDOW_SOURCE.read_text()

        self.assertIn("double_tap_gesture_recognizer.numberOfTapsRequired = 2;", source)
        self.assertIn(
            "[tap_gesture_recognizer requireGestureRecognizerToFail:double_tap_gesture_recognizer];",
            source,
        )
        self.assertIn("touch.tapCount == 1", source)

        handler = source[
            source.index("- (void)handleDoubleTap:") : source.index("- (void)handleTap2F:")
        ]
        self.assertIn("getScaledFirstTapPoint", handler)
        self.assertIn("RIGHT_BUTTON_CLICK", handler)
        self.assertIn("CURSOR_MOVE", handler)

    def test_double_tap_recognizer_is_direct_touch_only_and_released(self) -> None:
        source = WINDOW_SOURCE.read_text()

        self.assertIn("double_tap_gesture_recognizer.allowedTouchTypes = @[@(UITouchTypeDirect)];", source)
        self.assertIn(
            "[self releaseGestureRecognizer:double_tap_gesture_recognizer fromView:input_view];",
            source,
        )


if __name__ == "__main__":
    unittest.main()
