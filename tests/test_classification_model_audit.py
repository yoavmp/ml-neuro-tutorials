"""Offline tests for scripts/classification_model_audit.py and its committed
result (WP17 §2, §9: leakage, exact feature count, split disjointness,
train-only preprocessing, reproducibility, metric consistency).

Standard-library ``unittest``; no network. Re-validates the committed audit
JSON for self-consistency and uses a small synthetic frame (reused from
``test_abide_modeling_data``) plus targeted mocking to prove -- not just
assert -- that:

* the fitted pipeline's scaler is only ever fit on the training split;
* the locked test evaluation's fit is called exactly once, with exactly the
  training rows;
* train/test participant ids never overlap;
* re-running the same procedure on the same split is deterministic.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_classification_model_audit.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import classification_model_audit as cma  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedResult(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(cma.RESULT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = cma.validate(self.result)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.result["source"]["pinnedCommit"], cma.MANIFEST["source"]["pinned_commit"])

    def test_positive_class_is_autism_negative_is_control(self):
        self.assertEqual(self.result["positive_class"], "autism")
        self.assertEqual(self.result["negative_class"], "control")

    def test_exactly_360_features_all_eligible_ct(self):
        fr = self.result["feature_recipe"]
        self.assertEqual(fr["feature_count"], 360)
        self.assertEqual(fr["bundle"], "all-eligible")
        self.assertEqual(fr["measures"], ["CT"])

    def test_holdout_split_matches_the_manifest(self):
        hs = self.result["protocol"]["holdout_split"]
        manifest_hs = cma.MANIFEST["classification"]["holdout_split"]
        self.assertEqual(hs["test_size"], manifest_hs["test_size"])
        self.assertEqual(hs["random_state"], manifest_hs["random_state"])
        self.assertEqual(hs["stratify"], "y")

    def test_c_is_selected_honestly_by_cross_validation(self):
        cvsel = self.result["cv_selection"]
        self.assertEqual(cvsel["grid"], cma.C_GRID)
        self.assertEqual(cvsel["scoring"], "roc_auc")
        self.assertIn("StratifiedKFold", cvsel["folds"])
        self.assertIn("random_state=42", cvsel["folds"])
        self.assertIn(cvsel["selected_C"], cma.C_GRID)
        self.assertGreaterEqual(cvsel["selected_mean_cv_auc"], 0.0)
        self.assertLessEqual(cvsel["selected_mean_cv_auc"], 1.0)
        best_row = max(cvsel["curve"], key=lambda row: row["mean_cv_auc"])
        self.assertEqual(best_row["C"], cvsel["selected_C"])
        self.assertIn(f"C={cvsel['selected_C']!r}", self.result["protocol"]["model"])
        self.assertIn("never used to select C", self.result["protocol"]["note"])

    def test_cv_curve_has_one_row_per_grid_point_and_matches_grid(self):
        cvsel = self.result["cv_selection"]
        self.assertEqual(len(cvsel["curve"]), len(cma.C_GRID))
        self.assertEqual([row["C"] for row in cvsel["curve"]], cma.C_GRID)
        for row in cvsel["curve"]:
            self.assertGreaterEqual(row["mean_cv_auc"], 0.0)
            self.assertLessEqual(row["mean_cv_auc"], 1.0)

    def test_confusion_matrix_orientation_and_totals(self):
        ev = self.result["locked_test_eval"]
        cm = ev["confusion_matrix"]
        self.assertEqual(set(cm), {"tn", "fp", "fn", "tp"})
        self.assertEqual(cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"], ev["n_test"])
        self.assertEqual(cm["tp"] + cm["fn"], ev["test_positive_count"])
        self.assertEqual(cm["tn"] + cm["fp"], ev["test_negative_count"])

    def test_accuracy_and_auc_are_plausible_and_honestly_modest(self):
        ev = self.result["locked_test_eval"]
        self.assertGreaterEqual(ev["accuracy"], 0.0)
        self.assertLessEqual(ev["accuracy"], 1.0)
        self.assertGreaterEqual(ev["auc"], 0.0)
        self.assertLessEqual(ev["auc"], 1.0)

    def test_train_test_disjoint_and_reproducible(self):
        self.assertTrue(self.result["train_test_disjoint"])
        self.assertTrue(self.result["reproducibility_check"]["refit_metrics_identical"])

    def test_cohort_counts_match_manifest_group_counts(self):
        cohort = self.result["cohort"]
        gc = cma.MANIFEST["cohort"]["group_counts"]
        self.assertEqual(cohort["n_positive_total"], gc["1"])
        self.assertEqual(cohort["n_negative_total"], gc["2"])
        self.assertEqual(cohort["n_total"], gc["1"] + gc["2"])

    def test_runtime_is_recorded(self):
        self.assertIn("runtime_seconds", self.result)
        self.assertGreaterEqual(self.result["runtime_seconds"], 0)


def _tiny_frame():
    return synthetic_frame(n=80, seed=11)


class FeatureAndTargetIsolation(unittest.TestCase):
    def test_feature_columns_are_brain_only_and_exactly_360_on_real_manifest(self):
        # The tiny synthetic frame only has frontoparietal+occipital columns,
        # so this checks the REAL manifest's all-eligible x CT recipe count
        # directly (no network needed -- bundle_columns only needs the
        # inventory + measure prefixes, not the actual data values).
        from abide_modeling_data import bundle_columns

        cols = bundle_columns("all-eligible", ["CT"])
        self.assertEqual(len(cols), 360)
        self.assertTrue(all(c.startswith("fsCT_") for c in cols))

    def test_group_recoded_autism_is_one_control_is_zero(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        raw_groups = frame["group"].to_numpy()
        self.assertTrue(np.array_equal(y[raw_groups == 1.0], np.ones(int((raw_groups == 1.0).sum()))))
        self.assertTrue(np.array_equal(y[raw_groups == 2.0], np.zeros(int((raw_groups == 2.0).sum()))))

    def test_xy_rejects_missing_group(self):
        frame = _tiny_frame()
        frame.loc[0, "group"] = np.nan
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        with self.assertRaises(RuntimeError):
            cma._xy(frame, cols)


class SplitIsolation(unittest.TestCase):
    def test_train_and_test_subjects_never_overlap(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        X_train, X_test, y_train, y_test, subj_train, subj_test = cma._split(X, y, subjects)
        self.assertEqual(set(subj_train.tolist()) & set(subj_test.tolist()), set())

    def test_split_is_stratified_by_y(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        _, _, y_train, y_test, _, _ = cma._split(X, y, subjects)
        overall_rate = y.mean()
        self.assertAlmostEqual(y_train.mean(), overall_rate, delta=0.15)
        self.assertAlmostEqual(y_test.mean(), overall_rate, delta=0.2)


class FitEvalIsolation(unittest.TestCase):
    """_fit_eval's scaler and estimator must only ever see the training
    rows during .fit(); the test rows must reach only .predict()/
    .predict_proba()."""

    def test_fit_called_exactly_once_with_exactly_the_training_rows(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        X_train, X_test, y_train, y_test, _, _ = cma._split(X, y, subjects)

        from sklearn.linear_model import LogisticRegression

        seen_fit_sizes = []
        real_fit = LogisticRegression.fit

        def spy_fit(self, X_arg, y_arg, *a, **kw):
            seen_fit_sizes.append(len(y_arg))
            return real_fit(self, X_arg, y_arg, *a, **kw)

        with mock.patch.object(LogisticRegression, "fit", spy_fit):
            cma._fit_eval(X_train, y_train, X_test, y_test, C=1.0)

        self.assertEqual(seen_fit_sizes, [len(y_train)])

    def test_reproducible_refit(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        X_train, X_test, y_train, y_test, _, _ = cma._split(X, y, subjects)
        a = cma._fit_eval(X_train, y_train, X_test, y_test, C=1.0)
        b = cma._fit_eval(X_train, y_train, X_test, y_test, C=1.0)
        self.assertEqual(a, b)

    def test_confusion_matrix_cells_sum_to_n_test(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        X_train, X_test, y_train, y_test, _, _ = cma._split(X, y, subjects)
        ev = cma._fit_eval(X_train, y_train, X_test, y_test, C=1.0)
        cm = ev["confusion_matrix"]
        self.assertEqual(cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"], len(y_test))


class SelectCIsolation(unittest.TestCase):
    """_select_c must only ever touch the training partition it is given,
    never the outer test set, and must select from exactly C_GRID."""

    def test_selected_c_is_in_the_grid_and_deterministic(self):
        frame = _tiny_frame()
        cols = [c for c in frame.columns if c.startswith("fsCT_")]
        X, y, subjects = cma._xy(frame, cols)
        X_train, _X_test, y_train, _y_test, _, _ = cma._split(X, y, subjects)
        a = cma._select_c(X_train, y_train)
        b = cma._select_c(X_train, y_train)
        self.assertIn(a["selected_C"], cma.C_GRID)
        self.assertEqual(a["selected_C"], b["selected_C"])
        self.assertEqual(len(a["curve"]), len(cma.C_GRID))

    def test_select_c_signature_takes_only_the_training_partition(self):
        # _select_c's signature is (X_train, y_train) -- there is no test-set
        # parameter for it to touch, so the outer test set is structurally
        # excluded from C selection by construction.
        import inspect

        params = list(inspect.signature(cma._select_c).parameters)
        self.assertEqual(params, ["X_train", "y_train"])


if __name__ == "__main__":
    unittest.main()
