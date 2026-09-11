#!/usr/bin/env python3
"""Reproducible regression model audit for Exercise 2 (WP12 section 5).

Goal: decide -- empirically, before restructuring the notebook -- whether ``age``
or ``FIQ`` is the honest main ordinary-linear-regression example, and whether
ridge or lasso stabilises a broad brain-wide feature set for either target.

Design rules (WP12 section 5.3):

* every model is ``Pipeline(StandardScaler(), estimator)`` so scaling is learned
  from training data / training folds only;
* hyperparameters (ridge / lasso ``alpha``) are chosen by an **inner** CV on the
  training partition only, via ``RidgeCV`` / ``LassoCV`` nested inside the outer
  split;
* the outer estimate is a deterministic 5-fold cross-validation
  (``KFold(shuffle=True, random_state=0)`` -- the same protocol the manifest
  already pins). Nothing here consults a locked held-out test set to pick a
  target, feature set, model family, or alpha;
* additionally, for the two candidates the notebook will actually show, one
  locked held-out split (``test_size=0.25, random_state=42, stratify=group`` --
  the manifest ``protocol.holdout_split``) is evaluated **exactly once** and
  reported next to the nested-CV number, purely so the notebook can quote a
  single train/test figure.

Predeclared feature spaces (WP12 section 5.2):

1. ``all-eligible`` x every measure (CT, Area, Vol, LGI together) -- every
   eligible cortical brain feature across all measures (p = 1432);
2. ``all-eligible`` x one measurement family at a time (p = 360 each);
3. the predeclared compact anatomical bundle ``frontoparietal`` x CT (p = 78) --
   scientifically motivated for FIQ (P-FIT); run for age too as a comparison.

Alpha grids (documented, logarithmic):

* ridge: ``np.logspace(-1, 6, 29)``  (0.1 ... 1e6)
* lasso: ``np.logspace(-3, 2, 26)``  (1e-3 ... 100)

Outcomes: ``age`` (native brain-table column, N about 1004) and ``FIQ`` (merged
in from the phenotypic file, N about 908).

Usage::

    python scripts/regression_model_audit.py --run     # network; prints + writes JSON
    python scripts/regression_model_audit.py --check    # offline; re-validate committed JSON

The committed JSON summary lives at ``scripts/regression_model_audit_result.json``
and is asserted by ``tests/test_regression_model_audit.py``.
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
    classify_columns,
    load_modeling_frame,
)

RESULT_PATH = REPO_ROOT / "scripts" / "regression_model_audit_result.json"

OUTER_CV_SEED = 0
INNER_CV_SEED = 1
N_SPLITS = 5
RIDGE_ALPHAS = [float(a) for a in __import__("numpy").logspace(-1, 6, 29)]
LASSO_ALPHAS = [float(a) for a in __import__("numpy").logspace(-3, 2, 26)]

# The predeclared feature spaces. "measures" of None => every measure.
FEATURE_SPACES: list[dict[str, Any]] = [
    {"name": "all-eligible x all measures", "bundle": "all-eligible", "measures": ["CT", "Area", "Vol", "LGI"]},
    {"name": "all-eligible x CT", "bundle": "all-eligible", "measures": ["CT"]},
    {"name": "all-eligible x Area", "bundle": "all-eligible", "measures": ["Area"]},
    {"name": "all-eligible x Vol", "bundle": "all-eligible", "measures": ["Vol"]},
    {"name": "all-eligible x LGI", "bundle": "all-eligible", "measures": ["LGI"]},
    {"name": "frontoparietal x CT (P-FIT compact)", "bundle": "frontoparietal", "measures": ["CT"]},
]

TARGETS = ["age", "FIQ"]


def _feature_columns(frame: Any, space: dict[str, Any]) -> list[str]:
    cols = bundle_columns(space["bundle"], space["measures"], available=frame.columns)
    assert_brain_only(cols)
    return cols


def _xy(frame: Any, target: str, cols: list[str]):
    import numpy as np

    if target in cols:
        raise ValueError("leakage: target is in the feature list")
    present = frame[target].notna().to_numpy()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, target].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()
    if np.isnan(X).any():
        raise ValueError(f"{target}: brain features contain missing values")
    return X, y, groups


def _evaluate(model_family: str, X: Any, y: Any) -> dict[str, Any]:
    """Nested / isolated CV for one (feature space, target, model family)."""
    import numpy as np
    from sklearn.linear_model import LassoCV, LinearRegression, RidgeCV
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    outer = KFold(n_splits=N_SPLITS, shuffle=True, random_state=OUTER_CV_SEED)
    inner = KFold(n_splits=N_SPLITS, shuffle=True, random_state=INNER_CV_SEED)

    fold_r2: list[float] = []
    fold_mse: list[float] = []
    fold_alpha: list[float] = []
    fold_nnz: list[int] = []
    n_train_sizes: list[int] = []

    for train_idx, test_idx in outer.split(X):
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        n_train_sizes.append(len(train_idx))

        if model_family == "linear":
            est = make_pipeline(StandardScaler(), LinearRegression())
        elif model_family == "ridge":
            est = make_pipeline(
                StandardScaler(),
                RidgeCV(alphas=RIDGE_ALPHAS, cv=inner, scoring="r2"),
            )
        elif model_family == "lasso":
            est = make_pipeline(
                StandardScaler(),
                LassoCV(
                    alphas=LASSO_ALPHAS,
                    cv=inner,
                    random_state=INNER_CV_SEED,
                    max_iter=5000,
                    tol=1e-3,
                    n_jobs=-1,
                ),
            )
        else:  # pragma: no cover
            raise ValueError(model_family)

        est.fit(Xtr, ytr)
        pred = est.predict(Xte)
        fold_r2.append(float(r2_score(yte, pred)))
        fold_mse.append(float(mean_squared_error(yte, pred)))

        final = est.steps[-1][1]
        if model_family == "ridge":
            fold_alpha.append(float(final.alpha_))
            fold_nnz.append(int(np.sum(np.abs(final.coef_) > 0)))
        elif model_family == "lasso":
            fold_alpha.append(float(final.alpha_))
            fold_nnz.append(int(np.sum(np.abs(final.coef_) > 1e-10)))

    out: dict[str, Any] = {
        "model": model_family,
        "outer_cv": f"KFold(n_splits={N_SPLITS}, shuffle=True, random_state={OUTER_CV_SEED})",
        "n_train_per_fold": int(round(sum(n_train_sizes) / len(n_train_sizes))),
        "cv_r2_mean": round(float(np.mean(fold_r2)), 6),
        "cv_r2_std": round(float(np.std(fold_r2)), 6),
        "cv_r2_folds": [round(v, 6) for v in fold_r2],
        "cv_mse_mean": round(float(np.mean(fold_mse)), 4),
        "cv_mse_folds": [round(v, 4) for v in fold_mse],
    }
    if fold_alpha:
        out["alpha_grid"] = (
            f"np.logspace(-1, 6, 29)" if model_family == "ridge" else "np.logspace(-3, 2, 26)"
        )
        out["alpha_per_fold"] = [float(f"{a:.6g}") for a in fold_alpha]
        out["alpha_median"] = float(f"{np.median(fold_alpha):.6g}")
        out["nonzero_coef_per_fold"] = fold_nnz
        out["nonzero_coef_median"] = int(np.median(fold_nnz))
    return out


def _locked_holdout(model_family: str, X: Any, y: Any, groups: Any) -> dict[str, Any]:
    """Evaluate ONE locked held-out split exactly once (for the notebook's single
    train/test figure). Not used to choose anything."""
    import numpy as np
    from sklearn.linear_model import LassoCV, LinearRegression, RidgeCV
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold, train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    hs = MANIFEST["protocol"]["holdout_split"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups
    )
    inner = KFold(n_splits=N_SPLITS, shuffle=True, random_state=INNER_CV_SEED)
    if model_family == "linear":
        est = make_pipeline(StandardScaler(), LinearRegression())
    elif model_family == "ridge":
        est = make_pipeline(StandardScaler(), RidgeCV(alphas=RIDGE_ALPHAS, cv=inner, scoring="r2"))
    elif model_family == "lasso":
        est = make_pipeline(
            StandardScaler(),
            LassoCV(
                alphas=LASSO_ALPHAS,
                cv=inner,
                random_state=INNER_CV_SEED,
                max_iter=5000,
                tol=1e-3,
                n_jobs=-1,
            ),
        )
    else:  # pragma: no cover
        raise ValueError(model_family)
    est.fit(Xtr, ytr)
    pred = est.predict(Xte)
    res = {
        "split": f"train_test_split(test_size={hs['test_size']}, random_state={hs['random_state']}, stratify=group)",
        "n_train": int(len(ytr)),
        "n_test": int(len(yte)),
        "r2": round(float(r2_score(yte, pred)), 6),
        "mse": round(float(mean_squared_error(yte, pred)), 4),
    }
    final = est.steps[-1][1]
    if model_family in ("ridge", "lasso"):
        res["alpha"] = float(f"{final.alpha_:.6g}")
        thr = 0.0 if model_family == "ridge" else 1e-10
        res["nonzero_coef"] = int(np.sum(np.abs(final.coef_) > thr))
    return res


def run_audit() -> dict[str, Any]:
    import numpy as np

    frame = load_modeling_frame()
    taxonomy = classify_columns(frame.columns)
    brain_features = taxonomy["brain_features"]

    results: dict[str, Any] = {
        "generated_by": "scripts/regression_model_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "protocol": {
            "outer_cv": f"KFold(n_splits={N_SPLITS}, shuffle=True, random_state={OUTER_CV_SEED})",
            "inner_cv": f"KFold(n_splits={N_SPLITS}, shuffle=True, random_state={INNER_CV_SEED})",
            "ridge_alpha_grid": "np.logspace(-1, 6, 29)",
            "lasso_alpha_grid": "np.logspace(-3, 2, 26)",
            "pipeline": "Pipeline(StandardScaler(), estimator); scaler fitted on train/fold only",
            "note": "Nested CV chooses alpha with the inner CV on the training partition only. "
            "The locked held-out split is evaluated exactly once per candidate and is not used "
            "to select target, feature set, model family, or alpha.",
        },
        "targets": {},
        "candidates": [],
    }

    # target-level facts
    for target in TARGETS:
        col = frame[target]
        n = int(col.notna().sum())
        vals = col.dropna().to_numpy(dtype="float64")
        brain_na = int(frame.loc[col.notna(), brain_features].isna().to_numpy().sum())
        results["targets"][target] = {
            "usable_n": n,
            "missing_n": int(len(col) - n),
            "range": [float(np.min(vals)), float(np.max(vals))],
            "mean": round(float(np.mean(vals)), 4),
            "sd": round(float(np.std(vals)), 4),
            "missing_brain_feature_cells": brain_na,
        }

    for space in FEATURE_SPACES:
        cols = _feature_columns(frame, space)
        p = len(cols)
        for target in TARGETS:
            if space["bundle"] == "frontoparietal" and target == "age":
                # still run it, but mark that whole-brain is age's natural space
                pass
            X, y, groups = _xy(frame, target, cols)
            n_train = int(round(len(y) * (N_SPLITS - 1) / N_SPLITS))
            for family in ("linear", "ridge", "lasso"):
                if family == "linear" and p >= n_train:
                    # WP 5.3: OLS with p >= n_train is underdetermined -- compute
                    # for diagnostic comparison, label it, never recommend it.
                    ev = _evaluate(family, X, y)
                    ev["underdetermined"] = True
                    ev["underdetermined_note"] = (
                        f"p={p} >= n_train={n_train}; ordinary least squares is underdetermined "
                        "(sklearn returns the minimum-norm lstsq solution). Diagnostic only."
                    )
                else:
                    ev = _evaluate(family, X, y)
                    if family == "linear":
                        ev["underdetermined"] = False

                candidate = {
                    "target": target,
                    "feature_space": space["name"],
                    "bundle": space["bundle"],
                    "measures": space["measures"],
                    "p": p,
                    "usable_n": int(len(y)),
                    "n_train_per_fold": ev["n_train_per_fold"],
                    "p_over_n_train": round(p / ev["n_train_per_fold"], 4),
                    **{k: v for k, v in ev.items() if k != "n_train_per_fold"},
                }
                results["candidates"].append(candidate)

    # locked held-out, evaluated exactly once, only for the structures the
    # notebook will show: age (linear, whole-brain CT) and age vs FIQ regularised
    # (ridge, all-eligible x all measures).
    locked_specs = [
        ("age", "linear", {"name": "all-eligible x CT", "bundle": "all-eligible", "measures": ["CT"]}),
        ("age", "linear", {"name": "frontoparietal x CT (P-FIT compact)", "bundle": "frontoparietal", "measures": ["CT"]}),
        ("age", "ridge", {"name": "all-eligible x all measures", "bundle": "all-eligible", "measures": ["CT", "Area", "Vol", "LGI"]}),
        ("FIQ", "ridge", {"name": "all-eligible x all measures", "bundle": "all-eligible", "measures": ["CT", "Area", "Vol", "LGI"]}),
        ("FIQ", "lasso", {"name": "all-eligible x all measures", "bundle": "all-eligible", "measures": ["CT", "Area", "Vol", "LGI"]}),
        ("age", "lasso", {"name": "all-eligible x all measures", "bundle": "all-eligible", "measures": ["CT", "Area", "Vol", "LGI"]}),
    ]
    for target, family, space in locked_specs:
        cols = _feature_columns(frame, space)
        X, y, groups = _xy(frame, target, cols)
        results["candidates"].append(
            {
                "target": target,
                "feature_space": space["name"],
                "bundle": space["bundle"],
                "measures": space["measures"],
                "p": len(cols),
                "usable_n": int(len(y)),
                "locked_holdout": _locked_holdout(family, X, y, groups),
                "model": family,
                "kind": "locked-holdout-once",
            }
        )
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
    if results.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    seen_targets = {c["target"] for c in results.get("candidates", [])}
    if seen_targets != set(TARGETS):
        problems.append(f"candidates cover {seen_targets}, expected {set(TARGETS)}")
    for c in results.get("candidates", []):
        if c.get("kind") == "locked-holdout-once":
            continue
        if "cv_r2_mean" not in c:
            problems.append(f"{c['target']}/{c['feature_space']}/{c.get('model')}: no cv_r2_mean")
        if c.get("model") == "linear" and c["p"] >= c["n_train_per_fold"] and not c.get("underdetermined"):
            problems.append(f"{c['target']}/{c['feature_space']}: OLS p>=n_train not labelled underdetermined")
    return problems


def _print_table(results: dict[str, Any]) -> None:
    print()
    print("=== target facts ===")
    for t, f in results["targets"].items():
        print(f"  {t:5s} N={f['usable_n']:4d} miss={f['missing_n']:3d} "
              f"range=[{f['range'][0]:.1f},{f['range'][1]:.1f}] mean={f['mean']:.2f} sd={f['sd']:.2f} "
              f"brain-NaN={f['missing_brain_feature_cells']}")
    print()
    print("=== nested / isolated CV (outer KFold-5, alpha via inner CV) ===")
    hdr = f"{'target':5s} {'feature space':38s} {'model':7s} {'p':>5s} {'n_tr':>5s} {'p/n':>6s} {'cvR2':>9s} {'cvMSE':>11s} {'alpha~':>10s} {'nnz~':>6s}"
    print(hdr)
    print("-" * len(hdr))
    for c in results["candidates"]:
        if c.get("kind") == "locked-holdout-once":
            continue
        alpha = c.get("alpha_median", "")
        nnz = c.get("nonzero_coef_median", "")
        flag = "  UNDERDET" if c.get("underdetermined") else ""
        print(f"{c['target']:5s} {c['feature_space']:38.38s} {c['model']:7s} {c['p']:5d} "
              f"{c['n_train_per_fold']:5d} {c['p_over_n_train']:6.2f} {c['cv_r2_mean']:+9.4f} "
              f"{c['cv_mse_mean']:11.3f} {str(alpha):>10s} {str(nnz):>6s}{flag}")
    print()
    print("=== locked held-out split, evaluated once (NOT used for selection) ===")
    for c in results["candidates"]:
        if c.get("kind") != "locked-holdout-once":
            continue
        lh = c["locked_holdout"]
        extra = ""
        if "alpha" in lh:
            extra = f" alpha={lh['alpha']} nnz={lh['nonzero_coef']}"
        print(f"  {c['target']:5s} {c['model']:7s} {c['feature_space']:38.38s} "
              f"p={c['p']:4d} n_tr={lh['n_train']} n_te={lh['n_test']} "
              f"R2={lh['r2']:+.4f} MSE={lh['mse']:.3f}{extra}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
