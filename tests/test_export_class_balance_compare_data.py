"""Offline tests for scripts/export_class_balance_compare_data.py and its
committed artifact (WP38R sec 5). Compares ordinary vs class_weight="balanced"
logistic regression across five class balances (50:50 through 90:10) at a
FIXED decision threshold of 0.5 -- there is no threshold sweep and no raw
predicted-probability array in this artifact (contrast with the removed
``export_imbalance_threshold_data.py``).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_class_balance_compare_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_class_balance_compare_data as ecbcd  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ecbcd.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ecbcd.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = ecbcd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ecbcd.serialize(self.artifact), on_disk)

    def test_exactly_five_ratio_keys_in_order(self):
        keys = [r["key"] for r in self.artifact["ratios"]]
        self.assertEqual(keys, ["50:50", "60:40", "70:30", "80:20", "90:10"])
        entry_keys = [e["ratioKey"] for e in self.artifact["entries"]]
        self.assertEqual(sorted(entry_keys), sorted(keys))

    def test_95_5_is_absent(self):
        keys = [r["key"] for r in self.artifact["ratios"]]
        self.assertNotIn("95:5", keys)
        entry_keys = [e["ratioKey"] for e in self.artifact["entries"]]
        self.assertNotIn("95:5", entry_keys)
        raw_text = ecbcd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("95:5", raw_text)

    def test_both_models_present_for_every_ratio(self):
        for e in self.artifact["entries"]:
            self.assertIn("ordinary", e["models"])
            self.assertIn("classWeighted", e["models"])

    def test_confusion_matrices_are_internally_consistent(self):
        for e in self.artifact["entries"]:
            n_test = e["nTestMajority"] + e["nTestMinority"]
            for key in ("ordinary", "classWeighted"):
                cm = e["models"][key]["confusionMatrix"]
                self.assertEqual(cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"], n_test)
                expected_acc = (cm["tn"] + cm["tp"]) / n_test
                self.assertAlmostEqual(e["models"][key]["accuracy"], expected_acc, places=6)

    def test_majority_baseline_matches_recomputed_value_every_ratio(self):
        for e in self.artifact["entries"]:
            n_test = e["nTestMajority"] + e["nTestMinority"]
            expected = max(e["nTestMajority"], e["nTestMinority"]) / n_test
            for key in ("ordinary", "classWeighted"):
                self.assertAlmostEqual(
                    e["models"][key]["majorityBaselineAccuracy"], expected, places=6,
                    msg=f"{e['ratioKey']}/{key}",
                )

    def test_pr_auc_baseline_equals_minority_prevalence_every_ratio(self):
        for e in self.artifact["entries"]:
            n_test = e["nTestMajority"] + e["nTestMinority"]
            expected = e["nTestMinority"] / n_test
            for key in ("ordinary", "classWeighted"):
                self.assertAlmostEqual(
                    e["models"][key]["prAucBaseline"], expected, places=6,
                    msg=f"{e['ratioKey']}/{key}",
                )

    def test_baselines_identical_across_models_within_a_ratio(self):
        # Both models share the same cohort/split/test partition, so these two
        # baselines cannot differ by model -- only by ratio.
        for e in self.artifact["entries"]:
            o = e["models"]["ordinary"]
            w = e["models"]["classWeighted"]
            self.assertEqual(o["majorityBaselineAccuracy"], w["majorityBaselineAccuracy"])
            self.assertEqual(o["prAucBaseline"], w["prAucBaseline"])

    def test_model_c_fixed_at_one(self):
        self.assertEqual(self.artifact["modelC"], 1.0)
        self.assertIn("C=1.0", self.artifact["modelOrdinary"])
        self.assertIn("C=1.0", self.artifact["modelClassWeighted"])

    def test_class_weighted_model_declares_balanced_weighting(self):
        self.assertIn("class_weight='balanced'", self.artifact["modelClassWeighted"])
        self.assertNotIn("class_weight", self.artifact["modelOrdinary"])

    def test_no_threshold_or_probability_fields_shipped(self):
        # This activity fixes the decision threshold at 0.5 (.predict()) and
        # ships only aggregated metrics -- no raw predicted-probability
        # arrays and no threshold field anywhere in the artifact.
        raw_text = ecbcd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("predictedProbaPositive", raw_text)
        self.assertNotIn("threshold", raw_text.lower())

    def test_roc_and_pr_auc_are_probabilities(self):
        for e in self.artifact["entries"]:
            for key in ("ordinary", "classWeighted"):
                m = e["models"][key]
                self.assertGreaterEqual(m["rocAuc"], 0.0)
                self.assertLessEqual(m["rocAuc"], 1.0)
                self.assertGreaterEqual(m["prAuc"], 0.0)
                self.assertLessEqual(m["prAuc"], 1.0)

    def test_class_weighted_recall_never_below_ordinary(self):
        # Verified directly from the committed artifact (WP38R sec 5): at
        # every one of the five balance levels, class-weighted recall is
        # greater than or equal to ordinary recall. This is a fact about this
        # one cohort/split, not a general claim -- other metrics (accuracy,
        # balanced accuracy at 90:10) do NOT consistently favor either model,
        # and this test does not assert anything about them.
        for e in self.artifact["entries"]:
            o = e["models"]["ordinary"]["recall"]
            w = e["models"]["classWeighted"]["recall"]
            self.assertGreaterEqual(w, o, msg=f"{e['ratioKey']}: classWeighted recall {w} < ordinary recall {o}")

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
        a = ecbcd._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        b = ecbcd._resample_cohort(X, y, ratio, cohort_size=40, seed=5)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])


if __name__ == "__main__":
    unittest.main()
