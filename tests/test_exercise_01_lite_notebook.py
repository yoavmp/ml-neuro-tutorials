"""Offline structural tests for the migrated Exercise 1 JupyterLite notebook.

Mirrors tests/test_exercise_02_lite_notebook.py's shape and coverage for
Exercise 1 (WP42 Gate 2): required YOUR CODE HERE tasks exist, no
`raise NotImplementedError`, editable answer cells exist as bold questions
(no "YOUR ANSWER HERE" placeholder), checked questions have keyed answers,
no Spearman anywhere, the curated 13-column teaching table is preserved, and
the student/portable/reference notebooks stay structurally synchronized by
construction.

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_01_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_01_lite_notebook.py'
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_01.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_01_reference.ipynb"
CURATED_COLUMNS_PATH = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


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

        import generate_exercise_01_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_01_notebook.py", "--check"]
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 1: Exploratory Data Analysis")

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp42-103-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("Run this notebook's", source)

    def test_curated_table_matches_the_column_authority(self):
        curated = json.loads(CURATED_COLUMNS_PATH.read_text())
        self.assertIn("_CURATED_COLUMNS = [", self.code)
        for col in curated:
            self.assertIn(repr(col), self.code)

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertGreaterEqual(len(tagged), 4)
        self.assertLessEqual(len(tagged), 6)
        expected_tags = {
            "wp42-activity-tail-sample",
            "wp42-activity-missing-summary",
            "wp42-activity-drop-incomplete",
            "wp42-activity-fill-median",
        }
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(expected_tags, expected_tags & seen_tags)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    # -- editable answer cells: bold question, no placeholder -----------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())]
        self.assertGreaterEqual(len(answer_cells), 3)
        self.assertLessEqual(len(answer_cells), 5)

    def test_your_answer_here_placeholder_is_gone(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_one_notebook_wide_answer_cell_instruction(self):
        occurrences = self.md.lower().count("double-click")
        self.assertEqual(occurrences, 1)

    def test_no_duplicated_answer_prompts(self):
        answer_prompts = [
            _src(c).strip() for c in self.cells if c["cell_type"] == "markdown" and re.match(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip())
        ]
        self.assertEqual(len(answer_prompts), len(set(answer_prompts)))

    # -- checked questions: visibility (WP48's own new requirement) -------

    QUESTION_IDS = {
        "q-categorical-columns",
        "q-histogram-bins",
        "q-fiq-correlation",
    }

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        # Excludes the hidden setup cell itself (id wp42-000-setup), which
        # defines show_question() and mentions it in its own explanatory
        # comment -- every OTHER, visible cell that calls it is a question.
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp42-000-setup" and 'show_question("' in _src(c)
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

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("wrap-labels", self.code)
        self.assertIn("white-space: normal", self.code)

    def test_pearson_plot_title_is_not_clipped_by_the_colorbar(self):
        # WP48 B.5: the title used to be ax.set_title(...), centered on the
        # Axes the colorbar had already narrowed, clipping the full string
        # at the figure's right edge. fig.suptitle(...) is figure-level, so
        # it has the whole figure's width to render in.
        cell = next(c for c in self.cells if c.get("id") == "wp42-610-correlation-plot")
        source = _src(cell)
        self.assertIn("fig.suptitle(", source)
        self.assertNotIn("ax.set_title(", source)
        self.assertIn("Pearson correlation between numerical variables", source)

    # -- scope constraints (WP42 Gate 2) -------------------------------

    def test_no_spearman(self):
        self.assertNotIn("spearman", self.md.lower())
        self.assertNotIn("spearman", self.code.lower())

    def test_no_seaborn(self):
        # No prebuilt Pyodide wheel; every plot must use plain Matplotlib.
        self.assertNotIn("seaborn", self.code.lower())
        self.assertNotIn("import sns", self.code.lower())
        self.assertNotIn(" sns.", self.code.lower())

    def test_no_outlier_or_range_check_section(self):
        # A passing mention (e.g. "Pearson r is sensitive to outliers") is
        # fine; a dedicated outlier/range-check activity is not.
        headers = [_src(c).lower() for c in self.cells if c["cell_type"] == "markdown" and _src(c).lstrip().startswith("#")]
        for h in headers:
            self.assertNotIn("outlier", h)
            self.assertNotIn("range check", h)
            self.assertNotIn("range-check", h)

    def test_no_time_budget_language(self):
        for phrase in ("minutes to complete", "time budget", "you have 10 minutes"):
            self.assertNotIn(phrase, self.md.lower())

    def test_matplotlib_deprecation_narrowly_filtered(self):
        self.assertIn("warnings.filterwarnings(", self.code)
        self.assertIn("parameter as float was deprecated", self.code)
        self.assertNotIn('warnings.filterwarnings("ignore")', self.code)

    # -- retention explorer rebuilt notebook-native -----------------------

    def test_heatmap_does_not_depend_on_the_student_missingness_blank(self):
        # A supplied cell must not reference a variable only a completed
        # student blank would define, or a still-blank activity cascades
        # into unrelated later cells failing (confirmed live: this exact bug
        # broke every cell after the heatmap on a fresh "Run All Cells").
        heatmap_cell = next(c for c in self.cells if c.get("id") == "wp42-406-heatmap")
        source = _src(heatmap_cell)
        self.assertNotRegex(source, r"missing_summary\s*[.\[]")
        self.assertIn("data.isna()", source)

    def test_retention_explorer_is_notebook_native(self):
        widget_cell = next(c for c in self.cells if c.get("id") == "wp42-409-retention-widget")
        source = _src(widget_cell)
        self.assertIn("_retention_boxes", source)
        self.assertIn(".observe(", source)
        self.assertNotIn("iframe", source.lower())

    def test_histogram_widget_has_typed_numeric_input(self):
        widget_cell = next(c for c in self.cells if c.get("id") == "wp42-604-histogram-widget")
        source = _src(widget_cell)
        self.assertIn("BoundedIntText", source)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp42", "wp41", "wp-", "scripts/generate", "audit script"):
            self.assertNotIn(needle, low_md)


class StructuralSynchronization(unittest.TestCase):
    """Template, portable copy, and reference stay in sync."""

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
        blank_tags = {
            "wp42-activity-tail-sample",
            "wp42-activity-missing-summary",
            "wp42-activity-drop-incomplete",
            "wp42-activity-fill-median",
        }
        for a, b in zip(self.lite_cells, self.reference_cells):
            self.assertEqual(a["id"], b["id"])
            tags = set(a.get("metadata", {}).get("tags", []))
            if tags & blank_tags:
                continue
            self.assertEqual(_src(a), _src(b), a["id"])

    def test_reference_has_no_your_code_here_placeholders(self):
        text = "\n\n".join(_src(c) for c in self.reference_cells)
        self.assertNotIn("YOUR CODE HERE", text)


if __name__ == "__main__":
    unittest.main()
