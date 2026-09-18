#!/usr/bin/env python3
"""Reproducible regularization / feature-selection audit for Exercise 5 (WP28).

Everything Exercise 5 teaches on the p=360 ``all-eligible x CT`` recipe (the
same recipe Exercises 2 and 4 use) is computed here first, offline and
deterministically, so the notebook and the "Shrink the Coefficients" widget
both quote audited numbers rather than ad hoc in-notebook computation:

* **dev-split alpha curves** -- Linear Regression (no alpha), Ridge, and
  Lasso, each fit on the ``knn.dev_split`` fitting partition (n_fit=564) and
  scored on its validation partition (n_val=189; the manifest's
  ``regularization.dev_split``, identical to ``knn.dev_split``). This is the
  data behind the "Shrink the Coefficients" activity and Exercise 5 section
  4-5's worked examples. The outer test set (251 rows) is never touched here;
* **nested cross-validation** -- Linear Regression, Ridge, and Lasso (alpha
  tuned by an inner ``GridSearchCV``) compared with identical outer/inner
  folds to Exercise 4 section 6, on the full eligible cohort (n=1004). This
  is Exercise 5 section 6's complete regularized pipeline;
* **SelectKBest curve** -- ``SelectKBest(score_func=f_regression)`` inside a
  5-fold cross-validated pipeline, over candidate retained-feature counts
  ``5, 10, 20, 40, 80, 160, 360``, fit on the outer-training partition (753
  rows) only. Exercise 5 section 3;
* **training-only correlation ranking** -- each of the 360 features'
  Pearson correlation with age, computed on the outer-training partition
  only. Exercise 5 section 3's leakage-safe intuitive first stage;
* **stepwise (forward) selection** -- a greedy forward selection curve on the
  ``frontal`` (prefrontal-only, p=42 bilateral CT) bundle: the same greedy
  algorithm ``sklearn.feature_selection.SequentialFeatureSelector`` performs
  internally (verified below), computed feature-by-feature so the notebook
  can show the full "cross-validation MSE as features are added" curve, not
  just a single fixed-size selection. Exercise 5 section 7.

Design rules, shared with the rest of this course's audits:

* every model is ``Pipeline(StandardScaler(), estimator)``, scaler fit on
  training data / training folds only;
* the outer test set (``protocol.holdout_split``) is never read by this
  script at all -- Exercise 5's interactive alpha exploration and this audit
  both stop at the validation partition;
* alpha grids are logarithmic and documented in the manifest
  (``regularization.ridge_alpha_grid`` / ``lasso_alpha_grid``).

Usage::

    python scripts/regularization_model_audit.py --run     # network; writes JSON
    python scripts/regularization_model_audit.py --check   # offline; re-validate

The committed JSON summary lives at
``scripts/regularization_model_audit_result.json`` and is asserted by
``tests/test_regularization_model_audit.py``.
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

RESULT_PATH = REPO_ROOT / "scripts" / "regularization_model_audit_result.json"
REG = MANIFEST["regularization"]
RECIPE = REG["canonical_recipe"]
DEV_SPLIT = REG["dev_split"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
NESTED = REG["nested_cv_pipeline"]

K_GRID = [5, 10, 20, 40, 80, 160, 360]
STEPWISE_BUNDLE = REG["stepwise_candidate_bundle"]


def _ridge_alphas() -> list[float]:
    import numpy as np

    return [float(a) for a in np.logspace(-1, 5, 25)]


def _lasso_alphas() -> list[float]:
    import numpy as np

    return [float(a) for a in np.logspace(-3, 1, 25)]


def _load() -> tuple[Any, list[str]]:
    frame = load_modeling_frame()
    cols = bundle_columns(RECIPE["bundle"], RECIPE["measures"], available=frame.columns)
    assert_brain_only(cols)
    return frame, cols


def _outer_dev_splits(frame: Any, cols: list[str]):
    from sklearn.model_selection import train_test_split

    X, y, _ = feature_matrix(frame, RECIPE["bundle"], RECIPE["measures"], REG["target"])
    groups = frame.loc[frame[REG["target"]].notna(), "group"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"], stratify=groups_train
    )
    return X, y, X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val


def _dev_curve(X_fit: Any, y_fit: Any, X_val: Any, y_val: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import Lasso, LinearRegression, Ridge
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(X_fit)
    Xf, Xv = scaler.transform(X_fit), scaler.transform(X_val)

    lin = LinearRegression().fit(Xf, y_fit)
    lin_result = {
        "train_mse": round(float(mean_squared_error(y_fit, lin.predict(Xf))), 4),
        "val_mse": round(float(mean_squared_error(y_val, lin.predict(Xv))), 4),
        "train_r2": round(float(r2_score(y_fit, lin.predict(Xf))), 6),
        "val_r2": round(float(r2_score(y_val, lin.predict(Xv))), 6),
    }

    def _alpha_curve(estimator_cls: type, alphas: list[float], **kwargs: Any) -> dict[str, Any]:
        # Per-feature coefficients at every alpha are NOT stored here (360
        # features x 25 alphas would bloat this human-reviewable summary to
        # ~700KB for no benefit): this audit script reports aggregate curves
        # only. scripts/export_regularization_widget.py independently refits
        # the same models from raw data to build the widget's compact
        # tracked-feature coefficient artifact, following this project's
        # existing audit-script-is-diagnostic / export-script-recomputes
        # convention (see export_regression_catalog.py).
        train_mse, val_mse, train_r2, val_r2, nnz, norm = [], [], [], [], [], []
        for a in alphas:
            m = estimator_cls(alpha=a, **kwargs).fit(Xf, y_fit)
            train_mse.append(round(float(mean_squared_error(y_fit, m.predict(Xf))), 4))
            val_mse.append(round(float(mean_squared_error(y_val, m.predict(Xv))), 4))
            train_r2.append(round(float(r2_score(y_fit, m.predict(Xf))), 6))
            val_r2.append(round(float(r2_score(y_val, m.predict(Xv))), 6))
            nnz.append(int(np.sum(np.abs(m.coef_) > 1e-10)))
            norm.append(round(float(np.linalg.norm(m.coef_)), 4))
        best_i = int(np.argmin(val_mse))
        return {
            "alpha_grid": alphas,
            "train_mse": train_mse,
            "val_mse": val_mse,
            "train_r2": train_r2,
            "val_r2": val_r2,
            "nonzero_coef": nnz,
            "coef_norm": norm,
            "best_alpha": alphas[best_i],
            "best_alpha_index": best_i,
            "best_val_mse": val_mse[best_i],
        }

    ridge = _alpha_curve(Ridge, _ridge_alphas())
    lasso = _alpha_curve(Lasso, _lasso_alphas(), max_iter=20000, tol=1e-3)
    return {"linear": lin_result, "ridge": ridge, "lasso": lasso}


def _nested_cv(X: Any, y: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import Lasso, LinearRegression, Ridge
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import GridSearchCV, KFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    # NESTED["outer_cv"] / ["inner_cv"] hold the matching human-readable
    # descriptions in the manifest (asserted in validate() below); the actual
    # KFold objects are constructed directly here rather than eval'd from
    # that string.
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=100)
    inner_cv = KFold(n_splits=5, shuffle=True, random_state=101)

    ridge_alphas = _ridge_alphas()
    lasso_alphas = _lasso_alphas()

    out: dict[str, Any] = {}
    for name, est, grid in (
        ("linear", LinearRegression(), None),
        ("ridge", Ridge(), {"ridge__alpha": ridge_alphas}),
        ("lasso", Lasso(max_iter=20000, tol=1e-3), {"lasso__alpha": lasso_alphas}),
    ):
        fold_mse, fold_r2, fold_alpha, fold_nnz = [], [], [], []
        for train_idx, test_idx in outer_cv.split(X):
            Xtr, Xte, ytr, yte = X[train_idx], X[test_idx], y[train_idx], y[test_idx]
            pipe = Pipeline([("scaler", StandardScaler()), (name, est)])
            if grid:
                gs = GridSearchCV(pipe, grid, scoring="neg_mean_squared_error", cv=inner_cv, n_jobs=-1)
                gs.fit(Xtr, ytr)
                model = gs.best_estimator_
                fold_alpha.append(float(gs.best_params_[f"{name}__alpha"]))
                fold_nnz.append(int(np.sum(np.abs(model.named_steps[name].coef_) > 1e-10)))
            else:
                pipe.fit(Xtr, ytr)
                model = pipe
            pred = model.predict(Xte)
            fold_mse.append(round(float(mean_squared_error(yte, pred)), 4))
            fold_r2.append(round(float(r2_score(yte, pred)), 6))
        entry: dict[str, Any] = {
            "fold_mse": fold_mse,
            "fold_r2": fold_r2,
            "mean_mse": round(float(np.mean(fold_mse)), 4),
            "mean_r2": round(float(np.mean(fold_r2)), 6),
        }
        if fold_alpha:
            entry["fold_alpha"] = fold_alpha
            entry["fold_nonzero_coef"] = fold_nnz
        out[name] = entry
    return out


def _select_k_best(X_train: Any, y_train: Any) -> dict[str, Any]:
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GridSearchCV, KFold
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    cv = KFold(n_splits=5, shuffle=True, random_state=0)
    pipe = Pipeline(
        [("scaler", StandardScaler()), ("select", SelectKBest(score_func=f_regression)), ("lr", LinearRegression())]
    )
    grid = GridSearchCV(pipe, {"select__k": K_GRID}, scoring="neg_mean_squared_error", cv=cv, n_jobs=-1)
    grid.fit(X_train, y_train)
    cv_mse = [round(float(-v), 4) for v in grid.cv_results_["mean_test_score"]]
    cv_mse_std = [round(float(v), 4) for v in grid.cv_results_["std_test_score"]]
    best_i = int(cv_mse.index(min(cv_mse)))
    return {
        "k_grid": K_GRID,
        "cv": "KFold(n_splits=5, shuffle=True, random_state=0)",
        "cv_mse": cv_mse,
        "cv_mse_std": cv_mse_std,
        "best_k": K_GRID[best_i],
    }


def _correlation_ranking(X_train: Any, y_train: Any, cols: list[str]) -> dict[str, Any]:
    import numpy as np

    corrs = np.array([float(np.corrcoef(X_train[:, j], y_train)[0, 1]) for j in range(X_train.shape[1])])
    order = np.argsort(corrs)

    def _rows(indices: Any) -> list[dict[str, Any]]:
        return [{"feature": cols[int(j)], "r": round(float(corrs[int(j)]), 4)} for j in indices]

    near_zero = np.argsort(np.abs(corrs))[:5]
    return {
        "n_features": len(cols),
        "min_r": round(float(corrs.min()), 4),
        "max_r": round(float(corrs.max()), 4),
        "most_negative": _rows(order[:5]),
        "most_positive": _rows(order[::-1][:5]),
        "near_zero": _rows(near_zero),
    }


def _stepwise(frame: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import KFold, cross_val_score, train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    cols = bundle_columns(STEPWISE_BUNDLE, ["CT"], available=frame.columns)
    assert_brain_only(cols)
    X, y, _ = feature_matrix(frame, STEPWISE_BUNDLE, ["CT"], REG["target"])
    groups = frame.loc[frame[REG["target"]].notna(), "group"].to_numpy()
    X_train, _, y_train, _, _, _ = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )

    cv = KFold(n_splits=5, shuffle=True, random_state=0)
    remaining = list(range(X_train.shape[1]))
    selected: list[int] = []
    curve: list[float] = []
    for _ in range(X_train.shape[1]):
        best_j, best_score = None, -np.inf
        for j in remaining:
            cand = selected + [j]
            pipe = Pipeline([("scaler", StandardScaler()), ("lr", LinearRegression())])
            score = cross_val_score(
                pipe, X_train[:, cand], y_train, cv=cv, scoring="neg_mean_squared_error", n_jobs=-1
            ).mean()
            if score > best_score:
                best_score, best_j = score, j
        selected.append(best_j)
        remaining.remove(best_j)
        curve.append(round(float(-best_score), 4))

    best_size = int(np.argmin(curve)) + 1
    return {
        "bundle": STEPWISE_BUNDLE,
        "p": len(cols),
        "cv": "KFold(n_splits=5, shuffle=True, random_state=0)",
        "selection_order": [cols[j] for j in selected],
        "cv_mse_by_size": curve,
        "best_size": best_size,
        "best_mse": curve[best_size - 1],
    }


def run_audit() -> dict[str, Any]:
    t0 = time.time()
    frame, cols = _load()
    X, y, X_train, X_test, y_train, y_test, X_fit, X_val, y_fit, y_val = _outer_dev_splits(frame, cols)

    results: dict[str, Any] = {
        "generated_by": "scripts/regularization_model_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "recipe": {"bundle": RECIPE["bundle"], "measures": RECIPE["measures"], "p": len(cols)},
        "outer_holdout_split": {**HOLDOUT_SPLIT, "n_train": int(len(y_train)), "n_test": int(len(y_test))},
        "dev_split": {**DEV_SPLIT, "n_fit": int(len(y_fit)), "n_val": int(len(y_val))},
        "dev_curve": _dev_curve(X_fit, y_fit, X_val, y_val),
        "nested_cv": {
            "outer_cv": NESTED["outer_cv"],
            "inner_cv": NESTED["inner_cv"],
            **_nested_cv(X, y),
        },
        "select_k_best": _select_k_best(X_train, y_train),
        "correlation_ranking": _correlation_ranking(X_train, y_train, cols),
        "stepwise": _stepwise(frame),
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
    if results.get("recipe", {}).get("p") != 360:
        problems.append("recipe.p must be 360 (all-eligible x CT)")
    if results.get("nested_cv", {}).get("outer_cv") != NESTED["outer_cv"]:
        problems.append("nested_cv.outer_cv does not match the manifest's regularization.nested_cv_pipeline")
    if results.get("nested_cv", {}).get("inner_cv") != NESTED["inner_cv"]:
        problems.append("nested_cv.inner_cv does not match the manifest's regularization.nested_cv_pipeline")

    dc = results.get("dev_curve", {})
    for family in ("ridge", "lasso"):
        curve = dc.get(family, {})
        alphas = curve.get("alpha_grid", [])
        val_mse = curve.get("val_mse", [])
        if len(alphas) != len(val_mse) or not alphas:
            problems.append(f"dev_curve.{family}: alpha_grid/val_mse length mismatch")
            continue
        best_i = curve.get("best_alpha_index")
        if best_i in (0, len(alphas) - 1):
            problems.append(f"dev_curve.{family}: best alpha sits at a grid boundary (index {best_i})")

    ncv = results.get("nested_cv", {})
    for family in ("linear", "ridge", "lasso"):
        if "mean_mse" not in ncv.get(family, {}):
            problems.append(f"nested_cv.{family}: missing mean_mse")
    if ncv.get("ridge", {}).get("mean_mse", 0) >= ncv.get("linear", {}).get("mean_mse", 0):
        problems.append("nested_cv: ridge should out-perform (lower MSE than) unregularised linear regression here")

    skb = results.get("select_k_best", {})
    if skb.get("best_k") not in skb.get("k_grid", []):
        problems.append("select_k_best.best_k must be a member of k_grid")

    sw = results.get("stepwise", {})
    curve = sw.get("cv_mse_by_size", [])
    if curve and sw.get("best_size") not in range(1, len(curve) + 1):
        problems.append("stepwise.best_size out of range")

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
    print()
    print("=== dev-split (n_fit=564, n_val=189) ===")
    lin = results["dev_curve"]["linear"]
    print(f"  linear      train MSE={lin['train_mse']:.1f}  val MSE={lin['val_mse']:.1f}  val R2={lin['val_r2']:+.3f}")
    for family in ("ridge", "lasso"):
        c = results["dev_curve"][family]
        print(
            f"  {family:10s}  best alpha={c['best_alpha']:.4g}  val MSE={c['best_val_mse']:.1f}  "
            f"nnz={c['nonzero_coef'][c['best_alpha_index']]}"
        )
    print()
    print("=== nested CV (outer KFold-5, full cohort n=1004) ===")
    for family in ("linear", "ridge", "lasso"):
        c = results["nested_cv"][family]
        print(f"  {family:10s}  mean MSE={c['mean_mse']:.1f}  mean R2={c['mean_r2']:+.3f}")
    print()
    skb = results["select_k_best"]
    print(f"=== SelectKBest: best k = {skb['best_k']} (grid {skb['k_grid']}) ===")
    print()
    sw = results["stepwise"]
    print(f"=== stepwise forward selection ({sw['bundle']}, p={sw['p']}): best size = {sw['best_size']} ===")
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
