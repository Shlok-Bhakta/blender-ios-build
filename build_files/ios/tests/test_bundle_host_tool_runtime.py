# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from build_files.ios import bundle_host_tool_runtime as runtime


class BundleHostToolRuntimeTests(unittest.TestCase):
    def test_parses_otool_dependency_lines(self) -> None:
        output = """/tmp/makesdna:
\t@rpath/libOpenImageIO.dylib (compatibility version 3.1.0, current version 3.1.13)
\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
"""
        self.assertEqual(
            runtime.parse_otool_libraries(output),
            ("@rpath/libOpenImageIO.dylib", "/usr/lib/libSystem.B.dylib"),
        )

    def test_bundles_the_recursive_non_system_dependency_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tool = root / "tools/makesdna"
            first = root / "libraries/openimageio/lib/libOpenImageIO.dylib"
            second = root / "libraries/imath/lib/libImath.dylib"
            for item in (tool, first, second):
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_bytes(item.name.encode())

            dependencies = {
                "makesdna": (
                    "@rpath/libOpenImageIO.dylib",
                    "/usr/lib/libSystem.B.dylib",
                ),
                "libOpenImageIO.dylib": ("@rpath/libImath.dylib",),
                "libImath.dylib": ("@rpath/libImath.dylib",),
            }
            destination = root / "bundle"
            with mock.patch.object(
                runtime,
                "linked_libraries",
                side_effect=lambda binary: dependencies[binary.name],
            ):
                bundled = runtime.bundle_runtime(
                    (tool,),
                    root / "libraries",
                    destination,
                )

            self.assertEqual(
                bundled,
                (destination / "libImath.dylib", destination / "libOpenImageIO.dylib"),
            )
            self.assertEqual((destination / first.name).read_bytes(), first.read_bytes())
            self.assertEqual((destination / second.name).read_bytes(), second.read_bytes())

    def test_rejects_an_unhydrated_lfs_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tool = root / "makesdna"
            library = root / "libraries/openimageio/lib/libOpenImageIO.dylib"
            tool.write_bytes(b"tool")
            library.parent.mkdir(parents=True)
            library.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:test\n")

            with mock.patch.object(
                runtime,
                "linked_libraries",
                return_value=("@rpath/libOpenImageIO.dylib",),
            ):
                with self.assertRaisesRegex(RuntimeError, "unhydrated LFS"):
                    runtime.bundle_runtime((tool,), root / "libraries", root / "bundle")


if __name__ == "__main__":
    unittest.main()
