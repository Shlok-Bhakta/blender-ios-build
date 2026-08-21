# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import tempfile
import unittest

from build_files.ios.configure_python_cross_venv import (
    localized_build_time_vars,
    target_names,
    write_wrapper,
)


class PythonCrossEnvironmentTests(unittest.TestCase):
    def test_device_and_simulator_target_names_are_distinct(self) -> None:
        self.assertEqual(
            target_names("iphoneos", "arm64", "18.0"),
            ("arm64-iphoneos", "ios-18.0-arm64-iphoneos", "arm64-apple-ios18.0"),
        )
        self.assertEqual(
            target_names("iphonesimulator", "arm64", "18.0"),
            (
                "arm64-iphonesimulator",
                "ios-18.0-arm64-iphonesimulator",
                "arm64-apple-ios18.0-simulator",
            ),
        )

    def test_sysconfig_paths_and_tools_are_localized(self) -> None:
        original = {
            "prefix": "/build/python",
            "INCLUDEPY": "/build/python/include/python3.13",
            "LDSHARED": "clang -dynamiclib -F . -framework Python",
        }
        wrappers = {
            name: Path(f"/venv/bin/{name}")
            for name in ("ar", "clang", "clang++", "ranlib", "strip")
        }
        localized = localized_build_time_vars(original, Path("/target/python"), wrappers)
        self.assertEqual(localized["INCLUDEPY"], "/target/python/include/python3.13")
        self.assertIn("-F /target/python", localized["LDSHARED"])
        self.assertEqual(localized["CC"], "/venv/bin/clang")

    def test_compiler_wrapper_pins_sdk_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wrapper = Path(directory) / "clang"
            write_wrapper(wrapper, "iphoneos", "clang", "arm64-apple-ios18.0")
            source = wrapper.read_text(encoding="utf-8")
            self.assertIn("/usr/bin/xcrun --sdk iphoneos clang", source)
            self.assertIn("-target arm64-apple-ios18.0", source)
            self.assertTrue(wrapper.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
