"""Offline tests for scripts/export_regression_catalog.py.

Standard-library ``unittest``; no network. The committed catalog artifact is
validated as-is; a tiny in-memory catalog is built from a synthetic frame.

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

    def test_shape_and_cohort(self):
        a = self.artifact
        self.assertEqual(a["activity"], "regression-compare")
        self.assertEqual(a["cohort"]["n"], 908)
        self.assertEqual(len(a["observed"]), 908)
        self.assertEqual(len(a["foldOf"]), 908)
        self.assertEqual(sorted(set(a["foldOf"])), [0, 1, 2, 3, 4])
        self.assertTrue(all(isinstance(v, int) for v in a["observed"]))

    def test_contains_no_participant_identifier(self):
        blob = json.dumps(self.artifact)
        for token in ('"subject"', '"SUB_ID"', '"SITE_ID"', '"site"', '"participant"'):
            self.assertNotIn(token, blob)

    def test_source_pins_match_the_manifest(self):
        src = self.artifact["source"]
        man = erc.MANIFEST["source"]
        self.assertEqual(src["pinnedCommit"], man["pinned_commit"])
        self.assertEqual(src["brainTableSha256"], man["brain_table"]["sha256"])
        self.assertEqual(src["phenotypeTableSha256"], man["phenotype_table"]["sha256"])

    def test_every_enabled_model_metric_recomputes_from_its_predictions(self):
        obs = self.artifact["observed"]
        for m in self.artifact["models"]:
            if m["disabled"]:
                self.assertNotIn("predicted", m)
                self.assertIn("reason", m)
                continue
            r2, mse = erc._metrics(obs, m["predicted"])
            self.assertAlmostEqual(r2, m["cvR2"], places=4)
            self.assertAlmostEqual(mse, m["cvMSE"], places=2)
            self.assertEqual(len(m["predicted"]), 908)

    def test_literature_bundle_does_not_win(self):
        by_key = {m["key"]: m for m in self.artifact["models"] if not m["disabled"]}
        # every FIQ model has negative held-out R^2 in this sample
        self.assertTrue(all(m["cvR2"] < 0 for m in by_key.values()))
        # the P-FIT frontoparietal thickness bundle does worse than the
        # similarly scoped occipital comparison bundle
        self.assertLess(by_key["frontoparietal__CT"]["cvR2"], by_key["occipital__CT"]["cvR2"])

    def test_a_high_dimensional_combination_is_disabled_with_a_reason(self):
        disabled = [m for m in self.artifact["models"] if m["disabled"]]
        self.assertTrue(disabled)
        for m in disabled:
            self.assertGreaterEqual(m["featureCount"], 0.7 * self.artifact["crossValidation"]["foldTrainN"])
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
        for m in artifact["models"]:
            self.assertFalse(m["disabled"])
            self.assertEqual(len(m["predicted"]), 300)

    def test_catalog_carries_no_identifier_column(self):
        artifact = erc.build_catalog(synthetic_frame(n=300, seed=1), self._mini_manifest())
        problems = erc.validate_catalog(artifact, self._mini_manifest())
        self.assertEqual(problems, [])
        self.assertNotIn("subject", json.dumps(artifact))

    def test_tampered_prediction_is_rejected(self):
        man = self._mini_manifest()
        artifact = erc.build_catalog(synthetic_frame(n=300, seed=2), man)
        artifact["models"][0]["predicted"][0] += 50.0
        problems = erc.validate_catalog(artifact, man)
        self.assertTrue(any("cvR2" in p or "cvMSE" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
