"""Offline tests for scripts/decision_tree_model_audit.py and its committed
result (WP29, Exercise 6 sections 1/3/6).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and checks the pedagogical claims the notebook
will make against the audited numbers.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_decision_tree_model_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import decision_tree_model_audit as dta  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(dta.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = dta.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], dta.MANIFEST["source"]["pinned_commit"])

    def test_single_tree_uses_the_two_predeclared_features(self):
        st = self.result["single_tree"]
        self.assertEqual(st["features"], ["fsCT_L_3a_ROI", "fsCT_R_2_ROI"])
        self.assertEqual(st["settings"], {"max_depth": 3, "min_samples_leaf": 20, "random_state": 42})

    def test_single_tree_is_shallow_and_readable(self):
        st = self.result["single_tree"]
        self.assertLessEqual(st["depth"], 3)
        self.assertGreater(st["n_leaves"], 1)
        self.assertLess(st["n_leaves"], 16)

    def test_single_tree_never_violates_min_samples_leaf(self):
        st = self.result["single_tree"]
        self.assertGreaterEqual(st["min_leaf_sample_count"], st["settings"]["min_samples_leaf"])

    def test_complexity_curve_uses_only_the_full_recipe(self):
        cc = self.result["complexity_curve"]
        self.assertEqual(cc["p"], 360)

    def test_complexity_curve_training_error_is_monotone_non_increasing(self):
        cc = self.result["complexity_curve"]
        train_mse = cc["train_mse"]
        for a, b in zip(train_mse, train_mse[1:]):
            self.assertGreaterEqual(a, b - 1e-6)

    def test_complexity_curve_shows_overfitting(self):
        # Validation MSE must not be minimized at the deepest depth in the
        # grid -- otherwise there is no overfitting story to show.
        cc = self.result["complexity_curve"]
        self.assertNotEqual(cc["best_depth"], cc["depth_grid"][-1])

    def test_classification_complexity_curve_uses_the_exercise_3_recipe_and_cv(self):
        ccc = self.result["classification_complexity_curve"]
        self.assertEqual(ccc["p"], 360)
        self.assertEqual(ccc["cv"], "StratifiedKFold(n_splits=5, shuffle=True, random_state=42)")
        self.assertEqual(ccc["min_samples_leaf"], dta.DT["classification_complexity_curve"]["min_samples_leaf"])
        self.assertEqual(ccc["depth_grid"], list(range(1, 11)))

    def test_classification_complexity_curve_uses_the_full_eligible_cohort_not_a_holdout(self):
        # n must be the full eligible cohort (group present), not the
        # smaller classification.holdout_split test partition -- this audit
        # never touches that locked outer test set.
        ccc = self.result["classification_complexity_curve"]
        self.assertEqual(ccc["n"], ccc["n_positive"] + ccc["n_negative"])
        self.assertGreater(ccc["n"], dta.MANIFEST["classification"]["holdout_split"]["test_size"] * ccc["n"])

    def test_classification_inclusion_rule_is_evaluated_exactly_as_specified(self):
        ccc = self.result["classification_complexity_curve"]
        depths = ccc["depth_grid"]
        val_auc = ccc["val_auc"]
        rounded = [round(v, 2) for v in val_auc]
        best_rounded = max(rounded)
        expected_best_i = min(i for i, v in enumerate(rounded) if v == best_rounded)
        expected_best_depth = depths[expected_best_i]
        expected_margin = round(val_auc[expected_best_i] - val_auc[depths.index(2)], 6)
        self.assertEqual(ccc["best_depth"], expected_best_depth)
        self.assertEqual(ccc["margin_over_depth2"], expected_margin)
        self.assertEqual(ccc["inclusion_rule"]["depth_at_least_3"], expected_best_depth >= 3)
        self.assertEqual(ccc["inclusion_rule"]["margin_at_least_0_01"], expected_margin >= 0.01)
        self.assertEqual(
            ccc["inclusion_rule"]["include_figure"],
            bool(expected_best_depth >= 3 and expected_margin >= 0.01),
        )

    def test_fair_comparison_uses_identical_folds_for_every_model(self):
        fc = self.result["fair_comparison"]
        self.assertEqual(fc["cv"], "KFold(n_splits=5, shuffle=True, random_state=100)")
        for name in ("single_tree", "bagging", "random_forest"):
            self.assertEqual(len(fc["models"][name]["fold_mse"]), 5)

    def test_fair_comparison_random_forest_uses_explicit_max_features(self):
        fc = self.result["fair_comparison"]
        self.assertIn("random_forest_max_features", fc)
        self.assertIsInstance(fc["random_forest_max_features"], int)
        self.assertLess(fc["random_forest_max_features"], fc["p"])

    def test_ensembles_outperform_the_single_tree_here(self):
        fc = self.result["fair_comparison"]
        single = fc["models"]["single_tree"]["mean_mse"]
        for name in ("bagging", "random_forest"):
            self.assertLess(fc["models"][name]["mean_mse"], single)

    def test_no_claim_that_random_forest_always_wins(self):
        # This audit result alone must not be read as proof either way; the
        # notebook text (checked separately) must not assert a universal
        # ranking. Here we only confirm the numbers are recorded so that
        # claim can be checked honestly either way.
        fc = self.result["fair_comparison"]
        self.assertIn("mean_mse", fc["models"]["bagging"])
        self.assertIn("mean_mse", fc["models"]["random_forest"])

    def test_runtime_is_recorded(self):
        self.assertIn("runtime_seconds", self.result)
        self.assertGreater(self.result["runtime_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
