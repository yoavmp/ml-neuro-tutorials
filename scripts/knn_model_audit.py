#!/usr/bin/env python3
"""Reproducible KNN model audit for Exercise 3 (WP13 section 1).

Goal: decide -- empirically, before writing the notebook -- which feature
recipe gives the clearest standardized KNN-regression teaching example for
``age``, and what ``k`` a training-only selection procedure picks for it. The
outer test set (Exercise 2's own locked split) is never touched by this
selection; it is evaluated exactly once per candidate, purely to report the
one number the notebook quotes.

Design rules (WP13 section 1):

* every model is ``Pipeline(StandardScaler(), KNeighborsRegressor(...))`` so
  scaling is learned from training data / training folds only;
* ``k`` is chosen by a 5-fold ``KFold(shuffle=True, random_state=0)`` --
  Exercise 2's own documented cross-validation protocol
  (``book/config/abide_modeling.json`` ``protocol.cross_validation``) -- on the
  OUTER-TRAINING partition only. The k grid spans 1 through the largest k
  valid inside that cross-validation (a fold's own training size), evaluated
  at a representative, log-spaced set of points rather than every integer (a
  full even grid is used later in the notebook's own development curve,
  section 4.5, which is a separate, from-scratch computation);
* the special endpoint "k equals every participant in the fitting set" is
  evaluated too, as a diagnostic never used for selection: fit once on the
  full outer-training partition (753 rows) with ``k = n_train`` and predict
  the untouched outer test set once. At that k, every prediction is the
  training-partition mean (verified structurally, not just numerically);
* the outer test set (Exercise 2's ``train_test_split(test_size=0.25,
  random_state=42, stratify=group)``) is evaluated exactly once per candidate,
  after k is already locked by the training-only procedure above.

Predeclared feature spaces (WP13 section 1):

1. the exact Exercise 2 canonical recipe -- ``all-eligible`` bilateral cortical
   thickness, p = 360;
2. two already-predeclared, smaller anatomical bundles from
   ``book/config/abide_modeling.json`` (``frontoparietal`` p = 78,
   ``occipital`` p = 46) to see whether lower dimensionality changes standardized
   KNN's behaviour (the curse-of-dimensionality question the WP asks about).

No feature was chosen by looking at its association with ``age``; all three
recipes were already reviewed bundles/the canonical recipe before this audit
ran.

Usage::

    python scripts/knn_model_audit.py --run     # network; prints + writes JSON
    python scripts/knn_model_audit.py --check   # offline; re-validate committed JSON

The committed JSON summary lives at ``scripts/knn_model_audit_result.json`` and
is asserted by ``tests/test_knn_model_audit.py``.
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

RESULT_PATH = REPO_ROOT / "scripts" / "knn_model_audit_result.json"

TARGET = "age"
OUTER_CV_SEED = 0
N_SPLITS = 5

FEATURE_SPACES: list[dict[str, Any]] = [
    {"name": "all-eligible x CT (Exercise 2 canonical)", "bundle": "all-eligible", "measures": ["CT"]},
    {"name": "frontoparietal x CT (P-FIT compact)", "bundle": "frontoparietal", "measures": ["CT"]},
    {"name": "occipital x CT (comparison bundle)", "bundle": "occipital", "measures": ["CT"]},
]


def _feature_columns(frame: Any, space: dict[str, Any]) -> list[str]:
    cols = bundle_columns(space["bundle"], space["measures"], available=frame.columns)
    assert_brain_only(cols)
    return cols


def _outer_split(frame: Any, cols: list[str]):
    import numpy as np
    from sklearn.model_selection import train_test_split

    if TARGET in cols:
        raise ValueError("leakage: target is in the feature list")
    present = frame[TARGET].notna().to_numpy()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, TARGET].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    if np.isnan(X).any():
        raise ValueError(f"{TARGET}: brain features contain missing values")

    hs = MANIFEST["protocol"]["holdout_split"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups
    )
    return X_train, X_test, y_train, y_test


def _k_grid(k_max: int) -> list[int]:
    """A representative, log-spaced set of k in [1, k_max], always including the
    endpoints and a handful of small-k values where KNN changes fastest."""
    import numpy as np

    small = [k for k in (1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 40) if k <= k_max]
    log_part = sorted(
        {int(round(v)) for v in np.geomspace(max(small[-1], 1), k_max, num=16) if 1 <= v <= k_max}
    )
    grid = sorted(set(small) | set(log_part) | {k_max})
    return grid


def _cv_select_k(X_train: Any, y_train: Any, k_max: int) -> dict[str, Any]:
    """5-fold CV (Exercise 2's own protocol) on the training partition only.
    Returns the full per-k curve and the selected k (argmax mean CV R^2, ties
    broken toward the smaller / more parsimonious k)."""
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    cv = KFold(n_splits=N_SPLITS, shuffle=True, random_state=OUTER_CV_SEED)
    grid = _k_grid(k_max)

    curve = []
    for k in grid:
        fold_r2, fold_mse = [], []
        for tr_idx, va_idx in cv.split(X_train):
            pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))
            pipe.fit(X_train[tr_idx], y_train[tr_idx])
            pred = pipe.predict(X_train[va_idx])
            fold_r2.append(float(r2_score(y_train[va_idx], pred)))
            fold_mse.append(float(mean_squared_error(y_train[va_idx], pred)))
        curve.append(
            {
                "k": k,
                "cv_r2_mean": round(float(np.mean(fold_r2)), 6),
                "cv_r2_std": round(float(np.std(fold_r2)), 6),
                "cv_mse_mean": round(float(np.mean(fold_mse)), 4),
            }
        )

    best = max(curve, key=lambda row: row["cv_r2_mean"])
    # tie-break toward the smallest k within floating-point noise of the best
    tied = [row for row in curve if abs(row["cv_r2_mean"] - best["cv_r2_mean"]) < 1e-9]
    selected = min(tied, key=lambda row: row["k"])
    return {"grid": grid, "curve": curve, "selected_k": selected["k"], "selected": selected}


def _locked_test_eval(X_train, y_train, X_test, y_test, k: int) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))
    pipe.fit(X_train, y_train)
    train_pred = pipe.predict(X_train)
    test_pred = pipe.predict(X_test)
    return {
        "k": k,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "train_r2": round(float(r2_score(y_train, train_pred)), 6),
        "train_mse": round(float(mean_squared_error(y_train, train_pred)), 4),
        "test_r2": round(float(r2_score(y_test, test_pred)), 6),
        "test_mse": round(float(mean_squared_error(y_test, test_pred)), 4),
    }


def _fitting_set_endpoint(X_train, y_train, X_test, y_test) -> dict[str, Any]:
    """The special endpoint: k = every participant in the fitting set. Verifies
    structurally that every prediction equals the training-partition mean."""
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    n_fit = len(y_train)
    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=n_fit))
    pipe.fit(X_train, y_train)
    test_pred = pipe.predict(X_test)
    train_mean = float(np.mean(y_train))
    all_equal_mean = bool(np.allclose(test_pred, train_mean))
    return {
        "k": n_fit,
        "n_fit": n_fit,
        "train_mean": round(train_mean, 6),
        "all_predictions_equal_training_mean": all_equal_mean,
        "test_r2": round(float(r2_score(y_test, test_pred)), 6),
        "test_mse": round(float(mean_squared_error(y_test, test_pred)), 4),
    }


def run_audit() -> dict[str, Any]:
    t0 = time.time()
    frame = load_modeling_frame()

    results: dict[str, Any] = {
        "generated_by": "scripts/knn_model_audit.py --run",
        "target": TARGET,
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "protocol": {
            "outer_holdout_split": MANIFEST["protocol"]["holdout_split"],
            "cv_for_k_selection": f"KFold(n_splits={N_SPLITS}, shuffle=True, random_state={OUTER_CV_SEED})",
            "note": (
                "k is selected by 5-fold CV on the outer-TRAINING partition only "
                "(the same CV protocol Exercise 2 documents). The outer test set is "
                "evaluated exactly once per candidate, after k is already locked, and "
                "is never used to select k, the feature space, scaling, the distance "
                "metric, or weighting."
            ),
        },
        "candidates": [],
    }

    for space in FEATURE_SPACES:
        cols = _feature_columns(frame, space)
        p = len(cols)
        X_train, X_test, y_train, y_test = _outer_split(frame, cols)
        n_train, n_test = len(y_train), len(y_test)

        fold_train_n = int(round(n_train * (N_SPLITS - 1) / N_SPLITS))
        selection = _cv_select_k(X_train, y_train, k_max=fold_train_n)
        k_star = selection["selected_k"]
        locked = _locked_test_eval(X_train, y_train, X_test, y_test, k_star)
        endpoint = _fitting_set_endpoint(X_train, y_train, X_test, y_test)
        k1 = next(row for row in selection["curve"] if row["k"] == 1)

        results["candidates"].append(
            {
                "feature_space": space["name"],
                "bundle": space["bundle"],
                "measures": space["measures"],
                "p": p,
                "usable_n": int(n_train + n_test),
                "n_train": n_train,
                "n_test": n_test,
                "folds": N_SPLITS,
                "k_grid_max_valid_in_cv": fold_train_n,
                "k_grid": selection["grid"],
                "cv_curve": selection["curve"],
                "selected_k": k_star,
                "selected_k_cv_r2": selection["selected"]["cv_r2_mean"],
                "selected_k_cv_mse": selection["selected"]["cv_mse_mean"],
                "k1_cv_r2": k1["cv_r2_mean"],
                "k1_cv_mse": k1["cv_mse_mean"],
                "locked_test_eval": locked,
                "fitting_set_endpoint": endpoint,
            }
        )

    results["runtime_seconds"] = round(time.time() - t0, 2)
    return results


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_run() -> int:
    results = run_audit()
    text = serialize(results)
    RESULT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_table(results)
    return 0


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
    _print_table(results)
    return 0


def validate(results: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if results.get("target") != TARGET:
        problems.append("target must be 'age'")
    if results.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    names = {c["feature_space"] for c in results.get("candidates", [])}
    expected = {s["name"] for s in FEATURE_SPACES}
    if names != expected:
        problems.append(f"candidates cover {names}, expected {expected}")
    for c in results.get("candidates", []):
        if c["k_grid"][0] != 1:
            problems.append(f"{c['feature_space']}: k_grid must start at 1")
        if c["k_grid"][-1] != c["k_grid_max_valid_in_cv"]:
            problems.append(f"{c['feature_space']}: k_grid must end at the largest CV-valid k")
        if c["selected_k"] not in c["k_grid"]:
            problems.append(f"{c['feature_space']}: selected_k not in the evaluated grid")
        ep = c["fitting_set_endpoint"]
        if ep["k"] != c["n_train"]:
            problems.append(f"{c['feature_space']}: fitting_set_endpoint k must equal n_train")
        if not ep["all_predictions_equal_training_mean"]:
            problems.append(f"{c['feature_space']}: k=n_train did not predict the training mean everywhere")
    return problems


def _print_table(results: dict[str, Any]) -> None:
    print()
    print(f"=== KNN audit for target={results['target']} (runtime {results.get('runtime_seconds', '?')}s) ===")
    hdr = (
        f"{'feature space':38s} {'p':>4s} {'n_tr':>5s} {'n_te':>5s} {'k_max':>6s} "
        f"{'k*':>5s} {'cvR2':>8s} {'testR2':>8s} {'k=1 cvR2':>9s} {'k=n_fit testR2':>15s}"
    )
    print(hdr)
    print("-" * len(hdr))
    for c in results["candidates"]:
        print(
            f"{c['feature_space']:38.38s} {c['p']:4d} {c['n_train']:5d} {c['n_test']:5d} "
            f"{c['k_grid_max_valid_in_cv']:6d} {c['selected_k']:5d} {c['selected_k_cv_r2']:+8.4f} "
            f"{c['locked_test_eval']['test_r2']:+8.4f} {c['k1_cv_r2']:+9.4f} "
            f"{c['fitting_set_endpoint']['test_r2']:+15.4f}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
