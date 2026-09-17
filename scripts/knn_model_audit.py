#!/usr/bin/env python3
"""Reproducible KNN model audit for Exercise 2 (WP19: fixed worked-example k).

Goal: verify -- empirically, before/after writing the notebook -- the locked
held-out performance of the standardized KNN-regression worked example at the
course-design-predeclared ``K_EXAMPLE = 20``, and confirm that the canonical
feature recipe is a reasonable choice compared with two smaller predeclared
anatomical bundles evaluated at the exact same fixed k.

WP19 removed the early cross-validation / formal parameter-selection lesson
from Exercise 2. This script no longer searches candidate ``k`` values or
selects one by cross-validation: every candidate below is evaluated at the
single fixed ``K_EXAMPLE = 20``, exactly as the notebook's worked example
does. There is no hidden search that happens to return 20.

Design rules (WP19):

* every model is ``Pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))``
  so scaling is learned from training data only;
* ``K_EXAMPLE = 20`` is fixed by course design, not chosen by any selection
  procedure inside this script;
* the outer test set (Exercise 2's ``train_test_split(test_size=0.25,
  random_state=42, stratify=group)``) is evaluated exactly once per
  candidate;
* the special endpoint "k equals every participant in the fitting set" is
  still evaluated as a diagnostic: fit once on the full outer-training
  partition (753 rows) with ``k = n_train`` and predict the untouched outer
  test set once. At that k, every prediction is the training-partition mean
  (verified structurally, not just numerically).

Predeclared feature spaces (WP13 section 1, unchanged by WP19):

1. the exact Exercise 2 canonical recipe -- ``all-eligible`` bilateral cortical
   thickness, p = 360 (this is what the notebook uses);
2. two already-predeclared, smaller anatomical bundles from
   ``book/config/abide_modeling.json`` (``frontoparietal`` p = 78,
   ``occipital`` p = 46), evaluated at the same fixed k = 20 for comparison
   only -- not for selecting a feature space by search.

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
K_EXAMPLE = 20

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


def _locked_test_eval(X_train, y_train, X_test, y_test, k: int) -> dict[str, Any]:
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
            "k_example": K_EXAMPLE,
            "note": (
                "WP19: k = 20 is fixed by course design for the notebook's worked "
                "example, not selected by cross-validation or any other search. "
                "Every candidate feature space below is evaluated at this same "
                "fixed k, for comparison only. The outer test set is evaluated "
                "exactly once per candidate."
            ),
        },
        "candidates": [],
    }

    for space in FEATURE_SPACES:
        cols = _feature_columns(frame, space)
        p = len(cols)
        X_train, X_test, y_train, y_test = _outer_split(frame, cols)
        n_train, n_test = len(y_train), len(y_test)

        locked = _locked_test_eval(X_train, y_train, X_test, y_test, K_EXAMPLE)
        endpoint = _fitting_set_endpoint(X_train, y_train, X_test, y_test)

        results["candidates"].append(
            {
                "feature_space": space["name"],
                "bundle": space["bundle"],
                "measures": space["measures"],
                "p": p,
                "usable_n": int(n_train + n_test),
                "n_train": n_train,
                "n_test": n_test,
                "k_example": K_EXAMPLE,
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
    if results.get("protocol", {}).get("k_example") != K_EXAMPLE:
        problems.append(f"protocol.k_example must be {K_EXAMPLE}")
    names = {c["feature_space"] for c in results.get("candidates", [])}
    expected = {s["name"] for s in FEATURE_SPACES}
    if names != expected:
        problems.append(f"candidates cover {names}, expected {expected}")
    for c in results.get("candidates", []):
        if c["k_example"] != K_EXAMPLE:
            problems.append(f"{c['feature_space']}: k_example must be {K_EXAMPLE}")
        if c["locked_test_eval"]["k"] != K_EXAMPLE:
            problems.append(f"{c['feature_space']}: locked_test_eval.k must be {K_EXAMPLE}")
        ep = c["fitting_set_endpoint"]
        if ep["k"] != c["n_train"]:
            problems.append(f"{c['feature_space']}: fitting_set_endpoint k must equal n_train")
        if not ep["all_predictions_equal_training_mean"]:
            problems.append(f"{c['feature_space']}: k=n_train did not predict the training mean everywhere")
    return problems


def _print_table(results: dict[str, Any]) -> None:
    print()
    print(f"=== KNN audit for target={results['target']} (runtime {results.get('runtime_seconds', '?')}s) ===")
    hdr = f"{'feature space':38s} {'p':>4s} {'n_tr':>5s} {'n_te':>5s} {'k':>4s} {'testR2':>8s} {'k=n_fit testR2':>15s}"
    print(hdr)
    print("-" * len(hdr))
    for c in results["candidates"]:
        print(
            f"{c['feature_space']:38.38s} {c['p']:4d} {c['n_train']:5d} {c['n_test']:5d} "
            f"{c['k_example']:4d} {c['locked_test_eval']['test_r2']:+8.4f} "
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
