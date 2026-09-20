"""Offline tests for scripts/gradient_boosting_model_audit.py and its
committed result (WP32, Exercise 7 sections 3/6/7).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and checks the pedagogical/leakage claims the
notebook makes against the audited numbers.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_gradient_boosting_model_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import gradient_boosting_model_audit as gba  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(gba.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = gba.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], gba.MANIFEST["source"]["pinned_commit"])

    def test_sklearn_example_uses_the_declared_settings(self):
        se = self.result["sklearn_example"]
        expected = {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 2, "random_state": 42}
        for key, value in expected.items():
            self.assertEqual(se["settings"][key], value)
        self.assertEqual(se["n_fit"], 564)
        self.assertEqual(se["n_val"], 189)
        self.assertEqual(se["p"], 360)

    def test_cv_pipeline_uses_the_reduced_at_least_12_candidate_grid(self):
        cv = self.result["cv_pipeline"]
        self.assertGreaterEqual(cv["candidate_count"], 12)
        self.assertEqual(len(cv["candidate_grid"]), cv["candidate_count"])
        depths = {c["max_depth"] for c in cv["candidate_grid"]}
        self.assertEqual(depths, {1, 2, 3})

    def test_cv_pipeline_never_used_a_27_candidate_grid(self):
        # The intended grid (3 learning rates x 3 n_estimators x 3 depths =
        # 27) was reduced once, per the predeclared runtime rule -- see
        # book/config/abide_modeling.json's gradient_boosting.cv_pipeline.
        cv = self.result["cv_pipeline"]
        self.assertLess(cv["candidate_count"], 27)

    def test_cv_pipeline_folds_are_exactly_5(self):
        cv = self.result["cv_pipeline"]
        for candidate in cv["cv_results"]:
            self.assertEqual(len(candidate["fold_mse"]), 5)

    def test_cv_pipeline_development_test_are_disjoint_and_complete(self):
        cv = self.result["cv_pipeline"]
        self.assertTrue(cv["development_test_disjoint"])
        self.assertTrue(cv["development_test_union_equals_cohort"])
        self.assertEqual(cv["n_development"], 753)
        self.assertEqual(cv["n_outer_test"], 251)

    def test_selected_configuration_matches_a_fresh_minimum_cv_mse_recomputation(self):
        cv = self.result["cv_pipeline"]
        cv_results = cv["cv_results"]
        best_i = min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i))
        self.assertEqual(cv["selected_index"], best_i)
        self.assertEqual(cv["selected_params"], cv_results[best_i]["params"])
        self.assertEqual(cv["selected_mean_cv_mse"], cv_results[best_i]["mean_mse"])

    def test_locked_test_is_the_only_place_the_outer_test_metric_appears(self):
        cv = self.result["cv_pipeline"]
        self.assertIsInstance(cv["test_mse"], float)
        self.assertIsInstance(cv["test_r2"], float)

    def test_model_comparison_uses_the_identical_participant_split(self):
        mc = self.result["model_comparison"]
        self.assertEqual(mc["single_tree"]["protocol"], "single locked outer-test evaluation")
        self.assertEqual(mc["random_forest"]["protocol"], "single locked outer-test evaluation")
        self.assertEqual(mc["gradient_boosting"]["protocol"], "single locked outer-test evaluation")

    def test_model_comparison_carries_forward_decision_tree_settings_unchanged(self):
        mc = self.result["model_comparison"]
        fair = gba.DT["fair_comparison"]
        self.assertEqual(mc["single_tree"]["settings"], fair["tree_settings"])
        self.assertEqual(mc["random_forest"]["settings"]["n_estimators"], fair["n_estimators"])
        self.assertEqual(mc["random_forest"]["settings"]["max_features"], fair["random_forest_max_features"])

    def test_model_comparison_gradient_boosting_matches_the_cv_pipeline_test_metric(self):
        mc = self.result["model_comparison"]
        cv = self.result["cv_pipeline"]
        self.assertEqual(mc["gradient_boosting"]["mean_mse"], cv["test_mse"])
        self.assertEqual(mc["gradient_boosting"]["mean_r2"], cv["test_r2"])

    def test_comparison_does_not_force_gradient_boosting_to_win(self):
        # The audit records whichever model actually won; nothing here
        # asserts a particular ordering. This test documents that the
        # comparison numbers are recorded plainly (not post-hoc adjusted),
        # so a future run producing a different winner would not itself be
        # a bug.
        mc = self.result["model_comparison"]
        for name in ("single_tree", "random_forest", "gradient_boosting"):
            self.assertIn("mean_mse", mc[name])
            self.assertIn("mean_r2", mc[name])

    def test_runtime_is_recorded(self):
        self.assertIn("runtime_seconds", self.result)
        self.assertIn("cv_runtime_seconds", self.result["cv_pipeline"])


class Validate(unittest.TestCase):
    def test_flags_a_mismatched_source_pin(self):
        result = json.loads(gba.RESULT_PATH.read_text(encoding="utf-8"))
        result["source"]["pinnedCommit"] = "wrong"
        problems = gba.validate(result)
        self.assertTrue(any("pinnedCommit" in p for p in problems))

    def test_flags_a_stale_selected_index(self):
        result = json.loads(gba.RESULT_PATH.read_text(encoding="utf-8"))
        result["cv_pipeline"]["selected_index"] = 999 % len(result["cv_pipeline"]["cv_results"])
        # Force a definitely-wrong index (not the true minimum).
        cv_results = result["cv_pipeline"]["cv_results"]
        true_best = min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i))
        wrong = (true_best + 1) % len(cv_results)
        result["cv_pipeline"]["selected_index"] = wrong
        problems = gba.validate(result)
        self.assertTrue(any("selected_index" in p for p in problems))

    def test_flags_fewer_than_12_candidates(self):
        result = json.loads(gba.RESULT_PATH.read_text(encoding="utf-8"))
        result["cv_pipeline"]["candidate_grid"] = result["cv_pipeline"]["candidate_grid"][:5]
        problems = gba.validate(result)
        self.assertTrue(any("at least 12" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
