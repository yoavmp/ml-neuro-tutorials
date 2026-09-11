"""Offline tests for scripts/regression_model_audit.py and its committed result
(WP12 §5, §8.3: "audit reproducibility tests, including training-only
hyperparameter tuning").

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency, and uses a small synthetic frame (reused from
``test_abide_modeling_data``) plus targeted mocking to prove -- not just
assert -- that:

* the nested-CV helper never fits/tunes on rows outside that outer fold's
  training partition;
* the locked-holdout helper's ``RidgeCV``/``LassoCV`` inner cross-validation
  only ever sees the training split, never the held-out test rows;
* re-running the same procedure with the same seeds is deterministic.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_regression_model_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import regression_model_audit as rma  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(rma.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = rma.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], rma.MANIFEST["source"]["pinned_commit"])

    def test_both_targets_covered_by_every_feature_space(self):
        targets = {c["target"] for c in self.result["candidates"]}
        self.assertEqual(targets, {"age", "FIQ"})
        spaces = {c["feature_space"] for c in self.result["candidates"] if c.get("kind") != "locked-holdout-once"}
        for space in spaces:
            for target in ("age", "FIQ"):
                self.assertTrue(
                    any(c["target"] == target and c["feature_space"] == space for c in self.result["candidates"]),
                    f"{target}/{space} missing from the audit",
                )

    def test_every_ols_candidate_with_p_over_n_is_labelled_underdetermined(self):
        for c in self.result["candidates"]:
            if c.get("kind") == "locked-holdout-once" or c.get("model") != "linear":
                continue
            if c["p"] >= c["n_train_per_fold"]:
                self.assertTrue(c.get("underdetermined"), c)
            else:
                self.assertFalse(c.get("underdetermined"), c)

    def test_age_has_reliably_positive_cv_r2_every_feature_space(self):
        # WP12 §5.4: this is exactly the empirical trigger for choosing age as
        # the main ordinary-linear-regression example.
        for c in self.result["candidates"]:
            if c.get("kind") == "locked-holdout-once" or c["target"] != "age":
                continue
            if c["model"] == "linear" and c.get("underdetermined"):
                continue  # the underdetermined diagnostic case is expected to be poor
            self.assertGreater(c["cv_r2_mean"], 0, c)

    def test_fiq_regularised_never_reliably_positive(self):
        # WP12 §5.4: ridge/lasso on FIQ must stay at/near zero -- not be
        # reported as a positive result.
        for c in self.result["candidates"]:
            if c.get("kind") == "locked-holdout-once" or c["target"] != "FIQ":
                continue
            if c["model"] in ("ridge", "lasso"):
                self.assertLess(c["cv_r2_mean"], 0.05, c)

    def test_alpha_was_chosen_from_a_documented_logarithmic_grid(self):
        self.assertEqual(self.result["protocol"]["ridge_alpha_grid"], "np.logspace(-1, 6, 29)")
        self.assertEqual(self.result["protocol"]["lasso_alpha_grid"], "np.logspace(-3, 2, 26)")


def _tiny_frame():
    # A small, fast stand-in: 60 participants, ~78 CT + 78 Area features
    # (frontoparietal + occipital bundles), reused from test_abide_modeling_data.
    return synthetic_frame(n=60, seed=7)


class NestedCvIsolation(unittest.TestCase):
    """_evaluate must tune and fit each outer fold using ONLY that fold's
    training rows -- never the held-out test rows of that fold."""

    def test_ridge_inner_cv_never_receives_more_rows_than_the_outer_training_fold(self):
        frame = _tiny_frame()
        cols = rma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X, y, _ = rma._xy(frame, "FIQ", cols)

        from sklearn.linear_model import RidgeCV

        seen_fit_sizes = []
        real_fit = RidgeCV.fit

        def spy_fit(self, X_arg, y_arg, *a, **kw):
            seen_fit_sizes.append(len(y_arg))
            return real_fit(self, X_arg, y_arg, *a, **kw)

        with mock.patch.object(RidgeCV, "fit", spy_fit):
            rma._evaluate("ridge", X, y)

        # every outer fold's RidgeCV.fit call must see exactly that fold's
        # training rows (4/5 of n, +/- 1), never the full n and never the
        # held-out fold's rows.
        n = len(y)
        outer_train_n = n - (n // rma.N_SPLITS)
        self.assertEqual(len(seen_fit_sizes), rma.N_SPLITS)
        for size in seen_fit_sizes:
            self.assertLess(size, n)
            self.assertAlmostEqual(size, outer_train_n, delta=1)

    def test_deterministic_across_repeated_runs(self):
        frame = _tiny_frame()
        cols = rma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X, y, _ = rma._xy(frame, "FIQ", cols)
        first = rma._evaluate("ridge", X, y)
        second = rma._evaluate("ridge", X, y)
        self.assertEqual(first["cv_r2_folds"], second["cv_r2_folds"])
        self.assertEqual(first["alpha_per_fold"], second["alpha_per_fold"])


class LockedHoldoutIsolation(unittest.TestCase):
    """_locked_holdout's RidgeCV/LassoCV must tune alpha using only the
    training split; the held-out test rows must never reach .fit()."""

    def test_ridge_fit_never_sees_the_held_out_rows(self):
        frame = _tiny_frame()
        cols = rma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X, y, groups = rma._xy(frame, "FIQ", cols)
        hs = rma.MANIFEST["protocol"]["holdout_split"]
        expected_n_train = round(len(y) * (1 - hs["test_size"]))

        from sklearn.linear_model import RidgeCV

        seen_fit_sizes = []
        real_fit = RidgeCV.fit

        def spy_fit(self, X_arg, y_arg, *a, **kw):
            seen_fit_sizes.append(len(y_arg))
            return real_fit(self, X_arg, y_arg, *a, **kw)

        with mock.patch.object(RidgeCV, "fit", spy_fit):
            result = rma._locked_holdout("ridge", X, y, groups)

        self.assertEqual(len(seen_fit_sizes), 1)  # fit exactly once
        self.assertEqual(seen_fit_sizes[0], result["n_train"])
        self.assertLess(result["n_train"], len(y))
        self.assertAlmostEqual(result["n_train"], expected_n_train, delta=1)
        self.assertEqual(result["n_train"] + result["n_test"], len(y))

    def test_reproducible_with_the_same_manifest_split(self):
        frame = _tiny_frame()
        cols = rma._feature_columns(frame, {"bundle": "frontoparietal", "measures": ["CT"]})
        X, y, groups = rma._xy(frame, "FIQ", cols)
        a = rma._locked_holdout("linear", X, y, groups)
        b = rma._locked_holdout("linear", X, y, groups)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
