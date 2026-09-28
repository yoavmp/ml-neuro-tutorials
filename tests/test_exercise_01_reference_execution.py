"""Executes the completed Exercise 1 reference notebook and checks its
numbers against the approved established results (the same values the
pre-migration book/chapters/chapter_01/exercise_01.ipynb produced).

See tests/test_exercise_02_reference_execution.py for why cell sources are
executed directly in one shared namespace rather than via `jupyter execute`/
nbclient (this notebook has no ipywidgets Output() hang risk since its
widgets do not block on a comm handshake the way Section 8 of Exercise 2
does, but direct execution is used for consistency and simplicity).

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_01_reference_execution.py'
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import os
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_01_reference.ipynb"

_TOP_LEVEL_AWAIT = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT


async def _run_cell(source: str, ns: dict, name: str) -> None:
    code = compile(source, name, "exec", flags=_TOP_LEVEL_AWAIT)
    result = eval(code, ns)
    if inspect.iscoroutine(result):
        await result


async def _execute_notebook(nb) -> dict:
    ns: dict = {}
    for i, cell in enumerate(nb.cells):
        if cell["cell_type"] != "code":
            continue
        await _run_cell(cell["source"], ns, f"cell_{i}")
    return ns


def _execute_reference_notebook() -> dict:
    import matplotlib

    matplotlib.use("Agg")
    old_cwd = os.getcwd()
    os.chdir(REPO_ROOT / "book" / "lite" / "files")
    try:
        nb = nbformat.read(REFERENCE_PATH, as_version=4)
        return asyncio.run(_execute_notebook(nb))
    finally:
        os.chdir(old_cwd)


class ReferenceExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _execute_reference_notebook()

    def test_curated_table_shape(self):
        self.assertEqual(self.ns["data"].shape, (1114, 13))

    def test_missingness_matches_established_result(self):
        summary = self.ns["missing_summary"]
        established = {
            "ADI_R_SOCIAL_TOTAL_A": 812,
            "ADOS_G_TOTAL": 767,
            "SRS_TOTAL_RAW": 329,
            "VIQ": 315,
            "PIQ": 242,
            "CURRENT_MED_STATUS": 123,
            "FIQ": 99,
            "HANDEDNESS_CATEGORY": 23,
        }
        for column, n_missing in established.items():
            self.assertEqual(int(summary.loc[column, "n_missing"]), n_missing, column)

    def test_complete_case_counts_match_established_result(self):
        self.assertEqual(len(self.ns["data_complete"]), 95)  # complete for all 13 columns

    def test_fiq_median_fill_matches_established_result(self):
        self.assertAlmostEqual(self.ns["fiq_median"], 112.0, places=1)
        self.assertEqual(int(self.ns["data"]["FIQ"].isna().sum()), 99)
        self.assertEqual(int(self.ns["data_filled"]["FIQ"].isna().sum()), 0)
        self.assertAlmostEqual(self.ns["data_filled"]["FIQ"].mean(), 111.110413, places=3)

    def test_default_retention_matches_established_core_variable_result(self):
        # The retention widget's default ticks (DX_GROUP, AGE_AT_SCAN, SEX,
        # FIQ) match the old notebook's "core_variables" complete-case count.
        default_chosen = ["DX_GROUP", "AGE_AT_SCAN", "SEX", "FIQ"]
        retained = len(self.ns["data"].dropna(subset=default_chosen))
        self.assertEqual(retained, 1015)

    def test_fiq_viq_correlation_matches_established_result(self):
        matrix = self.ns["pearson_matrix"]
        self.assertAlmostEqual(matrix.loc["FIQ", "VIQ"], 0.833, places=2)


if __name__ == "__main__":
    unittest.main()
