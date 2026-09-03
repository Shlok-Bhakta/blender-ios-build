#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostPencilStateTests(unittest.TestCase):
    @staticmethod
    def window_implementation() -> str:
        source = WINDOW_SOURCE.read_text()
        return source[source.index("@implementation GHOSTUIWindow") :]

    def test_pencil_state_starts_with_the_touch(self) -> None:
        source = self.window_implementation()
        began = source[source.index("- (void)touchesBegan:") : source.index("- (void)touchesMoved:")]

        self.assertIn("[self updateTabletDataFromTouch:touch];", began)

    def test_pencil_motion_only_updates_the_tracked_touch(self) -> None:
        source = self.window_implementation()
        moved = source[source.index("- (void)touchesMoved:") : source.index("- (void)touchesEnded:")]

        self.assertIn("touch == current_pencil_touch", moved)
        self.assertIn("[self updateTabletDataFromTouch:touch];", moved)

    def test_pressure_is_bounded_and_unrelated_touches_do_not_clear_pencil_state(self) -> None:
        source = self.window_implementation()

        self.assertIn("maximumPossibleForce > 0.0", source)
        self.assertIn("std::clamp", source)
        self.assertGreaterEqual(source.count("[touches containsObject:current_pencil_touch]"), 2)
        self.assertGreaterEqual(source.count("[self resetTabletData]"), 2)


if __name__ == "__main__":
    unittest.main()
