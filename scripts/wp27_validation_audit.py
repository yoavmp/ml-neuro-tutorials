#!/usr/bin/env python3
"""Reproducible validation / cross-validation audit for Exercise 4 (WP27).

Exercise 4 reuses Exercise 2's ABIDE age-prediction task and its canonical
KNN recipe (``all-eligible`` bilateral cortical thickness, p=360, fixed
worked-example ``k=20``; see ``book/config/abide_modeling.json`` and
``scripts/knn_model_audit.py``). This script produces every number the
Exercise 4 notebook and its three interactive activities show, so that
nothing in the lesson is invented or hand-typed:

* Part A -- single-split vs. cross-validation stability across a predeclared
  sample-size grid and seed set (Section 2 / Activity 1, "One Split or
  Several Folds?");
* Part B -- train/validation/test tuning of KNN's ``k`` on the exact
  Exercise 2 outer holdout split and dev split, reporting the
  training-selected and validation-selected ``k`` and their one-time locked
  test result (Section 4-5 / Activity 2, "Choose k Before Revealing the Test
  Set");
* Part C -- nested cross-validation (inner selects ``k``, outer evaluates
  the complete tuning procedure) on the full eligible cohort (Section 6-7 /
  Activity 3, "Look Inside Nested Cross-Validation").

Design rules, fixed before any candidate was scored:

* every model is ``Pipeline(StandardScaler(), KNeighborsRegressor())`` so
  scaling is learned from training data / training folds only;
* the feature recipe, target, and fixed worked-example ``k=20`` are taken
  unchanged from Exercise 2 / WP19 -- nothing here selects a feature set;
* Part A's participant pools are NESTED and fixed per sample size (drawn
  once from one fixed master permutation of the full eligible cohort), so a
  changed split seed only changes how a fixed pool of participants is
  partitioned, never which participants are in the pool;
* Part A's fold/size combinations are validated against two predeclared
  numerical-validity rules (``MIN_TRAIN_OVER_K``, ``MIN_TEST_FOLD_SIZE``)
  fixed before any combination was scored; invalid combinations are recorded
  with ``valid: false`` and a reason, never silently dropped;
* Part B never selects ``k`` using the locked outer test set: the
  training-selected and validation-selected ``k`` come only from the fit /
  validation partitions. Every candidate ``k``'s test-set metric is computed
  once (so the static website can reveal whichever ``k`` a student locks in)
  but none of those numbers feeds back into any selection;
* Part C's inner cross-validation never sees its own outer-test fold.

Usage::

    python scripts/wp27_validation_audit.py --run     # network; prints + writes JSON
    python scripts/wp27_validation_audit.py --check   # offline; re-validate committed JSON

The committed JSON result lives at
``scripts/wp27_validation_audit_result.json`` and is asserted by
``tests/test_wp27_validation_audit.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
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

RESULT_PATH = REPO_ROOT / "scripts" / "wp27_validation_audit_result.json"

TARGET = "age"
RECIPE = {"bundle": "all-eligible", "measures": ["CT"]}  # identical to Exercise 2 / KNN worked example
FIXED_K = 20  # WP19 worked-example k, reused unchanged (never re-selected here)

# --- Part A: sample-size stability grid (Section 2 / Activity 1) -----------
SAMPLE_SIZES: list[Any] = [30, 50, 75, 100, 150, 250, 500, "all"]
SPLIT_SEEDS: list[int] = [0, 1, 2, 3, 4]
FOLD_OPTIONS: list[int] = [3, 5, 10]
SINGLE_SPLIT_TEST_SIZE = 0.25
POOL_MASTER_SEED = 20270  # one fixed permutation of the eligible cohort; pools nest

# Predeclared numerical-validity rules (fixed before any combination was scored).
MIN_TRAIN_OVER_K = 1.0     # KFold/train_test_split train partition must contain >= FIXED_K rows
MIN_TEST_FOLD_SIZE = 5     # a test/fold partition smaller than this is too noisy to show

# Instability criterion, used only to STATE (not cherry-pick) at which sizes
# the single-split score visibly moves across seeds: MSE is this audit's
# primary metric (per WP27 spec section 11), so the range statistic below is
# reported for every size for transparency, but the qualitative flag used in
# the notebook's own claim is "at least one of the predeclared seeds produced
# a single-split R2 below 0" -- a single split that performs worse than
# always predicting the training mean is an unambiguous, metric-independent
# sign of meaningful instability, and does not depend on picking a range
# threshold. (The range-based statistic is also reported below; it turned out
# noisy and non-monotonic in N with only 5 predeclared seeds -- see the WP27
# report for the full disclosure.)
INSTABILITY_R2_RANGE_THRESHOLD = 0.15

# --- Part B: train/validation/test tuning (Section 4-5 / Activity 2) -------
CANDIDATE_KS: list[int] = [1, 2, 3, 5, 8, 12, 20, 30, 50, 75, 100, 150, 250, 400, 564]

# --- Part C: nested cross-validation (Section 6-7 / Activity 3) ------------
NESTED_CANDIDATE_KS: list[int] = [5, 15, 30, 50, 75]
N_OUTER = 5
N_INNER = 5
OUTER_SEED = 100
INNER_SEED = 101


def _feature_columns(frame: Any) -> list[str]:
    cols = bundle_columns(RECIPE["bundle"], RECIPE["measures"], available=frame.columns)
    assert_brain_only(cols)
    return cols


def _eligible_xy(frame: Any, cols: list[str]):
    import numpy as np

    present = frame[TARGET].notna().to_numpy()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, TARGET].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    if np.isnan(X).any():
        raise ValueError(f"{TARGET}: brain features contain missing values")
    return X, y, groups


# --- Part A ------------------------------------------------------------


def _nested_pools(n_eligible: int) -> dict[Any, "Any"]:
    """One fixed permutation of the eligible cohort; each sample size's pool
    is a prefix of it, so pools nest (pool(50) subset pool(100) subset ...)."""
    import numpy as np

    rng = np.random.default_rng(POOL_MASTER_SEED)
    order = rng.permutation(n_eligible)
    pools: dict[Any, Any] = {}
    for size in SAMPLE_SIZES:
        n = n_eligible if size == "all" else min(size, n_eligible)
        pools[size] = order[:n]
    return pools


def _single_split_eval(X, y, seed: int) -> dict[str, Any]:
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    n = len(y)
    n_train_expected = round(n * (1 - SINGLE_SPLIT_TEST_SIZE))
    n_test_expected = n - n_train_expected
    valid = n_train_expected >= FIXED_K * MIN_TRAIN_OVER_K and n_test_expected >= MIN_TEST_FOLD_SIZE
    if not valid:
        return {
            "seed": seed,
            "valid": False,
            "reason": f"n_train={n_train_expected} or n_test={n_test_expected} fails the predeclared minimum size rule",
        }
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=SINGLE_SPLIT_TEST_SIZE, random_state=seed)
    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=FIXED_K))
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    return {
        "seed": seed,
        "valid": True,
        "n_train": int(len(y_tr)),
        "n_test": int(len(y_te)),
        "test_mse": round(float(mean_squared_error(y_te, pred)), 4),
        "test_r2": round(float(r2_score(y_te, pred)), 6),
    }


def _cv_eval(X, y, seed: int, folds: int) -> dict[str, Any]:
    import numpy as np
    from sklearn.model_selection import KFold, cross_validate
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    n = len(y)
    if folds > n:
        return {"seed": seed, "folds": folds, "valid": False, "reason": f"n={n} < folds={folds}"}
    base_test = n // folds
    remainder = n % folds
    # KFold(shuffle=True) distributes the remainder across the first `remainder`
    # folds, so fold sizes are base_test(+1) test / n-that many train.
    smallest_test = base_test
    largest_train = n - base_test
    if largest_train < FIXED_K * MIN_TRAIN_OVER_K or smallest_test < MIN_TEST_FOLD_SIZE:
        return {
            "seed": seed,
            "folds": folds,
            "valid": False,
            "reason": (
                f"train~{n - base_test - (1 if remainder else 0)} or test~{smallest_test} "
                "fails the predeclared minimum size rule"
            ),
        }
    kf = KFold(n_splits=folds, shuffle=True, random_state=seed)
    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=FIXED_K))
    scores = cross_validate(
        pipe, X, y, cv=kf, scoring=("neg_mean_squared_error", "r2"), return_train_score=False
    )
    fold_mse = [round(float(-v), 4) for v in scores["test_neg_mean_squared_error"]]
    fold_r2 = [round(float(v), 6) for v in scores["test_r2"]]
    fold_sizes = [int(len(te)) for _tr, te in kf.split(X)]
    train_sizes = [int(n - s) for s in fold_sizes]
    return {
        "seed": seed,
        "folds": folds,
        "valid": True,
        "fold_test_sizes": fold_sizes,
        "fold_train_sizes": train_sizes,
        "fold_mse": fold_mse,
        "fold_r2": fold_r2,
        "mean_mse": round(float(np.mean(fold_mse)), 4),
        "std_mse": round(float(np.std(fold_mse)), 4),
        "mean_r2": round(float(np.mean(fold_r2)), 6),
        "std_r2": round(float(np.std(fold_r2)), 6),
    }


def _part_a(frame: Any, cols: list[str]) -> dict[str, Any]:
    import numpy as np

    X_all, y_all, _groups = _eligible_xy(frame, cols)
    n_eligible = len(y_all)
    pools = _nested_pools(n_eligible)

    sizes_out: list[dict[str, Any]] = []
    for size in SAMPLE_SIZES:
        idx = pools[size]
        X, y = X_all[idx], y_all[idx]
        n = len(y)

        single = [_single_split_eval(X, y, seed) for seed in SPLIT_SEEDS]
        cv_by_folds = {
            str(folds): [_cv_eval(X, y, seed, folds) for seed in SPLIT_SEEDS] for folds in FOLD_OPTIONS
        }

        valid_single = [s for s in single if s["valid"]]
        single_r2_range = None
        single_mse_range = None
        if len(valid_single) >= 2:
            r2s = [s["test_r2"] for s in valid_single]
            mses = [s["test_mse"] for s in valid_single]
            single_r2_range = round(max(r2s) - min(r2s), 6)
            single_mse_range = round(max(mses) - min(mses), 4)

        cv5 = cv_by_folds["5"]
        valid_cv5 = [c for c in cv5 if c["valid"]]
        cv5_mean_r2_range = None
        cv5_mean_mse_range = None
        if len(valid_cv5) >= 2:
            means_r2 = [c["mean_r2"] for c in valid_cv5]
            means_mse = [c["mean_mse"] for c in valid_cv5]
            cv5_mean_r2_range = round(max(means_r2) - min(means_r2), 6)
            cv5_mean_mse_range = round(max(means_mse) - min(means_mse), 4)

        any_negative_single_r2 = any(s["test_r2"] < 0 for s in valid_single)
        any_negative_cv5_mean_r2 = any(c["mean_r2"] < 0 for c in valid_cv5)

        sizes_out.append(
            {
                "sample_size": size,
                "n_actual": n,
                "single_split": single,
                "cv_by_folds": cv_by_folds,
                "single_split_r2_range_across_seeds": single_r2_range,
                "single_split_mse_range_across_seeds": single_mse_range,
                "cv5_mean_r2_range_across_seeds": cv5_mean_r2_range,
                "cv5_mean_mse_range_across_seeds": cv5_mean_mse_range,
                "range_exceeds_threshold": (
                    single_r2_range is not None and single_r2_range >= INSTABILITY_R2_RANGE_THRESHOLD
                ),
                "any_negative_single_split_r2": any_negative_single_r2,
                "any_negative_cv5_mean_r2": any_negative_cv5_mean_r2,
                "instability_meaningful": any_negative_single_r2,
            }
        )

    meaningful_sizes = [s["sample_size"] for s in sizes_out if s["instability_meaningful"]]
    meaningful_below_100 = [s for s in meaningful_sizes if isinstance(s, int) and s < 100]
    instability_requires_small_n = bool(meaningful_sizes) and all(
        isinstance(s, int) and s < 100 for s in meaningful_sizes
    )

    return {
        "n_eligible": n_eligible,
        "fixed_k": FIXED_K,
        "sample_sizes": SAMPLE_SIZES,
        "split_seeds": SPLIT_SEEDS,
        "fold_options": FOLD_OPTIONS,
        "single_split_test_size": SINGLE_SPLIT_TEST_SIZE,
        "pool_master_seed": POOL_MASTER_SEED,
        "min_train_over_k": MIN_TRAIN_OVER_K,
        "min_test_fold_size": MIN_TEST_FOLD_SIZE,
        "instability_r2_range_threshold": INSTABILITY_R2_RANGE_THRESHOLD,
        "sizes": sizes_out,
        "sizes_with_meaningful_instability": meaningful_sizes,
        "sizes_with_meaningful_instability_below_100": meaningful_below_100,
        "instability_requires_small_n": instability_requires_small_n,
    }


# --- Part B ------------------------------------------------------------


def _part_b(frame: Any, cols: list[str]) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X_all, y_all, groups_all = _eligible_xy(frame, cols)

    hs = MANIFEST["protocol"]["holdout_split"]
    X_train, X_test, y_train, y_test, g_train, _g_test = train_test_split(
        X_all, y_all, groups_all, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups_all
    )

    dev = MANIFEST["knn"]["dev_split"]
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=dev["test_size"], random_state=dev["random_state"], stratify=g_train
    )

    rows: list[dict[str, Any]] = []
    for k in CANDIDATE_KS:
        pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))
        pipe.fit(X_fit, y_fit)
        fit_pred = pipe.predict(X_fit)
        val_pred = pipe.predict(X_val)

        pipe_full = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))
        pipe_full.fit(X_train, y_train)  # refit on fit+val (= outer training partition)
        test_pred = pipe_full.predict(X_test)

        rows.append(
            {
                "k": k,
                "train_mse": round(float(mean_squared_error(y_fit, fit_pred)), 4),
                "train_r2": round(float(r2_score(y_fit, fit_pred)), 6),
                "val_mse": round(float(mean_squared_error(y_val, val_pred)), 4),
                "val_r2": round(float(r2_score(y_val, val_pred)), 6),
                "test_mse_if_locked": round(float(mean_squared_error(y_test, test_pred)), 4),
                "test_r2_if_locked": round(float(r2_score(y_test, test_pred)), 6),
            }
        )

    training_selected_k = min(rows, key=lambda r: r["train_mse"])["k"]
    validation_selected_k = min(rows, key=lambda r: r["val_mse"])["k"]
    training_row = next(r for r in rows if r["k"] == training_selected_k)
    validation_row = next(r for r in rows if r["k"] == validation_selected_k)

    return {
        "recipe": RECIPE,
        "feature_count": len(cols),
        "outer_holdout_split": hs,
        "dev_split": dev,
        "n_outer_train": int(len(y_train)),
        "n_outer_test": int(len(y_test)),
        "n_fit": int(len(y_fit)),
        "n_val": int(len(y_val)),
        "candidate_ks": CANDIDATE_KS,
        "rows": rows,
        "training_selected_k": training_selected_k,
        "validation_selected_k": validation_selected_k,
        "training_selected_result": training_row,
        "validation_selected_result": validation_row,
        "validation_selected_beats_training_selected_on_test": bool(
            validation_row["test_mse_if_locked"] < training_row["test_mse_if_locked"]
        ),
    }


# --- Part C ------------------------------------------------------------


def _part_c(frame: Any, cols: list[str]) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import GridSearchCV, KFold
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    X, y, _groups = _eligible_xy(frame, cols)

    outer = KFold(n_splits=N_OUTER, shuffle=True, random_state=OUTER_SEED)
    inner = KFold(n_splits=N_INNER, shuffle=True, random_state=INNER_SEED)

    fold_rows: list[dict[str, Any]] = []
    for fold_i, (train_idx, test_idx) in enumerate(outer.split(X)):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        pipe = Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsRegressor())])
        grid = GridSearchCV(
            pipe,
            param_grid={"knn__n_neighbors": NESTED_CANDIDATE_KS},
            scoring="neg_mean_squared_error",
            cv=inner,
        )
        grid.fit(X_tr, y_tr)
        selected_k = int(grid.best_params_["knn__n_neighbors"])
        best_inner_mse = round(float(-grid.best_score_), 4)

        inner_mse_by_k = {
            str(NESTED_CANDIDATE_KS[i]): round(float(-grid.cv_results_["mean_test_score"][i]), 4)
            for i in range(len(NESTED_CANDIDATE_KS))
        }

        pred = grid.predict(X_te)
        fold_rows.append(
            {
                "outer_fold": fold_i,
                "n_train": int(len(y_tr)),
                "n_test": int(len(y_te)),
                "inner_mse_by_k": inner_mse_by_k,
                "selected_k": selected_k,
                "best_inner_mse": best_inner_mse,
                "outer_test_mse": round(float(mean_squared_error(y_te, pred)), 4),
                "outer_test_r2": round(float(r2_score(y_te, pred)), 6),
            }
        )

    outer_mse = [r["outer_test_mse"] for r in fold_rows]
    outer_r2 = [r["outer_test_r2"] for r in fold_rows]
    selected_ks = [r["selected_k"] for r in fold_rows]

    return {
        "recipe": RECIPE,
        "feature_count": len(cols),
        "n_eligible": int(len(y)),
        "candidate_ks": NESTED_CANDIDATE_KS,
        "n_outer": N_OUTER,
        "n_inner": N_INNER,
        "outer_seed": OUTER_SEED,
        "inner_seed": INNER_SEED,
        "outer_cv": f"KFold(n_splits={N_OUTER}, shuffle=True, random_state={OUTER_SEED})",
        "inner_cv": f"KFold(n_splits={N_INNER}, shuffle=True, random_state={INNER_SEED})",
        "fold_rows": fold_rows,
        "selected_k_per_fold": selected_ks,
        "selected_k_varies_across_folds": len(set(selected_ks)) > 1,
        "mean_outer_test_mse": round(float(np.mean(outer_mse)), 4),
        "std_outer_test_mse": round(float(np.std(outer_mse)), 4),
        "mean_outer_test_r2": round(float(np.mean(outer_r2)), 6),
        "std_outer_test_r2": round(float(np.std(outer_r2)), 6),
    }


def run_audit() -> dict[str, Any]:
    frame = load_modeling_frame()
    cols = _feature_columns(frame)

    return {
        "generated_by": "scripts/wp27_validation_audit.py --run",
        "target": TARGET,
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "part_a_sample_size_stability": _part_a(frame, cols),
        "part_b_train_val_test_tuning": _part_b(frame, cols),
        "part_c_nested_cv": _part_c(frame, cols),
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_run() -> int:
    results = run_audit()
    text = serialize(results)
    RESULT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_summary(results)
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
    _print_summary(results)
    return 0


def validate(results: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if results.get("target") != TARGET:
        problems.append("target must be 'age'")
    if results.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    a = results.get("part_a_sample_size_stability", {})
    if a.get("fixed_k") != FIXED_K:
        problems.append("part A fixed_k must equal FIXED_K")
    if a.get("sample_sizes") != SAMPLE_SIZES:
        problems.append("part A sample_sizes does not match the predeclared grid")
    if a.get("split_seeds") != SPLIT_SEEDS:
        problems.append("part A split_seeds does not match the predeclared grid")

    b = results.get("part_b_train_val_test_tuning", {})
    if b.get("candidate_ks") != CANDIDATE_KS:
        problems.append("part B candidate_ks does not match the predeclared grid")
    rows = b.get("rows", [])
    if rows:
        recomputed_train_sel = min(rows, key=lambda r: r["train_mse"])["k"]
        recomputed_val_sel = min(rows, key=lambda r: r["val_mse"])["k"]
        if recomputed_train_sel != b.get("training_selected_k"):
            problems.append("part B training_selected_k disagrees with recomputed argmin(train_mse)")
        if recomputed_val_sel != b.get("validation_selected_k"):
            problems.append("part B validation_selected_k disagrees with recomputed argmin(val_mse)")

    c = results.get("part_c_nested_cv", {})
    if c.get("candidate_ks") != NESTED_CANDIDATE_KS:
        problems.append("part C candidate_ks does not match the predeclared grid")
    if len(c.get("fold_rows", [])) != N_OUTER:
        problems.append(f"part C must report exactly {N_OUTER} outer folds")

    return problems


def _print_summary(results: dict[str, Any]) -> None:
    a = results["part_a_sample_size_stability"]
    print()
    print(f"=== Part A: sample-size stability (fixed k={a['fixed_k']}, n_eligible={a['n_eligible']}) ===")
    print(f"{'N':>6s} {'single R2 range':>16s} {'CV5 mean R2 range':>18s} {'meaningful?':>12s}")
    for s in a["sizes"]:
        print(
            f"{str(s['sample_size']):>6s} {str(s['single_split_r2_range_across_seeds']):>16s} "
            f"{str(s['cv5_mean_r2_range_across_seeds']):>18s} {str(s['instability_meaningful']):>12s}"
        )
    print(f"sizes with meaningful instability: {a['sizes_with_meaningful_instability']}")
    print(f"instability requires N<100: {a['instability_requires_small_n']}")

    b = results["part_b_train_val_test_tuning"]
    print()
    print(f"=== Part B: train/validation/test tuning (n_fit={b['n_fit']}, n_val={b['n_val']}, n_test={b['n_outer_test']}) ===")
    print(f"training-selected k = {b['training_selected_k']}  (train MSE {b['training_selected_result']['train_mse']})")
    print(f"validation-selected k = {b['validation_selected_k']}  (val MSE {b['validation_selected_result']['val_mse']})")
    print(f"  training-selected k, locked test MSE = {b['training_selected_result']['test_mse_if_locked']}, R2 = {b['training_selected_result']['test_r2_if_locked']}")
    print(f"  validation-selected k, locked test MSE = {b['validation_selected_result']['test_mse_if_locked']}, R2 = {b['validation_selected_result']['test_r2_if_locked']}")
    print(f"  validation-selected beats training-selected on this test set: {b['validation_selected_beats_training_selected_on_test']}")

    c = results["part_c_nested_cv"]
    print()
    print(f"=== Part C: nested CV ({c['n_outer']} outer x {c['n_inner']} inner folds) ===")
    for r in c["fold_rows"]:
        print(f"  outer fold {r['outer_fold']}: selected k={r['selected_k']:>3d}  outer-test MSE={r['outer_test_mse']:>8.2f}  R2={r['outer_test_r2']:+.4f}")
    print(f"mean outer-test MSE = {c['mean_outer_test_mse']} (sd {c['std_outer_test_mse']})")
    print(f"mean outer-test R2 = {c['mean_outer_test_r2']} (sd {c['std_outer_test_r2']})")
    print(f"selected k varies across folds: {c['selected_k_varies_across_folds']}  ({c['selected_k_per_fold']})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
