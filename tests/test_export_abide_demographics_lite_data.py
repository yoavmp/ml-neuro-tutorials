"""Offline tests for scripts/export_abide_demographics_lite_data.py.

Standard-library ``unittest``; no network. Validates the committed same-origin
sex/site sidecar that Exercise 8's JupyterLite notebook loads alongside the
existing abide_age_brain.csv (WP47) -- in particular, that it is row-for-row
aligned with that existing, unmodified shared export.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_abide_demographics_lite_data.py'
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

import export_abide_demographics_lite_data as eadl  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    def test_check_mode_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            eadl.check()  # raises SystemExit on failure
        self.assertIn("OK", out.getvalue())

    def test_header_and_participant_count(self):
        with eadl.CSV_PATH.open() as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        self.assertEqual(header, ["age", "sex", "site"])
        sidecar = json.loads(eadl.SIDECAR_PATH.read_text())
        self.assertEqual(len(rows), sidecar["participant_count"])
        self.assertEqual(len(rows), 1004)

    def test_sex_values_are_1_or_2(self):
        with eadl.CSV_PATH.open() as f:
            reader = csv.reader(f)
            next(reader)
            sexes = {row[1] for row in reader}
        self.assertEqual(sexes, {"1", "2"})

    def test_site_has_multiple_levels_and_no_blanks(self):
        with eadl.CSV_PATH.open() as f:
            reader = csv.reader(f)
            next(reader)
            sites = [row[2] for row in reader]
        self.assertGreater(len(set(sites)), 1)
        self.assertTrue(all(s for s in sites))

    def test_row_order_matches_the_existing_shared_brain_csv_exactly(self):
        with eadl.BRAIN_CSV_PATH.open() as f:
            brain_reader = csv.reader(f)
            brain_header = next(brain_reader)
            age_idx = brain_header.index("age")
            brain_ages = [r[age_idx] for r in brain_reader]
        with eadl.CSV_PATH.open() as f:
            demo_reader = csv.reader(f)
            next(demo_reader)
            demo_ages = [r[0] for r in demo_reader]
        self.assertEqual(brain_ages, demo_ages)

    def test_does_not_modify_the_existing_shared_export(self):
        # This script's own write() never touches abide_age_brain.csv or its
        # sidecar -- only reads them (BRAIN_CSV_PATH is read-only here).
        import inspect

        source = inspect.getsource(eadl.write)
        self.assertNotIn("BRAIN_CSV_PATH.write", source)
        self.assertNotIn("BRAIN_CSV_PATH.open(\"w\"", source)


if __name__ == "__main__":
    unittest.main()
