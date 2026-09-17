#!/usr/bin/env python3
"""Reproducible logistic-regression classification audit for Exercise 3 (WP19).

Exercise 3 predicts autism diagnosis from cortical structure -- the first
classification exercise in the course. WP19 removed the early
cross-validation / formal parameter-selection lesson: ``C`` is fixed by
course design at ``C_EXAMPLE = 1.0``, before the held-out result is
computed, not selected by ``GridSearchCV`` or any other search. This script
verifies the locked held-out performance of that fixed-C worked example.

Design (WP19):

* target: ``group`` (native to abide2.tsv), recoded autism (group==1) -> 1,
  control (group==2) -> 0. Positive class = autism.
* features: the exact Exercise 2/3 canonical recipe -- ``all-eligible x CT``,
  the same 360 bilateral cortical-thickness columns, brain-only (leakage
  guard enforced).
* split: ``train_test_split(test_size=0.25, random_state=42, stratify=y)`` --
  participant-level, one locked split, evaluated exactly once.
* model: ``Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))``,
  fit once on the outer-training partition, evaluated once on the outer test
  set. There is no hidden search that happens to return 1.0.

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

# WP19: C is fixed by course design, not selected by cross-validation.
C_EXAMPLE = 1.0


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
        raise RuntimeError("group has missing values; Exercise 3 expects diagnosis for every row")
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


def select_canonical_c(frame: Any = None) -> float:
    """The one fixed C for Exercise 3's canonical split -- reused by the
    threshold and imbalance export scripts so every artifact shares the
    exact same, course-design-fixed C (WP19). ``frame`` is accepted, but
    unused, for backward-compatible call sites -- C is a constant, not
    computed from data."""
    return C_EXAMPLE


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

    first = _fit_eval(X_train, y_train, X_test, y_test, C_EXAMPLE)
    second = _fit_eval(X_train, y_train, X_test, y_test, C_EXAMPLE)
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
            "model": f"Pipeline(StandardScaler(), LogisticRegression(C={C_EXAMPLE!r}, max_iter={MAX_ITER}))",
            "note": (
                "WP19: C = 1.0 is fixed by course design for the notebook's worked "
                "example, not selected by cross-validation or any other search. The "
                "outer test set is evaluated exactly once, with this fixed C."
            ),
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

    if f"C={C_EXAMPLE!r}" not in results.get("protocol", {}).get("model", ""):
        problems.append(f"protocol.model does not cite the fixed C_EXAMPLE={C_EXAMPLE!r}")

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
    print()
    print(f"=== classification audit (runtime {results.get('runtime_seconds', '?')}s) ===")
    print(f"n_train={results['cohort']['n_train']}  n_test={results['cohort']['n_test']}  "
          f"positives(autism)={results['cohort']['n_positive_total']}  negatives(control)={results['cohort']['n_negative_total']}")
    print(f"fixed C={C_EXAMPLE:g}  (worked example, no search)")
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
