"""Repository-wide content audit for WP25: the syllabus-aligned notebook
restructure (Exercise 3's KNN/bias-variance material merged into Exercise 2;
the old Exercise 4 classification lesson moved wholesale to become the new
Exercise 3; Exercises 4-12 added as placeholder pages; the pre-WP25 notebook
structure preserved on archive/pre-syllabus-notebook-structure).

Standard-library ``unittest``; no network. Uses ``git`` (local, offline) only
to confirm the archive branch's SHA and the Syllabus page's byte-for-byte
content against that branch -- no other test in this file touches git.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp25_content_audit.py'
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ARCHIVE_BRANCH = "archive/pre-syllabus-notebook-structure"
# The exact WP24 tip this WP25 archive branch and the WP25 branch itself both
# started from (recorded in WPs/WP25_SYLLABUS_ALIGNED_NOTEBOOK_RESTRUCTURE.md
# and WPs/reports/WP24_REPORT.md).
WP24_TIP_SHA = "914841c4c6033f232d96ce33b6dbcc23eda1c766"

EXERCISE_TITLES = {
    1: "Exercise 1: Exploratory Data Analysis",
    2: "Exercise 2: Regression and Bias-Variance Trade-Off",
    3: "Exercise 3: Classification and Metrics",
    4: "Exercise 4: Cross-Validation for Classification and Regression",
    5: "Exercise 5: Regularization and Feature Selection",
    6: "Exercise 6: Decision Trees",
    7: "Exercise 7: Trees and Boosting",
    8: "Exercise 8: PCA and Clustering",
    9: "Exercise 9: Advanced Models and Model Comparison",
    10: "Exercise 10: Common Machine Learning Mistakes",
    11: "Exercise 11: Embeddings and Representational Similarity Analysis",
    12: "Exercise 12: Review and Exam-Style Questions",
}

FINAL_PROJECT_NEEDLES = (
    "final project",
    "final-project",
    "capstone",
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


class ArchiveBranchTests(unittest.TestCase):
    def test_archive_branch_exists_locally(self):
        branches = _git("branch", "--list", ARCHIVE_BRANCH)
        self.assertIn(ARCHIVE_BRANCH, branches)

    def test_archive_branch_points_at_the_exact_wp24_tip(self):
        sha = _git("rev-parse", ARCHIVE_BRANCH).strip()
        self.assertEqual(sha, WP24_TIP_SHA)

    def test_archive_branch_has_no_new_commits_beyond_the_wp24_tip(self):
        # rev-list count from the WP24 tip to the archive branch tip must be 0.
        count = _git("rev-list", "--count", f"{WP24_TIP_SHA}..{ARCHIVE_BRANCH}").strip()
        self.assertEqual(count, "0")

    def test_archive_branch_preserves_the_old_knn_exercise_3(self):
        text = _git("show", f"{ARCHIVE_BRANCH}:book/chapters/chapter_03/exercise_03.ipynb")
        self.assertIn("Exercise 3: KNN and the Bias", text)
        self.assertIn("knn_abc.json", text)

    def test_archive_branch_preserves_the_old_classification_exercise_4(self):
        text = _git("show", f"{ARCHIVE_BRANCH}:book/chapters/chapter_04/exercise_04.ipynb")
        self.assertIn("Exercise 4: Classification with Logistic Regression", text)


class SyllabusPageUnchangedTests(unittest.TestCase):
    def test_syllabus_source_is_byte_for_byte_unchanged_from_the_wp24_tip(self):
        before = _git("show", f"{WP24_TIP_SHA}:book/syllabus.md")
        after = (REPO_ROOT / "book" / "syllabus.md").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_syllabus_page_was_not_edited_relative_to_the_archive_branch(self):
        before = _git("show", f"{ARCHIVE_BRANCH}:book/syllabus.md")
        after = (REPO_ROOT / "book" / "syllabus.md").read_text(encoding="utf-8")
        self.assertEqual(before, after)


class ExerciseOneThroughTwelveTitles(unittest.TestCase):
    def _title_of(self, n: int) -> str:
        if n <= 3:
            import json

            path = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb"
            nb = json.loads(path.read_text(encoding="utf-8"))
            return "".join(nb["cells"][0]["source"]).strip().lstrip("#").strip()
        path = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.md"
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        return first_line.lstrip("#").strip()

    def test_every_exercise_title_matches_the_required_syllabus_wording(self):
        for n, expected in EXERCISE_TITLES.items():
            with self.subTest(exercise=n):
                self.assertEqual(self._title_of(n), expected)

    def test_titles_use_title_case_for_the_named_phrases(self):
        required_phrases = (
            "Regression and Bias-Variance Trade-Off",
            "Classification and Metrics",
            "Cross-Validation for Classification and Regression",
            "Regularization and Feature Selection",
            "Advanced Models and Model Comparison",
            "Representational Similarity Analysis",
            "Exam-Style Questions",
        )
        all_titles = " | ".join(EXERCISE_TITLES.values())
        for phrase in required_phrases:
            self.assertIn(phrase, all_titles)

    def test_no_exercise_13(self):
        self.assertNotIn(13, EXERCISE_TITLES)
        self.assertFalse((REPO_ROOT / "book" / "chapters" / "chapter_13").exists())


class NoFinalProjectReferences(unittest.TestCase):
    def test_no_final_project_reference_in_any_exercise_1_to_12_page(self):
        for n in range(1, 13):
            if n <= 3:
                path = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb"
            else:
                path = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.md"
            text = path.read_text(encoding="utf-8").lower()
            for needle in FINAL_PROJECT_NEEDLES:
                self.assertNotIn(needle, text, (n, needle))

    def test_no_final_project_reference_in_portable_notebooks(self):
        for n in (1, 2, 3):
            path = (
                REPO_ROOT
                / "book"
                / "downloads"
                / f"chapter_{n:02d}"
                / f"exercise_{n:02d}_portable.ipynb"
            )
            text = path.read_text(encoding="utf-8").lower()
            for needle in FINAL_PROJECT_NEEDLES:
                self.assertNotIn(needle, text, (n, needle))


class NoDuplicateActiveCopies(unittest.TestCase):
    def test_only_one_active_classification_notebook(self):
        # Exercise 4 must be a placeholder, not a second copy of the
        # classification lesson.
        ex4_md = (REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("LogisticRegression", ex4_md)
        self.assertNotIn("confusion matrix", ex4_md.lower())
        self.assertFalse(
            (REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.ipynb").exists()
        )

    def test_only_one_active_copy_of_the_transferred_knn_material(self):
        import json

        nb = json.loads(
            (REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb").read_text(
                encoding="utf-8"
            )
        )
        # one illustrative markdown snippet ("```python K_EXAMPLE = 20```",
        # matching Exercise 2's linear-regression "Choosing C"-style pattern)
        # plus exactly one real, executed code cell -- never two fit cells.
        code_hits = sum(
            1
            for c in nb["cells"]
            if c["cell_type"] == "code" and "K_EXAMPLE = 20" in "".join(c["source"])
        )
        self.assertEqual(code_hits, 1)
        ex2 = (REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb").read_text(
            encoding="utf-8"
        )
        # not duplicated anywhere else in the active chapters
        for n in (1, 3):
            other = (
                REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb"
            ).read_text(encoding="utf-8")
            self.assertNotIn("K_EXAMPLE = 20", other)

    def test_no_active_knn_abc_assets_remain(self):
        self.assertFalse(
            (REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_abc.json").exists()
        )
        self.assertFalse(
            (
                REPO_ROOT
                / "book"
                / "_static"
                / "widgets"
                / "data"
                / "abide_knn_abc_manifest.json"
            ).exists()
        )
        self.assertFalse(
            (REPO_ROOT / "interactive" / "src" / "components" / "knn-abc.ts").exists()
        )


if __name__ == "__main__":
    unittest.main()
