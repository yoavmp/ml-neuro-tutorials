"""Offline tests for scripts/export_boosting_step_widget.py and its committed
data artifact (WP32, Exercise 7 "Build a Boosted Model").

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes the update equation independently for several stages
to prove the committed numbers, not merely assert they exist.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_boosting_step_widget_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_boosting_step_widget as bsw  # noqa: E402
from semantic_json_compare import DEFAULT_ABS_TOL, assert_semantically_equal  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(bsw.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = bsw.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_matches_a_fresh_recomputation(self):
        assert_semantically_equal(self.data, bsw.build_data(), abs_tol=DEFAULT_ABS_TOL)

    def test_observation_count_is_exactly_24(self):
        self.assertEqual(len(self.data["observations"]), 24)
        self.assertEqual(self.data["generatingProcess"]["nObservations"], 24)

    def test_explicitly_marked_synthetic(self):
        note = self.data["syntheticDataNote"].lower()
        self.assertTrue("synthetic" in note or "simulated" in note)
        self.assertIn("not abide", note)

    def test_seed_was_fixed_before_generation_no_search(self):
        gp = self.data["generatingProcess"]
        self.assertEqual(gp["seed"], bsw.SEED)
        self.assertIn("no seed search", gp["seedNote"].lower())

    def test_learning_rates_match_the_manifest(self):
        self.assertEqual(self.data["learningRates"], bsw.LEARNING_RATES)
        self.assertEqual(self.data["nStages"], bsw.N_STAGES)
        self.assertGreaterEqual(self.data["nStages"], 10)

    def test_stump_settings_are_max_depth_1(self):
        self.assertEqual(self.data["stumpSettings"]["maxDepth"], 1)

    def test_stage_0_equals_the_training_target_mean_for_every_learning_rate(self):
        mean_y = sum(o["y"] for o in self.data["observations"]) / len(self.data["observations"])
        for eta in self.data["learningRates"]:
            stages = self.data["stagesByLearningRate"][str(eta)]
            stage0 = stages[0]
            self.assertIsNone(stage0["stump"])
            for v in stage0["ensemblePrediction"]:
                self.assertAlmostEqual(v, mean_y, places=1)

    def test_every_update_follows_the_declared_equation(self):
        # yhat_i^(m) = yhat_i^(m-1) + eta * f_m(x_i), recomputed independently
        # of the script's own build logic, for every stage of every learning
        # rate.
        for eta in self.data["learningRates"]:
            stages = self.data["stagesByLearningRate"][str(eta)]
            for m in range(1, len(stages)):
                prev = stages[m - 1]["ensemblePrediction"]
                cur = stages[m]
                for i, (p, tree_pred) in enumerate(zip(prev, cur["treePrediction"])):
                    expected = p + eta * tree_pred
                    self.assertAlmostEqual(expected, cur["ensemblePrediction"][i], places=1)

    def test_training_mse_generally_decreases_with_more_stages(self):
        for eta in self.data["learningRates"]:
            stages = self.data["stagesByLearningRate"][str(eta)]
            self.assertLess(stages[-1]["trainMSE"], stages[0]["trainMSE"])

    def test_larger_learning_rate_reduces_training_error_faster_at_a_fixed_stage(self):
        # A smaller learning rate should not have LOWER training MSE than a
        # larger one at the same early stage, for this dataset/grid (the
        # notebook's stated lesson that smaller learning rates need more
        # trees to catch up).
        stage_index = 3
        rates = sorted(self.data["learningRates"])
        mses = [self.data["stagesByLearningRate"][str(r)][stage_index]["trainMSE"] for r in rates]
        for a, b in zip(mses, mses[1:]):
            self.assertGreaterEqual(a, b - 1e-6)

    def test_no_non_finite_values_anywhere(self):
        import math

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


if __name__ == "__main__":
    unittest.main()
