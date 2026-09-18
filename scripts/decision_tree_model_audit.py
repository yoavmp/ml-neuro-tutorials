#!/usr/bin/env python3
"""Reproducible decision-tree audit for Exercise 6 (WP29).

Everything Exercise 6 teaches on the ABIDE age-prediction problem is computed
here first, offline and deterministically, so the notebook quotes audited
numbers rather than ad hoc in-notebook computation:

* **single tree** -- a shallow ``DecisionTreeRegressor`` on the two
  ``sensorimotor_core`` cortical-thickness features with the largest
  training-partition correlation with age (section 1: "One Regression
  Tree"), fit on the dev-split fitting partition and scored on its
  validation partition;
* **complexity curve** -- training and validation MSE across a grid of
  ``max_depth`` values on the full p=360 recipe, same dev split (section 3:
  "How Large Should the Tree Be?");
* **fair comparison** -- ``DecisionTreeRegressor`` vs. ``BaggingRegressor``
  vs. ``RandomForestRegressor`` with identical cross-validation folds and
  fixed, predeclared complexity settings on the full eligible cohort
  (section 6: "A Fair Model Comparison").

The ensemble-replicate activity (sections 4-5, "One Tree or Many?") is
audited separately by ``scripts/export_tree_ensemble_widget.py`` -- that
script's own output artifact already contains the full audit (replicate
seeds, participant counts, model settings, MSE, R2, ensemble-size curves,
mean and variability across replicates) needed for those sections, so it is
not duplicated here. The "Build a Tree Greedily" synthetic activity (section
2) is likewise self-contained in ``scripts/export_tree_greedy_widget.py``,
since it does not touch the ABIDE data this script loads.

Design rules, shared with the rest of this course's audits:

* every model is fit directly on brain features with no scaling (trees do
  not require it -- this is section 1's first stated fact);
* the outer test set (``protocol.holdout_split``) is never read by this
  script -- the dev split (``regularization.dev_split``, reused verbatim)
  is used throughout sections 1 and 3, and section 6's cross-validation
  runs on the full eligible cohort instead of the outer split.

Usage::

    python scripts/decision_tree_model_audit.py --run     # network; writes JSON
    python scripts/decision_tree_model_audit.py --check   # offline; re-validate

The committed JSON summary lives at
``scripts/decision_tree_model_audit_result.json`` and is asserted by
``tests/test_decision_tree_model_audit.py``.
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

RESULT_PATH = REPO_ROOT / "scripts" / "decision_tree_model_audit_result.json"
DT = MANIFEST["decision_tree"]
RECIPE = DT["canonical_recipe"]
DEV_SPLIT = DT["dev_split"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
SINGLE_TREE = DT["single_tree"]
COMPLEXITY = DT["complexity_curve"]
FAIR = DT["fair_comparison"]


def _outer_dev_splits(X: Any, y: Any, groups: Any):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"], stratify=groups_train
    )
    return X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val


def _single_tree(frame: Any) -> dict[str, Any]:
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.tree import DecisionTreeRegressor, export_text

    bundle = SINGLE_TREE["bundle"]
    cols = bundle_columns(bundle, SINGLE_TREE["measures"], available=frame.columns)
    assert_brain_only(cols)
    features = SINGLE_TREE["features"]
    for f in features:
        if f not in cols:
            raise ValueError(f"single_tree feature {f!r} is not in bundle {bundle!r}")

    X, y, _ = feature_matrix(frame, bundle, SINGLE_TREE["measures"], DT["target"])
    groups = frame.loc[frame[DT["target"]].notna(), "group"].to_numpy()
    idx = [cols.index(f) for f in features]

    X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val = _outer_dev_splits(X, y, groups)
    Xp_fit = X_fit[:, idx]
    Xp_val = X_val[:, idx]

    settings = SINGLE_TREE["settings"]
    tree = DecisionTreeRegressor(**settings).fit(Xp_fit, y_fit)
    pred_val = tree.predict(Xp_val)

    tree_text = export_text(tree, feature_names=features)
    leaf_ids = tree.apply(Xp_fit)
    import numpy as np

    leaf_counts = {int(k): int(v) for k, v in zip(*np.unique(leaf_ids, return_counts=True))}
    leaf_values = sorted({round(float(v), 2) for v in tree.tree_.value.flatten() if v != 0})

    return {
        "features": features,
        "settings": settings,
        "n_fit": int(len(y_fit)),
        "n_val": int(len(y_val)),
        "n_leaves": int(tree.get_n_leaves()),
        "depth": int(tree.get_depth()),
        "leaf_sample_counts": leaf_counts,
        "min_leaf_sample_count": min(leaf_counts.values()),
        "leaf_predicted_values": leaf_values,
        "val_mse": round(float(mean_squared_error(y_val, pred_val)), 4),
        "val_r2": round(float(r2_score(y_val, pred_val)), 6),
        "tree_text": tree_text,
    }


def _natural_order_columns(frame: Any) -> list[str]:
    # The notebook builds its feature list the same simple way every earlier
    # exercise does (`[c for c in BRAIN_COLS if c.startswith("fsCT_")]`),
    # i.e. the raw table's own column order, not scripts/abide_modeling_data
    # .py's canonical ROI-then-hemisphere `bundle_columns` order. For linear
    # models column order is immaterial, but a DecisionTreeRegressor's
    # best-split tie-breaking among this recipe's many highly correlated
    # cortical-thickness columns is order-sensitive -- so this audit matches
    # the notebook's own column order exactly, rather than recomputing a
    # result the notebook's executed cells would not reproduce.
    return [c for c in frame.columns if c.startswith("fsCT_")]


def _complexity_curve(frame: Any) -> dict[str, Any]:
    from sklearn.metrics import mean_squared_error
    from sklearn.tree import DecisionTreeRegressor

    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    present = frame[DT["target"]].notna()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, DT["target"]].to_numpy(dtype="float64")
    groups = frame.loc[frame[DT["target"]].notna(), "group"].to_numpy()
    X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val = _outer_dev_splits(X, y, groups)

    depths = COMPLEXITY["depth_grid"]
    train_mse, val_mse, n_leaves = [], [], []
    for depth in depths:
        t = DecisionTreeRegressor(
            max_depth=depth,
            min_samples_leaf=COMPLEXITY["min_samples_leaf"],
            random_state=COMPLEXITY["random_state"],
        ).fit(X_fit, y_fit)
        train_mse.append(round(float(mean_squared_error(y_fit, t.predict(X_fit))), 4))
        val_mse.append(round(float(mean_squared_error(y_val, t.predict(X_val))), 4))
        n_leaves.append(int(t.get_n_leaves()))

    best_i = int(min(range(len(val_mse)), key=lambda i: val_mse[i]))
    return {
        "p": len(cols),
        "n_fit": int(len(y_fit)),
        "n_val": int(len(y_val)),
        "depth_grid": depths,
        "train_mse": train_mse,
        "val_mse": val_mse,
        "n_leaves": n_leaves,
        "best_depth": depths[best_i],
        "best_depth_index": best_i,
        "best_val_mse": val_mse[best_i],
    }


def _fair_comparison(frame: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import BaggingRegressor, RandomForestRegressor
    from sklearn.model_selection import KFold, cross_val_score
    from sklearn.tree import DecisionTreeRegressor

    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    present = frame[DT["target"]].notna()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, DT["target"]].to_numpy(dtype="float64")

    cv = KFold(n_splits=5, shuffle=True, random_state=100)
    tree_settings = FAIR["tree_settings"]
    n_estimators = FAIR["n_estimators"]
    max_features = FAIR["random_forest_max_features"]

    models = {
        "single_tree": DecisionTreeRegressor(**tree_settings),
        "bagging": BaggingRegressor(
            DecisionTreeRegressor(**tree_settings), n_estimators=n_estimators, random_state=tree_settings["random_state"]
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=n_estimators,
            max_features=max_features,
            random_state=tree_settings["random_state"],
            **{k: v for k, v in tree_settings.items() if k != "random_state"},
        ),
    }

    out: dict[str, Any] = {}
    for name, model in models.items():
        fold_mse = -cross_val_score(model, X, y, cv=cv, scoring="neg_mean_squared_error", n_jobs=-1)
        fold_r2 = cross_val_score(model, X, y, cv=cv, scoring="r2", n_jobs=-1)
        out[name] = {
            "fold_mse": [round(float(v), 4) for v in fold_mse],
            "fold_r2": [round(float(v), 6) for v in fold_r2],
            "mean_mse": round(float(np.mean(fold_mse)), 4),
            "sd_mse": round(float(np.std(fold_mse)), 4),
            "mean_r2": round(float(np.mean(fold_r2)), 6),
        }
    return {
        "p": len(cols),
        "n": int(len(y)),
        "cv": FAIR["cv"],
        "tree_settings": tree_settings,
        "n_estimators": n_estimators,
        "random_forest_max_features": max_features,
        "models": out,
    }


def run_audit() -> dict[str, Any]:
    t0 = time.time()
    frame = load_modeling_frame()
    results: dict[str, Any] = {
        "generated_by": "scripts/decision_tree_model_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "single_tree": _single_tree(frame),
        "complexity_curve": _complexity_curve(frame),
        "fair_comparison": _fair_comparison(frame),
    }
    results["runtime_seconds"] = round(time.time() - t0, 1)
    return results


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_run() -> int:
    results = run_audit()
    text = serialize(results)
    RESULT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_summary(results)
    return 0


def validate(results: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if results.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    st = results.get("single_tree", {})
    if st.get("min_leaf_sample_count", 0) < SINGLE_TREE["settings"]["min_samples_leaf"]:
        problems.append("single_tree: a leaf has fewer samples than min_samples_leaf")
    if st.get("n_leaves", 0) < 2:
        problems.append("single_tree: tree collapsed to a single leaf")

    cc = results.get("complexity_curve", {})
    depths = cc.get("depth_grid", [])
    train_mse = cc.get("train_mse", [])
    val_mse = cc.get("val_mse", [])
    if len(depths) != len(train_mse) or len(depths) != len(val_mse) or not depths:
        problems.append("complexity_curve: depth_grid/train_mse/val_mse length mismatch")
    else:
        for i in range(1, len(train_mse)):
            if train_mse[i] > train_mse[i - 1] + 1e-6:
                problems.append(f"complexity_curve: train_mse increased at depth {depths[i]} (not monotone non-increasing)")
                break

    fc = results.get("fair_comparison", {})
    models = fc.get("models", {})
    for name in ("single_tree", "bagging", "random_forest"):
        if "mean_mse" not in models.get(name, {}):
            problems.append(f"fair_comparison.models.{name}: missing mean_mse")
    if models.get("bagging", {}).get("mean_mse", 0) >= models.get("single_tree", {}).get("mean_mse", 1e9):
        problems.append("fair_comparison: bagging should out-perform (lower MSE than) the single tree here")

    return problems


def cmd_check() -> int:
    if not RESULT_PATH.exists():
        print(f"ERROR: {RESULT_PATH} missing; run --run first.", file=sys.stderr)
        return 1
    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    problems = validate(results)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {RESULT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(results)
    return 0


def _print_summary(results: dict[str, Any]) -> None:
    st = results["single_tree"]
    print(f"=== single tree ({', '.join(st['features'])}) ===")
    print(f"  leaves={st['n_leaves']}  val MSE={st['val_mse']:.1f}  val R2={st['val_r2']:+.3f}")
    print()
    cc = results["complexity_curve"]
    print(f"=== complexity curve (p={cc['p']}): best depth = {cc['best_depth']} (val MSE={cc['best_val_mse']:.1f}) ===")
    print()
    fc = results["fair_comparison"]
    print("=== fair comparison (5-fold CV, full cohort) ===")
    for name, m in fc["models"].items():
        print(f"  {name:15s}  mean MSE={m['mean_mse']:.1f}  mean R2={m['mean_r2']:+.3f}")
    print(f"runtime: {results.get('runtime_seconds')}s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
