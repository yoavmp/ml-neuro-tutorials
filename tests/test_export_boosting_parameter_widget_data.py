"""Offline tests for scripts/export_boosting_parameter_widget.py and its
committed data artifact (WP32, Exercise 7 "Explore the Boosting Parameters").

Standard-library ``unittest``; no network -- re-validates the committed
artifact for self-consistency, cohort/split sizes, grid completeness, and
locked-test exclusion. Does not refit any model (network + ~2 minutes); see
scripts/export_boosting_parameter_widget.py --refresh for that.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_boosting_parameter_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_boosting_parameter_widget as bpw  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(bpw.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = bpw.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_source_pins_match_the_manifest(self):
        self.assertEqual(self.data["source"]["pinnedCommit"], bpw.MANIFEST["source"]["pinned_commit"])

    def test_locked_test_is_excluded(self):
        self.assertIs(self.data["lockedTestExcluded"], True)
        # Structural guarantee: no key besides the declared flag itself
        # mentions "test" -- there is no field that could carry outer-test
        # data (e.g. no "testMSE", "observedTest", "outerTest*" key).
        other_keys = [k for k in self.data if k != "lockedTestExcluded"]
        self.assertFalse(any("test" in k.lower() for k in other_keys), other_keys)

    def test_cohort_and_split_sizes(self):
        split = self.data["split"]
        self.assertEqual(split["devSplit"]["nFit"], 564)
        self.assertEqual(split["devSplit"]["nVal"], 189)
        self.assertEqual(self.data["featureRecipe"]["featureCount"], 360)

    def test_grid_matches_manifest_declaration(self):
        self.assertEqual(self.data["learningRateGrid"], bpw.LEARNING_RATE_GRID)
        self.assertEqual(self.data["depthGrid"], bpw.DEPTH_GRID)
        self.assertEqual(self.data["nTreesGrid"], bpw.N_TREES_GRID)

    def test_defaults_are_members_of_their_own_grids(self):
        d = self.data["defaults"]
        self.assertIn(d["learningRate"], self.data["learningRateGrid"])
        self.assertIn(d["depth"], self.data["depthGrid"])
        self.assertIn(d["nTrees"], self.data["nTreesGrid"])

    def test_grid_has_one_entry_per_learning_rate_depth_combination(self):
        expected = len(self.data["learningRateGrid"]) * len(self.data["depthGrid"])
        self.assertEqual(len(self.data["grid"]), expected)

    def test_every_grid_point_has_a_full_prediction_array(self):
        n_val = self.data["split"]["devSplit"]["nVal"]
        for entry in self.data["grid"].values():
            for n in self.data["nTreesGrid"]:
                point = entry["byNTrees"][str(n)]
                self.assertEqual(len(point["predictedValidation"]), n_val)

    def test_training_mse_is_monotone_non_increasing_with_more_trees(self):
        for key, entry in self.data["grid"].items():
            train = [entry["byNTrees"][str(n)]["trainMSE"] for n in self.data["nTreesGrid"]]
            for a, b in zip(train, train[1:]):
                self.assertGreaterEqual(a, b - 1e-6, key)

    def test_default_configuration_shows_underfit_then_overfit_pattern(self):
        # This is the exact curve Section 5 discusses (learning_rate=0.1,
        # depth=2): validation MSE should improve substantially from the
        # smallest to some middle tree count, then not be at its best at the
        # largest tree count -- the early-stopping illustration.
        d = self.data["defaults"]
        entry = self.data["grid"][f"{d['learningRate']}|{d['depth']}"]
        val_by_n = {n: entry["byNTrees"][str(n)]["valMSE"] for n in self.data["nTreesGrid"]}
        smallest_n, largest_n = self.data["nTreesGrid"][0], self.data["nTreesGrid"][-1]
        best_n = min(val_by_n, key=val_by_n.get)
        self.assertLess(val_by_n[best_n], val_by_n[smallest_n])
        self.assertNotEqual(best_n, largest_n)

    def test_no_non_finite_values_anywhere(self):
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


class Validate(unittest.TestCase):
    def test_flags_a_missing_grid_entry(self):
        data = json.loads(bpw.OUT_PATH.read_text(encoding="utf-8"))
        key = next(iter(data["grid"]))
        del data["grid"][key]
        problems = bpw.validate(data)
        self.assertTrue(any("missing entry" in p for p in problems))

    def test_flags_locked_test_excluded_false(self):
        data = json.loads(bpw.OUT_PATH.read_text(encoding="utf-8"))
        data["lockedTestExcluded"] = False
        problems = bpw.validate(data)
        self.assertTrue(any("lockedTestExcluded" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
