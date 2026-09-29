"""Offline tests for book/chapters/chapter_03/exercise_03.ipynb.

WP44 replaced Exercise 3's canonical Jupyter Book notebook with a short
transition page (mirroring WP41/WP42's treatment of Exercises 1-2): the real
lesson now lives in book/lite/files/exercise_03.ipynb. This page must keep
the same H1 title (so the book Contents page's auto-generated listing is
unchanged) and must not preserve a second, divergent copy of the lesson.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_03_transition_page.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb"


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class TransitionPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.text = "\n\n".join(_src(c) for c in cls.cells)

    def test_valid_notebook(self):
        nbformat.validate(self.nb)

    def test_h1_title_unchanged(self):
        self.assertEqual(
            _src(self.cells[0]).splitlines()[0],
            "# Exercise 3: Classification and Metrics",
        )

    def test_is_short(self):
        self.assertLessEqual(len(self.cells), 3)

    def test_links_to_the_jupyterlite_notebook(self):
        self.assertIn(
            '<a href="../../lite/notebooks/index.html?path=exercise_03.ipynb">',
            self.text,
        )

    def test_links_to_the_downloadable_copy(self):
        self.assertIn('<a href="../../lite/files/exercise_03_portable.ipynb">', self.text)
        self.assertNotIn("downloads/chapter_03", self.text)

    def test_no_raw_github_or_colab_deep_link(self):
        self.assertNotIn("colab.research.google.com/github", self.text)
        self.assertNotIn("raw.githubusercontent.com", self.text)

    def test_no_analysis_content_duplicated_here(self):
        for needle in (
            "LogisticRegression",
            "train_test_split",
            "confusion matrix",
            "YOUR CODE HERE",
        ):
            self.assertNotIn(needle, self.text)

    def test_no_wp_or_script_references_in_student_text(self):
        low = self.text.lower()
        for needle in ("wp44", "scripts/", "generate_exercise_03"):
            self.assertNotIn(needle, low)


if __name__ == "__main__":
    unittest.main()
