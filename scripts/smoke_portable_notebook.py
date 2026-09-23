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
  workflow runs and prints its R-squared; the fixed-k=20 KNN workflow (reusing
  the same split) runs and prints its own held-out R-squared; the from-scratch
  empirical k=1..N_fit curve runs and verifies the k=N_fit endpoint; the
  learning curve prints n/p.
* ``chapter_03/exercise_03_portable.ipynb`` -- the same brain table, diagnosis
  (`group`) as target; the fixed-C=1.0 honest logistic-regression workflow
  runs and prints its confusion matrix, accuracy, and AUC; the editable
  threshold and class-imbalance demo cells run.
* ``chapter_04/exercise_04_portable.ipynb`` -- the same brain table, `age` as
  target, the same fixed 360-column KNN recipe and outer split as Exercise 2;
  the fixed-k=20 cross-validation workflow runs and prints its per-fold and
  mean MSE; the training/validation tuning cell runs and prints the
  training-selected and validation-selected k; the one-time test-reveal cell
  runs (its saved output is intentionally absent from the committed portable
  notebook -- see its banner cell); the nested-cross-validation cell runs and
  prints its per-fold selected k and mean outer-test MSE.
* ``chapter_05/exercise_05_portable.ipynb`` (WP33) -- the same brain table;
  cross-validated KNN, ridge, and lasso workflows run and print their
  selected k / alpha and validation MSE; the frontal-bundle forward feature
  selection cell runs and prints its selected feature count and CV MSE.
* ``chapter_06/exercise_06_portable.ipynb`` (WP33) -- the same brain table;
  the greedy-split search, the fixed-depth-3 tree fit, the depth-sweep
  table, and the bagging/Random-Forest fair comparison all run and print
  their MSE/AUC summaries.
* ``chapter_07/exercise_07_portable.ipynb`` (WP33) -- the same brain table;
  the stage-by-stage boosting reproduction, the CV-tuned gradient-boosting
  pipeline, and the tree-model comparison all run and print their selected
  settings and locked-test metrics.
* ``chapter_08/exercise_08_portable.ipynb`` (WP33; section 8 revised by
  WP34) -- the same brain table; the projection-activity reproduction, the
  standardized-PCA fit (explained variance), the research-example K-means
  fit, and the CV-tuned PCA + KNN pipeline (with its raw-feature KNN
  comparison) all run and print their audited numbers.
* ``chapter_09/exercise_09_portable.ipynb`` (WP34) -- the same brain table;
  the PCR/PLS and SVM synthetic-data reproductions, and the nested-cross-
  validation comparison of five models (standardized OLS, PCR, PLS, linear
  SVR, RBF SVR), all run and print their audited numbers.

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
            "n_features = 360",
            "held-out R^2 = 0.469",
            "k = 20",
            "held-out R^2 = 0.664",
            "fitting participants (N_fit) = 564   validation participants (N_val) = 189",
            "every validation prediction equals the fitting-set mean",
            "n_features (p) = 10",
        ),
    },
    "chapter_03": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
        "expect": (
            "463 autism (group=1), 541 control (group=2)",
            "n_train = 753   n_test = 251   n_features = 360",
            "accuracy    = 0.546",
            "AUC         = 0.569",
            "AUC is unchanged by the threshold: 0.569",
            "cohort: 400 participants (360 control, 40 autism)",
        ),
    },
    "chapter_04": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 1446 columns",
            "360 predictors, fixed before this lesson",
            "n_train = 753   n_test = 251   n_features = 360",
            "mean MSE = 33.8   (sd 5.4)",
            "n_fit = 564   n_val = 189",
            "training-selected k   = 1",
            "validation-selected k = 25",
            "validation-selected  k =  25   test MSE = 32.6   test R^2 = 0.651",
            "mean outer-test MSE = 33.4   (sd 7.5)",
            "selected k per outer fold: [15, 12, 10, 18, 15]",
        ),
    },
    "chapter_05": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_05" / "exercise_05_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 1446 columns",
            "n_train = 753   n_test = 251   n_features = 360",
            "best k by cross-validation: 80",
            "ridge best alpha = 562.3   validation MSE = 22.3   nonzero = 360",
            "lowest cross-validation MSE at 17 features (MSE = 56.4)",
        ),
    },
    "chapter_06": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_06" / "exercise_06_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 1446 columns",
            "360 predictors",
            "n_fit = 564   n_val = 189   n_test = 251 (test set untouched in this notebook)",
            "leaves = 8   depth = 3",
            "best Brain measure 1 threshold = 5.92  (reduction = 38.35)",
            "eligible = 1004   development = 753   outer test (excluded) = 251",
        ),
    },
    "chapter_07": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_07" / "exercise_07_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 1446 columns",
            "360 predictors",
            "n_fit = 564   n_val = 189   n_train (development) = 753   n_test = 251 (locked; read once, in section 6)",
            "stage 0 prediction (training mean) = 8.454",
            "selected settings: {'learning_rate': 0.1, 'n_estimators': 200, 'max_depth': 3}  (mean CV MSE = 27.2)",
            "locked-test MSE = 32.4   locked-test R2 = 0.653  (evaluated once)",
        ),
    },
    "chapter_08": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_08" / "exercise_08_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 1446 columns",
            "360 cortical-thickness predictors",
            "PC1 explained variance = 36.1%   PC2 explained variance = 5.9%",
            "cumulative explained variance through PC50 = 70.2%",
            "selected: n_components=20, k=10  (mean CV MSE = 24.8)",
            "raw-feature KNN selected: k=5  (mean CV MSE = 35.4)",
        ),
    },
    "chapter_09": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_09" / "exercise_09_portable.ipynb",
        "expect": (
            "data table: 1004 participants x 360 cortical-thickness predictors",
            "mean outer-fold performance (5 outer folds, nested cross-validation):",
            "Standardized OLS     mean MSE = 49.1   mean R2 = +0.427",
            "RBF SVR              mean MSE = 20.4   mean R2 = +0.772",
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
