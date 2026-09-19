"""Offline tests for scripts/export_tree_ensemble_widget.py and its committed
data artifact (WP29, Exercise 6 "One Tree or Many?").

Standard-library ``unittest``; no network -- reads the already-committed
JSON artifact and cross-checks its internal consistency (summary values
recomputed from the per-replicate rows).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_tree_ensemble_widget_data.py'
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_tree_ensemble_widget as te  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(te.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = te.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.data["source"]["pinnedCommit"], te.MANIFEST["source"]["pinned_commit"])

    def test_five_deterministic_replicate_seeds(self):
        seeds = [r["seed"] for r in self.data["replicates"]]
        self.assertEqual(seeds, [0, 1, 2, 3, 4])

    def test_replicates_draw_without_replacement_a_fixed_fraction(self):
        pool = self.data["settings"]["replicatePoolSize"]
        fraction = self.data["settings"]["replicateFraction"]
        expected_n = round(fraction * pool)
        for r in self.data["replicates"]:
            self.assertEqual(r["nTrain"], expected_n)

    def test_random_forest_max_features_is_explicit_and_less_than_feature_count(self):
        mf = self.data["settings"]["randomForestMaxFeatures"]
        self.assertIsInstance(mf, int)
        self.assertLess(mf, self.data["featureRecipe"]["featureCount"])

    def test_every_replicate_uses_the_same_validation_participants(self):
        n_val = self.data["split"]["devSplit"]["nVal"]
        self.assertEqual(len(self.data["observedValidation"]), n_val)
        for r in self.data["replicates"]:
            self.assertEqual(len(r["singleTree"]["predictedValidation"]), n_val)

    def test_root_splits_differ_across_replicates(self):
        # The whole point of the activity: different training samples select
        # different early splits, not just different random_state labels on
        # identical data.
        splits = {(r["rootSplit"]["feature"], r["rootSplit"]["threshold"]) for r in self.data["replicates"]}
        self.assertGreater(len(splits), 1)

    def test_summary_mean_mse_matches_recomputation_from_replicates(self):
        values = [r["singleTree"]["valMSE"] for r in self.data["replicates"]]
        expected_mean = round(statistics.fmean(values), 4)
        self.assertAlmostEqual(self.data["summary"]["singleTree"]["meanMSE"], expected_mean, places=2)

    def test_ensemble_variability_shrinks_with_more_trees(self):
        grid = self.data["nTreesGrid"]
        bagging = self.data["summary"]["bagging"]
        first_sd = bagging[str(grid[0])]["sdMSE"]
        last_sd = bagging[str(grid[-1])]["sdMSE"]
        self.assertLess(last_sd, first_sd)

    def test_single_tree_has_more_variability_than_bagging_at_largest_ensemble_size(self):
        grid = self.data["nTreesGrid"]
        single_sd = self.data["summary"]["singleTree"]["sdMSE"]
        bagging_sd = self.data["summary"]["bagging"][str(grid[-1])]["sdMSE"]
        self.assertGreater(single_sd, bagging_sd)

    def test_runtime_is_recorded(self):
        self.assertIn("runtimeSeconds", self.data)
        self.assertGreater(self.data["runtimeSeconds"], 0)


if __name__ == "__main__":
    unittest.main()
