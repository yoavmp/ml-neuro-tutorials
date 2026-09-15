#!/usr/bin/env python3
"""Reproducible logistic-regression classification audit for Exercise 4 (WP18).

Exercise 4 predicts autism diagnosis from cortical structure -- the first
classification exercise in the course. WP17 fixed a single, untuned C=1.0.
WP18 replaces that with an honest selection: C is chosen by cross-validation
on the outer-training partition only, the same discipline Exercise 3 (WP13)
uses to choose k, mirrored here for logistic regression's regularization
strength. The outer test set is evaluated exactly once, after C is already
locked, never to choose it.

Design (WP18 sec 2):

* target: ``group`` (native to abide2.tsv), recoded autism (group==1) -> 1,
  control (group==2) -> 0. Positive class = autism.
* features: the exact Exercise 2/3 canonical recipe -- ``all-eligible x CT``,
  the same 360 bilateral cortical-thickness columns, brain-only (leakage
  guard enforced).
* split: ``train_test_split(test_size=0.25, random_state=42, stratify=y)`` --
  participant-level, one locked split, evaluated exactly once.
* model selection: ``Pipeline(StandardScaler(), LogisticRegression())`` inside
  ``GridSearchCV`` over ``C_GRID = np.logspace(-4, 4, 9)``, scored by ROC AUC,
  with ``StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`` on the
  outer-TRAINING partition only. ``GridSearchCV(refit=True)`` refits the
  selected pipeline on the complete outer-training partition; the outer test
  set is then evaluated exactly once, with that already-locked C.

Usage::

    python scripts/classification_model_audit.py --run     # network; prints + writes JSON
    python scripts/classification_model_audit.py --check   # offline; re-validate committed JSON

The committed JSON summary lives at
``scripts/classification_model_audit_result.json`` and is asserted by
``tests/test_classification_model_audit.py``.
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

RESULT_PATH = REPO_ROOT / "scripts" / "classification_model_audit_result.json"

CLS = MANIFEST["classification"]
TEST_SIZE = CLS["holdout_split"]["test_size"]
RANDOM_STATE = CLS["holdout_split"]["random_state"]
MAX_ITER = 5000
POSITIVE_CODE = CLS["positive_class"]["code"]  # 1 = autism
NEGATIVE_CODE = CLS["negative_class"]["code"]  # 2 = control

# Honest C selection (WP18 sec 2): a predetermined logarithmic grid, five-fold
# stratified CV on the outer-training partition only, scored by ROC AUC.
C_GRID = [10.0 ** e for e in range(-4, 5)]
CV_SPLITS = 5
CV_RANDOM_STATE = 42
CV_SCORING = "roc_auc"


def _feature_columns(frame: Any) -> list[str]:
    recipe = CLS["canonical_recipe"]
    cols = bundle_columns(recipe["bundle"], recipe["measures"], available=frame.columns)
    assert_brain_only(cols)
    if len(cols) != 360:
        raise RuntimeError(f"expected exactly 360 approved ROI predictors, got {len(cols)}")
    return cols


def _xy(frame: Any, cols: list[str]):
    import numpy as np

    if "group" not in frame.columns:
        raise RuntimeError("frame is missing the 'group' diagnosis column")
    present = frame["group"].notna().to_numpy()
    if not present.all():
        raise RuntimeError("group has missing values; Exercise 4 expects diagnosis for every row")
    groups_raw = frame.loc[present, "group"].to_numpy(dtype="float64")
    unexpected = set(np.unique(groups_raw)) - {float(POSITIVE_CODE), float(NEGATIVE_CODE)}
    if unexpected:
        raise RuntimeError(f"group has unexpected codes: {sorted(unexpected)}")
    y = (groups_raw == float(POSITIVE_CODE)).astype(int)
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    subjects = frame.loc[present, "subject"].to_numpy()
    if np.isnan(X).any():
        raise RuntimeError("brain features contain missing values")
    return X, y, subjects


def _pipeline(C: float):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=MAX_ITER))


def _split(X: Any, y: Any, subjects: Any):
    from sklearn.model_selection import train_test_split

    return train_test_split(
        X, y, subjects, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )


def _select_c(X_train: Any, y_train: Any) -> dict[str, Any]:
    """5-fold stratified CV (WP18 sec 2) on the training partition only.
    Returns the full per-C curve and the selected C (argmax mean CV ROC AUC),
    via ``GridSearchCV(refit=True)`` -- which also refits the winning pipeline
    on the complete outer-training partition as part of selection."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    cv = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_RANDOM_STATE)
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=MAX_ITER))
    grid = GridSearchCV(
        pipe,
        param_grid={"logisticregression__C": C_GRID},
        scoring=CV_SCORING,
        cv=cv,
        refit=True,
    )
    grid.fit(X_train, y_train)

    curve = [
        {"C": c, "mean_cv_auc": round(float(m), 6), "std_cv_auc": round(float(s), 6)}
        for c, m, s in zip(C_GRID, grid.cv_results_["mean_test_score"], grid.cv_results_["std_test_score"])
    ]
    selected_c = float(grid.best_params_["logisticregression__C"])
    return {
        "grid": list(C_GRID),
        "curve": curve,
        "selected_C": selected_c,
        "selected_mean_cv_auc": round(float(grid.best_score_), 6),
        "fitted_pipeline": grid.best_estimator_,
    }


