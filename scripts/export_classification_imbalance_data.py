#!/usr/bin/env python3
"""Deterministically export the Exercise 3 class-imbalance interactive
(WP18 sec 4).

The browser activity ``classification-imbalance`` lets a student pick a class
ratio (control:autism, control always the majority class) and one of five
predetermined split seeds, then compares the logistic-regression model's
test accuracy against the majority-class baseline accuracy for that same
resampled cohort: full-cohort and train/test class counts, confusion matrix,
accuracy, majority baseline accuracy, AUC, balanced accuracy, sensitivity,
and specificity. The split is stratified internally so the displayed test
partition represents the selected ratio -- that is an implementation detail,
not the comparison the activity teaches (WP18 sec 4: no unstratified side,
no undefined-AUC case).

For each ratio (``book/config/abide_modeling.json``
``classification.imbalance_activity``), a fixed cohort of
``imbalance_activity.cohort_size`` real participants is drawn ONCE (without
replacement, deterministic per-ratio seed), so every split seed for that
ratio compares the exact same participants -- only the split's randomness
varies. Every model uses Exercise 3's own recipe and the SAME fixed C
(``classification_model_audit.C_EXAMPLE``, WP19) -- never re-tuned per
ratio or seed.

Output: ``book/_static/widgets/data/abide_classification_imbalance.json``.
Ships only aggregated counts and metrics per (ratio, seed) -- no brain
features, no participant identifiers, no raw probabilities.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute
  every (ratio, seed) combination, validate, and write.
* ``--check``    (offline): re-validate the committed artifact and confirm it
  is byte-for-byte canonical.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from abide_modeling_data import MANIFEST, REPO_ROOT, load_modeling_frame  # noqa: E402
from classification_model_audit import (  # noqa: E402
    _feature_columns,
    _pipeline,
    _xy,
    select_canonical_c,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_classification_imbalance.json"
SCHEMA_VERSION = 2


def _resample_cohort(X: Any, y: Any, ratio: dict[str, Any], cohort_size: int, seed: int):
    """Draw a fixed cohort (control majority, autism minority) without
    replacement for one ratio, using the given deterministic seed."""
    import numpy as np

    rng = np.random.default_rng(seed)
    majority_idx = np.flatnonzero(y == 0)  # control
    minority_idx = np.flatnonzero(y == 1)  # autism

    n_majority = round(cohort_size * ratio["majorityPct"])
    n_minority = cohort_size - n_majority
    if n_majority > len(majority_idx):
        raise RuntimeError(f"ratio {ratio['key']}: need {n_majority} control participants, only {len(majority_idx)} available")
    if n_minority > len(minority_idx):
        raise RuntimeError(f"ratio {ratio['key']}: need {n_minority} autism participants, only {len(minority_idx)} available")

    chosen_majority = rng.choice(majority_idx, size=n_majority, replace=False)
    chosen_minority = rng.choice(minority_idx, size=n_minority, replace=False)
    chosen = np.concatenate([chosen_majority, chosen_minority])
    return X[chosen], y[chosen], n_majority, n_minority


def _eval_split(X_train, y_train, X_test, y_test, C: float) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score

    n_test_pos = int(np.sum(y_test == 1))
    n_test_neg = int(np.sum(y_test == 0))
    if n_test_pos == 0 or n_test_neg == 0:
        raise RuntimeError("one-class test partition: cohort_size/ratio/seed produced an unusable split")

    model = _pipeline(C)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    accuracy = float(accuracy_score(y_test, y_pred))
    sensitivity = round(tp / (tp + fn), 6) if (tp + fn) > 0 else float("nan")
    specificity = round(tn / (tn + fp), 6) if (tn + fp) > 0 else float("nan")
    balanced_accuracy = round((sensitivity + specificity) / 2, 6)

    positive_index = list(model.classes_).index(1)
    proba = model.predict_proba(X_test)[:, positive_index]
    auc = round(float(roc_auc_score(y_test, proba)), 6)

    majority_baseline_accuracy = round(max(n_test_pos, n_test_neg) / len(y_test), 6)

    return {
        "nTrainMajority": int(np.sum(y_train == 0)),
        "nTrainMinority": int(np.sum(y_train == 1)),
        "nTestMajority": n_test_neg,
        "nTestMinority": n_test_pos,
        "confusionMatrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "accuracy": round(accuracy, 6),
        "majorityBaselineAccuracy": majority_baseline_accuracy,
        "auc": auc,
        "balancedAccuracy": balanced_accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
    }


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    cls = manifest["classification"]
    imb = cls["imbalance_activity"]
    cols = _feature_columns(frame)
    X, y, _subjects = _xy(frame, cols)

    c_star = select_canonical_c(frame)

    cohort_size = imb["cohort_size"]
    seed_base = imb["cohort_resample_seed_base"]
    split_seeds = imb["split_seeds"]

    entries: list[dict[str, Any]] = []
    for ratio_index, ratio in enumerate(imb["ratios"]):
        cohort_seed = seed_base + ratio_index
        X_cohort, y_cohort, n_majority, n_minority = _resample_cohort(X, y, ratio, cohort_size, cohort_seed)

        for seed in split_seeds:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_cohort, y_cohort, test_size=0.25, random_state=seed, stratify=y_cohort
            )
            metrics = _eval_split(X_tr, y_tr, X_te, y_te, c_star)

            entries.append(
                {
                    "ratioKey": ratio["key"],
                    "seed": seed,
                    "cohort": {"n": cohort_size, "nMajority": n_majority, "nMinority": n_minority},
                    **metrics,
                }
            )

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "classification-imbalance",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
        },
        "majorityClass": imb["majority_class"],
        "minorityClass": imb["minority_class"],
        "cohortSize": cohort_size,
        "ratios": imb["ratios"],
        "splitSeeds": split_seeds,
        "modelC": c_star,
        "model": f"Pipeline(StandardScaler(), LogisticRegression(C={c_star!r}, max_iter=5000)) -- C fixed by course design (WP19), fixed throughout this activity",
        "entries": entries,
    }


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "classification-imbalance":
        problems.append("activity must be 'classification-imbalance'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    imb = manifest["classification"]["imbalance_activity"]
    expected_ratio_keys = {r["key"] for r in imb["ratios"]}
    expected_seeds = set(imb["split_seeds"])
    entries = artifact.get("entries")
    if not isinstance(entries, list) or not entries:
        return problems + ["entries must be a non-empty array"]

    required_fields = {
        "nTrainMajority", "nTrainMinority", "nTestMajority", "nTestMinority",
        "confusionMatrix", "accuracy", "majorityBaselineAccuracy", "auc",
        "balancedAccuracy", "sensitivity", "specificity",
    }

    seen = set()
    for e in entries:
        key = (e.get("ratioKey"), e.get("seed"))
        if key in seen:
            problems.append(f"duplicate entry for {key}")
        seen.add(key)
        if e.get("ratioKey") not in expected_ratio_keys:
            problems.append(f"unexpected ratioKey {e.get('ratioKey')!r}")
        if e.get("seed") not in expected_seeds:
            problems.append(f"unexpected seed {e.get('seed')!r}")
        cohort = e.get("cohort", {})
        if cohort.get("n") != artifact.get("cohortSize"):
            problems.append(f"entry {key}: cohort.n does not match top-level cohortSize")
        if cohort.get("nMajority", 0) + cohort.get("nMinority", 0) != cohort.get("n"):
            problems.append(f"entry {key}: cohort majority+minority does not sum to n")

        missing = required_fields - set(e)
        if missing:
            problems.append(f"entry {key}: missing field(s) {sorted(missing)}")
            continue

        cm = e["confusionMatrix"]
        if set(cm) != {"tn", "fp", "fn", "tp"}:
            problems.append(f"entry {key}: confusionMatrix must have exactly tn/fp/fn/tp")
            continue
        n_test = cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"]
        if n_test != e["nTestMajority"] + e["nTestMinority"]:
            problems.append(f"entry {key}: confusion matrix total disagrees with nTestMajority+nTestMinority")
        recomputed_acc = (cm["tn"] + cm["tp"]) / n_test if n_test else None
        if recomputed_acc is not None and abs(recomputed_acc - e["accuracy"]) > 1e-6:
            problems.append(f"entry {key}: accuracy does not match its own confusion matrix")

        n_test_pos, n_test_neg = e["nTestMinority"], e["nTestMajority"]
        if n_test_pos == 0 or n_test_neg == 0:
            problems.append(f"entry {key}: one-class test partition must not occur in this activity")
        auc = e["auc"]
        if not isinstance(auc, (int, float)) or not (0.0 <= auc <= 1.0):
            problems.append(f"entry {key}: auc must be a number in [0, 1]")

        expected_baseline = round(max(n_test_pos, n_test_neg) / n_test, 6) if n_test else None
        if expected_baseline is not None and abs(e["majorityBaselineAccuracy"] - expected_baseline) > 1e-6:
            problems.append(f"entry {key}: majorityBaselineAccuracy disagrees with the recomputed value")

        sens, spec, bal = e["sensitivity"], e["specificity"], e["balancedAccuracy"]
        expected_bal = round((sens + spec) / 2, 6)
        if abs(bal - expected_bal) > 1e-6:
            problems.append(f"entry {key}: balancedAccuracy does not match (sensitivity+specificity)/2")

    if seen != {(r, s) for r in expected_ratio_keys for s in expected_seeds}:
        problems.append("entries do not cover every (ratio, seed) combination exactly once")

    if artifact.get("modelC") != manifest["classification"]["worked_example_C"]:
        problems.append("modelC does not match the manifest's classification.worked_example_C")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in artifact.keys():
        if key.lower() in identifier_token:
            problems.append(f"artifact has an identifier-shaped key: {key!r}")

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def _summary(artifact: dict[str, Any]) -> str:
    lines = [
        f"activity    : {artifact['activity']}",
        f"cohortSize  : {artifact['cohortSize']}",
        f"modelC      : {artifact['modelC']}",
        f"ratios      : {[r['key'] for r in artifact['ratios']]}",
        f"seeds       : {artifact['splitSeeds']}",
        f"entries     : {len(artifact['entries'])}",
    ]
    return "\n".join(lines)


def cmd_refresh() -> int:
    frame = load_modeling_frame()
    artifact = build_artifact(frame)
    problems = validate_artifact(artifact)
    if problems:
        print("ERROR: built artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = serialize(artifact)
    ARTIFACT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    print(_summary(artifact))
    return 0


def cmd_check() -> int:
    if not ARTIFACT_PATH.exists():
        print(f"ERROR: {ARTIFACT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    on_disk = ARTIFACT_PATH.read_text(encoding="utf-8")
    try:
        artifact = json.loads(on_disk)
    except json.JSONDecodeError as exc:
        print(f"ERROR: artifact is not valid JSON: {exc}", file=sys.stderr)
        return 1
    problems = validate_artifact(artifact)
    if problems:
        print("ERROR: committed artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if serialize(artifact) != on_disk:
        print("ERROR: committed artifact is not canonical (re-serialization differs).", file=sys.stderr)
        return 1
    print(f"OK: {ARTIFACT_PATH.relative_to(REPO_ROOT)} is valid and canonical.")
    print(_summary(artifact))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute + write the artifact (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed artifact offline")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
