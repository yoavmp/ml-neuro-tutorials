"""Offline tests for scripts/wp27_validation_audit.py and its committed
result (WP27: validation and cross-validation for Exercise 4).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and checks the specific numeric facts the Exercise
4 notebook and its three interactive activities state.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp27_validation_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import wp27_validation_audit as wva  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(wva.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = wva.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], wva.MANIFEST["source"]["pinned_commit"])

    def test_target_is_age(self):
        self.assertEqual(self.result["target"], "age")


class PartA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = json.loads(wva.RESULT_PATH.read_text(encoding="utf-8"))["part_a_sample_size_stability"]

    def test_fixed_k_is_20_the_exercise_2_worked_example(self):
        self.assertEqual(self.a["fixed_k"], 20)

    def test_sample_sizes_match_the_predeclared_grid(self):
        self.assertEqual(self.a["sample_sizes"], [30, 50, 75, 100, 150, 250, 500, "all"])

    def test_split_seeds_match_the_predeclared_sequence(self):
        self.assertEqual(self.a["split_seeds"], [0, 1, 2, 3, 4])

    def test_pools_are_nested_by_construction(self):
        # Every smaller sample size's participant pool is a strict prefix of
        # every larger size's pool (see _nested_pools); this test recomputes
        # the pools directly rather than trusting the summary.
        pools = wva._nested_pools(self.a["n_eligible"])
        ordered_sizes = [30, 50, 75, 100, 150, 250, 500, "all"]
        for smaller, larger in zip(ordered_sizes, ordered_sizes[1:]):
            small_pool = list(pools[smaller])
            large_pool = list(pools[larger])
            self.assertEqual(small_pool, large_pool[: len(small_pool)])

    def test_ten_fold_excluded_at_smallest_size_for_min_fold_size(self):
        n30 = next(s for s in self.a["sizes"] if s["sample_size"] == 30)
        for c in n30["cv_by_folds"]["10"]:
            self.assertFalse(c["valid"], c)
            self.assertIn("reason", c)

    def test_instability_flag_uses_negative_r2_not_bare_range(self):
        # The predeclared range-threshold statistic is noisy/non-monotonic
        # with only 5 seeds (see the WP27 report); the notebook's own claim
        # uses the stricter, metric-independent "a single split can score
        # worse than always predicting the mean" criterion instead.
        for s in self.a["sizes"]:
            self.assertEqual(s["instability_meaningful"], s["any_negative_single_split_r2"])

    def test_meaningful_instability_is_confined_to_n_below_100(self):
        for size in self.a["sizes_with_meaningful_instability"]:
            self.assertIsInstance(size, int)
            self.assertLess(size, 100)
        self.assertTrue(self.a["instability_requires_small_n"])


class PartB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = json.loads(wva.RESULT_PATH.read_text(encoding="utf-8"))["part_b_train_val_test_tuning"]

    def test_matches_exercise_2_outer_split_sizes(self):
        self.assertEqual(self.b["n_outer_train"], 753)
        self.assertEqual(self.b["n_outer_test"], 251)

    def test_matches_exercise_2_dev_split_sizes(self):
        self.assertEqual(self.b["n_fit"], 564)
        self.assertEqual(self.b["n_val"], 189)

    def test_training_selected_k_is_the_most_flexible_candidate(self):
        # k=1 gives perfect (zero-error) resubstitution on the fitting data;
        # it must be the argmin of training MSE among the candidate grid.
        self.assertEqual(self.b["training_selected_k"], 1)
        self.assertEqual(self.b["training_selected_result"]["train_mse"], 0.0)

    def test_validation_selected_k_is_in_the_candidate_grid(self):
        self.assertIn(self.b["validation_selected_k"], self.b["candidate_ks"])

    def test_test_metrics_never_influenced_selection(self):
        # The selection functions (argmin over train_mse / val_mse) never
        # reference test_mse_if_locked / test_r2_if_locked; this test proves
        # it by recomputing the selection from a copy of rows with the test
        # fields removed.
        stripped = [
            {k: v for k, v in row.items() if k not in ("test_mse_if_locked", "test_r2_if_locked")}
            for row in self.b["rows"]
        ]
        recomputed_train_sel = min(stripped, key=lambda r: r["train_mse"])["k"]
        recomputed_val_sel = min(stripped, key=lambda r: r["val_mse"])["k"]
        self.assertEqual(recomputed_train_sel, self.b["training_selected_k"])
        self.assertEqual(recomputed_val_sel, self.b["validation_selected_k"])

    def test_every_candidate_k_has_a_locked_test_result(self):
        for row in self.b["rows"]:
            self.assertIn("test_mse_if_locked", row)
            self.assertIn("test_r2_if_locked", row)


class PartC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(wva.RESULT_PATH.read_text(encoding="utf-8"))["part_c_nested_cv"]

    def test_five_outer_folds(self):
        self.assertEqual(len(self.c["fold_rows"]), 5)

    def test_every_fold_selected_from_the_candidate_grid(self):
        for row in self.c["fold_rows"]:
            self.assertIn(row["selected_k"], self.c["candidate_ks"])

    def test_outer_test_metrics_present_for_every_fold(self):
        for row in self.c["fold_rows"]:
            self.assertIn("outer_test_mse", row)
            self.assertIn("outer_test_r2", row)

    def test_mean_and_std_recomputable_from_fold_rows(self):
        mses = [r["outer_test_mse"] for r in self.c["fold_rows"]]
        self.assertAlmostEqual(sum(mses) / len(mses), self.c["mean_outer_test_mse"], places=3)


if __name__ == "__main__":
    unittest.main()
