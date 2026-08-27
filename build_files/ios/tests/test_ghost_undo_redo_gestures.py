#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostUndoRedoGestureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_two_finger_single_and_double_taps_are_distinct(self) -> None:
        self.assertIn("double_tap2f_gesture_recognizer", self.source)
        self.assertIn("@selector(handleDoubleTap2F:)", self.source)
        self.assertIn("double_tap2f_gesture_recognizer.numberOfTapsRequired = 2;", self.source)
        self.assertIn("double_tap2f_gesture_recognizer.numberOfTouchesRequired = 2;", self.source)
        self.assertIn(
            "requireGestureRecognizerToFail:double_tap2f_gesture_recognizer",
            self.source,
        )
        self.assertIn(
            "[self releaseGestureRecognizer:double_tap2f_gesture_recognizer fromView:input_view];",
            self.source,
        )

    def test_taps_emit_blenders_undo_and_redo_shortcuts(self) -> None:
        shortcut = self.source[
            self.source.rindex("- (void)generateUndoRedoShortcut:") :
            self.source.rindex("- (void)handleTap2F:")
        ]
        handlers = self.source[
            self.source.rindex("- (void)handleTap2F:") :
            self.source.rindex("- (void)handleTap3F:")
        ]

        self.assertIn("GHOST_kKeyLeftControl", shortcut)
        self.assertIn("GHOST_kKeyLeftShift", shortcut)
        self.assertIn("GHOST_kKeyZ", shortcut)
        self.assertIn("[self generateUndoRedoShortcut:false];", handlers)
        self.assertIn("[self generateUndoRedoShortcut:true];", handlers)


if __name__ == "__main__":
    unittest.main()
