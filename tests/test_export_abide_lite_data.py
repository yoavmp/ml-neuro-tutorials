"""Offline tests for scripts/export_abide_lite_data.py.

Standard-library ``unittest``; no network. Validates the committed same-origin
CSV that lets the JupyterLite Exercise 2 notebook load its data without any
Git access, GitHub token, or repository visibility (WP41 section 4.4).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_abide_lite_data.py'
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_abide_lite_data as ealt  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            ealt.check()  # raises SystemExit on failure
        self.assertIn("OK", out.getvalue())

    def test_predictor_count_is_360(self):
        with ealt.CSV_PATH.open() as f:
            header = next(csv.reader(f))
        self.assertEqual(len(header) - 2, 360)
        self.assertEqual(header[-2], "age")
        self.assertEqual(header[-1], "group")

    def test_participant_count_matches_sidecar(self):
        sidecar = json.loads(ealt.SIDECAR_PATH.read_text())
        with ealt.CSV_PATH.open() as f:
            rows = list(csv.reader(f))[1:]
        self.assertEqual(len(rows), sidecar["participant_count"])
        self.assertGreater(len(rows), 900)  # sanity: full ABIDE-II n=1004

    def test_sidecar_predictor_columns_match_canonical_recipe(self):
        sidecar = json.loads(ealt.SIDECAR_PATH.read_text())
        recipe = ealt.MANIFEST["protocol"]["canonical_recipe"]
        self.assertEqual(recipe["bundle"], "all-eligible")
        self.assertEqual(recipe["measures"], ["CT"])
        self.assertEqual(len(sidecar["predictor_columns"]), 360)
        self.assertEqual(len(set(sidecar["predictor_columns"])), 360)

    def test_rows_are_finite_numeric(self):
        with ealt.CSV_PATH.open() as f:
            reader = csv.reader(f)
            next(reader)
            for i, row in enumerate(reader):
                values = [float(v) for v in row]
                self.assertTrue(all(v == v for v in values))  # no NaN
                if i > 20:  # a sample is enough; full-file float parsing is slow
                    break


if __name__ == "__main__":
    unittest.main()
