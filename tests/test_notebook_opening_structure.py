"""WP20 correction pass: cross-notebook authoring-rule checks for Exercises
1-4, covering the durable requirements in NOTEBOOK_AUTHORING_STANDARDS.md.

Deliberately structural/count-based rather than exact-wording where possible
(the opening list content is free to be reworded by a future WP), except for
a short list of deprecated student-facing phrases that must not reappear in
canonical notebooks, portable notebooks, or interactive widget config text.

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_notebook_opening_structure.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL = {
    "chapter_01": REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb",
    "chapter_02": REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb",
    "chapter_03": REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb",
    "chapter_04": REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.ipynb",
}
PORTABLE = {
    "chapter_01": REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb",
    "chapter_02": REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
    "chapter_03": REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
    "chapter_04": REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb",
}
WIDGET_CONFIGS = sorted((REPO_ROOT / "book" / "_static" / "widgets" / "configs").glob("*.json"))

# Exercise number, one row per notebook, in the same order as CANONICAL.
EXERCISE_NUMBERS = {"chapter_01": "1", "chapter_02": "2", "chapter_03": "3", "chapter_04": "4"}

COVERS_HEADING = "## What this notebook covers"
MAIN_HEADING_RE = re.compile(r"^## \d+\.", re.MULTILINE)
OPENING_LIST_ITEM_RE = re.compile(r"^\s*\d+\.\s", re.MULTILINE)

# Deprecated student-facing phrases this correction pass removed. Must not
# reappear, in any casing, anywhere a student can see them.
DEPRECATED_PHRASES = [
    "Honest evaluation versus invalid alternatives",
    "Honest vs invalid evaluation",
    "honest-vs-invalid",
    "One honest linear-regression workflow",
    "One honest logistic-regression model",
    "stratified train/test split does -- and does not -- fix",
    "stratified train/test split does—and does not—fix",
]
DEPRECATED_RE = re.compile("|".join(re.escape(p) for p in DEPRECATED_PHRASES), re.IGNORECASE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_source(cell: dict) -> str:
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def _cell_output_text(cell: dict) -> str:
    parts = []
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream":
            text = out.get("text", "")
            parts.append("".join(text) if isinstance(text, list) else text)
        elif "data" in out:
            plain = out.get("data", {}).get("text/plain", "")
            parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


def _full_text(nb: dict) -> str:
    parts = []
    for cell in nb.get("cells", []):
        parts.append(_cell_source(cell))
        parts.append(_cell_output_text(cell))
    return "\n".join(parts)


def _markdown_text(nb: dict) -> str:
    return "\n\n".join(
        _cell_source(c) for c in nb.get("cells", []) if c.get("cell_type") == "markdown"
    )


class OpeningStructureTests(unittest.TestCase):
    """§3.3 of NOTEBOOK_AUTHORING_STANDARDS.md: one 'What this notebook
    covers' section per notebook, with the identifying sentence inside it,
    and an opening list whose count matches the notebook's own numbered
    sections."""

    def test_exactly_one_covers_heading_per_notebook(self):
        for key, path in CANONICAL.items():
            md = _markdown_text(_load(path))
            self.assertEqual(
                md.count(COVERS_HEADING), 1, f"{key}: expected exactly one '{COVERS_HEADING}' heading"
            )

    def test_identifying_sentence_is_inside_the_covers_section(self):
        for key, path in CANONICAL.items():
            md = _markdown_text(_load(path))
            start = md.index(COVERS_HEADING)
            next_heading = md.find("\n## ", start + len(COVERS_HEADING))
            section = md[start:next_heading] if next_heading != -1 else md[start:]
            expected = f"This is Exercise {EXERCISE_NUMBERS[key]} of"
            self.assertIn(
                expected, section, f"{key}: identifying sentence missing from the covers section"
            )
            # ...and not loose directly under the main title (before the
            # covers heading at all).
            before = md[:start]
            self.assertNotIn(expected, before, f"{key}: identifying sentence sits above the covers heading")

    def test_opening_list_count_matches_numbered_sections(self):
        for key, path in CANONICAL.items():
            md = _markdown_text(_load(path))
            start = md.index(COVERS_HEADING)
            next_heading = md.find("\n## ", start + len(COVERS_HEADING))
            section = md[start:next_heading] if next_heading != -1 else md[start:]
            n_list_items = len(OPENING_LIST_ITEM_RE.findall(section))
            n_sections = len(MAIN_HEADING_RE.findall(md))
            self.assertGreater(n_list_items, 0, f"{key}: opening list has no numbered items")
            self.assertEqual(
                n_list_items,
                n_sections,
                f"{key}: opening list has {n_list_items} items but the notebook has {n_sections} numbered sections",
            )


class RepeatedLoadingCellTests(unittest.TestCase):
    """§3.2: Exercise 1 keeps its own first/only loading example visible;
    Exercises 2-4 collapse the repeated loading cell's input while keeping
    its useful output visible."""

    def test_exercise_1_loading_cells_are_visible(self):
        nb = _load(CANONICAL["chapter_01"])
        for idx in (4, 6):
            tags = nb["cells"][idx].get("metadata", {}).get("tags", [])
            self.assertEqual(tags, [], f"chapter_01 cell {idx} should carry no hide tag")

    def test_exercises_2_to_4_hide_input_on_the_repeated_loading_cell(self):
        for key in ("chapter_02", "chapter_03", "chapter_04"):
            nb = _load(CANONICAL[key])
            cell = nb["cells"][4]
            tags = cell.get("metadata", {}).get("tags", [])
            self.assertIn("hide-input", tags, f"{key} cell 4 should carry hide-input")
            self.assertNotIn("hide-cell", tags, f"{key} cell 4 must not use hide-cell (it hides output too)")

    def test_exercises_2_to_4_loading_cell_output_is_present(self):
        for key in ("chapter_02", "chapter_03", "chapter_04"):
            nb = _load(CANONICAL[key])
            cell = nb["cells"][4]
            text = _cell_output_text(cell)
            self.assertIn("data table:", text, f"{key} cell 4 output is missing or stale")


class DeprecatedPhraseTests(unittest.TestCase):
    """Phrases removed by the WP20 correction pass must not resurface in
    canonical notebooks, portable notebooks, or interactive widget config
    text."""

    def test_canonical_notebooks_are_clean(self):
        for key, path in CANONICAL.items():
            text = _full_text(_load(path))
            matches = sorted(set(m.group(0) for m in DEPRECATED_RE.finditer(text)))
            self.assertEqual(matches, [], f"{key} (canonical) still contains: {matches}")

    def test_portable_notebooks_are_clean(self):
        for key, path in PORTABLE.items():
            text = _full_text(_load(path))
            matches = sorted(set(m.group(0) for m in DEPRECATED_RE.finditer(text)))
            self.assertEqual(matches, [], f"{key} (portable) still contains: {matches}")

    def test_widget_configs_are_clean(self):
        for path in WIDGET_CONFIGS:
            text = path.read_text(encoding="utf-8")
            matches = sorted(set(m.group(0) for m in DEPRECATED_RE.finditer(text)))
            self.assertEqual(matches, [], f"{path.name} still contains: {matches}")


if __name__ == "__main__":
    unittest.main()
