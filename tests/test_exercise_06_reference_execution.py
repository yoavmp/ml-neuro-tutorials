"""Executes the completed Exercise 6 reference notebook and checks its
numbers against approved results -- verified directly against
book/lite/files/data/abide_age_brain.csv and, where unaffected by that data
source's column ordering, against scripts/decision_tree_model_audit_result.json
(see the generator's module docstring and the WP46 report for the full
before/after comparison on the order-sensitive sections), modeled on
tests/test_exercise_05_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45 documented: this notebook's native widgets use an
ipywidgets ``Output()`` widget as a context manager, which hangs nbclient's
real ZMQ kernel with no frontend attached to acknowledge the widget comm
handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_06_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_06_reference.ipynb"

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

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["df"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_fit"]), 564)
        self.assertEqual(len(self.ns["y_val"]), 189)
        self.assertEqual(len(self.ns["y_test"]), 251)

    def test_small_tree_matches_the_audit_exactly(self):
        # Not order-sensitive at depth 3 on two named features: matches
        # scripts/decision_tree_model_audit_result.json.single_tree exactly.
        self.assertEqual(self.ns["small_tree"].get_n_leaves(), 8)
        self.assertEqual(self.ns["small_tree"].get_depth(), 3)
        self.assertAlmostEqual(self.ns["small_tree_val_mse"], 45.9783, places=2)
        self.assertAlmostEqual(self.ns["small_tree_val_r2"], 0.361081, places=3)

    def test_complexity_curve_matches_the_audit_exactly(self):
        # Not order-sensitive at these shallow depths: matches
        # scripts/decision_tree_model_audit_result.json.complexity_curve exactly.
        import numpy as np

        val_mse = self.ns["tree_depth_val_mse"]
        best_i = int(np.argmin(val_mse))
        self.assertEqual(self.ns["MAX_DEPTHS"][best_i], 2)
        self.assertAlmostEqual(val_mse[best_i], 41.6389, places=2)

    def test_classification_complexity_curve_supports_the_inclusion_rule(self):
        # Close to, not bit-identical to, the legacy audit (order-sensitive
        # at these deeper depths on 360 order-shuffled features) -- see the
        # generator's module docstring. The inclusion rule (depth >= 3,
        # margin >= 0.01 over depth 2) still passes against this data source.
        cls_val_auc = self.ns["cls_val_auc"]
        best_i = int(__import__("numpy").argmax(cls_val_auc))
        best_depth = self.ns["MAX_DEPTHS"][best_i]
        margin = cls_val_auc[best_i] - cls_val_auc[1]
        self.assertGreaterEqual(best_depth, 3)
        self.assertGreaterEqual(margin, 0.01)
        self.assertEqual(len(self.ns["dev_pos"]), 753)
        self.assertEqual(len(self.ns["test_pos"]), 251)

    def test_ensemble_widget_cache_shows_variance_reduction(self):
        # Live-recomputed widget data, not compared to a fixed legacy
        # number: sanity-checked for the qualitative finding the activity
        # teaches (bagging/RF reduce variance vs. a single tree).
        import numpy as np

        cache = self.ns["_ens_cache"]
        seeds = self.ns["_ens_replicate_seeds"]
        n = self.ns["_ENS_N_TREES_GRID"][-1]
        singles = [cache[(s, n)]["single"] for s in seeds]
        baggings = [cache[(s, n)]["bagging"] for s in seeds]
        forests = [cache[(s, n)]["random_forest"] for s in seeds]
        self.assertLess(np.mean(baggings), np.mean(singles))
        self.assertLess(np.mean(forests), np.mean(singles))

    def test_model_comparison_matches_the_notebooks_own_data_source(self):
        # Verified directly against book/lite/files/data/abide_age_brain.csv
        # (see the generator's module docstring); close to but not
        # bit-identical to the legacy audit's 57.4426/32.6774/34.33 for the
        # same order-sensitivity reason as the classification curve.
        results = self.ns["tree_cv_fold_results"]
        self.assertEqual(set(results), {"Single tree", "Bagging", "Random Forest"})
        for name in results:
            self.assertEqual(len(results[name]["mse"]), 5)
            self.assertEqual(len(results[name]["r2"]), 5)
        import numpy as np

        single_mean = np.mean(results["Single tree"]["mse"])
        bagging_mean = np.mean(results["Bagging"]["mse"])
        forest_mean = np.mean(results["Random Forest"]["mse"])
        self.assertAlmostEqual(single_mean, 56.7434, places=1)
        self.assertAlmostEqual(bagging_mean, 32.7764, places=1)
        self.assertAlmostEqual(forest_mean, 34.0980, places=1)
        self.assertLess(bagging_mean, forest_mean)  # matches the legacy notebook's own finding


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class DepthCheckCellBehavior(unittest.TestCase):
    """The Section 3 depth-sweep check cell must behave correctly for a
    correct, an incorrect-but-complete, and an unfinished student attempt --
    exercised directly (fast, no browser) against the exact check-cell
    source every rendered notebook shares."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp46-306-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "depth_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        ns = dict(self.base_ns)
        ns["tree_depth_val_mse"] = [500.0] * len(ns["MAX_DEPTHS"])
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        self.assertNotIn("fail", output.lower())

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class ComparisonCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp46-604-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "comparison_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
