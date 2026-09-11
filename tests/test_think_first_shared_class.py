"""WP14 section 2: one shared blue "Think first" admonition across every
canonical notebook (Exercises 1-3).

Standard-library ``unittest``; no network. Scans every markdown cell of all
three canonical notebooks and asserts that every "Think first" admonition
block uses the single shared ``think-first`` MyST class, and that no legacy
variant (``:class: note`` immediately preceding a "Think first" title, or any
other class) remains anywhere.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_think_first_shared_class.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = {
    "chapter_01": REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb",
    "chapter_02": REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb",
    "chapter_03": REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb",
}

# Matches ```{admonition} Think first ... ``` blocks, capturing the ":class:"
# line (if any) that immediately follows the title line.
_BLOCK_RE = re.compile(
    r"```\{admonition\}\s*Think first\s*\n(:class:\s*([A-Za-z0-9_-]+))?", re.MULTILINE
)


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class ThinkFirstSharedClass(unittest.TestCase):
    def test_every_think_first_admonition_uses_the_shared_blue_class(self):
        for chapter, path in NOTEBOOKS.items():
            nb = nbformat.read(path, as_version=4)
            found_any = False
            for cell in nb.cells:
                if cell["cell_type"] != "markdown":
                    continue
                src = _src(cell)
                for m in _BLOCK_RE.finditer(src):
                    found_any = True
                    cls = m.group(2)
                    with self.subTest(chapter=chapter, cell=cell["id"]):
                        self.assertEqual(
                            cls,
                            "think-first",
                            f"{chapter} cell {cell['id']!r}: Think first block uses class "
                            f"{cls!r}, expected 'think-first'",
                        )
            self.assertTrue(found_any, f"{chapter}: no Think first admonition found at all")

    def test_no_legacy_note_class_think_first_block_remains(self):
        legacy = re.compile(r"```\{admonition\}\s*Think first\s*\n:class:\s*note\b", re.MULTILINE)
        for chapter, path in NOTEBOOKS.items():
            nb = nbformat.read(path, as_version=4)
            for cell in nb.cells:
                if cell["cell_type"] != "markdown":
                    continue
                src = _src(cell)
                with self.subTest(chapter=chapter, cell=cell["id"]):
                    self.assertNotRegex(src, legacy)

    def test_think_first_css_defines_one_distinct_blue_treatment(self):
        css = (REPO_ROOT / "book" / "_static" / "custom.css").read_text(encoding="utf-8")
        self.assertIn(".admonition.think-first", css)
        # the shared class must not be grouped into the same (rust) selector
        # block as .challenge / .how-to-use any more
        self.assertNotRegex(
            css, re.compile(r"\.admonition\.think-first,\s*\n\.bd-article \.admonition\.challenge")
        )
        self.assertIn("--ml-think-accent", css)


if __name__ == "__main__":
    unittest.main()
