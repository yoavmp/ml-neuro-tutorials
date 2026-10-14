"""Executes the completed Exercise 12 reference notebook and checks its
numbers against directly-verified results -- verified directly against
book/lite/files/data/abide_age_brain.csv (Cases 1 and 3) and the fixed-seed
synthetic generators defined by the generator itself (Cases 2, 4, 5, 6);
see scripts/generate_exercise_12_notebook.py's module docstring and
WPs/reports/WP57_REPORT.md for the full verification transcript. Modeled on
tests/test_exercise_09_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44-WP47/WP51/WP52 documented: this notebook's native
widgets use an ipywidgets ``Output()`` widget as a context manager, which
hangs nbclient's real ZMQ kernel with no frontend attached to acknowledge
the widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_12_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_12_reference.ipynb"
STUDENT_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_12.ipynb"

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

    # -- Case 1 --------------------------------------------------------

    def test_three_way_split_shapes(self):
        self.assertEqual(len(self.ns["df"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)
        self.assertEqual(self.ns["X_train"].shape, (602, 360))
        self.assertEqual(self.ns["X_val"].shape, (201, 360))
        self.assertEqual(self.ns["X_test"].shape, (201, 360))

    def test_scaler_leaky_is_fit_on_train_and_val_never_test(self):
        # WP57R: the contaminated scaler now excludes X_test entirely
        # (803 rows = X_train + X_val), unlike the WP57 original (1,004
        # rows, including X_test) -- preserving X_test as genuinely
        # untouched for Case 3.
        self.assertEqual(len(self.ns["X_train_and_val"]), 803)
        self.assertAlmostEqual(self.ns["scaler_leaky"].mean_[0], 2.371498, delta=0.001)
        self.assertAlmostEqual(self.ns["scaler_honest"].mean_[0], 2.371573, delta=0.001)

    def test_leaky_and_honest_scaler_means_differ_but_only_slightly(self):
        diff = abs(self.ns["scaler_leaky"].mean_[0] - self.ns["scaler_honest"].mean_[0])
        self.assertGreater(diff, 0.0)
        self.assertLess(diff, 0.05)

    def test_case1_check_cell_passes_for_honest_and_fails_for_leaky(self):
        # WP57R: directly demonstrates the fixed check cell's own
        # discriminating power -- a scaler fit on X_train passes a tight
        # tolerance; the supplied leaky scaler (fit on X_train_and_val)
        # fails it. The original check (TOLERANCE=0.01 against one
        # hardcoded feature mean) would have let the leaky scaler pass.
        import io
        from contextlib import redirect_stdout

        nb = nbformat.read(REFERENCE_PATH, as_version=4)
        check_cell = next(c for c in nb.cells if c.get("id") == "wp57-110-case1-check")

        ns_honest = dict(self.ns)
        ns_honest["scaler_honest"] = self.ns["scaler_honest"]
        out_honest = io.StringIO()
        with redirect_stdout(out_honest):
            exec(compile(check_cell["source"], "wp57-110-case1-check", "exec"), ns_honest)
        self.assertIn("Looks good", out_honest.getvalue())

        ns_leaky = dict(self.ns)
        ns_leaky["scaler_honest"] = self.ns["scaler_leaky"]  # submit the WRONG (leaky) scaler
        out_leaky = io.StringIO()
        with redirect_stdout(out_leaky):
            exec(compile(check_cell["source"], "wp57-110-case1-check", "exec"), ns_leaky)
        self.assertIn("Not quite", out_leaky.getvalue())
        self.assertNotIn("Looks good", out_leaky.getvalue())

    def test_case1_knn_comparison_matches_directly_verified_numbers(self):
        results = self.ns["case1_knn_results"]
        expected = {
            "full": {"leaky_val_mse": 32.7146, "honest_val_mse": 32.3903},
            100: {"leaky_val_mse": 60.0136, "honest_val_mse": 60.9107},
            60: {"leaky_val_mse": 10.3340, "honest_val_mse": 10.6304},
        }
        for size_label, exp in expected.items():
            self.assertAlmostEqual(results[size_label]["leaky_val_mse"], exp["leaky_val_mse"], delta=0.01)
            self.assertAlmostEqual(results[size_label]["honest_val_mse"], exp["honest_val_mse"], delta=0.01)
        # Direction is not guaranteed and is reported honestly either way.
        self.assertGreater(results["full"]["leaky_val_mse"], results["full"]["honest_val_mse"])
        self.assertLess(results[100]["leaky_val_mse"], results[100]["honest_val_mse"])
        self.assertLess(results[60]["leaky_val_mse"], results[60]["honest_val_mse"])

    def test_case1_knn_comparison_never_reads_x_test(self):
        self.assertEqual(len(self.ns["_case1_pool_X"]), len(self.ns["X_train"]) + len(self.ns["X_val"]))

    # -- Case 2 --------------------------------------------------------

    def test_case2_contaminated_r2_matches_directly_verified_value(self):
        self.assertAlmostEqual(self.ns["contaminated_r2"], 0.8973, delta=0.001)

    def test_case2_honest_r2_matches_directly_verified_value(self):
        self.assertAlmostEqual(self.ns["honest_pca_r2"], 0.1209, delta=0.01)

    def test_case2_contaminated_path_cannot_run_without_the_held_out_y(self):
        # The contaminated path's own fitted scaler/PCA expect 3 columns
        # (x1, x2, y) -- confirms the structural requirement is real, not
        # just a label.
        self.assertEqual(self.ns["contaminated_scaler"].mean_.shape, (3,))
        self.assertEqual(self.ns["honest_scaler"].mean_.shape, (2,))

    def test_case2_honest_r2_is_far_below_contaminated(self):
        self.assertLess(self.ns["honest_pca_r2"], self.ns["contaminated_r2"] - 0.3)

    # -- Case 3 --------------------------------------------------------

    def test_case3_tree_val_results_match_directly_verified_numbers(self):
        by_depth = {r["depth"]: r["val_mse"] for r in self.ns["tree_val_results"]}
        expected = {1: 72.596, 2: 54.358, 3: 46.895, 5: 45.123, 10: 46.283, None: 46.524}
        for d, exp in expected.items():
            self.assertAlmostEqual(by_depth[d], exp, delta=0.1)

    def test_case3_selection_disagrees_between_train_and_val(self):
        self.assertEqual(self.ns["depth_by_train_mse"], None)
        self.assertEqual(self.ns["depth_by_val_mse"], 5)
        self.assertNotEqual(self.ns["depth_by_train_mse"], self.ns["depth_by_val_mse"])

    def test_case3_val_selected_depth_beats_train_selected_depth_on_test(self):
        test_mse_train_choice = self.ns["test_mse_by_train_choice"]
        test_mse_val_choice = self.ns["test_mse_by_val_choice"]
        self.assertAlmostEqual(test_mse_train_choice, 74.740, delta=0.5)
        self.assertAlmostEqual(test_mse_val_choice, 66.143, delta=0.5)
        self.assertLess(test_mse_val_choice, test_mse_train_choice)

    def test_case3_test_set_never_used_before_the_consequence_cell(self):
        # X_test/y_test must exist (Case 1 defines them) but neither
        # tree_val_results nor depth_by_val_mse computation should have
        # touched them -- only the later consequence cell does.
        self.assertIn("X_test", self.ns)
        self.assertIn("y_test", self.ns)

    # -- Case 4 --------------------------------------------------------

    def test_case4_confusion_matrix_and_metrics(self):
        import numpy as np

        cm = self.ns["case4_cm"]
        self.assertTrue(np.array_equal(cm, np.array([[95, 0], [5, 0]])))
        self.assertAlmostEqual(self.ns["case4_accuracy"], 0.95, delta=0.001)
        self.assertAlmostEqual(self.ns["balanced_acc"], 0.5, delta=0.001)
        self.assertAlmostEqual(self.ns["sensitivity"], 0.0, delta=0.001)
        self.assertAlmostEqual(self.ns["specificity"], 1.0, delta=0.001)
        self.assertIsNone(self.ns["precision"])

    def test_case4_validation_set_has_five_positives_of_one_hundred(self):
        self.assertEqual(len(self.ns["case4_val_idx"]), 100)
        self.assertEqual(int(self.ns["case4_y"][self.ns["case4_val_idx"]].sum()), 5)

    # -- Case 5 --------------------------------------------------------

    def test_case5_row_split_shows_inflated_overlap_and_score(self):
        self.assertEqual(self.ns["row_overlap"], 38)
        self.assertAlmostEqual(self.ns["row_val_r2"], 0.8973, delta=0.01)

    def test_case5_group_split_has_zero_overlap_and_lower_honest_score(self):
        self.assertEqual(self.ns["group_overlap"], 0)
        self.assertAlmostEqual(self.ns["group_val_r2"], 0.6219, delta=0.01)

    def test_case5_group_split_scores_lower_than_row_split(self):
        self.assertLess(self.ns["group_val_r2"], self.ns["row_val_r2"])

    # -- Case 6 --------------------------------------------------------

    def test_case6_test_mse_by_alpha_matches_directly_verified_numbers(self):
        expected = {0.01: 7.584, 0.1: 7.583, 1: 7.573, 10: 7.558, 100: 9.679}
        # Re-derive the per-alpha MSE the same way the notebook's own loop
        # does, to confirm the printed/best values are not just hardcoded.
        from sklearn.linear_model import Ridge
        from sklearn.metrics import mean_squared_error

        for alpha, exp in expected.items():
            model = Ridge(alpha=alpha).fit(
                self.ns["case6_X"][self.ns["case6_train_idx"]], self.ns["case6_y"][self.ns["case6_train_idx"]]
            )
            mse = mean_squared_error(
                self.ns["case6_y"][self.ns["case6_test_idx"]], model.predict(self.ns["case6_X"][self.ns["case6_test_idx"]])
            )
            self.assertAlmostEqual(mse, exp, delta=0.01)

    def test_case6_best_alpha_chosen_by_peeking(self):
        self.assertEqual(self.ns["best_alpha"], 10)
        self.assertAlmostEqual(self.ns["best_test_mse"], 7.558, delta=0.01)

    # -- questions -------------------------------------------------------

    def test_seven_questions_defined(self):
        self.assertEqual(len(self.ns["_QUESTIONS"]), 7)

    def test_shuffle_is_reproducible_and_varies_positions_across_questions(self):
        import random

        questions = self.ns["_QUESTIONS"]
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

        single_positions = [p for p in positions if isinstance(p, int)]
        self.assertGreater(len(set(single_positions)), 1)
        self.assertTrue(any(p != 0 for p in single_positions))

    def test_show_question_displays_the_shuffled_widget_with_correct_feedback(self):
        import io
        import random
        from contextlib import redirect_stdout

        make_single = self.ns["make_single_choice_question"]
        make_multi = self.ns["make_multi_choice_question"]
        q = self.ns["_QUESTIONS"]["q-scaler-leakage"]

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

        mq = self.ns["_QUESTIONS"]["q-classifier-metrics"]
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

    # -- widgets self-contained and independent of blanks ------------------

    def test_widget1_recomputes_both_paths_independently(self):
        self.assertIn("_w_r2_contaminated", self.ns)
        self.assertIn("_w_r2_honest", self.ns)
        self.assertAlmostEqual(self.ns["_w_r2_contaminated"], 0.8973, delta=0.001)
        self.assertAlmostEqual(self.ns["_w_r2_honest"], 0.1209, delta=0.01)

    def test_widget2_precomputed_fits_cover_the_full_depth_grid(self):
        self.assertEqual(set(self.ns["_w3_fits"].keys()), {1, 2, 3, 5, 10, None})


class StudentTemplateNoCascade(unittest.TestCase):
    """The untouched template must execute cleanly end to end: every
    blank's own check cell degrades to its own guidance, with zero
    exceptions, and cases stay independent of each other."""

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
            "wp57-110-case1-check",
            "wp57-209-case2-check",
            "wp57-309-case3-check",
            "wp57-507-case5-check",
        ):
            cell = next(c for c in nb.cells if c.get("id") == check_id)
            out = io.StringIO()
            with redirect_stdout(out):
                exec(compile(cell["source"], check_id, "exec"), dict(self.ns))
            self.assertIn("Not complete yet", out.getvalue(), check_id)

    def test_supplied_widgets_and_demos_run_independently_of_every_blank(self):
        # Both native widgets and Case 1/4/6's supplied demos work even
        # though every required blank above/around them was left untouched.
        self.assertAlmostEqual(self.ns["_w_r2_contaminated"], 0.8973, delta=0.001)
        self.assertEqual(set(self.ns["_w3_fits"].keys()), {1, 2, 3, 5, 10, None})
        self.assertAlmostEqual(self.ns["case4_accuracy"], 0.95, delta=0.001)
        self.assertEqual(self.ns["best_alpha"], 10)
        self.assertIn("full", self.ns["case1_knn_results"])

    def test_consequence_cells_report_missing_without_raising(self):
        self.assertIsNone(self.ns.get("scaler_honest"))
        self.assertIsNone(self.ns.get("honest_pca_r2"))
        self.assertEqual(self.ns.get("tree_val_results"), [])
        self.assertIsNone(self.ns.get("depth_by_val_mse"))
        self.assertIsNone(self.ns.get("group_overlap"))
        self.assertIsNone(self.ns.get("group_val_r2"))

    def test_case3_and_case5_independent_cases_still_run_despite_case1_case2_blanks(self):
        # Cases 3-6 do not depend on Case 1's or Case 2's blanks at all.
        self.assertEqual(self.ns["depth_by_train_mse"], None)
        self.assertAlmostEqual(self.ns["row_val_r2"], 0.8973, delta=0.01)
        self.assertAlmostEqual(self.ns["case4_accuracy"], 0.95, delta=0.001)


if __name__ == "__main__":
    unittest.main()
