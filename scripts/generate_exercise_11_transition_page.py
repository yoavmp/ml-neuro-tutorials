#!/usr/bin/env python3
"""Generate the Exercise 11 transition page at its canonical book URL.

WP61D, following the exact pattern
scripts/generate_exercise_09_transition_page.py and
scripts/generate_exercise_12_transition_page.py established: the canonical
book page at book/chapters/chapter_11/exercise_11.ipynb becomes a short
transition page pointing at the JupyterLite notebook; the real lesson lives
in scripts/generate_exercise_11_notebook.py's generated output. This
replaces the old titled placeholder stub
book/chapters/chapter_11/exercise_11.md ("Materials for this exercise will
be added before the practice session.").

Modes:
  --write   regenerate book/chapters/chapter_11/exercise_11.ipynb.
  --check   fail if the committed file is stale.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_markdown_cell, new_notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "book" / "chapters" / "chapter_11" / "exercise_11.ipynb"
OLD_STUB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_11" / "exercise_11.md"

LITE_URL = "../../lite/notebooks/index.html?path=exercise_11.ipynb"
DOWNLOAD_URL = "../../lite/files/exercise_11_portable.ipynb"


def build_notebook() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    title = new_markdown_cell("# Exercise 11: Embeddings and RSA\n")
    title["id"] = "wp61d-transition-title"

    body = new_markdown_cell(
        f"""
This exercise runs as a single interactive notebook, directly in your
browser -- supplied code, your own code, written answers, checked questions,
and figures all live together in one place.

**<a href="{LITE_URL}">Open Exercise 11</a>**

The notebook opens with a **Back to course contents** button, and a
**Download my notebook** button that saves your current work (including your
edits) at any time. Your edits are stored only in this browser; use download
if you want a copy that survives clearing your browser data or moving to a
different device or browser.

If you would rather work outside the browser, <a href="{DOWNLOAD_URL}">download
the same notebook</a> and open it in a local Jupyter installation, or in
[Google Colab](https://colab.research.google.com/) using **File > Upload
notebook**.
""".strip()
        + "\n"
    )
    body["id"] = "wp61d-transition-body"

    nb["cells"] = [title, body]
    return nb


def _serialize() -> str:
    return nbformat.writes(build_notebook(), version=4)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    text = _serialize()
    if args.write:
        if OUT_PATH.exists() and OUT_PATH.read_text() == text:
            print("up to date")
        else:
            OUT_PATH.write_text(text)
            print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")
        if OLD_STUB_PATH.exists():
            OLD_STUB_PATH.unlink()
            print(f"removed superseded stub {OLD_STUB_PATH.relative_to(REPO_ROOT)}")
    else:
        if not OUT_PATH.exists() or OUT_PATH.read_text() != text:
            raise SystemExit(f"stale (run --write): {OUT_PATH.relative_to(REPO_ROOT)}")
        if OLD_STUB_PATH.exists():
            raise SystemExit(f"stale: superseded stub still present: {OLD_STUB_PATH.relative_to(REPO_ROOT)}")
        print("OK: up to date")


if __name__ == "__main__":
    main()
