"""Offline tests for Exercise 9's instructor/reference full-training-data
SVR benchmark (WP52 item 13).

scripts/compute_exercise_09_svr_benchmark.py computes this number OFFLINE,
on the full 753-row training partition (never the student's own 300-row
SVR-activity subset), with a configuration chosen before any validation
score was seen. scripts/generate_exercise_09_notebook.py reads the
committed JSON artifact this script writes and embeds it, explicitly
labeled, into Section 6's comparison -- this file checks that artifact
stays internally consistent and in sync with a fresh recomputation.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_svr_benchmark.py'
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_svr_benchmark.json"


class BenchmarkArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = json.loads(BENCHMARK_PATH.read_text())

    def test_artifact_is_up_to_date(self):
        proc = subprocess.run(
            [sys.executable, "scripts/compute_exercise_09_svr_benchmark.py", "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_split_matches_every_other_model_in_the_notebook(self):
        split = self.benchmark["split"]
        self.assertEqual(split["test_size"], 0.25)
        self.assertEqual(split["random_state"], 42)
        self.assertEqual(split["stratify"], "group")

    def test_row_and_feature_counts(self):
        self.assertEqual(self.benchmark["n_train"], 753)
        self.assertEqual(self.benchmark["n_val"], 251)
        self.assertEqual(self.benchmark["n_features"], 360)

    def test_not_tuned_against_validation(self):
        self.assertTrue(self.benchmark["params_chosen_without_validation_tuning"])

    def test_params_are_plain_library_defaults(self):
        # The whole point: a configuration decided before any validation
        # score existed. Plain SVR() defaults are the simplest such choice.
        params = self.benchmark["params"]
        self.assertEqual(params["kernel"], "rbf")
        self.assertEqual(params["C"], 1.0)
        self.assertEqual(params["gamma"], "scale")
        self.assertEqual(params["epsilon"], 0.1)

    def test_scores_are_plausible_and_not_suspiciously_perfect(self):
        # A real, honestly-reported number -- not required to beat every
        # other method (and in fact it does not; see WP52_REPORT.md).
        self.assertGreater(self.benchmark["val_mse"], 0)
        self.assertLess(self.benchmark["val_r2"], 1.0)
        self.assertGreater(self.benchmark["val_r2"], -1.0)

    def test_description_distinguishes_it_from_the_student_subset_and_the_old_summary(self):
        text = self.benchmark["description"].lower()
        self.assertIn("instructor", text)
        self.assertIn("not the student's own", text)
        self.assertIn("not the old pre-migration nested-cv summary", text)


if __name__ == "__main__":
    unittest.main()
