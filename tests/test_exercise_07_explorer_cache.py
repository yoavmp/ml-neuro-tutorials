"""Offline tests for scripts/generate_exercise_07_explorer_cache.py and its
committed cache artifact (WP65, Exercise 7 Interactive Activity 2 "Explore
the Boosting Parameters").

Standard-library ``unittest``; no network, no model fitting -- re-validates
the committed cache for self-consistency, cohort/split sizes, grid
completeness, locked-test exclusion, and cross-checks its
learning_rate=0.1/max_depth=2 row against the numbers
scripts/generate_exercise_07_notebook.py's own module docstring already
documents and audits for Section 4's sweep (same data, same split, same
settings -- staged_predict at stage n must equal a fresh fit with
n_estimators=n). Does not refit any model; see
scripts/generate_exercise_07_explorer_cache.py --run for that
(~2 minutes).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_07_explorer_cache.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import generate_exercise_07_explorer_cache as cache_gen  # noqa: E402


class CommittedCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(cache_gen.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = cache_gen.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_locked_test_is_excluded(self):
        self.assertIs(self.data["lockedTestExcluded"], True)
        other_keys = [k for k in self.data if k != "lockedTestExcluded"]
        self.assertFalse(any("test" in k.lower() for k in other_keys), other_keys)

    def test_cohort_and_split_sizes_match_the_notebooks_own_split(self):
        # wp46-104-load in generate_exercise_07_notebook.py prints these
        # exact sizes for the notebook's own data load.
        split = self.data["split"]
        self.assertEqual(split["nFit"], 564)
        self.assertEqual(split["nVal"], 189)
        self.assertEqual(split["featureCount"], 360)
        self.assertEqual(split["outer"], {"test_size": 0.25, "random_state": 42})
        self.assertEqual(split["dev"], {"test_size": 0.25, "random_state": 7})

    def test_grid_matches_the_notebook_generators_declared_grids(self):
        from generate_exercise_07_notebook import (
            EXPLORER_DEPTH_GRID,
            EXPLORER_LR_GRID,
            EXPLORER_N_TREES_GRID,
        )

        self.assertEqual(self.data["learningRateGrid"], EXPLORER_LR_GRID)
        self.assertEqual(self.data["depthGrid"], EXPLORER_DEPTH_GRID)
        self.assertEqual(self.data["nTreesGrid"], EXPLORER_N_TREES_GRID)

    def test_grid_has_one_entry_per_learning_rate_depth_combination(self):
        expected = len(self.data["learningRateGrid"]) * len(self.data["depthGrid"])
        self.assertEqual(len(self.data["grid"]), expected)

    def test_training_mse_is_monotone_non_increasing_with_more_trees(self):
        for key, entry in self.data["grid"].items():
            train = entry["trainMse"]
            for a, b in zip(train, train[1:]):
                self.assertGreaterEqual(a, b - 1e-6, key)

    def test_default_configuration_shows_underfit_then_overfit_pattern(self):
        entry = self.data["grid"]["0.1|2"]
        n_trees_grid = self.data["nTreesGrid"]
        val_by_n = dict(zip(n_trees_grid, entry["valMse"]))
        smallest_n, largest_n = n_trees_grid[0], n_trees_grid[-1]
        best_n = min(val_by_n, key=val_by_n.get)
        self.assertLess(val_by_n[best_n], val_by_n[smallest_n])
        self.assertNotEqual(best_n, largest_n)

    def test_default_row_matches_section_4_sweeps_audited_numbers(self):
        # scripts/generate_exercise_07_notebook.py's own module docstring
        # documents Section 4's independently-fit sweep (learning_rate=0.1,
        # max_depth=2) as: 34.05 at 10 trees, a minimum of 18.73 at
        # 100-150 trees, and 19.37 at 300 trees. staged_predict at stage n
        # from one fit with n_estimators=300 is mathematically identical to
        # a fresh fit with n_estimators=n for GradientBoostingRegressor
        # (deterministic given the same random_state), so this cache's
        # 0.1|2 row must reproduce those same numbers closely.
        entry = self.data["grid"]["0.1|2"]
        val_by_n = dict(zip(self.data["nTreesGrid"], entry["valMse"]))
        self.assertAlmostEqual(val_by_n[10], 34.05, delta=0.1)
        self.assertAlmostEqual(val_by_n[100], 18.73, delta=0.1)
        self.assertAlmostEqual(val_by_n[300], 19.37, delta=0.1)

    def test_no_non_finite_values_anywhere(self):
        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, float):
                self.assertTrue(math.isfinite(node))

        walk(self.data)


class Validate(unittest.TestCase):
    def test_flags_a_missing_grid_entry(self):
        data = json.loads(cache_gen.RESULT_PATH.read_text(encoding="utf-8"))
        key = next(iter(data["grid"]))
        del data["grid"][key]
        problems = cache_gen.validate(data)
        self.assertTrue(any("missing entry" in p for p in problems))

    def test_flags_locked_test_excluded_false(self):
        data = json.loads(cache_gen.RESULT_PATH.read_text(encoding="utf-8"))
        data["lockedTestExcluded"] = False
        problems = cache_gen.validate(data)
        self.assertTrue(any("lockedTestExcluded" in p for p in problems))

    def test_flags_a_grid_mismatch_with_the_notebook_generator(self):
        data = json.loads(cache_gen.RESULT_PATH.read_text(encoding="utf-8"))
        data["learningRateGrid"] = [0.99]
        problems = cache_gen.validate(data)
        self.assertTrue(any("learningRateGrid" in p for p in problems))


class EmbeddedInNotebook(unittest.TestCase):
    """Cross-check against generate_exercise_07_notebook.py's own embedding,
    so the two scripts cannot silently drift apart."""

    def test_notebook_generator_embeds_this_exact_cache(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        import generate_exercise_07_notebook as gen

        literal = gen._explorer_cache_literal()
        data = json.loads(cache_gen.RESULT_PATH.read_text(encoding="utf-8"))
        for lr in gen.EXPLORER_LR_GRID:
            for depth in gen.EXPLORER_DEPTH_GRID:
                entry = data["grid"][f"{lr}|{depth}"]
                self.assertIn(f"({lr!r}, {depth!r}):", literal)
                self.assertIn(repr(entry["valMse"][-1]), literal)


if __name__ == "__main__":
    unittest.main()
