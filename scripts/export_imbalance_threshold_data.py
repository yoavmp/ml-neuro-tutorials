#!/usr/bin/env python3
"""Export the Exercise 10 "High Accuracy Can Still Miss the Minority Class"
interactive (WP38 sec 9).

Reuses the exact same fixed 90:10 (control:autism) cohort mechanism as
Exercise 3's class-imbalance activity (``book/config/abide_modeling.json``
``classification.imbalance_activity``, ratio key ``"90:10"``, the same
``cohort_resample_seed_base`` and one of its five predeclared
``split_seeds``) and Exercise 3's own fixed logistic-regression recipe
(``classification_model_audit._pipeline``, ``C=classification_model_audit.C_EXAMPLE``)
-- Exercise 10 introduces no new sampling rule or model family.

Two models are fit on the *same* training partition of the *same* cohort:
ordinary ``LogisticRegression(C=1.0)`` and
``LogisticRegression(C=1.0, class_weight="balanced")``. Both are then scored
once on the *same* locked test partition; only their predicted probabilities
for the positive (autism) class are shipped, alongside the true test labels.
The browser activity recomputes confusion matrix / accuracy / balanced
accuracy / precision / recall / F1 at any chosen threshold from those fixed
arrays -- it never refits a model or tunes a threshold against this data
(WP38 sec 9.1: "not a valid procedure for choosing and reporting a final
threshold"). ROC-AUC and PR-AUC are threshold-independent and are computed
once here.

Output: ``book/_static/widgets/data/abide_imbalance_threshold.json``.
Ships only the fixed cohort counts, the two probability arrays, and the true
labels (100 values each) -- no brain features, no participant identifiers.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute,
  validate, and write.
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
from classification_model_audit import C_EXAMPLE, MAX_ITER, _feature_columns, _xy  # noqa: E402

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_imbalance_threshold.json"
SCHEMA_VERSION = 1
RATIO_KEY = "90:10"


def _resample_cohort(X: Any, y: Any, ratio: dict[str, Any], cohort_size: int, seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    majority_idx = np.flatnonzero(y == 0)  # control
    minority_idx = np.flatnonzero(y == 1)  # autism

    n_majority = round(cohort_size * ratio["majorityPct"])
    n_minority = cohort_size - n_majority
    chosen_majority = rng.choice(majority_idx, size=n_majority, replace=False)
    chosen_minority = rng.choice(minority_idx, size=n_minority, replace=False)
    chosen = np.concatenate([chosen_majority, chosen_minority])
    return X[chosen], y[chosen], n_majority, n_minority


def _pipeline(C: float, class_weight: str | None):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=MAX_ITER, class_weight=class_weight))


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    cls = manifest["classification"]
    imb = cls["imbalance_activity"]
    cols = _feature_columns(frame)
    X, y, _subjects = _xy(frame, cols)

    ratio = next(r for r in imb["ratios"] if r["key"] == RATIO_KEY)
    ratio_index = imb["ratios"].index(ratio)
    cohort_seed = imb["cohort_resample_seed_base"] + ratio_index
    split_seed = imb["split_seeds"][0]

    X_cohort, y_cohort, n_majority, n_minority = _resample_cohort(X, y, ratio, imb["cohort_size"], cohort_seed)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_cohort, y_cohort, test_size=0.25, random_state=split_seed, stratify=y_cohort
    )

    models: dict[str, Any] = {}
    for key, class_weight in (("ordinary", None), ("classWeighted", "balanced")):
        pipe = _pipeline(C_EXAMPLE, class_weight)
        pipe.fit(X_tr, y_tr)
        positive_index = list(pipe.classes_).index(1)
        proba = pipe.predict_proba(X_te)[:, positive_index]
        models[key] = {
            "predictedProbaPositive": [round(float(p), 6) for p in proba],
            "rocAuc": round(float(roc_auc_score(y_te, proba)), 6),
            "prAuc": round(float(average_precision_score(y_te, proba)), 6),
        }

    n_test_pos = int(np.sum(y_te == 1))
    n_test_neg = int(np.sum(y_te == 0))

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "imbalance-threshold",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
        },
        "ratioKey": RATIO_KEY,
        "majorityClass": imb["majority_class"],
        "minorityClass": imb["minority_class"],
        "cohort": {"n": imb["cohort_size"], "nMajority": n_majority, "nMinority": n_minority},
        "splitSeed": split_seed,
        "testLabels": [int(v) for v in y_te],
        "nTestMajority": n_test_neg,
        "nTestMinority": n_test_pos,
        "positivePrevalence": round(n_test_pos / (n_test_pos + n_test_neg), 6),
        "majorityBaselineAccuracy": round(max(n_test_pos, n_test_neg) / (n_test_pos + n_test_neg), 6),
        "modelC": C_EXAMPLE,
        "models": {
            "ordinary": {"model": f"Pipeline(StandardScaler(), LogisticRegression(C={C_EXAMPLE!r}))", **models["ordinary"]},
            "classWeighted": {
                "model": f"Pipeline(StandardScaler(), LogisticRegression(C={C_EXAMPLE!r}, class_weight='balanced'))",
                **models["classWeighted"],
            },
        },
    }


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "imbalance-threshold":
        problems.append("activity must be 'imbalance-threshold'")
    if artifact.get("ratioKey") != RATIO_KEY:
        problems.append(f"ratioKey must be {RATIO_KEY!r}")

    cohort = artifact.get("cohort", {})
    if cohort.get("nMajority", 0) + cohort.get("nMinority", 0) != cohort.get("n"):
        problems.append("cohort majority+minority does not sum to n")

    labels = artifact.get("testLabels")
    if not isinstance(labels, list) or not labels:
        return problems + ["testLabels must be a non-empty array"]
    n_test = len(labels)
    n_pos = sum(1 for v in labels if v == 1)
    n_neg = sum(1 for v in labels if v == 0)
    if n_pos + n_neg != n_test:
        problems.append("testLabels contains values other than 0/1")
    if artifact.get("nTestMinority") != n_pos or artifact.get("nTestMajority") != n_neg:
        problems.append("nTestMinority/nTestMajority disagree with testLabels")
    expected_baseline = round(max(n_pos, n_neg) / n_test, 6) if n_test else None
    if expected_baseline is not None and abs(artifact.get("majorityBaselineAccuracy", -1) - expected_baseline) > 1e-6:
        problems.append("majorityBaselineAccuracy disagrees with the recomputed value")
    expected_prevalence = round(n_pos / n_test, 6) if n_test else None
    if expected_prevalence is not None and abs(artifact.get("positivePrevalence", -1) - expected_prevalence) > 1e-6:
        problems.append("positivePrevalence disagrees with the recomputed value")

    if artifact.get("modelC") != manifest["classification"]["worked_example_C"]:
        problems.append("modelC does not match the manifest's classification.worked_example_C")

    models = artifact.get("models", {})
    for key in ("ordinary", "classWeighted"):
        m = models.get(key, {})
        proba = m.get("predictedProbaPositive")
        if not isinstance(proba, list) or len(proba) != n_test:
            problems.append(f"models.{key}.predictedProbaPositive must have exactly {n_test} entries")
            continue
        if not all(0.0 <= p <= 1.0 for p in proba):
            problems.append(f"models.{key}.predictedProbaPositive must be within [0, 1]")
        for metric in ("rocAuc", "prAuc"):
            v = m.get(metric)
            if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
                problems.append(f"models.{key}.{metric} must be a number in [0, 1]")

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
    return "\n".join(
        [
            f"activity        : {artifact['activity']}",
            f"ratioKey        : {artifact['ratioKey']}",
            f"cohort          : {artifact['cohort']}",
            f"nTest           : {len(artifact['testLabels'])}",
            f"majorityBaseline: {artifact['majorityBaselineAccuracy']}",
            f"ordinary rocAuc : {artifact['models']['ordinary']['rocAuc']}  prAuc: {artifact['models']['ordinary']['prAuc']}",
            f"weighted rocAuc : {artifact['models']['classWeighted']['rocAuc']}  prAuc: {artifact['models']['classWeighted']['prAuc']}",
        ]
    )


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
