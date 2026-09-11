"""Offline tests for scripts/abide_modeling_data.py and the modelling manifest.

Standard-library ``unittest``; no network. A small synthetic DataFrame stands in
for the merged ABIDE table where one is needed.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_abide_modeling_data.py'
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import abide_modeling_data as amd  # noqa: E402

MANIFEST = amd.MANIFEST


def synthetic_frame(n: int = 40, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cols: dict[str, object] = {
        "subject": np.arange(1000, 1000 + n),
        "site": ["ABIDEII-KKI_1"] * (n // 2) + ["ABIDEII-NYU_1"] * (n - n // 2),
        "age": rng.uniform(6, 40, n),
        "age_resid": rng.uniform(-5, 5, n),
        "sex": rng.integers(1, 3, n).astype(float),
        "group": rng.integers(1, 3, n).astype(float),
        # FIQ / SRS / VIQ are integer standard scores in the real data
        "FIQ": np.round(rng.normal(110, 15, n)),
        "SRS_TOTAL_RAW": np.round(rng.normal(55, 40, n)),
        "VIQ": np.round(rng.normal(110, 15, n)),
    }
    # brain columns for two measures over the frontoparietal + occipital bundles
    rois = set(MANIFEST["bundles"]["frontoparietal"]["rois"]) | set(
        MANIFEST["bundles"]["occipital"]["rois"]
    )
    for roi in rois:
        for prefix in ("fsCT", "fsArea"):
            for hemi in ("L", "R"):
                cols[f"{prefix}_{hemi}_{roi}_ROI"] = rng.normal(2.5, 0.3, n)
    return pd.DataFrame(cols)


class ManifestCheck(unittest.TestCase):
    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = amd.cmd_check()
        self.assertEqual(rc, 0, out.getvalue())

    def test_every_bundle_roi_is_a_real_bilateral_atlas_label(self):
        inv = set(MANIFEST["atlas"]["roi_label_inventory"])
        asym = set(MANIFEST["atlas"]["asymmetric_labels"])
        for name, bundle in MANIFEST["bundles"].items():
            with self.subTest(bundle=name):
                self.assertEqual(len(bundle["rois"]), len(set(bundle["rois"])))
                for roi in bundle["rois"]:
                    self.assertIn(roi, inv)
                    self.assertNotIn(roi, asym)

    def test_leakage_forbidden_list_covers_every_target(self):
        forbidden = set(MANIFEST["leakage_guard"]["forbidden_exact"])
        for target in MANIFEST["targets"]:
            self.assertIn(target, forbidden)
        self.assertIn("VIQ", forbidden)
        self.assertIn("PIQ", forbidden)

    def test_targets_have_the_two_required_roles(self):
        roles = {t["role"] for t in MANIFEST["targets"].values()}
        self.assertIn("main", roles)
        self.assertIn("regularization_preview", roles)

    def test_main_target_is_age(self):
        # WP12: the modelling audit found age has reliably positive
        # out-of-sample R2 while FIQ does not, even with regularisation.
        self.assertEqual(MANIFEST["targets"]["age"]["role"], "main")
        self.assertEqual(MANIFEST["targets"]["FIQ"]["role"], "regularization_preview")

    def test_canonical_recipe_is_a_real_bundle_and_measure(self):
        recipe = MANIFEST["protocol"]["canonical_recipe"]
        self.assertTrue(recipe["bundle"] == "all-eligible" or recipe["bundle"] in MANIFEST["bundles"])
        for m in recipe["measures"]:
            self.assertIn(m, MANIFEST["measures"])


class BrainColumnParsing(unittest.TestCase):
    def test_parses_a_valid_name(self):
        bc = amd.parse_brain_column("fsCT_L_46_ROI")
        self.assertEqual((bc.measure, bc.hemisphere, bc.roi), ("CT", "L", "46"))

    def test_parses_a_hyphenated_roi(self):
        bc = amd.parse_brain_column("fsArea_R_9-46d_ROI")
        self.assertEqual((bc.measure, bc.hemisphere, bc.roi), ("Area", "R", "9-46d"))

    def test_rejects_a_non_brain_name(self):
        for bad in ("FIQ", "age", "fsCT_L_46", "fsXX_L_46_ROI", "fsCT_M_46_ROI"):
            with self.subTest(bad=bad):
                self.assertFalse(amd.is_brain_column(bad))
                with self.assertRaises(ValueError):
                    amd.parse_brain_column(bad)

    def test_rejects_an_unknown_roi(self):
        with self.assertRaises(ValueError):
            amd.parse_brain_column("fsCT_L_NOTAROI_ROI")

    def test_enforces_hemisphere_of_asymmetric_labels(self):
        self.assertEqual(amd.parse_brain_column("fsCT_L_5L_ROI").roi, "5L")
        with self.assertRaises(ValueError):
            amd.parse_brain_column("fsCT_R_5L_ROI")

    def test_classify_columns_splits_the_three_kinds(self):
        frame = synthetic_frame()
        tax = amd.classify_columns(frame.columns)
        self.assertEqual(sorted(tax["identifiers"]), ["site", "subject"])
        self.assertIn("FIQ", tax["phenotypes"])
        self.assertIn("age", tax["phenotypes"])
        self.assertGreater(len(tax["brain_features"]), 100)
        self.assertEqual(tax["hemispheres"], ["L", "R"])
        self.assertEqual(set(tax["measures"]), {"CT", "Area"})


class Bundles(unittest.TestCase):
    def test_bundle_columns_order_is_roi_then_measure_then_hemisphere(self):
        cols = amd.bundle_columns("frontoparietal", ["CT", "Area"])
        self.assertEqual(cols[:4], [
            "fsCT_L_46_ROI", "fsCT_R_46_ROI", "fsArea_L_46_ROI", "fsArea_R_46_ROI",
        ])
        self.assertEqual(len(cols), 39 * 2 * 2)
        self.assertEqual(len(cols), len(set(cols)))

    def test_all_eligible_excludes_asymmetric_labels(self):
        cols = amd.bundle_columns("all-eligible", ["CT"])
        self.assertEqual(len(cols), 179 * 2)
        self.assertNotIn("fsCT_L_5L_ROI", cols)

    def test_rejects_unknown_measure_and_bundle(self):
        with self.assertRaises(ValueError):
            amd.bundle_columns("frontoparietal", ["fsXX"])
        with self.assertRaises(ValueError):
            amd.bundle_columns("nonsense", ["CT"])

    def test_available_filter_rejects_a_missing_column(self):
        frame = synthetic_frame()
        # temporal bundle columns are not in the synthetic frame
        with self.assertRaises(ValueError):
            amd.bundle_columns("temporal", ["CT"], available=frame.columns)


class LeakageGuard(unittest.TestCase):
    def test_assert_brain_only_accepts_brain_columns(self):
        amd.assert_brain_only(["fsCT_L_46_ROI", "fsArea_R_IPS1_ROI"])

    def test_assert_brain_only_rejects_targets_and_phenotypes(self):
        for bad in (["FIQ"], ["VIQ"], ["age"], ["SITE_ID"], ["group"], ["fsCT_L_46_ROI", "sex"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                amd.assert_brain_only(bad)

    def test_feature_matrix_is_brain_only_and_drops_missing_target(self):
        frame = synthetic_frame()
        frame.loc[:4, "FIQ"] = np.nan
        X, y, cols = amd.feature_matrix(frame, "frontoparietal", ["CT"], "FIQ")
        self.assertEqual(X.shape[0], len(frame) - 5)
        self.assertEqual(X.shape[1], 78)
        self.assertEqual(len(y), X.shape[0])
        amd.assert_brain_only(cols)
        self.assertNotIn("FIQ", cols)

    def test_feature_matrix_rejects_an_unknown_target(self):
        with self.assertRaises(ValueError):
            amd.feature_matrix(synthetic_frame(), "frontoparietal", ["CT"], "not_a_real_target")

    def test_feature_matrix_accepts_age_as_a_target(self):
        # age (WP12 main target) is native to the brain table, no join needed.
        X, y, cols = amd.feature_matrix(synthetic_frame(), "frontoparietal", ["CT"], "age")
        self.assertEqual(X.shape, (len(synthetic_frame()), 78))
        self.assertEqual(len(y), X.shape[0])
        amd.assert_brain_only(cols)
        self.assertNotIn("age", cols)


if __name__ == "__main__":
    unittest.main()
