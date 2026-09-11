"""Offline tests for scripts/export_knn_abc_data.py.

Standard-library ``unittest``; no network. The committed artifact is
validated as-is; a tiny in-memory artifact is built from a synthetic frame to
exercise ``build_artifact`` / ``validate_artifact`` without downloading real
data.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_knn_abc_data.py'
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

import export_knn_abc_data as eabc  # noqa: E402
from test_abide_modeling_data import synthetic_frame  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(eabc.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = eabc.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_validator_finds_no_problems(self):
        self.assertEqual(eabc.validate_artifact(self.artifact), [])

    def test_shape_and_split(self):
        a = self.artifact
        self.assertEqual(a["activity"], "knn-abc")
        self.assertEqual(a["target"]["name"], "age")
        self.assertEqual(a["featureRecipe"]["featureCount"], 360)
        self.assertEqual(a["split"]["nTrain"], 753)
        self.assertEqual(a["split"]["nTest"], 251)
        self.assertEqual(a["split"]["kMax"], 251)
        self.assertEqual(len(a["observedTrain"]), 753)
        self.assertEqual(len(a["observedTest"]), 251)
        self.assertEqual(len(a["neighborTargetsA"]), 251)
        self.assertEqual(len(a["neighborTargetsB"]), 753)
        self.assertEqual(len(a["neighborTargetsC"]), 251)
        self.assertTrue(all(len(row) == 251 for row in a["neighborTargetsA"]))
        self.assertTrue(all(len(row) == 251 for row in a["neighborTargetsB"]))
        self.assertTrue(all(len(row) == 251 for row in a["neighborTargetsC"]))

    def test_default_k_is_the_audit_selected_k(self):
        self.assertEqual(self.artifact["selectedKFromAudit"], 15)

    def test_contains_no_participant_identifier(self):
        blob = json.dumps(self.artifact)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob)

    def test_source_pins_match_the_manifest(self):
        src = self.artifact["source"]
        man = eabc.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])

    def test_k1_endpoint_b_and_c_are_exact_resubstitution_a_is_not(self):
        a = self.artifact
        b_first = [row[0] for row in a["neighborTargetsB"]]
        c_first = [row[0] for row in a["neighborTargetsC"]]
        self.assertEqual(b_first, a["observedTrain"])
        self.assertEqual(c_first, a["observedTest"])
        a_first = [row[0] for row in a["neighborTargetsA"]]
        self.assertNotEqual(a_first, a["observedTest"])

    def test_serialization_is_canonical(self):
        on_disk = eabc.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(eabc.serialize(self.artifact), on_disk)

    def test_representative_k_recomputation_matches_expected_pattern(self):
        # WP14 §4.4 / §7.10: at k=1, B and C are perfect (every point is its
        # own neighbour); A is not. Recomputed independently here from the
        # stored arrays, not merely asserted about the endpoint row.
        a = self.artifact

        def r2(obs, pred):
            obs = list(obs)
            pred = list(pred)
            mean_obs = sum(obs) / len(obs)
            ss_res = sum((o - p) ** 2 for o, p in zip(obs, pred))
            ss_tot = sum((o - mean_obs) ** 2 for o in obs)
            return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

        k = 1
        pred_a = [row[0] for row in a["neighborTargetsA"]]
        pred_b = [row[0] for row in a["neighborTargetsB"]]
        pred_c = [row[0] for row in a["neighborTargetsC"]]
        r2_a = r2(a["observedTest"], pred_a)
        r2_b = r2(a["observedTrain"], pred_b)
        r2_c = r2(a["observedTest"], pred_c)
        self.assertAlmostEqual(r2_b, 1.0, places=6)
        self.assertAlmostEqual(r2_c, 1.0, places=6)
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
        artifact = eabc.build_artifact(frame, man)
        self.assertEqual(eabc.validate_artifact(artifact, man), [])
        n_train, n_test, k_max = (
            artifact["split"]["nTrain"],
            artifact["split"]["nTest"],
            artifact["split"]["kMax"],
        )
        self.assertEqual(k_max, min(n_train, n_test))
        self.assertEqual(len(artifact["neighborTargetsA"]), n_test)
        self.assertEqual(len(artifact["neighborTargetsB"]), n_train)
        self.assertEqual(len(artifact["neighborTargetsC"]), n_test)

    def test_tampered_shape_is_rejected(self):
        man = _mini_manifest()
        artifact = eabc.build_artifact(synthetic_frame(n=300, seed=2), man)
        artifact["neighborTargetsA"] = artifact["neighborTargetsA"][:-1]
        problems = eabc.validate_artifact(artifact, man)
        self.assertTrue(any("neighborTargetsA" in p for p in problems))

    def test_tampered_k1_endpoint_is_rejected(self):
        man = _mini_manifest()
        artifact = eabc.build_artifact(synthetic_frame(n=300, seed=6), man)
        artifact["neighborTargetsB"][0][0] = 9999.0
        problems = eabc.validate_artifact(artifact, man)
        self.assertTrue(any("neighborTargetsB" in p for p in problems))

    def test_no_identifier_leak(self):
        artifact = eabc.build_artifact(synthetic_frame(n=300, seed=1), _mini_manifest())
        self.assertNotIn("subject", json.dumps(artifact))


if __name__ == "__main__":
    unittest.main()
