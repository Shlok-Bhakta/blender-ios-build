#!/usr/bin/env python3

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
PROPERTIES_SOURCE = (
    REPOSITORY / "intern" / "cycles" / "blender" / "addon" / "properties.py"
)


def load_defaults_module():
    tree = ast.parse(PROPERTIES_SOURCE.read_text())
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_should_use_metal_on_ios"
    )
    namespace = {}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(PROPERTIES_SOURCE), "exec"), namespace)
    return SimpleNamespace(should_use_metal=namespace["_should_use_metal_on_ios"])


class CyclesIOSDefaultsTests(unittest.TestCase):
    def test_real_ios_metal_device_selects_gpu_defaults(self) -> None:
        defaults = load_defaults_module()

        self.assertTrue(
            defaults.should_use_metal(
                "iOS",
                (("Apple GPU", "METAL", "METAL_Apple_GPU"), ("CPU", "CPU", "CPU")),
            )
        )

    def test_ios_without_usable_metal_device_stays_on_cpu(self) -> None:
        defaults = load_defaults_module()

        self.assertFalse(defaults.should_use_metal("iOS", (("CPU", "CPU", "CPU"),)))

    def test_non_ios_platforms_keep_upstream_defaults(self) -> None:
        defaults = load_defaults_module()

        self.assertFalse(
            defaults.should_use_metal("Darwin", (("Apple GPU", "METAL", "METAL_Apple_GPU"),))
        )

    def test_cycles_properties_use_the_conditional_ios_default(self) -> None:
        source = PROPERTIES_SOURCE.read_text()

        self.assertIn("IOS_USE_METAL_BY_DEFAULT", source)
        self.assertIn("default='GPU' if IOS_USE_METAL_BY_DEFAULT else 'CPU'", source)
        self.assertIn("if IOS_USE_METAL_BY_DEFAULT:", source)


if __name__ == "__main__":
    unittest.main()
