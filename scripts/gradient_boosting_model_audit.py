#!/usr/bin/env python3
"""Reproducible gradient-boosting audit for Exercise 7 (WP32).

Audits everything Exercise 7's non-widget code cells quote as numbers, so the
notebook reads audited results rather than computing them ad hoc:

* **sklearn example** (section 3) -- one short ``GradientBoostingRegressor``
  fit on the dev-split fitting partition, scored on its validation partition;
* **CV-tuning pipeline** (section 6) -- cross-validation restricted to the
  outer development partition (never the locked outer test), a fixed
  parameter grid (reduced from 27 to 12 candidates -- see
  ``book/config/abide_modeling.json``'s ``gradient_boosting.cv_pipeline`` for
  the predeclared runtime rule), selection by minimum mean CV MSE, refit on
  all development participants, and exactly one evaluation of the locked
  outer test set;
* **tree-based model comparison** (section 7) -- the selected gradient
  boosting model evaluated on the same locked test set, alongside the
  existing Exercise 6 single-tree and Random Forest numbers carried forward
  unchanged from ``scripts/decision_tree_model_audit_result.json`` (never
  retuned here).

The two interactive activities ("Build a Boosted Model" and "Explore the
Boosting Parameters") are audited separately by their own export scripts
(``scripts/export_boosting_step_widget.py``,
``scripts/export_boosting_parameter_widget.py``) since those artifacts
already contain everything those sections display.

Design rules, shared with the rest of this course's audits:

* the outer test set (``protocol.holdout_split``) is read exactly once, in
  the CV-tuning pipeline's final step, after every gradient-boosting setting
  has already been fixed from development-only cross-validation;
* participant disjointness between the development partition and the outer
  test set is proven by stable subject-id set membership, not merely by
  never reading a stored index;
* tree-based models are fit directly on brain features with no scaling.

Usage::

    python scripts/gradient_boosting_model_audit.py --run     # network; writes JSON
    python scripts/gradient_boosting_model_audit.py --check   # offline; re-validate

The committed JSON summary lives at
``scripts/gradient_boosting_model_audit_result.json`` and is asserted by
``tests/test_gradient_boosting_model_audit.py``.
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

RESULT_PATH = REPO_ROOT / "scripts" / "gradient_boosting_model_audit_result.json"
DT = MANIFEST["decision_tree"]
GB = MANIFEST["gradient_boosting"]
DEV_SPLIT = GB["dev_split"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
SKLEARN_EXAMPLE = GB["sklearn_example"]
CV_PIPELINE = GB["cv_pipeline"]


def _outer_dev_splits(X: Any, y: Any, groups: Any):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"], stratify=groups_train
    )
    return X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val


def _natural_order_columns(frame: Any) -> list[str]:
    # Matches the notebook's own FEATURES list (raw table order), not
    # scripts/abide_modeling_data.py's canonical ROI-then-hemisphere
    # bundle_columns order -- identical reasoning to
    # decision_tree_model_audit.py's own _natural_order_columns: a
    # tree-based model's best-split tie-breaking among this recipe's many
    # highly correlated cortical-thickness columns is order-sensitive, so
    # this audit matches the notebook's own column order exactly, rather
    # than recomputing a result the notebook's executed cells would not
    # reproduce.
    return [c for c in frame.columns if c.startswith("fsCT_")]


def _cols_and_frame_arrays(frame: Any):
    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    present = frame[GB["target"]].notna()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, GB["target"]].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    subjects = frame.loc[present, "subject"].to_numpy()
    return cols, X, y, groups, subjects


def _sklearn_example(frame: Any) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error, r2_score

    cols, X, y, groups, subjects = _cols_and_frame_arrays(frame)
    X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val = _outer_dev_splits(X, y, groups)

    gb_model = GradientBoostingRegressor(
        n_estimators=SKLEARN_EXAMPLE["n_estimators"],
        learning_rate=SKLEARN_EXAMPLE["learning_rate"],
        max_depth=SKLEARN_EXAMPLE["max_depth"],
        random_state=SKLEARN_EXAMPLE["random_state"],
    ).fit(X_fit, y_fit)
    predictions = gb_model.predict(X_val)

    return {
        "p": len(cols),
        "n_fit": int(len(y_fit)),
        "n_val": int(len(y_val)),
        "settings": dict(SKLEARN_EXAMPLE),
        "val_mse": round(float(mean_squared_error(y_val, predictions)), 4),
        "val_r2": round(float(r2_score(y_val, predictions)), 6),
    }


def _outer_split_with_subjects(cols: Any, X: Any, y: Any, groups: Any, subjects: Any):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    subjects_train, subjects_test = train_test_split(
        subjects, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    dev_subjects = set(subjects_train.tolist())
    test_subjects = set(subjects_test.tolist())
    if dev_subjects & test_subjects:
        raise RuntimeError("development/outer-test participant sets overlap")
    if (dev_subjects | test_subjects) != set(subjects.tolist()):
        raise RuntimeError("development + outer-test union does not equal the eligible-with-target cohort")
    return X_train, X_test, y_train, y_test, subjects_train, subjects_test


def _cv_tuning_pipeline(frame: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold

    cols, X, y, groups, subjects = _cols_and_frame_arrays(frame)

    # Step 1: preserve the locked outer test -- split once, up front.
    X_train, X_test, y_train, y_test, subjects_train, subjects_test = _outer_split_with_subjects(
        cols, X, y, groups, subjects
    )

    # Step 2-4: cross-validation only within the development partition, over
    # the reduced 12-candidate grid (see gradient_boosting.cv_pipeline.runtime_audit
    # for why the full 27-candidate grid was reduced before this script ever ran).
    reduced = CV_PIPELINE["reduced_grid"]
    pairs = reduced["learning_rate_n_estimators_pairs"]
    depths = reduced["max_depth"]
    candidates = [
        {"learning_rate": lr, "n_estimators": n, "max_depth": d}
        for d in depths
        for lr, n in pairs
    ]

    cv = KFold(n_splits=5, shuffle=True, random_state=CV_PIPELINE["cv_random_state"])
    fold_splits = list(cv.split(X_train))

    t_cv0 = time.time()
    cv_results = []
    for candidate in candidates:
        fold_mse = []
        for train_idx, val_idx in fold_splits:
            model = GradientBoostingRegressor(random_state=42, **candidate)
            model.fit(X_train[train_idx], y_train[train_idx])
            pred = model.predict(X_train[val_idx])
            fold_mse.append(mean_squared_error(y_train[val_idx], pred))
        cv_results.append(
            {
                "params": candidate,
                "fold_mse": [round(float(v), 4) for v in fold_mse],
                "mean_mse": round(float(np.mean(fold_mse)), 4),
                "sd_mse": round(float(np.std(fold_mse)), 4),
            }
        )
    cv_runtime = round(time.time() - t_cv0, 1)

    # Step 4: select by minimum mean CV MSE, first candidate wins ties.
    best_i = int(min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i)))
    best = cv_results[best_i]

    # Step 5: refit the selected configuration on all development participants.
    final_model = GradientBoostingRegressor(random_state=42, **best["params"]).fit(X_train, y_train)

    # Step 6: evaluate the locked outer test set exactly once.
    test_pred = final_model.predict(X_test)
    test_mse = round(float(mean_squared_error(y_test, test_pred)), 4)
    test_r2 = round(float(r2_score(y_test, test_pred)), 6)

    return {
        "p": len(cols),
        "n_development": int(len(y_train)),
        "n_outer_test": int(len(y_test)),
        "development_test_disjoint": True,
        "development_test_union_equals_cohort": True,
        "candidate_grid": candidates,
        "candidate_count": len(candidates),
        "cv": f"KFold(n_splits=5, shuffle=True, random_state={CV_PIPELINE['cv_random_state']})",
        "cv_runtime_seconds": cv_runtime,
        "cv_results": cv_results,
        "selected_index": best_i,
        "selected_params": best["params"],
        "selected_mean_cv_mse": best["mean_mse"],
        "test_mse": test_mse,
        "test_r2": test_r2,
    }


def _model_comparison(frame: Any, gb_test_mse: float, gb_test_r2: float) -> dict[str, Any]:
    """Section 7: a consistent held-out comparison. The single tree and
    Random Forest use Exercise 6's own complexity settings
    (decision_tree.fair_comparison.tree_settings / n_estimators /
    random_forest_max_features) carried forward unchanged -- no new
    hyperparameter search for either model -- but are fit and evaluated here
    on the identical participant split (dev_split-free outer development
    partition -> locked outer test, protocol.holdout_split) the
    gradient-boosting model above already used, rather than reusing Exercise
    6's separate 5-fold-CV numbers from a different cohort/protocol
    (decision_tree_model_audit_result.json's fair_comparison ran on the full
    eligible cohort with 5-fold CV, not this single locked test set)."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.tree import DecisionTreeRegressor

    cols, X, y, groups, subjects = _cols_and_frame_arrays(frame)
    X_train, X_test, y_train, y_test, subjects_train, subjects_test = _outer_split_with_subjects(
        cols, X, y, groups, subjects
    )

    fair = DT["fair_comparison"]
    tree_settings = fair["tree_settings"]
    n_estimators = fair["n_estimators"]
    max_features = fair["random_forest_max_features"]

    single_tree = DecisionTreeRegressor(**tree_settings).fit(X_train, y_train)
    single_pred = single_tree.predict(X_test)

    random_forest = RandomForestRegressor(
        n_estimators=n_estimators,
        max_features=max_features,
        random_state=tree_settings["random_state"],
        **{k: v for k, v in tree_settings.items() if k != "random_state"},
    ).fit(X_train, y_train)
    rf_pred = random_forest.predict(X_test)

    return {
        "note": (
            "All three models below use the identical participant split (outer development "
            "partition -> locked outer test, protocol.holdout_split, n_test=251) and the identical "
            "360-feature recipe and target as the gradient-boosting model. single_tree and "
            "random_forest use Exercise 6's own complexity settings (decision_tree.fair_comparison), "
            "carried forward unchanged rather than retuned -- this table is a consistent held-out "
            "comparison, not proof that one algorithm universally wins."
        ),
        "settings_source": "decision_tree.fair_comparison (carried forward, not retuned)",
        "single_tree": {
            "settings": tree_settings,
            "mean_mse": round(float(mean_squared_error(y_test, single_pred)), 4),
            "mean_r2": round(float(r2_score(y_test, single_pred)), 6),
            "protocol": "single locked outer-test evaluation",
        },
        "random_forest": {
            "settings": {**tree_settings, "n_estimators": n_estimators, "max_features": max_features},
            "mean_mse": round(float(mean_squared_error(y_test, rf_pred)), 4),
            "mean_r2": round(float(r2_score(y_test, rf_pred)), 6),
            "protocol": "single locked outer-test evaluation",
        },
        "gradient_boosting": {
            "mean_mse": gb_test_mse,
            "mean_r2": gb_test_r2,
            "protocol": "single locked outer-test evaluation",
        },
    }


