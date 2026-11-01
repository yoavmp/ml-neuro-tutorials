"""Offline structural tests for the Exercise 11 JupyterLite notebook.

WP61, modeled directly on tests/test_exercise_09_lite_notebook.py: required
YOUR CODE HERE tasks exist with no disguised solutions, checked questions
have keyed answers IN THE HIDDEN SETUP CELL ONLY, correct answers are
reproducibly shuffled rather than always listed first, no install cell, no
iframe/legacy-widget-config reference, and the student template, its
portable copy, and the completed reference notebook stay structurally
synchronized by construction (scripts/generate_exercise_11_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_11_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    python3 -m unittest discover -s tests -p 'test_exercise_11_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_11.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_11" / "exercise_11_portable.ipynb"
LITE_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_11_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_11_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp61-activity-rdm",
    "wp61-activity-animacy",
}

SINGLE_CHOICE_QUESTION_IDS = {
    "q-row-voxel",
    "q-rdm-cell",
    "q-mds-distortion",
}
MULTI_CHOICE_QUESTION_IDS = {"q-face-match-implications"}
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

        import generate_exercise_11_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_11_notebook.py", "--check"]
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
            "# Exercise 11: Embeddings and Representational Similarity Analysis",
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
        load_cell = next(c for c in self.cells if c.get("id") == "wp61-103-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_cell_count_is_reasonable(self):
        self.assertLessEqual(len(self.cells), 50)
        self.assertGreaterEqual(len(self.cells), 25)

    def test_no_stored_error_outputs(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error")

    # -- YOUR CODE HERE tasks ----------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 2)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_example_format_wording_not_example_shape(self):
        # WP61R item 7.
        self.assertIn("# Example format (not a real result):", self.code)
        self.assertNotIn("Example shape only", self.code)

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
        # Each forbidden fragment is a literal line from that blank's own
        # reference_source (a real working line of the solution) -- never a
        # phrase that could legitimately appear in a directional hint.
        forbidden_by_tag = {
            "wp61-activity-rdm": ("neural_rdm[i, j] = 1 - r",),
            "wp61-activity-animacy": (
                "nonscrambled_categories = [c for c in CATEGORIES if c != \"scrambledpix\"]",
                "animacy_hypothesis_rdm = np.array([",
            ),
        }
        for tag, forbidden in forbidden_by_tag.items():
            cell = next(c for c in self.cells if tag in c.get("metadata", {}).get("tags", []))
            source = _src(cell)
            self.assertIn("YOUR CODE HERE", source)
            for needle in forbidden:
                self.assertNotIn(needle, source, f"{tag} contains a solution fragment: {needle!r}")

    def test_required_output_names_appear_in_instructions(self):
        rdm_instructions = next(c for c in self.cells if c.get("id") == "wp61-204-instructions")
        self.assertIn("neural_rdm", _src(rdm_instructions))

        animacy_instructions = next(c for c in self.cells if c.get("id") == "wp61-404-instructions")
        for name in ("nonscrambled_categories", "animacy_hypothesis_rdm", "animacy_match_r"):
            self.assertIn(name, _src(animacy_instructions))

    def test_split_half_section_is_fully_removed(self):
        # WP61R item 12.
        for needle in ("split_half_r", "odd_rdm", "even_rdm", "ODD_CATEGORY_PATTERNS", "EVEN_CATEGORY_PATTERNS", "Split-Half"):
            self.assertNotIn(needle, self.code + self.md, needle)
        self.assertNotIn("q-split-half", self.code)
        self.assertNotIn("q-condition-order", self.code)

    def test_q_row_voxel_moved_before_category_patterns(self):
        # WP61R item 8.
        ids = [c.get("id") for c in self.cells]
        self.assertLess(ids.index("wp61-106-q-row-voxel"), ids.index("wp61-203-category-patterns"))
        self.assertLess(ids.index("wp61-105-heatmap"), ids.index("wp61-106-q-row-voxel"))

    # -- checked questions: visibility and shuffle --------------------------

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        checked = [
            c for c in self.cells if c.get("id") != "wp61-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 4)
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

    def test_every_question_declares_a_shuffle_seed_and_type(self):
        setup_source = _src(self.cells[1])
        for qid in QUESTION_IDS:
            block_match = re.search(rf'"{re.escape(qid)}":\s*dict\((.*?)\n    \),', setup_source, re.DOTALL)
            self.assertIsNotNone(block_match, qid)
            self.assertIn("shuffle_seed=", block_match.group(1), qid)

    def test_multiselect_question_uses_checkboxes_with_sensible_partial_feedback(self):
        self.assertIn("make_multi_choice_question", self.code)
        self.assertIn("widgets.Checkbox", self.code)
        self.assertIn("true statements selected", self.code)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- native widgets (no iframes) -----------------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/", self.code + self.md)

    def test_distance_metric_activity_is_notebook_native_and_precomputed(self):
        cell = next(c for c in self.cells if c.get("id") == "wp61-506-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("_DISTANCE_VARIANTS", source)
        self.assertIn("_DISTANCE_EMBEDDINGS", source)
        # Precomputed up front, outside the render function: the dropdown's
        # change handler only looks up an existing dict entry.
        self.assertLess(source.index("_DISTANCE_EMBEDDINGS = {"), source.index("def _distance_render"))

    def test_grouping_activity_is_notebook_native_and_labeled_exploratory(self):
        cell = next(c for c in self.cells if c.get("id") == "wp61-408-widget")
        source = _src(cell)
        self.assertIn("widgets.SelectMultiple", source)
        intro = next(c for c in self.cells if c.get("id") == "wp61-407-widget-intro")
        self.assertIn("exploration, not an independent test", _src(intro))

    def test_grouping_activity_excludes_scrambled_category(self):
        cell = next(c for c in self.cells if c.get("id") == "wp61-408-widget")
        source = _src(cell)
        self.assertIn('!= "scrambledpix"', source)

    # -- WP61R author corrections --------------------------------------------

    def test_mds_warnings_fixed_via_explicit_parameters_not_suppression(self):
        # WP61R item 9: every MDS(...) call sets n_init, init, and the
        # modern metric= spelling explicitly (root-cause fixes for the
        # three distinct FutureWarnings sklearn's MDS can emit), and no
        # warnings.filterwarnings call targets any of them.
        self.assertEqual(self.code.count("n_init=4"), 2)
        self.assertEqual(self.code.count('init="random"'), 2)
        self.assertEqual(self.code.count('metric="precomputed"'), 2)
        self.assertNotIn('dissimilarity="precomputed"', self.code)
        self.assertNotIn("dissimilarity.*deprecated", self.code)
        self.assertNotIn("default value of `init`", self.code)

    def test_mds_scatter_cell_guards_against_unfilled_neural_rdm(self):
        # WP61R item 10.
        cell = next(c for c in self.cells if c.get("id") == "wp61-303-mds")
        source = _src(cell)
        self.assertIn("not np.allclose(neural_rdm, 0.0)", source)

    def test_rdm_plot_cell_also_guards_against_unfilled_neural_rdm(self):
        # Consistency fix alongside item 10: the Section 2 heatmap-plot cell
        # had the identical latent bug.
        cell = next(c for c in self.cells if c.get("id") == "wp61-208-plot")
        source = _src(cell)
        self.assertIn("not np.allclose(neural_rdm, 0.0)", source)

    def test_mds_reflection_no_longer_mentions_the_written_answer_prompt(self):
        # WP61R item 11.
        reflection = next(c for c in self.cells if c.get("id") == "wp61-304-reflection")
        self.assertNotIn("prompt for the written-answer cell below", _src(reflection))

    def test_overview_wording_and_no_ventral_temporal_voxel_phrase(self):
        # WP61R items 1 and 2.
        overview = next(c for c in self.cells if c.get("id") == "wp61-002-overview")
        self.assertIn("run x category x voxel response patterns", _src(overview))
        self.assertNotIn("ventral-temporal-voxel", self.md)
        intro = next(c for c in self.cells if c.get("id") == "wp61-102-intro")
        self.assertNotIn("so that comparison is not circular", _src(intro))

    def test_manifest_is_linked_directly_from_section_1(self):
        # WP61R items 3 and 4 (correction): a direct clickable link, not a
        # "find it in JupyterLite's data folder" explanation.
        intro = next(c for c in self.cells if c.get("id") == "wp61-102-intro")
        source = _src(intro)
        self.assertIn("[haxby_rsa_patterns.manifest.json](data/haxby_rsa_patterns.manifest.json)", source)
        self.assertNotIn("data folder", source.lower())

    def test_heatmap_intro_wording(self):
        # WP61R item 5.
        intro = next(c for c in self.cells if c.get("id") == "wp61-104-heatmap-intro")
        self.assertIn("Here we can see", _src(intro))
        self.assertNotIn("Supplied:", _src(intro))

    def test_heatmap_has_row_boundary_lines(self):
        # WP61R item 6.
        cell = next(c for c in self.cells if c.get("id") == "wp61-105-heatmap")
        source = _src(cell)
        self.assertIn("ax.axhline(i - 0.5", source)

    def test_no_secure_answer_protection_paragraph(self):
        # WP61R item 14.
        self.assertNotIn("secure answer protection", self.md)
        self.assertNotIn("technically curious student can always recover", self.md)

    def test_widget_controls_use_the_label_overflow_fix(self):
        self.assertIn('style={"description_width": "initial"}', self.code)
        self.assertIn("widget-controls-row", self.code)
        self.assertIn("controls_row(", self.code)

    # -- data provenance and scope ------------------------------------------

    def test_no_raw_fmri_download_in_student_notebook(self):
        self.assertNotIn("fetch_haxby", self.code)
        self.assertNotIn("nilearn", self.code.lower())
        self.assertNotIn("nibabel", self.code.lower())

    def test_category_level_caveat_is_stated(self):
        self.assertIn("category-level", self.md)

    def test_no_naive_pvalue_presented(self):
        low_md = self.md.lower()
        self.assertIn("no p-value is reported", low_md)
        self.assertNotIn("p < 0.05", self.md)

    # -- editable answer cells -----------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [
            c
            for c in self.cells
            if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE | re.DOTALL)
        ]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp61", "wp-", "scripts/generate", "audit_result"):
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
        # WP61D release: book/downloads/chapter_11/exercise_11_portable.ipynb
        # is now produced (see scripts/generate_exercise_11_notebook.py's
        # PORTABLE_PATH) -- identical content to the JupyterLite template,
        # same as every other migrated exercise.
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
                continue
            self.assertEqual(_src(a), _src(b), a["id"])

    def test_reference_has_no_your_code_here_placeholders(self):
        text = "\n\n".join(_src(c) for c in self.reference_cells)
        self.assertNotIn("YOUR CODE HERE", text)


if __name__ == "__main__":
    unittest.main()
