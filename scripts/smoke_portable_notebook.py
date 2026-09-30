#!/usr/bin/env python3
"""Execute the portable notebook(s) outside the repository and check key outputs.

Copies each portable notebook into a fresh temporary directory (so no
repository-relative path can accidentally work), runs every cell with a clean
kernel via ``nbclient``, and asserts no cell raised and that a few deterministic
strings appear in the output.

Notebooks and their expected strings:

* chapter_01 is intentionally absent -- see the comment above its old ``SMOKE``
  entry for why (an ipywidgets.Output()/nbclient hang, pre-existing since
  WP41 for chapter_02's own equivalent widget, not introduced or fixed here).
* chapter_03 is intentionally absent (WP44) -- see the comment above its old
  ``SMOKE`` entry for why (its guarded model-fit cell correctly, by design,
  raises an actionable ``RuntimeError`` on the unmodified distributed
  template, since Section 3's FEATURES/X-y/split activities are intentionally
  left blank; this script's ``client.execute()`` call has no
  `on_notebook_start=` retry-past-an-expected-error mode, so the whole run
  aborts there, before ever reaching the confusion-matrix/AUC cells).
* ``chapter_02/exercise_02_portable.ipynb`` -- the merged modelling table loads
  with 1004 participants and 360 brain predictors; the held-out linear-
  regression workflow runs and prints its R-squared; the guarded KNN-check
  cell (a student fill-in-the-blank exercise, correctly blank in the
  distributed portable notebook) prints its "not complete yet" guard message
  rather than a result; the from-scratch empirical k=1..N_fit curve runs and
  prints its fitting/validation participant counts and the validation-
  optimal k. Section 8's own "k = {k} model complexity" print is not checked
  here: it runs inside an ``ipywidgets.Output()`` context, whose captured
  text is stored in the widget's own comm-synced state, not in the cell's
  regular ``outputs`` list that ``_all_output_text()`` below reads -- the
  same structural gap chapter_01's exclusion above is about, not something
  this WP's fix can check for without changing that extraction method.
* chapter_04 and chapter_05 are intentionally absent (WP45) -- see the
  comment above their old ``SMOKE`` entries for why (each notebook's
  Section 2/4 predefined-comparison or split-stability activity uses an
  ``ipywidgets.Output()`` widget as a context manager, the same pattern
  documented to hang ``nbclient`` with no real frontend attached; the same
  numbers are verified instead by directly executing the reference
  notebook's cell sources in
  ``tests/test_exercise_04_reference_execution.py`` and
  ``tests/test_exercise_05_reference_execution.py``).
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
    # chapter_01 is intentionally absent: WP42 migrated Exercise 1 to a
    # JupyterLite-native notebook whose interactive widgets use
    # ipywidgets.Output() as a context manager (the retention explorer and
    # histogram widgets), historically believed to hang nbclient's real ZMQ
    # kernel indefinitely with no frontend attached to acknowledge the widget
    # comm handshake. This WP found chapter_02's own equivalent Section 8
    # widget (the same Output()-context pattern) runs to completion cleanly
    # in real CI without hanging, so that specific claim about chapter_02 no
    # longer holds (whatever the earlier bounded-run finding was, it is not
    # reproducing now) -- chapter_01 itself was not re-verified, so its
    # exclusion is left in place rather than assumed fixed too.
    "chapter_02": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
        "expect": (
            "1004 participants, 360 brain predictors",
            "n_train = 753   n_test = 251",
            "held-out R^2 = 0.469",
            "held-out MSE = 49.6",
            "Not complete yet: define knn_pred, knn_r2, and knn_mse above first.",
            "fitting participants = 564   validation participants = 189",
            "k with lowest validation error = 17",
        ),
    },
    # chapter_03 is intentionally absent: WP44 migrated Exercise 3 to a
    # JupyterLite-native notebook whose Section 3 (FEATURES, X/y, and the
    # train/test split) is now a genuine student fill-in-the-blank sequence
    # rather than fully worked code -- confirmed live (WP44): a bounded run
    # of the unmodified distributed template against this script correctly
    # raises the guarded, actionable RuntimeError
    # ("X_train/X_test/y_train/y_test are not defined yet...") at the given
    # model-fit cell, which this script's plain client.execute() treats as a
    # fatal error and aborts on, before ever reaching the confusion-matrix,
    # ROC/AUC, threshold, or imbalance cells. This is not an
    # ipywidgets.Output()/nbclient hang (no hang occurs here, unlike
    # chapter_01's exclusion above) -- it is a structural mismatch between
    # this script's "run everything, check solved output" design and a
    # notebook whose middle section is deliberately left blank. The same
    # numeric results this script would have checked are already verified,
    # correctly (executing the completed reference notebook, not the blank
    # student template), by tests/test_exercise_03_reference_execution.py.
    # chapter_04 and chapter_05 are intentionally absent: WP45 migrated both
    # to JupyterLite-native notebooks whose Section 4 (chapter_04, the "One
    # Split or Several Folds?" activity) and Section 2 (chapter_05, the
    # predefined feature-set comparison) each use an ipywidgets.Output()
    # widget as a context manager -- the same pattern WP41's maintainer
    # guide (section 8) documents as hanging nbclient's real ZMQ kernel
    # indefinitely, with no real frontend attached to acknowledge the widget
    # comm handshake (chapter_01's own exclusion above is the precedent).
    # The same numbers this script would have checked are already verified,
    # correctly, by directly executing the completed reference notebook's
    # cell sources (not nbclient) in
    # tests/test_exercise_04_reference_execution.py and
    # tests/test_exercise_05_reference_execution.py.
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
    "chapter_10": {
        "path": REPO_ROOT / "book" / "downloads" / "chapter_10" / "exercise_10_portable.ipynb",
        "expect": (
            "1004 participants, 360 cortical-thickness columns",
            "10299 sensor windows, 30 participants, 6 activities",
            "Ordinary             mean validation accuracy at k=5: 0.894",
            "Participant-grouped  mean validation accuracy at k=5: 0.831",
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
