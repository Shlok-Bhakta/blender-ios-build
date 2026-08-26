#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
KEYMAP_DATA = (
    REPOSITORY / "scripts" / "presets" / "keyconfig" / "keymap_data" / "blender_default.py"
)
BLENDER_KEYCONFIG = REPOSITORY / "scripts" / "presets" / "keyconfig" / "Blender.py"


def load_keymap_data():
    spec = importlib.util.spec_from_file_location("ios_blender_default_keymap", KEYMAP_DATA)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class View3DObjectMovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.keymap = load_keymap_data()

    def test_primary_selection_tools_do_not_translate_on_drag(self) -> None:
        params = self.keymap.Params(select_mouse="LEFT")

        for keymap_factory in (
            self.keymap.km_3d_view_tool_select,
            self.keymap.km_3d_view_tool_select_box,
        ):
            items = keymap_factory(params, fallback=False)[2]["items"]
            self.assertFalse(any(item[0] == "transform.translate" for item in items))

    def test_ios_does_not_override_blenders_standard_selection_keymaps(self) -> None:
        keymap_source = KEYMAP_DATA.read_text()
        blender_keyconfig = BLENDER_KEYCONFIG.read_text()

        self.assertNotIn("use_v3d_tweak_drag_translate", keymap_source)
        self.assertNotIn("use_v3d_tweak_drag_translate", blender_keyconfig)


if __name__ == "__main__":
    unittest.main()
