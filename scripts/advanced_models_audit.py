#!/usr/bin/env python3
"""Nested cross-validation ABIDE-II age-prediction comparison for Exercise 9
(WP34, section 8): standardized OLS (reference), PCR, PLS, linear SVR, and
RBF SVR, on the identical 1004-participant, 360-cortical-thickness-feature
cohort every other exercise uses.

Every model shares the identical OUTER ``KFold(n_splits=5, shuffle=True,
random_state=100)`` (Exercise 4's own nested-cross-validation convention,
``knn.nested`` in spirit) and, for every model with a hyperparameter to
select, the identical INNER ``KFold(n_splits=5, shuffle=True,
random_state=101)`` computed once per outer fold and reused across every
model's candidate grid within that fold. All scaling/PCA/PLS fitting happens
inside the pipeline, so it is refit separately for every inner and outer
training partition. Inner selection always uses mean inner-fold MSE; each
model is refit once on the complete outer-training fold at its selected
hyperparameter(s) and evaluated exactly once on that outer-test fold.

Usage::

    python scripts/advanced_models_audit.py --run     # network; writes JSON
    python scripts/advanced_models_audit.py --check   # offline; re-validate

The committed JSON summary lives at
``scripts/advanced_models_audit_result.json`` and is asserted by
``tests/test_advanced_models_audit.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from abide_modeling_data import MANIFEST, REPO_ROOT, assert_brain_only, load_modeling_frame  # noqa: E402

RESULT_PATH = REPO_ROOT / "scripts" / "advanced_models_audit_result.json"
ADV = MANIFEST["advanced_models"]
CMP = ADV["abide_comparison"]
OUTER_CFG = CMP["outer_cv"]
INNER_CFG = CMP["inner_cv"]
MODELS = CMP["models"]
RBF_SVR_EPSILON: float = MODELS["rbf_svr"]["fixed_epsilon"]
# WP35 §14: after removing the nonconvergent C=10 candidate, the new largest
# candidate (C=1) still needs more than 5000 liblinear iterations to
# converge on real data (measured: up to ~8,924 iterations; confirmed
# converged cleanly by 20,000 across every (C, epsilon) pair still in the
# grid, at negligible added runtime cost, unlike C=10's genuine
# non-convergence even at max_iter=100000).
LINEAR_SVR_MAX_ITER = 20000


def _natural_order_columns(frame: Any) -> list[str]:
    # Same convention as pca_kmeans_audit.py / gradient_boosting_model_audit.py.
    return [c for c in frame.columns if c.startswith("fsCT_")]


def _make_pipeline(model_key: str, params: dict[str, Any]) -> Any:
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVR, LinearSVR

    if model_key == "ols":
        return Pipeline([("scale", StandardScaler()), ("model", LinearRegression())])
    if model_key == "pcr":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=params["n_components"], random_state=0)),
                ("model", LinearRegression()),
            ]
        )
    if model_key == "pls":
        return Pipeline(
            [("scale", StandardScaler()), ("model", PLSRegression(n_components=params["n_components"], scale=False))]
        )
    if model_key == "linear_svr":
        # LinearSVR (liblinear coordinate descent), not SVR(kernel="linear")
        # (libsvm SMO): identical epsilon-insensitive linear objective, but
        # SVR(kernel="linear") took 65s for a single C=10 fit on this
        # n=803, p=360 training fold (measured directly) -- roughly 800
        # such fits are needed across the nested CV grid, an infeasible
        # runtime. LinearSVR is scikit-learn's own documented recommendation
        # for exactly this n/p regime. See MANIFEST["advanced_models"]
        # ["abide_comparison"]["linear_svr_solver_note"].
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LinearSVR(C=params["C"], epsilon=params["epsilon"], max_iter=LINEAR_SVR_MAX_ITER, random_state=0)),
            ]
        )
    if model_key == "rbf_svr":
        # epsilon fixed at 1.0 (one year) rather than left at scikit-learn's
        # implicit default (0.1) -- WP35 §15: only C and gamma are tuned, to
        # keep this teaching grid manageable; epsilon is stated as fixed, not
        # optimized. See MANIFEST["advanced_models"]["abide_comparison"]
        # ["rbf_svr_epsilon_note"].
        return Pipeline(
            [("scale", StandardScaler()), ("model", SVR(kernel="rbf", C=params["C"], gamma=params["gamma"], epsilon=RBF_SVR_EPSILON))]
        )
    raise ValueError(f"unknown model_key {model_key!r}")


def _param_grid(model_key: str) -> list[dict[str, Any]]:
    grid = MODELS[model_key].get("grid")
    if grid is None:
        return [{}]
    if model_key in ("pcr", "pls"):
        return [{"n_components": n} for n in grid["n_components"]]
    if model_key == "linear_svr":
        return [{"C": c, "epsilon": e} for c in grid["C"] for e in grid["epsilon"]]
    if model_key == "rbf_svr":
        return [{"C": c, "gamma": g} for c in grid["C"] for g in grid["gamma"]]
    raise ValueError(model_key)


def _fit_predict(model_key: str, params: dict[str, Any], X_tr: Any, y_tr: Any, X_te: Any) -> Any:
    import numpy as np

    pipe = _make_pipeline(model_key, params)
    pipe.fit(X_tr, y_tr)
    pred = np.asarray(pipe.predict(X_te)).reshape(-1)
    return pred


def _select_by_inner_cv(
    model_key: str, X_tr: Any, y_tr: Any, inner_splits: list[tuple[Any, Any]], warning_sink: list[str], outer_fold: int
) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import mean_squared_error

    candidates = _param_grid(model_key)
    rows = []
    for params in candidates:
        fold_mse = []
        for tr, va in inner_splits:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                pred = _fit_predict(model_key, params, X_tr[tr], y_tr[tr], X_tr[va])
                for w in caught:
                    warning_sink.append(f"outer_fold={outer_fold} model={model_key} params={params}: {w.category.__name__}: {w.message}")
            fold_mse.append(mean_squared_error(y_tr[va], pred))
        rows.append({"params": params, "mean_mse": float(np.mean(fold_mse))})
    best = min(rows, key=lambda r: r["mean_mse"])
    return {"candidates": rows, "selected_params": best["params"], "selected_mean_cv_mse": best["mean_mse"]}


def run_audit() -> dict[str, Any]:
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import KFold

    t0 = time.time()
    frame = load_modeling_frame()
    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    if len(cols) != 360:
        raise RuntimeError(f"expected 360 cortical-thickness columns, got {len(cols)}")
    if len(frame) != 1004:
        raise RuntimeError(f"expected 1004 eligible participants, got {len(frame)}")
    if frame["age"].isna().any():
        raise RuntimeError("expected no missing age values in the eligible cohort")

    X = frame.loc[:, cols].to_numpy(dtype="float64")
    y = frame["age"].to_numpy(dtype="float64")

    outer_cv = KFold(n_splits=OUTER_CFG["n_splits"], shuffle=OUTER_CFG["shuffle"], random_state=OUTER_CFG["random_state"])
    inner_cv = KFold(n_splits=INNER_CFG["n_splits"], shuffle=INNER_CFG["shuffle"], random_state=INNER_CFG["random_state"])

    model_keys = ["ols", "pcr", "pls", "linear_svr", "rbf_svr"]
    warning_sink: list[str] = []
    per_model_folds: dict[str, list[dict[str, Any]]] = {k: [] for k in model_keys}

    for outer_fold, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]
        inner_splits = list(inner_cv.split(X_tr))  # identical inner folds for every model, this outer fold

        for model_key in model_keys:
            tuned = MODELS[model_key]["tuned"]
            if tuned:
                selection = _select_by_inner_cv(model_key, X_tr, y_tr, inner_splits, warning_sink, outer_fold)
                params = selection["selected_params"]
            else:
                selection = None
                params = {}

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                pred = _fit_predict(model_key, params, X_tr, y_tr, X_te)
                for w in caught:
                    warning_sink.append(f"outer_fold={outer_fold} model={model_key} (final fit) params={params}: {w.category.__name__}: {w.message}")

            row: dict[str, Any] = {
                "outer_fold": outer_fold,
                "n_train": int(len(y_tr)),
                "n_test": int(len(y_te)),
                "selected_params": params,
                "outer_test_mse": round(float(mean_squared_error(y_te, pred)), 4),
                "outer_test_r2": round(float(r2_score(y_te, pred)), 6),
            }
            if selection is not None:
                row["inner_candidates"] = [
                    {"params": c["params"], "mean_mse": round(c["mean_mse"], 4)} for c in selection["candidates"]
                ]
            per_model_folds[model_key].append(row)

    import numpy as np

    summary: dict[str, Any] = {}
    for model_key in model_keys:
        folds = per_model_folds[model_key]
        mses = np.array([f["outer_test_mse"] for f in folds])
        r2s = np.array([f["outer_test_r2"] for f in folds])
        summary[model_key] = {
            "label": MODELS[model_key]["label"],
            "folds": folds,
            "mean_outer_test_mse": round(float(mses.mean()), 4),
            "sd_outer_test_mse": round(float(mses.std(ddof=0)), 4),
            "mean_outer_test_r2": round(float(r2s.mean()), 6),
            "sd_outer_test_r2": round(float(r2s.std(ddof=0)), 6),
        }
        if model_key == "rbf_svr":
            # Fixed (not tuned) for this teaching comparison -- WP35 §15.
            summary[model_key]["fixed_params"] = {"epsilon": RBF_SVR_EPSILON}

    results: dict[str, Any] = {
        "generated_by": "scripts/advanced_models_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
            "phenotypeTableSha256": MANIFEST["source"]["phenotype_table"]["sha256"],
        },
        "cohort": {"n_participants": int(len(frame)), "n_features": len(cols)},
        "outer_cv": dict(OUTER_CFG),
        "inner_cv": dict(INNER_CFG),
        "models": model_keys,
        "summary": summary,
        "convergence_warnings": warning_sink,
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

    model_keys = results.get("models", [])
    if set(model_keys) != set(MODELS.keys()):
        problems.append(f"models must be exactly {sorted(MODELS.keys())}")

    if 10 in MODELS.get("linear_svr", {}).get("grid", {}).get("C", []):
        problems.append("linear_svr grid must not contain C=10 (WP35 §14: nonconvergent, never selected)")

    rbf_fixed = results.get("summary", {}).get("rbf_svr", {}).get("fixed_params", {})
    if rbf_fixed.get("epsilon") != RBF_SVR_EPSILON:
        problems.append(f"summary.rbf_svr.fixed_params.epsilon must be {RBF_SVR_EPSILON} (WP35 §15), got {rbf_fixed.get('epsilon')}")

    for w in results.get("convergence_warnings", []):
        if "linear_svr" in w:
            problems.append(f"unexpected linear_svr convergence warning after removing C=10: {w}")

    summary = results.get("summary", {})
    n_outer = results.get("outer_cv", {}).get("n_splits")
    all_test_indices_by_fold: dict[int, set[int]] = {}
    for model_key in model_keys:
        entry = summary.get(model_key, {})
        folds = entry.get("folds", [])
        if len(folds) != n_outer:
            problems.append(f"summary[{model_key}]: expected {n_outer} outer folds, got {len(folds)}")
            continue

        mses = [f["outer_test_mse"] for f in folds]
        r2s = [f["outer_test_r2"] for f in folds]
        mean_mse = sum(mses) / len(mses)
        if abs(mean_mse - entry.get("mean_outer_test_mse", -1)) > 1e-3:
            problems.append(f"summary[{model_key}]: mean_outer_test_mse does not match a fresh recomputation")
        mean_r2 = sum(r2s) / len(r2s)
        if abs(mean_r2 - entry.get("mean_outer_test_r2", -1)) > 1e-3:
            problems.append(f"summary[{model_key}]: mean_outer_test_r2 does not match a fresh recomputation")

        for f in folds:
            if MODELS[model_key]["tuned"]:
                candidates = f.get("inner_candidates", [])
                grid = _param_grid(model_key)
                if len(candidates) != len(grid):
                    problems.append(f"summary[{model_key}] outer_fold={f['outer_fold']}: inner_candidates length mismatch")
                best = min(candidates, key=lambda c: c["mean_mse"]) if candidates else None
                if best is not None and best["params"] != f.get("selected_params"):
                    problems.append(
                        f"summary[{model_key}] outer_fold={f['outer_fold']}: selected_params does not match a fresh "
                        "minimum-inner-CV-MSE recomputation"
                    )
            all_test_indices_by_fold.setdefault(f["outer_fold"], set()).add(f["n_test"])

    # Every model must see the identical outer-fold test SIZE (proxy for
    # identical outer folds, since the raw indices are not stored to keep
    # this artifact small; the notebook's own audit cell re-derives the
    # actual KFold object and confirms the fold membership directly).
    for fold, sizes in all_test_indices_by_fold.items():
        if len(sizes) != 1:
            problems.append(f"outer_fold={fold}: models disagree on n_test ({sizes}) -- outer folds must be identical")

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
    for model_key in results["models"]:
        s = results["summary"][model_key]
        fixed = s.get("fixed_params")
        fixed_note = f"  fixed={fixed}" if fixed else ""
        print(f"{s['label']:14s} mean outer-test MSE={s['mean_outer_test_mse']:.2f} (sd {s['sd_outer_test_mse']:.2f})  R2={s['mean_outer_test_r2']:+.3f}{fixed_note}")
    if results.get("convergence_warnings"):
        print(f"convergence warnings recorded: {len(results['convergence_warnings'])}")
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