def run_audit() -> dict[str, Any]:
    t0 = time.time()
    frame = load_modeling_frame()
    sklearn_example = _sklearn_example(frame)
    cv_pipeline = _cv_tuning_pipeline(frame)
    results: dict[str, Any] = {
        "generated_by": "scripts/gradient_boosting_model_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "sklearn_example": sklearn_example,
        "cv_pipeline": cv_pipeline,
        "model_comparison": _model_comparison(frame, cv_pipeline["test_mse"], cv_pipeline["test_r2"]),
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

    se = results.get("sklearn_example", {})
    if se.get("settings") != dict(SKLEARN_EXAMPLE):
        problems.append("sklearn_example.settings does not match the manifest's declared settings")

    cv = results.get("cv_pipeline", {})
    if not cv.get("development_test_disjoint"):
        problems.append("cv_pipeline: development_test_disjoint must be true")
    if not cv.get("development_test_union_equals_cohort"):
        problems.append("cv_pipeline: development_test_union_equals_cohort must be true")
    n_dev, n_test = cv.get("n_development"), cv.get("n_outer_test")
    if None in (n_dev, n_test):
        problems.append("cv_pipeline: n_development/n_outer_test missing")

    candidates = cv.get("candidate_grid", [])
    if len(candidates) < 12:
        problems.append("cv_pipeline: candidate_grid must have at least 12 candidates")
    cv_results = cv.get("cv_results", [])
    if len(cv_results) != len(candidates):
        problems.append("cv_pipeline: cv_results length must match candidate_grid length")
    for r in cv_results:
        if len(r.get("fold_mse", [])) != 5:
            problems.append(f"cv_pipeline: candidate {r.get('params')} does not have exactly 5 fold MSE values")

    selected_index = cv.get("selected_index")
    if isinstance(selected_index, int) and cv_results:
        recomputed_best = min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i))
        if recomputed_best != selected_index:
            problems.append("cv_pipeline: selected_index does not match a fresh minimum-mean-CV-MSE recomputation")
        if cv.get("selected_params") != cv_results[selected_index]["params"]:
            problems.append("cv_pipeline: selected_params does not match cv_results[selected_index].params")
        if cv.get("selected_mean_cv_mse") != cv_results[selected_index]["mean_mse"]:
            problems.append("cv_pipeline: selected_mean_cv_mse does not match cv_results[selected_index].mean_mse")

    if cv.get("test_mse") is None or cv.get("test_r2") is None:
        problems.append("cv_pipeline: test_mse/test_r2 missing (locked test must be evaluated exactly once)")

    mc = results.get("model_comparison", {})
    for name in ("single_tree", "random_forest", "gradient_boosting"):
        if "mean_mse" not in mc.get(name, {}):
            problems.append(f"model_comparison.{name}: missing mean_mse")
    if mc.get("gradient_boosting", {}).get("mean_mse") != cv.get("test_mse"):
        problems.append("model_comparison.gradient_boosting.mean_mse must equal cv_pipeline.test_mse")

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
    se = results["sklearn_example"]
    print(f"=== sklearn example: val MSE={se['val_mse']:.1f}  val R2={se['val_r2']:+.3f} ===")
    cv = results["cv_pipeline"]
    print(
        f"=== CV pipeline ({cv['candidate_count']} candidates, {cv['cv']}): "
        f"selected {cv['selected_params']} (mean CV MSE={cv['selected_mean_cv_mse']:.1f}) "
        f"-- test MSE={cv['test_mse']:.1f}  test R2={cv['test_r2']:+.3f}, cv runtime={cv['cv_runtime_seconds']}s ==="
    )
    mc = results["model_comparison"]
    print("=== comparison ===")
    for name in ("single_tree", "random_forest", "gradient_boosting"):
        m = mc[name]
        print(f"  {name:18s} mean MSE={m['mean_mse']:.1f}  mean R2={m['mean_r2']:+.3f}  ({m['protocol']})")
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
