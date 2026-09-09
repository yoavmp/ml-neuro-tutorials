"""Offline unit tests for scripts/build_portable_notebook.py.

Standard-library ``unittest`` only. No network. The committed portable notebook
is read but never rewritten.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_build_portable_notebook.py'
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

import nbformat

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_portable_notebook as bpn  # noqa: E402


def _load_canonical():
    return nbformat.read(bpn.CANONICAL, as_version=4)


def _columns():
    return json.loads(bpn.COLUMNS_JSON.read_text(encoding="utf-8"))


def _joined(nb):
    parts = []
    for cell in nb.cells:
        src = cell["source"]
        parts.append("".join(src) if isinstance(src, list) else src)
    return "\n".join(parts)


class ConvertMystDirectives(unittest.TestCase):
    def test_admonition_becomes_heading(self):
        out = bpn.convert_myst_directives(
            "```{admonition} Think first\n:class: think-first\n\nAnswer before you run it.\n```"
        )
        self.assertIn("#### Think first", out)
        self.assertIn("Answer before you run it.", out)
        self.assertNotIn("```{", out)
        self.assertNotIn(":class:", out)

    def test_dropdown_becomes_details(self):
        out = bpn.convert_myst_directives(
            "```{dropdown} Check your reasoning\n\nBecause the median is global.\n```"
        )
        self.assertIn("<details>", out)
        self.assertIn("<summary><strong>Check your reasoning</strong></summary>", out)
        self.assertIn("</details>", out)
        self.assertNotIn("```{", out)

    def test_card_plus_dropdown_in_one_cell(self):
        src = (
            "```{admonition} Think first\n:class: think-first\n\n1. First?\n2. Second?\n```\n"
            "\n"
            "```{dropdown} Check your reasoning\n\nThe reasoning.\n```"
        )
        out = bpn.convert_myst_directives(src)
        self.assertIn("#### Think first", out)
        self.assertIn("1. First?", out)
        self.assertIn("<details>", out)
        self.assertIn("The reasoning.", out)
        self.assertNotIn("```{", out)

    def test_plain_markdown_is_untouched(self):
        src = "### A heading\n\nSome *text* and a $$x = 1$$ formula.\n"
        self.assertEqual(bpn.convert_myst_directives(src), src.rstrip("\n"))


class BuildPortable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = bpn.build_portable(_load_canonical(), _columns())
        cls.text = _joined(cls.nb)

    def test_banner_and_setup_prepended(self):
        self.assertEqual(self.nb.cells[0]["id"], bpn.BANNER_ID)
        self.assertEqual(self.nb.cells[1]["id"], bpn.SETUP_ID)
        self.assertIn(bpn.PUBLISHED_PAGE, self.nb.cells[0]["source"])
        self.assertIn("requirements.txt", self.nb.cells[1]["source"])

    def test_no_iframe_or_static_or_directive_or_hidetag(self):
        self.assertNotIn("<iframe", self.text)
        self.assertNotIn("_static/", self.text)
        self.assertNotIn("```{", self.text)
        for cell in self.nb.cells:
            if cell["cell_type"] == "code":
                tags = cell.get("metadata", {}).get("tags", [])
                self.assertEqual(set(tags) & bpn.HIDE_TAGS, set())
                self.assertEqual(cell.get("outputs"), [])
                self.assertIsNone(cell.get("execution_count"))

    def test_iframe_cells_replaced_with_published_links(self):
        # all three activity titles are gone, replaced by the same course URL
        for title in bpn.IFRAME_REPLACEMENTS:
            self.assertNotIn(f'title="{title}"', self.text)
        self.assertEqual(self.text.count(bpn.PUBLISHED_PAGE), 1 + 3)  # banner + 3

    def test_dropped_navigation_admonitions(self):
        for cell in self.nb.cells:
            self.assertNotIn("Run or download this notebook", cell["source"])
            self.assertNotIn("How to use this notebook", cell["source"])

    def test_portable_data_loading_is_offline_safe(self):
        self.assertIn("CURATED_COLUMNS = [", self.text)
        self.assertIn("phenotypes = phenotypes[CURATED_COLUMNS].copy()", self.text)
        self.assertNotIn("COLUMNS_URL", self.text)
        self.assertNotIn("pd.read_json(", self.text)
        # the pinned CSV URL is kept
        self.assertIn("neurohackademy/nh2020-curriculum/", self.text)
        # every curated column is embedded, in order
        for col in _columns():
            self.assertIn(f'"{col}"', self.text)

    def test_categorical_conversion_preserved(self):
        self.assertIn('.astype("category")', self.text)

    def test_histogram_example_cell_survives(self):
        code = [c["source"] for c in self.nb.cells if c["cell_type"] == "code"]
        hist = [s for s in code if 'x="AGE_AT_SCAN"' in s and "bins=25" in s]
        self.assertEqual(len(hist), 1)

    def test_unique_cell_ids(self):
        ids = [c["id"] for c in self.nb.cells]
        self.assertEqual(len(ids), len(set(ids)))

    def test_valid_nbformat(self):
        nbformat.validate(self.nb)


class Determinism(unittest.TestCase):
    def test_repeated_builds_are_byte_identical(self):
        a = bpn.serialize(bpn.build_portable(_load_canonical(), _columns()))
        b = bpn.serialize(bpn.build_portable(_load_canonical(), _columns()))
        self.assertEqual(a, b)
        self.assertTrue(a.endswith("\n"))

    def test_committed_file_is_not_stale(self):
        expected = bpn.serialize(bpn.build_portable(_load_canonical(), _columns()))
        self.assertTrue(
            bpn.PORTABLE.exists(),
            "book/downloads/chapter_01/exercise_01_portable.ipynb is missing; run --write",
        )
        self.assertEqual(
            bpn.PORTABLE.read_text(encoding="utf-8"),
            expected,
            "portable notebook is stale; run scripts/build_portable_notebook.py --write",
        )


class CheckMode(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = bpn.main(argv)
        return rc, out.getvalue() + err.getvalue()

    def test_check_passes_on_committed_file(self):
        rc, _ = self._run(["--check"])
        self.assertEqual(rc, 0)

    def test_check_detects_staleness(self):
        original = bpn.PORTABLE.read_text(encoding="utf-8")
        try:
            bpn.PORTABLE.write_text(original + "\n", encoding="utf-8")
            rc, msg = self._run(["--check"])
            self.assertEqual(rc, 1)
            self.assertIn("stale", msg.lower())
        finally:
            bpn.PORTABLE.write_text(original, encoding="utf-8")

    def test_requires_a_mode(self):
        with self.assertRaises(SystemExit):
            self._run([])


if __name__ == "__main__":
    unittest.main()
