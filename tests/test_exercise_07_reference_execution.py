"""Executes the completed Exercise 7 reference notebook and checks its
numbers against approved results -- verified directly against
book/lite/files/data/abide_age_brain.csv and, where unaffected by that data
source's column ordering, against
scripts/gradient_boosting_model_audit_result.json and
scripts/export_boosting_step_widget.py (see the generator's module
docstring and the WP46 report for the full before/after comparison on the
order-sensitive Section 6/7 computations), modeled on
tests/test_exercise_06_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45/WP46 documented: this notebook's native widgets
use an ipywidgets ``Output()`` widget as a context manager, which hangs
nbclient's real ZMQ kernel with no frontend attached to acknowledge the
widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_07_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_07_reference.ipynb"

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
        self.assertEqual(len(self.ns["y_train"]), 753)
        self.assertEqual(len(self.ns["y_test"]), 251)

    def test_build_a_boosted_model_matches_the_audited_synthetic_widget(self):
        # Entirely synthetic (no ABIDE data); replicates
        # scripts/export_boosting_step_widget.py's own algorithm verbatim.
        stages = self.ns["_step_stages_by_rate"][0.1]
        self.assertEqual(len(stages), 13)  # stage 0..12
        self.assertAlmostEqual(stages[0]["train_mse"], 16.20, delta=0.05)
        self.assertIsNone(stages[0]["stump"])
        self.assertIsNotNone(stages[1]["stump"])

    def test_sklearn_example_close_to_the_legacy_audit(self):
        # Not order-sensitive enough at this shallow depth to diverge
        # further from scripts/gradient_boosting_model_audit_result.json.
        self.assertAlmostEqual(self.ns["gb_val_mse"], 18.3254, places=2)
        self.assertAlmostEqual(self.ns["gb_val_r2"], 0.745349, places=3)

    def test_sweep_reproduces_the_underfit_best_overfit_shape(self):
        results = {r["n_estimators"]: r["val_mse"] for r in self.ns["boosting_sweep_results"]}
        self.assertEqual(set(results), set(self.ns["N_TREES_VALUES"]))
        best = min(results.values())
        self.assertAlmostEqual(best, 18.73, delta=0.5)
        self.assertLess(best, results[10])  # underfit end is worse than the minimum
        self.assertLess(best, results[300])  # overfit end is worse than the minimum

    def test_stop_curve_training_mse_keeps_falling_while_validation_does_not(self):
        train_mse = self.ns["stop_train_mse"]
        val_mse = self.ns["stop_val_mse"]
        self.assertAlmostEqual(train_mse[-1], 0.81, delta=0.1)  # matches the legacy audit closely
        self.assertLess(min(val_mse), val_mse[-1])  # validation minimum is not at the largest tree count

    def test_pipeline_selects_a_genuine_configuration_from_the_reduced_grid(self):
        # This notebook's own data source selects (0.1, 200, depth=2), not
        # the legacy audit's (0.1, 200, depth=3) -- see the generator's
        # module docstring for the documented, honestly-computed divergence.
        search = self.ns["boosting_search"]
        self.assertEqual(len(search.cv_results_["params"]), 12)
        best_mean_mse = -search.best_score_
        self.assertAlmostEqual(best_mean_mse, 27.4236, places=1)
        self.assertAlmostEqual(self.ns["boosting_test_mse"], 29.3842, places=1)
        self.assertAlmostEqual(self.ns["boosting_test_r2"], 0.685223, places=2)

    def test_pipeline_never_lets_earlier_exploration_touch_the_locked_test(self):
        # The reference notebook's own pipeline blank must call
        # boosting_search.fit on X_train/y_train only.
        cell = next(c for c in nbformat.read(REFERENCE_PATH, as_version=4).cells if c.get("id") == "wp46-604-blank")
        source = cell["source"]
        self.assertIn("boosting_search.fit(X_train, y_train)", source)
        self.assertNotIn("boosting_search.fit(X_test", source)

    def test_boosting_cv_results_has_twelve_rows_and_both_fixed_slices(self):
        results = self.ns["boosting_cv_results"]
        self.assertEqual(len(results), 12)
        self.assertGreaterEqual(len(results[results["max_depth"] == 2]), 2)
        self.assertGreaterEqual(len(results[results["learning_rate"] == 0.1]), 2)

    def test_comparison_matches_the_notebooks_own_data_source(self):
        # Verified directly against book/lite/files/data/abide_age_brain.csv;
        # close to but not bit-identical to the legacy audit's 70.13/0.249
        # and 38.20/0.591 for the same order-sensitivity reason as Exercise
        # 6's fair comparison.
        table = self.ns["comparison_table"]
        self.assertAlmostEqual(table.loc["Single tree", "locked_test_mse"], 71.2880, places=1)
        self.assertAlmostEqual(table.loc["Random Forest", "locked_test_mse"], 35.6616, places=1)
        self.assertAlmostEqual(table.loc["Gradient boosting", "locked_test_mse"], self.ns["boosting_test_mse"], places=6)
        self.assertEqual(table["locked_test_mse"].idxmin(), "Gradient boosting")


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class SweepCheckCellBehavior(unittest.TestCase):
    """The Section 4 sweep check cell must behave correctly for a correct,
    an incorrect-but-complete, and an unfinished student attempt --
    exercised directly (fast, no browser) against the exact check-cell
    source every rendered notebook shares."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp46-405-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "sweep_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        ns = dict(self.base_ns)
        ns["boosting_sweep_results"] = [{"n_estimators": n, "val_mse": 500.0} for n in ns["N_TREES_VALUES"]]
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        self.assertNotIn("fail", output.lower())

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class PipelineCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp46-605-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "pipeline_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class BarCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp46-611-bar-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "bar_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
