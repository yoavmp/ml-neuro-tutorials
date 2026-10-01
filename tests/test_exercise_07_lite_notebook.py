"""Offline structural tests for the migrated Exercise 7 JupyterLite notebook.

WP46, modeled on tests/test_exercise_06_lite_notebook.py: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, required editable answer
cells exist, checked questions have keyed answers, no install cell, no
iframe/legacy-widget-config reference, and the student template, its
portable copy, and the completed reference notebook stay structurally
synchronized by construction (scripts/generate_exercise_07_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_07_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_07_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_07.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_07" / "exercise_07_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_07_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp46-activity-sweep",
    "wp46-activity-pipeline",
    "wp46-activity-bars",
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

        import generate_exercise_07_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_07_notebook.py", "--check"]
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 7: Boosting and Gradient Boosting")

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp46-104-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_data_load_prints_established_split_sizes(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp46-104-load")
        source = _src(load_cell)
        self.assertIn('test_size=0.25, random_state=42, stratify=groups', source)
        self.assertIn('test_size=0.25, random_state=7, stratify=groups_train', source)

    # -- scope exclusions -------------------------------------------------

    def test_no_adaboost_or_classification_boosting(self):
        low_code = self.code.lower()
        for needle in ("adaboost", "gradientboostingclassifier"):
            self.assertNotIn(needle, low_code)

    def test_xgboost_is_prose_only_never_executed(self):
        self.assertIn("XGBRegressor", self.md)
        self.assertNotIn("import xgboost", self.code)
        self.assertNotIn("XGBRegressor", self.code)
        self.assertIn("does not install, import, or execute `xgboost`", self.md)

    def test_no_feature_scaling_for_trees(self):
        self.assertNotIn("StandardScaler", self.code)

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 3)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_sweep_blank_is_not_pre_populated_with_the_solution(self):
        cell = next(c for c in self.cells if "wp46-activity-sweep" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn('boosting_sweep_results.append({"n_estimators"', source)

    def test_pipeline_blank_is_not_pre_populated_with_the_solution(self):
        cell = next(c for c in self.cells if "wp46-activity-pipeline" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("YOUR CODE HERE", source)
        # The hint comments show the shape of the solution, but every line
        # is commented out -- nothing here is executable as-is.
        for line in source.splitlines():
            if "boosting_search.fit(X_train, y_train)" in line:
                self.assertTrue(line.strip().startswith("#"), line)

    def test_bars_blank_is_not_pre_populated_with_the_solution(self):
        cell = next(c for c in self.cells if "wp46-activity-bars" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn('ax.bar(labels_a', source)

    def test_required_output_names_appear_in_instructions(self):
        sweep_instructions = next(c for c in self.cells if c.get("id") == "wp46-403-instructions")
        for name in ("boosting_sweep_results", "boosting_sweep_fig"):
            self.assertIn(name, _src(sweep_instructions))

        pipeline_instructions = next(c for c in self.cells if c.get("id") == "wp46-603-instructions")
        for name in ("boosting_search", "boosting_best_model", "boosting_test_mse", "boosting_test_r2"):
            self.assertIn(name, _src(pipeline_instructions))

        bar_instructions = next(c for c in self.cells if c.get("id") == "wp46-609-bar-instructions")
        for name in ("boosting_bar_fig_a", "boosting_bar_fig_b"):
            self.assertIn(name, _src(bar_instructions))

    def test_reduced_grid_is_12_candidates_not_27(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-604-blank")
        source = _src(cell)
        self.assertIn("lr_n_estimators_pairs = [(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]", source)
        self.assertIn("max_depth_grid = [1, 2, 3]", source)
        self.assertIn("27-candidate", self.md)
        self.assertIn("12-candidate", self.md)

    def test_no_author_facing_language_in_pipeline_section(self):
        low_md = self.md.lower()
        for needle in ("predeclared", "audited on the target machine", "target machine", "wp report", "audit script"):
            self.assertNotIn(needle, low_md)

    # -- checked questions --------------------------------------------------

    def test_checked_questions_have_keys_and_feedback(self):
        checked = [
            c
            for c in self.cells
            if "display(make_single_choice_question" in _src(c) or "display(make_multi_choice_question" in _src(c)
        ]
        self.assertEqual(len(checked), 3)
        for c in checked:
            src = _src(c)
            self.assertTrue("correct_index=" in src or "correct_indices=" in src, src)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/boosting_step_by_step.json", self.code + self.md)
        self.assertNotIn("configs/boosting_parameter_explorer.json", self.code + self.md)

    def test_step_by_step_activity_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-204-step-widget")
        source = _src(cell)
        self.assertIn("Previous Step", source)
        self.assertIn("Next Step", source)
        self.assertIn("IntSlider", source)

    def test_parameter_explorer_activity_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-407-explorer-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("SelectionSlider", source)
        self.assertIn("staged_predict", source)

    def test_parameter_explorer_never_touches_the_locked_test_set(self):
        cell = next(c for c in self.cells if c.get("id") == "wp46-407-explorer-widget")
        source = _src(cell)
        self.assertNotIn("X_test", source)
        self.assertNotIn("y_test", source)
        intro = next(c for c in self.cells if c.get("id") == "wp46-406-activity2-intro")
        self.assertIn("never part of this activity", _src(intro))

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE)]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    # -- preserved recipe/values ----------------------------------------

    def test_sklearn_example_settings_match_established_recipe(self):
        self.assertIn("'n_estimators': 100, 'learning_rate': 0.05, 'max_depth': 2, 'random_state': 42", self.code)

    def test_fair_comparison_reuses_exercise_6_settings(self):
        self.assertIn("'max_depth': 6", self.code)
        self.assertIn("'min_samples_leaf': 5", self.code)
        self.assertIn("max_features=fair_max_features", self.code)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp46", "wp-", "scripts/generate", "audit_result"):
            self.assertNotIn(needle, low_md)


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
