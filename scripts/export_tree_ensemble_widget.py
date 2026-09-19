#!/usr/bin/env python3
"""Deterministic ensemble-comparison audit + widget export for Exercise 6's
"One Tree or Many?" activity (WP29, sections 4-5).

Compares a single regression tree, bagging, and a Random Forest across five
deterministic training replicates. Each replicate draws a fixed 70% of the
dev-split fitting partition (``book/config/abide_modeling.json``'s
``decision_tree.dev_split``, identical to ``knn.dev_split`` /
``regularization.dev_split``) without replacement at a predefined seed; every
model in a replicate trains on the identical subset and is scored on the
identical fixed validation partition (n_val=189). The outer test set is
never touched. Bagging and the Random Forest additionally perform their own
internal bootstrap sampling; the Random Forest also randomizes the feature
subset considered at each split (``max_features``).

This script both recomputes the audit (replicate seeds, participant counts,
model settings, MSE, R2, ensemble-size curves, mean and variability across
replicates) and writes the browser widget's data artifact -- the same JSON
serves both roles, since every number the widget displays is already part of
the audit.

Two ``max_features`` candidates for the Random Forest are computed and
printed for the record (``--audit-max-features``): ``round(sqrt(p))=19`` and
``p // 3 = 120``. The manifest's declared setting (19) was fixed before
either candidate's validation outcome was known, not chosen afterward to
favor Random Forest.

Usage::

    python scripts/export_tree_ensemble_widget.py --refresh   # network; writes JSON
    python scripts/export_tree_ensemble_widget.py --check     # offline; re-validate

Asserted by ``tests/test_export_tree_ensemble_widget_data.py``.
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
    bundle_columns,
    feature_matrix,
    load_modeling_frame,
)

OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "tree_ensemble_compare.json"
DT = MANIFEST["decision_tree"]
RECIPE = DT["canonical_recipe"]
DEV_SPLIT = DT["dev_split"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
ENSEMBLE = DT["ensemble"]


def _splits(frame: Any):
    from sklearn.model_selection import train_test_split

    cols = bundle_columns(RECIPE["bundle"], RECIPE["measures"], available=frame.columns)
    assert_brain_only(cols)
    X, y, _ = feature_matrix(frame, RECIPE["bundle"], RECIPE["measures"], DT["target"])
    groups = frame.loc[frame[DT["target"]].notna(), "group"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"], stratify=groups_train
    )
    return cols, X, y, X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val


def _replicate_indices(n_pool: int, seed: int, fraction: float):
    import numpy as np

    n_rep = int(round(fraction * n_pool))
    rng = np.random.RandomState(seed)
    return rng.choice(n_pool, size=n_rep, replace=False)


def build_data(audit_max_features: bool = False) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import BaggingRegressor, RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.tree import DecisionTreeRegressor

    t0 = time.time()
    frame = load_modeling_frame()
    cols, X, y, X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val = _splits(frame)

    tree_settings = ENSEMBLE["tree_settings"]
    n_trees_grid = ENSEMBLE["n_trees_grid"]
    max_features = ENSEMBLE["random_forest_max_features"]
    seeds = ENSEMBLE["replicate_seeds"]
    fraction = ENSEMBLE["replicate_fraction"]
    n_pool = len(y_fit)

    if audit_max_features:
        p_third = max(1, X.shape[1] // 3)
        print(f"candidate max_features: sqrt(p)={round(len(cols) ** 0.5)}  p/3={p_third}  (using {max_features})")

    replicates = []
    for seed in seeds:
        idx = _replicate_indices(n_pool, seed, fraction)
        Xi, yi = X_fit[idx], y_fit[idx]

        single = DecisionTreeRegressor(**tree_settings).fit(Xi, yi)
        root_feature = cols[int(single.tree_.feature[0])]
        root_threshold = round(float(single.tree_.threshold[0]), 4)
        single_pred = single.predict(X_val)

        bagging_by_n: dict[str, Any] = {}
        rf_by_n: dict[str, Any] = {}
        for n_trees in n_trees_grid:
            bag = BaggingRegressor(
                DecisionTreeRegressor(**tree_settings), n_estimators=n_trees, random_state=tree_settings["random_state"]
            ).fit(Xi, yi)
            bag_pred = bag.predict(X_val)
            bagging_by_n[str(n_trees)] = {
                "valMSE": round(float(mean_squared_error(y_val, bag_pred)), 4),
                "valR2": round(float(r2_score(y_val, bag_pred)), 6),
                "predictedValidation": [round(float(v), 3) for v in bag_pred],
            }

            rf = RandomForestRegressor(
                n_estimators=n_trees,
                max_features=max_features,
                random_state=tree_settings["random_state"],
                **{k: v for k, v in tree_settings.items() if k != "random_state"},
            ).fit(Xi, yi)
            rf_pred = rf.predict(X_val)
            rf_by_n[str(n_trees)] = {
                "valMSE": round(float(mean_squared_error(y_val, rf_pred)), 4),
                "valR2": round(float(r2_score(y_val, rf_pred)), 6),
                "predictedValidation": [round(float(v), 3) for v in rf_pred],
            }

        replicates.append(
            {
                "seed": seed,
                "nTrain": int(len(idx)),
                "rootSplit": {"feature": root_feature, "threshold": root_threshold},
                "singleTree": {
                    "valMSE": round(float(mean_squared_error(y_val, single_pred)), 4),
                    "valR2": round(float(r2_score(y_val, single_pred)), 6),
                    "predictedValidation": [round(float(v), 3) for v in single_pred],
                },
                "bagging": {"byNTrees": bagging_by_n},
                "randomForest": {"byNTrees": rf_by_n},
            }
        )

    def _summary_for(get_mse) -> dict[str, Any]:
        values = [get_mse(r) for r in replicates]
        return {
            "meanMSE": round(float(np.mean(values)), 4),
            "sdMSE": round(float(np.std(values)), 4),
            "values": [round(float(v), 4) for v in values],
        }

    summary_single = _summary_for(lambda r: r["singleTree"]["valMSE"])
    summary_bagging = {
        str(n): _summary_for(lambda r, n=n: r["bagging"]["byNTrees"][str(n)]["valMSE"]) for n in n_trees_grid
    }
    summary_rf = {
        str(n): _summary_for(lambda r, n=n: r["randomForest"]["byNTrees"][str(n)]["valMSE"]) for n in n_trees_grid
    }

    return {
        "schemaVersion": 1,
        "activity": "tree-ensemble-compare",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "target": {"name": DT["target"], "label": "Age at scan", "unit": "years"},
        "featureRecipe": {"bundle": RECIPE["bundle"], "measures": RECIPE["measures"], "featureCount": len(cols)},
        "split": {
            "outerHoldout": {**HOLDOUT_SPLIT, "nTrain": int(len(y_train)), "nTest": int(len(y_test))},
            "devSplit": {**DEV_SPLIT, "nFit": int(len(y_fit)), "nVal": int(len(y_val))},
        },
        "settings": {
            "replicateFraction": fraction,
            "replicatePoolSize": n_pool,
            "treeSettings": tree_settings,
            "randomForestMaxFeatures": max_features,
        },
        "nTreesGrid": n_trees_grid,
        "observedValidation": [round(float(v), 3) for v in y_val],
        "replicates": replicates,
        "summary": {
            "singleTree": summary_single,
            "bagging": summary_bagging,
            "randomForest": summary_rf,
        },
        "runtimeSeconds": round(time.time() - t0, 1),
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_refresh() -> int:
    data = build_data(audit_max_features=True)
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
    n_val = data.get("split", {}).get("devSplit", {}).get("nVal")
    if len(data.get("observedValidation", [])) != n_val:
        problems.append("observedValidation length must equal split.devSplit.nVal")
    reps = data.get("replicates", [])
    if len(reps) < 3:
        problems.append("expected multiple deterministic replicates")
    for r in reps:
        if len(r["singleTree"]["predictedValidation"]) != n_val:
            problems.append(f"replicate seed={r['seed']}: singleTree prediction length mismatch")
        for n in data.get("nTreesGrid", []):
            for family in ("bagging", "randomForest"):
                entry = r[family]["byNTrees"].get(str(n))
                if entry is None or len(entry["predictedValidation"]) != n_val:
                    problems.append(f"replicate seed={r['seed']} {family} n={n}: prediction length mismatch")
    summary = data.get("summary", {})
    bagging_sd = [summary["bagging"][str(n)]["sdMSE"] for n in data.get("nTreesGrid", [])]
    if bagging_sd and bagging_sd[-1] > summary["singleTree"]["sdMSE"]:
        problems.append("bagging at the largest n_trees should have lower MSE variability than the single tree")
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
    print(f"=== single tree: mean MSE={data['summary']['singleTree']['meanMSE']:.1f} "
          f"sd={data['summary']['singleTree']['sdMSE']:.1f} ===")
    print("n_trees   bagging(mean,sd)      RF(mean,sd)")
    for n in data["nTreesGrid"]:
        b = data["summary"]["bagging"][str(n)]
        r = data["summary"]["randomForest"][str(n)]
        print(f"{n:7d}   {b['meanMSE']:6.2f} {b['sdMSE']:5.2f}        {r['meanMSE']:6.2f} {r['sdMSE']:5.2f}")
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
