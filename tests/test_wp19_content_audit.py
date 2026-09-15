"""Repository-wide content audit for WP19: confirms that early-course
cross-validation / formal-parameter-selection material is absent from the
rendered student-facing sources of Exercises 1-4.

Scope (WP19 §8.1): the four canonical notebooks, their generated portable
notebooks, and the four activity-widget config JSON files whose text is
rendered directly in the book pages (knn_explore, knn_abc,
classification_threshold, classification_imbalance). Historical WP documents
and completed WP reports are records and are intentionally NOT scanned here
(WP19 §2 scope rule).

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp19_content_audit.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

NOTEBOOK_PATHS = [
    REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb",
    REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb",
    REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb",
    REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb",
]

WIDGET_CONFIG_PATHS = [
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_explore.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_abc.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "classification_threshold.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "classification_imbalance.json",
]

# Case-insensitive substrings that must not appear in rendered student-facing
# text for Exercises 1-4 (WP19 §8.1). Regex-escaped where needed.
PROHIBITED_PATTERNS = [
    r"gridsearchcv",
    r"cross_val_score",
    r"cross_validate\b",
    r"stratifiedkfold",
    r"\bkfold\(",  # KFold used as a live model-selection call, not the word alone
    r"\bcross[- ]validation\b",
    r"5-fold cross-validation",
    r"best\s+k\b",
    r"selected\s+k\b",
    r"optimal\s+k\b",
    r"cv-selected\s+k",
    r"best\s+c\b",
    r"selected\s+c\b",
    r"optimal\s+c\b",
    r"cv-selected\s+c",
    r"choosing k honestly",
    r"choosing c honestly",
    r"k_selected",
    r"c_selected",
]

PROHIBITED_RE = re.compile("|".join(PROHIBITED_PATTERNS), re.IGNORECASE)


def _notebook_text(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        src = cell.get("source", "")
        parts.append("".join(src) if isinstance(src, list) else src)
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                text = out.get("text", "")
                parts.append("".join(text) if isinstance(text, list) else text)
            elif "data" in out:
                plain = out["data"].get("text/plain", "")
                parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


class NotebookContentAudit(unittest.TestCase):
    def test_notebooks_exist(self):
        for path in NOTEBOOK_PATHS:
            self.assertTrue(path.exists(), path)

    def test_no_prohibited_early_cv_or_tuning_terms(self):
        for path in NOTEBOOK_PATHS:
            text = _notebook_text(path)
            matches = sorted(set(m.group(0).lower() for m in PROHIBITED_RE.finditer(text)))
            self.assertEqual(
                matches, [], f"{path.relative_to(REPO_ROOT)} contains prohibited terms: {matches}"
            )

    def test_exercise_3_uses_fixed_k20_language(self):
        for path in (NOTEBOOK_PATHS[2], NOTEBOOK_PATHS[6]):
            text = _notebook_text(path)
            self.assertIn("K_EXAMPLE = 20", text, path)

    def test_exercise_4_uses_fixed_c1_language(self):
        for path in (NOTEBOOK_PATHS[3], NOTEBOOK_PATHS[7]):
            text = _notebook_text(path)
            self.assertIn("C_EXAMPLE = 1.0", text, path)


class WidgetConfigContentAudit(unittest.TestCase):
    def test_configs_exist(self):
        for path in WIDGET_CONFIG_PATHS:
            self.assertTrue(path.exists(), path)

    def test_no_prohibited_early_cv_or_tuning_terms(self):
        for path in WIDGET_CONFIG_PATHS:
            text = path.read_text(encoding="utf-8")
            matches = sorted(set(m.group(0).lower() for m in PROHIBITED_RE.finditer(text)))
            self.assertEqual(
                matches, [], f"{path.relative_to(REPO_ROOT)} contains prohibited terms: {matches}"
            )

    def test_knn_explore_default_k_is_the_fixed_worked_example(self):
        cfg = json.loads((REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_explore.json").read_text())
        self.assertEqual(cfg["defaultK"], 20)


if __name__ == "__main__":
    unittest.main()
