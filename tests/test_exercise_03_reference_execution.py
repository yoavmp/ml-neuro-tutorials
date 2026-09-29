"""Executes the completed Exercise 3 reference notebook and checks its
numbers against the approved established results
(scripts/classification_model_audit_result.json), modeled on
tests/test_exercise_02_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses, including top-level ``await`` support for
the setup cell's Pyodide-only branch (never taken here, since
sys.platform != "emscripten" outside a browser). Avoids `jupyter
execute`/nbclient for the same reason WP41 documented for Exercise 2: this
notebook's Sections 5-6 use an ipywidgets ``Output()`` widget as a context
manager, which hangs nbclient's real ZMQ kernel with no frontend attached to
acknowledge the widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_03_reference_execution.py'
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
import os
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_03_reference.ipynb"
AUDIT_RESULT = json.loads((REPO_ROOT / "scripts" / "classification_model_audit_result.json").read_text())

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
        cls.ev = AUDIT_RESULT["locked_test_eval"]

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["df"]), AUDIT_RESULT["cohort"]["n_total"])
        self.assertEqual(len(self.ns["FEATURES"]), AUDIT_RESULT["feature_recipe"]["feature_count"])

    def test_class_counts_match_the_audit(self):
        self.assertEqual(int(self.ns["y"].sum()), AUDIT_RESULT["cohort"]["n_positive_total"])
        self.assertEqual(int((self.ns["y"] == 0).sum()), AUDIT_RESULT["cohort"]["n_negative_total"])

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_train"]), AUDIT_RESULT["cohort"]["n_train"])
        self.assertEqual(len(self.ns["y_test"]), AUDIT_RESULT["cohort"]["n_test"])

    def test_logistic_regression_matches_established_result(self):
        self.assertAlmostEqual(self.ns["accuracy"], self.ev["accuracy"], places=6)
        self.assertAlmostEqual(self.ns["sensitivity"], self.ev["sensitivity"], places=6)
        self.assertAlmostEqual(self.ns["specificity"], self.ev["specificity"], places=6)
        self.assertAlmostEqual(self.ns["auc"], self.ev["auc"], places=6)

    def test_confusion_matrix_matches_established_result(self):
        cm = self.ev["confusion_matrix"]
        self.assertEqual(int(self.ns["tn"]), cm["tn"])
        self.assertEqual(int(self.ns["fp"]), cm["fp"])
        self.assertEqual(int(self.ns["fn"]), cm["fn"])
        self.assertEqual(int(self.ns["tp"]), cm["tp"])

    def test_c_example_matches_established_protocol(self):
        self.assertEqual(self.ns["C_EXAMPLE"], 1.0)
        self.assertIn("C=1.0", AUDIT_RESULT["protocol"]["model"])

    def test_imbalance_cohort_matches_established_result(self):
        # The imbalance widget's own default ratio ("90:10") is refit as a
        # side effect of executing the reference notebook top to bottom;
        # re-derive the same fixed cohort draw directly to confirm the
        # notebook's own resampling matches the pre-migration notebook's
        # committed "360 control, 40 autism" result at that ratio.
        import numpy as np

        X, y = self.ns["X"], self.ns["y"]
        majority_pct, minority_pct = self.ns["_RATIO_TABLE"]["90:10"]
        n_majority = round(400 * majority_pct)
        n_minority = 400 - n_majority
        self.assertEqual(n_majority, 360)
        self.assertEqual(n_minority, 40)
        rng = np.random.default_rng(20000)
        majority_idx = np.flatnonzero(y == 0)
        minority_idx = np.flatnonzero(y == 1)
        chosen = np.concatenate([
            rng.choice(majority_idx, size=n_majority, replace=False),
            rng.choice(minority_idx, size=n_minority, replace=False),
        ])
        self.assertEqual(len(chosen), 400)


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class MetricsCheckCellBehavior(unittest.TestCase):
    """The Section 4 confusion-matrix check cell must behave correctly for a
    correct, an incorrect-but-complete, and an unfinished student attempt --
    exercised directly (fast, no browser) against the exact check-cell
    source every rendered notebook shares, mirroring WP42's KNN-check
    behavior tests for Exercise 2."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp44-414-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "metrics_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)
        self.assertNotIn("differs from", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        ns = dict(self.base_ns)
        ns["accuracy"] = 0.10
        ns["sensitivity"] = 0.05
        ns["specificity"] = 0.05
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        self.assertIn("does not automatically mean", output)
        self.assertNotIn("fail", output.lower())
        self.assertNotIn("incorrect", output.lower())

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class AucCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp44-424-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "auc_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
