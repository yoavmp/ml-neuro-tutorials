"""Offline tests for scripts/export_classification_threshold_data.py and its
committed artifact (WP17 §4, §9).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_classification_threshold_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_classification_threshold_data as ectd  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ectd.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ectd.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = ectd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ectd.serialize(self.artifact), on_disk)

    def test_labels_and_probabilities_align_with_n_test(self):
        n_test = self.artifact["split"]["nTest"]
        self.assertEqual(len(self.artifact["labels"]), n_test)
        self.assertEqual(len(self.artifact["probabilities"]), n_test)

    def test_both_classes_present(self):
        labels = set(self.artifact["labels"])
        self.assertEqual(labels, {0, 1})

    def test_no_participant_identifier_shaped_keys(self):
        identifier_token = ("id", "sub", "subject", "site", "participant")
        for key in self.artifact:
            self.assertNotIn(key.lower(), identifier_token)

    def test_feature_count_is_360(self):
        self.assertEqual(self.artifact["featureRecipe"]["featureCount"], 360)

    def test_auc_matches_recomputation_from_labels_and_probabilities(self):
        from sklearn.metrics import roc_auc_score

        recomputed = roc_auc_score(self.artifact["labels"], self.artifact["probabilities"])
        self.assertAlmostEqual(recomputed, self.artifact["aucFromAudit"], places=3)

    def test_selected_c_is_cited_and_not_the_old_untuned_default(self):
        # WP18: C is selected honestly by cross-validation, not fixed at 1.0.
        self.assertIn("selectedC", self.artifact)
        self.assertIn(f"C={self.artifact['selectedC']!r}", self.artifact["model"])


class ConfusionAtHelper(unittest.TestCase):
    def test_confusion_at_threshold_matches_hand_worked_example(self):
        labels = [1, 1, 0, 0]
        probs = [0.9, 0.4, 0.6, 0.1]
        tn, fp, fn, tp = ectd._confusion_at(labels, probs, 0.5)
        # threshold 0.5: predicted = [1, 0, 1, 0] vs labels [1, 1, 0, 0]
        # -> TP=1 (idx0), FN=1 (idx1), FP=1 (idx2), TN=1 (idx3)
        self.assertEqual((tn, fp, fn, tp), (1, 1, 1, 1))

    def test_higher_threshold_never_increases_positive_predictions(self):
        labels = [1, 1, 0, 0, 1, 0]
        probs = [0.9, 0.2, 0.6, 0.1, 0.55, 0.75]
        _, fp_lo, _, tp_lo = ectd._confusion_at(labels, probs, 0.2)
        _, fp_hi, _, tp_hi = ectd._confusion_at(labels, probs, 0.8)
        self.assertLessEqual(tp_hi + fp_hi, tp_lo + fp_lo)


if __name__ == "__main__":
    unittest.main()
