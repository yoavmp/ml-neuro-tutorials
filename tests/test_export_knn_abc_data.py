"""Offline tests for scripts/export_knn_abc_data.py.

Standard-library ``unittest``; no network. The committed manifest + binary
artifact is validated as-is; a tiny in-memory artifact is built from a
synthetic frame to exercise ``build_artifact`` / ``validate_artifact``
without downloading real data.

WP15 §3 rewrote this artifact from one large JSON file of nested number
arrays (schema v1) to a small JSON manifest + one compact binary payload
(schema v2, ``scripts/binary_asset.py``); this file supersedes the schema v1
version of the same tests -- see git history for that version.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_knn_abc_data.py'
"""

from __future__ import annotations

import copy
import io
import json
import os
import struct
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_knn_abc_data as eabc  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402

SIZE_BUDGET_MAX_BYTES = 1_000_000


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(eabc.MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.blob = eabc.BINARY_PATH.read_bytes()

    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = eabc.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_validator_finds_no_problems(self):
        self.assertEqual(eabc.validate_artifact(self.manifest, self.blob), [])

    def test_shape_and_split(self):
        m = self.manifest
        self.assertEqual(m["activity"], "knn-abc")
        self.assertEqual(m["target"]["name"], "age")
        self.assertEqual(m["featureRecipe"]["featureCount"], 360)
        self.assertEqual(m["split"]["nTrain"], 753)
        self.assertEqual(m["split"]["nTest"], 251)
        self.assertEqual(m["split"]["kMax"], 251)
        self.assertEqual(m["sections"]["observedTrain"]["shape"], [753])
        self.assertEqual(m["sections"]["observedTest"]["shape"], [251])
        self.assertEqual(m["sections"]["neighborIndexA"]["shape"], [251, 251])
        self.assertEqual(m["sections"]["neighborIndexB"]["shape"], [753, 251])
        self.assertEqual(m["sections"]["neighborIndexC"]["shape"], [251, 251])

    def test_default_k_is_the_audit_selected_k(self):
        self.assertEqual(self.manifest["selectedKFromAudit"], 15)

    def test_contains_no_participant_identifier(self):
        blob_text = json.dumps(self.manifest)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob_text)

    def test_source_pins_match_the_manifest(self):
        src = self.manifest["source"]
        man = eabc.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])

    def test_binary_digest_and_length_match(self):
        b = self.manifest["binary"]
        self.assertEqual(b["byteLength"], len(self.blob))
        self.assertEqual(b["sha256"], eabc.sha256_hex(self.blob))

    def test_k1_endpoint_b_and_c_are_exact_resubstitution_a_is_not(self):
        logical = eabc._reconstruct_logical(self.manifest, self.blob)
        b_first = logical["neighborTargetsB"][:, 0]
        c_first = logical["neighborTargetsC"][:, 0]
        import numpy as np

        self.assertTrue(np.allclose(b_first, logical["observedTrain"], atol=1e-2))
        self.assertTrue(np.allclose(c_first, logical["observedTest"], atol=1e-2))
        a_first = logical["neighborTargetsA"][:, 0]
        self.assertFalse(np.allclose(a_first, logical["observedTest"], atol=1e-2))

    def test_serialization_is_canonical(self):
        on_disk = eabc.MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertEqual(eabc.serialize_manifest(self.manifest), on_disk)

    def test_schema_version_is_2(self):
        self.assertEqual(self.manifest["schemaVersion"], 2)

    def test_no_obsolete_large_json_asset_remains(self):
        obsolete = eabc.DATA_DIR / "abide_knn_abc.json"
        self.assertFalse(obsolete.exists(), f"{obsolete} should have been deleted in favour of the binary format")

    def test_size_budget(self):
        self.assertLess(eabc.BINARY_PATH.stat().st_size, SIZE_BUDGET_MAX_BYTES)
        self.assertLess(eabc.MANIFEST_PATH.stat().st_size, SIZE_BUDGET_MAX_BYTES)

    def test_representative_k_recomputation_matches_expected_pattern(self):
        # WP14 §4.4 / §7.10: at k=1, B and C are perfect (every point is its
        # own neighbour); A is not. Recomputed independently here from the
        # reconstructed arrays, not merely asserted about the endpoint row.
        logical = eabc._reconstruct_logical(self.manifest, self.blob)

        def r2(obs, pred):
            obs = list(obs)
            pred = list(pred)
            mean_obs = sum(obs) / len(obs)
            ss_res = sum((o - p) ** 2 for o, p in zip(obs, pred))
            ss_tot = sum((o - mean_obs) ** 2 for o in obs)
            return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

        pred_a = logical["neighborTargetsA"][:, 0].tolist()
        pred_b = logical["neighborTargetsB"][:, 0].tolist()
        pred_c = logical["neighborTargetsC"][:, 0].tolist()
        r2_a = r2(logical["observedTest"].tolist(), pred_a)
        r2_b = r2(logical["observedTrain"].tolist(), pred_b)
        r2_c = r2(logical["observedTest"].tolist(), pred_c)
        self.assertAlmostEqual(r2_b, 1.0, places=2)
        self.assertAlmostEqual(r2_c, 1.0, places=2)
        self.assertLess(r2_a, r2_b)
        self.assertLess(r2_a, r2_c)


