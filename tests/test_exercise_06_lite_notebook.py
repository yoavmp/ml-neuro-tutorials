"""Offline structural tests for the migrated Exercise 6 JupyterLite notebook.

WP46, modeled on tests/test_exercise_05_lite_notebook.py: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, required editable answer
cells exist, checked questions have keyed answers, no install cell, no
iframe/legacy-widget-config reference, and the student template, its
portable copy, and the completed reference notebook stay structurally
synchronized by construction (scripts/generate_exercise_06_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_06_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_06_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_06.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_06" / "exercise_06_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_06_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp46-activity-depth",
    "wp46-activity-comparison",
}


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

        import generate_exercise_06_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_06_notebook.py", "--check"]
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 6: Decision Trees")

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp46-103-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    # -- SMALL_TREE_FEATURES rename (WP46 section: rename TREE_FEATURES) ----

    def test_small_tree_features_renamed_consistently(self):
        self.assertIn('SMALL_TREE_FEATURES = [\'fsCT_L_3a_ROI\', \'fsCT_R_2_ROI\']', self.code)
        self.assertNotIn("TREE_FEATURES = [", self.code.replace("SMALL_TREE_FEATURES", ""))
        self.assertNotRegex(self.code, r"(?<!SMALL_)\bTREE_FEATURES\b")

    def test_no_feature_scaling_for_trees(self):
        self.assertIn("does **not** require feature scaling", self.md)
        self.assertNotIn("StandardScaler", self.code)

    def test_single_tree_settings_and_output(self):
        self.assertIn("'max_depth': 3", self.code)
        self.assertIn("'min_samples_leaf': 20", self.code)
        self.assertIn("leaves = {small_tree.get_n_leaves()}", self.code)

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 2)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_depth_blank_is_not_pre_populated_with_the_solution(self):
        cell = next(c for c in self.cells if "wp46-activity-depth" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn("ax.plot(MAX_DEPTHS, tree_depth_train_mse", source)

    def test_comparison_blank_is_not_pre_populated_with_the_solution(self):
        cell = next(c for c in self.cells if "wp46-activity-comparison" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn("for train_idx, val_idx in cv.split(X):\n    X_tr", source)

    def test_required_output_names_appear_in_instructions(self):
        depth_instructions = next(c for c in self.cells if c.get("id") == "wp46-304-instructions")
        for name in ("tree_depth_train_mse", "tree_depth_val_mse", "tree_depth_fig"):
            self.assertIn(name, _src(depth_instructions))

        comparison_instructions = next(c for c in self.cells if c.get("id") == "wp46-602-instructions")
        self.assertIn("tree_cv_fold_results", _src(comparison_instructions))
        self.assertIn("tree_cv_summary", _src(comparison_instructions))

    # -- checked questions: visibility (WP48's own new requirement) -------

    QUESTION_IDS = {
        "q-greedy-splitting",
        "q-depth-selection",
        "q-bagging-forest-variance",
        "q-bagging-reduces-variance",
    }

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp46-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 4)
        for c in checked:
            src = _src(c)
            self.assertNotIn("correct_index", src)
            self.assertNotIn("correct_indices", src)
            self.assertTrue(any(f'show_question("{qid}")' in src for qid in self.QUESTION_IDS), src)

    def test_hidden_setup_cell_carries_every_question_definition(self):
        setup = self.cells[1]
        source = _src(setup)
        self.assertIn("_QUESTIONS = {", source)
        for qid in self.QUESTION_IDS:
            self.assertIn(f'"{qid}"', source)
        self.assertIn("def show_question(question_id):", source)

    def test_every_question_declares_a_shuffle_seed(self):
        # WP53 course-wide review item 2: the shuffle mechanism itself
        # lives in the hidden setup cell; see
        # tests/test_exercise_06_reference_execution.py for the executed
        # proof that shuffling is reproducible and varies positions across
        # questions.
        setup_source = _src(self.cells[1])
        for qid in self.QUESTION_IDS:
            block_match = re.search(rf'"{re.escape(qid)}":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
            self.assertIsNotNone(block_match, qid)
            self.assertIn("shuffle_seed=", block_match.group(1), qid)

    def test_question_radio_labels_do_not_clip_wrapped_rows(self):
        # WP49: applying WP48 E.3's fix (originally Exercise-4-only) to the
        # identical duplicated CSS block here too -- a long option that wraps
        # to two lines must not overlap the option below it, since the
        # ipywidgets default fixes each radio label's row height to one line
        # unless explicitly overridden.
        self.assertIn(".widget-radio-box label", self.code)
        self.assertIn("height: auto !important", self.code)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    def test_depth_selection_question_correct_answer_is_validation_mse(self):
        # The question content moved into the hidden setup cell's
        # _QUESTIONS dict (WP48); check it there instead of in the visible
        # cell, which now only calls show_question("q-depth-selection").
        checked_cell = next(c for c in self.cells if c.get("id") == "wp46-307-checked")
        self.assertEqual(_src(checked_cell).strip(), 'show_question("q-depth-selection")')
        setup_source = _src(self.cells[1])
        match = re.search(r'"q-depth-selection": dict\((.*?)\n    \),', setup_source, re.DOTALL)
        self.assertIsNotNone(match)
        q_block = match.group(1)
        self.assertIn("correct_index=0", q_block)
        self.assertIn("The depth that minimizes validation MSE.", q_block)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/tree_greedy_split.json", self.code + self.md)
        self.assertNotIn("configs/tree_ensemble_compare.json", self.code + self.md)

    def test_greedy_activity_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-204-greedy-widget")
        source = _src(cell)
        for name in ("Lock My Answer", "Reveal Best Split", "Continue to Next Node", "Reset Tree"):
            self.assertIn(name, source)

    def test_ensemble_activity_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-503-ensemble-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("Number of trees:", source)

    def test_number_of_trees_label_is_not_clipped(self):
        # WP53: ipywidgets' default Dropdown description width truncated
        # "Number of trees:" live -- description_width=initial plus a
        # scoped CSS backstop (verified pattern from Exercise 9) fixes it.
        cell = next(c for c in self.cells if c.get("id") == "wp46-503-ensemble-widget")
        source = _src(cell)
        self.assertIn('style={"description_width": "initial"}', source)
        self.assertIn("ens-ntrees-row", source)
        self.assertIn("white-space: normal !important", source)

    def test_regression_tree_diagram_uses_a_larger_higher_resolution_figure(self):
        # WP53: plot_tree's default fontsize auto-shrinks to fit a small
        # figsize=(9, 5) canvas -- unreadable even before any CSS display
        # width is applied. A larger, higher-DPI figure with an explicit
        # fontsize fixes the actual rendered pixels.
        self.assertIn("figsize=(15, 9), dpi=140", self.code)
        self.assertIn("fontsize=12", self.code)

    def test_think_first_replaced_with_think(self):
        self.assertNotIn("Think first:", self.code + self.md)
        self.assertIn("**Think:**", self.code + self.md)

    def test_greedy_legend_only_requested_when_labels_exist(self):
        # WP53: ax.legend() used to be called unconditionally, even before
        # any labeled artist existed (before "Lock My Answer"), emitting
        # "No artists with labels found to put in legend".
        self.assertIn("ax.get_legend_handles_labels()[0]", self.code)

    def test_greedy_widget_redraws_on_every_dropdown_change(self):
        # WP53 item 4: both the feature and threshold dropdowns must
        # redraw immediately -- not only after a button click -- and the
        # left plot must preview the current (not-yet-locked) selection.
        cell = next(c for c in self.cells if c.get("id") == "wp46-204-greedy-widget")
        source = _src(cell)
        self.assertIn("_greedy_feature_dd.observe(_greedy_render, names=\"value\")", source)
        self.assertIn("_greedy_threshold_dd.observe(_greedy_render, names=\"value\")", source)
        self.assertIn("current selection", source)

    def test_train_val_wording_used_instead_of_development(self):
        # WP53: "(development data only)" / "development = N" -> "train-val"
        # wording in the classification-depth-contrast cell; the actual
        # counts (753 train-val participants) are unchanged.
        cell = next(c for c in self.cells if c.get("id") == "wp46-310-classification")
        source = _src(cell)
        self.assertIn("train-val data only", source)
        self.assertIn("train-val = {len(dev_pos)}", source)
        self.assertNotIn("development data only", source)
        self.assertNotIn("development =", source)

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())]
        self.assertGreaterEqual(len(answer_cells), 2)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    # -- preserved recipe/values ----------------------------------------

    def test_established_split_arguments_present(self):
        self.assertIn("test_size=0.25, random_state=42, stratify=groups", self.code)

    def test_max_depths_matches_established_recipe(self):
        self.assertIn("MAX_DEPTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", self.code)

    def test_fair_comparison_settings_match_established_recipe(self):
        self.assertIn("KFold(n_splits=5, shuffle=True, random_state=100)", self.code)
        self.assertIn("max_features=19", self.code)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp46", "wp-", "scripts/generate", "audit script", "audit_result"):
            self.assertNotIn(needle, low_md)

    def test_no_boosting_content_leaked_in(self):
        for needle in ("gradientboosting", "adaboost", "learning_rate"):
            self.assertNotIn(needle, self.code.lower())


class StructuralSynchronization(unittest.TestCase):
    """Section 4.7: template, portable copy, and reference stay in sync."""

    @classmethod
    def setUpClass(cls):
        cls.lite_nb, cls.lite_cells = _load(LITE_PATH)
        cls.portable_nb, cls.portable_cells = _load(PORTABLE_PATH)
        cls.reference_nb, cls.reference_cells = _load(REFERENCE_PATH)

    def test_lite_and_portable_are_identical(self):
        self.assertEqual(len(self.lite_cells), len(self.portable_cells))
        for a, b in zip(self.lite_cells, self.portable_cells):
            self.assertEqual(_src(a), _src(b))
            self.assertEqual(a["id"], b["id"])

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
