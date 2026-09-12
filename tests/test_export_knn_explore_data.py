"""Offline tests for scripts/export_knn_explore_data.py.

Standard-library ``unittest``; no network. The committed manifest + binary
artifact is validated as-is; a tiny in-memory artifact is built from a
synthetic frame to exercise ``build_artifact`` / ``validate_artifact``
without downloading real data.

WP15 §3 rewrote this artifact from one large JSON file of nested number
arrays (schema v2) to a small JSON manifest + one compact binary payload
(schema v3, ``scripts/binary_asset.py``); this file supersedes the schema v2
version of the same tests -- see git history for that version.

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

# WP15 §3.5: combined baseline (WP14) was 4,569,372 bytes for both KNN
# artifacts together; target at least a 50% reduction and no individual
# committed runtime-data object above 1,000,000 bytes.
SIZE_BUDGET_MAX_BYTES = 1_000_000


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(ekd.MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.blob = ekd.BINARY_PATH.read_bytes()

    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = ekd.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_validator_finds_no_problems(self):
        self.assertEqual(ekd.validate_artifact(self.manifest, self.blob), [])

    def test_shape_and_split(self):
        m = self.manifest
        self.assertEqual(m["activity"], "knn-explore")
        self.assertEqual(m["target"]["name"], "age")
        self.assertEqual(m["featureRecipe"]["featureCount"], 360)
        self.assertEqual(m["split"]["nOuterTrain"], 753)
        self.assertEqual(m["split"]["nFit"], 564)
        self.assertEqual(m["split"]["nValidation"], 189)
        self.assertEqual(m["sections"]["observedValidation"]["shape"], [189])
        self.assertEqual(m["sections"]["observedFitting"]["shape"], [564])
        self.assertEqual(m["sections"]["neighborIndexA"]["shape"], [189, 564])

    def test_contains_no_participant_identifier(self):
        blob_text = json.dumps(self.manifest)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob_text)

    def test_source_pins_match_the_manifest(self):
        src = self.manifest["source"]
        man = ekd.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])
        self.assertEqual(src["brainTableSha256"], man["brain_table"]["sha256"])
        self.assertEqual(src["phenotypeTableSha256"], man["phenotype_table"]["sha256"])

    def test_endpoint_k1_is_perfect_resubstitution(self):
        logical = ekd._reconstruct_logical(self.manifest, self.blob)
        self.assertAlmostEqual(float(logical["curve"]["fitR2"][0]), 1.0, places=2)

    def test_endpoint_k_equals_n_fit_is_the_constant_mean_predictor(self):
        logical = ekd._reconstruct_logical(self.manifest, self.blob)
        self.assertAlmostEqual(float(logical["curve"]["fitR2"][-1]), 0.0, places=2)

    def test_validation_optimal_k_is_the_argmax_of_val_r2(self):
        m = self.manifest
        logical = ekd._reconstruct_logical(m, self.blob)
        val_r2 = logical["curve"]["valR2"]
        best = float(max(val_r2))
        self.assertAlmostEqual(float(val_r2[m["validationOptimalK"] - 1]), best, places=4)

    def test_audit_selected_k_is_a_genuinely_usable_model(self):
        m = self.manifest
        logical = ekd._reconstruct_logical(m, self.blob)
        self.assertEqual(m["selectedKFromAudit"], 15)
        self.assertGreater(float(logical["curve"]["valR2"][m["selectedKFromAudit"] - 1]), 0)

    def test_serialization_is_canonical(self):
        on_disk = ekd.MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertEqual(ekd.serialize_manifest(self.manifest), on_disk)

    def test_schema_version_is_3(self):
        self.assertEqual(self.manifest["schemaVersion"], 3)

    def test_binary_digest_and_length_match(self):
        b = self.manifest["binary"]
        self.assertEqual(b["byteLength"], len(self.blob))
        self.assertEqual(b["sha256"], ekd.sha256_hex(self.blob))

    def test_three_training_samples_present_and_shaped(self):
        logical = ekd._reconstruct_logical(self.manifest, self.blob)
        samples = logical["trainingSamples"]
        self.assertEqual(set(samples), {"A", "B", "C"})
        n_fit, n_val = self.manifest["split"]["nFit"], self.manifest["split"]["nValidation"]
        for label, sample in samples.items():
            with self.subTest(sample=label):
                rows = sample["neighborTargetsByProximity"]
                self.assertEqual(rows.shape, (n_val, n_fit))
                # independent structural re-verification of the k=n_fit
                # endpoint for every sample (WP14 §7.14)
                preds_at_k_nfit = rows.mean(axis=1)
                for pred in preds_at_k_nfit:
                    self.assertAlmostEqual(float(pred), sample["fitTargetMean"], places=2)

    def test_training_sample_a_matches_the_top_level_baseline(self):
        logical = ekd._reconstruct_logical(self.manifest, self.blob)
        import numpy as np

        self.assertTrue(
            np.array_equal(
                logical["trainingSamples"]["A"]["neighborTargetsByProximity"],
                logical["neighborTargetsByProximity"],
            )
        )
        self.assertEqual(logical["trainingSamples"]["A"]["fitTargetMean"], self.manifest["fitTargetMean"])

    def test_training_samples_b_and_c_are_genuinely_different_draws(self):
        import numpy as np

        logical = ekd._reconstruct_logical(self.manifest, self.blob)
        a = logical["trainingSamples"]["A"]["neighborTargetsByProximity"]
        b = logical["trainingSamples"]["B"]["neighborTargetsByProximity"]
        c = logical["trainingSamples"]["C"]["neighborTargetsByProximity"]
        self.assertFalse(np.array_equal(a, b))
        self.assertFalse(np.array_equal(a, c))
        self.assertFalse(np.array_equal(b, c))

    def test_no_obsolete_large_json_asset_remains(self):
        obsolete = ekd.DATA_DIR / "abide_knn_explore.json"
        self.assertFalse(obsolete.exists(), f"{obsolete} should have been deleted in favour of the binary format")

    def test_size_budget(self):
        # WP15 §3.5: no individual committed runtime-data object above 1 MB.
        self.assertLess(ekd.BINARY_PATH.stat().st_size, SIZE_BUDGET_MAX_BYTES)
        self.assertLess(ekd.MANIFEST_PATH.stat().st_size, SIZE_BUDGET_MAX_BYTES)

    def test_independent_variance_and_bias_proxy_recomputation_at_representative_k(self):
        # WP14 §7.13: independent verification of the variance proxy and the
        # bias-like proxy, mirroring the exact client-side formulas
        # (interactive/src/knn-explore.ts) against the committed (now
        # reconstructed-from-binary) artifact.
        m = self.manifest
        logical = ekd._reconstruct_logical(m, self.blob)
        n_val = m["split"]["nValidation"]
        samples = [logical["trainingSamples"][k]["neighborTargetsByProximity"].tolist() for k in ("A", "B", "C")]
        observed = logical["observedValidation"].tolist()

        for k in (1, m["selectedKFromAudit"], m["split"]["nFit"]):
            preds = [[sum(row[:k]) / k for row in sample] for sample in samples]  # 3 x n_val
            sds = []
            for i in range(n_val):
                vals = [preds[s][i] for s in range(3)]
                mean = sum(vals) / 3
                var = sum((v - mean) ** 2 for v in vals) / 3
                sds.append(var**0.5)
            variance_proxy = sum(sds) / n_val
            self.assertGreaterEqual(variance_proxy, 0.0)
            if k == 1:
                self.assertGreater(variance_proxy, 0.0)
            if k == m["split"]["nFit"]:
                self.assertLess(variance_proxy, 1.0)

            ensemble = [sum(preds[s][i] for s in range(3)) / 3 for i in range(n_val)]
            mean_obs = sum(observed) / n_val
            mean_ens = sum(ensemble) / n_val
            cov = sum((observed[i] - mean_obs) * (ensemble[i] - mean_ens) for i in range(n_val))
            var_obs = sum((o - mean_obs) ** 2 for o in observed)
            slope = cov / var_obs if var_obs > 0 else 0.0
            if k == m["split"]["nFit"]:
                self.assertAlmostEqual(slope, 0.0, places=2)
            else:
                self.assertLessEqual(slope, 1.2)


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
        manifest_json, blob = ekd.build_artifact(frame, man)
        self.assertEqual(ekd.validate_artifact(manifest_json, blob, man), [])
        self.assertEqual(manifest_json["featureRecipe"]["bundle"], "frontoparietal")
        n_fit = manifest_json["split"]["nFit"]
        n_val = manifest_json["split"]["nValidation"]
        logical = ekd._reconstruct_logical(manifest_json, blob)
        self.assertEqual(len(logical["observedFitting"]), n_fit)
        self.assertEqual(len(logical["observedValidation"]), n_val)
        self.assertEqual(logical["neighborTargetsByProximity"].shape, (n_val, n_fit))
        self.assertEqual(len(logical["curve"]["fitR2"]), n_fit)

    def test_k_equals_n_fit_predicts_a_single_constant_for_every_validation_row(self):
        frame = synthetic_frame(n=300, seed=4)
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(frame, man)
        n_fit = manifest_json["split"]["nFit"]
        fit_mean = manifest_json["fitTargetMean"]
        logical = ekd._reconstruct_logical(manifest_json, blob)
        for row in logical["neighborTargetsByProximity"]:
            predicted_at_k_max = float(sum(row) / n_fit)
            self.assertAlmostEqual(predicted_at_k_max, fit_mean, places=2)

    def test_artifact_carries_no_identifier_column(self):
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(synthetic_frame(n=300, seed=1), man)
        problems = ekd.validate_artifact(manifest_json, blob, man)
        self.assertEqual(problems, [])
        self.assertNotIn("subject", json.dumps(manifest_json))

    def test_tampered_section_shape_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(synthetic_frame(n=300, seed=2), man)
        manifest_json["sections"]["curveFitR2"]["shape"] = [999]
        problems = ekd.validate_artifact(manifest_json, blob, man)
        self.assertTrue(any("curveFitR2" in p for p in problems))

    def test_tampered_endpoint_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(synthetic_frame(n=300, seed=5), man)
        # corrupt curveFitR2's first float32 value in the binary blob directly
        sec = manifest_json["sections"]["curveFitR2"]
        mutable = bytearray(blob)
        import struct

        mutable[sec["byteOffset"] : sec["byteOffset"] + 4] = struct.pack("<f", 0.5)
        problems = ekd.validate_artifact(manifest_json, bytes(mutable), man)
        self.assertTrue(any("perfect resubstitution" in p for p in problems))

    def test_binary_digest_mismatch_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(synthetic_frame(n=300, seed=6), man)
        manifest_json["binary"]["sha256"] = "0" * 64
        problems = ekd.validate_artifact(manifest_json, blob, man)
        self.assertTrue(any("sha256" in p for p in problems))

    def test_out_of_range_index_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = ekd.build_artifact(synthetic_frame(n=300, seed=7), man)
        sec = manifest_json["sections"]["neighborIndexA"]
        mutable = bytearray(blob)
        import struct

        # first uint16 element of neighborIndexA -> an out-of-range index
        mutable[sec["byteOffset"] : sec["byteOffset"] + 2] = struct.pack("<H", 65000)
        problems = ekd.validate_artifact(manifest_json, bytes(mutable), man)
        self.assertTrue(any("out-of-range" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
