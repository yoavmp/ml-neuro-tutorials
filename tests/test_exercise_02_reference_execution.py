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


def _execute_reference_notebook() -> dict:
    import matplotlib

    matplotlib.use("Agg")  # headless: no display, no GUI event loop
    # cwd must be book/lite/files so the notebook's relative
    # "data/abide_age_brain.csv" resolves to the same-origin asset, just
    # as it does when JupyterLite serves the notebook from that folder.
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


def _knn_check_source() -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == "wp41-506-check")
    return cell["source"]


class KnnCheckCellBehavior(unittest.TestCase):
    """WP42 Gate 1 item 4: the KNN check cell must behave correctly for a
    correct, an incorrect-but-complete, and an unfinished student attempt --
    exercised here directly (fast, no browser needed) against the exact
    check-cell source every rendered notebook shares."""

    @classmethod
    def setUpClass(cls):
        cls.source = _knn_check_source()
        # A real, established k=20 result for the "correct" case rather than
        # hand-typed numbers. Executed independently of ReferenceExecution
        # (not read off its class attribute): unittest does not guarantee
        # cross-class ordering, and this class alphabetically precedes it.
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "knn_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)
        self.assertNotIn("differs from", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        ns = dict(self.base_ns)
        ns["knn_r2"] = 0.10  # far from the established ~0.664
        ns["knn_mse"] = 120.0  # far from the established ~31.4
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        # Must not accuse the student of a definite mistake -- a different
        # valid implementation or an earlier choice can also explain this.
        self.assertIn("does not automatically mean", output)
        self.assertNotIn("fail", output.lower())
        self.assertNotIn("incorrect", output.lower())

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
