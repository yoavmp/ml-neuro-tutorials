"""WP09 assertions for the course-level book structure (offline).

Covers the rename to *Machine Learning for Neuroscience*, and the
Introduction -> Contents -> Resources -> References top-level ordering.

WP56 removed the Syllabus page entirely (its own book page, its `_toc.yml`
nav entry, and student-facing links to it) -- see
`tests/test_classify_release_change.py`'s page-removal coverage for the
release-gate side of that change. The top-level pages are now Introduction,
Contents, Resources, and References only.

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

    def test_order_is_intro_contents_resources_references(self):
        # WP56: Syllabus was removed -- the top-level chapters are now
        # Contents, Resources, References, in that order (Introduction is
        # the book root, not a "chapters" entry).
        chapters = self.toc["chapters"]
        self.assertEqual(chapters[0]["file"], "contents")
        self.assertEqual(chapters[1]["file"], "resources")
        self.assertEqual(chapters[2]["file"], "references")
        self.assertEqual(len(chapters), 3)
        self.assertEqual(
            chapters[0]["sections"][0]["file"], "chapters/chapter_01/exercise_01"
        )

    def test_syllabus_is_not_in_the_toc(self):
        files = [c["file"] for c in self.toc["chapters"]]
        self.assertNotIn("syllabus", files)

    def test_exercises_one_through_nine_follow_in_order(self):
        # WP49/WP52: Exercises 10-12 are intentionally excluded from the
        # public toctree for this release (see
        # test_exercises_ten_through_twelve_source_preserved_but_not_published
        # below) -- 1-9 are published, in order.
        sections = self.toc["chapters"][0]["sections"]
        files = [s["file"] for s in sections]
        self.assertEqual(
            files,
            [f"chapters/chapter_{n:02d}/exercise_{n:02d}" for n in range(1, 10)],
        )
        for n in range(1, 10):
            self.assertTrue((BOOK / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb").exists())

    def test_exercises_ten_through_twelve_source_preserved_but_not_published(self):
        # WP49: unpublished, not deleted -- their source stays on disk (and
        # in git history) for later inspection/redesign, but must not appear
        # in the public toctree alongside Exercises 1-9.
        sections = self.toc["chapters"][0]["sections"]
        files = [s["file"] for s in sections]
        for n in (10, 11, 12):
            self.assertNotIn(f"chapters/chapter_{n:02d}/exercise_{n:02d}", files)
        self.assertTrue((BOOK / "chapters" / "chapter_10" / "exercise_10.ipynb").exists())
        for n in (11, 12):
            self.assertTrue((BOOK / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.md").exists())

    def test_no_exercise_13_in_toc(self):
        sections = self.toc["chapters"][0]["sections"]
        files = [s["file"] for s in sections]
        self.assertNotIn("chapters/chapter_13/exercise_13", files)
        self.assertEqual(len(files), 9)


class Pages(unittest.TestCase):
    def test_syllabus_page_was_removed(self):
        # WP56: the Syllabus page (and its nav entry, see Toc tests above)
        # is gone -- Introduction, Contents, Resources, and References are
        # the complete set of top-level pages now.
        self.assertFalse((BOOK / "syllabus.md").exists())

    def test_resources_covers_the_required_minimum_links(self):
        text = (BOOK / "resources.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Resources"))
        low = text.lower()
        for needle in (
            "hastie.su.domains/islp/islp_website.pdf.download.html",  # ISL w/ Python free edition
            "statlearning.com",
            "fcon_1000.projects.nitrc.org/indi/abide/abide_ii.html",  # official ABIDE II site
            "abideii_data_legend.pdf",  # phenotypic legend
            "github.com/neurohackademy/nh2020-curriculum",  # WP55: student-facing credit link (the pinned raw.githubusercontent.com URL is now only inside the notebooks' own loaders, not this page)
            "lite/files/data/abide_age_brain.csv",  # same-origin course export
        ):
            self.assertIn(needle, low, f"Resources is missing: {needle!r}")
        # No encouragement to install the repository itself.
        self.assertNotIn("git clone", low)
        self.assertNotIn("pip install -r requirements", low)

    def test_resources_does_not_link_private_repo_internals(self):
        text = (BOOK / "resources.md").read_text(encoding="utf-8")
        self.assertNotIn("github.com/yoavmp/ml-neuro-tutorials", text)

    def test_references_leads_with_the_course_book_and_covers_the_minimum(self):
        text = (BOOK / "references.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# References"))
        # The course book citation leads the page (WP54: "should lead the
        # References page").
        first_entry_pos = text.index("1. Gareth James")
        self.assertLess(first_entry_pos, text.index("Di Martino"))
        self.assertLess(first_entry_pos, text.index("Bethlehem"))
        self.assertLess(first_entry_pos, text.index("Storsve"))
        low = text.lower()
        for needle in (
            "an introduction to statistical learning",
            "10.1038/sdata.2017.10",  # ABIDE II dataset publication
            "bethlehem",
            "10.1038/s41586-022-04554-y",
            "storsve",
            "10.1523/jneurosci.0391-14.2014",
        ):
            self.assertIn(needle, low, f"References is missing: {needle!r}")

    def test_introduction_covers_the_required_concepts(self):
        # WP54: replaces the WP09-era passive/legacy-notebook version of
        # this page (every exercise got its own Colab link and a revealable-
        # guide/open-question framing; neither claim is true of the current
        # JupyterLite-native Exercises 1-9).
        intro = (BOOK / "intro.md").read_text(encoding="utf-8")
        self.assertTrue(intro.startswith("# Introduction"))
        low = " ".join(intro.lower().split())  # collapse line wrapping
        for needle in (
            "practice-session materials",
            "machine learning for neuroscience",
            "moodle",
            "at your own pace",
            "nothing to install",
            "your code here",
            "interactive activities",
            "select more than one correct option",
            "feedback",
            "download my notebook",
            "colab",
            ".ipynb",
            "reset from course template",
            "python 3.11",
            "ipywidgets",
            "pyodide",
        ):
            self.assertIn(needle, low, f"Introduction is missing: {needle!r}")

    def test_introduction_has_no_moodle_url_no_time_budget_no_guaranteed_3_11(self):
        intro = (BOOK / "intro.md").read_text(encoding="utf-8")
        self.assertNotIn("moodle.", intro.lower())
        self.assertNotRegex(intro, r"\d+\s*[-–]\s*\d+\s*min")
        self.assertNotIn("minutes", intro.lower())
        low = intro.lower()
        self.assertNotIn("every question has", low)
        self.assertNotIn("all questions have", low)
        # WP54: the kernelspec says "Python 3", not a specific minor
        # version -- never claim every environment literally runs 3.11.
        self.assertNotIn("every environment runs python 3.11", low)
        self.assertNotIn("always runs python 3.11", low)
        # No instruction to clear browser storage, and no promise that an
        # old downloaded copy updates itself or migrates automatically.
        self.assertNotIn("clear your browser", low)
        self.assertNotIn("clear site data", low)
        self.assertNotIn("automatically migrat", low)
        # No student-facing repo-install/requirements.txt instruction.
        self.assertNotIn("requirements.txt", low)
        self.assertNotIn("git clone", low)

    def test_contents_page_still_lists_practices(self):
        contents = (BOOK / "contents.md").read_text(encoding="utf-8")
        self.assertIn("# Contents", contents)
        self.assertIn("{tableofcontents}", contents)

    def test_introduction_links_onward_to_the_other_top_level_pages(self):
        # WP56: with Syllabus gone, Introduction is the landing page and
        # carries forward the pointer to Contents (practice notebooks) that
        # used to live on Syllabus, plus Resources and References.
        intro = (BOOK / "intro.md").read_text(encoding="utf-8")
        self.assertIn("[Contents](contents.md)", intro)
        self.assertIn("[Resources](resources.md)", intro)
        self.assertIn("[References](references.md)", intro)


if __name__ == "__main__":
    unittest.main()
