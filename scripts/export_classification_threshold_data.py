#!/usr/bin/env python3
"""Deterministically export the Exercise 4 decision-threshold interactive
(WP17 sec 4).

The browser activity ``classification-threshold`` lets a student move a
probability threshold and see the confusion matrix, accuracy, sensitivity,
specificity, and a ROC curve with the chosen threshold's point marked -- all
recomputed live from a FIXED set of honest test-set predicted probabilities.
The model is never refit when the threshold changes; only the confusion
matrix depends on the threshold, never the AUC.

Exactly Exercise 4's own locked split/recipe/model
(``book/config/abide_modeling.json`` ``classification``):
``Pipeline(StandardScaler(), LogisticRegression(C=<selected>, max_iter=5000))``
on the canonical ``all-eligible x CT`` recipe (p=360),
``train_test_split(test_size=0.25, random_state=42, stratify=y)``. C is the
same fixed value used throughout the notebook (WP19;
``classification_model_audit.select_canonical_c`` now returns the fixed
``C_EXAMPLE``) --
this script never tunes anything itself, it only reuses that fixed value so
the threshold activity's probabilities come from the same worked-example
model.

Output: ``book/_static/widgets/data/abide_classification_threshold.json``.
Ships only the 251 test-set true labels (0/1) and predicted probabilities
(P(autism)) -- no brain features, no participant identifiers.

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
from classification_model_audit import (  # noqa: E402
    _feature_columns,
    _fit_eval,
    _pipeline,
    _split,
    _xy,
    select_canonical_c,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_classification_threshold.json"
SCHEMA_VERSION = 1
PROB_DECIMALS = 6


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or MANIFEST
    cls = manifest["classification"]
    cols = _feature_columns(frame)
    X, y, subjects = _xy(frame, cols)
    X_train, X_test, y_train, y_test, subj_train, subj_test = _split(X, y, subjects)

    c_star = select_canonical_c(frame)
    model = _pipeline(c_star)
    model.fit(X_train, y_train)
    positive_index = list(model.classes_).index(1)
    proba = model.predict_proba(X_test)[:, positive_index]

    audit_eval = _fit_eval(X_train, y_train, X_test, y_test, c_star)

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "classification-threshold",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
        },
        "positiveClass": cls["positive_class"]["label"],
        "negativeClass": cls["negative_class"]["label"],
        "featureRecipe": {
            "bundle": cls["canonical_recipe"]["bundle"],
            "measures": cls["canonical_recipe"]["measures"],
            "featureCount": len(cols),
        },
        "split": {
            "testSize": cls["holdout_split"]["test_size"],
            "randomState": cls["holdout_split"]["random_state"],
            "nTrain": int(len(y_train)),
            "nTest": int(len(y_test)),
        },
        "model": f"Pipeline(StandardScaler(), LogisticRegression(C={c_star!r}, max_iter=5000))",
        "modelC": c_star,
        "aucFromAudit": audit_eval["auc"],
        "accuracyAtHalfFromAudit": audit_eval["accuracy"],
        "labels": [int(v) for v in y_test.tolist()],
        "probabilities": [round(float(v), PROB_DECIMALS) for v in proba.tolist()],
    }


def _confusion_at(labels: list[int], probs: list[float], threshold: float) -> tuple[int, int, int, int]:
    tn = fp = fn = tp = 0
    for label, p in zip(labels, probs):
        pred = 1 if p >= threshold else 0
        if label == 1 and pred == 1:
            tp += 1
        elif label == 1 and pred == 0:
            fn += 1
        elif label == 0 and pred == 1:
            fp += 1
        else:
            tn += 1
    return tn, fp, fn, tp


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "classification-threshold":
        problems.append("activity must be 'classification-threshold'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    labels = artifact.get("labels")
    probs = artifact.get("probabilities")
    split = artifact.get("split", {})
    n_test = split.get("nTest")
    if not isinstance(labels, list) or not isinstance(probs, list):
        return problems + ["labels/probabilities must be arrays"]
    if len(labels) != n_test or len(probs) != n_test:
        problems.append(f"labels/probabilities must have length nTest={n_test}")
        return problems
    if any(v not in (0, 1) for v in labels):
        problems.append("labels must be only 0 or 1")
    if any(not (0.0 <= p <= 1.0) for p in probs):
        problems.append("probabilities must be within [0, 1]")
    if len(set(labels)) < 2:
        problems.append("labels must contain both classes (AUC would be undefined)")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in artifact.keys():
        if key.lower() in identifier_token:
            problems.append(f"artifact has an identifier-shaped key: {key!r}")

    # Recompute accuracy at threshold 0.5 from the raw arrays and compare to
    # the audit's own locked-eval accuracy (same model, same split).
    if not problems:
        tn, fp, fn, tp = _confusion_at(labels, probs, 0.5)
        recomputed_acc = (tn + tp) / n_test
        stored_acc = artifact.get("accuracyAtHalfFromAudit")
        if not isinstance(stored_acc, (int, float)) or abs(recomputed_acc - stored_acc) > 1e-6:
            problems.append(
                f"accuracyAtHalfFromAudit {stored_acc} does not match confusion-matrix-at-0.5 "
                f"accuracy recomputed from labels/probabilities ({recomputed_acc})"
            )
        auc = artifact.get("aucFromAudit")
        if not isinstance(auc, (int, float)) or not (0.0 <= auc <= 1.0):
            problems.append("aucFromAudit must be a number in [0, 1]")

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def _summary(artifact: dict[str, Any]) -> str:
    s = artifact["split"]
    return (
        f"activity   : {artifact['activity']}\n"
        f"n_train    : {s['nTrain']}   n_test : {s['nTest']}\n"
        f"AUC (audit): {artifact['aucFromAudit']:.3f}   accuracy@0.5 (audit): {artifact['accuracyAtHalfFromAudit']:.3f}"
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
