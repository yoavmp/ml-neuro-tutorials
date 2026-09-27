#!/usr/bin/env python3
"""Generate the Exercise 2 transition page at its old canonical URL.

WP41 section 3.1: the old Exercise 2 URL "may become a small transition page
or redirect, but it must not preserve a second divergent version of the
lesson." The real lesson now lives in the JupyterLite template (see
scripts/generate_exercise_02_notebook.py); this page keeps the same H1 title
(so the book Contents page's auto-generated listing is unchanged) and points
students straight at the JupyterLite notebook.

WP41R blocker 3: both destination links use raw inline HTML `<a href=...>`
rather than Markdown `[text](url)` syntax. MyST/Sphinx treats a *relative*
Markdown link that is not a scheme-qualified external URL as a candidate
cross-reference to another document in this project; since neither
"../../lite/notebooks/index.html?path=..." nor
"../../downloads/chapter_02/exercise_02_portable.ipynb" is a real Sphinx
document, that resolution fails and the built HTML ends up either as a
same-page "#..." anchor (a no-op click) or literal unlinked text. Raw inline
HTML in a Markdown cell is passed through untouched by CommonMark/MyST, so it
renders as an ordinary, working `<a>` tag instead.

The download path is real (not 404) because `book/_config.yml` copies
`book/downloads/` into the built site via Sphinx's `html_extra_path` -- see
the comment there. That also means this page never needs a raw
raw.githubusercontent.com/colab.research.google.com/github/... URL (which
requires the source repository to stay public): both links are same-origin,
so they keep working after the repository goes private, same as the
JupyterLite notebook and its data already do.

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
# Not "../../downloads/chapter_02/..." -- book/downloads/ is excluded from
# the Jupyter Book build (see book/_config.yml) and only exists as a
# raw-GitHub-served artifact for older chapters; this served copy instead
# comes from book/lite/files/ (see LITE_FILES_PORTABLE_COPY_PATH in
# scripts/generate_exercise_02_notebook.py), which `jupyter lite build`
# already copies into the site verbatim, same-origin.
DOWNLOAD_URL = "../../lite/files/exercise_02_portable.ipynb"


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

**<a href="{LITE_URL}">Open Exercise 2</a>**

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
