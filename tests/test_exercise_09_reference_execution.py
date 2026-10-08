"""Executes the completed Exercise 9 reference notebook and checks its
numbers against directly-verified results -- verified directly against
book/lite/files/data/abide_age_brain.csv using the same train_test_split
convention every other exercise uses (test_size=0.25, random_state=42,
stratify=group); see the generator's module docstring and WP52_REPORT.md
for the full reasoning and every verification command. Modeled on
tests/test_exercise_08_reference_execution.py and the WP51 version of this
file, trimmed/extended for WP52's 15 review corrections.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45/WP46/WP47/WP51 documented: this notebook's
native widgets use an ipywidgets ``Output()`` widget as a context manager,
which hangs nbclient's real ZMQ kernel with no frontend attached to
acknowledge the widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_reference.ipynb"
STUDENT_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09.ipynb"

_TOP_LEVEL_AWAIT = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT


async def _run_cell(source: str, ns: dict, name: str) -> None:
    code = compile(source, name, "exec", flags=_TOP_LEVEL_AWAIT)
    result = eval(code, ns)
    if inspect.iscoroutine(result):
        await result


async def _execute_notebook(nb) -> tuple[dict, list[tuple[int, str, str]]]:
    ns: dict = {}
    errors: list[tuple[int, str, str]] = []
    for i, cell in enumerate(nb.cells):
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        try:
            await _run_cell(source, ns, f"cell_{i}")
        except Exception as exc:  # noqa: BLE001 -- collected, not swallowed
            errors.append((i, cell.get("id"), f"{type(exc).__name__}: {exc}"))
    return ns, errors


def _execute(path: Path) -> tuple[dict, list[tuple[int, str, str]]]:
    import matplotlib

    matplotlib.use("Agg")  # headless: no display, no GUI event loop
    old_cwd = os.getcwd()
    os.chdir(REPO_ROOT / "book" / "lite" / "files")
    try:
        nb = nbformat.read(path, as_version=4)
        return asyncio.run(_execute_notebook(nb))
    finally:
        os.chdir(old_cwd)


class ReferenceExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns, cls.errors = _execute(REFERENCE_PATH)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_section_6_compare_cell_raises_no_matplotlib_warning(self):
        # WP52 item 14: re-run Section 6's own compare cell (the one that
        # builds the bar chart) in isolation, with warnings as errors, to
        # confirm set_xticks() before set_xticklabels() actually avoids the
        # "FixedFormatter should only be used together with FixedLocator"
        # warning -- not just that the code looks right.
        import warnings

        import matplotlib

        matplotlib.use("Agg")
        nb = nbformat.read(REFERENCE_PATH, as_version=4)
        compare_cell = next(c for c in nb.cells if c.get("id") == "wp51-603-compare")
        ns = dict(self.ns)
        old_cwd = os.getcwd()
        os.chdir(REPO_ROOT / "book" / "lite" / "files")
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                exec(compile(compare_cell["source"], "wp51-603-compare", "exec"), ns)
        finally:
            os.chdir(old_cwd)
        matplotlib_warnings = [w for w in caught if "matplotlib" in str(w.category.__module__).lower() or "Fixed" in str(w.message)]
        self.assertEqual(matplotlib_warnings, [], [str(w.message) for w in matplotlib_warnings])

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["df"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)
        self.assertEqual(self.ns["X_train"].shape, (753, 360))
        self.assertEqual(self.ns["X_val"].shape, (251, 360))

    def test_pcr_results_match_directly_verified_numbers_mse_and_r2(self):
        by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pcr_results"]}
        r2_by_n = {r["n_components"]: r["val_r2"] for r in self.ns["pcr_results"]}
        expected_mse = {2: 51.138, 5: 44.488, 10: 34.808, 20: 31.943, 50: 29.610}
        expected_r2 = {2: 0.452, 5: 0.523, 10: 0.627, 20: 0.658, 50: 0.683}
        for n, exp in expected_mse.items():
            self.assertAlmostEqual(by_n[n], exp, delta=0.05)
        for n, exp in expected_r2.items():
            self.assertAlmostEqual(r2_by_n[n], exp, delta=0.01)
        # monotonically improving across this grid, as directly verified
        ordered = [by_n[n] for n in sorted(by_n)]
        self.assertTrue(all(a >= b - 1e-6 for a, b in zip(ordered, ordered[1:])))

    def test_pls_results_match_directly_verified_numbers_and_peak_at_5(self):
        by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pls_results"]}
        r2_by_n = {r["n_components"]: r["val_r2"] for r in self.ns["pls_results"]}
        expected_mse = {2: 39.935, 5: 29.658, 10: 38.797, 20: 48.906, 50: 49.555}
        expected_r2 = {2: 0.572, 5: 0.682, 10: 0.584, 20: 0.476, 50: 0.469}
        for n, exp in expected_mse.items():
            self.assertAlmostEqual(by_n[n], exp, delta=0.05)
        for n, exp in expected_r2.items():
            self.assertAlmostEqual(r2_by_n[n], exp, delta=0.01)
        self.assertEqual(min(by_n, key=by_n.get), 5)

    def test_pls_beats_pcr_at_low_component_counts_but_not_at_pcrs_own_best(self):
        pcr_by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pcr_results"]}
        pls_by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pls_results"]}
        self.assertLess(pls_by_n[5], pcr_by_n[5])
        self.assertGreater(min(pls_by_n.values()), min(pcr_by_n.values()) - 0.2)

    def test_svr_subset_results_match_directly_verified_numbers(self):
        results = {(r["kernel"], r["C"]): r["val_mse"] for r in self.ns["svr_results"]}
        self.assertAlmostEqual(results[("linear", 1)], 94.996, delta=0.1)
        self.assertAlmostEqual(results[("rbf", 1)], 60.886, delta=0.1)
        self.assertAlmostEqual(results[("rbf", 100)], 29.535, delta=0.1)
        self.assertEqual(len(self.ns["X_train_svr_subset"]), 300)

    def test_svr_subset_is_a_strict_subset_of_the_training_partition(self):
        self.assertLess(len(self.ns["X_train_svr_subset"]), len(self.ns["X_train"]))

    def test_ridge_and_kernel_ridge_match_directly_verified_numbers(self):
        self.assertAlmostEqual(self.ns["ridge_result"]["val_mse"], 31.813, delta=0.01)
        self.assertAlmostEqual(self.ns["kernel_ridge_result"]["val_mse"], 21.924, delta=0.01)
        self.assertAlmostEqual(self.ns["ridge_result"]["val_r2"], 0.659, delta=0.01)
        self.assertAlmostEqual(self.ns["kernel_ridge_result"]["val_r2"], 0.765, delta=0.01)

    def test_kernel_ridge_beats_plain_ridge_on_this_split(self):
        self.assertLess(self.ns["kernel_ridge_result"]["val_mse"], self.ns["ridge_result"]["val_mse"])

    def test_svc_boundary_activity_default_matches_directly_verified_numbers(self):
        # WP52 item 7: the standalone demo was removed; make_svc_dataset
        # and the SVC pipeline now live only inside the interactive
        # activity's own cell. Reproduce its default setting (nonlinear
        # data, RBF, C=1, gamma="scale") directly here, the same way the
        # widget's own _svm_render() does internally.
        X2, y2, train_idx, val_idx = self.ns["make_svc_dataset"]("nonlinear")
        pipe = self.ns["Pipeline"]([("scale", self.ns["StandardScaler"]()), ("svc", self.ns["SVC"](kernel="rbf", C=1, gamma="scale"))])
        pipe.fit(X2[train_idx], y2[train_idx])
        self.assertAlmostEqual(pipe.score(X2[train_idx], y2[train_idx]), 0.949, delta=0.01)
        self.assertAlmostEqual(pipe.score(X2[val_idx], y2[val_idx]), 0.952, delta=0.01)

    def test_full_data_svr_benchmark_is_a_separate_labeled_instructor_row(self):
        # WP52 item 13: not the student's subset result, not the old
        # nested-CV summary -- a distinct, labeled, offline-computed row.
        self.assertIn("SVR_BENCHMARK", self.ns)
        benchmark = self.ns["SVR_BENCHMARK"]
        self.assertAlmostEqual(benchmark["val_mse"], 54.083, delta=0.01)
        self.assertAlmostEqual(benchmark["val_r2"], 0.421, delta=0.01)
        self.assertEqual(benchmark["n_train"], 753)
        self.assertEqual(benchmark["n_features"], 360)
        svr_subset_best = min(self.ns["svr_results"], key=lambda r: r["val_mse"])
        self.assertNotAlmostEqual(svr_subset_best["val_mse"], benchmark["val_mse"], delta=0.01)

    def test_comparison_table_has_r2_for_every_row(self):
        comparison_df = self.ns["comparison_df"]
        self.assertIn("val_r2", comparison_df.columns)
        self.assertTrue(comparison_df["val_r2"].notna().all())
        self.assertEqual(len(comparison_df), 5)  # PCR, PLS, Ridge, KernelRidge, SVR benchmark

    def test_single_split_never_reused_as_a_second_locked_test_set(self):
        # WP51 "Load and split": exactly one split, reused throughout --
        # never recombined into a second held-out layer.
        self.assertNotIn("X_test", self.ns)
        self.assertNotIn("y_test", self.ns)

    def test_shuffle_is_reproducible_and_varies_positions_across_questions(self):
        # WP52 item 6: correct answers must not all land first, and the
        # same per-question seed must always give the same order (so
        # rerunning a show_question() cell never unpredictably changes it).
        import random

        questions = self.ns["_QUESTIONS"]
        self.assertEqual(len(questions), 5)
        positions = []
        for qid, q in questions.items():
            seed = q["shuffle_seed"]
            if q["type"] == "multi":
                n = len(q["statements"])
                order = list(range(n))
                random.Random(seed).shuffle(order)
                positions.append(sorted(order.index(i) for i in q["correct_indices"]))
                order2 = list(range(n))
                random.Random(seed).shuffle(order2)
                self.assertEqual(order, order2, qid)
            else:
                n = len(q["options"])
                order = list(range(n))
                random.Random(seed).shuffle(order)
                positions.append(order.index(q["correct_index"]))
                order2 = list(range(n))
                random.Random(seed).shuffle(order2)
                self.assertEqual(order, order2, qid)

        flat_first_positions = [p[0] if isinstance(p, list) else p for p in positions]
        self.assertGreater(len(set(flat_first_positions)), 1)
        single_positions = [p for p in positions if isinstance(p, int)]
        self.assertTrue(any(p != 0 for p in single_positions))

    def test_show_question_displays_the_shuffled_widget_with_correct_feedback(self):
        # Executed proof (not just a position check): building the actual
        # widget for one single-choice and one multi-choice question, after
        # shuffling, and confirming the right selection reports correct.
        # (ipywidgets' Output() only truly captures stdout inside a live
        # frontend comm; outside one, prints simply pass through -- so this
        # captures real process stdout instead of reading widget.outputs.)
        import io
        import random
        from contextlib import redirect_stdout

        make_single = self.ns["make_single_choice_question"]
        make_multi = self.ns["make_multi_choice_question"]
        q = self.ns["_QUESTIONS"]["q-leakage"]

        order = list(range(len(q["options"])))
        random.Random(q["shuffle_seed"]).shuffle(order)
        shuffled_options = [q["options"][i] for i in order]
        shuffled_correct = order.index(q["correct_index"])
        widget = make_single(q["prompt"], shuffled_options, shuffled_correct, q["feedback_correct"])
        radio = widget.children[2]
        radio.index = shuffled_correct
        button = widget.children[3]
        captured = io.StringIO()
        with redirect_stdout(captured):
            button.click()
        self.assertIn("Correct", captured.getvalue())

        mq = self.ns["_QUESTIONS"]["q-c-gamma-epsilon"]
        morder = list(range(len(mq["statements"])))
        random.Random(mq["shuffle_seed"]).shuffle(morder)
        shuffled_statements = [mq["statements"][i] for i in morder]
        shuffled_correct_set = {morder.index(i) for i in mq["correct_indices"]}
        mwidget = make_multi(mq["prompt"], shuffled_statements, shuffled_correct_set, mq["feedback_correct"])
        checkboxes = [c for c in mwidget.children if type(c).__name__ == "Checkbox"]
        for i in shuffled_correct_set:
            checkboxes[i].value = True
        mbutton = next(c for c in mwidget.children if type(c).__name__ == "Button")
        mcaptured = io.StringIO()
        with redirect_stdout(mcaptured):
            mbutton.click()
        self.assertIn("Correct", mcaptured.getvalue())

    def test_removed_sections_leave_no_trace_in_the_executed_namespace(self):
        # WP52 item 10: Lasso/RBFSampler/KNN demos no longer exist.
        for name in (
            "plain_lasso_nnz",
            "rbf_lasso_nnz",
            "plain_logistic_val_acc",
            "rbf_logistic_val_acc",
            "knn_uniform",
            "knn_gaussian",
        ):
            self.assertNotIn(name, self.ns)


class StudentTemplateNoCascade(unittest.TestCase):
    """The untouched template must execute cleanly end to end: every blank's
    own check cell degrades to its own guidance, with zero exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.ns, cls.errors = _execute(STUDENT_PATH)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_every_required_blank_check_cell_shows_not_complete_yet(self):
        import io
        from contextlib import redirect_stdout

        nb = nbformat.read(STUDENT_PATH, as_version=4)
        for check_id in (
            "wp51-205-pcr-check",
            "wp51-305-pls-check",
            "wp51-412-svr-check",
            "wp51-506-kernelridge-check",
        ):
            cell = next(c for c in nb.cells if c.get("id") == check_id)
            out = io.StringIO()
            with redirect_stdout(out):
                exec(compile(cell["source"], check_id, "exec"), dict(self.ns))
            self.assertIn("Not complete yet", out.getvalue(), check_id)

    def test_supplied_activities_and_demos_run_independently_of_every_blank(self):
        # The native widgets and the SVR benchmark constant are all
        # supplied (not blanks) and must work even though every blank above
        # them was left untouched.
        self.assertIn("SVR_BENCHMARK", self.ns)
        self.assertEqual(len(self.ns["X_train"]), 753)
        self.assertEqual(len(self.ns["X_val"]), 251)

    def test_comparison_table_reports_missing_results_without_raising(self):
        # pcr_results/pls_results/svr_results are pre-declared as empty
        # lists by the starter cells themselves (WP52 item 2's required
        # shape); ridge_result/kernel_ridge_result have no such
        # pre-declaration and are genuinely absent until the blank runs.
        self.assertEqual(self.ns.get("pcr_results"), [])
        self.assertEqual(self.ns.get("pls_results"), [])
        self.assertNotIn("ridge_result", self.ns)
        self.assertNotIn("kernel_ridge_result", self.ns)
        self.assertIn("_missing", self.ns)
        self.assertGreaterEqual(len(self.ns["_missing"]), 4)
        # The instructor SVR benchmark is never "missing" -- it does not
        # depend on any student blank.
        self.assertIn("comparison_df", self.ns)
        self.assertEqual(len(self.ns["comparison_df"]), 1)


if __name__ == "__main__":
    unittest.main()
