"""Offline structural tests for the Exercise 12 JupyterLite notebook.

WP57, modeled on tests/test_exercise_09_lite_notebook.py: required YOUR
CODE HERE tasks exist with no disguised solutions (not even in comments),
checked questions have keyed answers IN THE HIDDEN SETUP CELL ONLY,
correct answers are reproducibly shuffled rather than always listed first,
no install cell, no iframe, and the student template, its portable copy,
and the completed reference notebook stay structurally synchronized by
construction (scripts/generate_exercise_12_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_12_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_12_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_12.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_12" / "exercise_12_portable.ipynb"
LITE_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_12_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_12_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp57-activity-scaler",
    "wp57-activity-pca",
    "wp57-activity-tree",
    "wp57-activity-group",
}

SINGLE_CHOICE_QUESTION_IDS = {
    "q-scaler-leakage",
    "q-pca-deployment",
    "q-train-vs-val-select",
    "q-tree-deploy",
    "q-group-leakage",
    "q-test-peeking",
}
MULTI_CHOICE_QUESTION_IDS = {"q-classifier-metrics"}
QUESTION_IDS = SINGLE_CHOICE_QUESTION_IDS | MULTI_CHOICE_QUESTION_IDS


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


def _load(path: Path):
    nb = nbformat.read(path, as_version=4)
    return nb, nb.cells


class GeneratorIsUpToDate(unittest.TestCase):
    def test_generated_files_match_the_generator(self):
        import io
        from contextlib import redirect_stdout

        import generate_exercise_12_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_12_notebook.py", "--check"]
        try:
            with redirect_stdout(out):
                gen.main()
        finally:
            sys.argv = argv


class StudentTemplateStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb, cls.cells = _load(LITE_PATH)
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")

    def test_valid_notebook(self):
        nbformat.validate(self.nb)

    def test_title(self):
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 12: Common Mistakes and Pitfalls")

    def test_run_first_notice_precedes_the_collapsed_setup_cell(self):
        notice = self.cells[0]
        self.assertEqual(notice["cell_type"], "markdown")
        self.assertNotIn("source_hidden", notice.get("metadata", {}).get("jupyter", {}))
        self.assertIn("Run the cell below first", _src(notice))

    def test_setup_cell_is_collapsed_and_first(self):
        setup = self.cells[1]
        self.assertEqual(setup["cell_type"], "code")
        self.assertTrue(setup.get("metadata", {}).get("jupyter", {}).get("source_hidden"))

    def test_data_load_gives_an_actionable_error_if_setup_was_skipped(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp57-103-load-split")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_case3_depends_gracefully_on_case1s_split(self):
        tree_cell = next(c for c in self.cells if c.get("id") == "wp57-304-run-it")
        source = _src(tree_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)

    def test_three_way_split_defines_required_names(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp57-103-load-split")
        source = _src(load_cell)
        for name in ("X_train", "X_val", "X_test", "y_train", "y_val", "y_test", "FEATURES"):
            self.assertIn(name, source)
        self.assertEqual(source.count("train_test_split"), 3)

    def test_cell_count_is_reasonable(self):
        self.assertLessEqual(len(self.cells), 90)
        self.assertGreaterEqual(len(self.cells), 50)

    def test_no_stored_error_outputs(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error")

    def test_six_case_headers_present_in_order(self):
        expected = [
            "## 1. Preparing the Predictors",
            "## 2. Two Components",
            "## 3. Picking a Tree",
            "## 4. A High-Accuracy Classifier",
            "## 5. Many Rows per Participant",
            "## 6. One Last Setting to Try",
        ]
        headers = [h for h in self.md.splitlines() if re.match(r"^## \d", h)]
        self.assertEqual(headers, expected)

    def test_case_headers_do_not_reveal_the_mistake(self):
        # WP57: neutral headings -- case names, not "the bug" or "leakage".
        for low_needle in ("leakage", "mistake", "bug", "wrong", "invalid", "flawed"):
            for header in ("## 1. Preparing the Predictors", "## 2. Two Components", "## 3. Picking a Tree",
                           "## 4. A High-Accuracy Classifier", "## 5. Many Rows per Participant",
                           "## 6. One Last Setting to Try"):
                self.assertNotIn(low_needle, header.lower())

    def test_overview_heading_renamed_and_no_case_preview_list(self):
        # WP57R: the six-item "In this notebook you will" list gave away
        # each case's diagnosis before the student reached it -- removed
        # entirely. "What this notebook covers" no longer fits (there is
        # no longer a list of what is covered), so the heading was renamed.
        overview = _src(next(c for c in self.cells if c.get("id") == "wp57-002-overview"))
        self.assertIn("## How This Notebook Works", overview)
        self.assertNotIn("## What this notebook covers", overview)
        self.assertNotIn("In this notebook you will", overview)
        numbered = re.findall(r"^\d+\. ", overview, re.MULTILINE)
        self.assertEqual(len(numbered), 0)

    def test_overview_keeps_the_run_diagnose_repair_inspect_paragraph(self):
        overview = _src(next(c for c in self.cells if c.get("id") == "wp57-002-overview"))
        self.assertIn("**run**", overview)
        self.assertIn("**repair**", overview)
        self.assertIn("**inspect the consequence**", overview)

    def test_real_danger_is_bolded(self):
        overview = _src(next(c for c in self.cells if c.get("id") == "wp57-002-overview"))
        self.assertIn("**that is the real danger**", overview)

    # -- YOUR CODE HERE tasks (4 required blanks: Cases 1, 2, 3, 5) -------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 4)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_fill_code_here_marker_is_itself_a_comment(self):
        for c in self.cells:
            src = _src(c)
            if "YOUR CODE HERE" not in src:
                continue
            for line in src.splitlines():
                if "YOUR CODE HERE" in line:
                    self.assertTrue(line.strip().startswith("#"), line)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_blanks_contain_no_executable_solution_even_commented(self):
        forbidden = (
            ".fit(", "Pipeline([", ".predict(", ".transform(", "mean_squared_error(y_val", "r2_score(y_val",
            "PCA(n_components", "GroupShuffleSplit(", "StandardScaler().fit(",
        )
        for tag in BLANK_TAGS:
            cell = next(c for c in self.cells if tag in c.get("metadata", {}).get("tags", []))
            source = _src(cell)
            self.assertIn("YOUR CODE HERE", source)
            for needle in forbidden:
                self.assertNotIn(needle, source, f"{tag} contains a solution fragment: {needle!r}")

    def test_required_output_names_appear_in_instructions(self):
        case1_instructions = next(c for c in self.cells if c.get("id") == "wp57-108-instructions")
        self.assertIn("scaler_honest", _src(case1_instructions))

        case2_instructions = next(c for c in self.cells if c.get("id") == "wp57-207-instructions")
        self.assertIn("honest_pca_r2", _src(case2_instructions))

        case3_instructions = next(c for c in self.cells if c.get("id") == "wp57-307-instructions")
        for name in ("tree_val_results", "depth_by_val_mse"):
            self.assertIn(name, _src(case3_instructions))

        case5_instructions = next(c for c in self.cells if c.get("id") == "wp57-505-instructions")
        for name in ("group_overlap", "group_val_r2"):
            self.assertIn(name, _src(case5_instructions))

    # -- Case 1: tight live check, and the KNN score-level comparison -----

    def test_case1_scaler_leaky_never_touches_x_test(self):
        run_it = _src(next(c for c in self.cells if c.get("id") == "wp57-105-run-it"))
        self.assertIn("X_train_and_val", run_it)
        self.assertIn("StandardScaler().fit(X_train_and_val)", run_it)
        self.assertNotIn("StandardScaler().fit(X)", run_it)
        # X_test is only ever mentioned in a comment explaining it is NOT
        # used -- never actually read as data anywhere in this cell.
        self.assertNotIn("X_train, X_val, X_test", run_it)
        self.assertNotIn(".fit(X_test", run_it)

    def test_case1_check_uses_a_tight_live_tolerance_not_a_loose_constant(self):
        # WP57R: the original check compared one feature's mean to a
        # hardcoded constant with TOLERANCE=0.01 -- looser than the real
        # diff, so it would have accepted a leaky scaler by mistake. The
        # fixed check compares the full mean vector to X_train's own,
        # live-computed means, with a tight tolerance.
        check = _src(next(c for c in self.cells if c.get("id") == "wp57-110-case1-check"))
        self.assertIn("X_train.mean(axis=0)", check)
        self.assertIn("TOLERANCE = 1e-06", check)
        self.assertNotIn("EXPECTED_MEAN_TRAIN", check)
        self.assertIn(
            "cannot by itself prove every possible solution is leakage-free", check
        )

    def test_case1_consequence_does_not_promise_a_guaranteed_large_effect(self):
        consequence = _src(next(c for c in self.cells if c.get("id") == "wp57-111-consequence"))
        self.assertIn("60 participants", consequence)
        self.assertIn("could shift", consequence)
        self.assertNotIn("always changes the score", consequence)

    def test_case1_knn_comparison_is_supplied_not_a_blank(self):
        knn_cell = next(c for c in self.cells if c.get("id") == "wp57-113-knn-compare")
        src = _src(knn_cell)
        self.assertNotIn("YOUR CODE HERE", src)
        self.assertIn("KNeighborsRegressor", src)
        self.assertIn("CASE1_KNN_K = 5", src)

    def test_case1_knn_comparison_never_touches_x_test(self):
        knn_cell = _src(next(c for c in self.cells if c.get("id") == "wp57-113-knn-compare"))
        # X_test is only ever mentioned in a comment explaining it is NOT
        # used -- never actually read as data anywhere in this cell.
        self.assertNotIn("X_train, X_val, X_test", knn_cell)
        for needle in (".fit(X_test", "[X_test]", ", X_test)", ", X_test,"):
            self.assertNotIn(needle, knn_cell)
        self.assertIn("_case1_pool_X = np.concatenate([X_train, X_val])", knn_cell)

    def test_case1_knn_comparison_reports_every_attempted_size(self):
        knn_cell = _src(next(c for c in self.cells if c.get("id") == "wp57-113-knn-compare"))
        self.assertIn('case1_knn_results["full"]', knn_cell)
        self.assertIn("for n_total in", knn_cell)

    def test_case1_knn_wrapup_accepts_a_small_or_opposite_direction_result(self):
        wrapup = _src(next(c for c in self.cells if c.get("id") == "wp57-114-knn-wrapup"))
        self.assertIn("better", wrapup)
        self.assertIn("not guaranteed", wrapup)

    # -- checked questions: visibility, count, and shuffle -----------------

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp57-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 7)
        for c in checked:
            src = _src(c)
            self.assertNotIn("correct_index", src)
            self.assertNotIn("correct_indices", src)
            self.assertTrue(any(f'show_question("{qid}")' in src for qid in QUESTION_IDS), src)

    def test_hidden_setup_cell_carries_every_question_definition(self):
        setup = self.cells[1]
        source = _src(setup)
        self.assertIn("_QUESTIONS = {", source)
        for qid in QUESTION_IDS:
            self.assertIn(f'"{qid}"', source)
        self.assertIn("correct_index", source)
        self.assertIn("correct_indices", source)
        self.assertIn("def show_question(question_id):", source)
        self.assertIn("shuffle_seed", source)

    def test_exactly_one_multiselect_question(self):
        setup_source = _src(self.cells[1])
        match = re.search(r'"q-classifier-metrics":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertIn('type="multi"', match.group(1))
        for qid in SINGLE_CHOICE_QUESTION_IDS:
            m = re.search(rf'"{re.escape(qid)}":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
            self.assertIsNotNone(m, qid)
            self.assertIn('type="single"', m.group(1))

    def test_every_question_declares_a_shuffle_seed(self):
        setup_source = _src(self.cells[1])
        for qid in QUESTION_IDS:
            block_match = re.search(rf'"{re.escape(qid)}":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
            self.assertIsNotNone(block_match, qid)
            self.assertIn("shuffle_seed=", block_match.group(1), qid)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) ------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/", self.code + self.md)

    def test_two_widgets_present_and_notebook_native(self):
        widget1 = next(c for c in self.cells if c.get("id") == "wp57-212-widget")
        widget2 = next(c for c in self.cells if c.get("id") == "wp57-315-widget")
        for cell in (widget1, widget2):
            src = _src(cell)
            self.assertIn("widgets.Dropdown", src)
            self.assertIn("widgets.Output", src)

    def test_widget1_is_self_contained_and_fixes_axis_range(self):
        widget1 = next(c for c in self.cells if c.get("id") == "wp57-212-widget")
        src = _src(widget1)
        # duplicates its own data/imports rather than depending on the blank
        self.assertIn("_w_rng = np.random.RandomState", src)
        self.assertIn("_w_lo, _w_hi", src)
        self.assertIn("scatter_true_vs_pred", src)

    def test_widget2_precomputes_fits_for_responsiveness(self):
        widget2 = next(c for c in self.cells if c.get("id") == "wp57-315-widget")
        src = _src(widget2)
        self.assertIn("_w3_fits = {}", src)
        # toggle callback only selects/redraws -- no new .fit( call inside it
        render_start = src.index("def _widget3_render")
        render_body = src[render_start:]
        self.assertNotIn(".fit(", render_body)

    def test_widget_controls_use_the_label_overflow_fix(self):
        self.assertIn('style={"description_width": "initial"}', self.code)
        self.assertIn("widget-controls-row", self.code)
        self.assertIn("controls_row(", self.code)

    def test_synthetic_data_is_labeled_as_synthetic(self):
        for cell_id in ("wp57-202-intro", "wp57-402-intro", "wp57-502-intro", "wp57-602-intro"):
            cell = next(c for c in self.cells if c.get("id") == cell_id)
            self.assertIn("synthetic", _src(cell).lower())

    def test_abide_cases_credit_the_real_data(self):
        case1_intro = _src(next(c for c in self.cells if c.get("id") == "wp57-102-intro"))
        self.assertIn("ABIDE", case1_intro)

    # -- Case 2: y-as-input is the one deliberate mistake -------------------

    def test_case2_contaminated_path_requires_the_held_out_y(self):
        run_it = _src(next(c for c in self.cells if c.get("id") == "wp57-204-run-it"))
        self.assertIn("contaminated_cols = np.column_stack([x1, x2, case2_y])", run_it)
        self.assertIn("needs the held-out y", run_it)
        # PCA/scaler are fit on TRAINING rows only -- the only remaining
        # mistake is that y is one of the columns being transformed.
        self.assertIn("contaminated_scaler.transform(contaminated_cols[case2_train_idx])", run_it)

    def test_case2_honest_path_never_uses_y_as_a_column(self):
        blank_cell = next(c for c in self.cells if "wp57-activity-pca" in c.get("metadata", {}).get("tags", []))
        starter = _src(blank_cell)
        self.assertNotIn("case2_y]", starter)  # never column_stack([..., case2_y])

    def test_case2_widget_mirrors_the_train_only_fit_for_both_paths(self):
        widget = _src(next(c for c in self.cells if c.get("id") == "wp57-212-widget"))
        self.assertIn("cols[_w_train_idx]", widget)
        self.assertNotIn("_W_Y_SCALE", widget)
        self.assertNotIn("fit on ALL rows", widget)

    # -- no disguised/early answer reveal -----------------------------------

    def test_results_labeled_contaminated_or_invalid_only_after_diagnosis(self):
        run_it_case2 = _src(next(c for c in self.cells if c.get("id") == "wp57-204-run-it"))
        self.assertNotIn("INVALID", run_it_case2)
        self.assertNotIn("invalid", run_it_case2)
        consequence_case2 = _src(next(c for c in self.cells if c.get("id") == "wp57-209-case2-check"))
        self.assertIn("INVALID", consequence_case2)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_editable_written_answer_cell_exists(self):
        answer_cells = [
            c
            for c in self.cells
            if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE)
        ]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp57", "wp-", "scripts/generate", "wp38"):
            self.assertNotIn(needle, low_md)


class StructuralSynchronization(unittest.TestCase):
    """Template, portable copy, and reference stay in sync."""

    @classmethod
    def setUpClass(cls):
        cls.lite_nb, cls.lite_cells = _load(LITE_PATH)
        cls.portable_nb, cls.portable_cells = _load(PORTABLE_PATH)
        cls.lite_copy_nb, cls.lite_copy_cells = _load(LITE_PORTABLE_COPY_PATH)
        cls.reference_nb, cls.reference_cells = _load(REFERENCE_PATH)

    def test_lite_and_portable_are_identical(self):
        self.assertEqual(len(self.lite_cells), len(self.portable_cells))
        for a, b in zip(self.lite_cells, self.portable_cells):
            self.assertEqual(_src(a), _src(b))
            self.assertEqual(a["id"], b["id"])

    def test_lite_and_its_served_portable_copy_are_identical(self):
        self.assertEqual(len(self.lite_cells), len(self.lite_copy_cells))
        for a, b in zip(self.lite_cells, self.lite_copy_cells):
            self.assertEqual(_src(a), _src(b))

    def test_reference_has_the_same_cell_ids_and_non_blank_cells_match(self):
        self.assertEqual(len(self.lite_cells), len(self.reference_cells))
        for a, b in zip(self.lite_cells, self.reference_cells):
            self.assertEqual(a["id"], b["id"])
            tags = set(a.get("metadata", {}).get("tags", []))
            if tags & BLANK_TAGS:
                continue  # the one place student/reference content differs by design
            self.assertEqual(_src(a), _src(b), a["id"])

    def test_reference_has_no_your_code_here_placeholders(self):
        text = "\n\n".join(_src(c) for c in self.reference_cells)
        self.assertNotIn("YOUR CODE HERE", text)


if __name__ == "__main__":
    unittest.main()
