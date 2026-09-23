"""Offline tests for scripts/advanced_models_audit.py and its committed
result (WP34, Exercise 9 section 8: the nested-cross-validation ABIDE-II
model comparison).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and checks the leakage-safety/fairness claims the
notebook makes against the audited numbers.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_advanced_models_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import advanced_models_audit as ama  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(ama.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ama.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], ama.MANIFEST["source"]["pinned_commit"])

    def test_cohort_is_the_full_1004_participant_360_feature_table(self):
        self.assertEqual(self.result["cohort"]["n_participants"], 1004)
        self.assertEqual(self.result["cohort"]["n_features"], 360)

    def test_five_models_compared(self):
        self.assertEqual(set(self.result["models"]), {"ols", "pcr", "pls", "linear_svr", "rbf_svr"})

    def test_outer_and_inner_cv_match_the_manifest(self):
        self.assertEqual(self.result["outer_cv"], ama.OUTER_CFG)
        self.assertEqual(self.result["inner_cv"], ama.INNER_CFG)
        self.assertEqual(self.result["outer_cv"]["n_splits"], 5)
        self.assertEqual(self.result["inner_cv"]["n_splits"], 5)

    def test_every_model_has_exactly_five_outer_folds(self):
        for model_key in self.result["models"]:
            self.assertEqual(len(self.result["summary"][model_key]["folds"]), 5)

    def test_every_model_shares_identical_outer_test_fold_sizes(self):
        sizes_by_fold: dict[int, set[int]] = {}
        for model_key in self.result["models"]:
            for f in self.result["summary"][model_key]["folds"]:
                sizes_by_fold.setdefault(f["outer_fold"], set()).add(f["n_test"])
        for fold, sizes in sizes_by_fold.items():
            self.assertEqual(len(sizes), 1, (fold, sizes))

    def test_outer_test_sizes_sum_to_the_full_cohort(self):
        ols_folds = self.result["summary"]["ols"]["folds"]
        self.assertEqual(sum(f["n_test"] for f in ols_folds), 1004)

    def test_tuned_models_selected_params_match_a_fresh_minimum_inner_mse_recomputation(self):
        for model_key in ("pcr", "pls", "linear_svr", "rbf_svr"):
            for f in self.result["summary"][model_key]["folds"]:
                candidates = f["inner_candidates"]
                best = min(candidates, key=lambda c: c["mean_mse"])
                self.assertEqual(f["selected_params"], best["params"], (model_key, f["outer_fold"]))

    def test_ols_has_no_inner_candidates(self):
        for f in self.result["summary"]["ols"]["folds"]:
            self.assertNotIn("inner_candidates", f)
            self.assertEqual(f["selected_params"], {})

    def test_mean_outer_test_metrics_match_a_fresh_recomputation(self):
        for model_key in self.result["models"]:
            entry = self.result["summary"][model_key]
            mses = [f["outer_test_mse"] for f in entry["folds"]]
            self.assertAlmostEqual(sum(mses) / len(mses), entry["mean_outer_test_mse"], places=2)

    def test_parameter_grids_match_the_manifest(self):
        for model_key in ("pcr", "pls", "linear_svr", "rbf_svr"):
            grid = ama.MODELS[model_key]["grid"]
            expected = ama._param_grid(model_key)
            for f in self.result["summary"][model_key]["folds"]:
                self.assertEqual(len(f["inner_candidates"]), len(expected), model_key)
            if model_key == "pcr":
                self.assertEqual(grid["n_components"], [5, 10, 20, 50, 100, 200])
            if model_key == "pls":
                self.assertEqual(grid["n_components"], [2, 5, 10, 20])
            if model_key == "linear_svr":
                self.assertEqual(grid["C"], [0.01, 0.1, 1])
                self.assertEqual(grid["epsilon"], [0.5, 1, 2])
            if model_key == "rbf_svr":
                self.assertEqual(grid["C"], [1, 10, 100])
                self.assertEqual(grid["gamma"], ["scale", 0.001, 0.01])

    def test_linear_svr_grid_excludes_the_nonconvergent_c_equals_10(self):
        # WP35 §14: C=10 never converged (even at max_iter=100000) and was
        # never selected by any outer fold; it must not be in the grid.
        self.assertNotIn(10, ama.MODELS["linear_svr"]["grid"]["C"])
        for f in self.result["summary"]["linear_svr"]["folds"]:
            for c in f["inner_candidates"]:
                self.assertNotEqual(c["params"].get("C"), 10)

    def test_no_convergence_warnings_remain(self):
        self.assertEqual(self.result.get("convergence_warnings", []), [])

    def test_rbf_svr_epsilon_is_explicit_and_not_sklearns_implicit_default(self):
        fixed = self.result["summary"]["rbf_svr"]["fixed_params"]
        self.assertEqual(fixed["epsilon"], 1.0)
        # scikit-learn's SVR default is epsilon=0.1; regressing to it silently
        # (e.g. dropping the explicit kwarg) must fail this test.
        self.assertNotEqual(fixed["epsilon"], 0.1)
        self.assertEqual(ama.RBF_SVR_EPSILON, 1.0)

    def test_rbf_svr_pipeline_actually_sets_epsilon(self):
        pipe = ama._make_pipeline("rbf_svr", {"C": 1, "gamma": "scale"})
        self.assertEqual(pipe.named_steps["model"].epsilon, 1.0)

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