def select_canonical_c(frame: Any) -> float:
    """The one honest C selection for Exercise 4's canonical split -- reused
    by the threshold and imbalance export scripts so every artifact shares
    the exact same, honestly selected, fixed C (WP18 sec 2.4/4.4)."""
    cols = _feature_columns(frame)
    X, y, subjects = _xy(frame, cols)
    X_train, _X_test, y_train, _y_test, _subj_train, _subj_test = _split(X, y, subjects)
    return _select_c(X_train, y_train)["selected_C"]


def _fit_eval(X_train, y_train, X_test, y_test, C: float) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score

    model = _pipeline(C)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, list(model.classes_).index(1)]

    # rows = actual, columns = predicted; labels=[0, 1] so index 0 = control
    # (negative), index 1 = autism (positive) on BOTH axes.
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    accuracy = float(accuracy_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_proba))
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")

    return {
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "accuracy": round(accuracy, 6),
        "auc": round(auc, 6),
        "sensitivity": round(float(sensitivity), 6),
        "specificity": round(float(specificity), 6),
        "n_test": int(len(y_test)),
        "test_positive_count": int(np.sum(y_test == 1)),
        "test_negative_count": int(np.sum(y_test == 0)),
    }


def run_audit() -> dict[str, Any]:
    import numpy as np

    t0 = time.time()
    frame = load_modeling_frame()
    cols = _feature_columns(frame)
    X, y, subjects = _xy(frame, cols)

    X_train, X_test, y_train, y_test, subj_train, subj_test = _split(X, y, subjects)

    overlap = set(subj_train.tolist()) & set(subj_test.tolist())
    if overlap:
        raise RuntimeError(f"train/test participant overlap: {sorted(overlap)[:5]}")

    selection = _select_c(X_train, y_train)
    c_star = selection["selected_C"]

    first = _fit_eval(X_train, y_train, X_test, y_test, c_star)
    second = _fit_eval(X_train, y_train, X_test, y_test, c_star)
    if first != second:
        raise RuntimeError("refitting the identical pipeline on the identical split was not reproducible")

    results: dict[str, Any] = {
        "generated_by": "scripts/classification_model_audit.py --run",
        "target": "group (recoded: autism=1, control=0)",
        "positive_class": CLS["positive_class"]["label"],
        "negative_class": CLS["negative_class"]["label"],
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
        },
        "feature_recipe": {
            "bundle": CLS["canonical_recipe"]["bundle"],
            "measures": CLS["canonical_recipe"]["measures"],
            "feature_count": len(cols),
        },
        "protocol": {
            "holdout_split": {"test_size": TEST_SIZE, "random_state": RANDOM_STATE, "stratify": "y"},
            "model": f"Pipeline(StandardScaler(), LogisticRegression(C={c_star!r}, max_iter={MAX_ITER}))",
            "note": (
                "C is selected honestly: GridSearchCV over a predetermined logarithmic grid "
                "(np.logspace(-4, 4, 9)), scored by ROC AUC, with StratifiedKFold(n_splits=5, "
                "shuffle=True, random_state=42) on the outer-TRAINING partition only. The "
                "outer test set is evaluated exactly once, after C is already locked, and is "
                "never used to select C, the feature space, scaling, or the scoring rule."
            ),
        },
        "cv_selection": {
            "grid": selection["grid"],
            "folds": f"StratifiedKFold(n_splits={CV_SPLITS}, shuffle=True, random_state={CV_RANDOM_STATE})",
            "scoring": CV_SCORING,
            "curve": selection["curve"],
            "selected_C": c_star,
            "selected_mean_cv_auc": selection["selected_mean_cv_auc"],
        },
        "cohort": {
            "n_total": int(len(y)),
            "n_positive_total": int(np.sum(y == 1)),
            "n_negative_total": int(np.sum(y == 0)),
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
        },
        "reproducibility_check": {"refit_metrics_identical": True},
        "train_test_disjoint": True,
        "locked_test_eval": first,
        "runtime_seconds": round(time.time() - t0, 2),
    }
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
    if results.get("feature_recipe", {}).get("feature_count") != 360:
        problems.append("feature_recipe.feature_count must be exactly 360")
    if results.get("feature_recipe", {}).get("bundle") != "all-eligible":
        problems.append("feature_recipe.bundle must be 'all-eligible'")
    proto = results.get("protocol", {}).get("holdout_split", {})
    if proto.get("test_size") != TEST_SIZE or proto.get("random_state") != RANDOM_STATE:
        problems.append("protocol.holdout_split does not match the manifest's classification.holdout_split")

    cvsel = results.get("cv_selection", {})
    if cvsel.get("grid") != C_GRID:
        problems.append("cv_selection.grid does not match the fixed C_GRID")
    if cvsel.get("scoring") != CV_SCORING:
        problems.append(f"cv_selection.scoring must be {CV_SCORING!r}")
    selected_c = cvsel.get("selected_C")
    if selected_c not in C_GRID:
        problems.append("cv_selection.selected_C is not in the evaluated grid")
    mean_auc = cvsel.get("selected_mean_cv_auc")
    if not isinstance(mean_auc, (int, float)) or not (0.0 <= mean_auc <= 1.0):
        problems.append("cv_selection.selected_mean_cv_auc must be a number in [0, 1]")
    curve = cvsel.get("curve", [])
    if len(curve) != len(C_GRID):
        problems.append("cv_selection.curve must have one row per grid point")
    else:
        best_row = max(curve, key=lambda row: row["mean_cv_auc"])
        if best_row["C"] != selected_c:
            problems.append("cv_selection.selected_C is not the grid's argmax mean_cv_auc")
    if f"C={selected_c!r}" not in results.get("protocol", {}).get("model", ""):
        problems.append("protocol.model does not cite cv_selection.selected_C")

    if not results.get("train_test_disjoint"):
        problems.append("train_test_disjoint must be true")
    if not results.get("reproducibility_check", {}).get("refit_metrics_identical"):
        problems.append("reproducibility_check.refit_metrics_identical must be true")
    cm = results.get("locked_test_eval", {}).get("confusion_matrix", {})
    required_cells = {"tn", "fp", "fn", "tp"}
    if set(cm) != required_cells:
        problems.append(f"confusion_matrix must have exactly {required_cells}")
    else:
        n_test = results["locked_test_eval"]["n_test"]
        if cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] != n_test:
            problems.append("confusion_matrix cells do not sum to n_test")
        acc = results["locked_test_eval"]["accuracy"]
        recomputed_acc = (cm["tn"] + cm["tp"]) / n_test
        if abs(acc - recomputed_acc) > 1e-6:
            problems.append(f"accuracy {acc} does not match confusion matrix ({recomputed_acc})")
    auc = results.get("locked_test_eval", {}).get("auc")
    if not isinstance(auc, (int, float)) or not (0.0 <= auc <= 1.0):
        problems.append("locked_test_eval.auc must be a number in [0, 1]")
    return problems


def _print_summary(results: dict[str, Any]) -> None:
    ev = results["locked_test_eval"]
    cm = ev["confusion_matrix"]
    cvsel = results["cv_selection"]
    print()
    print(f"=== classification audit (runtime {results.get('runtime_seconds', '?')}s) ===")
    print(f"n_train={results['cohort']['n_train']}  n_test={results['cohort']['n_test']}  "
          f"positives(autism)={results['cohort']['n_positive_total']}  negatives(control)={results['cohort']['n_negative_total']}")
    print(f"selected C={cvsel['selected_C']:g}  (mean 5-fold training-only CV AUC={cvsel['selected_mean_cv_auc']:.3f})")
    print(f"confusion matrix: TN={cm['tn']} FP={cm['fp']} FN={cm['fn']} TP={cm['tp']}")
    print(f"accuracy={ev['accuracy']:.3f}  AUC={ev['auc']:.3f}  "
          f"sensitivity={ev['sensitivity']:.3f}  specificity={ev['specificity']:.3f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
