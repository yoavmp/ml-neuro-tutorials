"""Offline structural tests for the rebuilt Exercise 9 JupyterLite notebook.

WP51, modeled on tests/test_exercise_08_lite_notebook.py: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, required editable answer
cells exist, checked questions have keyed answers IN THE HIDDEN SETUP CELL
ONLY (never in the visible question cell), no install cell, no iframe/
legacy-widget-config reference, the old embedded five-model nested-CV
summary is demoted to a single labeled, non-graded, collapsed historical
reference, and the student template, its portable copy, and the completed
reference notebook stay structurally synchronized by construction
(scripts/generate_exercise_09_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_09_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_09" / "exercise_09_portable.ipynb"
LITE_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp51-activity-pcr",
    "wp51-activity-pls",
    "wp51-activity-svr",
    "wp51-activity-kernelridge",
    "wp51-activity-lasso-optional",
}

REQUIRED_BLANK_TAGS = BLANK_TAGS - {"wp51-activity-lasso-optional"}

QUESTION_IDS = {
    "q-pcr-vs-pls",
    "q-leakage",
    "q-c-gamma-epsilon",
    "q-train-vs-val",
    "q-exact-vs-approx",
    "q-knn-trees",
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

        import generate_exercise_09_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_09_notebook.py", "--check"]
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 9: PCR, PLS, Support Vector Machines, and Kernels")

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp51-103-load-split")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_single_split_defines_required_names(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp51-103-load-split")
        source = _src(load_cell)
        for name in ("X_train", "X_val", "y_train", "y_val", "FEATURES", "X", "y"):
            self.assertIn(name, source)
        # import + the one call, both confined to this cell -- the split
        # is made exactly once and reused throughout, never repeated.
        self.assertEqual(source.count("train_test_split"), 2)
        self.assertEqual(self.code.count("train_test_split"), 2)

    def test_cell_count_is_reasonable(self):
        self.assertLessEqual(len(self.cells), 75)
        self.assertGreaterEqual(len(self.cells), 40)

    def test_no_stored_error_outputs(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error")

    # -- scope exclusions -------------------------------------------------

    def test_no_out_of_scope_methods(self):
        # Random forests/decision trees are mentioned conceptually in
        # Section 5's "no kernel switch" discussion and as a deliberate
        # wrong-answer distractor (q-knn-trees) -- never taught or fit here
        # -- so they are not in this exclusion list.
        low_code = self.code.lower()
        low_md = self.md.lower()
        for needle in (
            "hierarchical clustering",
            "dendrogram",
            "t-sne",
            "tsne",
            "umap",
            "dbscan",
            "gaussian mixture",
            "gaussianmixture",
            "adaboost",
        ):
            self.assertNotIn(needle, low_code, needle)
            self.assertNotIn(needle, low_md, needle)

    def test_nested_cross_validation_appears_only_in_the_labeled_historical_reference(self):
        details_cell = next(c for c in self.cells if "<details>" in _src(c))
        details_src = _src(details_cell).lower()
        self.assertIn("nested", details_src)
        outside = self.md.lower().replace(details_src, "")
        self.assertNotIn("nested cross-validation", outside)
        self.assertNotIn("nested cross-validation", self.code.lower())

    def test_the_old_embedded_summary_is_not_reused_as_this_notebooks_result(self):
        # WP51 "Results and runtime discipline": the old nested-CV numbers
        # must never be copied into this notebook's own conclusions.
        self.assertNotIn("EMBEDDED_SUMMARY", self.code)
        details = next(c for c in self.cells if "<details>" in _src(c))
        src = _src(details)
        self.assertIn("historical", src.lower())
        self.assertIn("not a result of this notebook's own single train/validation", src)
        self.assertNotIn("<details>", self.md.replace(src, ""))  # exactly one such block

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 5)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_required_blanks_are_distinct_from_the_optional_challenge(self):
        tagged_ids = {c.get("id") for c in self.cells for t in c.get("metadata", {}).get("tags", []) if t in REQUIRED_BLANK_TAGS}
        self.assertEqual(len(tagged_ids), 4)
        optional_cell = next(c for c in self.cells if "wp51-activity-lasso-optional" in c.get("metadata", {}).get("tags", []))
        self.assertIn("optional", _src(optional_cell).lower())

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_blanks_are_not_pre_populated_with_the_solution(self):
        # The hint comments show the shape of the solution, but every such
        # line is commented out.
        checks = [
            ("wp51-activity-pcr", "pipe.fit(X_train, y_train)"),
            ("wp51-activity-pls", "PLSRegression(n_components=n, scale=False)"),
            ("wp51-activity-svr", "pipe.fit(X_train_svr_subset, y_train_svr_subset)"),
            ("wp51-activity-kernelridge", 'KernelRidge(kernel="rbf"'),
            ("wp51-activity-lasso-optional", "Lasso(alpha="),
        ]
        for tag, forbidden in checks:
            cell = next(c for c in self.cells if tag in c.get("metadata", {}).get("tags", []))
            source = _src(cell)
            self.assertIn("YOUR CODE HERE", source)
            for line in source.splitlines():
                if forbidden in line:
                    self.assertTrue(line.strip().startswith("#"), line)

    def test_required_output_names_appear_in_instructions(self):
        pcr_instructions = next(c for c in self.cells if c.get("id") == "wp51-203-instructions")
        self.assertIn("pcr_results", _src(pcr_instructions))

        pls_instructions = next(c for c in self.cells if c.get("id") == "wp51-303-instructions")
        self.assertIn("pls_results", _src(pls_instructions))

        svr_instructions = next(c for c in self.cells if c.get("id") == "wp51-410-instructions")
        self.assertIn("svr_results", _src(svr_instructions))

        kr_instructions = next(c for c in self.cells if c.get("id") == "wp51-504-table-and-instructions")
        for name in ("ridge_result", "kernel_ridge_result"):
            self.assertIn(name, _src(kr_instructions))

    # -- checked questions: visibility -------------------------------------

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp51-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 6)
        for c in checked:
            src = _src(c)
            self.assertNotIn("correct_index", src)
            self.assertTrue(any(f'show_question("{qid}")' in src for qid in QUESTION_IDS), src)

    def test_hidden_setup_cell_carries_every_question_definition(self):
        setup = self.cells[1]
        source = _src(setup)
        self.assertIn("_QUESTIONS = {", source)
        for qid in QUESTION_IDS:
            self.assertIn(f'"{qid}"', source)
        self.assertIn("correct_index", source)
        self.assertIn("def show_question(question_id):", source)

    def test_question_radio_labels_do_not_clip_wrapped_rows(self):
        self.assertIn(".widget-radio-box label", self.code)
        self.assertIn("height: auto !important", self.code)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/pcr_pls_explore.json", self.code + self.md)
        self.assertNotIn("configs/svm_explorer.json", self.code + self.md)

    def test_pcr_pls_activity_is_notebook_native_and_synthetic(self):
        cell = next(c for c in self.cells if c.get("id") == "wp51-310-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("_pcrpls_make_data", source)
        self.assertNotIn("abide", source.lower())

    def test_svm_activity_is_notebook_native_and_shows_train_val_distinction(self):
        cell = next(c for c in self.cells if c.get("id") == "wp51-407-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("SVC", source)
        self.assertIn("train_idx", source)
        self.assertIn("val_idx", source)
        self.assertIn('marker="^"', source)  # validation points visually distinct

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE)]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp51", "wp-", "scripts/generate", "audit_result"):
            self.assertNotIn(needle, low_md)

    # -- SVR subset discipline (WP51 "Results and runtime discipline") ----

    def test_svr_subset_is_documented_as_not_equal_to_full_dataset(self):
        instructions = next(c for c in self.cells if c.get("id") == "wp51-410-instructions")
        src = _src(instructions)
        self.assertIn("subset", src.lower())
        self.assertIn("not full-dataset scores", src)


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
