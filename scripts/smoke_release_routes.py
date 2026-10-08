#!/usr/bin/env python3
"""Targeted artifact smoke checks for the change-aware release gate (WP50).

For each given exercise number, against an *already-built*
`book/_build/html` directory, checks -- no browser, no kernel execution,
filesystem/JSON/text assertions only -- that:

* the transition route (`chapters/chapter_0N/exercise_0N.html`) was
  published, is non-empty HTML, and contains an "Open Exercise N" link whose
  href matches `book/config/exercise_manifest.json`'s own `liteUrl` for that
  exercise (resolved relative to the chapter page, as the browser resolves
  it) -- this is exactly the link WP49's transition page exists to provide,
  and the one thing a wording-only edit to that page could silently break;
* the JupyterLite template (`lite/files/exercise_0N.ipynb`) was published
  and is valid, non-empty notebook JSON;
* the portable download served at the transition page's own download link
  (`lite/files/exercise_0N_portable.ipynb` -- *not*
  `book/config/exercise_manifest.json`'s `fallbackDownloadablePath`, which
  is the repository-relative source path the generator writes to,
  `book/downloads/chapter_0N/...`; that directory is in
  `book/_config.yml`'s own `exclude_patterns` and is never copied into the
  built site at all -- confirmed live in WPs/reports/WP49_REPORT.md's own
  deployment-verification section, which checked `lite/files/
  exercise_03_portable.ipynb`, not a `downloads/` URL) was published and is
  valid, non-empty notebook JSON.

This is the "smoke-check the generated N notebook, transition route, and
portable download" step the WP50 spec's prose-only and exercise-scoped gate
rows both require, kept deliberately cheap (runs in well under a second per
exercise) so it adds negligible cost even on every push. The interactive
*behaviour* those routes serve (kernel start, widget interaction, grading,
download-with-edits) is covered by Playwright
(`exercise-0N-lite.spec.ts`/`chapterNN.spec.ts`) only when the gate actually
requires it -- see `scripts/classify_release_change.py`.

Usage:
    .venv/bin/python scripts/smoke_release_routes.py --build-dir book/_build/html --exercises 1,3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "exercise_manifest.json"


def _manifest_entry(n: int) -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text())
    for entry in manifest["exercises"]:
        if entry["number"] == n:
            return entry
    raise SystemExit(f"exercise {n} not found in {MANIFEST_PATH}")


def _check_valid_nonempty_notebook(path: Path, errors: list[str], label: str) -> None:
    if not path.is_file():
        errors.append(f"{label}: expected notebook not found at {path}")
        return
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: {path} is not valid JSON ({exc})")
        return
    if not nb.get("cells"):
        errors.append(f"{label}: {path} has no cells")


def smoke_check_exercise(n: int, build_dir: Path) -> list[str]:
    errors: list[str] = []
    entry = _manifest_entry(n)
    nn = f"{n:02d}"

    transition_html = build_dir / "chapters" / f"chapter_{nn}" / f"exercise_{nn}.html"
    if not transition_html.is_file():
        errors.append(f"exercise {n}: transition page not published at {transition_html}")
    else:
        html = transition_html.read_text(encoding="utf-8", errors="replace")
        if f"Open Exercise {n}" not in html:
            errors.append(f"exercise {n}: transition page does not contain the expected 'Open Exercise {n}' link text")
        lite_href_fragment = Path(entry["liteUrl"]).name  # e.g. "index.html?path=exercise_01.ipynb" -> compare by name/query
        if lite_href_fragment not in html and entry["liteUrl"] not in html:
            errors.append(
                f"exercise {n}: transition page does not reference its manifest liteUrl ({entry['liteUrl']!r})"
            )

    lite_template = build_dir / "lite" / "files" / f"exercise_{nn}.ipynb"
    _check_valid_nonempty_notebook(lite_template, errors, f"exercise {n} JupyterLite template")

    # Not book/config/exercise_manifest.json's `fallbackDownloadablePath`
    # (that's the repo-relative source path under book/downloads/, which
    # book/_config.yml excludes from the build entirely) -- this is the
    # actual served download URL the transition page links to.
    portable_path = build_dir / "lite" / "files" / f"exercise_{nn}_portable.ipynb"
    _check_valid_nonempty_notebook(portable_path, errors, f"exercise {n} portable download")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build-dir", default="book/_build/html")
    parser.add_argument("--exercises", required=True, help="comma-separated exercise numbers, e.g. 1,3")
    args = parser.parse_args()

    build_dir = Path(args.build_dir).resolve()
    if not build_dir.is_dir():
        raise SystemExit(f"--build-dir {build_dir} does not exist -- build the site first")

    numbers = [int(x) for x in args.exercises.split(",") if x.strip()]
    all_errors: list[str] = []
    for n in numbers:
        errors = smoke_check_exercise(n, build_dir)
        if errors:
            all_errors.extend(errors)
        else:
            print(f"OK: exercise {n} route, JupyterLite template, and portable download all smoke-check clean")

    if all_errors:
        print("FAILED:")
        for e in all_errors:
            print(f"  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
