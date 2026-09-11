#!/usr/bin/env python3
"""Execute the portable notebook(s) outside the repository and check key outputs.

Copies each portable notebook into a fresh temporary directory (so no
repository-relative path can accidentally work), runs every cell with a clean
kernel via ``nbclient``, and asserts no cell raised and that a few deterministic
strings appear in the output.

Notebooks and their expected strings:

* ``chapter_01/exercise_01_portable.ipynb`` -- ABIDE-II table loads as
  1114 x 13; the complete-case retention example reports all 13 variables.
* ``chapter_02/exercise_02_portable.ipynb`` -- the merged modelling table loads
  with `age` available for all 1004 participants; the held-out linear-regression
  workflow runs and prints its R-squared; the learning curve prints n/p.
* ``chapter_03/exercise_03_portable.ipynb`` -- the same modelling table; the
  executable training-only cross-validation cell selects k=15 and the held-out
  KNN workflow at that k prints its R-squared; the from-scratch empirical
  k=1..N_fit curve runs and verifies the k=N_fit endpoint; the static
  honest-vs-invalid k_demo cell runs.

Needs network access (the notebooks download pinned public CSVs). Used by CI and
runnable locally:

    .venv/bin/python scripts/smoke_portable_notebook.py
    .venv/bin/python scripts/smoke_portable_notebook.py --notebook chapter_02
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parents[1]

SMOKE = {
    "chapter_01": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb",
        "expect": (
            "Data table shape: (1114, 13)",
            "Complete for all 13 variables",
        ),
    },
    "chapter_02": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
        "expect": (
            "age available for 1004 of 1004",
            "held-out R^2 =",
            "n_features (p) = 360",
        ),
    },
    "chapter_03": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
        "expect": (
            "age available for 1004 of 1004",
            "selected k = 15",
            "k = 15",
            "held-out R^2 = 0.649",
            "N_fit = 564   N_val = 189",
            "every validation prediction equals the fitting-set mean",
        ),
    },
}


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


def _run_one(key: str, spec: dict) -> int:
    path: Path = spec["path"]
    if not path.exists():
        print(f"ERROR: {path} not found; run build_portable_notebook.py --write", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix=f"portable-smoke-{key}-") as tmp:
        work = Path(tmp) / path.name
        shutil.copy2(path, work)
        nb = nbformat.read(work, as_version=4)
        client = NotebookClient(
            nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": tmp}}
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
        print(f"FAIL [{key}]: portable notebook raised {len(errors)} error(s)", file=sys.stderr)
        return 1

    text = _all_output_text(nb)
    missing = [s for s in spec["expect"] if s not in text]
    if missing:
        print(f"FAIL [{key}]: expected output not found: {missing}", file=sys.stderr)
        print(text[:4000], file=sys.stderr)
        return 1

    executed = sum(
        1 for c in nb.cells if c.get("cell_type") == "code" and c.get("execution_count")
    )
    print(f"OK [{key}]: portable notebook executed cleanly ({executed} code cells, key values matched)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--notebook", choices=(*SMOKE.keys(), "all"), default="all")
    args = parser.parse_args(argv)
    keys = list(SMOKE) if args.notebook == "all" else [args.notebook]
    rc = 0
    for key in keys:
        rc |= _run_one(key, SMOKE[key])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
