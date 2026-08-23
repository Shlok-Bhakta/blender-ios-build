#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "build_files/ios/simulator_memory_soak.py"
SPEC = importlib.util.spec_from_file_location("simulator_memory_soak", MODULE_PATH)
assert SPEC and SPEC.loader
soak = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(soak)


class SimulatorMemorySoakTests(unittest.TestCase):
    def test_plateau_accepts_bounded_warm_memory(self) -> None:
        samples = [410_000, 430_000, 438_000, 441_000, 440_500, 441_200]
        result = soak.analyze_samples(samples, max_growth_kib=16_384, max_slope_kib=1_024)

        self.assertEqual(result.growth_kib, 3_200)
        self.assertLess(result.slope_kib_per_sample, 1_024)

    def test_plateau_rejects_sustained_growth(self) -> None:
        samples = [400_000, 420_000, 440_000, 460_000, 480_000, 500_000]

        with self.assertRaisesRegex(soak.SoakFailure, "sustained memory growth"):
            soak.analyze_samples(samples, max_growth_kib=32_768, max_slope_kib=8_192)

    def test_analysis_requires_enough_samples(self) -> None:
        with self.assertRaisesRegex(soak.SoakFailure, "at least six"):
            soak.analyze_samples([1, 2, 3], max_growth_kib=10, max_slope_kib=10)

    def test_stable_simulator_metal_roots_are_classified_as_platform_cache(self) -> None:
        report = """Process 42: 144 leaks for 19584 total leaked bytes.
      12 (1.61K) ROOT LEAK: <_MTLFunctionInternal 0x123> [448]
"""
        baseline = soak.parse_leak_report(report)
        final = soak.parse_leak_report(report)

        result = soak.analyze_leak_scans(baseline, final)

        self.assertEqual(result.root_types, ("_MTLFunctionInternal",))
        self.assertEqual(result.growth_bytes, 0)

    def test_new_or_application_owned_leaks_fail_the_soak(self) -> None:
        baseline = soak.parse_leak_report(
            "0 leaks for 0 total leaked bytes.\n"
        )
        final = soak.parse_leak_report(
            "1 leak for 64 total leaked bytes.\n"
            "1 (64 bytes) ROOT LEAK: <GHOSTLeakedObject 0x123> [64]\n"
        )

        with self.assertRaisesRegex(soak.SoakFailure, "application-owned"):
            soak.analyze_leak_scans(baseline, final)


if __name__ == "__main__":
    unittest.main()
