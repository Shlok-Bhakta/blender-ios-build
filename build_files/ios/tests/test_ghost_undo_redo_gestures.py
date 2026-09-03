#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostUndoRedoGestureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_two_and_three_finger_taps_emit_undo_and_redo(self) -> None:
        undo_handler = self.source[
            self.source.rindex("- (void)handleTap2F:"):
            self.source.rindex("- (void)handleTap3F:")
        ]
        redo_handler = self.source[
            self.source.rindex("- (void)handleTap3F:"):
            self.source.rindex("- (void)handleTap4F:")
        ]
        self.assertIn("generateUndoRedoShortcut:false", undo_handler)
        self.assertIn("generateUndoRedoShortcut:true", redo_handler)

    def test_shortcut_helper_preserves_keyboard_undo_and_redo(self) -> None:
        shortcut = self.source[
            self.source.rindex("- (void)generateUndoRedoShortcut:"):
            self.source.rindex("- (void)generateHardwareKeyEvents:")
        ]
        self.assertIn("GHOST_kKeyLeftControl", shortcut)
        self.assertIn("GHOST_kKeyLeftShift", shortcut)
        self.assertIn("GHOST_kKeyZ", shortcut)

    def test_two_finger_hold_owns_rmb_without_competing_with_undo(self) -> None:
        self.assertIn("two_finger_hold_gesture_recognizer.minimumPressDuration", self.source)
        self.assertIn("two_finger_hold_gesture_recognizer.allowableMovement", self.source)
        self.assertIn(
            "[tap2f_gesture_recognizer "
            "requireGestureRecognizerToFail:two_finger_hold_gesture_recognizer];",
            self.source,
        )
        self.assertNotIn(
            "[pan2f_gesture_recognizer "
            "requireGestureRecognizerToFail:two_finger_hold_gesture_recognizer];",
            self.source,
        )

        hold = self.source[
            self.source.rindex("- (void)handleTwoFingerHold:"):
            self.source.rindex("- (void)handleTap2F:")
        ]
        undo = self.source[
            self.source.rindex("- (void)handleTap2F:"):
            self.source.rindex("- (void)handleTap3F:")
        ]
        down = hold.index("button(GHOST_kButtonMaskRight, true")
        move = hold.index("moveRelativeTo")
        up = hold.index("button(GHOST_kButtonMaskRight, false")
        self.assertLess(down, move)
        self.assertLess(move, up)
        self.assertIn("sender.state == UIGestureRecognizerStateBegan", hold)
        self.assertIn("sender.state == UIGestureRecognizerStateChanged && two_finger_hold_active", hold)
        self.assertNotIn("generateUndoRedoShortcut", hold)
        self.assertNotIn("GHOST_kButtonMaskRight", undo)


if __name__ == "__main__":
    unittest.main()
