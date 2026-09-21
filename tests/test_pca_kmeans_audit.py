"""Offline tests for scripts/pca_kmeans_audit.py and its committed result
(WP33, Exercise 8 sections 4/8).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and checks the pedagogical/leakage claims the
notebook makes against the audited numbers.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_pca_kmeans_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import pca_kmeans_audit as pka  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(pka.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = pka.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], pka.MANIFEST["source"]["pinned_commit"])

    def test_cohort_is_the_full_1004_participant_360_feature_table(self):
        self.assertEqual(self.result["cohort"]["n_participants"], 1004)
        self.assertEqual(self.result["cohort"]["n_features"], 360)

    def test_explained_variance_ratio_is_50_entries_non_increasing(self):
        evr = self.result["pca"]["explained_variance_ratio"]
        self.assertEqual(len(evr), 50)
        self.assertEqual(evr, sorted(evr, reverse=True))
        self.assertGreater(evr[0], evr[1])

    def test_cumulative_explained_variance_is_monotone_and_bounded(self):
        cum = self.result["pca"]["cumulative_explained_variance"]
        self.assertEqual(len(cum), 50)
        for a, b in zip(cum, cum[1:]):
            self.assertLessEqual(a, b + 1e-9)
        self.assertLessEqual(cum[-1], 1.0 + 1e-9)

    def test_pc1_is_a_uniformly_signed_global_component(self):
        # PC1's own sign convention is arbitrary (sklearn may flip it), but
        # every loading should agree in sign -- the notebook's "global
        # cortical-thickness pattern" interpretation depends on this.
        self.assertTrue(self.result["pca"]["pc1_all_same_sign"])

    def test_grouped_loading_uses_mean_absolute_value_never_negative(self):
        grouped = self.result["pca"]["grouped_mean_abs_loading"]
        for group in ("frontal", "parietal", "temporal", "occipital"):
            with self.subTest(group=group):
                self.assertIn(group, grouped)
                for value in grouped[group].values():
                    self.assertGreaterEqual(value, 0.0)

    def test_anatomical_group_sizes_match_the_manifest_bundles(self):
        for group, size in self.result["pca"]["group_sizes"].items():
            with self.subTest(group=group):
                # Each canonical ROI id is bilateral (L + R), so the column
                # count is exactly twice the manifest's ROI-id count.
                self.assertEqual(size, 2 * len(pka.MANIFEST["bundles"][group]["rois"]))

    def test_supervised_pipeline_development_test_are_disjoint_and_complete(self):
        sup = self.result["supervised_pipeline"]
        self.assertTrue(sup["development_test_disjoint"])
        self.assertTrue(sup["development_test_union_equals_cohort"])
        self.assertEqual(sup["n_development"], 753)
        self.assertEqual(sup["n_outer_test"], 251)

    def test_supervised_pipeline_component_grid_matches_the_spec(self):
        sup = self.result["supervised_pipeline"]
        self.assertEqual(sup["component_grid"], [2, 5, 10, 20, 50, 100, 200])
        self.assertEqual(len(sup["cv_results"]), len(sup["component_grid"]))
        for candidate in sup["cv_results"]:
            self.assertEqual(len(candidate["fold_mse"]), 5)

    def test_selected_component_count_matches_a_fresh_minimum_cv_mse_recomputation(self):
        sup = self.result["supervised_pipeline"]
        cv_results = sup["cv_results"]
        best_i = min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i))
        self.assertEqual(sup["selected_index"], best_i)
        self.assertEqual(sup["selected_n_components"], cv_results[best_i]["n_components"])
        self.assertEqual(sup["selected_mean_cv_mse"], cv_results[best_i]["mean_mse"])

    def test_locked_test_metrics_are_present_and_evaluated_once(self):
        sup = self.result["supervised_pipeline"]
        self.assertIsInstance(sup["pca_pipeline_test_mse"], float)
        self.assertIsInstance(sup["pca_pipeline_test_r2"], float)
        self.assertIsInstance(sup["baseline_no_pca_test_mse"], float)

    def test_pca_beats_baseline_flag_matches_a_fresh_comparison(self):
        sup = self.result["supervised_pipeline"]
        expected = sup["pca_pipeline_test_mse"] < sup["baseline_no_pca_test_mse"]
        self.assertEqual(sup["pca_beats_baseline"], expected)

    def test_no_non_finite_values_anywhere(self):
        import math

        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, float):
                self.assertTrue(math.isfinite(node))

        walk(self.result)


if __name__ == "__main__":
    unittest.main()
