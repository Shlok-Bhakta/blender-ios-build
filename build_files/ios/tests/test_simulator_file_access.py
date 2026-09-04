#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY / "build_files" / "ios" / "simulator_file_access.py"
SPEC = importlib.util.spec_from_file_location("simulator_file_access", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SimulatorFileAccessTests(unittest.TestCase):
    def test_flow_opens_file_browser_before_requesting_a_native_folder(self) -> None:
        flow = MODULE.maestro_flow()

        close_visible = flow.index(f"id: {MODULE.CLOSE_BUTTON_ID}")
        add_visible = flow.index(f"id: {MODULE.ADD_LOCATION_BUTTON_ID}")
        add_tap = flow.index(f"id: {MODULE.ADD_LOCATION_BUTTON_ID}", add_visible + 1)
        picker_visible = flow.index("visible: Cancel")

        self.assertLess(close_visible, add_visible)
        self.assertLess(add_visible, add_tap)
        self.assertLess(add_tap, picker_visible)

    def test_flow_captures_the_native_picker(self) -> None:
        flow = MODULE.maestro_flow()

        self.assertIn("startRecording: blender-ios-file-access", flow)
        self.assertIn("takeScreenshot: blender-ios-folder-picker", flow)
        self.assertIn("stopRecording", flow)
        self.assertNotIn("tapOn: Cancel", flow)


if __name__ == "__main__":
    unittest.main()
