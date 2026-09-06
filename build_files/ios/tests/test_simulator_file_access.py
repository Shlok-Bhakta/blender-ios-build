#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'simulator_file_access.py'
SPEC = importlib.util.spec_from_file_location('simulator_file_access', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SimulatorFileAccessTests(unittest.TestCase):
    def test_three_real_selections_precede_browser_close(self):
        flow = MODULE.maestro_flow()
        self.assertEqual(flow.count('point: 84%,29%'), 3)
        self.assertLess(flow.rindex('point: 84%,29%'), flow.rindex(MODULE.CLOSE_BUTTON_ID))
        self.assertIn('startRecording: blender-ios-file-access', flow)
        self.assertTrue(flow.endswith('- stopRecording\n'))

    def test_phone_uses_landscape_picker(self):
        flow = MODULE.maestro_flow(phone=True)
        self.assertIn('setOrientation: LANDSCAPE_LEFT', flow)
        self.assertEqual(flow.count('point: 94%,12%'), 3)

    def test_success_requires_bookmark_and_fresh_ticks_after_close(self):
        MODULE.validate_outcome({'ticks': 5},
                                {'ticks': 9, 'windows': 1, 'bookmarks': ['/external/folder/']},
                                Path('/external/folder'))

    def test_stalled_loop_fails_even_if_bookmark_exists(self):
        with self.assertRaisesRegex(MODULE.FileAccessFailure, 'main loop stopped'):
            MODULE.validate_outcome({'ticks': 5},
                                    {'ticks': 5, 'windows': 1, 'bookmarks': ['/external/folder/']},
                                    Path('/external/folder'))

    def test_missing_or_duplicate_bookmark_fails(self):
        for bookmarks in ([], ['/wrong/path'], ['/external/folder', '/external/folder/']):
            with self.subTest(bookmarks=bookmarks), self.assertRaisesRegex(
                    MODULE.FileAccessFailure, 'exactly once'):
                MODULE.validate_outcome({'ticks': 5},
                                        {'ticks': 9, 'windows': 1, 'bookmarks': bookmarks},
                                        Path('/external/folder'))

    def test_stuck_browser_fails_even_with_fresh_ticks(self):
        with self.assertRaisesRegex(MODULE.FileAccessFailure, 'did not close'):
            MODULE.validate_outcome({'ticks': 5},
                                    {'ticks': 9, 'windows': 2, 'bookmarks': ['/external/folder']},
                                    Path('/external/folder'))

    def test_probe_is_valid_python(self):
        compile(MODULE.state_source(Path('/tmp/test'), Path('/external/folder'),
                                    Path('/tmp/provider.dylib'), True), 'probe', 'exec')

    def test_device_reproduction_requires_callback_return_while_scope_is_stalled(self):
        source = Path(MODULE.__file__).read_text()

        self.assertIn('picker callback after tapping Open', source)
        self.assertIn('picker callback return while permission I/O is blocked', source)
        self.assertIn('folder selection blocked the picker in permission I/O', source)
        self.assertIn('folder selection released the document picker host', source)
        self.assertIn('folder picker copied instead of granting access', source)

    def test_external_folder_fixture_contains_many_nested_items(self):
        source = Path(MODULE.__file__).read_text()

        self.assertIn('for item_index in range(90)', source)
        self.assertIn('Nested', source)


if __name__ == '__main__':
    unittest.main()
