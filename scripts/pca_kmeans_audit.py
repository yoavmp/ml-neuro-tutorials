#!/usr/bin/env python3
"""Reproducible PCA + K-means audit for Exercise 8 (WP33).

Audits everything Exercise 8's non-widget code cells quote as numbers, so the
notebook reads audited results rather than computing them ad hoc:

* **cohort/features** -- the same 1004-participant, 360-cortical-thickness-
  feature table Exercises 2, 4, 5, 6, and 7 use (``unsupervised.recipe``);
* **PCA** (section 4) -- standardized explained-variance ratios and
  cumulative explained variance for the first 50 components, signed loadings
  for the strongest individual ROIs on PC1/PC2, and grouped mean-absolute
  loading within each anatomical bundle in ``unsupervised.anatomical_groups``
  (never a signed sum, which can cancel);
* **supervised PCA pipeline** (section 8) -- cross-validation restricted to
  the outer development partition (never the locked outer test), a fixed
  ``component_grid``, selection by minimum mean CV MSE, refit on all
  development participants, one evaluation of the locked outer test set, and
  a plain-linear-regression baseline on the same split.

The two interactive activities ("Find the Best Projection" and "Explore PCA
and K-Means") are audited separately by their own export scripts
(``scripts/export_pca_projection_widget.py``,
``scripts/export_pca_kmeans_widget.py``) since those artifacts already
contain everything those sections display.

Design rules, shared with the rest of this course's audits:

* the outer test set (``protocol.holdout_split``) is read exactly once, in
  the supervised pipeline's final step, after the component count has
  already been fixed from development-only cross-validation;
* PCA and K-means (sections 1-7) never see diagnosis, sex, site, or age --
  those are joined onto results only afterward, for display;
* the 360-feature column order matches the notebook's own natural-table
  order (``_natural_order_columns``), the same convention
  ``gradient_boosting_model_audit.py`` and ``decision_tree_model_audit.py``
  already use, so a highly-correlated-feature-driven divergence between this
  audit and the notebook's own cells cannot silently creep in.

Usage::

    python scripts/pca_kmeans_audit.py --run     # network; writes JSON
    python scripts/pca_kmeans_audit.py --check   # offline; re-validate

The committed JSON summary lives at
``scripts/pca_kmeans_audit_result.json`` and is asserted by
``tests/test_pca_kmeans_audit.py``.
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
    load_modeling_frame,
)

RESULT_PATH = REPO_ROOT / "scripts" / "pca_kmeans_audit_result.json"
UNSUP = MANIFEST["unsupervised"]
RECIPE = UNSUP["recipe"]
GROUPS: list[str] = UNSUP["anatomical_groups"]
LOADING_SUMMARY = UNSUP["loading_summary"]
SUP = UNSUP["supervised_pipeline"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]


def _natural_order_columns(frame: Any) -> list[str]:
    # Matches the notebook's own FEATURES list (raw table order), not
    # abide_modeling_data.bundle_columns's canonical ROI-then-hemisphere
    # order -- same reasoning as gradient_boosting_model_audit.py /
    # decision_tree_model_audit.py's own helper of the same name.
    return [c for c in frame.columns if c.startswith("fsCT_")]


def _cols_and_X(frame: Any) -> tuple[list[str], Any]:
    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    X = frame.loc[:, cols].to_numpy(dtype="float64")
    return cols, X


def _pca_summary(frame: Any, cols: list[str], X: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=50, random_state=0).fit(Xs)
    evr = pca.explained_variance_ratio_
    cum = np.cumsum(evr)
    loadings = pca.components_  # (50, 360)

    n_top = LOADING_SUMMARY["n_top_rois"]
    n_shown = LOADING_SUMMARY["n_components_shown"]
    top_rois: dict[str, list[dict[str, Any]]] = {}
    for pc in range(n_shown):
        order = np.argsort(-np.abs(loadings[pc]))[:n_top]
        top_rois[f"PC{pc + 1}"] = [
            {"column": cols[i], "loading": round(float(loadings[pc][i]), 4)} for i in order
        ]

    grouped: dict[str, dict[str, float]] = {}
    for group in GROUPS:
        group_cols = bundle_columns(group, ["CT"], available=frame.columns)
        idx = [cols.index(c) for c in group_cols]
        grouped[group] = {
            f"PC{pc + 1}": round(float(np.mean(np.abs(loadings[pc][idx]))), 4) for pc in range(n_shown)
        }

    return {
        "n_components_fit": 50,
        "explained_variance_ratio": [round(float(v), 6) for v in evr],
        "cumulative_explained_variance": [round(float(v), 6) for v in cum],
        "cumulative_at": {str(k): round(float(cum[k - 1]), 4) for k in [2, 5, 10, 20, 50]},
        "top_rois_by_component": top_rois,
        "grouped_mean_abs_loading": grouped,
        "group_sizes": {g: len(bundle_columns(g, ["CT"], available=frame.columns)) for g in GROUPS},
        "pc1_all_same_sign": bool(np.all(loadings[0] > 0) or np.all(loadings[0] < 0)),
    }


def _outer_dev_split(cols: list[str], X: Any, y: Any, groups: Any):
    from sklearn.model_selection import train_test_split

    return train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )


def _supervised_pipeline(frame: Any, cols: list[str], X: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold, train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    target = "age"
    present = frame[target].notna().to_numpy()
    Xy = X[present]
    y = frame.loc[present, target].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    subjects = frame.loc[present, "subject"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = _outer_dev_split(cols, Xy, y, groups)
    subjects_train, subjects_test = train_test_split(
        subjects, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    dev_subjects = set(subjects_train.tolist())
    test_subjects = set(subjects_test.tolist())
    if dev_subjects & test_subjects:
        raise RuntimeError("development/outer-test participant sets overlap")
    if (dev_subjects | test_subjects) != set(subjects.tolist()):
        raise RuntimeError("development + outer-test union does not equal the eligible-with-target cohort")

    grid = SUP["component_grid"]
    cv = KFold(n_splits=5, shuffle=True, random_state=SUP["cv_random_state"])
    fold_splits = list(cv.split(X_train))

    t0 = time.time()
    cv_results = []
    for n in grid:
        fold_mse = []
        for tr, va in fold_splits:
            pipe = Pipeline(
                [
                    ("scale", StandardScaler()),
                    ("pca", PCA(n_components=n, random_state=0)),
                    ("model", LinearRegression()),
                ]
            )
            pipe.fit(X_train[tr], y_train[tr])
            pred = pipe.predict(X_train[va])
            fold_mse.append(mean_squared_error(y_train[va], pred))
        cv_results.append(
            {
                "n_components": n,
                "fold_mse": [round(float(v), 4) for v in fold_mse],
                "mean_mse": round(float(np.mean(fold_mse)), 4),
                "sd_mse": round(float(np.std(fold_mse)), 4),
            }
        )
    cv_runtime = round(time.time() - t0, 1)

    best_i = int(min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i)))
    best = cv_results[best_i]
    selected_n = best["n_components"]

    final_pipe = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=selected_n, random_state=0)),
            ("model", LinearRegression()),
        ]
    ).fit(X_train, y_train)
    test_pred = final_pipe.predict(X_test)
    test_mse = round(float(mean_squared_error(y_test, test_pred)), 4)
    test_r2 = round(float(r2_score(y_test, test_pred)), 6)

    baseline_pipe = Pipeline([("scale", StandardScaler()), ("model", LinearRegression())]).fit(X_train, y_train)
    baseline_pred = baseline_pipe.predict(X_test)
    baseline_mse = round(float(mean_squared_error(y_test, baseline_pred)), 4)
    baseline_r2 = round(float(r2_score(y_test, baseline_pred)), 6)

    return {
        "target": target,
        "p": len(cols),
        "n_development": int(len(y_train)),
        "n_outer_test": int(len(y_test)),
        "development_test_disjoint": True,
        "development_test_union_equals_cohort": True,
        "component_grid": grid,
        "cv": f"KFold(n_splits=5, shuffle=True, random_state={SUP['cv_random_state']})",
        "cv_runtime_seconds": cv_runtime,
        "cv_results": cv_results,
        "selected_index": best_i,
        "selected_n_components": selected_n,
        "selected_mean_cv_mse": best["mean_mse"],
        "pca_pipeline_test_mse": test_mse,
        "pca_pipeline_test_r2": test_r2,
        "baseline_no_pca_test_mse": baseline_mse,
        "baseline_no_pca_test_r2": baseline_r2,
        "pca_beats_baseline": test_mse < baseline_mse,
    }


def run_audit() -> dict[str, Any]:
    t0 = time.time()
    frame = load_modeling_frame()
    cols, X = _cols_and_X(frame)
    if len(cols) != 360:
        raise RuntimeError(f"expected 360 cortical-thickness columns, got {len(cols)}")
    if len(frame) != 1004:
        raise RuntimeError(f"expected 1004 eligible participants, got {len(frame)}")

    pca_summary = _pca_summary(frame, cols, X)
    supervised = _supervised_pipeline(frame, cols, X)

    results: dict[str, Any] = {
        "generated_by": "scripts/pca_kmeans_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "cohort": {"n_participants": int(len(frame)), "n_features": len(cols)},
        "pca": pca_summary,
        "supervised_pipeline": supervised,
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

    cohort = results.get("cohort", {})
    if cohort.get("n_participants") != 1004:
        problems.append("cohort.n_participants must be 1004")
    if cohort.get("n_features") != 360:
        problems.append("cohort.n_features must be 360")

    pca = results.get("pca", {})
    evr = pca.get("explained_variance_ratio", [])
    if len(evr) != 50:
        problems.append("pca.explained_variance_ratio must have 50 entries")
    elif evr != sorted(evr, reverse=True):
        problems.append("pca.explained_variance_ratio must be non-increasing")
    if not pca.get("pc1_all_same_sign"):
        problems.append("pca.pc1_all_same_sign must be true (PC1 is expected to be a global, uniformly-signed component)")
    grouped = pca.get("grouped_mean_abs_loading", {})
    for g in GROUPS:
        stats = grouped.get(g, {})
        for v in stats.values():
            if v < 0:
                problems.append(f"grouped_mean_abs_loading[{g}]: value must be non-negative (mean absolute loading)")

    sup = results.get("supervised_pipeline", {})
    if not sup.get("development_test_disjoint"):
        problems.append("supervised_pipeline: development_test_disjoint must be true")
    if not sup.get("development_test_union_equals_cohort"):
        problems.append("supervised_pipeline: development_test_union_equals_cohort must be true")
    cv_results = sup.get("cv_results", [])
    grid = sup.get("component_grid", [])
    if len(cv_results) != len(grid):
        problems.append("supervised_pipeline: cv_results length must match component_grid length")
    for r in cv_results:
        if len(r.get("fold_mse", [])) != 5:
            problems.append(f"supervised_pipeline: n_components={r.get('n_components')} does not have exactly 5 fold MSE values")
    selected_index = sup.get("selected_index")
    if isinstance(selected_index, int) and cv_results:
        recomputed_best = min(range(len(cv_results)), key=lambda i: (cv_results[i]["mean_mse"], i))
        if recomputed_best != selected_index:
            problems.append("supervised_pipeline: selected_index does not match a fresh minimum-mean-CV-MSE recomputation")
        if cv_results[selected_index]["n_components"] != sup.get("selected_n_components"):
            problems.append("supervised_pipeline: selected_n_components does not match cv_results[selected_index].n_components")
    if sup.get("pca_pipeline_test_mse") is None:
        problems.append("supervised_pipeline: pca_pipeline_test_mse missing (locked test must be evaluated exactly once)")
    expected_beats = sup.get("pca_pipeline_test_mse", float("inf")) < sup.get("baseline_no_pca_test_mse", float("-inf"))
    if sup.get("pca_beats_baseline") != expected_beats:
        problems.append("supervised_pipeline: pca_beats_baseline does not match a fresh MSE comparison")

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
    pca = results["pca"]
    print(f"=== PCA: cumulative EV at 2/5/10/20/50 = {pca['cumulative_at']} ===")
    sup = results["supervised_pipeline"]
    print(
        f"=== supervised pipeline: selected n_components={sup['selected_n_components']} "
        f"(mean CV MSE={sup['selected_mean_cv_mse']:.1f}) -- "
        f"PCA test MSE={sup['pca_pipeline_test_mse']:.1f} R2={sup['pca_pipeline_test_r2']:+.3f}; "
        f"baseline test MSE={sup['baseline_no_pca_test_mse']:.1f} R2={sup['baseline_no_pca_test_r2']:+.3f} ==="
    )
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
