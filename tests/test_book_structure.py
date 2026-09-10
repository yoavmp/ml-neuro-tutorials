"""WP09 assertions for the course-level book structure (offline).

Covers the rename to *Machine Learning for Neuroscience*, the
Introduction -> Syllabus -> Contents -> Exercise I ordering, and the
title-only Syllabus page.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_book_structure.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOK = REPO_ROOT / "book"

COURSE_TITLE = "Machine Learning for Neuroscience"


class BookConfig(unittest.TestCase):
    def test_course_title_is_exact_and_has_no_markdown_or_old_name(self):
        cfg = yaml.safe_load((BOOK / "_config.yml").read_text(encoding="utf-8"))
        self.assertEqual(cfg["title"], COURSE_TITLE)
        self.assertNotIn("*", cfg["title"])
        self.assertNotIn("Neuroscientists", cfg["title"])


class Toc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.toc = yaml.safe_load((BOOK / "_toc.yml").read_text(encoding="utf-8"))

    def test_introduction_is_the_book_root(self):
        self.assertEqual(self.toc["root"], "intro")

    def test_order_is_intro_syllabus_contents_then_exercise_nested(self):
        chapters = self.toc["chapters"]
        self.assertEqual(chapters[0]["file"], "syllabus")
        self.assertEqual(chapters[1]["file"], "contents")
        self.assertEqual(
            chapters[1]["sections"][0]["file"], "chapters/chapter_01/exercise_01"
        )

    def test_exercise_two_follows_exercise_one(self):
        sections = self.toc["chapters"][1]["sections"]
        files = [s["file"] for s in sections]
        self.assertEqual(
            files,
            ["chapters/chapter_01/exercise_01", "chapters/chapter_02/exercise_02"],
        )
        self.assertTrue(
            (BOOK / "chapters" / "chapter_02" / "exercise_02.ipynb").exists()
        )


class Pages(unittest.TestCase):
    def test_syllabus_is_title_only(self):
        text = (BOOK / "syllabus.md").read_text(encoding="utf-8").strip()
        self.assertEqual(text, "# Syllabus")

    def test_introduction_covers_the_required_concepts(self):
        intro = (BOOK / "intro.md").read_text(encoding="utf-8")
        self.assertTrue(intro.startswith("# Introduction"))
        low = " ".join(intro.lower().split())  # collapse line wrapping
        for needle in (
            "practice-session materials",
            "machine learning for neuroscience",
            "moodle",
            "at your own pace",
            "nothing to install",
            "colab",
            ".ipynb",
            "experiment by changing it",
            "before",  # questions placed before explanations
            "assessment",
            "revealable",
            "no single correct answer",
        ):
            self.assertIn(needle, low, f"Introduction is missing: {needle!r}")

    def test_introduction_has_no_moodle_url_no_time_budget_no_answer_guarantee(self):
        intro = (BOOK / "intro.md").read_text(encoding="utf-8")
        self.assertNotIn("http", intro)  # Moodle is named, never linked
        self.assertNotIn("moodle.", intro.lower())
        self.assertNotRegex(intro, r"\d+\s*[-–]\s*\d+\s*min")
        self.assertNotIn("minutes", intro.lower())
        low = intro.lower()
        self.assertNotIn("every question has", low)
        self.assertNotIn("all questions have", low)

    def test_contents_page_still_lists_practices(self):
        contents = (BOOK / "contents.md").read_text(encoding="utf-8")
        self.assertIn("# Contents", contents)
        self.assertIn("{tableofcontents}", contents)


if __name__ == "__main__":
    unittest.main()
