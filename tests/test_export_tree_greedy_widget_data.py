"""Offline tests for scripts/export_tree_greedy_widget.py and its committed
data artifact (WP30, Exercise 6 "Build a Tree Greedily" -- replaces WP29's
four-quadrant dataset with a noisy, two-continuous-feature simulation).

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes candidate thresholds, split MSE, and the seed search
independently (not just by re-calling the script's own functions) for a few
cases to prove the committed numbers, not merely assert they exist.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_tree_greedy_widget_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_tree_greedy_widget as tg  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(tg.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = tg.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_matches_a_fresh_recomputation(self):
        self.assertEqual(
            json.dumps(self.data, sort_keys=True),
            json.dumps(tg.build_data(), sort_keys=True),
        )

    def test_observation_count_is_exactly_16(self):
        self.assertEqual(len(self.data["observations"]), 16)
        self.assertEqual(self.data["generatingProcess"]["nObservations"], 16)

    def test_explicitly_marked_synthetic(self):
        note = self.data["syntheticDataNote"].lower()
        self.assertTrue("synthetic" in note or "simulated" in note)
        self.assertIn("not abide", note)

    def test_feature_labels_are_student_facing(self):
        self.assertEqual(self.data["features"]["x1"]["label"], "Brain measure 1")
        self.assertEqual(self.data["features"]["x2"]["label"], "Brain measure 2")

    def test_generating_process_matches_declared_formula_constants(self):
        gp = self.data["generatingProcess"]
        self.assertEqual(gp["x1"], {"distribution": "Normal", "mean": tg.MU1, "sd": tg.SD1})
        self.assertEqual(gp["x2"], {"distribution": "Normal", "mean": tg.MU2, "sd": tg.SD2})
        self.assertEqual(gp["intercept"], tg.INTERCEPT)
        self.assertEqual(gp["beta1"], tg.BETA1)
        self.assertEqual(gp["beta2"], tg.BETA2)
        self.assertEqual(gp["gamma"], tg.GAMMA)
        self.assertEqual(gp["noiseSD"], tg.NOISE_SD)
        self.assertEqual(gp["selectedSeed"], tg.SELECTED_SEED)
        self.assertEqual(gp["seedSearchRange"], [0, 49])

    def test_selected_seed_is_genuinely_the_first_passing_seed_0_to_49(self):
        # Recompute the seed search independently of the committed artifact
        # and of the script's own select_seed(): every seed strictly before
        # the selected one must fail at least one acceptance criterion.
        for seed in range(tg.SELECTED_SEED):
            passed, reasons = tg.seed_diagnostics(seed)
            self.assertFalse(passed, f"seed {seed} unexpectedly passes: should have been selected instead")
        passed, reasons = tg.seed_diagnostics(tg.SELECTED_SEED)
        self.assertTrue(passed, reasons)

    def test_feature_target_correlations_are_associated_but_not_perfect(self):
        import numpy as np

        x1 = np.array([o["x1"] for o in self.data["observations"]])
        x2 = np.array([o["x2"] for o in self.data["observations"]])
        y = np.array([o["y"] for o in self.data["observations"]])
        corr1 = float(np.corrcoef(x1, y)[0, 1])
        corr2 = float(np.corrcoef(x2, y)[0, 1])
        for corr in (corr1, corr2):
            self.assertGreaterEqual(abs(corr), 0.35)
            self.assertLessEqual(abs(corr), 0.90)

    def test_three_rounds_root_and_two_children(self):
        ids = [r["id"] for r in self.data["rounds"]]
        self.assertEqual(ids, ["root", "left-child", "right-child"])

    def test_root_split_is_on_x1_children_on_x2(self):
        root, left, right = self.data["rounds"]
        self.assertEqual(root["optimal"]["feature"], "x1")
        self.assertEqual(left["optimal"]["feature"], "x2")
        self.assertEqual(right["optimal"]["feature"], "x2")

    def test_thresholds_are_midpoints_between_observed_values(self):
        root = self.data["rounds"][0]
        obs_x1 = sorted({o["x1"] for o in self.data["observations"]})
        expected = [round((obs_x1[i] + obs_x1[i + 1]) / 2, 4) for i in range(len(obs_x1) - 1)]
        self.assertEqual(root["candidates"]["x1"]["thresholds"], expected)

    def test_weighted_split_mse_matches_manual_computation(self):
        root = self.data["rounds"][0]
        active = self.data["observations"]
        t = root["optimal"]["threshold"]
        feature = root["optimal"]["feature"]
        left = [o["y"] for o in active if o[feature] <= t]
        right = [o["y"] for o in active if o[feature] > t]
        n = len(active)

        def mse(ys):
            m = sum(ys) / len(ys)
            return sum((v - m) ** 2 for v in ys) / len(ys)

        expected = round((len(left) / n) * mse(left) + (len(right) / n) * mse(right), 6)
        self.assertAlmostEqual(root["optimal"]["splitMSE"], expected, places=5)

    def test_optimal_split_has_the_largest_reduction_among_candidates(self):
        for r in self.data["rounds"]:
            best = r["optimal"]["reduction"]
            for feature in ("x1", "x2"):
                for red in r["candidates"][feature]["reduction"]:
                    self.assertLessEqual(red, best + 1e-9)

    def test_every_round_optimum_is_a_unique_non_tied_best(self):
        # Recompute the second-best candidate for every round independently
        # and confirm the committed optimum strictly beats it (WP30 sec 3.1:
        # "the best weighted-MSE split is unique at each of the three
        # activity rounds").
        for r in self.data["rounds"]:
            all_candidates = []
            for feature in ("x1", "x2"):
                c = r["candidates"][feature]
                all_candidates.extend(zip(c["reduction"], c["nLeft"], c["nRight"]))
            all_candidates.sort(key=lambda t: -t[0])
            best_reduction, best_nl, best_nr = all_candidates[0]
            second_reduction, _, _ = all_candidates[1]
            self.assertAlmostEqual(best_reduction, r["optimal"]["reduction"], places=5)
            self.assertGreater(best_reduction - second_reduction, 0.0)
            self.assertGreaterEqual(best_nl, 3)
            self.assertGreaterEqual(best_nr, 3)

    def test_child_active_sets_partition_the_root(self):
        root, left, right = self.data["rounds"]
        root_ids = set(root["activeObservationIds"])
        left_ids = set(left["activeObservationIds"])
        right_ids = set(right["activeObservationIds"])
        self.assertEqual(left_ids | right_ids, root_ids)
        self.assertEqual(left_ids & right_ids, set())


if __name__ == "__main__":
    unittest.main()
