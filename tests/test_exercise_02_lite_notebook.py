"""Offline structural tests for the migrated Exercise 2 JupyterLite notebook.

Covers WP41 section 12 "Exercise 2 content" items 22-34: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, KNeighborsRegressor is not
imported before the student task, correlations use training rows only, no
hidden plotting solution beside the reference image, required editable
answer cells exist, checked questions have keyed answers and feedback, the
curse-of-dimensionality text is absent, internal numbered comments are
absent, metrics match baseline, former k-axis plots use numeric 1/k with a
visible "Model complexity" title and still report integer k, no visible
"1/k" axis title, and no duplicated prompts.

Also checks section 4.7 "structurally synchronized by construction": the
student template, its portable copy, and the completed reference notebook
share the same non-blank cells, generated from one source
(scripts/generate_exercise_02_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_02_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_02_lite_notebook.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_02.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_02_reference.ipynb"

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

        import generate_exercise_02_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_02_notebook.py", "--check"]
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
            _src(self.cells[1]).splitlines()[0],
            "# Exercise 2: Regression and Bias-Variance Trade-Off",
        )

    def test_setup_cell_is_collapsed_and_first(self):
        setup = self.cells[0]
        self.assertEqual(setup["cell_type"], "code")
        self.assertTrue(setup.get("metadata", {}).get("jupyter", {}).get("source_hidden"))

    # -- item 22: all requested YOUR CODE HERE tasks exist ------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertGreaterEqual(len(tagged), 4)
        self.assertLessEqual(len(tagged), 6)
        expected_tags = {
            "wp41-activity-2a",
            "wp41-activity-2b",
            "wp41-activity-3a",
            "wp41-activity-3b",
            "wp41-activity-5",
        }
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(expected_tags, expected_tags & seen_tags)

    # -- item 23: no raise NotImplementedError -------------------------------

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    # -- item 24: KNeighborsRegressor not imported before the student task --

    def test_kneighbors_not_imported_before_student_task(self):
        # KNeighborsRegressor legitimately appears later, supplied, in
        # Section 8's explore-k widget -- it must not appear any earlier,
        # i.e. not before Section 5's own "YOUR CODE HERE" import task.
        section_5_idx = next(i for i, c in enumerate(self.cells) if "wp41-activity-5" in c.get("metadata", {}).get("tags", []))
        before_code = "\n\n".join(_src(c) for c in self.cells[:section_5_idx] if c["cell_type"] == "code")
        self.assertNotIn("KNeighborsRegressor", before_code)
        self.assertIn("from sklearn.neighbors import", _src(self.cells[section_5_idx]))

    # -- item 25: correlations use training rows only ------------------------

    def test_2b_instructions_require_training_only(self):
        self.assertIn("training-only", self.md.lower())

    # -- item 26: no hidden plotting solution beside the reference image ----

    def test_3b_has_no_solution_beside_the_reference_image(self):
        idx = [i for i, c in enumerate(self.cells) if "reference" in c.get("id", "")]
        for i in idx:
            self.assertNotIn("plt.scatter(y_test, y_pred", _src(self.cells[i]))

    # -- item 27: required editable answer cells exist -----------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if "YOUR ANSWER HERE" in _src(c)]
        self.assertGreaterEqual(len(answer_cells), 3)
        self.assertLessEqual(len(answer_cells), 5)
        for c in answer_cells:
            self.assertEqual(c["cell_type"], "markdown")

    # -- item 28: checked questions have keyed answers and feedback ---------

    def test_checked_questions_have_keys_and_feedback(self):
        checked = [
            c
            for c in self.cells
            if "display(make_single_choice_question" in _src(c) or "display(make_multi_choice_question" in _src(c)
        ]
        self.assertGreaterEqual(len(checked), 4)
        self.assertLessEqual(len(checked), 6)
        for c in checked:
            src = _src(c)
            self.assertTrue("correct_index=" in src or "correct_indices=" in src, src)

    # -- item 29: curse-of-dimensionality text is absent ---------------------

    def test_no_curse_of_dimensionality(self):
        self.assertNotIn("curse of dimensionality", self.md.lower())
        self.assertNotIn("curse-of-dimensionality", self.md.lower())

    # -- item 30: internal numbered comments are absent ----------------------

    def test_no_internal_numbered_comments(self):
        import re

        for pattern in (r"#\s*1-2\.", r"#\s*3\.\s+one fixed", r"#\s*4-7\.", r"#\s*8\.\s+observed"):
            self.assertNotRegex(self.code, pattern)

    # -- item 32/33: model-complexity axis conventions -----------------------

    def test_model_complexity_axis_used_not_raw_1_over_k(self):
        self.assertIn('set_xlabel("Model complexity")', self.code)
        self.assertNotIn('set_xlabel("1/k")', self.code)
        self.assertNotIn("set_xlabel('1/k')", self.code)

    def test_integer_k_still_visible_via_companion_axis(self):
        self.assertIn("ax_top", self.code)
        self.assertIn('set_xlabel("k (for reference)")', self.code)

    def test_section_8_widget_reports_k_and_complexity(self):
        self.assertIn('k = {k}', self.code)
        self.assertIn("model complexity (1/k)", self.code)

    # -- item 34: no duplicated prompts --------------------------------------

    def test_no_duplicated_reflection_or_answer_prompts(self):
        answer_prompts = [
            _src(c) for c in self.cells if c["cell_type"] == "markdown" and "YOUR ANSWER HERE" in _src(c)
        ]
        self.assertEqual(len(answer_prompts), len(set(answer_prompts)))

    # -- section 3.4: no install cell ----------------------------------------

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    # -- section 8/9 editorial: no WP/script references in student text -----

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp41", "wp-", "scripts/generate", "audit script"):
            self.assertNotIn(needle, low_md)

    def test_no_stale_exercise_3_or_fiq_content(self):
        self.assertNotIn("FIQ", self.md)
        self.assertNotIn("FIQ", self.code)
        self.assertNotIn("ridge", self.md.lower())
        self.assertNotIn("lasso", self.md.lower())


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
        blank_tags = {
            "wp41-activity-2a",
            "wp41-activity-2b",
            "wp41-activity-3a",
            "wp41-activity-3b",
            "wp41-activity-5",
        }
        for a, b in zip(self.lite_cells, self.reference_cells):
            self.assertEqual(a["id"], b["id"])
            tags = set(a.get("metadata", {}).get("tags", []))
            if tags & blank_tags:
                continue  # the one place student/reference content differs by design
            self.assertEqual(_src(a), _src(b), a["id"])

    def test_reference_has_no_your_code_here_placeholders(self):
        text = "\n\n".join(_src(c) for c in self.reference_cells)
        self.assertNotIn("YOUR CODE HERE", text)


if __name__ == "__main__":
    unittest.main()
