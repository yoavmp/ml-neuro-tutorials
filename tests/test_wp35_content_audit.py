"""Repository-wide student-facing language audit for WP35.

Two independent checks, across every canonical and portable notebook for
Exercises 1-9 plus every activity-widget config JSON:

1. No likely author/operator-facing phrase (a private production decision,
   an internal script/report/WP reference, or wording that speaks to the
   course instructor rather than to a student) appears anywhere a student
   can see it. A narrow, explicit allowlist covers legitimate instructional
   uses of an otherwise-flagged word -- this audit does not ban ordinary
   English globally.
2. No unclear "development partition" phrasing remains where a student can
   see it (WP35 §3): every remaining instance must already have been
   replaced by context-specific plain language elsewhere in the same WP.

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp35_content_audit.py'
"""

from __future__ import annotations

import glob
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_NOTEBOOKS = sorted(REPO_ROOT.glob("book/chapters/chapter_0[1-9]/exercise_0[1-9].ipynb"))
PORTABLE_NOTEBOOKS = sorted(REPO_ROOT.glob("book/downloads/chapter_0[1-9]/exercise_0[1-9]_portable.ipynb"))
WIDGET_CONFIGS = sorted((REPO_ROOT / "book" / "_static" / "widgets" / "configs").glob("*.json"))

# Phrases/patterns that speak to the course author/instructor or leak
# internal production process into student-visible material (WP35 §3).
# Matched case-insensitively against plain text (markdown/comments/prose),
# not against code identifiers, so `predeclared_grid` as a variable name is
# not itself flagged -- only these phrases appearing in running text.
FORBIDDEN_PHRASES = [
    "predeclared",
    "audited on the target machine",
    "the wp report",
    "see the script",
    "see the report",
    "per the task",
    "per the instructions",
    "internal timing protocol",
    "audit",
    "canonical",
    "manifest",
    "payload",
    "render count",
    "test fixture",
    "implementation detail",
]
WP_REFERENCE_RE = re.compile(r"\bwp ?\d{2}\b", re.IGNORECASE)
SCRIPT_PATH_RE = re.compile(r"\bscripts/[\w.]+\.py\b")

# Narrow allowlist: (path suffix, cell/field index or None for "anywhere in
# file", phrase) triples for confirmed legitimate instructional uses. Empty
# by design -- every current hit has been rewritten in plain language rather
# than allowlisted; add an entry here only for a genuine future exception,
# reviewed in context per WP35 §3's instruction not to blind-replace.
ALLOWLIST: set[tuple[str, str]] = set()


def _cell_text(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def _load_cells(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def _scan_notebook(path: Path) -> list[str]:
    findings = []
    rel = str(path.relative_to(REPO_ROOT))
    for i, cell in enumerate(_load_cells(path)):
        text = _cell_text(cell)
        low = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in low and (rel, phrase) not in ALLOWLIST:
                findings.append(f"{rel} cell {i} ({cell.get('cell_type')}): forbidden phrase {phrase!r}")
        if WP_REFERENCE_RE.search(text) and (rel, "wp-reference") not in ALLOWLIST:
            findings.append(f"{rel} cell {i} ({cell.get('cell_type')}): WP-number reference")
        if SCRIPT_PATH_RE.search(text) and (rel, "script-path") not in ALLOWLIST:
            findings.append(f"{rel} cell {i} ({cell.get('cell_type')}): internal script-path reference")
    return findings


def _scan_widget_config(path: Path) -> list[str]:
    findings = []
    rel = str(path.relative_to(REPO_ROOT))
    cfg = json.loads(path.read_text(encoding="utf-8"))
    text_parts = [str(cfg.get(k, "")) for k in ("title", "description", "instructions", "testSetNote")]
    text_parts.extend(str(p) for p in cfg.get("reflectionPrompts", []) or [])
    blob = " ".join(text_parts)
    low = blob.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in low and (rel, phrase) not in ALLOWLIST:
            findings.append(f"{rel}: forbidden phrase {phrase!r}")
    if WP_REFERENCE_RE.search(blob) and (rel, "wp-reference") not in ALLOWLIST:
        findings.append(f"{rel}: WP-number reference")
    if SCRIPT_PATH_RE.search(blob) and (rel, "script-path") not in ALLOWLIST:
        findings.append(f"{rel}: internal script-path reference")
    return findings


class AuthorFacingLanguageAudit(unittest.TestCase):
    def test_no_author_facing_phrases_in_canonical_notebooks(self):
        findings = [f for path in CANONICAL_NOTEBOOKS for f in _scan_notebook(path)]
        self.assertEqual(findings, [], "\n" + "\n".join(findings))

    def test_no_author_facing_phrases_in_portable_notebooks(self):
        findings = [f for path in PORTABLE_NOTEBOOKS for f in _scan_notebook(path)]
        self.assertEqual(findings, [], "\n" + "\n".join(findings))

    def test_no_author_facing_phrases_in_widget_configs(self):
        findings = [f for path in WIDGET_CONFIGS for f in _scan_widget_config(path)]
        self.assertEqual(findings, [], "\n" + "\n".join(findings))

    def test_at_least_nine_canonical_and_portable_notebooks_scanned(self):
        # Guards against a glob typo silently scanning zero files.
        self.assertEqual(len(CANONICAL_NOTEBOOKS), 9)
        self.assertGreaterEqual(len(PORTABLE_NOTEBOOKS), 9)
        self.assertGreater(len(WIDGET_CONFIGS), 10)


class DevelopmentPartitionAudit(unittest.TestCase):
    """WP35 §3: every unclear student-facing 'development partition' use in
    Exercises 1-9 has been replaced by context-specific plain language."""

    def test_no_development_partition_in_canonical_notebooks(self):
        findings = []
        for path in CANONICAL_NOTEBOOKS:
            for i, cell in enumerate(_load_cells(path)):
                if "development partition" in _cell_text(cell).lower():
                    findings.append(f"{path.relative_to(REPO_ROOT)} cell {i}")
        self.assertEqual(findings, [], findings)

    def test_no_development_partition_in_portable_notebooks(self):
        findings = []
        for path in PORTABLE_NOTEBOOKS:
            for i, cell in enumerate(_load_cells(path)):
                if "development partition" in _cell_text(cell).lower():
                    findings.append(f"{path.relative_to(REPO_ROOT)} cell {i}")
        self.assertEqual(findings, [], findings)

    def test_no_development_partition_in_widget_configs_or_data(self):
        findings = []
        for path in WIDGET_CONFIGS:
            if "development partition" in path.read_text(encoding="utf-8").lower():
                findings.append(str(path.relative_to(REPO_ROOT)))
        for path in sorted((REPO_ROOT / "book" / "_static" / "widgets" / "data").glob("*.json")):
            if "development partition" in path.read_text(encoding="utf-8").lower():
                findings.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(findings, [], findings)


if __name__ == "__main__":
    unittest.main()
