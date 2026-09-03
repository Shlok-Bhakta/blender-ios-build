#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "build_files/ios/simulator_window_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("simulator_window_lifecycle", MODULE_PATH)
assert SPEC and SPEC.loader
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)


class SimulatorWindowLifecycleTests(unittest.TestCase):
    def test_driver_waits_for_fresh_main_loop_ticks_between_render_windows(self) -> None:
        source = lifecycle.lifecycle_source(Path("/tmp/window-lifecycle"))

        self.assertIn("render_display_type = 'WINDOW'", source)
        self.assertIn("bpy.ops.render.render('INVOKE_DEFAULT')", source)
        self.assertIn(f"< {lifecycle.MAIN_LOOP_SETTLE_TICKS}", source)
        self.assertIn("marker.write_text('PASS')", source)
        compile(source, "ios_window_lifecycle", "exec")

    def test_driver_covers_blenders_parentless_main_window_path(self) -> None:
        source = lifecycle.lifecycle_source(Path("/tmp/window-lifecycle"), "main")

        self.assertIn("bpy.ops.wm.window_new_main()", source)
        self.assertNotIn("bpy.ops.render.render", source)

    def test_flow_closes_three_distinct_native_windows(self) -> None:
        flow = lifecycle.maestro_flow()

        self.assertEqual(flow.count("- tapOn:"), lifecycle.WINDOW_CYCLES)
        self.assertEqual(flow.count("    visible:"), lifecycle.WINDOW_CYCLES)
        self.assertEqual(flow.count("    notVisible:"), lifecycle.WINDOW_CYCLES)
        self.assertEqual(flow.count(lifecycle.CLOSE_BUTTON_ID), lifecycle.WINDOW_CYCLES * 3)


if __name__ == "__main__":
    unittest.main()
