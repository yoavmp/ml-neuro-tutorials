"""Offline tests for scripts/export_knn_explore_data.py.

Standard-library ``unittest``; no network. The committed artifact is
validated as-is; a tiny in-memory artifact is built from a synthetic frame to
exercise ``build_artifact`` / ``validate_artifact`` without downloading real
data.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_knn_explore_data.py'
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

import export_knn_explore_data as ekd  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ekd.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = ekd.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_validator_finds_no_problems(self):
        self.assertEqual(ekd.validate_artifact(self.artifact), [])

    def test_shape_and_split(self):
        a = self.artifact
        self.assertEqual(a["activity"], "knn-explore")
        self.assertEqual(a["target"]["name"], "age")
        self.assertEqual(a["featureRecipe"]["featureCount"], 360)
        self.assertEqual(a["split"]["nOuterTrain"], 753)
        self.assertEqual(a["split"]["nFit"], 564)
        self.assertEqual(a["split"]["nValidation"], 189)
        self.assertEqual(len(a["observedValidation"]), 189)
        self.assertEqual(len(a["observedFitting"]), 564)
        self.assertEqual(len(a["neighborTargetsByProximity"]), 189)
        self.assertTrue(all(len(row) == 564 for row in a["neighborTargetsByProximity"]))

    def test_contains_no_participant_identifier(self):
        blob = json.dumps(self.artifact)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob)

    def test_source_pins_match_the_manifest(self):
        src = self.artifact["source"]
        man = ekd.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])
        self.assertEqual(src["brainTableSha256"], man["brain_table"]["sha256"])
        self.assertEqual(src["phenotypeTableSha256"], man["phenotype_table"]["sha256"])

    def test_endpoint_k1_is_perfect_resubstitution(self):
        curve = self.artifact["curve"]
        self.assertAlmostEqual(curve["fitR2"][0], 1.0, places=6)

    def test_endpoint_k_equals_n_fit_is_the_constant_mean_predictor(self):
        curve = self.artifact["curve"]
        self.assertAlmostEqual(curve["fitR2"][-1], 0.0, places=3)

    def test_validation_optimal_k_is_the_argmax_of_val_r2(self):
        a = self.artifact
        best = max(a["curve"]["valR2"])
        self.assertAlmostEqual(a["curve"]["valR2"][a["validationOptimalK"] - 1], best, places=9)

    def test_audit_selected_k_is_a_genuinely_usable_model(self):
        a = self.artifact
        self.assertEqual(a["selectedKFromAudit"], 15)
        self.assertGreater(a["curve"]["valR2"][a["selectedKFromAudit"] - 1], 0)

    def test_serialization_is_canonical(self):
        on_disk = ekd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ekd.serialize(self.artifact), on_disk)

    def test_schema_version_is_2(self):
        self.assertEqual(self.artifact["schemaVersion"], 2)

    def test_three_training_samples_present_and_shaped(self):
        a = self.artifact
        samples = a["trainingSamples"]
        self.assertEqual(set(samples), {"A", "B", "C"})
        n_fit, n_val = a["split"]["nFit"], a["split"]["nValidation"]
        for label, sample in samples.items():
            with self.subTest(sample=label):
                rows = sample["neighborTargetsByProximity"]
                self.assertEqual(len(rows), n_val)
                self.assertTrue(all(len(row) == n_fit for row in rows))
                # independent structural re-verification of the k=n_fit
                # endpoint for every sample (WP14 §7.14)
                for row in rows:
                    self.assertAlmostEqual(sum(row) / n_fit, sample["fitTargetMean"], places=3)

    def test_training_sample_a_matches_the_top_level_baseline(self):
        a = self.artifact
        self.assertEqual(a["trainingSamples"]["A"]["neighborTargetsByProximity"], a["neighborTargetsByProximity"])
        self.assertEqual(a["trainingSamples"]["A"]["fitTargetMean"], a["fitTargetMean"])

    def test_training_samples_b_and_c_are_genuinely_different_draws(self):
        # bootstrap resamples of the same pool must not be byte-identical to A
        a = self.artifact
        self.assertNotEqual(
            a["trainingSamples"]["B"]["neighborTargetsByProximity"],
            a["trainingSamples"]["A"]["neighborTargetsByProximity"],
        )
        self.assertNotEqual(
            a["trainingSamples"]["C"]["neighborTargetsByProximity"],
            a["trainingSamples"]["A"]["neighborTargetsByProximity"],
        )
        self.assertNotEqual(
            a["trainingSamples"]["B"]["neighborTargetsByProximity"],
            a["trainingSamples"]["C"]["neighborTargetsByProximity"],
        )

    def test_independent_variance_and_bias_proxy_recomputation_at_representative_k(self):
        # WP14 §7.13: independent verification of the variance proxy and the
        # bias-like proxy, mirroring the exact client-side formulas
        # (interactive/src/knn-explore.ts) against the committed artifact.
        a = self.artifact
        n_val = a["split"]["nValidation"]
        samples = [a["trainingSamples"][k]["neighborTargetsByProximity"] for k in ("A", "B", "C")]
        observed = a["observedValidation"]

        for k in (1, a["selectedKFromAudit"], a["split"]["nFit"]):
            preds = [[sum(row[:k]) / k for row in sample] for sample in samples]  # 3 x n_val
            # variance proxy: mean across validation participants of the SD of
            # the 3 samples' predictions for that participant
            sds = []
            for i in range(n_val):
                vals = [preds[s][i] for s in range(3)]
                mean = sum(vals) / 3
                var = sum((v - mean) ** 2 for v in vals) / 3
                sds.append(var**0.5)
            variance_proxy = sum(sds) / n_val
            self.assertGreaterEqual(variance_proxy, 0.0)
            if k == 1:
                # smallest k: this dataset's fitting-set nearest neighbour is
                # sensitive to which training draw was used
                self.assertGreater(variance_proxy, 0.0)
            if k == a["split"]["nFit"]:
                # k = n_fit: every sample's predictions collapse to that
                # sample's own (slightly different, since bootstrap) mean --
                # variance proxy is small but need not be exactly zero
                self.assertLess(variance_proxy, 1.0)

            # bias-like proxy: calibration slope of the ensemble-mean
            # prediction (average of the 3 samples) regressed on the observed
            # value; slope near 1 = little flattening, near 0 = fully flattened
            ensemble = [sum(preds[s][i] for s in range(3)) / 3 for i in range(n_val)]
            mean_obs = sum(observed) / n_val
            mean_ens = sum(ensemble) / n_val
            cov = sum((observed[i] - mean_obs) * (ensemble[i] - mean_ens) for i in range(n_val))
            var_obs = sum((o - mean_obs) ** 2 for o in observed)
            slope = cov / var_obs if var_obs > 0 else 0.0
            if k == a["split"]["nFit"]:
                # at k=n_fit every sample is a constant predictor -> slope is
                # exactly 0 (no relationship at all with the observed value)
                self.assertAlmostEqual(slope, 0.0, places=6)
            else:
                self.assertLessEqual(slope, 1.2)  # sanity bound, not a tight claim


def _mini_manifest():
    # The synthetic frame only carries frontoparietal + occipital ROIs (WP12's
    # test_abide_modeling_data.synthetic_frame), not the full all-eligible
    # 360-feature recipe -- so the mini manifest points the KNN recipe at the
    # frontoparietal bundle instead, purely for testing build_artifact /
    # validate_artifact without downloading real data.
    man = copy.deepcopy(ekd.MANIFEST)
    man["knn"]["canonical_recipe"] = {"bundle": "frontoparietal", "measures": ["CT"]}
    man["knn"]["dev_split"] = {"test_size": 0.3, "random_state": 7, "stratify": "group"}
    return man


class BuildFromSyntheticFrame(unittest.TestCase):
    def test_build_and_validate_round_trip(self):
        frame = synthetic_frame(n=300, seed=3)
        man = _mini_manifest()
        artifact = ekd.build_artifact(frame, man)
        self.assertEqual(ekd.validate_artifact(artifact, man), [])
        self.assertEqual(artifact["featureRecipe"]["bundle"], "frontoparietal")
        n_fit = artifact["split"]["nFit"]
        n_val = artifact["split"]["nValidation"]
        self.assertEqual(len(artifact["observedFitting"]), n_fit)
        self.assertEqual(len(artifact["observedValidation"]), n_val)
        self.assertEqual(len(artifact["neighborTargetsByProximity"]), n_val)
        self.assertTrue(all(len(row) == n_fit for row in artifact["neighborTargetsByProximity"]))
        self.assertEqual(len(artifact["curve"]["k"]), n_fit)

    def test_k_equals_n_fit_predicts_a_single_constant_for_every_validation_row(self):
        frame = synthetic_frame(n=300, seed=4)
        man = _mini_manifest()
        artifact = ekd.build_artifact(frame, man)
        n_fit = artifact["split"]["nFit"]
        fit_mean = artifact["fitTargetMean"]
        for row in artifact["neighborTargetsByProximity"]:
            predicted_at_k_max = sum(row) / n_fit
            self.assertAlmostEqual(predicted_at_k_max, fit_mean, places=3)

    def test_catalog_carries_no_identifier_column(self):
        artifact = ekd.build_artifact(synthetic_frame(n=300, seed=1), _mini_manifest())
        problems = ekd.validate_artifact(artifact, _mini_manifest())
        self.assertEqual(problems, [])
        self.assertNotIn("subject", json.dumps(artifact))

    def test_tampered_curve_is_rejected(self):
        man = _mini_manifest()
        artifact = ekd.build_artifact(synthetic_frame(n=300, seed=2), man)
        artifact["curve"]["k"][3] = 999
        problems = ekd.validate_artifact(artifact, man)
        self.assertTrue(any("curve.k" in p for p in problems))

    def test_tampered_endpoint_is_rejected(self):
        man = _mini_manifest()
        artifact = ekd.build_artifact(synthetic_frame(n=300, seed=5), man)
        artifact["curve"]["fitR2"][0] = 0.5
        problems = ekd.validate_artifact(artifact, man)
        self.assertTrue(any("perfect resubstitution" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
