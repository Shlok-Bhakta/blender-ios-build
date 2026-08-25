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


def find_binding(items, operator, value):
    return next(
        item
        for item in items
        if item[0] == operator
        and item[1].get("type") == "LEFTMOUSE"
        and item[1].get("value") == value
    )


class View3DDirectObjectDragTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.keymap = load_keymap_data()

    def test_ios_primary_selection_tools_select_then_invoke_normal_translate(self) -> None:
        params = self.keymap.Params(
            select_mouse="LEFT",
            use_v3d_tweak_drag_translate=True,
        )
        name, context, data = self.keymap.km_3d_view_tool_select(params, fallback=False)

        self.assertEqual(name, "3D View Tool: Tweak")
        self.assertEqual(context, {"space_type": "VIEW_3D", "region_type": "WINDOW"})

        select = find_binding(data["items"], "view3d.select", "PRESS")
        self.assertIn(("deselect_all", True), select[2]["properties"])
        self.assertIn(("select_passthrough", True), select[2]["properties"])

        translate = find_binding(data["items"], "transform.translate", "CLICK_DRAG")
        self.assertEqual(translate[2]["properties"], [("release_confirm", True)])
        self.assertLess(data["items"].index(select), data["items"].index(translate))

        name, context, data = self.keymap.km_3d_view_tool_select_box(params, fallback=False)
        self.assertEqual(name, "3D View Tool: Select Box")
        self.assertEqual(context, {"space_type": "VIEW_3D", "region_type": "WINDOW"})

        select = find_binding(data["items"], "view3d.select", "PRESS")
        self.assertIn(("deselect_all", True), select[2]["properties"])
        self.assertIn(("select_passthrough", True), select[2]["properties"])
        translate = find_binding(data["items"], "transform.translate", "CLICK_DRAG")
        box_select = find_binding(data["items"], "view3d.select_box", "CLICK_DRAG")
        self.assertLess(data["items"].index(select), data["items"].index(translate))
        self.assertLess(data["items"].index(translate), data["items"].index(box_select))

    def test_opt_in_is_limited_to_ios_primary_selection_keymaps(self) -> None:
        default_params = self.keymap.Params(select_mouse="LEFT")
        primary_items = self.keymap.km_3d_view_tool_select(
            default_params, fallback=False
        )[2]["items"]
        primary_box_items = self.keymap.km_3d_view_tool_select_box(
            default_params, fallback=False
        )[2]["items"]
        fallback_items = self.keymap.km_3d_view_tool_select(
            default_params, fallback=True
        )[2]["items"]

        self.assertFalse(any(item[0] == "transform.translate" for item in primary_items))
        self.assertFalse(any(item[0] == "transform.translate" for item in primary_box_items))
        find_binding(fallback_items, "transform.translate", "CLICK_DRAG")

        right_select_params = self.keymap.Params(
            select_mouse="RIGHT",
            use_v3d_tweak_drag_translate=True,
        )
        for keymap_factory in (
            self.keymap.km_3d_view_tool_select,
            self.keymap.km_3d_view_tool_select_box,
        ):
            right_select_items = keymap_factory(
                right_select_params, fallback=False
            )[2]["items"]
            self.assertFalse(any(item[0] == "transform.translate" for item in right_select_items))

        blender_keyconfig = BLENDER_KEYCONFIG.read_text()
        self.assertIn(
            'use_v3d_tweak_drag_translate=(platform == "ios")',
            blender_keyconfig,
        )


if __name__ == "__main__":
    unittest.main()
