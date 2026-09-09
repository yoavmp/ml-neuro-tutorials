"""WP07 content assertions for the canonical Chapter 1 EDA notebook.

Reads ``book/chapters/chapter_01/exercise_01.ipynb`` with ``nbformat`` and checks
the specific corrections WP07 asked for. Offline, no build required.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_notebook_corrections.py'
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb"


class NotebookCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.by_id = {c["id"]: c for c in cls.nb.cells}
        cls.md = "\n\n".join(
            c["source"] for c in cls.nb.cells if c["cell_type"] == "markdown"
        )
        cls.code = [c for c in cls.nb.cells if c["cell_type"] == "code"]

    # 1. no time estimate in "About this exercise"
    def test_no_time_budget_in_about(self):
        about = self.by_id["a1b2c30d4e5f"]["source"]
        self.assertNotRegex(about, r"\d+\s*[-–]\s*\d+\s*min")
        self.assertNotIn("minutes", about)
        self.assertNotIn("Budget", about)

    # 2. opening makes the assessment / deeper-understanding point without
    #    promising verbatim exam questions or a guaranteed answer for every Q
    def test_about_describes_questions_accurately(self):
        about = self.by_id["a1b2c30d4e5f"]["source"].lower()
        self.assertIn("assessment", about)
        self.assertTrue("exam" in about or "assessment" in about)
        self.assertNotIn("every question has a revealable answer", about)
        self.assertIn("open discussion question", about)

    # 3. "How to use" no longer enumerates the interactive activities and
    #    mentions browser / no-install, Colab, and portable download
    def test_how_to_use_is_concise(self):
        how = self.by_id["b2c3d40e5f6a"]["source"]
        self.assertNotIn("histogram", how.lower())
        self.assertNotIn("retention", how.lower())
        self.assertNotIn("correlation", how.lower())
        self.assertIn("browser", how.lower())
        self.assertIn("Colab", how)
        self.assertIn("portable", how.lower())

    # 3b. stable Colab / download links to the portable notebook are present
    def test_portable_links_present(self):
        joined = self.md
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/"
            "blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb",
            joined,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_01/exercise_01_portable.ipynb",
            joined,
        )

    # 4. the irrelevant object-dtype question is gone, adjacent questions stay
    def test_object_dtype_question_removed(self):
        card = self.by_id["e05d9a3c-cf5d-4b7b-ba0c-92aa7659d389"]["source"]
        self.assertNotIn("object", card)
        self.assertIn("How many participants and variables are present?", card)
        self.assertIn("Which variables contain missing observations?", card)
        self.assertIn("Are any categorical variables stored as numbers/strings?", card)
        # exactly three enumerated questions remain
        self.assertEqual(len(re.findall(r"^\d+\. ", card, re.M)), 3)
        for cell in self.nb.cells:
            self.assertNotIn(
                "Why might pandas assign the `object` data type", cell["source"]
            )

    # 5. collapsible executable Python age histogram, AGE_AT_SCAN, 25 bins
    def test_histogram_example_cell(self):
        hist = self.by_id["e6f7a8b9c0d1"]
        self.assertEqual(hist["cell_type"], "code")
        self.assertIn("hide-input", hist["metadata"].get("tags", []))
        src = hist["source"]
        self.assertIn('x="AGE_AT_SCAN"', src)
        self.assertIn("bins=25", src)
        self.assertIn("years", src)  # x-axis label in years
        self.assertIn("Number of participants", src)  # y-axis
        # it sits right after the histogram iframe cell + its one-line intro
        ids = [c["id"] for c in self.nb.cells]
        self.assertEqual(
            ids[ids.index("23475ca3-3adb-41b9-9918-6e75b953a2fd") + 2], "e6f7a8b9c0d1"
        )

    # 6. IQR defined explicitly before the fences
    def test_iqr_defined_before_fences(self):
        cell = self.by_id["58db4c1fc44e"]["source"]
        self.assertIn(r"\mathrm{IQR} = Q_3 - Q_1", cell)
        self.assertIn("25th", cell)
        self.assertIn("75th", cell)
        i_def = cell.index(r"\mathrm{IQR} = Q_3 - Q_1")
        i_fence = cell.index(r"1.5")
        self.assertLess(i_def, i_fence, "IQR must be defined before the 1.5*IQR fences")
        self.assertIn("does not prove the value is an error", cell)

    # 7. stripplot jitter is seeded, RNG state restored
    def test_stripplot_is_seeded(self):
        cell = self.by_id["80632a35b296"]["source"]
        self.assertIn("np.random.seed(0)", cell)
        self.assertIn("np.random.get_state()", cell)
        self.assertIn("np.random.set_state(", cell)
        self.assertLess(cell.index("np.random.seed(0)"), cell.index("sns.stripplot("))

    # counts
    def test_cell_and_visibility_counts(self):
        self.assertEqual(len(self.nb.cells), 84)
        self.assertEqual(len(self.code), 23)
        vis = {"visible": 0, "hide-input": 0, "hide-cell": 0, "hide-output": 0}
        for c in self.code:
            tags = set(c["metadata"].get("tags", []))
            key = next((k for k in ("hide-cell", "hide-input", "hide-output") if k in tags), "visible")
            vis[key] += 1
        self.assertEqual(vis, {"visible": 12, "hide-input": 8, "hide-cell": 3, "hide-output": 0})

    def test_valid_and_unique_ids(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.nb.cells]
        self.assertEqual(len(ids), len(set(ids)))
        # only hide-* tags anywhere
        for c in self.nb.cells:
            for t in c["metadata"].get("tags", []):
                self.assertIn(t, {"hide-input", "hide-cell", "hide-output"})


if __name__ == "__main__":
    unittest.main()
