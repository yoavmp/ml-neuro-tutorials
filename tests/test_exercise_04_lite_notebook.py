"""Offline structural tests for the migrated Exercise 4 JupyterLite notebook.

WP45, modeled on tests/test_exercise_03_lite_notebook.py: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, required editable answer
cells exist, checked questions have keyed answers, no install cell, and the
student template, its portable copy, and the completed reference notebook
stay structurally synchronized by construction
(scripts/generate_exercise_04_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_04_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_04.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_04_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp45-activity-cv",
    "wp45-activity-nested-cv",
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

        import generate_exercise_04_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_04_notebook.py", "--check"]
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
        self.assertEqual(
            _src(self.cells[2]).splitlines()[0],
            "# Exercise 4: Validation and Cross-Validation",
        )

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp45-103-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    # -- terminology: regression MSE, never a classification metric --------

    def test_target_is_continuous_age_not_a_classification_label(self):
        self.assertIn("continuous measurement", self.md)
        self.assertIn("mean squared error", self.md.lower())
        self.assertNotIn("LogisticRegression", self.code)
        self.assertNotIn("confusion matrix", self.md.lower())
        self.assertNotIn("accuracy_score", self.code)

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

    def test_cv_blank_is_not_pre_populated_with_the_solution(self):
        cv_cell = next(c for c in self.cells if "wp45-activity-cv" in c.get("metadata", {}).get("tags", []))
        source = _src(cv_cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn("cross_validate(", source)

    def test_nested_cv_blank_does_not_give_the_full_solution(self):
        nested_cell = next(c for c in self.cells if "wp45-activity-nested-cv" in c.get("metadata", {}).get("tags", []))
        source = _src(nested_cell)
        self.assertIn("YOUR CODE HERE", source)
        self.assertNotIn("GridSearchCV(", source)
        self.assertNotIn("grid.fit(X_tr, y_tr)", source)

    # -- checked questions: visibility (WP48's own new requirement) -------

    QUESTION_IDS = {
        "q-single-split-vs-cv-stability",
        "q-inner-loop-data",
        "q-outer-test-mse-meaning",
    }

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp45-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 3)
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

    def test_threadpoolctl_warning_narrowly_filtered(self):
        # WP48 E.1: same upstream threadpoolctl/Pyodide RuntimeWarning
        # reproduced live for Exercise 2 (see
        # tests/test_exercise_02_lite_notebook.py), filtered consistently
        # here by exact message AND category=RuntimeWarning, never a
        # blanket RuntimeWarning filter.
        self.assertIn("JsProxy\\.as_object_map", self.code)
        self.assertIn("category=RuntimeWarning", self.code)
        self.assertNotIn('warnings.filterwarnings("ignore", category=RuntimeWarning)', self.code)

    def test_question_radio_labels_do_not_clip_wrapped_rows(self):
        # WP48 E.3: a long option that wraps to two lines must not overlap
        # the option below it -- the ipywidgets default fixes each radio
        # label's row height to one line unless explicitly overridden.
        self.assertIn(".widget-radio-box label", self.code)
        self.assertIn("height: auto !important", self.code)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/validation_stability.json", self.code + self.md)
        self.assertNotIn("configs/validation_lock_test.json", self.code + self.md)
        self.assertNotIn("configs/nested_cv_explorer.json", self.code + self.md)

    def test_stability_widget_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp45-403-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("sample size:", source)
        self.assertIn("seed:", source)

    def test_nested_cv_conceptual_diagram_present(self):
        # WP48 E.4: the old raw-HTML/inline-CSS diagram is replaced by a
        # rendered image, embedded as a notebook attachment (never a
        # separate linked file, which would break for a downloaded/Colab
        # copy) with descriptive alt text -- the same nbformat mechanism
        # Exercise 2's Activity 3B reference image already uses.
        diagram = next(c for c in self.cells if c.get("id") == "wp45-503-diagram")
        source = _src(diagram)
        self.assertNotIn("ml-ncv-diagram", source)
        self.assertNotIn("<div", source)
        self.assertIn("attachment:exercise_04_nested_cv_diagram.png", source)
        self.assertIn("![", source)
        self.assertGreater(len(source.strip()), 40)  # real alt text, not a bare image tag
        self.assertIn("attachments", diagram)
        self.assertIn("exercise_04_nested_cv_diagram.png", diagram["attachments"])
        self.assertIn("image/png", diagram["attachments"]["exercise_04_nested_cv_diagram.png"])

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    # -- preserved recipe/values ----------------------------------------

    def test_k_example_fixed_not_tuned_in_sections_2_and_3(self):
        self.assertIn("K_EXAMPLE = 20", self.code)

    def test_established_split_arguments_present(self):
        self.assertIn("test_size=0.25, random_state=42, stratify=groups", self.code)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp45", "wp-", "scripts/generate", "audit script", "audit_result"):
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
