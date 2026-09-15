"""Offline tests for scripts/export_regression_catalog.py.

Standard-library ``unittest``; no network. The committed catalog artifact is
validated as-is; a tiny in-memory catalog is built from a synthetic frame.

WP19 correction: this catalog no longer scores entries with a hidden 5-fold
KFold / cross_val_predict procedure. Every entry now shares the same fixed,
reproducible train/test split (``protocol.holdout_split``) -- identical to
Exercise 2 Section 2 / Exercise 3's own outer holdout split.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_regression_catalog.py'
"""

from __future__ import annotations

import copy
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_regression_catalog as erc  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(erc.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = erc.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_validator_finds_no_problems(self):
        self.assertEqual(erc.validate_catalog(self.artifact), [])

    def test_schema_version_is_2(self):
        self.assertEqual(self.artifact["schemaVersion"], 2)

    def test_shape_and_cohort(self):
        a = self.artifact
        self.assertEqual(a["activity"], "regression-compare")
        # WP12: the catalog target is age (native, N=1004), not FIQ (N=908).
        self.assertEqual(a["target"]["name"], "age")
        self.assertEqual(a["cohort"]["n"], 1004)
        # WP19: one fixed 75/25 holdout split, identical to Exercise 2/3's own.
        hs = a["holdoutSplit"]
        self.assertEqual(hs["testSize"], 0.25)
        self.assertEqual(hs["randomState"], 42)
        self.assertEqual(hs["stratify"], "group")
        self.assertEqual(hs["nTrain"], 753)
        self.assertEqual(hs["nTest"], 251)
        self.assertEqual(hs["nTrain"] + hs["nTest"], a["cohort"]["n"])
        self.assertEqual(len(a["observedTest"]), 251)
        self.assertNotIn("foldOf", a)
        self.assertNotIn("crossValidation", a)
        # age is fractional years, not an integer standard score like FIQ.
        self.assertTrue(all(isinstance(v, (int, float)) for v in a["observedTest"]))
        self.assertFalse(all(float(v).is_integer() for v in a["observedTest"]))

    def test_contains_no_participant_identifier(self):
        blob = json.dumps(self.artifact)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob)

    def test_no_cross_validation_artifacts_remain(self):
        blob = json.dumps(self.artifact).lower()
        for token in ("kfold", "cross_val", "cross-validation", "cross validation", "fold"):
            self.assertNotIn(token, blob)

    def test_source_pins_match_the_manifest(self):
        src = self.artifact["source"]
        man = erc.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])
        self.assertEqual(src["brainTableSha256"], man["brain_table"]["sha256"])
        self.assertEqual(src["phenotypeTableSha256"], man["phenotype_table"]["sha256"])

    def test_every_enabled_model_metric_recomputes_from_its_predictions(self):
        obs = self.artifact["observedTest"]
        for m in self.artifact["models"]:
            if m["disabled"]:
                self.assertNotIn("predicted", m)
                self.assertIn("reason", m)
                continue
            r2, mse = erc._metrics(obs, m["predicted"])
            self.assertAlmostEqual(r2, m["testR2"], places=4)
            self.assertAlmostEqual(mse, m["testMSE"], places=2)
            self.assertEqual(len(m["predicted"]), 251)

    def test_most_bundles_predict_age_above_chance(self):
        # WP12: unlike FIQ (WP11, every model negative), age has a real signal
        # in cortical structure. WP19: under the single fixed held-out split
        # (higher variance than the old aggregated 5-fold estimate), almost
        # every enabled configuration is still positive; a couple of the
        # smallest, weakest bundle x measure combinations (e.g. parietal
        # Area/LGI) can legitimately land at or just below zero on one split.
        by_key = {m["key"]: m for m in self.artifact["models"] if not m["disabled"]}
        n_positive = sum(1 for m in by_key.values() if m["testR2"] > 0)
        self.assertGreaterEqual(n_positive, round(0.9 * len(by_key)))
        # the frontoparietal (originally IQ-literature) bundle is not the best
        # comparison bundle for age either -- occipital still edges it out.
        self.assertLess(by_key["frontoparietal__CT"]["testR2"], by_key["occipital__CT"]["testR2"])
        # the canonical all-eligible recipe, used throughout the course, is
        # clearly positive.
        self.assertGreater(by_key["all-eligible__CT"]["testR2"], 0.4)

    def test_canonical_recipe_matches_exercise_2s_own_worked_example(self):
        # all-eligible x CT is the exact recipe/split Exercise 2 Section 2 and
        # Exercise 3 use for their own worked examples (held-out R^2 = 0.469).
        canonical = next(m for m in self.artifact["models"] if m["key"] == "all-eligible__CT")
        self.assertAlmostEqual(canonical["testR2"], 0.469, places=3)

    def test_a_high_dimensional_combination_is_disabled_with_a_reason(self):
        disabled = [m for m in self.artifact["models"] if m["disabled"]]
        self.assertTrue(disabled)
        for m in disabled:
            self.assertGreaterEqual(m["featureCount"], 0.7 * self.artifact["holdoutSplit"]["nTrain"])
            self.assertIn("least squares", m["reason"])

    def test_serialization_is_canonical(self):
        on_disk = erc.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(erc.serialize(self.artifact), on_disk)


