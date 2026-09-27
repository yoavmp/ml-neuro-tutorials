#!/usr/bin/env python3
"""Generate the Exercise 2 transition page at its old canonical URL.

WP41 section 3.1: the old Exercise 2 URL "may become a small transition page
or redirect, but it must not preserve a second divergent version of the
lesson." The real lesson now lives in the JupyterLite template (see
scripts/generate_exercise_02_notebook.py); this page keeps the same H1 title
(so the book Contents page's auto-generated listing is unchanged) and points
students straight at the JupyterLite notebook.

Modes:
  --write   regenerate book/chapters/chapter_02/exercise_02.ipynb.
  --check   fail if the committed file is stale.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_markdown_cell, new_notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb"

LITE_URL = "../../lite/notebooks/index.html?path=exercise_02.ipynb"
DOWNLOAD_URL = "../../downloads/chapter_02/exercise_02_portable.ipynb"


def build_notebook() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    title = new_markdown_cell("# Exercise 2: Regression and Bias-Variance Trade-Off\n")
    title["id"] = "wp41-transition-title"

    body = new_markdown_cell(
        f"""
This exercise now runs as a single interactive notebook, directly in your
browser -- supplied code, your own code, written answers, checked questions,
and figures all live together in one place.

**[Open Exercise 2]({LITE_URL})**

The notebook opens with a **Back to course contents** button, and a
**Download my notebook** button that saves your current work (including your
edits) at any time. Your edits are stored only in this browser; use download
if you want a copy that survives clearing your browser data or moving to a
different device or browser.

If you would rather work outside the browser, download the same notebook
directly and run it in a local Jupyter installation or in
[Google Colab](https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_02/exercise_02_portable.ipynb):
[{DOWNLOAD_URL}]({DOWNLOAD_URL})
""".strip()
        + "\n"
    )
    body["id"] = "wp41-transition-body"

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
    else:
        if not OUT_PATH.exists() or OUT_PATH.read_text() != text:
            raise SystemExit(f"stale (run --write): {OUT_PATH.relative_to(REPO_ROOT)}")
        print("OK: up to date")


if __name__ == "__main__":
    main()
