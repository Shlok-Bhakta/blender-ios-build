#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostUndoRedoGestureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_two_finger_tap_is_a_virtual_cursor_context_click(self) -> None:
        self.assertNotIn("double_tap2f_gesture_recognizer", self.source)
        handler = self.source[
            self.source.rindex("- (void)handleTap2F:") :
            self.source.rindex("- (void)handleTap3F:")
        ]
        self.assertIn("virtual_pointer->click(GHOST_kButtonMaskRight)", handler)

    def test_touch_gestures_do_not_synthesize_undo_or_redo(self) -> None:
        handlers = self.source[
            self.source.rindex("- (void)handleTap2F:") :
            self.source.rindex("- (void)handleTap3F:")
        ]
        self.assertNotIn("generateUndoRedoShortcut", self.source)
        self.assertNotIn("GHOST_kKeyZ", handlers)


if __name__ == "__main__":
    unittest.main()
