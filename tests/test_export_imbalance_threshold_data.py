"""Offline tests for scripts/export_imbalance_threshold_data.py and its
committed artifact (WP38 sec 9). Ships only fixed predicted probabilities
and true labels for a fixed 90:10 cohort; the browser recomputes confusion
matrix / metrics at any threshold client-side, never refitting.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_imbalance_threshold_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_imbalance_threshold_data as eitd  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(eitd.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = eitd.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = eitd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(eitd.serialize(self.artifact), on_disk)

    def test_ratio_is_90_10(self):
        self.assertEqual(self.artifact["ratioKey"], "90:10")
        self.assertEqual(self.artifact["cohort"]["nMajority"], 360)
        self.assertEqual(self.artifact["cohort"]["nMinority"], 40)

    def test_majority_baseline_is_90_percent(self):
        self.assertAlmostEqual(self.artifact["majorityBaselineAccuracy"], 0.9, delta=0.02)

    def test_pr_auc_baseline_equals_positive_prevalence(self):
        self.assertAlmostEqual(self.artifact["positivePrevalence"], 0.1, delta=0.02)

    def test_both_models_share_identical_test_labels(self):
        # Both models are scored on the same locked test partition.
        n_test = len(self.artifact["testLabels"])
        for key in ("ordinary", "classWeighted"):
            self.assertEqual(len(self.artifact["models"][key]["predictedProbaPositive"]), n_test)

    def test_same_c_used_for_both_models(self):
        self.assertIn(f"C={self.artifact['modelC']!r}", self.artifact["models"]["ordinary"]["model"])
        self.assertIn(f"C={self.artifact['modelC']!r}", self.artifact["models"]["classWeighted"]["model"])

    def test_class_weighted_model_declares_balanced_weighting(self):
        self.assertIn("class_weight='balanced'", self.artifact["models"]["classWeighted"]["model"])
        self.assertNotIn("class_weight", self.artifact["models"]["ordinary"]["model"])

    def test_roc_and_pr_auc_are_probabilities(self):
        for key in ("ordinary", "classWeighted"):
            self.assertGreaterEqual(self.artifact["models"][key]["rocAuc"], 0.0)
            self.assertLessEqual(self.artifact["models"][key]["rocAuc"], 1.0)
            self.assertGreaterEqual(self.artifact["models"][key]["prAuc"], 0.0)
            self.assertLessEqual(self.artifact["models"][key]["prAuc"], 1.0)

    def test_no_participant_identifier_shaped_keys(self):
        identifier_token = ("id", "sub", "subject", "site", "participant")
        for key in self.artifact:
            self.assertNotIn(key.lower(), identifier_token)


class ResampleCohort(unittest.TestCase):
    def test_resample_is_deterministic(self):
        import numpy as np

        y = np.array([0] * 100 + [1] * 100)
        X = np.arange(200).reshape(200, 1).astype(float)
        ratio = {"key": "90:10", "majorityPct": 0.9, "minorityPct": 0.1}
        a = eitd._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        b = eitd._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])


if __name__ == "__main__":
    unittest.main()
