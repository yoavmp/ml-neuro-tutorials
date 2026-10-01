"""Offline structural tests for the migrated Exercise 8 JupyterLite notebook.

WP47, modeled on tests/test_exercise_07_lite_notebook.py: required YOUR CODE
HERE tasks exist, no raise NotImplementedError, required editable answer
cells exist, checked questions have keyed answers IN THE HIDDEN SETUP CELL
ONLY (never in the visible question cell -- WP47's own "Multiple-choice
answer visibility" requirement), no install cell, no iframe/legacy-widget-
config reference, and the student template, its portable copy, and the
completed reference notebook stay structurally synchronized by construction
(scripts/generate_exercise_08_notebook.py).

Standard-library ``unittest``; no network, no kernel execution (see
tests/test_exercise_08_reference_execution.py for the executed-output /
numerical-integrity checks, which do run a kernel).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_08_lite_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
LITE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_08.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_08" / "exercise_08_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_08_reference.ipynb"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp47-activity-pca",
    "wp47-activity-variance",
    "wp47-activity-scatter",
    "wp47-activity-loadings",
    "wp47-activity-kmeans",
}

QUESTION_IDS = {
    "q-unsupervised-explore",
    "q-unsupervised-info",
    "q-pca-separation",
    "q-kmeans-reflection",
    "q-activity-kmeans",
    "q-pipeline-leakage",
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

        import generate_exercise_08_notebook as gen

        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["generate_exercise_08_notebook.py", "--check"]
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
        self.assertEqual(_src(self.cells[2]).splitlines()[0], "# Exercise 8: Unsupervised Learning")

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
        load_cell = next(c for c in self.cells if c.get("id") == "wp47-104-load")
        source = _src(load_cell)
        self.assertIn("except NameError", source)
        self.assertIn("raise RuntimeError", source)
        self.assertIn("notebook's first code cell", source)

    def test_data_load_never_feeds_demographics_into_pca_or_kmeans(self):
        load_cell = next(c for c in self.cells if c.get("id") == "wp47-104-load")
        source = _src(load_cell)
        self.assertIn("load_demographics_table", source)
        self.assertIn("for LATER coloring/interpretation", source)

    # -- scope exclusions -------------------------------------------------

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
            "pcr",
            "principal component regression",
            "linearregression",
        ):
            self.assertNotIn(needle, low_code, needle)
            self.assertNotIn(needle, low_md, needle)

    # -- YOUR CODE HERE tasks -------------------------------------------

    def test_your_code_here_tasks_exist(self):
        tagged = [c for c in self.cells if "YOUR CODE HERE" in _src(c)]
        self.assertEqual(len(tagged), 5)
        seen_tags = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(BLANK_TAGS, BLANK_TAGS & seen_tags)

    def test_no_raise_not_implemented(self):
        self.assertNotIn("NotImplementedError", self.code)

    def test_no_pip_install_cell(self):
        self.assertNotIn("!pip install", self.code)
        self.assertNotIn("%pip install", self.code)

    def test_blanks_are_not_pre_populated_with_the_solution(self):
        # The hint comments show the shape of the solution, but every such
        # line is commented out -- nothing here is executable as-is (the
        # same convention test_exercise_07_lite_notebook.py uses).
        for tag, forbidden in [
            ("wp47-activity-pca", "pca_explore = PCA(n_components=50, random_state=0).fit(Xs)"),
            ("wp47-activity-variance", "pca_variance_fig, axes = plt.subplots(1, 2, figsize=(11, 4))"),
            ("wp47-activity-scatter", "scatter = ax.scatter(X_pca[:, 0]"),
            ("wp47-activity-loadings", "ax.barh(range(N_TOP), values[::-1]"),
            ("wp47-activity-kmeans", "km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(cluster_X)"),
        ]:
            cell = next(c for c in self.cells if tag in c.get("metadata", {}).get("tags", []))
            source = _src(cell)
            self.assertIn("YOUR CODE HERE", source)
            for line in source.splitlines():
                if forbidden in line:
                    self.assertTrue(line.strip().startswith("#"), line)

    def test_required_output_names_appear_in_instructions(self):
        pca_instructions = next(c for c in self.cells if c.get("id") == "wp47-203-pca-instructions")
        for name in ("Xs", "pca_explore", "X_pca"):
            self.assertIn(name, _src(pca_instructions))

        variance_instructions = next(c for c in self.cells if c.get("id") == "wp47-206-variance-instructions")
        self.assertIn("pca_variance_fig", _src(variance_instructions))

        scatter_instructions = next(c for c in self.cells if c.get("id") == "wp47-209-scatter-instructions")
        self.assertIn("pca_scatter_fig", _src(scatter_instructions))

        loadings_instructions = next(c for c in self.cells if c.get("id") == "wp47-214-loadings-instructions")
        self.assertIn("pca_loadings_fig", _src(loadings_instructions))

        kmeans_instructions = next(c for c in self.cells if c.get("id") == "wp47-304-kmeans-instructions")
        for name in ("kmeans_results", "kmeans_inertia_fig", "kmeans_silhouette_fig"):
            self.assertIn(name, _src(kmeans_instructions))

    # -- checked questions: visibility (WP47's own new requirement) -------

    def test_checked_questions_use_show_question_with_no_visible_answer_key(self):
        # Excludes the hidden setup cell itself (id wp47-000-setup), which
        # defines show_question() and mentions it in its own explanatory
        # comment -- every OTHER, visible cell that calls it is a question.
        checked = [
            c
            for c in self.cells
            if c.get("id") != "wp47-000-setup" and 'show_question("' in _src(c)
        ]
        self.assertEqual(len(checked), 6)
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
        self.assertIn("def show_question(question_id):", source)

    def test_question_widgets_use_full_width_wrap_css(self):
        self.assertIn("checked-question", self.code)
        self.assertIn("white-space: normal", self.code)

    # -- notebook-native widgets (no iframes) --------------------------------

    def test_no_iframe_or_legacy_widget_config_reference(self):
        self.assertNotIn("<iframe", self.code + self.md)
        self.assertNotIn("configs/pca_projection.json", self.code + self.md)
        self.assertNotIn("configs/pca_kmeans_explorer.json", self.code + self.md)

    def test_explore_activity_is_notebook_native(self):
        cell = next(c for c in self.cells if c.get("id") == "wp47-403-widget")
        source = _src(cell)
        self.assertIn("widgets.Dropdown", source)
        self.assertIn("KMeans", source)
        self.assertIn("_activity_cache", source)

    def test_explore_activity_prefers_students_own_x_pca_with_a_labeled_fallback(self):
        cell = next(c for c in self.cells if c.get("id") == "wp47-403-widget")
        source = _src(cell)
        self.assertIn('if "X_pca" in globals()', source)
        self.assertIn("a fixed, independently computed PCA", source)

    # -- editable answer cells -------------------------------------------

    def test_editable_answer_cells_exist(self):
        answer_cells = [c for c in self.cells if c["cell_type"] == "markdown" and re.search(r"^>\s*\*\*.+\*\*\s*$", _src(c).strip(), re.MULTILINE)]
        self.assertGreaterEqual(len(answer_cells), 1)

    def test_no_your_answer_here_placeholder(self):
        self.assertNotIn("YOUR ANSWER HERE", self.md)

    # -- Section 5: leakage-safe pipeline, supplied (not a blank) ----------

    def test_pipeline_is_supplied_not_a_blank(self):
        cell = next(c for c in self.cells if c.get("id") == "wp47-506-pipeline")
        self.assertNotIn("YOUR CODE HERE", _src(cell))
        self.assertNotIn("wp47-activity", " ".join(cell.get("metadata", {}).get("tags", [])))

    def test_pipeline_never_reuses_section_2s_full_data_pca(self):
        cell = next(c for c in self.cells if c.get("id") == "wp47-506-pipeline")
        source = _src(cell)
        self.assertNotIn("pca_explore", source)
        self.assertNotIn("Xs)", source.split("Pipeline([")[0][-20:])

    def test_pipeline_code_block_is_shown(self):
        idx = next(i for i, c in enumerate(self.cells) if c.get("id") == "wp47-502-intro")
        src = _src(self.cells[idx])
        self.assertIn('("scale", StandardScaler())', src)
        self.assertIn('("pca", PCA())', src)
        self.assertIn('("model", KNeighborsRegressor())', src)

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("wp47", "wp-", "scripts/generate", "audit_result"):
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
