#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
BLENDFILE_SOURCE = (
    REPOSITORY / "source" / "blender" / "blenkernel" / "intern" / "blendfile.cc"
)


class IOSDefaultsTests(unittest.TestCase):
    def test_factory_preferences_use_touch_friendly_ui_scale(self) -> None:
        source = BLENDFILE_SOURCE.read_text()
        defaults = source[
            source.index("UserDef *BKE_blendfile_userdef_from_defaults()") : source.index(
                "bool BKE_blendfile_userdef_write("
            )
        ]

        self.assertIn("#ifdef WITH_APPLE_CROSSPLATFORM", defaults)
        self.assertIn("userdef->ui_scale = 1.65f;", defaults)


if __name__ == "__main__":
    unittest.main()
