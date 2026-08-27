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
        self.assertIn("toolbar_text_item", toolbar)
        self.assertIn("toolbar_value_label", toolbar)

    def test_native_text_responder_does_not_cover_the_blender_field(self) -> None:
        self.assertIn('accessibilityIdentifier = @"blender_text_entry"', self.source)
        self.assertIn(
            "text_field.frame = CGRectMake(0.0f, 0.0f, 1.0f, 1.0f);",
            self.source,
        )
        self.assertIn("text_field.backgroundColor = UIColor.clearColor;", self.source)
        self.assertNotIn("text_field.frame = displayRect;", self.source)

    def test_accessory_prioritizes_the_live_value_and_truncates_the_tip(self) -> None:
        toolbar = self.source[
            self.source.rindex("- (void)initToolbar") : self.source.rindex(
                "- (void)generateKeyboardReturnEvent"
            )
        ]
        change_handler = self.source[
            self.source.rindex("- (void)handleKeyboardEditChange:") : self.source.rindex(
                "- (void)handleKeyboardEditBegin:"
            )
        ]

        self.assertIn("NSLineBreakByTruncatingTail", toolbar)
        self.assertIn("monospacedDigitSystemFontOfSize", toolbar)
        self.assertIn('accessibilityIdentifier = @"blender_text_entry_value"', toolbar)
        self.assertIn("toolbar_value_label.text = sender.text", change_handler)

    def test_cancel_uses_blenders_escape_semantics(self) -> None:
        handler = self.source[
            self.source.rindex("- (void)handleCancelButton") : self.source.rindex(
                "- (void)initUITextField"
            )
        ]

        self.assertIn("GHOST_kKeyEsc", handler)
        self.assertNotIn("generateKeyboardReturnEvent", handler)

    def test_text_field_never_tracks_the_blender_widget_frame(self) -> None:
        self.assertNotIn("CGRect blender_text_field_frame;", self.source)
        self.assertNotIn("text_field.frame = blender_text_field_frame;", self.source)


if __name__ == "__main__":
    unittest.main()
