"""Executes the completed Exercise 4 reference notebook and checks its
numbers against the approved established results
(scripts/wp27_validation_audit_result.json for the nested cross-validation
activity; verified directly against book/lite/files/data/abide_age_brain.csv
for the one-split and Section 3 cross-validation numbers -- see the
generator's module docstring and the WP45 report), modeled on
tests/test_exercise_03_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses, including top-level ``await`` support for
the setup cell's Pyodide-only branch (never taken here, since
sys.platform != "emscripten" outside a browser). Avoids `jupyter
execute`/nbclient for the same reason WP41/WP44 documented: this notebook's
Section 4 widget uses an ipywidgets ``Output()`` widget as a context
manager, which hangs nbclient's real ZMQ kernel with no frontend attached to
acknowledge the widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_04_reference.ipynb"
AUDIT_RESULT = json.loads((REPO_ROOT / "scripts" / "wp27_validation_audit_result.json").read_text())

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
        self.assertEqual(len(self.ns["df"]), AUDIT_RESULT["part_a_sample_size_stability"]["n_eligible"])
        self.assertEqual(len(self.ns["FEATURES"]), 360)

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_train"]), 753)
        self.assertEqual(len(self.ns["y_test"]), 251)

    def test_one_split_matches_established_result(self):
        self.assertAlmostEqual(self.ns["one_split_mse"], 31.3768, places=3)
        self.assertAlmostEqual(self.ns["one_split_r2"], 0.663879, places=5)

    def test_section_3_cross_validation_matches_established_result(self):
        self.assertAlmostEqual(self.ns["cv_mean_mse"], 33.8121, places=3)
        self.assertAlmostEqual(self.ns["cv_mean_r2"], 0.615255, places=5)
        self.assertEqual(len(self.ns["cv_fold_mse"]), 5)

    def test_k_example_matches_established_protocol(self):
        self.assertEqual(self.ns["K_EXAMPLE"], 20)

    def test_nested_cv_matches_wp27_audit(self):
        c = AUDIT_RESULT["part_c_nested_cv"]
        nested = self.ns["nested"]
        self.assertEqual(len(nested), c["n_outer"])
        self.assertAlmostEqual(nested["outer_test_mse"].mean(), c["mean_outer_test_mse"], places=2)
        self.assertAlmostEqual(nested["outer_test_r2"].mean(), c["mean_outer_test_r2"], places=4)
        self.assertEqual(list(nested["selected_k"]), c["selected_k_per_fold"])

    def test_stability_widget_default_matches_wp27_audit(self):
        # The Section 4 widget's default (sample size = 100, seed = 0) is
        # computed live by the same algorithm scripts/wp27_validation_audit.py
        # used for its own Part A audit; re-derive it directly here (rather
        # than reading the widget's printed Output, which this direct
        # cell-execution technique does not capture) and compare against the
        # committed audit JSON.
        import numpy as np
        from sklearn.metrics import mean_squared_error, r2_score
        from sklearn.model_selection import KFold, cross_validate, train_test_split
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        X, y = self.ns["X"], self.ns["y"]
        pools = self.ns["_stability_pools_cache"]
        idx = pools[100]
        Xp, yp = X[idx], y[idx]

        Xtr, Xte, ytr, yte = train_test_split(Xp, yp, test_size=0.25, random_state=0)
        pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=20)).fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        single_mse = mean_squared_error(yte, pred)

        kf = KFold(n_splits=5, shuffle=True, random_state=0)
        scores = cross_validate(
            make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=20)),
            Xp, yp, cv=kf, scoring=("neg_mean_squared_error", "r2"),
        )
        cv_mse = (-scores["test_neg_mean_squared_error"]).mean()

        size_entry = next(s for s in AUDIT_RESULT["part_a_sample_size_stability"]["sizes"] if s["sample_size"] == 100)
        audited_single = next(s for s in size_entry["single_split"] if s["seed"] == 0)
        audited_cv = next(c for c in size_entry["cv_by_folds"]["5"] if c["seed"] == 0)
        self.assertAlmostEqual(single_mse, audited_single["test_mse"], places=2)
        self.assertAlmostEqual(cv_mse, audited_cv["mean_mse"], places=2)


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class CvCheckCellBehavior(unittest.TestCase):
    """The Section 3 cross-validation check cell must behave correctly for a
    correct, an incorrect-but-complete, and an unfinished student attempt --
    exercised directly (fast, no browser) against the exact check-cell
    source every rendered notebook shares."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp45-304-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "cv_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_incorrect_but_complete_attempt_is_not_falsely_called_a_failure(self):
        import numpy as np

        ns = dict(self.base_ns)
        ns["cv_fold_mse"] = np.array([500.0, 510.0, 495.0, 505.0, 498.0])
        ns["cv_mean_mse"] = float(ns["cv_fold_mse"].mean())
        output = self._run(ns)
        self.assertNotIn("Looks good", output)
        self.assertIn("differs from", output)
        self.assertNotIn("fail", output.lower())

    def test_wrong_fold_count_is_flagged(self):
        import numpy as np

        ns = dict(self.base_ns)
        ns["cv_fold_mse"] = np.array([33.0, 34.0, 35.0])
        ns["cv_mean_mse"] = 34.0
        output = self._run(ns)
        self.assertIn("Not quite", output)

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)


class NestedCvCheckCellBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp45-506-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "nested_check", "exec"), dict(ns))
        return out.getvalue()

    def test_correct_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message(self):
        import pandas as pd

        ns = dict(self.base_ns)
        ns["nested"] = pd.DataFrame([])
        output = self._run(ns)
        self.assertIn("Not complete yet", output)


if __name__ == "__main__":
    unittest.main()
