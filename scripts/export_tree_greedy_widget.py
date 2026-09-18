#!/usr/bin/env python3
"""Deterministic synthetic dataset + greedy-split audit for Exercise 6's
"Build a Tree Greedily" activity (WP29).

The dataset is entirely synthetic -- 16 observations on two predictors
(X1, X2) and a continuous target, arranged in four "quadrants" (low/high on
each predictor) with a small deterministic per-point offset -- designed so
the greedy algorithm's root split is unambiguously on X1 (a large MSE
reduction over the best X2 split) and each of the two children's best split
is unambiguously on X2. This gives exactly three splitting rounds (root,
left child, right child) and four leaves.

This script recomputes, for every round (root / left child / right child):

* the active observations;
* every valid candidate threshold for each feature (the midpoints between
  that feature's distinct observed values among the active observations);
* the weighted split MSE and MSE reduction at every candidate threshold;
* the optimal feature, threshold, split MSE, and reduction.

The output, ``book/_static/widgets/data/tree_greedy_split.json``, is both
the browser widget's data artifact and this activity's committed
deterministic audit (there is no separate ABIDE-style audit script for a
synthetic dataset with no model-fitting decisions to record).

Usage::

    python scripts/export_tree_greedy_widget.py --refresh   # writes JSON
    python scripts/export_tree_greedy_widget.py --check     # re-validate

Asserted by ``tests/test_export_tree_greedy_widget_data.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "tree_greedy_split.json"

# --- the synthetic dataset ---------------------------------------------
_X1_LOW = [1.0, 2.0, 3.0, 4.0]
_X1_HIGH = [7.0, 8.0, 9.0, 10.0]
_X2_LOW = [1.0, 2.0, 3.0, 4.0]
_X2_HIGH = [7.0, 8.0, 9.0, 10.0]
_OFFSETS = [-1.0, -0.3, 0.3, 1.0]
_QUADRANT_MEANS = {
    ("low", "low"): 8.0,
    ("low", "high"): 18.0,
    ("high", "low"): 26.0,
    ("high", "high"): 40.0,
}
_QUADRANT_X1 = {"low": _X1_LOW, "high": _X1_HIGH}
_QUADRANT_X2 = {"low": _X2_LOW, "high": _X2_HIGH}


def build_observations() -> list[dict[str, Any]]:
    observations = []
    pid = 0
    for x1_level in ("low", "high"):
        for x2_level in ("low", "high"):
            mean = _QUADRANT_MEANS[(x1_level, x2_level)]
            for i in range(4):
                x1 = _QUADRANT_X1[x1_level][i]
                x2 = _QUADRANT_X2[x2_level][i]
                y = round(mean + _OFFSETS[i], 2)
                observations.append({"id": pid, "x1": x1, "x2": x2, "y": y})
                pid += 1
    return observations


def _mse(ys: list[float]) -> float:
    if not ys:
        return 0.0
    mean = sum(ys) / len(ys)
    return sum((v - mean) ** 2 for v in ys) / len(ys)


def _candidate_thresholds(values: list[float]) -> list[float]:
    uniq = sorted(set(values))
    return [round((uniq[i] + uniq[i + 1]) / 2, 4) for i in range(len(uniq) - 1)]


def _feature_candidates(active: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    parent_mse = round(_mse([o["y"] for o in active]), 6)
    n = len(active)
    values = [o[feature] for o in active]
    thresholds = _candidate_thresholds(values)
    split_mse, reduction, n_left, n_right = [], [], [], []
    for t in thresholds:
        left = [o["y"] for o in active if o[feature] <= t]
        right = [o["y"] for o in active if o[feature] > t]
        wmse = (len(left) / n) * _mse(left) + (len(right) / n) * _mse(right)
        split_mse.append(round(wmse, 6))
        reduction.append(round(parent_mse - wmse, 6))
        n_left.append(len(left))
        n_right.append(len(right))
    return {
        "thresholds": thresholds,
        "splitMSE": split_mse,
        "reduction": reduction,
        "nLeft": n_left,
        "nRight": n_right,
    }


def _round_summary(round_id: str, label: str, active: list[dict[str, Any]]) -> dict[str, Any]:
    parent_mse = round(_mse([o["y"] for o in active]), 6)
    candidates = {"x1": _feature_candidates(active, "x1"), "x2": _feature_candidates(active, "x2")}

    best = None
    for feature in ("x1", "x2"):
        c = candidates[feature]
        for i, red in enumerate(c["reduction"]):
            if best is None or red > best["reduction"]:
                best = {
                    "feature": feature,
                    "thresholdIndex": i,
                    "threshold": c["thresholds"][i],
                    "splitMSE": c["splitMSE"][i],
                    "reduction": red,
                    "nLeft": c["nLeft"][i],
                    "nRight": c["nRight"][i],
                }
    assert best is not None
    left_ys = [o["y"] for o in active if o[best["feature"]] <= best["threshold"]]
    right_ys = [o["y"] for o in active if o[best["feature"]] > best["threshold"]]
    best["leftMean"] = round(sum(left_ys) / len(left_ys), 3)
    best["rightMean"] = round(sum(right_ys) / len(right_ys), 3)

    return {
        "id": round_id,
        "label": label,
        "activeObservationIds": [o["id"] for o in active],
        "parentMSE": parent_mse,
        "candidates": candidates,
        "optimal": best,
    }


def build_data() -> dict[str, Any]:
    observations = build_observations()

    root_active = observations
    root = _round_summary("root", "Root node (all 16 observations)", root_active)
    opt = root["optimal"]

    left_active = [o for o in root_active if o[opt["feature"]] <= opt["threshold"]]
    right_active = [o for o in root_active if o[opt["feature"]] > opt["threshold"]]
    left = _round_summary(
        "left-child",
        f"Left child ({opt['feature'].upper()} <= {opt['threshold']})",
        left_active,
    )
    right = _round_summary(
        "right-child",
        f"Right child ({opt['feature'].upper()} > {opt['threshold']})",
        right_active,
    )

    return {
        "schemaVersion": 1,
        "activity": "tree-greedy-split",
        "syntheticDataNote": (
            "This dataset is synthetic: it was constructed to have a clear, learnable split "
            "structure, not drawn from real participants."
        ),
        "features": {
            "x1": {"name": "x1", "label": "X1"},
            "x2": {"name": "x2", "label": "X2"},
        },
        "observations": observations,
        "rounds": [root, left, right],
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
    if len(data.get("observations", [])) < 12 or len(data["observations"]) > 20:
        problems.append("observations count must be within [12, 20]")
    rounds = data.get("rounds", [])
    if len(rounds) != 3:
        problems.append("there must be exactly 3 rounds (root, left child, right child)")
    if rounds:
        if rounds[0]["optimal"]["feature"] != "x1":
            problems.append("root optimal split is expected to be on x1 for this dataset")
        for r in rounds[1:]:
            if r["optimal"]["feature"] != "x2":
                problems.append(f"round {r['id']}: optimal split is expected to be on x2 for this dataset")
        for r in rounds:
            for feature, c in r["candidates"].items():
                lengths = {len(c["thresholds"]), len(c["splitMSE"]), len(c["reduction"]), len(c["nLeft"]), len(c["nRight"])}
                if len(lengths) != 1:
                    problems.append(f"round {r['id']} feature {feature}: candidate array length mismatch")
                opt = r["optimal"]
                if opt["reduction"] < 0:
                    problems.append(f"round {r['id']}: optimal reduction is negative")
    return problems


def cmd_check() -> int:
    if not OUT_PATH.exists():
        print(f"ERROR: {OUT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    recomputed = build_data()
    if json.dumps(data, sort_keys=True) != json.dumps(recomputed, sort_keys=True):
        print("ERROR: committed artifact does not match a fresh recomputation.", file=sys.stderr)
        return 1
    problems = validate(data)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {OUT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(data)
    return 0


def _print_summary(data: dict[str, Any]) -> None:
    for r in data["rounds"]:
        opt = r["optimal"]
        print(
            f"{r['id']:12s} n={len(r['activeObservationIds']):2d}  parentMSE={r['parentMSE']:7.3f}  "
            f"optimal={opt['feature']}<= {opt['threshold']:.2f}  reduction={opt['reduction']:7.3f}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute and write the JSON artifact")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
