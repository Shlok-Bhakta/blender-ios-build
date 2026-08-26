#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostTextEntryPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WINDOW_SOURCE.read_text()

    def test_accessory_toolbar_uses_conventional_cancel_and_done_layout(self) -> None:
        toolbar = self.source[
            self.source.rindex("- (void)initToolbar") : self.source.rindex(
                "- (void)generateKeyboardReturnEvent"
            )
        ]

        self.assertIn("UIBarButtonSystemItemFlexibleSpace", toolbar)
        items = toolbar[toolbar.index("toolbar.items = @[") :]
        cancel_position = items.index("toolbar_cancel_editing_item")
        flexible_position = items.index("toolbar_flexible_space_item")
        done_position = items.index("toolbar_done_editing_item")
        self.assertLess(cancel_position, flexible_position)
        self.assertLess(flexible_position, done_position)
        self.assertNotIn("toolbar_live_text_item", toolbar)

    def test_native_text_field_is_accessible_and_touch_sized(self) -> None:
        self.assertIn('accessibilityIdentifier = @"blender_text_entry"', self.source)
        self.assertIn("std::max<CGFloat>(displayRect.size.height, 44.0f)", self.source)
        self.assertIn("17.0f", self.source)
        self.assertIn("text_luminance", self.source)
        self.assertIn("clearButtonMode = UITextFieldViewModeWhileEditing", self.source)

    def test_cancel_uses_blenders_escape_semantics(self) -> None:
        handler = self.source[
            self.source.rindex("- (void)handleCancelButton") : self.source.rindex(
                "- (void)initUITextField"
            )
        ]

        self.assertIn("GHOST_kKeyEsc", handler)
        self.assertNotIn("generateKeyboardReturnEvent", handler)

    def test_text_field_restores_the_original_blender_frame_after_editing(self) -> None:
        self.assertIn("CGRect blender_text_field_frame;", self.source)
        self.assertIn("text_field.frame = blender_text_field_frame;", self.source)


if __name__ == "__main__":
    unittest.main()
