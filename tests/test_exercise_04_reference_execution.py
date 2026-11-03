"""Executes the completed Exercise 4 reference notebook and checks its
numbers against the generator's own recomputed EXPECTED_* constants
(scripts/generate_exercise_04_notebook.py), modeled on
tests/test_exercise_02_reference_execution.py.

WP62: this notebook now selects C from a validation set rather than using
the retired fixed C=1.0, so it is intentionally no longer compared against
scripts/classification_model_audit_result.json -- that file documents a
separate, unchanged audit of the fixed-C procedure for other callers
(scripts/export_classification_threshold_data.py,
scripts/export_classification_imbalance_data.py).

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
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_reference_execution.py'
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import os
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_04_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import generate_exercise_04_notebook as gen  # noqa: E402

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
    # WP60 correction: the live JupyterLite copy opens from "v2/" (see
    # LITE_TEMPLATE_PATH), and JupyterLite sets the kernel's cwd to the
    # notebook's own directory -- this chdir mirrors that exactly, so the
    # loader's "../data/..." resolves and this test actually stays
    # offline (reads the committed local CSV) instead of silently falling
    # back to a live network fetch.
    os.chdir(REPO_ROOT / "book" / "lite" / "files" / "v2")
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
        self.assertEqual(len(self.ns["df"]), gen.EXPECTED_N_TOTAL)
        self.assertEqual(len(self.ns["FEATURES"]), gen.EXPECTED_N_FEATURES)

    def test_class_counts_match_the_audit(self):
        self.assertEqual(int(self.ns["y"].sum()), gen.EXPECTED_N_POSITIVE)
        self.assertEqual(int((self.ns["y"] == 0).sum()), gen.EXPECTED_N_NEGATIVE)

    def test_established_split_sizes(self):
        self.assertEqual(len(self.ns["y_train"]), gen.EXPECTED_N_TRAIN)
        self.assertEqual(len(self.ns["y_val"]), gen.EXPECTED_N_VAL)
        self.assertEqual(len(self.ns["y_test"]), gen.EXPECTED_N_TEST)

    def test_logistic_regression_matches_established_result(self):
        self.assertAlmostEqual(self.ns["accuracy"], gen.EXPECTED_ACCURACY, places=6)
        self.assertAlmostEqual(self.ns["sensitivity"], gen.EXPECTED_SENSITIVITY, places=6)
        self.assertAlmostEqual(self.ns["specificity"], gen.EXPECTED_SPECIFICITY, places=6)
        self.assertAlmostEqual(self.ns["auc"], gen.EXPECTED_AUC, places=6)

    def test_confusion_matrix_matches_established_result(self):
        self.assertEqual(int(self.ns["tn"]), gen.EXPECTED_TN)
        self.assertEqual(int(self.ns["fp"]), gen.EXPECTED_FP)
        self.assertEqual(int(self.ns["fn"]), gen.EXPECTED_FN)
        self.assertEqual(int(self.ns["tp"]), gen.EXPECTED_TP)

    def test_selected_c_matches_the_validation_search(self):
        self.assertEqual(self.ns["selected_C"], gen.EXPECTED_SELECTED_C)
        self.assertEqual(len(self.ns["validation_table"]), len(gen.C_GRID))
        self.assertEqual(list(self.ns["validation_table"]["C"]), gen.C_GRID)

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

    def test_data_setup_cell_emits_no_performance_warning(self):
        # WP53 item: SEX/SITE used to be appended to the already-wide
        # (~360-column) predictor table one column at a time, which pandas
        # flags as PerformanceWarning ("DataFrame is highly fragmented ...
        # Consider using pd.concat instead"), reproduced live in
        # JupyterLite. Re-executes just the data/setup cell in isolation,
        # under warnings.catch_warnings(record=True), and asserts zero
        # PerformanceWarnings -- the exact cell the WP names.
        import warnings

        nb_cells = nbformat.read(REFERENCE_PATH, as_version=4).cells
        setup_cell = next(c for c in nb_cells if c.get("id") == "wp44-000-setup")
        load_cell = next(c for c in nb_cells if c.get("id") == "wp44-102-load")
        old_cwd = os.getcwd()
        os.chdir(REPO_ROOT / "book" / "lite" / "files" / "v2")
        try:
            ns: dict = {}
            asyncio.run(_run_cell(setup_cell["source"], ns, "wp44-000-setup"))
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                asyncio.run(_run_cell(load_cell["source"], ns, "wp44-102-load"))
        finally:
            os.chdir(old_cwd)
        perf_warnings = [w for w in caught if "PerformanceWarning" in type(w.message).__name__]
        self.assertEqual(perf_warnings, [])
        self.assertEqual(ns["df"].shape[1], len(ns["_ABIDE_LITE_FEATURES"]) + 3)  # + group, SEX, SITE
        self.assertEqual(list(ns["df"].columns[-2:]), ["SEX", "SITE"])

    def test_shuffle_is_reproducible_and_varies_positions_across_questions(self):
        # WP53 course-wide review item 2: correct answers must not all land
        # first, and the same per-question seed must always give the same
        # order (so rerunning a show_question() cell never unpredictably
        # changes it) -- the same check already established for Exercise 9
        # (see tests/test_exercise_09_reference_execution.py).
        import random

        questions = self.ns["_QUESTIONS"]
        self.assertEqual(len(questions), 5)
        positions = []
        for qid, q in questions.items():
            seed = q["shuffle_seed"]
            n = len(q["options"])
            order = list(range(n))
            random.Random(seed).shuffle(order)
            order2 = list(range(n))
            random.Random(seed).shuffle(order2)
            self.assertEqual(order, order2, qid)
            if q["kind"] == "multi":
                positions.append(sorted(order.index(i) for i in q["correct_indices"]))
            else:
                positions.append(order.index(q["correct_index"]))

        flat_first_positions = [p[0] if isinstance(p, list) else p for p in positions]
        self.assertGreater(len(set(flat_first_positions)), 1)
        single_positions = [p for p in positions if isinstance(p, int)]
        self.assertTrue(any(p != 0 for p in single_positions))


def _check_cell_source(cell_id: str) -> str:
    nb = nbformat.read(REFERENCE_PATH, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == cell_id)
    return cell["source"]


class XYCheckCellBehavior(unittest.TestCase):
    """The Section 3 X/y sanity check (wp44-324-check) must behave correctly
    whether a student builds X/y as NumPy arrays or as a pandas
    DataFrame/Series, and must give one helpful message -- never an
    ambiguous-Series-truth-value crash -- for incomplete, nonnumeric, or
    invalid-label attempts. Exercised directly (fast, no browser) against
    the exact check-cell source every rendered notebook shares (WP48)."""

    @classmethod
    def setUpClass(cls):
        cls.source = _check_cell_source("wp44-324-check")
        cls.base_ns = _execute_reference_notebook()

    def _run(self, ns: dict) -> str:
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(self.source, "xy_check", "exec"), dict(ns))
        return out.getvalue()

    def test_numpy_attempt_prints_looks_good(self):
        output = self._run(self.base_ns)
        self.assertIn("Looks good", output)

    def test_dataframe_and_series_attempt_prints_looks_good(self):
        # The exact ambiguous-truth-value regression this check must avoid:
        # np.isfinite(X).all() on a DataFrame returns a per-column Series,
        # which raises in a bare `if`/`elif` instead of printing a message.
        ns = dict(self.base_ns)
        ns["X"] = ns["df"][ns["FEATURES"]]
        ns["y"] = ns["df"]["group"]
        output = self._run(ns)
        self.assertIn("Looks good", output)

    def test_unfinished_attempt_gives_a_helpful_message_not_an_error(self):
        output = self._run({})
        self.assertIn("Not complete yet", output)

    def test_nonnumeric_x_gives_a_helpful_message_not_a_crash(self):
        ns = dict(self.base_ns)
        bad_x = ns["X"].astype(object).copy()
        bad_x[0, 0] = "not a number"
        ns["X"] = bad_x
        output = self._run(ns)
        self.assertIn("Not quite", output)
        self.assertIn("numeric", output)

    def test_incomplete_row_count_gives_a_helpful_message(self):
        ns = dict(self.base_ns)
        ns["X"] = ns["X"][:-1]
        output = self._run(ns)
        self.assertIn("Not quite", output)
        self.assertIn("rows", output)

    def test_raw_1_2_labels_are_rejected_before_downstream_use(self):
        ns = dict(self.base_ns)
        ns["y"] = ns["y"] + 1  # simulate an un-recoded {1, 2} label
        output = self._run(ns)
        self.assertIn("Not quite", output)
        self.assertIn("only 0 and 1", output)


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
