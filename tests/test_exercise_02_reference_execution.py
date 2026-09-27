"""Executes the completed Exercise 2 reference notebook and checks its
numbers against the approved established results (WP41 section 10, section
12 item 38, section 13 bounded-validation item 9).

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses, including top-level ``await`` support for
the setup cell's Pyodide-only branch (never taken here, since
sys.platform != "emscripten" outside a browser). This intentionally avoids
`jupyter execute`/nbclient for this specific notebook: its Section 8 activity
uses an ipywidgets ``Output()`` widget as a context manager, which was found
to hang nbclient's real ZMQ kernel with no frontend attached to acknowledge
the widget comm handshake -- a known category of headless-execution issue
that does not occur with a real frontend (verified separately against the
actual JupyterLite build, see WP41's Gate A Playwright verification, and
implied by book/chapters/chapter_01/exercise_01.ipynb's own Jupyter Book
build executing ipywidgets-free notebooks routinely). Executing cell source
directly is simpler, deterministic, and exercises the identical Python
semantics.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_02_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_02_reference.ipynb"

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
        source = cell["source"]
        await _run_cell(source, ns, f"cell_{i}")
    return ns


class ReferenceExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib

        matplotlib.use("Agg")  # headless: no display, no GUI event loop
        # cwd must be book/lite/files so the notebook's relative
        # "data/abide_age_brain.csv" resolves to the same-origin asset, just
        # as it does when JupyterLite serves the notebook from that folder.
        cls._old_cwd = os.getcwd()
        os.chdir(REPO_ROOT / "book" / "lite" / "files")
        try:
            nb = nbformat.read(REFERENCE_PATH, as_version=4)
            cls.ns = asyncio.run(_execute_notebook(nb))
        finally:
            os.chdir(cls._old_cwd)

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["data"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_train"]), 753)
        self.assertEqual(len(self.ns["y_test"]), 251)

    def test_linear_regression_matches_established_result(self):
        self.assertAlmostEqual(self.ns["test_r2"], 0.469, places=3)
        self.assertAlmostEqual(self.ns["test_mse"], 49.554, places=2)

    def test_training_score_and_invalid_panels_match_established_result(self):
        self.assertAlmostEqual(self.ns["train_r2"], 0.845, places=3)
        self.assertAlmostEqual(self.ns["train_mse"], 13.530, places=2)
        self.assertAlmostEqual(self.ns["invalid_r2"], 1.000, places=3)
        self.assertAlmostEqual(self.ns["invalid_mse"], 0.0, places=2)

    def test_knn_k20_matches_established_result(self):
        self.assertAlmostEqual(self.ns["knn_r2"], 0.664, places=3)
        self.assertAlmostEqual(self.ns["knn_mse"], 31.4, places=1)

    def test_knn_sweep_matches_established_result(self):
        self.assertEqual(self.ns["N_FIT"], 564)
        self.assertEqual(len(self.ns["y_val"]), 189)
        self.assertEqual(self.ns["val_optimal_k"], 17)

    def test_sample_size_bonus_uses_the_established_10_feature_recipe(self):
        self.assertEqual(len(self.ns["FEATURES_SS"]), 10)
        self.assertEqual(
            set(self.ns["SAMPLE_SIZE_ROIS"]), {"4", "3a", "3b", "1", "2"}
        )


if __name__ == "__main__":
    unittest.main()
