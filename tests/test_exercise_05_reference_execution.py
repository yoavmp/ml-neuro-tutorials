"""Executes the completed Exercise 5 reference notebook and checks its
numbers against the approved established results -- verified directly
against book/lite/files/data/abide_age_brain.csv and, for Section 2's
predefined-bundle comparison, against the already-audited widget data
book/_static/widgets/data/abide_regression_models.json (see the generator's
module docstring and the WP45 report), modeled on
tests/test_exercise_03_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45 documented: this notebook's Section 2 widget uses
an ipywidgets ``Output()`` widget as a context manager, which hangs
nbclient's real ZMQ kernel with no frontend attached to acknowledge the
widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_05_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_05_reference.ipynb"
BUNDLE_SOURCE = json.loads((REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_regression_models.json").read_text())

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


def _bundle_established(key: str) -> dict:
    return next(m for m in BUNDLE_SOURCE["models"] if m["bundle"] == key and m["measures"] == ["CT"])


class ReferenceExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _execute_reference_notebook()

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["df"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_train"]), 753)
        self.assertEqual(len(self.ns["y_test"]), 251)

    def test_predefined_bundle_comparison_matches_established_widget_data(self):
        cache = self.ns["_bundle_cache"]
        # The default dropdown values (frontoparietal / occipital) are
        # refit as a side effect of executing the reference notebook top
        # to bottom.
        for key in ("frontoparietal", "occipital"):
            established = _bundle_established(key)
            result = cache[key]
            self.assertEqual(result["n_features"], established["featureCount"])
            self.assertAlmostEqual(result["mse"], established["testMSE"], places=2)
            self.assertAlmostEqual(result["r2"], established["testR2"], places=4)

    def test_all_seven_bundles_reproduce_established_widget_data(self):
        for key in self.ns["_FEATURE_BUNDLES"]:
            feats = self.ns["_FEATURE_BUNDLES"][key]
            established = _bundle_established(key)
            self.assertEqual(len(feats), established["featureCount"], key)

    def test_k_select_matches_established_cross_validation_search(self):
        self.assertEqual(self.ns["K_SELECT"], 80)
        self.assertEqual(self.ns["select_grid"].best_params_["select__k"], 80)

    def test_selected_feature_result_matches_established_result(self):
        self.assertAlmostEqual(self.ns["selected_test_mse"], 39.3416, places=2)
        self.assertEqual(len(self.ns["selected_features"]), 80)

    def test_ridge_example_matches_established_result(self):
        self.assertEqual(self.ns["RIDGE_ALPHA_EXAMPLE"], 1.0)
        self.assertAlmostEqual(self.ns["ridge_mse"], 48.7896, places=2)
        self.assertEqual(self.ns["ridge_nonzero"], 360)

    def test_lasso_example_matches_established_result(self):
        self.assertAlmostEqual(self.ns["lasso_mse"], 29.876985988314583, places=2)
        self.assertLess(self.ns["lasso_nonzero"], 360)

    def test_lasso_cv_tuning_matches_established_result(self):
        self.assertAlmostEqual(self.ns["lasso_cv_alpha"], 0.21544346900318823, places=4)
        self.assertAlmostEqual(self.ns["lasso_cv_test_mse"], 30.874983952668835, places=2)


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class SelectFeaturesCheckCellBehavior(unittest.TestCase):
    """The Section 3 feature-selection check cell must behave correctly for
    a correct, an incorrect-but-complete, and an unfinished student attempt
    -- exercised directly (fast, no browser) against the exact check-cell
    source every rendered notebook shares."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp45-307-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "select_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        ns = dict(self.base_ns)
        ns["selected_test_mse"] = 500.0
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        self.assertNotIn("fail", output.lower())

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class LassoCvCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp45-504-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "lasso_cv_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
