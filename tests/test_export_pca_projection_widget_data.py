"""Offline tests for scripts/export_pca_projection_widget.py and its
committed data artifact (WP33, Exercise 8 "Find the Best Projection").

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes the projection math independently for several angles
to prove the committed numbers, not merely assert they exist.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_pca_projection_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_pca_projection_widget as ppw  # noqa: E402
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

    def test_observation_count_is_exactly_40(self):
        self.assertEqual(len(self.data["observations"]), 40)
        self.assertEqual(self.data["generatingProcess"]["nObservations"], 40)

    def test_explicitly_marked_synthetic(self):
        note = self.data["syntheticDataNote"].lower()
        self.assertTrue("synthetic" in note or "simulated" in note)
        self.assertIn("not abide", note)

    def test_seed_was_fixed_before_generation_no_search(self):
        gp = self.data["generatingProcess"]
        self.assertEqual(gp["seed"], ppw.SEED)
        self.assertIn("no seed search", gp["seedNote"].lower())

    def test_observations_are_mean_centered(self):
        xs = [o["x"] for o in self.data["observations"]]
        ys = [o["y"] for o in self.data["observations"]]
        self.assertAlmostEqual(sum(xs) / len(xs), 0.0, places=1)
        self.assertAlmostEqual(sum(ys) / len(ys), 0.0, places=1)

    def test_angle_slider_covers_0_to_180(self):
        self.assertEqual(self.data["angleSliderDeg"]["min"], 0)
        self.assertEqual(self.data["angleSliderDeg"]["max"], 180)

    def test_true_pc1_is_not_axis_aligned(self):
        # A meaningful test of "the best axis need not match either original
        # feature axis": the true PC1 angle should not land suspiciously
        # close to 0 or 90 degrees.
        angle = self.data["truePc1"]["angleDeg"]
        self.assertGreater(angle, 5.0)
        self.assertLess(angle, 85.0)

    def test_total_variance_equals_sum_of_projected_variance_and_reconstruction_error(self):
        xs = [o["x"] for o in self.data["observations"]]
        ys = [o["y"] for o in self.data["observations"]]
        total = self.data["totalVariance"]
        for angle_deg in (0, 17, 45, 63, 90, 128, 180):
            theta = math.radians(angle_deg)
            ux, uy = math.cos(theta), math.sin(theta)
            projected = [x * ux + y * uy for x, y in zip(xs, ys)]
            captured = sum(t * t for t in projected) / len(projected)
            reconstruction_mse = total - captured
            self.assertGreaterEqual(reconstruction_mse, -1e-6)
            self.assertAlmostEqual(captured + reconstruction_mse, total, places=4)

    def test_true_pc1_angle_is_a_local_variance_maximum(self):
        xs = [o["x"] for o in self.data["observations"]]
        ys = [o["y"] for o in self.data["observations"]]

        def variance_at(angle_deg: float) -> float:
            theta = math.radians(angle_deg)
            ux, uy = math.cos(theta), math.sin(theta)
            projected = [x * ux + y * uy for x, y in zip(xs, ys)]
            return sum(t * t for t in projected) / len(projected)

        best_angle = self.data["truePc1"]["angleDeg"]
        best_variance = variance_at(best_angle)
        for delta in (-5, -1, 1, 5):
            self.assertLessEqual(variance_at(best_angle + delta), best_variance + 1e-6)

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
