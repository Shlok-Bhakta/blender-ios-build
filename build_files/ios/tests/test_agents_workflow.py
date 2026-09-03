#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
AGENTS = REPOSITORY / "AGENTS.md"


class AgentWorkflowTests(unittest.TestCase):
    def test_agents_require_observed_red_green_regression_coverage(self) -> None:
        guidance = AGENTS.read_text()
        guidance_lower = guidance.lower()

        self.assertIn("Observe the regression fail before changing production code", guidance)
        self.assertIn("highest honest test layer", guidance)
        self.assertIn("Source-text assertions are supporting checks", guidance)
        self.assertIn("run the same reproduction again", guidance_lower)

    def test_agents_require_a_true_stacked_pr(self) -> None:
        guidance = AGENTS.read_text()

        self.assertIn("one change per stacked PR", guidance)
        self.assertIn("base the new PR on the previous PR branch", guidance)
        self.assertIn("Do not create a GitHub issue unless the user asks", guidance)
        self.assertIn("Use a `story/`, `feat/`, or `refactor/` branch", guidance)

    def test_agents_require_one_silent_ci_watcher(self) -> None:
        guidance = AGENTS.read_text()

        self.assertIn("gh run watch <run-id>", guidance)
        self.assertIn("--interval 1800 --exit-status", guidance)
        self.assertIn("Do not poll CI in a loop", guidance)


if __name__ == "__main__":
    unittest.main()
