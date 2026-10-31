"""Offline tests for scripts/export_haxby_rsa_data.py.

Standard-library ``unittest``; no network. Validates the committed
run x category x ventral-temporal-voxel CSV and its manifest that let
Exercise 11's JupyterLite notebook load its data without downloading or
processing the ~300 MB raw Haxby functional file (WP61 Gate A).

Run:
    python3 -m unittest discover -s tests -p 'test_export_haxby_rsa_data.py'
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_haxby_rsa_data as ehrd  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = ehrd.cmd_check()
        self.assertEqual(rc, 0)
        self.assertIn("OK", out.getvalue())

    def test_csv_shape_is_12_runs_by_8_categories(self):
        import pandas as pd

        frame = pd.read_csv(ehrd.OUT_CSV)
        self.assertEqual(len(frame), 96)  # 12 runs x 8 categories
        self.assertEqual(frame["run"].nunique(), 12)
        self.assertEqual(frame["category"].nunique(), 8)
        voxel_cols = [c for c in frame.columns if c.startswith("voxel_")]
        self.assertEqual(len(voxel_cols), 464)

    def test_every_run_has_every_category_exactly_once(self):
        import pandas as pd

        frame = pd.read_csv(ehrd.OUT_CSV)
        counts = frame.groupby("run")["category"].nunique()
        self.assertTrue((counts == 8).all())
        per_run_category_counts = frame.groupby(["run", "category"]).size()
        self.assertTrue((per_run_category_counts == 1).all())

    def test_no_missing_or_non_finite_values(self):
        import numpy as np
        import pandas as pd

        frame = pd.read_csv(ehrd.OUT_CSV)
        voxel_cols = [c for c in frame.columns if c.startswith("voxel_")]
        self.assertFalse(frame[voxel_cols].isna().any().any())
        self.assertTrue(np.isfinite(frame[voxel_cols].to_numpy()).all())

    def test_manifest_mask_is_the_broad_vt_mask_not_category_selective(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        self.assertEqual(manifest["maskUsed"]["file"], "mask4_vt.nii.gz")
        self.assertEqual(manifest["maskUsed"]["nilearnAttribute"], "mask_vt")

    def test_manifest_records_odd_even_coverage(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        check = manifest["extraction"]["oddEvenCheck"]
        self.assertTrue(check["eachSubsetCoversAllCategories"])
        self.assertEqual(sorted(check["oddRuns"] + check["evenRuns"]), list(range(12)))

    def test_manifest_subject_and_source_pinned(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        self.assertEqual(manifest["dataset"]["subject"], 2)
        self.assertEqual(manifest["dataset"]["sourceUrl"], ehrd.DATASET_SOURCE_URL)

    def test_derived_file_checksum_matches_committed_file(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        on_disk_sha = ehrd.sha256_hex(ehrd.OUT_CSV.read_bytes())
        self.assertEqual(manifest["derivedFile"]["sha256"], on_disk_sha)

    def test_categories_are_the_documented_eight(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        self.assertEqual(
            sorted(manifest["extraction"]["categories"]),
            ["bottle", "cat", "chair", "face", "house", "scissors", "scrambledpix", "shoe"],
        )

    def test_no_exclusions_were_necessary(self):
        manifest = json.loads(ehrd.OUT_MANIFEST.read_text())
        exclusions = manifest["extraction"]["exclusions"]
        self.assertEqual(len(exclusions), 1)
        self.assertIn("none", exclusions[0])


if __name__ == "__main__":
    unittest.main()