def _mini_manifest():
    man = copy.deepcopy(eabc.MANIFEST)
    man["knn"]["canonical_recipe"] = {"bundle": "frontoparietal", "measures": ["CT"]}
    return man


class BuildFromSyntheticFrame(unittest.TestCase):
    def test_build_and_validate_round_trip(self):
        frame = synthetic_frame(n=300, seed=3)
        man = _mini_manifest()
        manifest_json, blob = eabc.build_artifact(frame, man)
        self.assertEqual(eabc.validate_artifact(manifest_json, blob, man), [])
        n_train, n_test, k_max = (
            manifest_json["split"]["nTrain"],
            manifest_json["split"]["nTest"],
            manifest_json["split"]["kMax"],
        )
        self.assertEqual(k_max, min(n_train, n_test))
        logical = eabc._reconstruct_logical(manifest_json, blob)
        self.assertEqual(logical["neighborTargetsA"].shape, (n_test, k_max))
        self.assertEqual(logical["neighborTargetsB"].shape, (n_train, k_max))
        self.assertEqual(logical["neighborTargetsC"].shape, (n_test, k_max))

    def test_tampered_shape_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = eabc.build_artifact(synthetic_frame(n=300, seed=2), man)
        manifest_json["sections"]["neighborIndexA"]["shape"] = [1, 1]
        problems = eabc.validate_artifact(manifest_json, blob, man)
        self.assertTrue(any("neighborIndexA" in p for p in problems))

    def test_tampered_k1_endpoint_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = eabc.build_artifact(synthetic_frame(n=300, seed=6), man)
        sec = manifest_json["sections"]["neighborIndexB"]
        mutable = bytearray(blob)
        # point the first query row's nearest neighbour at a DIFFERENT (but
        # in-range) reference row than its true self-match.
        mutable[sec["byteOffset"] : sec["byteOffset"] + 2] = struct.pack("<H", 1)
        problems = eabc.validate_artifact(manifest_json, bytes(mutable), man)
        self.assertTrue(any("neighborTargetsB" in p for p in problems))

    def test_out_of_range_index_is_rejected(self):
        man = _mini_manifest()
        manifest_json, blob = eabc.build_artifact(synthetic_frame(n=300, seed=7), man)
        sec = manifest_json["sections"]["neighborIndexC"]
        mutable = bytearray(blob)
        mutable[sec["byteOffset"] : sec["byteOffset"] + 2] = struct.pack("<H", 65000)
        problems = eabc.validate_artifact(manifest_json, bytes(mutable), man)
        self.assertTrue(any("out-of-range" in p for p in problems))

    def test_no_identifier_leak(self):
        manifest_json, _blob = eabc.build_artifact(synthetic_frame(n=300, seed=1), _mini_manifest())
        self.assertNotIn("subject", json.dumps(manifest_json))


if __name__ == "__main__":
    unittest.main()
