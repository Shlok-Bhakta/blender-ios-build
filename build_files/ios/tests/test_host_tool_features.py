# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
FEATURE_MODULE = REPOSITORY / "build_files" / "cmake" / "host_tool_features.cmake"


class HostToolFeatureTests(unittest.TestCase):
    def run_validation(self, manifest: str, *, python_enabled: bool) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            manifest_path = temporary / "makesrna.features"
            manifest_path.write_text(manifest)
            driver_path = temporary / "validate.cmake"
            driver_path.write_text(
                textwrap.dedent(
                    f"""
                    include(\"{FEATURE_MODULE}\")
                    foreach(feature IN LISTS BLENDER_HOST_TOOL_FEATURES)
                      set(${{feature}} OFF)
                    endforeach()
                    set(WITH_PYTHON {'ON' if python_enabled else 'OFF'})
                    blender_validate_host_tool_features(\"{manifest_path}\")
                    """
                )
            )
            return subprocess.run(
                ["cmake", "-P", str(driver_path)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_matching_manifest_is_accepted(self) -> None:
        module_text = FEATURE_MODULE.read_text()
        feature_block = re.search(
            r"set\(BLENDER_HOST_TOOL_FEATURES(?P<features>.*?)\)",
            module_text,
            re.DOTALL,
        )
        self.assertIsNotNone(feature_block)
        features = {
            feature: "OFF"
            for feature in re.findall(r"\bWITH_[A-Z0-9_]+\b", feature_block["features"])
        }
        features["WITH_PYTHON"] = "ON"
        manifest = "schema=1\n" + "".join(
            f"{name}={value}\n" for name, value in features.items()
        )
        result = self.run_validation(manifest, python_enabled=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_python_mismatch_is_rejected_with_rebuild_direction(self) -> None:
        result = self.run_validation(
            "schema=1\nWITH_PYTHON=OFF\n",
            python_enabled=True,
        )
        self.assertNotEqual(result.returncode, 0)
        output = result.stdout + result.stderr
        self.assertIn("WITH_PYTHON", output)
        self.assertIn("Rebuild the native host tools", output)

    def test_missing_manifest_is_rejected(self) -> None:
        result = self.run_validation("schema=1\n", python_enabled=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing feature", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
