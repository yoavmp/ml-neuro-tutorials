"""Offline structural tests for the corrected Exercise 9 JupyterLite notebook.

WP52, modeled on tests/test_exercise_08_lite_notebook.py and the WP51
version of this file it replaces: required YOUR CODE HERE tasks exist with
no disguised solutions, checked questions (including the "mark all correct"
multiselect) have keyed answers IN THE HIDDEN SETUP CELL ONLY, correct
answers are reproducibly shuffled rather than always listed first, no
install cell, no iframe/legacy-widget-config reference, the removed
sections (compact SVC demo, Lasso/RBFSampler, KNN/trees, the old historical
nested-CV reference) stay removed, and the student template, its portable
copy, and the completed reference notebook stay structurally synchronized
by construction (scripts/generate_exercise_09_notebook.py).

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
}

SINGLE_CHOICE_QUESTION_IDS = {
    "q-pcr-vs-pls",
    "q-leakage",
    "q-train-vs-val",
    "q-exact-vs-approx",
}
MULTI_CHOICE_QUESTION_IDS = {"q-c-gamma-epsilon"}
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 9: Advanced Models")

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
        self.assertLessEqual(len(self.cells), 60)
        self.assertGreaterEqual(len(self.cells), 35)

    def test_no_stored_error_outputs(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error")

    # -- scope exclusions (WP52 items 7, 10, 15) --------------------------

    def test_no_out_of_scope_methods(self):
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
            # WP52 item 10: Lasso/RBFSampler/KNN/trees material cut from
            # Section 5 entirely, not just trimmed.
            "rbfsampler",
            "lasso",
            "kneighbors",
            "random forest",
            "decision tree",
        ):
            self.assertNotIn(needle, low_code, needle)
            self.assertNotIn(needle, low_md, needle)

    def test_no_compact_svc_demo_section(self):
        # WP52 item 7: removed entirely -- the interactive SVM activity
        # supplies that visualization instead.
        self.assertNotIn("A compact SVC example", self.md)
        self.assertNotIn("boundary, margin, and support vectors", self.md.lower())

    def test_no_historical_reference_section(self):
        # WP52 item 15: the collapsed historical nested-CV reference is
        # removed entirely, not just relabeled.
        self.assertNotIn("<details>", self.md)
        self.assertNotIn("historical", self.md.lower())
        self.assertNotIn("nested", (self.md + self.code).lower())

    def test_no_kernel_application_table_or_removed_subsections(self):
        # WP52 item 10: the multi-model kernel table and everything from
        # "Lasso and logistic regression" onward within Section 5 is gone.
        self.assertNotIn("Lasso and logistic regression", self.md)
        self.assertNotIn("Optional challenge", self.md)
        self.assertNotIn("KNN's distance weighting", self.md)
        self.assertNotIn("Trees and forests", self.md)

    # -- YOUR CODE HERE tasks (WP52 items 2, 9, 11) -----------------------

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
        # WP52 items 2/9/11: unlike WP51's version of this notebook, these
        # blanks must not even contain a commented-out loop/pipeline/fit/
        # predict/score solution -- only genuine hints and an optional
        # dummy-shaped example.
        forbidden = (".fit(", "Pipeline([", ".predict(", "mean_squared_error(y_val", "r2_score(y_val")
        for tag in BLANK_TAGS:
            cell = next(c for c in self.cells if tag in c.get("metadata", {}).get("tags", []))
            source = _src(cell)
            self.assertIn("YOUR CODE HERE", source)
            for needle in forbidden:
                self.assertNotIn(needle, source, f"{tag} contains a solution fragment: {needle!r}")

    def test_pcr_blank_has_exact_starter_shape(self):
        # WP52 item 2, verbatim requirement.
        cell = next(c for c in self.cells if "wp51-activity-pcr" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("PCR_COMPONENT_GRID = [2, 5, 10, 20, 50]", source)
        self.assertIn("pcr_results = []", source)

    def test_svr_blank_mentions_gridsearchcv_as_a_comment_only(self):
        # WP52 item 9: a comment about GridSearchCV outside the browser is
        # fine; it must not become the complete solution.
        cell = next(c for c in self.cells if "wp51-activity-svr" in c.get("metadata", {}).get("tags", []))
        source = _src(cell)
        self.assertIn("GridSearchCV", source)
        for line in source.splitlines():
            if "GridSearchCV" in line:
                self.assertTrue(line.strip().startswith("#"), line)
        self.assertNotIn("GridSearchCV(", source)

    def test_required_output_names_appear_in_instructions(self):
        pcr_instructions = next(c for c in self.cells if c.get("id") == "wp51-203-instructions")
        self.assertIn("pcr_results", _src(pcr_instructions))

        pls_instructions = next(c for c in self.cells if c.get("id") == "wp51-303-instructions")
        self.assertIn("pls_results", _src(pls_instructions))

        svr_instructions = next(c for c in self.cells if c.get("id") == "wp51-410-instructions")
        self.assertIn("svr_results", _src(svr_instructions))

        kr_instructions = next(c for c in self.cells if c.get("id") == "wp51-504-ridge-kernelridge-instructions")
        for name in ("ridge_result", "kernel_ridge_result"):
            self.assertIn(name, _src(kr_instructions))
        self.assertNotIn("| Model | Kernel relationship |", _src(kr_instructions))

    def test_pcr_and_pls_schemas_include_r2(self):
        # WP52 item 13: PCR/PLS rows need val_r2, not just val_mse.
        pcr_instructions = next(c for c in self.cells if c.get("id") == "wp51-203-instructions")
        self.assertIn("val_r2", _src(pcr_instructions))
        pls_instructions = next(c for c in self.cells if c.get("id") == "wp51-303-instructions")
        self.assertIn("val_r2", _src(pls_instructions))

    # -- checked questions: visibility and shuffle (WP52 items 5, 6) ------

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp51-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 5)
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

    def test_svm_question_is_multiselect_with_separate_c_gamma_epsilon_statements(self):
        # WP52 item 5.
        setup_source = _src(self.cells[1])
        match = re.search(r'"q-c-gamma-epsilon":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
        self.assertIsNotNone(match)
        block = match.group(1)
        self.assertIn('type="multi"', block)
        self.assertIn("statements=", block)
        self.assertIn("correct_indices=", block)
        n_true = block.count("true")
        # At least two statements mention each of C, gamma, and epsilon.
        for needle in ("C ", "gamma", "epsilon"):
            self.assertGreaterEqual(block.lower().count(needle.lower()), 2, needle)

    def test_question_radio_labels_do_not_clip_wrapped_rows(self):
        self.assertIn(".widget-radio-box label", self.code)
        self.assertIn("height: auto !important", self.code)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    def test_multiselect_question_uses_checkboxes_with_sensible_partial_feedback(self):
        self.assertIn("make_multi_choice_question", self.code)
        self.assertIn("widgets.Checkbox", self.code)
        # Sensible feedback for a partial selection -- never reveals which
        # specific statements were right or wrong.
        self.assertIn("true statements selected", self.code)

    def test_every_question_declares_a_shuffle_seed_and_type(self):
        # WP52 item 6: the mechanism itself lives in the hidden setup cell;
        # see tests/test_exercise_09_reference_execution.py for the
        # executed proof that shuffling is reproducible and varies
        # positions across questions.
        setup_source = _src(self.cells[1])
        for qid in QUESTION_IDS:
            block_match = re.search(rf'"{re.escape(qid)}":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
            self.assertIsNotNone(block_match, qid)
            self.assertIn("shuffle_seed=", block_match.group(1), qid)

    # -- notebook-native widgets (no iframes), label legibility (items 3,8)

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

    def test_pcr_pls_widget_recolors_by_target_and_fixes_mse_ylim(self):
        # WP52 item 4.
        cell = next(c for c in self.cells if c.get("id") == "wp51-310-widget")
        source = _src(cell)
        self.assertIn("c=y2[train_idx]", source)  # recolored by the generated target
        self.assertIn("signal_dir", source)  # rotating true-signal arrow
        self.assertIn("pls_dir", source)  # PLS's own learned direction
        self.assertIn("set_ylim(0, _PCRPLS_MSE_YLIM)", source)
        self.assertIn("_pcrpls_global_max_mse", source)  # computed from the global max

    def test_svm_activity_is_notebook_native_and_shows_train_val_distinction(self):
        cell = next(c for c in self.cells if c.get("id") == "wp51-407-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("SVC", source)
        self.assertIn("train_idx", source)
        self.assertIn("val_idx", source)
        self.assertIn('marker="^"', source)  # validation points visually distinct
        self.assertIn("make_svc_dataset", source)  # relocated here after item 7's cut

    def test_widget_controls_use_the_label_overflow_fix(self):
        # WP52 items 3/8: description_width + the wrapping CSS backstop,
        # applied to every Dropdown-based activity.
        self.assertIn('style={"description_width": "initial"}', self.code)
        self.assertIn("widget-controls-row", self.code)
        self.assertIn("controls_row(", self.code)

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE)]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp51", "wp52", "wp-", "scripts/generate", "audit_result"):
            self.assertNotIn(needle, low_md)

    # -- SVR subset discipline and the full-data benchmark (WP52 item 13) --

    def test_svr_subset_is_documented_as_not_equal_to_full_dataset(self):
        instructions = next(c for c in self.cells if c.get("id") == "wp51-410-instructions")
        src = _src(instructions)
        self.assertIn("subset", src.lower())
        self.assertIn("not full-dataset scores", src)

    def test_section_6_uses_a_labeled_instructor_benchmark_not_the_student_subset(self):
        compare_intro = _src(next(c for c in self.cells if c.get("id") == "wp51-602-compare-intro"))
        compare_code = _src(next(c for c in self.cells if c.get("id") == "wp51-603-compare"))
        self.assertIn("instructor", compare_intro.lower())
        self.assertIn("SVR_BENCHMARK", compare_code)
        self.assertIn("not ranked", compare_code.lower())
        self.assertIn("exploratory", compare_intro.lower())

    def test_comparison_includes_r2_for_every_full_data_model(self):
        compare_code = _src(next(c for c in self.cells if c.get("id") == "wp51-603-compare"))
        self.assertIn('"val_r2"', compare_code)

    def test_no_matplotlib_xticklabels_warning_pattern(self):
        # WP52 item 14: explicit set_xticks before set_xticklabels.
        compare_code = _src(next(c for c in self.cells if c.get("id") == "wp51-603-compare"))
        self.assertIn("set_xticks(", compare_code)
        xticks_index = compare_code.index("set_xticks(")
        xticklabels_index = compare_code.index("set_xticklabels(")
        self.assertLess(xticks_index, xticklabels_index)


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
