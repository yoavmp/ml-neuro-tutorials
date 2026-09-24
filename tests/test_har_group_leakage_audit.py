"""Offline tests for scripts/har_group_leakage_audit.py -- the mandatory
UCI HAR preflight audit (WP38 sec 8.2). Asserts the committed result is
current, canonical, and that all four inclusion conditions pass.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_har_group_leakage_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import har_group_leakage_audit as hgla  # noqa: E402
from uci_har_data import K_VALUES, load_compact_table  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(hgla.RESULT_PATH.read_text(encoding="utf-8"))

    def test_result_is_current_and_canonical(self):
        # Serialization equality is the meaningful check here: JSON object
        # keys are always strings, so a freshly recomputed Python dict (whose
        # per-k dicts use int keys) is never `==` to the dict read back from
        # disk (str keys) even when they serialize identically.
        frame = load_compact_table()
        recomputed = hgla.build_result(frame)
        self.assertEqual(hgla.serialize(recomputed), hgla.RESULT_PATH.read_text(encoding="utf-8"))

    def test_all_five_k_values_preserved(self):
        self.assertEqual(self.result["kValues"], list(K_VALUES))
        self.assertEqual(len(self.result["comparison"]["kResults"]), 5)

    def test_condition_1_ordinary_crosses_folds(self):
        self.assertTrue(self.result["conditions"]["condition1ParticipantsCrossOrdinary"])

    def test_condition_2_grouped_disjoint(self):
        self.assertTrue(self.result["conditions"]["condition2GroupedDisjoint"])

    def test_condition_3_at_least_two_qualifying_k(self):
        self.assertTrue(self.result["conditions"]["condition3Qualifies"])
        self.assertGreaterEqual(self.result["conditions"]["condition3QualifyingKCount"], 2)

    def test_condition_4_not_one_anomalous_fold(self):
        self.assertTrue(self.result["conditions"]["condition4Qualifies"])

    def test_overall_preflight_passes(self):
        self.assertTrue(self.result["conditions"]["overallPass"])


class ConditionLogic(unittest.TestCase):
    def _fake_comparison(self, acc_gaps_per_fold):
        """Build a minimal fake comparison dict for one k with the given
        per-fold (ordinary, grouped) accuracy pairs."""
        ordinary_acc = [o for o, g in acc_gaps_per_fold]
        grouped_acc = [g for o, g in acc_gaps_per_fold]
        return {
            "participantsCrossingFoldsOrdinary": 30,
            "participantsCrossingFoldsGrouped": 0,
            "groupedFoldsDisjoint": True,
            "kResults": [
                {
                    "k": 5,
                    "ordinary": {"accPerFold": ordinary_acc, "f1PerFold": ordinary_acc},
                    "grouped": {"accPerFold": grouped_acc, "f1PerFold": grouped_acc},
                    "accGap": round(sum(ordinary_acc) / 5 - sum(grouped_acc) / 5, 6),
                    "f1Gap": round(sum(ordinary_acc) / 5 - sum(grouped_acc) / 5, 6),
                }
            ],
        }

    def test_single_anomalous_fold_fails_condition_4(self):
        # A big gap in one fold, no gap in the other four -- the mean clears
        # the 0.03 threshold, but only 1 of 5 folds is individually positive,
        # so condition 4 (>= 3 of 5 folds) must fail regardless of condition 3.
        comparison = self._fake_comparison([(0.95, 0.50), (0.80, 0.80), (0.80, 0.80), (0.80, 0.80), (0.80, 0.80)])
        conditions = hgla._condition_checks(comparison)
        self.assertEqual(conditions["condition4PerKPositiveFolds"][5], 1)
        self.assertFalse(conditions["overallPass"])

    def test_consistent_small_gap_across_folds_passes_condition_4_but_not_3(self):
        comparison = self._fake_comparison([(0.81, 0.80)] * 5)
        conditions = hgla._condition_checks(comparison)
        self.assertFalse(conditions["condition3Qualifies"])


if __name__ == "__main__":
    unittest.main()
