# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import re
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostInputLifetimeTests(unittest.TestCase):
    def test_keyboard_result_owns_its_utf8_storage(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertIn("std::string text_field_string;", source)
        self.assertNotIn("const char *text_field_string;", source)
        self.assertIn("return text_field_string.c_str();", source)

    def test_input_window_removes_dead_observers_and_releases_owned_objects(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertNotIn("addObserver:self", source)
        self.assertNotIn("external_keyboard_connected", source)
        self.assertIn("- (void)invalidateInput", source)
        self.assertIn("[pencil_interaction setDelegate:nil];", source)
        self.assertIn("[text_field removeFromSuperview];", source)
        self.assertIn("[super dealloc];", source)

    def test_failed_keyboard_activation_is_reported(self) -> None:
        source = WINDOW_SOURCE.read_text()
        activation = re.search(
            r"if \(!\[text_field becomeFirstResponder\]\) \{(?P<body>.*?)\n\s*\}",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(activation)
        self.assertIn("return GHOST_kFailure;", activation.group("body"))

    def test_dead_input_state_is_removed(self) -> None:
        source = WINDOW_SOURCE.read_text()
        self.assertNotIn("current_keyboard_properties", source)
        self.assertNotIn("pencil_used", source)

    def test_teardown_disables_keyboard_callbacks_before_resigning(self) -> None:
        source = WINDOW_SOURCE.read_text()
        teardown = re.search(
            r"- \(void\)invalidateInput\n\{(?P<body>.*?)\n\}", source, re.DOTALL
        )
        self.assertIsNotNone(teardown)
        body = teardown.group("body")
        self.assertLess(
            body.index("onscreen_keyboard_active = false;"),
            body.index("[text_field resignFirstResponder];"),
        )


if __name__ == "__main__":
    unittest.main()
