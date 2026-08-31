#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostGlobalSearchGestureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_four_finger_tap_is_direct_touch_only(self) -> None:
        registration = self.source[
            self.source.index("/* Four-finger tap gesture recognizer. */") :
            self.source.index("/* A direct finger moves the virtual cursor relatively")
        ]

        self.assertIn("tap4f_gesture_recognizer.numberOfTouchesRequired = 4;", registration)
        self.assertIn(
            "tap4f_gesture_recognizer.allowedTouchTypes = @[@(UITouchTypeDirect)];",
            registration,
        )

    def test_four_finger_tap_emits_blenders_f3_search_shortcut(self) -> None:
        handler = self.source[
            self.source.rindex("- (void)handleTap4F:") :
            self.source.rindex("- (void)handlePan:")
        ]

        self.assertIn("GHOST_kKeyF3 down:true", handler)
        self.assertIn("GHOST_kKeyF3 down:false", handler)
        self.assertNotIn("GHOST_kEventFourFingerTap", handler)


if __name__ == "__main__":
    unittest.main()