class BuildFromSyntheticFrame(unittest.TestCase):
    def _mini_manifest(self):
        man = copy.deepcopy(erc.MANIFEST)
        man["catalog"]["bundles"] = ["frontoparietal", "occipital"]
        man["catalog"]["measurement_subsets"] = [["CT"], ["Area"]]
        return man

    def test_build_and_validate_round_trip(self):
        frame = synthetic_frame(n=300, seed=3)
        man = self._mini_manifest()
        artifact = erc.build_catalog(frame, man)
        self.assertEqual(erc.validate_catalog(artifact, man), [])
        self.assertEqual(artifact["cohort"]["n"], 300)
        self.assertEqual(len(artifact["models"]), 4)  # 2 bundles x 2 subsets
        hs = artifact["holdoutSplit"]
        self.assertEqual(hs["nTrain"] + hs["nTest"], 300)
        for m in artifact["models"]:
            self.assertFalse(m["disabled"])
            self.assertEqual(len(m["predicted"]), hs["nTest"])

    def test_same_split_reused_across_every_bundle(self):
        # WP19: the same held-out participants must be used for every
        # feature-set comparison -- verified indirectly via observedTest
        # being identical regardless of which bundles/measures are compared.
        frame = synthetic_frame(n=300, seed=7)
        man = self._mini_manifest()
        a = erc.build_catalog(frame, man)
        man2 = copy.deepcopy(man)
        man2["catalog"]["bundles"] = ["frontoparietal"]
        man2["catalog"]["measurement_subsets"] = [["CT"]]
        b = erc.build_catalog(frame, man2)
        self.assertEqual(a["observedTest"], b["observedTest"])
        self.assertEqual(a["holdoutSplit"], b["holdoutSplit"])

    def test_catalog_carries_no_identifier_column(self):
        artifact = erc.build_catalog(synthetic_frame(n=300, seed=1), self._mini_manifest())
        problems = erc.validate_catalog(artifact, self._mini_manifest())
        self.assertEqual(problems, [])
        self.assertNotIn("subject", json.dumps(artifact))

    def test_scaler_and_model_fit_only_on_training_rows(self):
        # Proof, not just assertion: StandardScaler.fit / LinearRegression.fit
        # must only ever see the training rows -- never the held-out test rows.
        from unittest import mock

        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler

        frame = synthetic_frame(n=300, seed=5)
        man = self._mini_manifest()
        man["catalog"]["bundles"] = ["frontoparietal"]
        man["catalog"]["measurement_subsets"] = [["CT"]]

        seen_scaler_fit_sizes = []
        seen_model_fit_sizes = []
        real_scaler_fit = StandardScaler.fit
        real_model_fit = LinearRegression.fit

        def spy_scaler_fit(self, X, *a, **kw):
            seen_scaler_fit_sizes.append(len(X))
            return real_scaler_fit(self, X, *a, **kw)

        def spy_model_fit(self, X, y, *a, **kw):
            seen_model_fit_sizes.append(len(y))
            return real_model_fit(self, X, y, *a, **kw)

        with mock.patch.object(StandardScaler, "fit", spy_scaler_fit), mock.patch.object(
            LinearRegression, "fit", spy_model_fit
        ):
            artifact = erc.build_catalog(frame, man)

        n_train = artifact["holdoutSplit"]["nTrain"]
        self.assertTrue(seen_scaler_fit_sizes)
        self.assertTrue(seen_model_fit_sizes)
        for size in seen_scaler_fit_sizes:
            self.assertEqual(size, n_train)
        for size in seen_model_fit_sizes:
            self.assertEqual(size, n_train)

    def test_tampered_prediction_is_rejected(self):
        man = self._mini_manifest()
        artifact = erc.build_catalog(synthetic_frame(n=300, seed=2), man)
        artifact["models"][0]["predicted"][0] += 50.0
        problems = erc.validate_catalog(artifact, man)
        self.assertTrue(any("testR2" in p or "testMSE" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
