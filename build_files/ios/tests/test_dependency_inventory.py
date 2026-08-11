# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import unittest

from build_files.ios.inventory_dependencies import parse_ninja_graph, transitive_dependencies


class DependencyInventoryTests(unittest.TestCase):
    def test_parses_public_targets_and_order_only_edges(self) -> None:
        graph = parse_ninja_graph(
            """\
build external_zlib: phony CMakeFiles/external_zlib
build CMakeFiles/external_zlib | ${cmake_ninja_workdir}CMakeFiles/external_zlib: phony complete
build external_png: phony CMakeFiles/external_png
build CMakeFiles/external_png | ${cmake_ninja_workdir}CMakeFiles/external_png: phony complete || external_zlib
"""
        )
        self.assertEqual(graph, {"external_png": ["external_zlib"], "external_zlib": []})

    def test_computes_transitive_dependencies(self) -> None:
        graph = {"external_a": ["external_b"], "external_b": ["external_c"], "external_c": []}
        self.assertEqual(transitive_dependencies(graph, "external_a"), ["external_b", "external_c"])


if __name__ == "__main__":
    unittest.main()
