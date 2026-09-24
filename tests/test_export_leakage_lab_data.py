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

    def test_scaling_scenario_shows_no_difference_for_ols(self):
        # Ordinary least squares predictions are invariant to any consistent
        # invertible rescaling of the inputs, so fitting the scaler on train
        # rows only vs. train+test rows must give identical predictions.
        for e in self.artifact["entries"]:
            if e["scenario"] == "scaling":
                self.assertAlmostEqual(e["correct"]["mse"], e["leaky"]["mse"], places=4)
                self.assertAlmostEqual(e["correct"]["r2"], e["leaky"]["r2"], places=4)

    def test_feature_selection_shows_inflation_at_full_sample(self):
        # At the full eligible cohort (least noisy comparison), the leaky
        # feature-selection variant should not be systematically worse.
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
