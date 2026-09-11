"""Offline tests for scripts/knn_model_audit.py and its committed result
(WP13 §1, §7.3: "audit reproducibility and training-only k selection tests").

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency, and uses a small synthetic frame (reused from
``test_abide_modeling_data``) plus targeted mocking to prove -- not just
assert -- that:

* k selection (5-fold CV) only ever fits on that outer fold's OWN training
  rows, never the outer test set and never more rows than the fold provides;
* the locked test evaluation fits its final model exactly once, on exactly
  the training partition, and never touches the test rows except to predict;
* the k=n_train "every participant in the fitting set" endpoint really does
  predict a single constant (the training-partition mean) for every query;
* re-running the same procedure with the same seeds is deterministic.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_knn_model_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import knn_model_audit as kma  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(kma.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = kma.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], kma.MANIFEST["source"]["pinned_commit"])

    def test_target_is_age(self):
        self.assertEqual(self.result["target"], "age")

    def test_all_three_predeclared_feature_spaces_present(self):
        names = {c["feature_space"] for c in self.result["candidates"]}
        self.assertEqual(names, {s["name"] for s in kma.FEATURE_SPACES})

    def test_canonical_recipe_matches_exercise_2(self):
        canonical = next(
            c for c in self.result["candidates"] if c["bundle"] == "all-eligible" and c["measures"] == ["CT"]
        )
        self.assertEqual(canonical["p"], 360)
        self.assertEqual(canonical["n_train"], 753)
        self.assertEqual(canonical["n_test"], 251)

    def test_canonical_recipe_was_selected_for_the_notebook(self):
        # WP13 §1: the audit found no curse-of-dimensionality problem for the
        # canonical 360-feature recipe, so it -- not a smaller bundle -- is
        # used as the notebook's standard example.
        candidates = {c["feature_space"]: c for c in self.result["candidates"]}
        canonical = next(c for c in candidates.values() if c["bundle"] == "all-eligible")
        others = [c for c in candidates.values() if c["bundle"] != "all-eligible"]
        self.assertTrue(others)
        for other in others:
            self.assertGreaterEqual(canonical["locked_test_eval"]["test_r2"], other["locked_test_eval"]["test_r2"])

    def test_selected_k_beats_the_test_r2_of_ols_on_the_same_recipe(self):
        # Exercise 2's OLS on this exact split/recipe scored R^2 = 0.475.
        canonical = next(
            c for c in self.result["candidates"] if c["bundle"] == "all-eligible" and c["measures"] == ["CT"]
        )
        self.assertGreater(canonical["locked_test_eval"]["test_r2"], 0.475)

    def test_k_grid_spans_one_through_the_largest_cv_valid_k(self):
        for c in self.result["candidates"]:
            self.assertEqual(c["k_grid"][0], 1)
            self.assertEqual(c["k_grid"][-1], c["k_grid_max_valid_in_cv"])
            self.assertEqual(c["k_grid"], sorted(c["k_grid"]))
            self.assertEqual(len(c["k_grid"]), len(set(c["k_grid"])))

    def test_selected_k_is_the_argmax_of_the_cv_curve(self):
        for c in self.result["candidates"]:
            best = max(row["cv_r2_mean"] for row in c["cv_curve"])
            selected_row = next(row for row in c["cv_curve"] if row["k"] == c["selected_k"])
            self.assertAlmostEqual(selected_row["cv_r2_mean"], best, places=9)

    def test_fitting_set_endpoint_predicts_a_single_constant(self):
        for c in self.result["candidates"]:
            ep = c["fitting_set_endpoint"]
            self.assertTrue(ep["all_predictions_equal_training_mean"], c["feature_space"])
            self.assertEqual(ep["k"], c["n_train"])

    def test_runtime_is_recorded(self):
        self.assertIn("runtime_seconds", self.result)
        self.assertGreater(self.result["runtime_seconds"], 0)


def _tiny_frame():
    # 60 participants, ~78 CT + 78 Area features (frontoparietal + occipital
    # bundles) -- reused from test_abide_modeling_data, fast for isolation
    # tests that do not need the full 360-feature canonical recipe.
    return synthetic_frame(n=60, seed=7)


class CvSelectionIsolation(unittest.TestCase):
    """_cv_select_k must fit every candidate k using ONLY that outer fold's
    own training rows -- never the outer test set, never the full training
    partition."""

    def test_knn_fit_never_receives_more_rows_than_the_cv_fold_provides(self):
        frame = _tiny_frame()
        cols = kma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        cols_and_frame = kma._outer_split(frame, cols)
        X_train, X_test, y_train, y_test = cols_and_frame

        from sklearn.neighbors import KNeighborsRegressor

        seen_fit_sizes = []
        real_fit = KNeighborsRegressor.fit

        def spy_fit(self, X_arg, y_arg, *a, **kw):
            seen_fit_sizes.append(len(y_arg))
            return real_fit(self, X_arg, y_arg, *a, **kw)

        k_max = min(5, len(y_train) - 1)
        with mock.patch.object(KNeighborsRegressor, "fit", spy_fit):
            kma._cv_select_k(X_train, y_train, k_max=k_max)

        n = len(y_train)
        fold_train_n = n - (n // kma.N_SPLITS)
        self.assertTrue(seen_fit_sizes)
        for size in seen_fit_sizes:
            self.assertLess(size, n, "a CV fold fit on the full training partition, not just its own fold")
            self.assertAlmostEqual(size, fold_train_n, delta=1)

    def test_deterministic_across_repeated_runs(self):
        frame = _tiny_frame()
        cols = kma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X_train, X_test, y_train, y_test = kma._outer_split(frame, cols)
        k_max = min(10, len(y_train) - 1)
        first = kma._cv_select_k(X_train, y_train, k_max=k_max)
        second = kma._cv_select_k(X_train, y_train, k_max=k_max)
        self.assertEqual(first["curve"], second["curve"])
        self.assertEqual(first["selected_k"], second["selected_k"])


class LockedTestIsolation(unittest.TestCase):
    """_locked_test_eval's final KNeighborsRegressor.fit must be called
    exactly once, with exactly the training rows -- the test rows must never
    reach .fit()."""

    def test_fit_called_exactly_once_with_exactly_the_training_rows(self):
        frame = _tiny_frame()
        cols = kma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X_train, X_test, y_train, y_test = kma._outer_split(frame, cols)

        from sklearn.neighbors import KNeighborsRegressor

        seen_fit_sizes = []
        real_fit = KNeighborsRegressor.fit

        def spy_fit(self, X_arg, y_arg, *a, **kw):
            seen_fit_sizes.append(len(y_arg))
            return real_fit(self, X_arg, y_arg, *a, **kw)

        with mock.patch.object(KNeighborsRegressor, "fit", spy_fit):
            result = kma._locked_test_eval(X_train, y_train, X_test, y_test, k=3)

        self.assertEqual(seen_fit_sizes, [len(y_train)])
        self.assertEqual(result["n_train"], len(y_train))
        self.assertEqual(result["n_test"], len(y_test))

    def test_reproducible(self):
        frame = _tiny_frame()
        cols = kma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X_train, X_test, y_train, y_test = kma._outer_split(frame, cols)
        a = kma._locked_test_eval(X_train, y_train, X_test, y_test, k=3)
        b = kma._locked_test_eval(X_train, y_train, X_test, y_test, k=3)
        self.assertEqual(a, b)


class FittingSetEndpoint(unittest.TestCase):
    def test_k_equal_to_every_fitting_participant_predicts_the_training_mean(self):
        frame = _tiny_frame()
        cols = kma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X_train, X_test, y_train, y_test = kma._outer_split(frame, cols)
        ep = kma._fitting_set_endpoint(X_train, y_train, X_test, y_test)
        self.assertEqual(ep["k"], len(y_train))
        self.assertTrue(ep["all_predictions_equal_training_mean"])
        self.assertAlmostEqual(ep["train_mean"], float(np.mean(y_train)), places=4)


if __name__ == "__main__":
    unittest.main()
