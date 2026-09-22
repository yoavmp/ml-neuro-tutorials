"""Offline tests for scripts/export_pcr_pls_widget.py and its committed data
artifact (WP34, Exercise 9 "PCR or PLS?").

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes catalogue entries independently to prove the committed
numbers, not merely assert they exist.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_pcr_pls_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_pcr_pls_widget as ppw  # noqa: E402
from semantic_json_compare import DEFAULT_ABS_TOL, assert_semantically_equal  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(ppw.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ppw.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_matches_a_fresh_recomputation(self):
        assert_semantically_equal(self.data, ppw.build_data(), abs_tol=DEFAULT_ABS_TOL)

    def test_observation_count_matches_the_manifest(self):
        self.assertEqual(len(self.data["points"]), ppw.N_OBSERVATIONS)
        self.assertEqual(self.data["generatingProcess"]["nObservations"], ppw.N_OBSERVATIONS)
        self.assertEqual(self.data["generatingProcess"]["nTrain"], ppw.N_TRAIN)

    def test_explicitly_marked_synthetic(self):
        note = self.data["syntheticDataNote"].lower()
        self.assertTrue("synthetic" in note or "simulated" in note)
        self.assertIn("not abide", note)

    def test_train_and_val_ids_partition_every_point_exactly_once(self):
        train_ids = set(self.data["trainIds"])
        val_ids = set(self.data["valIds"])
        self.assertEqual(len(train_ids), ppw.N_TRAIN)
        self.assertEqual(train_ids & val_ids, set())
        self.assertEqual(train_ids | val_ids, set(range(ppw.N_OBSERVATIONS)))

    def test_pc1_explains_more_variance_than_pc2(self):
        gp = self.data["generatingProcess"]
        self.assertGreater(gp["pc1ExplainedVarianceRatio"], gp["pc2ExplainedVarianceRatio"])
        self.assertAlmostEqual(gp["pc1ExplainedVarianceRatio"] + gp["pc2ExplainedVarianceRatio"], 1.0, places=4)

    def test_all_three_presets_and_both_methods_and_both_component_counts_present(self):
        for method in ppw.METHODS:
            for n in ppw.COMPONENT_GRID:
                for preset in ppw.PRESET_KEYS:
                    self.assertIn(ppw._catalog_key(method, n, preset), self.data["catalog"])

    def test_pcr_direction_never_depends_on_the_preset(self):
        # PCR never sees the target, so its first-component direction must
        # be identical across every preset (for a fixed n_components).
        for n in ppw.COMPONENT_GRID:
            directions = {
                preset: tuple(self.data["catalog"][ppw._catalog_key("pcr", n, preset)]["firstComponentDirection"])
                for preset in ppw.PRESET_KEYS
            }
            values = list(directions.values())
            for d in values[1:]:
                self.assertEqual(d, values[0], directions)

    def test_pls_direction_changes_with_the_preset(self):
        # PLS does see the target, so its direction should differ between
        # the weak and strong presets (they use very different beta pairs).
        n = ppw.COMPONENT_GRID[0]
        weak_dir = self.data["catalog"][ppw._catalog_key("pls", n, "weak")]["firstComponentDirection"]
        strong_dir = self.data["catalog"][ppw._catalog_key("pls", n, "strong")]["firstComponentDirection"]
        self.assertNotEqual(tuple(weak_dir), tuple(strong_dir))

    def test_pcr_and_pls_converge_once_both_components_are_retained(self):
        max_n = max(ppw.COMPONENT_GRID)
        for preset in ppw.PRESET_KEYS:
            pcr = self.data["catalog"][ppw._catalog_key("pcr", max_n, preset)]
            pls = self.data["catalog"][ppw._catalog_key("pls", max_n, preset)]
            self.assertAlmostEqual(pcr["trainMse"], pls["trainMse"], places=2)
            self.assertAlmostEqual(pcr["valMse"], pls["valMse"], places=2)

    def test_pls_beats_or_matches_pcr_at_one_component_for_every_preset(self):
        # PLS's single component is chosen using the target; it should never
        # do meaningfully worse than PCR's target-blind component here.
        for preset in ppw.PRESET_KEYS:
            pcr = self.data["catalog"][ppw._catalog_key("pcr", 1, preset)]
            pls = self.data["catalog"][ppw._catalog_key("pls", 1, preset)]
            self.assertLessEqual(pls["valMse"], pcr["valMse"] + 1e-6)

    def test_weak_moderate_strong_trend_at_one_component(self):
        # WP35 §13: presets now encode alignment with the HIGHEST-variance
        # direction (PC1). At one component, PCR is stuck using PC1 alone,
        # so PLS's advantage over PCR should be largest under "weak"
        # (target mostly explained by the lower-variance direction, PC2,
        # which PCR's single component cannot reach) and should shrink
        # monotonically as alignment with PC1 strengthens.
        gaps = {}
        for preset in ("weak", "moderate", "strong"):
            pcr = self.data["catalog"][ppw._catalog_key("pcr", 1, preset)]
            pls = self.data["catalog"][ppw._catalog_key("pls", 1, preset)]
            gaps[preset] = pcr["valMse"] - pls["valMse"]
        self.assertGreater(gaps["weak"], gaps["moderate"])
        self.assertGreater(gaps["moderate"], gaps["strong"])
        # Under "strong" alignment with PC1, PCR's target-blind component
        # already points at (or very near) the target-relevant direction,
        # so the PLS advantage should have narrowed substantially from the
        # "weak" case, not merely decreased.
        self.assertLess(gaps["strong"], gaps["weak"] * 0.5)

    def test_presets_labelled_for_highest_variance_direction(self):
        for preset in ppw.PRESET_KEYS:
            label = self.data["presets"][preset]["label"].lower()
            self.assertIn("highest-variance direction", label)
            self.assertNotIn("lower-variance direction", label)

    def test_first_component_directions_are_unit_vectors(self):
        for entry in self.data["catalog"].values():
            dx, dy = entry["firstComponentDirection"]
            self.assertAlmostEqual(dx**2 + dy**2, 1.0, places=2)

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


if __name__ == "__main__":
    unittest.main()
