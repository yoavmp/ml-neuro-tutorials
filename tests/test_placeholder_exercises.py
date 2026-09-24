"""Offline assertions for the WP25 placeholder pages, Exercises 11-12.

WP25 restructured the book around the new course syllabus. Exercises 1-3 are
full notebooks (covered by their own dedicated test files); Exercises 5-12
were minimal Markdown placeholder pages with no content yet. WP27 converted
Exercise 4 from a placeholder into a real notebook (see
test_exercise_04_notebook.py); WP28 did the same for Exercise 5 (see
test_exercise_05_notebook.py); WP29 did the same for Exercise 6 (see
test_exercise_06_notebook.py); WP32 did the same for Exercise 7 (see
test_exercise_07_notebook.py); WP33 did the same for Exercise 8 (see
test_exercise_08_notebook.py); WP34 did the same for Exercise 9 (see
test_exercise_09_notebook.py); WP38 did the same for Exercise 10 (see
test_exercise_10_notebook.py), so none of the seven is covered here any
more. This file confirms each remaining placeholder (11-12) exists, carries
exactly its required title and one placeholder sentence, and contains none
of the material the task explicitly excludes from a placeholder (no
learning objectives, dates, final-project reminders, Colab/download
buttons, interactive content, empty code cells, syllabus quotations, or
section outlines).

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_placeholder_exercises.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PLACEHOLDER_TITLES = {
    11: "Exercise 11: Embeddings and Representational Similarity Analysis",
    12: "Exercise 12: Review and Exam-Style Questions",
}

PLACEHOLDER_SENTENCE = "Materials for this exercise will be added before the practice session."

EXCLUDED_SUBSTRINGS = (
    "learning objective",
    "colab",
    "download",
    "<iframe",
    "```{admonition}",
    "```python",
    "```{code",
    "final project",
    "final-project",
    "תרגול",
    "syllabus",
)


class PlaceholderExercises(unittest.TestCase):
    def _path_for(self, n: int) -> Path:
        return REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.md"

    def test_every_placeholder_file_exists(self):
        for n in PLACEHOLDER_TITLES:
            path = self._path_for(n)
            self.assertTrue(path.exists(), path)

    def test_no_exercise_13_placeholder_exists(self):
        self.assertFalse((REPO_ROOT / "book" / "chapters" / "chapter_13").exists())

    def test_no_ipynb_placeholder_files_exist(self):
        # Exercise 4 previously held the classification notebook (moved to
        # Exercise 3 by WP25); confirm no stale .ipynb remains at any
        # placeholder route.
        for n in PLACEHOLDER_TITLES:
            ipynb = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb"
            self.assertFalse(ipynb.exists(), ipynb)

    def test_each_placeholder_has_exactly_the_title_and_one_sentence(self):
        for n, title in PLACEHOLDER_TITLES.items():
            text = self._path_for(n).read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if line.strip()]
            self.assertEqual(lines, [f"# {title}", PLACEHOLDER_SENTENCE], (n, lines))

    def test_no_excluded_content_in_any_placeholder(self):
        for n in PLACEHOLDER_TITLES:
            text = self._path_for(n).read_text(encoding="utf-8").lower()
            for needle in EXCLUDED_SUBSTRINGS:
                self.assertNotIn(needle.lower(), text, (n, needle))

    def test_no_active_portable_notebook_for_any_placeholder(self):
        for n in PLACEHOLDER_TITLES:
            portable = (
                REPO_ROOT / "book" / "downloads" / f"chapter_{n:02d}" / f"exercise_{n:02d}_portable.ipynb"
            )
            self.assertFalse(portable.exists(), portable)


if __name__ == "__main__":
    unittest.main()
