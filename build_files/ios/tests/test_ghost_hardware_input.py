#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostHardwareInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_mouse_taps_support_secondary_and_middle_buttons(self) -> None:
        self.assertIn("mouse_secondary_tap_recognizer", self.source)
        self.assertIn("buttonMaskRequired = UIEventButtonMaskSecondary", self.source)
        self.assertIn("mouse_middle_tap_recognizer", self.source)
        self.assertIn("buttonMaskRequired = UIEventButtonMaskForButtonNumber(3)", self.source)

    def test_mouse_drags_preserve_the_pressed_button(self) -> None:
        self.assertIn("initial_button_mask = event.buttonMask", self.source)
        self.assertIn("return GHOST_kButtonMaskMiddle;", self.source)
        self.assertIn("return GHOST_kButtonMaskRight;", self.source)
        handler = self.source[
            self.source.rindex("- (void)handleHardwareDrag:") :
            self.source.rindex("- (void)handlePan2f:")
        ]
        self.assertIn("pointerButton(button_mask)", handler)
        self.assertIn("virtual_pointer->button(button, true)", handler)
        self.assertIn("virtual_pointer->button(button, false)", handler)

    def test_pointer_scroll_generates_a_trackpad_scroll_event(self) -> None:
        self.assertIn("scroll_gesture_recognizer", self.source)
        self.assertIn("allowedScrollTypesMask = UIScrollTypeMaskAll", self.source)
        self.assertIn("POINTER_SCROLL", self.source)
        self.assertIn("GHOST_kTrackpadEventScroll", self.source)

    def test_hover_only_enables_tablet_data_for_pencil(self) -> None:
        self.assertIn("hover_touch_type", self.source)
        self.assertIn("[sender getTouchType] == UITouchTypePencil", self.source)

    def test_hardware_keyboard_focus_is_restored_after_text_entry(self) -> None:
        self.assertIn("- (BOOL)canBecomeFirstResponder", self.source)
        self.assertIn("[rootWindow becomeFirstResponder]", self.source)
        self.assertIn("[self becomeFirstResponder]", self.source)
        self.assertIn("UIKeyModifierCommand", self.source)


if __name__ == "__main__":
    unittest.main()
