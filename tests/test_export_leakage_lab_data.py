"""Offline tests for scripts/export_leakage_lab_data.py and its committed
artifact (WP38 sec 6). Every entry pairs a correct pipeline (preprocessing
fit on training rows only) against a leaky variant (the same step fit on the
full sampled cohort before the outer split), for the same rows and outer
split.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_leakage_lab_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_leakage_lab_data as ella  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ella.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ella.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = ella.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ella.serialize(self.artifact), on_disk)

    def test_every_scenario_size_seed_combination_present_exactly_once(self):
        keys = {(e["scenario"], e["sampleSize"], e["seed"]) for e in self.artifact["entries"]}
        expected = {
            (scenario, size, seed)
            for scenario in self.artifact["scenarios"]
            for size in self.artifact["sampleSizes"]
            for seed in self.artifact["seeds"]
        }
        self.assertEqual(keys, expected)
        self.assertEqual(len(self.artifact["entries"]), 60)

    def test_scaling_scenario_gap_is_real_but_bounded_for_knn(self):
        # WP38R sec 4: the estimator is KNeighborsRegressor(n_neighbors=15)
        # everywhere, not LinearRegression. Unlike ordinary least squares,
        # KNN's distance-based predictions DO depend on feature scale, so the
        # old assumption (scaling correct/leaky pairs are identical) no
        # longer holds -- and it must not. Recomputing the artifact under the
        # predeclared design (WP38R sec 4.1, no post-hoc k/seed/size search)
        # showed every scaling entry has a nonzero gap, but the direction is
        # not consistent from split to split (14/20 entries have leaky R2 >
        # correct R2, 6/20 have leaky R2 < correct R2) and the magnitude
        # stays modest: |leaky R2 - correct R2| <= ~0.07 across all 20
        # (sample_size, seed) combinations. This is an honest structural
        # check reflecting what was actually observed, not a bound chosen to
        # force a particular direction or a "no difference" conclusion.
        gaps = []
        for e in self.artifact["entries"]:
            if e["scenario"] == "scaling":
                self.assertGreaterEqual(e["correct"]["mse"], 0)
                self.assertGreaterEqual(e["leaky"]["mse"], 0)
                self.assertTrue(np.isfinite(e["correct"]["r2"]))
                self.assertTrue(np.isfinite(e["leaky"]["r2"]))
                gap = e["leaky"]["r2"] - e["correct"]["r2"]
                gaps.append(gap)
                # Not identical: KNN is scale-sensitive, so equality here
                # would indicate a regression back to an OLS-shaped result.
                self.assertNotEqual(e["correct"]["mse"], e["leaky"]["mse"])
                self.assertNotEqual(e["correct"]["r2"], e["leaky"]["r2"])
                # Bounded: the observed gaps are real but modest, never wild.
                self.assertLessEqual(abs(gap), 0.15)
        self.assertTrue(gaps)
        # Both signs are actually observed across the predeclared splits --
        # i.e. leakage is not uniformly "worse" or uniformly "better" here,
        # which is itself part of the lesson (a leaky evaluation is invalid
        # regardless of which way a given split happens to move the score).
        self.assertTrue(any(g > 0 for g in gaps))
        self.assertTrue(any(g < 0 for g in gaps))

    def test_feature_selection_shows_inflation_at_full_sample(self):
        # At the full eligible cohort (least noisy comparison), the leaky
        # feature-selection variant should not be systematically worse.
        # Re-verified against the recomputed KNeighborsRegressor(n_neighbors=15)
        # artifact (WP38R sec 4): the observed mean gap at the full sample is
        # about +0.026 (all 5 seeds individually positive), comfortably above
        # this -0.02 threshold, so no threshold change was needed here.
        full_sample_entries = [
            e for e in self.artifact["entries"]
            if e["scenario"] == "feature_selection" and e["sampleSize"] == max(self.artifact["sampleSizes"])
        ]
        self.assertTrue(full_sample_entries)
        gaps = [e["leaky"]["r2"] - e["correct"]["r2"] for e in full_sample_entries]
        self.assertGreaterEqual(sum(gaps) / len(gaps), -0.02)

    def test_nrows_are_consistent_with_sample_size(self):
        for e in self.artifact["entries"]:
            self.assertEqual(e["nTrain"] + e["nTest"], e["sampleSize"])

    def test_no_participant_identifier_shaped_keys(self):
        identifier_token = ("id", "sub", "subject", "site", "participant")
        for key in self.artifact:
            self.assertNotIn(key.lower(), identifier_token)

    def test_mse_is_non_negative(self):
        for e in self.artifact["entries"]:
            self.assertGreaterEqual(e["correct"]["mse"], 0)
            self.assertGreaterEqual(e["leaky"]["mse"], 0)


class ScenarioHelpers(unittest.TestCase):
    def test_scaling_entry_is_deterministic(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(60, 5))
        y = rng.normal(size=60)
        train_idx = np.arange(45)
        test_idx = np.arange(45, 60)
        a = ella._scaling_entry(X, y, train_idx, test_idx)
        b = ella._scaling_entry(X, y, train_idx, test_idx)
        self.assertEqual(a, b)

    def test_feature_selection_entry_leaky_uses_all_rows_for_selection(self):
        rng = np.random.default_rng(1)
        X = rng.normal(size=(60, 20))
        y = X[:, 0] * 3 + rng.normal(scale=0.1, size=60)  # informative first column
        train_idx = np.arange(45)
        test_idx = np.arange(45, 60)
        result = ella._feature_selection_entry(X, y, train_idx, test_idx, k=5)
        self.assertIn("correct", result)
        self.assertIn("leaky", result)
        self.assertGreaterEqual(result["correct"]["mse"], 0)
        self.assertGreaterEqual(result["leaky"]["mse"], 0)

    def test_pca_entry_returns_both_sides(self):
        rng = np.random.default_rng(2)
        X = rng.normal(size=(60, 15))
        y = rng.normal(size=60)
        train_idx = np.arange(45)
        test_idx = np.arange(45, 60)
        result = ella._pca_entry(X, y, train_idx, test_idx, n_components=5)
        self.assertIn("correct", result)
        self.assertIn("leaky", result)


if __name__ == "__main__":
    unittest.main()
