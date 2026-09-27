"""Offline tests for book/chapters/chapter_02/exercise_02.ipynb.

WP41 replaced Exercise 2's canonical Jupyter Book notebook with a short
transition page (section 3.1): the real lesson now lives in
book/lite/files/exercise_02.ipynb. This page must keep the same H1 title (so
the book Contents page's auto-generated listing is unchanged) and must not
preserve a second, divergent copy of the lesson.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_02_transition_page.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb"


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
            "# Exercise 2: Regression and Bias-Variance Trade-Off",
        )

    def test_is_short(self):
        # A transition page, not a second lesson.
        self.assertLessEqual(len(self.cells), 3)

    def test_links_to_the_jupyterlite_notebook(self):
        # WP41R blocker 3: a bare Markdown `[text](../../lite/...)` link (the
        # pre-fix form) is a relative, non-scheme URL, which MyST/Sphinx
        # tries to resolve as an internal cross-reference and, failing that,
        # renders as a same-page "#..." anchor -- a no-op click. Raw HTML
        # passes through untouched, so require the real `<a href="...">`
        # form here, not just the URL as a substring anywhere on the page.
        self.assertIn(
            '<a href="../../lite/notebooks/index.html?path=exercise_02.ipynb">',
            self.text,
        )

    def test_links_to_the_downloadable_copy(self):
        # Same reasoning, and not book/downloads/ (excluded from the Jupyter
        # Book build -- see book/_config.yml): the served copy lives in
        # book/lite/files/, which `jupyter lite build` publishes same-origin.
        self.assertIn('<a href="../../lite/files/exercise_02_portable.ipynb">', self.text)
        self.assertNotIn("downloads/chapter_02", self.text)

    def test_no_raw_github_or_colab_deep_link(self):
        # WP41R blocker 3: colab.research.google.com/github/.../main/... only
        # ever reflects the public "main" branch (stale while this migration
        # is unpushed) and stops working once the repository goes private.
        self.assertNotIn("colab.research.google.com/github", self.text)
        self.assertNotIn("raw.githubusercontent.com", self.text)

    def test_no_analysis_content_duplicated_here(self):
        # None of the real lesson's code or established numbers should be
        # re-created on this page -- only a pointer to the notebook.
        for needle in (
            "KNeighborsRegressor",
            "LinearRegression",
            "train_test_split",
            "held-out R",
            "YOUR CODE HERE",
        ):
            self.assertNotIn(needle, self.text)

    def test_no_wp_or_script_references_in_student_text(self):
        low = self.text.lower()
        for needle in ("wp41", "scripts/", "generate_exercise_02"):
            self.assertNotIn(needle, low)


if __name__ == "__main__":
    unittest.main()
