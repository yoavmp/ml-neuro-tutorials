"""Offline structural tests for the migrated Exercise 3 JupyterLite notebook.

WP44 Gate B, modeled on tests/test_exercise_02_lite_notebook.py: required
YOUR CODE HERE tasks exist, no raise NotImplementedError, no diagnosis-label
leakage before the student builds y, required editable answer cells exist,
checked questions have keyed answers, no install cell, and the student
template, its portable copy, and the completed reference notebook stay
structurally synchronized by construction
(scripts/generate_exercise_03_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_03_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_03_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_03.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_03_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp44-activity-features",
    "wp44-activity-xy",
    "wp44-activity-split",
    "wp44-activity-metrics",
    "wp44-activity-roc",
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

        import generate_exercise_03_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_03_notebook.py", "--check"]
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
            "# Exercise 3: Classification and Metrics",
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
        load_cell = next(c for c in self.cells if c.get("id") == "wp44-102-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_model_fit_cell_is_guarded_against_unfinished_prerequisites(self):
        fit_cell = next(c for c in self.cells if c.get("id") == "wp44-342-fit")
        source = _src(fit_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertGreaterEqual(len(tagged), 4)
        self.assertLessEqual(len(tagged), 6)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    # -- diagnosis-label mapping is explicit, not inferred ----------------

    def test_group_codes_are_verified_before_mapping(self):
        cell = next(c for c in self.cells if c.get("id") == "wp44-104-labels")
        source = _src(cell)
        self.assertIn("observed_codes = sorted(df[\"group\"].unique())", source)
        self.assertIn("assert observed_codes == [1, 2]", source)
        self.assertIn("0 = control, 1 = autism", self.md + source)

    def test_y_is_not_defined_before_the_students_own_xy_activity(self):
        # Section 1 only verifies/displays labels; it must not pre-build the
        # `y` variable Section 3's own "YOUR CODE HERE" activity defines.
        xy_idx = next(i for i, c in enumerate(self.cells) if "wp44-activity-xy" in c.get("metadata", {}).get("tags", []))
        before_code = "\n\n".join(_src(c) for c in self.cells[:xy_idx] if c["cell_type"] == "code")
        self.assertNotIn('y = (df["group"]', before_code)

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())]
        self.assertGreaterEqual(len(answer_cells), 3)
        self.assertLessEqual(len(answer_cells), 5)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_no_duplicated_answer_prompts(self):
        answer_prompts = [
            _src(c).strip()
            for c in self.cells
            if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())
        ]
        self.assertEqual(len(answer_prompts), len(set(answer_prompts)))

    # -- checked questions: visibility (WP48's own new requirement) -------

    QUESTION_IDS = {
        "q-probability-near-threshold",
        "q-threshold-tradeoff",
        "q-roc-needs-proba",
        "q-threshold-false-negatives",
        "q-accuracy-under-imbalance",
    }

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp44-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 5)
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

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/classification_threshold.json", self.code + self.md)
        self.assertNotIn("configs/classification_imbalance.json", self.code + self.md)

    def test_threshold_widget_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp44-503-widget")
        source = _src(cell)
        self.assertIn("widgets.FloatSlider", source)
        self.assertIn("widgets.BoundedFloatText", source)
        self.assertIn("threshold = 0.50", source)

    def test_imbalance_widget_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp44-603-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn('class_ratio = "90:10"', source)
        self.assertIn("cohort: {len(y_cohort)} participants", source)

    # -- preserved recipe/values ----------------------------------------

    def test_c_example_fixed_not_tuned(self):
        self.assertIn("C_EXAMPLE = 1.0", self.code)
        self.assertNotIn("GridSearchCV", self.code)
        self.assertNotIn("StratifiedKFold", self.code)
        self.assertNotIn("cross_val", self.code.lower())

    def test_established_split_arguments_present(self):
        self.assertIn("test_size=0.25, random_state=42, stratify=y", self.code)

    def test_established_auc_referenced_in_its_check(self):
        # The accuracy/sensitivity/specificity numeric autocheck cell was
        # replaced by a qualitative reflection (WP48, D.3); the AUC check
        # (untouched) still embeds its own established value.
        self.assertIn("0.569221", self.code)

    # -- SEX/SITE metadata distractors and the explicit group recode ------

    def test_sex_and_site_loaded_as_metadata_distractors(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp44-102-load")
        intro_cell = next(c for c in self.cells if c.get("id") == "wp44-103-labels-intro")
        self.assertIn("SEX", _src(load_cell) + _src(intro_cell))
        self.assertIn("SITE", _src(load_cell) + _src(intro_cell))
        self.assertIn("distractor", _src(intro_cell).lower())

    def test_group_is_explicitly_recoded_to_binary_before_xy_activity(self):
        cell = next(c for c in self.cells if c.get("id") == "wp44-104-labels")
        source = _src(cell)
        self.assertIn('df["group"] = df["group"].map(', source)
        self.assertIn("assert set(df[\"group\"].unique()) == {0, 1}", source)
        xy_idx = next(i for i, c in enumerate(self.cells) if "wp44-activity-xy" in c.get("metadata", {}).get("tags", []))
        labels_idx = next(i for i, c in enumerate(self.cells) if c.get("id") == "wp44-104-labels")
        self.assertLess(labels_idx, xy_idx)

    def test_confusion_matrix_reflection_replaces_the_numeric_autocheck(self):
        cell = next(c for c in self.cells if c.get("id") == "wp44-414-reflection")
        self.assertEqual(cell["cell_type"], "markdown")
        source = _src(cell).lower()
        self.assertIn("plausible", source)
        self.assertNotIn("linear regression", source)
        self.assertIn("not", source)
        self.assertIn("necessarily generalize better", source)
        self.assertIn('y = df["sex"]', source)
        self.assertIn("unsafe", source)
        self.assertNotIn("wp44-414-check", self.code)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp44", "wp-", "scripts/generate", "audit script", "audit_result"):
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
