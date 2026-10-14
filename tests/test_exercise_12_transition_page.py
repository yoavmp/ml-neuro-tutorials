"""Offline tests for book/chapters/chapter_12/exercise_12.ipynb.

WP57 replaces the old, never-built placeholder stub
book/chapters/chapter_12/exercise_12.md (a stub for a different, never-
implemented topic, with no reviewable historical content of its own) with
a short transition page (mirroring WP44-WP47/WP52's treatment of Exercises
3-9): the real lesson now lives in book/lite/files/exercise_12.ipynb.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_12_transition_page.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_12" / "exercise_12.ipynb"
OLD_STUB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_12" / "exercise_12.md"


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

    def test_old_placeholder_stub_is_superseded(self):
        self.assertFalse(OLD_STUB_PATH.exists())

    def test_h1_title(self):
        self.assertEqual(_src(self.cells[0]).splitlines()[0], "# Exercise 12: Common Mistakes and Pitfalls")

    def test_is_short(self):
        self.assertLessEqual(len(self.cells), 3)

    def test_links_to_the_jupyterlite_notebook(self):
        self.assertIn('<a href="../../lite/notebooks/index.html?path=exercise_12.ipynb">', self.text)

    def test_links_to_the_downloadable_copy(self):
        self.assertIn('<a href="../../lite/files/exercise_12_portable.ipynb">', self.text)
        self.assertNotIn("downloads/chapter_12", self.text)

    def test_no_raw_github_or_colab_deep_link(self):
        self.assertNotIn("colab.research.google.com/github", self.text)
        self.assertNotIn("raw.githubusercontent.com", self.text)

    def test_no_analysis_content_duplicated_here(self):
        for needle in ("PCA(", "StandardScaler(", "GroupShuffleSplit", "YOUR CODE HERE"):
            self.assertNotIn(needle, self.text)

    def test_no_wp_or_script_references_in_student_text(self):
        low = self.text.lower()
        for needle in ("wp57", "wp38", "scripts/", "generate_exercise_12"):
            self.assertNotIn(needle, low)


if __name__ == "__main__":
    unittest.main()
