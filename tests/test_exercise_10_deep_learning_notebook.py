"""Offline structural tests for the WP58 Exercise 10 ("Deep Learning") notebook.

Colab/local-only notebook (Gate A found this course's pinned JupyterLite
build cannot install PyTorch -- see WPs/reports/WP58_REPORT.md). Checks:
required YOUR CODE HERE blanks exist with no full solution leaked as a
comment, checked questions have keyed answers in the hidden setup cell
only (never in a visible cell), correct answers are reproducibly shuffled
rather than always listed first, the student template and the completed
reference notebook stay structurally synchronized by construction
(scripts/generate_exercise_10_deep_learning_notebook.py), no MyST
directive fences (this notebook has no Jupyter Book page), and the
preserved legacy Exercise 10 notebook is untouched.

Standard-library ``unittest``; no network, no kernel execution (see
WPs/reports/WP58_REPORT.md for the executed-output / timing verification,
which does run a kernel in an isolated Python 3.11 environment).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_10_deep_learning_notebook.py'
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_10" / "exercise_10_deep_learning_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_10_deep_learning_reference.ipynb"
LEGACY_NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_10" / "exercise_10.ipynb"
LEGACY_PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_10" / "exercise_10_portable.ipynb"
PLACEHOLDER_PATH = REPO_ROOT / "book" / "chapters" / "chapter_10" / "placeholder.md"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

BLANK_TAGS = {
    "wp58-activity-tensors",
    "wp58-activity-model",
    "wp58-activity-loop",
}

QUESTION_IDS = {
    "q-tensor-shape",
    "q-logits-loss",
    "q-gradient-update",
    "q-train-only-scaling",
    "q-overfitting-earlystop",
    "q-test-set-choices",
}

SECTION_TITLES = [
    "## 1. Setup and the Task",
    "## 2. Hold-Out Design and Tensors",
    "## 3. Build a Fully Connected Network",
    "## 4. Train and Validate",
    "## 5. Final Evaluation and Comparison",
    "## 6. Interpretation and Limits",
]

ENGINEERING_VOCAB = ("schema", "payload", "artifact", "manifest", "wp58", "fixture", "canonical recipe")

# Phrases that would only appear in a fully-worked solution, not a hint.
# These must appear in the reference notebook's blanks but never in the
# student notebook's blanks.
SOLUTION_PHRASES = [
    "torch.tensor(X_train_s, dtype=torch.float32)",
    "torch.utils.data.TensorDataset(X_train_t, y_train_t)",
    "torch.utils.data.DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)",
    "nn.Linear(input_dim, hidden1)",
    "nn.Linear(hidden1, hidden2)",
    "self.act1(self.fc1(x))",
    "self.act2(self.fc2(x))",
    "return self.fc3(x)",
    "logits = model(xb)",
    "loss = loss_fn(logits, yb)",
]


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


def _joined(nb) -> str:
    return "\n".join(_src(c) for c in nb.cells)


class ExerciseTenDeepLearningStudentNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(PORTABLE_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.joined = _joined(cls.nb)

    def test_notebook_is_valid_nbformat(self):
        nbformat.validate(self.nb)

    def test_title_cell_is_first_and_only_the_title(self):
        first = _src(self.cells[0]).strip()
        self.assertEqual(first, "# Exercise 10: Deep Learning")

    def test_what_this_notebook_covers_has_six_numbered_items_matching_sections(self):
        idx = next(i for i, c in enumerate(self.cells) if "What this notebook covers" in _src(c))
        text = _src(self.cells[idx])
        numbered = [line for line in text.splitlines() if re.match(r"^\d+\.\s", line.strip())]
        self.assertEqual(len(numbered), 6)

    def test_all_section_headings_present_in_order(self):
        positions = []
        for title in SECTION_TITLES:
            found = [i for i, c in enumerate(self.cells) if title in _src(c)]
            self.assertTrue(found, f"missing section heading: {title!r}")
            positions.append(found[0])
        self.assertEqual(positions, sorted(positions))

    def test_colab_local_only_and_no_jupyterlite_claim(self):
        self.assertIn("Google Colab or ordinary local Jupyter", self.joined)
        self.assertIn("not available through this course's in-browser\nJupyterLite launcher", self.joined)

    def test_pyodide_version_and_evidence_named(self):
        self.assertIn("jupyterlite-pyodide-kernel 0.8.5", self.joined)
        self.assertIn("Pyodide v314.0.5", self.joined)
        self.assertIn("verified directly, not assumed", self.joined)

    def test_conditional_torch_install_cell_present_once(self):
        self.assertEqual(self.joined.count("%pip install torch"), 1)
        self.assertIn("except ImportError:", self.joined)

    def test_data_counts_stated(self):
        self.assertIn("1,440", self.joined)
        self.assertIn("1,004 participants", self.joined)
        self.assertIn("cortical thickness", self.joined.lower())
        self.assertIn("cortical surface area", self.joined.lower())
        self.assertIn("grey-matter volume", self.joined.lower())
        self.assertIn("gyrification", self.joined.lower())

    def test_no_myst_directive_fences(self):
        # This notebook has no Jupyter Book page -- plain Markdown only.
        self.assertNotIn("```{", self.joined)

    def test_no_engineering_vocabulary_leaks_to_student_text(self):
        lowered = self.joined.lower()
        for term in ENGINEERING_VOCAB:
            self.assertNotIn(term, lowered, term)

    def test_three_blanks_present_with_expected_tags(self):
        tagged = {t for c in self.cells for t in c.get("metadata", {}).get("tags", [])}
        self.assertEqual(tagged & BLANK_TAGS, BLANK_TAGS)

    def test_student_blanks_contain_ellipsis_placeholder_not_full_solution(self):
        for c in self.cells:
            tags = c.get("metadata", {}).get("tags", [])
            if any(t in BLANK_TAGS for t in tags):
                src = _src(c)
                self.assertIn("...", src)
                for phrase in SOLUTION_PHRASES:
                    self.assertNotIn(phrase, src, f"student blank leaks solution phrase: {phrase!r}")

    def test_six_show_question_calls_present(self):
        calls = re.findall(r'show_question\("([^"]+)"\)', self.joined)
        for qid in QUESTION_IDS:
            self.assertIn(f'show_question("{qid}")', self.joined)
        self.assertEqual(set(calls), QUESTION_IDS)
        self.assertEqual(len(calls), len(QUESTION_IDS))

    def test_correct_index_never_appears_outside_hidden_setup_cell(self):
        hidden_cells = {
            c["id"] for c in self.cells if c.get("metadata", {}).get("jupyter", {}).get("source_hidden")
        }
        self.assertTrue(hidden_cells)
        for c in self.cells:
            if c["id"] in hidden_cells:
                continue
            self.assertNotIn("correct_index", _src(c))

    def test_setup_cell_is_hidden_and_first_code_cell(self):
        code_cells = [c for c in self.cells if c["cell_type"] == "code"]
        first_code = code_cells[0]
        self.assertEqual(first_code.get("metadata", {}).get("jupyter", {}).get("source_hidden"), True)

    def test_early_stopping_and_train_only_scaling_language_present(self):
        self.assertIn("fit on `X_train` only", self.joined)
        self.assertIn("early stopping", self.joined.lower())
        self.assertIn("restored", self.joined.lower())

    def test_test_set_evaluated_once_language_present(self):
        self.assertIn("exactly once", self.joined)

    def test_comparison_includes_dummy_logreg_and_network(self):
        self.assertIn("dummy (majority class)", self.joined)
        self.assertIn("logistic regression", self.joined.lower())
        self.assertIn("neural network", self.joined.lower())
        self.assertIn("balanced_accuracy", self.joined)
        self.assertIn("roc_auc", self.joined)

    def test_earlier_exercise_context_not_a_controlled_comparison(self):
        normalized = " ".join(self.joined.split())
        self.assertIn("Exercise 3", normalized)
        self.assertIn("not** as a directly controlled comparison", normalized)

    def test_citation_present_with_exact_qualifications(self):
        normalized = " ".join(self.joined.split())
        self.assertIn("Saponaro et al. (2022, *NeuroImage: Clinical*)", normalized)
        self.assertIn("221 structural morphometric features", normalized)
        self.assertIn("1,638 participants", normalized)
        self.assertIn("37 sites", normalized)
        self.assertIn("0.58", normalized)
        self.assertIn("0.67", normalized)
        self.assertIn("functional** MRI", normalized)

    def test_no_diagnostic_or_definitive_ceiling_claim(self):
        normalized = " ".join(self.joined.split())
        self.assertIn("supports a diagnostic or causal claim", normalized)
        self.assertIn("None of this supports", normalized)
        self.assertIn("does not mean this general approach has hit some definitive ceiling", normalized)

    def test_portable_notebook_has_no_repository_relative_dependency(self):
        for forbidden in ("_static/", "../../config/", "<iframe", "requirements.txt", "```{"):
            self.assertNotIn(forbidden, self.joined)


class ExerciseTenDeepLearningReferenceNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.student_nb = nbformat.read(PORTABLE_PATH, as_version=4)
        cls.reference_nb = nbformat.read(REFERENCE_PATH, as_version=4)

    def test_notebook_is_valid_nbformat(self):
        nbformat.validate(self.reference_nb)

    def test_reference_blanks_contain_the_real_solution(self):
        for c in self.reference_nb.cells:
            tags = c.get("metadata", {}).get("tags", [])
            if any(t in BLANK_TAGS for t in tags):
                src = _src(c)
                self.assertNotIn("YOUR CODE HERE", src)
                self.assertNotIn("...", src)

    def test_student_and_reference_share_identical_scaffold(self):
        """The two notebooks must have the same cells, in the same order,
        with identical source -- except for the three blank-tagged cells,
        where they intentionally differ (student placeholder vs. the real
        solution). This is enforced by construction (one shared cell list
        rendered twice), not just by this test, but the test guards against
        a stale committed file."""
        student_ids = [c["id"] for c in self.student_nb.cells]
        reference_ids = [c["id"] for c in self.reference_nb.cells]
        self.assertEqual(student_ids, reference_ids)

        differing = []
        for sc, rc in zip(self.student_nb.cells, self.reference_nb.cells):
            if _src(sc) != _src(rc):
                differing.append(sc["id"])
        self.assertEqual(set(differing), BLANK_TAGS_CELL_IDS)


BLANK_TAGS_CELL_IDS = {"wp58-207-tensors-blank", "wp58-303-model-blank", "wp58-403-loop-blank"}


class ExerciseTenGeneratorStaleness(unittest.TestCase):
    """The committed notebooks must match what the generator would produce
    right now -- catches an edit to the generator that was not followed by
    --write, without needing to shell out or hit the network."""

    def test_generator_check_mode_reports_up_to_date(self):
        import importlib

        module = importlib.import_module("generate_exercise_10_deep_learning_notebook")
        for mode, path in [("student", PORTABLE_PATH), ("reference", REFERENCE_PATH)]:
            nb = module.build_notebook(mode)
            expected = nbformat.writes(nb, version=4)
            actual = path.read_text()
            self.assertEqual(
                actual, expected, f"{path} is stale; run scripts/generate_exercise_10_deep_learning_notebook.py --write"
            )


class LegacyExerciseTenUntouched(unittest.TestCase):
    """WP58 must not touch the preserved legacy Exercise 10 notebook, its
    portable copy, or the live published placeholder stub."""

    def test_legacy_notebook_still_titled_examples_and_common_mistakes(self):
        nb = nbformat.read(LEGACY_NB_PATH, as_version=4)
        first = _src(nb.cells[0]).strip()
        self.assertEqual(first, "# Exercise 10: Examples and Common Mistakes")

    def test_legacy_portable_notebook_exists(self):
        self.assertTrue(LEGACY_PORTABLE_PATH.exists())

    def test_placeholder_page_still_says_coming_later(self):
        text = PLACEHOLDER_PATH.read_text()
        self.assertIn("Deep Learning", text)
        self.assertNotIn("<iframe", text)


if __name__ == "__main__":
    unittest.main()
