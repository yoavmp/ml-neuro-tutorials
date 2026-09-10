"""Offline assertions for book/chapters/chapter_02/exercise_02.ipynb (Exercise II).

Standard-library ``unittest``; no network. Checks structure, the leakage guard
in the notebook code, that the literature bundle matches the reviewed manifest,
that the executed outputs are present, and that no KNN / bias-variance content
was added.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_02_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class Notebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    def test_valid_and_ids_are_stable_and_unique(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith("wp11-") for i in ids), ids)

    def test_h1_title(self):
        self.assertEqual(_src(self.cells[0]).splitlines()[0], "# Exercise II: Regression")

    def test_opening_has_scope_and_prerequisites_no_time_budget(self):
        opening = "\n".join(_src(c) for c in self.cells[:4])
        self.assertIn("What this notebook covers", opening)
        self.assertIn("Prerequisites", opening)
        low = opening.lower()
        self.assertNotIn("minutes", low)
        self.assertNotRegex(opening, r"\d+\s*[-–]\s*\d+\s*min")
        # does not re-teach the course-level Introduction / How-to material
        self.assertNotIn("at your own pace", low)
        self.assertNotIn("moodle", low)

    def test_cell_count_is_short_relative_to_exercise_one(self):
        n = len(self.cells)
        self.assertGreaterEqual(n, 28)
        self.assertLessEqual(n, 50)
        ex1 = nbformat.read(
            REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4
        )
        self.assertLess(n, len(ex1.cells))

    def test_only_hide_input_and_hide_cell_tags_are_used(self):
        seen = set()
        for c in self.cells:
            seen |= set(c.get("metadata", {}).get("tags", []))
        self.assertTrue(seen <= {"hide-input", "hide-cell"}, seen)

    def test_no_knn_or_bias_variance_section(self):
        for c in self.cells:
            if c["cell_type"] != "markdown":
                continue
            for line in _src(c).splitlines():
                if line.startswith("#"):
                    low = line.lower()
                    self.assertNotIn("nearest neighbour", low)
                    self.assertNotIn("nearest neighbor", low)
                    self.assertNotIn("knn", low)
                    self.assertNotIn("bias-variance", low)
                    self.assertNotIn("bias–variance", low)
        # the words may appear only in the single forward-looking sentence
        self.assertLessEqual(self.md.lower().count("nearest neighbour"), 1)
        self.assertLessEqual(self.md.lower().count("bias-variance"), 1)

    def test_five_numbered_sections_present(self):
        for head in (
            "## 1. The modelling table",
            "## 2. One honest linear-regression workflow",
            "## 3. Three ways to score the same model",
            "## 4. Comparing feature sets",
            "## 5. What does sample size change?",
        ):
            self.assertIn(head, self.md)

    def test_embedded_frontoparietal_bundle_matches_the_manifest(self):
        cell = next(c for c in self.cells if c["id"] == "wp11-021")
        # the notebook embeds the list literally; it must equal the reviewed one
        src = _src(cell)
        start = src.index("FRONTOPARIETAL = ") + len("FRONTOPARIETAL = ")
        end = src.index("]", start) + 1
        embedded = json.loads(src[start:end])
        self.assertEqual(embedded, MANIFEST["bundles"]["frontoparietal"]["rois"])

    def test_notebook_code_has_the_leakage_guard(self):
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', self.code)
        self.assertIn('"FIQ" not in FEATURES', self.code)

    def test_fixed_stratified_split_and_pipeline(self):
        self.assertIn("random_state=42", self.code)
        self.assertIn("stratify=groups", self.code)
        self.assertIn("make_pipeline(StandardScaler(), LinearRegression())", self.code)

    def test_invalid_leakage_model_is_a_clearly_named_object(self):
        self.assertIn("invalid_test_fitted_model", self.code)
        # it is never reused in a later section
        after = self.code.split("invalid_test_fitted_model", 2)
        self.assertEqual(len(after), 3)  # defined + used once in section 3 only

    def test_activity_iframe_points_at_the_regression_compare_config(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        self.assertEqual(len(iframe_cells), 1)
        src = _src(iframe_cells[0])
        self.assertIn("configs/regression_compare.json", src)
        self.assertIn(
            'title="Interactive feature-set comparison for predicting IQ from brain structure"',
            src,
        )

    def test_literature_citations_present(self):
        self.assertIn("10.1017/S0140525X07001185", self.md)  # Jung & Haier P-FIT
        self.assertIn("10.1093/cercor/bhl125", self.md)  # Narr et al.

    def test_executed_outputs_are_present_and_teach_the_point(self):
        out = self.all_output
        self.assertIn("1004 participants", out)
        self.assertIn("held-out R^2 = -0.", out)  # negative held-out R^2
        self.assertIn("n_train = 681", out)
        self.assertIn("n_features (p) = 78", out)
        # the A/B/C leakage table is present with all three rows
        self.assertIn("A. correct", out)
        self.assertIn("B. training score", out)
        self.assertIn("C. invalid", out)

    def test_no_execution_errors_committed(self):
        for c in self.cells:
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error", _src(c)[:120])


def _collect_output(nb) -> str:
    parts = []
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                parts.append(out.get("text", ""))
            elif "data" in out:
                plain = out["data"].get("text/plain", "")
                parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
