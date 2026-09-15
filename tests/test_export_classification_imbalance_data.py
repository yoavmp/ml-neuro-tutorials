"""Offline tests for scripts/export_classification_imbalance_data.py and its
committed artifact (WP18 sec 4, sec 9). WP17's unstratified comparison side
is gone: every entry now carries one stratified split's metrics directly
(accuracy, majority baseline, AUC, balanced accuracy, sensitivity,
specificity), all using the SAME C selected honestly once on the canonical
Section 3 split.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_classification_imbalance_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_classification_imbalance_data as ecid  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ecid.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ecid.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = ecid.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ecid.serialize(self.artifact), on_disk)

    def test_every_ratio_seed_combination_present_exactly_once(self):
        pairs = {(e["ratioKey"], e["seed"]) for e in self.artifact["entries"]}
        expected = {
            (r["key"], s)
            for r in self.artifact["ratios"]
            for s in self.artifact["splitSeeds"]
        }
        self.assertEqual(pairs, expected)

    def test_majority_is_control_minority_is_autism(self):
        self.assertEqual(self.artifact["majorityClass"], "control")
        self.assertEqual(self.artifact["minorityClass"], "autism")

    def test_no_stratified_unstratified_split_anymore(self):
        for e in self.artifact["entries"]:
            self.assertNotIn("stratified", e)
            self.assertNotIn("unstratified", e)
            for field in (
                "accuracy", "majorityBaselineAccuracy", "auc", "balancedAccuracy",
                "sensitivity", "specificity", "confusionMatrix",
                "nTrainMajority", "nTrainMinority", "nTestMajority", "nTestMinority",
            ):
                self.assertIn(field, e)

    def test_same_selected_c_used_throughout(self):
        self.assertIn("selectedC", self.artifact)
        self.assertIn(f"C={self.artifact['selectedC']!r}", self.artifact["model"])

    def test_stratified_counts_approximate_the_ratio(self):
        for e in self.artifact["entries"]:
            ratio = next(r for r in self.artifact["ratios"] if r["key"] == e["ratioKey"])
            n_train = e["nTrainMajority"] + e["nTrainMinority"]
            observed_majority_frac = e["nTrainMajority"] / n_train
            # integer rounding on small counts (e.g. 95:5 with n_train=300)
            self.assertAlmostEqual(observed_majority_frac, ratio["majorityPct"], delta=0.03)

    def test_no_participant_identifier_shaped_keys(self):
        identifier_token = ("id", "sub", "subject", "site", "participant")
        for key in self.artifact:
            self.assertNotIn(key.lower(), identifier_token)

    def test_95_5_is_meaningfully_sparse(self):
        entries_95_5 = [e for e in self.artifact["entries"] if e["ratioKey"] == "95:5"]
        self.assertTrue(entries_95_5)
        for e in entries_95_5:
            self.assertEqual(e["cohort"]["nMinority"], 20)

    def test_95_5_auc_is_always_defined_never_undefined(self):
        # WP18 sec 4: no one-class test partition / undefined-AUC case remains
        # in this activity's data (N=400 makes 95:5's ~5-participant stratified
        # test minority always non-empty).
        for e in self.artifact["entries"]:
            self.assertIsInstance(e["auc"], (int, float))
            self.assertGreaterEqual(e["auc"], 0.0)
            self.assertLessEqual(e["auc"], 1.0)

    def test_majority_baseline_accuracy_reflects_the_majority_class(self):
        for e in self.artifact["entries"]:
            n_test = e["nTestMajority"] + e["nTestMinority"]
            expected = max(e["nTestMajority"], e["nTestMinority"]) / n_test
            self.assertAlmostEqual(e["majorityBaselineAccuracy"], expected, places=6)

    def test_balanced_accuracy_is_mean_of_sensitivity_and_specificity(self):
        for e in self.artifact["entries"]:
            expected = round((e["sensitivity"] + e["specificity"]) / 2, 6)
            self.assertAlmostEqual(e["balancedAccuracy"], expected, places=6)

    def test_95_5_majority_baseline_is_95_percent(self):
        for e in self.artifact["entries"]:
            if e["ratioKey"] == "95:5":
                self.assertAlmostEqual(e["majorityBaselineAccuracy"], 0.95, delta=0.02)


class ResampleCohort(unittest.TestCase):
    def test_resample_is_deterministic_for_a_fixed_seed(self):
        y = np.array([0] * 100 + [1] * 100)
        X = np.arange(200).reshape(200, 1).astype(float)
        ratio = {"key": "70:30", "majorityPct": 0.70, "minorityPct": 0.30}
        a = ecid._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        b = ecid._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])

    def test_resample_honours_the_requested_ratio_counts(self):
        y = np.array([0] * 100 + [1] * 100)
        X = np.arange(200).reshape(200, 1).astype(float)
        ratio = {"key": "95:5", "majorityPct": 0.95, "minorityPct": 0.05}
        X_cohort, y_cohort, n_majority, n_minority = ecid._resample_cohort(X, y, ratio, cohort_size=40, seed=1)
        self.assertEqual(n_majority, 38)
        self.assertEqual(n_minority, 2)
        self.assertEqual(int(np.sum(y_cohort == 0)), 38)
        self.assertEqual(int(np.sum(y_cohort == 1)), 2)

    def test_raises_when_the_pool_cannot_supply_the_requested_count(self):
        y = np.array([0] * 5 + [1] * 5)
        X = np.arange(10).reshape(10, 1).astype(float)
        ratio = {"key": "95:5", "majorityPct": 0.95, "minorityPct": 0.05}
        with self.assertRaises(RuntimeError):
            ecid._resample_cohort(X, y, ratio, cohort_size=40, seed=1)


class EvalSplit(unittest.TestCase):
    def test_two_class_test_partition_reports_a_real_auc_and_balanced_accuracy(self):
        rng = np.random.default_rng(0)
        X_train = rng.normal(size=(40, 3))
        y_train = np.array([0] * 20 + [1] * 20)
        X_test = rng.normal(size=(10, 3))
        y_test = np.array([0] * 5 + [1] * 5)

        result = ecid._eval_split(X_train, y_train, X_test, y_test, C=1.0)
        self.assertGreaterEqual(result["auc"], 0.0)
        self.assertLessEqual(result["auc"], 1.0)
        expected_balanced = round((result["sensitivity"] + result["specificity"]) / 2, 6)
        self.assertAlmostEqual(result["balancedAccuracy"], expected_balanced, places=6)

    def test_one_class_test_partition_raises(self):
        rng = np.random.default_rng(0)
        X_train = rng.normal(size=(40, 3))
        y_train = np.array([0] * 20 + [1] * 20)
        X_test = rng.normal(size=(6, 3))
        y_test = np.zeros(6, dtype=int)  # only the majority class in the test partition

        with self.assertRaises(RuntimeError):
            ecid._eval_split(X_train, y_train, X_test, y_test, C=1.0)


if __name__ == "__main__":
    unittest.main()
