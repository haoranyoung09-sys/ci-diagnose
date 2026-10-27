"""Golden eval against fixture labels. Offline."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "eval_fixtures", ROOT / "scripts" / "eval_fixtures.py"
)
assert SPEC is not None and SPEC.loader is not None
eval_fixtures = importlib.util.module_from_spec(SPEC)
sys.modules["eval_fixtures"] = eval_fixtures
SPEC.loader.exec_module(eval_fixtures)


class EvalScriptTest(unittest.TestCase):
    def test_corpus_scores_perfect(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "eval_fixtures.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("accuracy: 73/73 (1.000)", completed.stdout)
        self.assertIn("mismatches: 0", completed.stdout)
        self.assertIn("offline: true", completed.stdout)
        self.assertNotIn("gh run view", completed.stdout)

    def test_summary_counts_an_off_diagonal(self) -> None:
        matrix = {
            label: {predicted: 0 for predicted in eval_fixtures.CATEGORIES}
            for label in eval_fixtures.CATEGORIES
        }
        matrix["test"]["test"] = 3
        matrix["test"]["flake"] = 1
        matrix["unknown"]["unknown"] = 2
        summary = eval_fixtures.summarize(matrix)
        self.assertEqual(summary["total"], 6)
        self.assertEqual(summary["correct"], 5)
        self.assertAlmostEqual(float(summary["accuracy"]), 5 / 6)


if __name__ == "__main__":
    unittest.main()
