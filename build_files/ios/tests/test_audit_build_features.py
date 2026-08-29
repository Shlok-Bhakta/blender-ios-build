# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


AUDITOR = Path(__file__).resolve().parents[1] / "audit_build_features.py"


class BuildFeatureAuditTests(unittest.TestCase):
    def run_audit(self, contents: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "Blender"
            executable.write_bytes(contents)
            return subprocess.run(
                [sys.executable, str(AUDITOR), str(executable), "--require-opensubdiv"],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_accepts_executable_with_opensubdiv_runtime(self) -> None:
        result = self.run_audit(
            b"bpy.app.opensubdiv\0OpenSubdiv library information backend\0"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_executable_with_disabled_modifier_branch(self) -> None:
        result = self.run_audit(
            b"bpy.app.opensubdiv\0OpenSubdiv library information backend\0"
            b"Disabled, built without OpenSubdiv\0"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("disabled modifier branch", result.stdout + result.stderr)

    def test_rejects_executable_without_opensubdiv_runtime(self) -> None:
        result = self.run_audit(b"Blender\0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing OpenSubdiv marker", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
