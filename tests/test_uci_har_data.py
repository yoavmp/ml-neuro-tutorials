"""Offline tests for scripts/uci_har_data.py: the committed compact UCI HAR
table, its provenance, and the shared grouped-vs-random fold comparison used
by both the mandatory preflight audit and the browser widget exporter
(WP38 sec 8, sec 13).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_uci_har_data.py'
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import uci_har_data as uhd  # noqa: E402


class CompactTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = uhd.load_compact_table()

    def test_row_and_participant_counts(self):
        self.assertEqual(len(self.frame), 10299)
        self.assertEqual(self.frame["participant_id"].nunique(), 30)

    def test_exactly_six_activities(self):
        self.assertEqual(sorted(self.frame["activity_id"].unique()), sorted(uhd.ACTIVITY_LABELS))

    def test_eighteen_feature_columns_present(self):
        self.assertEqual(len(uhd.FEATURE_SUBSET), 18)
        for col in uhd.FEATURE_SUBSET:
            self.assertIn(col, self.frame.columns)

    def test_no_missing_values(self):
        self.assertEqual(int(self.frame[list(uhd.FEATURE_SUBSET)].isna().sum().sum()), 0)

    def test_repeated_rows_per_participant(self):
        counts = self.frame["participant_id"].value_counts()
        self.assertEqual(len(counts), 30)
        self.assertTrue((counts > 1).all())


class Provenance(unittest.TestCase):
    def test_provenance_matches_pinned_source(self):
        provenance = uhd.load_provenance()
        self.assertEqual(provenance["dataset"]["sourceUrl"], "https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones")
        self.assertEqual(provenance["dataset"]["doi"], "https://doi.org/10.24432/C54S4K")
        self.assertEqual(provenance["dataset"]["license"], "CC BY 4.0")

    def test_derived_file_checksum_matches_committed_file(self):
        provenance = uhd.load_provenance()
        actual = uhd.sha256_hex(uhd.COMPACT_CSV_PATH.read_bytes())
        self.assertEqual(provenance["derivedFile"]["sha256"], actual)

    def test_no_target_informed_selection_noted(self):
        provenance = uhd.load_provenance()
        self.assertIn("not by predictive performance", provenance["extraction"]["note"])


class FoldComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = uhd.load_compact_table()
        cls.result = uhd.compute_fold_comparison(cls.frame, k_values=(5,))

    def test_ordinary_splitting_crosses_folds_for_every_participant(self):
        self.assertEqual(self.result["participantsCrossingFoldsOrdinary"], 30)

    def test_grouped_splitting_has_zero_overlap(self):
        self.assertEqual(self.result["participantsCrossingFoldsGrouped"], 0)
        self.assertTrue(self.result["groupedFoldsDisjoint"])

    def test_grouped_fold_is_a_single_value_per_participant(self):
        for p in self.result["participantFolds"]:
            self.assertIsInstance(p["groupedFold"], int)
            self.assertGreaterEqual(len(p["ordinaryFolds"]), 1)

    def test_ordinary_is_more_optimistic_than_grouped_at_k5(self):
        r = self.result["kResults"][0]
        self.assertGreater(r["accGap"], 0)
        self.assertGreater(r["f1Gap"], 0)

    def test_confusion_matrices_have_five_folds_of_six_by_six(self):
        r = self.result["kResults"][0]
        for side in ("ordinary", "grouped"):
            confusions = r[side]["confusionPerFold"]
            self.assertEqual(len(confusions), 5)
            for cm in confusions:
                self.assertEqual(len(cm), 6)
                self.assertTrue(all(len(row) == 6 for row in cm))

    def test_is_deterministic(self):
        result2 = uhd.compute_fold_comparison(self.frame, k_values=(5,))
        self.assertEqual(self.result["kResults"], result2["kResults"])


if __name__ == "__main__":
    unittest.main()
