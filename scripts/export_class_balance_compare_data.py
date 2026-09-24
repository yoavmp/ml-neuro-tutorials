#!/usr/bin/env python3
"""Export the Exercise 10 class-balance comparison interactive (WP38R sec 5).

WP38R replaced the earlier "High Accuracy Can Still Miss the Minority Class"
threshold-comparison activity (``imbalance-threshold``, WP38) because a
classification-threshold slider is the wrong lesson at this course stage. The
new activity, ``class-balance-compare``, drops threshold selection entirely
and instead compares the SAME two logistic-regression pipelines -- ordinary
and ``class_weight="balanced"`` -- across FIVE progressively more imbalanced
control:autism samples, at a FIXED decision threshold of 0.5, so the lesson
is about how prevalence itself changes accuracy/baseline/recall rather than
about threshold tuning.

Reuses the exact same fixed-cohort mechanism as Exercise 3's class-imbalance
activity (``book/config/abide_modeling.json``
``classification.imbalance_activity``) and Exercise 3's own fixed
logistic-regression recipe (``classification_model_audit.C_EXAMPLE``,
``classification_model_audit.MAX_ITER``) -- no new sampling rule, no new
model family, no parameter search:

* only the FIRST FIVE ratios in the manifest's own ``ratios`` list are used,
  in order (``50:50``, ``60:40``, ``70:30``, ``80:20``, ``90:10``) --
  ``95:5`` is deliberately excluded (WP38R sec 5: exactly five balance
  levels);
* each ratio's fixed cohort is drawn with
  ``cohort_seed = cohort_resample_seed_base + ratio_index`` where
  ``ratio_index`` is the ratio's own position (0-4) in the manifest's
  ``ratios`` list -- identical to Exercise 3's own cohort draws for the
  ratios they share;
* exactly ONE split per ratio, ``split_seed = split_seeds[0]`` (seed 0) --
  the same precedent the old ``export_imbalance_threshold_data.py`` set;
  there is no seed selector control anywhere in this activity;
* both models are fit on the SAME training partition of the SAME cohort and
  scored on the SAME locked test partition using ``.predict()`` (decision
  threshold fixed at 0.5) -- there is no threshold sweep, no predicted
  probability array shipped, and no refitting in the browser.

Output: ``book/_static/widgets/data/abide_class_balance_compare.json``.
Ships only aggregated per-(ratio, model) counts and metrics -- no brain
features, no participant identifiers, no raw predicted probabilities.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute
  every (ratio, model) combination, validate, and write.
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

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_class_balance_compare.json"
SCHEMA_VERSION = 1

# WP38R sec 5: exactly the first five ratios from the manifest's own list, in
# order -- 95:5 is deliberately excluded (five balance levels, not six).
N_RATIOS = 5
EXPECTED_RATIO_KEYS = ["50:50", "60:40", "70:30", "80:20", "90:10"]


def _resample_cohort(X: Any, y: Any, ratio: dict[str, Any], cohort_size: int, seed: int):
    """Draw a fixed cohort (control majority, autism minority) without
    replacement for one ratio, using the given deterministic seed -- byte-
    for-byte identical mechanism to
    ``export_classification_imbalance_data.py`` / the old
    ``export_imbalance_threshold_data.py`` (same predeclared rule, not a new
    one)."""
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


def _pipeline(C: float, class_weight: str | None):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=MAX_ITER, class_weight=class_weight))


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _eval_model(X_train, y_train, X_test, y_test, C: float, class_weight: str | None) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

    pipe = _pipeline(C, class_weight)
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    n_test = tn + fp + fn + tp
    n_test_pos = int(np.sum(y_test == 1))
    n_test_neg = int(np.sum(y_test == 0))

    accuracy = (tn + tp) / n_test
    majority_baseline_accuracy = max(n_test_pos, n_test_neg) / n_test

    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    specificity = tn / (tn + fp) if (tn + fp) > 0 else None
    balanced_accuracy = (recall + specificity) / 2 if (recall is not None and specificity is not None) else None
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    if precision is None or recall is None or (precision + recall) == 0:
        f1 = None
    else:
        f1 = (2 * precision * recall) / (precision + recall)

    positive_index = list(pipe.classes_).index(1)
    proba = pipe.predict_proba(X_test)[:, positive_index]
    roc_auc = float(roc_auc_score(y_test, proba))
    pr_auc = float(average_precision_score(y_test, proba))
    pr_auc_baseline = n_test_pos / n_test

    return {
        "confusionMatrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "accuracy": round(accuracy, 6),
        "majorityBaselineAccuracy": round(majority_baseline_accuracy, 6),
        "balancedAccuracy": _round_or_none(balanced_accuracy),
        "recall": _round_or_none(recall),
        "precision": _round_or_none(precision),
        "f1": _round_or_none(f1),
        "rocAuc": round(roc_auc, 6),
        "prAuc": round(pr_auc, 6),
        "prAucBaseline": round(pr_auc_baseline, 6),
    }


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    cls = manifest["classification"]
    imb = cls["imbalance_activity"]
    cols = _feature_columns(frame)
    X, y, _subjects = _xy(frame, cols)

    ratios = imb["ratios"][:N_RATIOS]
    if [r["key"] for r in ratios] != EXPECTED_RATIO_KEYS:
        raise RuntimeError(f"expected the manifest's first {N_RATIOS} ratio keys to be {EXPECTED_RATIO_KEYS}, got {[r['key'] for r in ratios]}")

    seed_base = imb["cohort_resample_seed_base"]
    split_seed = imb["split_seeds"][0]
    cohort_size = imb["cohort_size"]

    entries: list[dict[str, Any]] = []
    for ratio_index, ratio in enumerate(ratios):
        cohort_seed = seed_base + ratio_index
        X_cohort, y_cohort, n_majority, n_minority = _resample_cohort(X, y, ratio, cohort_size, cohort_seed)

        X_tr, X_te, y_tr, y_te = train_test_split(
            X_cohort, y_cohort, test_size=0.25, random_state=split_seed, stratify=y_cohort
        )

        import numpy as np

        n_train_majority = int(np.sum(y_tr == 0))
        n_train_minority = int(np.sum(y_tr == 1))
        n_test_majority = int(np.sum(y_te == 0))
        n_test_minority = int(np.sum(y_te == 1))

        models = {
            "ordinary": _eval_model(X_tr, y_tr, X_te, y_te, C_EXAMPLE, None),
            "classWeighted": _eval_model(X_tr, y_tr, X_te, y_te, C_EXAMPLE, "balanced"),
        }

        entries.append(
            {
                "ratioKey": ratio["key"],
                "cohort": {"n": cohort_size, "nMajority": n_majority, "nMinority": n_minority},
                "nTrainMajority": n_train_majority,
                "nTrainMinority": n_train_minority,
                "nTestMajority": n_test_majority,
                "nTestMinority": n_test_minority,
                "models": models,
            }
        )

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "class-balance-compare",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
        },
        "majorityClass": imb["majority_class"],
        "minorityClass": imb["minority_class"],
        "cohortSize": cohort_size,
        "splitSeed": split_seed,
        "modelC": C_EXAMPLE,
        "ratios": ratios,
        "modelOrdinary": f"Pipeline(StandardScaler(), LogisticRegression(C={C_EXAMPLE!r}, max_iter={MAX_ITER}))",
        "modelClassWeighted": (
            f"Pipeline(StandardScaler(), LogisticRegression(C={C_EXAMPLE!r}, max_iter={MAX_ITER}, class_weight='balanced'))"
        ),
        "entries": entries,
    }


def _close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "class-balance-compare":
        problems.append("activity must be 'class-balance-compare'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    ratios = artifact.get("ratios")
    ratio_keys = [r.get("key") for r in ratios] if isinstance(ratios, list) else None
    if ratio_keys != EXPECTED_RATIO_KEYS:
        problems.append(f"ratios must be exactly {EXPECTED_RATIO_KEYS} in order, got {ratio_keys!r}")
    if ratio_keys is not None and "95:5" in ratio_keys:
        problems.append("ratios must not include '95:5' (exactly five balance levels, 50:50 through 90:10)")

    if artifact.get("modelC") != C_EXAMPLE:
        problems.append(f"modelC must equal classification_model_audit.C_EXAMPLE ({C_EXAMPLE!r})")
    if artifact.get("modelC") != manifest["classification"]["worked_example_C"]:
        problems.append("modelC does not match the manifest's classification.worked_example_C")

    entries = artifact.get("entries")
    if not isinstance(entries, list) or len(entries) != N_RATIOS:
        return problems + [f"entries must be an array of exactly {N_RATIOS} items"]

    identifier_token = ("id", "sub", "subject", "site", "participant")
    seen_ratio_keys: set[str] = set()

    for e in entries:
        rk = e.get("ratioKey")
        if rk in seen_ratio_keys:
            problems.append(f"duplicate entry for ratioKey {rk!r}")
        seen_ratio_keys.add(rk)
        if rk not in EXPECTED_RATIO_KEYS:
            problems.append(f"unexpected ratioKey {rk!r}")

        cohort = e.get("cohort", {})
        if cohort.get("nMajority", -1) + cohort.get("nMinority", -1) != cohort.get("n", -3):
            problems.append(f"entry {rk}: cohort majority+minority does not sum to n")
        if cohort.get("n") != artifact.get("cohortSize"):
            problems.append(f"entry {rk}: cohort.n does not match top-level cohortSize")

        n_train_major = e.get("nTrainMajority")
        n_train_minor = e.get("nTrainMinority")
        n_test_major = e.get("nTestMajority")
        n_test_minor = e.get("nTestMinority")
        if None in (n_train_major, n_train_minor, n_test_major, n_test_minor):
            problems.append(f"entry {rk}: missing train/test count field(s)")
            continue
        if n_train_major + n_test_major != cohort.get("nMajority"):
            problems.append(f"entry {rk}: nTrainMajority + nTestMajority does not equal cohort.nMajority")
        if n_train_minor + n_test_minor != cohort.get("nMinority"):
            problems.append(f"entry {rk}: nTrainMinority + nTestMinority does not equal cohort.nMinority")

        n_test = n_test_major + n_test_minor
        if n_test_major == 0 or n_test_minor == 0:
            problems.append(f"entry {rk}: one-class test partition must not occur in this activity")

        models = e.get("models", {})
        for key in ("ordinary", "classWeighted"):
            m = models.get(key)
            if not isinstance(m, dict):
                problems.append(f"entry {rk}: models.{key} is missing")
                continue

            cm = m.get("confusionMatrix", {})
            if set(cm) != {"tn", "fp", "fn", "tp"}:
                problems.append(f"entry {rk}/{key}: confusionMatrix must have exactly tn/fp/fn/tp")
                continue
            tn, fp, fn, tp = cm["tn"], cm["fp"], cm["fn"], cm["tp"]
            if any(v < 0 for v in (tn, fp, fn, tp)):
                problems.append(f"entry {rk}/{key}: confusion matrix cells must be non-negative")
            cm_total = tn + fp + fn + tp
            if cm_total != n_test:
                problems.append(f"entry {rk}/{key}: confusion matrix total ({cm_total}) disagrees with nTestMajority+nTestMinority ({n_test})")

            expected_accuracy = (tn + tp) / cm_total if cm_total else None
            if expected_accuracy is not None and not _close(m.get("accuracy", -1), expected_accuracy):
                problems.append(f"entry {rk}/{key}: accuracy does not match its own confusion matrix")
            if not (0.0 <= m.get("accuracy", -1) <= 1.0):
                problems.append(f"entry {rk}/{key}: accuracy must be in [0, 1]")

            expected_baseline = max(n_test_major, n_test_minor) / n_test if n_test else None
            if expected_baseline is not None and not _close(m.get("majorityBaselineAccuracy", -1), expected_baseline):
                problems.append(f"entry {rk}/{key}: majorityBaselineAccuracy disagrees with the recomputed value")

            expected_recall = tp / (tp + fn) if (tp + fn) > 0 else None
            stored_recall = m.get("recall")
            if expected_recall is None:
                problems.append(f"entry {rk}/{key}: recall should be defined (tp+fn>0 expected in this activity)")
            elif stored_recall is None or not _close(stored_recall, expected_recall):
                problems.append(f"entry {rk}/{key}: recall disagrees with the recomputed value")

            expected_specificity = tn / (tn + fp) if (tn + fp) > 0 else None
            expected_balanced = (
                (expected_recall + expected_specificity) / 2
                if expected_recall is not None and expected_specificity is not None
                else None
            )
            stored_balanced = m.get("balancedAccuracy")
            if expected_balanced is None:
                if stored_balanced is not None:
                    problems.append(f"entry {rk}/{key}: balancedAccuracy should be null (undefined)")
            elif stored_balanced is None or not _close(stored_balanced, expected_balanced):
                problems.append(f"entry {rk}/{key}: balancedAccuracy disagrees with the recomputed value")

            expected_precision = tp / (tp + fp) if (tp + fp) > 0 else None
            stored_precision = m.get("precision")
            if expected_precision is None:
                if stored_precision is not None:
                    problems.append(f"entry {rk}/{key}: precision should be null when tp+fp == 0")
            elif stored_precision is None or not _close(stored_precision, expected_precision):
                problems.append(f"entry {rk}/{key}: precision disagrees with the recomputed value")

            if expected_precision is None or expected_recall is None or (expected_precision + expected_recall) == 0:
                expected_f1 = None
            else:
                expected_f1 = (2 * expected_precision * expected_recall) / (expected_precision + expected_recall)
            stored_f1 = m.get("f1")
            if expected_f1 is None:
                if stored_f1 is not None:
                    problems.append(f"entry {rk}/{key}: f1 should be null (undefined)")
            elif stored_f1 is None or not _close(stored_f1, expected_f1):
                problems.append(f"entry {rk}/{key}: f1 disagrees with the recomputed value")

            for metric in ("rocAuc", "prAuc"):
                v = m.get(metric)
                if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
                    problems.append(f"entry {rk}/{key}: {metric} must be a number in [0, 1]")

            expected_pr_baseline = n_test_minor / n_test if n_test else None
            stored_pr_baseline = m.get("prAucBaseline")
            if expected_pr_baseline is not None and (
                stored_pr_baseline is None or not _close(stored_pr_baseline, expected_pr_baseline)
            ):
                problems.append(f"entry {rk}/{key}: prAucBaseline disagrees with the recomputed positive prevalence")

        ord_m = models.get("ordinary", {})
        cw_m = models.get("classWeighted", {})
        if ord_m.get("majorityBaselineAccuracy") != cw_m.get("majorityBaselineAccuracy"):
            problems.append(f"entry {rk}: majorityBaselineAccuracy must be identical for both models (same test partition)")
        if ord_m.get("prAucBaseline") != cw_m.get("prAucBaseline"):
            problems.append(f"entry {rk}: prAucBaseline must be identical for both models (same test partition)")

    if seen_ratio_keys != set(EXPECTED_RATIO_KEYS):
        problems.append("entries do not cover exactly the five expected ratio keys")

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
        f"splitSeed   : {artifact['splitSeed']}",
        f"modelC      : {artifact['modelC']}",
        f"ratios      : {[r['key'] for r in artifact['ratios']]}",
    ]
    for e in artifact["entries"]:
        o = e["models"]["ordinary"]
        w = e["models"]["classWeighted"]
        lines.append(
            f"  {e['ratioKey']:>6}  n_test=({e['nTestMajority']:>3},{e['nTestMinority']:>3})  "
            f"ordinary: acc={o['accuracy']:.3f} base={o['majorityBaselineAccuracy']:.3f} recall={o['recall']:.3f} f1={o['f1']}  "
            f"weighted: acc={w['accuracy']:.3f} recall={w['recall']:.3f} f1={w['f1']}"
        )
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
