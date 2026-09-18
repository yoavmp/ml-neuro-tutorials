"""Offline tests for scripts/export_tree_greedy_widget.py and its committed
data artifact (WP29, Exercise 6 "Build a Tree Greedily").

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes candidate thresholds and split MSE independently
(not just by re-calling the script's own functions) for a few cases to
prove the committed numbers, not merely assert they exist.

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

    def test_observation_count_is_in_range(self):
        self.assertGreaterEqual(len(self.data["observations"]), 12)
        self.assertLessEqual(len(self.data["observations"]), 20)

    def test_explicitly_marked_synthetic(self):
        self.assertIn("synthetic", self.data["syntheticDataNote"].lower())

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

    def test_child_active_sets_partition_the_root(self):
        root, left, right = self.data["rounds"]
        root_ids = set(root["activeObservationIds"])
        left_ids = set(left["activeObservationIds"])
        right_ids = set(right["activeObservationIds"])
        self.assertEqual(left_ids | right_ids, root_ids)
        self.assertEqual(left_ids & right_ids, set())


if __name__ == "__main__":
    unittest.main()
