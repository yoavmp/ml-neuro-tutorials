#!/usr/bin/env python3
"""Execute the portable notebook outside the repository and check key outputs.

Copies ``book/downloads/chapter_01/exercise_01_portable.ipynb`` into a fresh
temporary directory (so no repository-relative path can accidentally work),
runs every cell with a clean kernel via ``nbclient``, and asserts:

* no cell raised;
* the ABIDE-II table still loads as 1114 x 13 (the WP09 curated slice);
* the IQR range-check still flags 56 of 1114 ages.

Needs network access (the notebook downloads the pinned ABIDE-II CSV). Used by
CI and runnable locally:

    .venv/bin/python scripts/smoke_portable_notebook.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTABLE = REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb"

EXPECTED_SUBSTRINGS = (
    "Data table shape: (1114, 13)",
    "56 of 1114 participants flagged",
)


def _all_output_text(nb) -> str:
    parts: list[str] = []
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


def main() -> int:
    if not PORTABLE.exists():
        print(f"ERROR: {PORTABLE} not found; run build_portable_notebook.py --write", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="portable-smoke-") as tmp:
        work = Path(tmp) / PORTABLE.name
        shutil.copy2(PORTABLE, work)
        nb = nbformat.read(work, as_version=4)
        client = NotebookClient(
            nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": tmp}}
        )
        client.execute()

    errors = [
        out
        for cell in nb.cells
        if cell.get("cell_type") == "code"
        for out in cell.get("outputs", [])
        if out.get("output_type") == "error"
    ]
    if errors:
        for out in errors:
            print("\n".join(out.get("traceback", [])), file=sys.stderr)
        print(f"FAIL: portable notebook raised {len(errors)} error(s)", file=sys.stderr)
        return 1

    text = _all_output_text(nb)
    missing = [s for s in EXPECTED_SUBSTRINGS if s not in text]
    if missing:
        print(f"FAIL: expected output not found: {missing}", file=sys.stderr)
        print(text[:4000], file=sys.stderr)
        return 1

    executed = sum(
        1
        for c in nb.cells
        if c.get("cell_type") == "code" and c.get("execution_count")
    )
    print(f"OK: portable notebook executed cleanly ({executed} code cells, key values matched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
