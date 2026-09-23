#!/usr/bin/env python3
"""Deterministic ABIDE-development-data grid + widget export for Exercise 7's
"Explore the Boosting Parameters" activity (WP32).

Uses only the fixed 564-participant fitting subset and 189-participant
validation subset from the outer development partition
(``book/config/abide_modeling.json``'s ``gradient_boosting.dev_split``,
identical to ``decision_tree.dev_split`` / ``knn.dev_split`` /
``regularization.dev_split``). The locked outer test set is never read by
this script.

For each (learning_rate, max_depth) pair in the precomputed grid, one
``GradientBoostingRegressor`` is fit once with the largest tree count in
``n_trees_grid`` (300); ``staged_predict`` then supplies every displayed
tree-count step's training/validation predictions from that single fit,
rather than refitting once per tree count (18 fits total, not 198).

This script both recomputes the audit (grid, metrics, cohort sizes,
disjointness) and writes the browser widget's data artifact.

Usage::

    python scripts/export_boosting_parameter_widget.py --refresh   # network; writes JSON
    python scripts/export_boosting_parameter_widget.py --check     # offline; re-validate

Asserted by ``tests/test_export_boosting_parameter_widget_data.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from abide_modeling_data import (  # noqa: E402
    MANIFEST,
    REPO_ROOT,
    assert_brain_only,
    load_modeling_frame,
)

OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "boosting_parameter_explorer.json"
GB = MANIFEST["gradient_boosting"]
RECIPE = GB["canonical_recipe"]
DEV_SPLIT = GB["dev_split"]


def _natural_order_columns(frame: Any) -> list[str]:
    # Matches the notebook's own FEATURES list (raw table order) and
    # gradient_boosting_model_audit.py's own _natural_order_columns --
    # identical reasoning to decision_tree_model_audit.py: a tree-based
    # model's best-split tie-breaking among this recipe's many highly
    # correlated cortical-thickness columns is order-sensitive.
    return [c for c in frame.columns if c.startswith("fsCT_")]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
PE = GB["parameter_explorer"]
LEARNING_RATE_GRID: list[float] = PE["learning_rate_grid"]
DEPTH_GRID: list[int] = PE["depth_grid"]
N_TREES_GRID: list[int] = PE["n_trees_grid"]
MAX_TREES = max(N_TREES_GRID)


def _splits(frame: Any):
    from sklearn.model_selection import train_test_split

    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    present = frame[GB["target"]].notna()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, GB["target"]].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    subjects = frame.loc[present, "subject"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    subjects_train, subjects_test = train_test_split(
        subjects, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val, subjects_fit, subjects_val = train_test_split(
        X_train, y_train, subjects_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"],
        stratify=groups_train,
    )
    return cols, X_fit, X_val, y_fit, y_val, subjects_fit, subjects_val, subjects_test


def build_data() -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error, r2_score

    t0 = time.time()
    frame = load_modeling_frame()
    cols, X_fit, X_val, y_fit, y_val, subjects_fit, subjects_val, subjects_test = _splits(frame)

    # Locked-test exclusion, proven by participant-set membership.
    fit_val_subjects = set(subjects_fit.tolist()) | set(subjects_val.tolist())
    test_subjects = set(subjects_test.tolist())
    if fit_val_subjects & test_subjects:
        raise RuntimeError("fitting/validation participants overlap the locked outer test set")

    grid: dict[str, Any] = {}
    for lr in LEARNING_RATE_GRID:
        for depth in DEPTH_GRID:
            model = GradientBoostingRegressor(
                n_estimators=MAX_TREES, learning_rate=lr, max_depth=depth, random_state=42
            ).fit(X_fit, y_fit)

            train_by_stage = list(model.staged_predict(X_fit))
            val_by_stage = list(model.staged_predict(X_val))

            by_n_trees: dict[str, Any] = {}
            for n in N_TREES_GRID:
                train_pred = train_by_stage[n - 1]
                val_pred = val_by_stage[n - 1]
                by_n_trees[str(n)] = {
                    "trainMSE": round(float(mean_squared_error(y_fit, train_pred)), 4),
                    "valMSE": round(float(mean_squared_error(y_val, val_pred)), 4),
                    "valR2": round(float(r2_score(y_val, val_pred)), 6),
                    "predictedValidation": [round(float(v), 3) for v in val_pred],
                }

            grid[f"{lr}|{depth}"] = {
                "learningRate": lr,
                "maxDepth": depth,
                "byNTrees": by_n_trees,
            }

    return {
        "schemaVersion": 1,
        "activity": "boosting-parameter-explorer",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "target": {"name": GB["target"], "label": "Age at scan", "unit": "years"},
        "featureRecipe": {"bundle": RECIPE["bundle"], "measures": RECIPE["measures"], "featureCount": len(cols)},
        "split": {
            "outerHoldout": HOLDOUT_SPLIT,
            "devSplit": {**DEV_SPLIT, "nFit": int(len(y_fit)), "nVal": int(len(y_val))},
        },
        "lockedTestExcluded": True,
        "learningRateGrid": LEARNING_RATE_GRID,
        "depthGrid": DEPTH_GRID,
        "nTreesGrid": N_TREES_GRID,
        "defaults": {
            "learningRate": PE["default_learning_rate"],
            "depth": PE["default_depth"],
            "nTrees": PE["default_n_trees"],
        },
        "observedValidation": [round(float(v), 3) for v in y_val],
        "grid": grid,
        "runtimeSeconds": round(time.time() - t0, 1),
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_refresh() -> int:
    data = build_data()
    text = serialize(data)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_summary(data)
    return 0


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if data.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    if data.get("lockedTestExcluded") is not True:
        problems.append("lockedTestExcluded must be true")

    n_val = data.get("split", {}).get("devSplit", {}).get("nVal")
    if len(data.get("observedValidation", [])) != n_val:
        problems.append("observedValidation length must equal split.devSplit.nVal")

    lr_grid = data.get("learningRateGrid", [])
    depth_grid = data.get("depthGrid", [])
    n_trees_grid = data.get("nTreesGrid", [])
    grid = data.get("grid", {})
    if len(grid) != len(lr_grid) * len(depth_grid):
        problems.append("grid must have one entry per (learning_rate, depth) combination")

    for lr in lr_grid:
        for depth in depth_grid:
            key = f"{lr}|{depth}"
            entry = grid.get(key)
            if entry is None:
                problems.append(f"grid missing entry for learning_rate={lr}, depth={depth}")
                continue
            by_n = entry.get("byNTrees", {})
            prev_val_mse = None
            prev_train_mse = None
            for n in n_trees_grid:
                point = by_n.get(str(n))
                if point is None or len(point.get("predictedValidation", [])) != n_val:
                    problems.append(f"{key} n={n}: missing or misaligned prediction array")
                    continue
                if point["trainMSE"] < 0 or point["valMSE"] < 0:
                    problems.append(f"{key} n={n}: negative MSE")
                if prev_train_mse is not None and point["trainMSE"] > prev_train_mse + 1e-6:
                    problems.append(f"{key} n={n}: training MSE increased relative to a smaller tree count (not monotone non-increasing)")
                prev_train_mse = point["trainMSE"]
                prev_val_mse = point["valMSE"]

    defaults = data.get("defaults", {})
    if defaults.get("learningRate") not in lr_grid:
        problems.append("defaults.learningRate is not in learningRateGrid")
    if defaults.get("depth") not in depth_grid:
        problems.append("defaults.depth is not in depthGrid")
    if defaults.get("nTrees") not in n_trees_grid:
        problems.append("defaults.nTrees is not in nTreesGrid")

    return problems


def cmd_check() -> int:
    if not OUT_PATH.exists():
        print(f"ERROR: {OUT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    problems = validate(data)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {OUT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(data)
    return 0


def _print_summary(data: dict[str, Any]) -> None:
    print(f"grid: {len(data['learningRateGrid'])} learning rates x {len(data['depthGrid'])} depths x "
          f"{len(data['nTreesGrid'])} tree counts")
    best_val_mse = None
    best_key = None
    for key, entry in data["grid"].items():
        for n, point in entry["byNTrees"].items():
            if best_val_mse is None or point["valMSE"] < best_val_mse:
                best_val_mse = point["valMSE"]
                best_key = (key, n)
    print(f"best validation MSE={best_val_mse:.2f} at (learning_rate|depth)={best_key[0]}, n_trees={best_key[1]}")
    print(f"runtime: {data.get('runtimeSeconds')}s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="run the audit (network) and write the JSON artifact")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
