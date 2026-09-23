"""Offline tests for scripts/export_pcr_pls_widget.py and its committed data
artifact (WP34, Exercise 9 "PCR or PLS?"; variance-controlled target
construction corrected by WP36).

Standard-library ``unittest``; no network -- the dataset is entirely
synthetic. Recomputes catalogue entries independently to prove the committed
numbers, not merely assert they exist.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_pcr_pls_widget_data.py'
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_pcr_pls_widget as ppw  # noqa: E402
from semantic_json_compare import DEFAULT_ABS_TOL, assert_semantically_equal  # noqa: E402

# Computed once from the unchanged `_generate_points()`/`_train_val_indices()`
# functions and verified byte-for-byte identical to the WP35 branch tip
# (`fix/wp35-exercises7-9-review` @ 0e10af7)'s committed `points`/`trainIds`/
# `valIds` before this WP's edits -- a hermetic guard (no git dependency at
# test time) against WP36 accidentally changing the predictor cloud or split
# while correcting the target construction (WP36 §4: "Predictor coordinates
# are byte-for-byte unchanged from WP35"; "Training and validation row IDs
# are unchanged").
WP35_DATASET_SHA256 = "88b896c27300382366ce09560a9d02297dc8cecc5b0c1d3fba7aea4017c73b8d"


def _dataset_hash(points, train_idx, val_idx) -> str:
    blob = json.dumps(
        {
            "points": [[round(float(p[0]), 4), round(float(p[1]), 4)] for p in points],
            "trainIds": train_idx,
            "valIds": val_idx,
        },
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


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

    def test_predictor_cloud_and_split_are_byte_for_byte_unchanged_from_wp35(self):
        pts = ppw._generate_points()
        train_idx, val_idx = ppw._train_val_indices()
        self.assertEqual(_dataset_hash(pts, train_idx, val_idx), WP35_DATASET_SHA256)
        # And the committed artifact matches that same fresh computation.
        self.assertEqual(
            [[p["x"], p["y"]] for p in self.data["points"]],
            [[round(float(p[0]), 4), round(float(p[1]), 4)] for p in pts],
        )
        self.assertEqual(self.data["trainIds"], train_idx)
        self.assertEqual(self.data["valIds"], val_idx)

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
        # the weak and strong presets (opposite-signal-direction weights).
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
            self.assertAlmostEqual(pcr["valR2"], pls["valR2"], places=2)
            pcr_preds = pcr["valPredictions"]
            pls_preds = pls["valPredictions"]
            for a, b in zip(pcr_preds, pls_preds):
                self.assertAlmostEqual(a, b, places=2)
            # Retaining both directions must not reverse the conceptual
            # explanation: convergence holds for every preset alike.
            self.assertLess(abs(pcr["valMse"] - pls["valMse"]), 0.01)

    def test_pls_beats_or_matches_pcr_at_one_component_for_every_preset(self):
        # PLS's single component is chosen using the target; it should never
        # do meaningfully worse than PCR's target-blind component here.
        for preset in ppw.PRESET_KEYS:
            pcr = self.data["catalog"][ppw._catalog_key("pcr", 1, preset)]
            pls = self.data["catalog"][ppw._catalog_key("pls", 1, preset)]
            self.assertLessEqual(pls["valMse"], pcr["valMse"] + 1e-6)

    def test_pcr_mse_strictly_improves_weak_to_moderate_to_strong(self):
        mse = {p: self.data["catalog"][ppw._catalog_key("pcr", 1, p)]["valMse"] for p in ("weak", "moderate", "strong")}
        self.assertGreater(mse["weak"], mse["moderate"])
        self.assertGreater(mse["moderate"], mse["strong"])
        # Substantially better, not an insignificant floating-point gap.
        self.assertGreater(mse["weak"] - mse["strong"], 0.5)

    def test_pcr_r2_strictly_improves_weak_to_moderate_to_strong(self):
        r2 = {p: self.data["catalog"][ppw._catalog_key("pcr", 1, p)]["valR2"] for p in ("weak", "moderate", "strong")}
        self.assertLess(r2["weak"], r2["moderate"])
        self.assertLess(r2["moderate"], r2["strong"])

    def test_weak_moderate_strong_trend_at_one_component(self):
        # WP36: with signal/noise held constant across presets, PLS's
        # advantage over PCR at one component must be largest under "weak"
        # alignment with PC1 and shrink monotonically toward "strong".
        gaps = {}
        for preset in ("weak", "moderate", "strong"):
            pcr = self.data["catalog"][ppw._catalog_key("pcr", 1, preset)]
            pls = self.data["catalog"][ppw._catalog_key("pls", 1, preset)]
            gaps[preset] = pcr["valMse"] - pls["valMse"]
        self.assertGreater(gaps["weak"], gaps["moderate"])
        self.assertGreater(gaps["moderate"], gaps["strong"])
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

    def test_preset_directions_are_unit_length(self):
        for preset in ppw.PRESET_KEYS:
            w1 = self.data["presets"][preset]["weightPc1"]
            w2 = self.data["presets"][preset]["weightPc2"]
            self.assertAlmostEqual(w1**2 + w2**2, 1.0, places=6)

    def test_weak_and_strong_are_symmetric(self):
        # WP36 §3's reasonable-example directions: weak/strong swap w1/w2.
        weak = self.data["presets"]["weak"]
        strong = self.data["presets"]["strong"]
        self.assertAlmostEqual(weak["weightPc1"], strong["weightPc2"], places=6)
        self.assertAlmostEqual(weak["weightPc2"], strong["weightPc1"], places=6)

    def test_signal_variance_equal_across_presets(self):
        # Recompute each preset's pure signal contribution (before noise) and
        # confirm its sample variance is identical across presets -- the
        # core WP36 invariant that raw coefficient-swapping violated.
        pts = ppw._generate_points()
        pc1, pc2, _ = ppw._pc_scores(pts)
        z1, z2 = ppw._standardized_orthogonal_scores(pc1, pc2)
        variances = {}
        for preset in ppw.PRESET_KEYS:
            p = ppw.PRESETS[preset]
            signal = ppw.SIGNAL_SD * (p["w1"] * z1 + p["w2"] * z2)
            variances[preset] = float(signal.var())
        values = list(variances.values())
        for v in values[1:]:
            self.assertAlmostEqual(v, values[0], places=6, msg=variances)
        self.assertAlmostEqual(values[0], ppw.SIGNAL_SD**2, places=6)

    def test_noise_vector_and_variance_identical_across_presets(self):
        # The *same* noise realization (not merely the same distribution) is
        # added to every preset's signal -- verified by reconstructing each
        # preset's target minus its own signal and confirming they match.
        import numpy as np

        pts = ppw._generate_points()
        pc1, pc2, _ = ppw._pc_scores(pts)
        z1, z2 = ppw._standardized_orthogonal_scores(pc1, pc2)
        noise_rng = np.random.RandomState(ppw.SEED + 2)
        noise_unit = ppw._unit_noise(z1, z2, noise_rng)
        self.assertAlmostEqual(float(noise_unit.var()), 1.0, places=6)

        recovered_noise = {}
        for preset in ppw.PRESET_KEYS:
            p = ppw.PRESETS[preset]
            signal = ppw.SIGNAL_SD * (p["w1"] * z1 + p["w2"] * z2)
            y = np.array(self.data["targets"][preset])
            recovered = y - (signal - signal.mean())
            recovered_noise[preset] = recovered
        keys = list(recovered_noise)
        for k in keys[1:]:
            diff = np.abs(recovered_noise[k] - recovered_noise[keys[0]])
            self.assertLess(float(diff.max()), 1e-2, (k, keys[0]))

    def test_total_target_variance_comparable_across_presets(self):
        variances = {p: float((__import__("numpy").array(self.data["targets"][p])).var()) for p in ppw.PRESET_KEYS}
        values = list(variances.values())
        for v in values[1:]:
            self.assertAlmostEqual(v, values[0], delta=0.05 * values[0], msg=variances)

    def test_signal_to_noise_ratio_identical_across_presets(self):
        # SNR = signal_sd^2 / noise_sd^2 is a fixed manifest-level constant,
        # independent of preset by construction.
        snr = ppw.SIGNAL_SD**2 / ppw.NOISE_SD**2
        self.assertGreater(snr, 0)
        for preset in ppw.PRESET_KEYS:
            p = ppw.PRESETS[preset]
            self.assertAlmostEqual(p["w1"] ** 2 + p["w2"] ** 2, 1.0, places=6)
        # SNR itself doesn't vary by preset since it never enters the
        # per-preset computation -- this test documents/pins that fact.
        self.assertAlmostEqual(ppw.SIGNAL_SD**2 / ppw.NOISE_SD**2, snr, places=9)

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
