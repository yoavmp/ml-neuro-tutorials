#!/usr/bin/env python3
"""Offline precomputation of Exercise 7 Interactive Activity 2's
(learning rate x tree depth x tree count) grid (WP65, "Explore the Boosting
Parameters").

Historically this grid was recomputed live, inside the notebook's own
Activity 2 cell, every time that cell ran (18 `GradientBoostingRegressor`
fits). This script moves that computation offline: it reproduces the
notebook's own Section 1 data load and splits
(``scripts/generate_exercise_07_notebook.py``'s ``wp46-104-load`` cell) byte
-for-byte -- same same-origin CSV
(``book/lite/files/data/abide_age_brain.csv``), same natural fsCT_* column
order (from that CSV's own sidecar manifest, the same source
``generate_exercise_07_notebook.py`` embeds as ``_ABIDE_LITE_FEATURES``), and
the exact same two ``train_test_split`` calls -- then fits the same 18
(``EXPLORER_LR_GRID`` x ``EXPLORER_DEPTH_GRID``) models on the fitting subset
only and reads every tree-count step from a single fit's ``staged_predict``,
exactly as Activity 2 itself always has. The grids (learning rate, depth,
n_trees) are imported directly from ``generate_exercise_07_notebook`` so the
cache and the notebook can never drift apart silently.

The locked outer test set (``X_test``/``y_test``) is split out, matched to
the notebook's own split exactly, and then never read again -- this script
only ever fits on ``X_fit``/``y_fit`` and scores on ``X_val``/``y_val``.

The committed JSON result
(``scripts/exercise_07_explorer_cache_result.json``) is what
``generate_exercise_07_notebook.py`` embeds as a literal dict
(``_EXPLORER_CACHE``) in the notebook's first, collapsed setup cell, so
Activity 2's own cell only ever builds controls and redraws saved results --
rerunning it fits nothing, in JupyterLite, local Jupyter, or Colab alike (the
same embedded literal ships in the portable notebook, with no dependency on
any repository file at notebook-run time).

Usage::

    python scripts/generate_exercise_07_explorer_cache.py --run     # offline; writes JSON
    python scripts/generate_exercise_07_explorer_cache.py --check   # offline; re-validate

Asserted by ``tests/test_exercise_07_explorer_cache.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.csv"
DATA_SIDECAR = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.manifest.json"
RESULT_PATH = REPO_ROOT / "scripts" / "exercise_07_explorer_cache_result.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_exercise_07_notebook import (  # noqa: E402
    EXPLORER_DEPTH_GRID,
    EXPLORER_LR_GRID,
    EXPLORER_N_TREES_GRID,
)

# Matches scripts/generate_exercise_07_notebook.py's wp46-104-load cell
# exactly -- the notebook's own, original data split.
OUTER_TEST_SIZE, OUTER_RANDOM_STATE = 0.25, 42
DEV_TEST_SIZE, DEV_RANDOM_STATE = 0.25, 7


def _grid_key(lr: float, depth: int) -> str:
    return f"{lr}|{depth}"


def _load_splits():
    import pandas as pd
    from sklearn.model_selection import train_test_split

    sidecar = json.loads(DATA_SIDECAR.read_text())
    features = sidecar["predictor_columns"]

    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["age"])
    X = df[features].to_numpy(float)
    y = df["age"].to_numpy(float)
    groups = df["group"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=OUTER_TEST_SIZE, random_state=OUTER_RANDOM_STATE, stratify=groups
    )
    del X_test, y_test, groups_test  # locked outer test: split out, never read again

    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_TEST_SIZE, random_state=DEV_RANDOM_STATE, stratify=groups_train
    )
    return len(features), X_fit, X_val, y_fit, y_val


def build_cache() -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error

    t0 = time.time()
    n_features, X_fit, X_val, y_fit, y_val = _load_splits()
    max_trees = max(EXPLORER_N_TREES_GRID)

    grid: dict[str, Any] = {}
    for lr in EXPLORER_LR_GRID:
        for depth in EXPLORER_DEPTH_GRID:
            model = GradientBoostingRegressor(
                learning_rate=lr, max_depth=depth, n_estimators=max_trees, random_state=42
            ).fit(X_fit, y_fit)

            train_by_stage = list(model.staged_predict(X_fit))
            val_by_stage = list(model.staged_predict(X_val))

            train_mse = [round(float(mean_squared_error(y_fit, train_by_stage[n - 1])), 6) for n in EXPLORER_N_TREES_GRID]
            val_mse = [round(float(mean_squared_error(y_val, val_by_stage[n - 1])), 6) for n in EXPLORER_N_TREES_GRID]
            grid[_grid_key(lr, depth)] = {"trainMse": train_mse, "valMse": val_mse}

    return {
        "schemaVersion": 1,
        "generated_by": "scripts/generate_exercise_07_explorer_cache.py --run",
        "source": {"dataFile": "book/lite/files/data/abide_age_brain.csv", "manifestSha256": json.loads(DATA_SIDECAR.read_text())["sha256"]},
        "split": {
            "outer": {"test_size": OUTER_TEST_SIZE, "random_state": OUTER_RANDOM_STATE},
            "dev": {"test_size": DEV_TEST_SIZE, "random_state": DEV_RANDOM_STATE},
            "nFit": int(len(y_fit)),
            "nVal": int(len(y_val)),
            "featureCount": n_features,
        },
        "lockedTestExcluded": True,
        "learningRateGrid": EXPLORER_LR_GRID,
        "depthGrid": EXPLORER_DEPTH_GRID,
        "nTreesGrid": EXPLORER_N_TREES_GRID,
        "grid": grid,
        "runtimeSeconds": round(time.time() - t0, 1),
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_run() -> int:
    data = build_cache()
    text = serialize(data)
    RESULT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_summary(data)
    return 0


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if data.get("lockedTestExcluded") is not True:
        problems.append("lockedTestExcluded must be true")
    other_keys = [k for k in data if k != "lockedTestExcluded"]
    if any("test" in k.lower() for k in other_keys):
        problems.append("no field besides lockedTestExcluded may mention 'test'")

    if data.get("learningRateGrid") != EXPLORER_LR_GRID:
        problems.append("learningRateGrid does not match generate_exercise_07_notebook.EXPLORER_LR_GRID")
    if data.get("depthGrid") != EXPLORER_DEPTH_GRID:
        problems.append("depthGrid does not match generate_exercise_07_notebook.EXPLORER_DEPTH_GRID")
    if data.get("nTreesGrid") != EXPLORER_N_TREES_GRID:
        problems.append("nTreesGrid does not match generate_exercise_07_notebook.EXPLORER_N_TREES_GRID")

    lr_grid = data.get("learningRateGrid", [])
    depth_grid = data.get("depthGrid", [])
    n_trees_grid = data.get("nTreesGrid", [])
    grid = data.get("grid", {})
    if len(grid) != len(lr_grid) * len(depth_grid):
        problems.append("grid must have one entry per (learning_rate, depth) combination")

    for lr in lr_grid:
        for depth in depth_grid:
            key = _grid_key(lr, depth)
            entry = grid.get(key)
            if entry is None:
                problems.append(f"grid missing entry for learning_rate={lr}, depth={depth}")
                continue
            train_mse, val_mse = entry.get("trainMse", []), entry.get("valMse", [])
            if len(train_mse) != len(n_trees_grid) or len(val_mse) != len(n_trees_grid):
                problems.append(f"{key}: trainMse/valMse length must match nTreesGrid")
                continue
            if any(v < 0 for v in train_mse + val_mse):
                problems.append(f"{key}: negative MSE")
            for a, b in zip(train_mse, train_mse[1:]):
                if b > a + 1e-6:
                    problems.append(f"{key}: training MSE increased relative to a smaller tree count (not monotone non-increasing)")

    n_fit, n_val = data.get("split", {}).get("nFit"), data.get("split", {}).get("nVal")
    if None in (n_fit, n_val):
        problems.append("split.nFit/nVal missing")

    return problems


def cmd_check() -> int:
    if not RESULT_PATH.exists():
        print(f"ERROR: {RESULT_PATH} missing; run --run first.", file=sys.stderr)
        return 1
    data = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    problems = validate(data)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {RESULT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(data)
    return 0


def _print_summary(data: dict[str, Any]) -> None:
    print(
        f"grid: {len(data['learningRateGrid'])} learning rates x {len(data['depthGrid'])} depths x "
        f"{len(data['nTreesGrid'])} tree counts (n_fit={data['split']['nFit']}, n_val={data['split']['nVal']})"
    )
    best_val_mse = None
    best_key = None
    for key, entry in data["grid"].items():
        for n, v in zip(data["nTreesGrid"], entry["valMse"]):
            if best_val_mse is None or v < best_val_mse:
                best_val_mse, best_key = v, (key, n)
    print(f"best validation MSE={best_val_mse:.2f} at (learning_rate|depth)={best_key[0]}, n_trees={best_key[1]}")
    print(f"runtime: {data.get('runtimeSeconds')}s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="recompute the grid (offline, local CSV) and write the JSON cache")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON cache (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
