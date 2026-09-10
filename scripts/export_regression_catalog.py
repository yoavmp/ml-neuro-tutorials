#!/usr/bin/env python3
"""Deterministically export the Exercise II feature-set comparison catalog.

The browser activity ``regression-compare`` (book/_static/widgets/) lets a
student pick a measurement subset x anatomical ROI bundle for two models and
compares their out-of-sample performance side by side. Re-implementing
scikit-learn in JavaScript would be fragile, so this script pre-computes a
finite, audited catalog of model results offline and the browser only switches
between them.

Output: ``book/_static/widgets/data/abide_regression_models.json``.

Every catalog entry uses the **same** eligible participant cohort (FIQ present
after requiring usable brain data, n=908) and the **same** deterministic 5-fold
split (``KFold(n_splits=5, shuffle=True, random_state=0)``), so the observed
target vector and the per-row fold assignment are stored once and shared. Each
model entry stores only its out-of-fold predictions and the metrics recomputed
from them. Preprocessing (``StandardScaler``) is fitted inside each fold via a
``Pipeline``. No participant identifiers, no raw brain features, no training
scores.

Recipes come from ``book/config/abide_modeling.json`` (``catalog`` block).
An entry whose feature count reaches ``0.7 * fold-training-n`` is emitted as
``disabled`` with a reason instead of being fitted.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute
  every entry, validate, and write.
* ``--check``    (offline): re-validate the committed artifact and confirm it is
  byte-for-byte canonical.
* ``--print-upstream-hash`` (network): report the current source hashes.

Determinism: ``sort_keys`` + compact separators, floats rounded to a fixed
precision, a single trailing newline, no timestamps.
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
    bundle_columns,
    feature_matrix,
    load_modeling_frame,
    sha256_hex,
    _verified_bytes,  # noqa: F401  (re-exported for --print-upstream-hash)
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_regression_models.json"
SCHEMA_VERSION = 1
PRED_DECIMALS = 4
TARGET = MANIFEST["catalog"]["target"]
IDENTIFIABILITY_FRACTION = 0.7


def _pipeline():
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LinearRegression())


def _fold_assignment(n: int, cv) -> list[int]:
    fold_of = [-1] * n
    for fold_index, (_, test_idx) in enumerate(cv.split(range(n))):
        for i in test_idx:
            fold_of[i] = fold_index
    if any(f < 0 for f in fold_of):
        raise RuntimeError("fold assignment left a row unassigned")
    return fold_of


def _metrics(observed: "Any", predicted: "Any") -> tuple[float, float]:
    import numpy as np

    obs = np.asarray(observed, dtype="float64")
    pred = np.asarray(predicted, dtype="float64")
    ss_res = float(np.sum((obs - pred) ** 2))
    ss_tot = float(np.sum((obs - obs.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    mse = float(np.mean((obs - pred) ** 2))
    return r2, mse


def build_catalog(frame: "Any", manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    import numpy as np
    from sklearn.model_selection import KFold, cross_val_predict

    manifest = manifest or MANIFEST
    cat = manifest["catalog"]
    cv_cfg = manifest["protocol"]["cross_validation"]
    if cv_cfg["kind"] != "KFold":
        raise ValueError(f"unsupported cross_validation kind {cv_cfg['kind']!r}")
    cv = KFold(n_splits=cv_cfg["n_splits"], shuffle=cv_cfg["shuffle"], random_state=cv_cfg["random_state"])

    present = frame[TARGET].notna().to_numpy()
    y = frame.loc[present, TARGET].to_numpy(dtype="float64")
    n = int(len(y))
    if not np.allclose(y, np.round(y)):
        raise ValueError(f"{TARGET} is expected to be integer-valued")
    observed = [int(round(v)) for v in y]
    fold_of = _fold_assignment(n, cv)
    fold_train_n = n - max(fold_of.count(f) for f in range(cv_cfg["n_splits"]))
    p_bound = IDENTIFIABILITY_FRACTION * fold_train_n

    subsets = [list(s) for s in cat["measurement_subsets"]]
    models: list[dict[str, Any]] = []
    for bundle in cat["bundles"]:
        for measures in subsets:
            cols = bundle_columns(bundle, measures, available=frame.columns, manifest=manifest)
            p = len(cols)
            key = f"{bundle}__{'+'.join(measures)}"
            entry: dict[str, Any] = {
                "key": key,
                "bundle": bundle,
                "measures": measures,
                "featureCount": p,
            }
            if p >= p_bound:
                entry["disabled"] = True
                entry["reason"] = (
                    f"{p} features vs {fold_train_n} training rows per fold: ordinary least "
                    f"squares is not numerically defensible here (no regularisation in this activity)."
                )
                models.append(entry)
                continue
            X, y_chk, _ = feature_matrix(frame, bundle, measures, TARGET, manifest=manifest)
            if not np.array_equal(np.round(y_chk), np.round(y)):
                raise RuntimeError(f"{key}: cohort mismatch with the shared target vector")
            pred = cross_val_predict(_pipeline(), X, y, cv=cv)
            r2, mse = _metrics(y, pred)
            entry["disabled"] = False
            entry["predicted"] = [round(float(v), PRED_DECIMALS) for v in pred]
            entry["cvR2"] = round(r2, 6)
            entry["cvMSE"] = round(mse, 4)
            models.append(entry)

    active = [m for m in models if not m["disabled"]]
    if not active:
        raise RuntimeError("catalog produced no enabled entries")

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "regression-compare",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
            "phenotypeTableSha256": src["phenotype_table"]["sha256"],
        },
        "target": {
            "name": TARGET,
            "label": "Full-scale IQ (FIQ)",
            "unit": "IQ points",
        },
        "cohort": {
            "n": n,
            "requirement": f"{TARGET} recorded after requiring complete brain data",
            "diagnosisNote": "held-out participants from the same 17 ABIDE-II sites; not unseen scanners",
        },
        "crossValidation": {
            "kind": "KFold",
            "nSplits": cv_cfg["n_splits"],
            "shuffle": cv_cfg["shuffle"],
            "randomState": cv_cfg["random_state"],
            "foldTrainN": fold_train_n,
        },
        "preprocessing": "Pipeline(StandardScaler, LinearRegression) fitted inside each fold",
        "observed": observed,
        "foldOf": fold_of,
        "bundles": {
            b: {
                "label": (
                    "All eligible ROIs"
                    if b == "all-eligible"
                    else manifest["bundles"][b]["label"]
                ),
                "rois": (
                    [r for r in manifest["atlas"]["roi_label_inventory"]
                     if r not in manifest["atlas"]["asymmetric_labels"]]
                    if b == "all-eligible"
                    else list(manifest["bundles"][b]["rois"])
                ),
            }
            for b in cat["bundles"]
        },
        "measures": {
            m: {"label": manifest["measures"][m]["name"], "unit": manifest["measures"][m]["unit"]}
            for subset in subsets
            for m in subset
        },
        "measurementSubsets": subsets,
        "models": models,
    }


def validate_catalog(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    """Human-readable problems for the committed catalog artifact."""
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]

    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "regression-compare":
        problems.append("activity must be 'regression-compare'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    if src.get("brainTableSha256") != manifest["source"]["brain_table"]["sha256"]:
        problems.append("source.brainTableSha256 does not match the manifest")
    if src.get("phenotypeTableSha256") != manifest["source"]["phenotype_table"]["sha256"]:
        problems.append("source.phenotypeTableSha256 does not match the manifest")

    observed = artifact.get("observed")
    fold_of = artifact.get("foldOf")
    n = artifact.get("cohort", {}).get("n")
    if not isinstance(observed, list) or not observed:
        problems.append("observed must be a non-empty array")
        return problems
    if n != len(observed):
        problems.append(f"cohort.n {n} != len(observed) {len(observed)}")
    if not isinstance(fold_of, list) or len(fold_of) != len(observed):
        problems.append("foldOf must align with observed")
        return problems
    n_splits = artifact.get("crossValidation", {}).get("nSplits")
    if sorted(set(fold_of)) != list(range(n_splits or 0)):
        problems.append(f"foldOf must use every fold index 0..{(n_splits or 0) - 1}")
    if any(not isinstance(v, int) or isinstance(v, bool) for v in observed):
        problems.append("observed must be integers")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in ("observed", "foldOf"):
        pass
    for extra_key in artifact.keys():
        if extra_key.lower() in identifier_token:
            problems.append(f"artifact has an identifier-shaped key: {extra_key!r}")

    keys_seen: set[str] = set()
    enabled = 0
    for m in artifact.get("models", []):
        if not isinstance(m, dict):
            problems.append("model entry is not an object")
            continue
        key = m.get("key")
        if key in keys_seen:
            problems.append(f"duplicate model key {key!r}")
        keys_seen.add(key)
        if m.get("bundle") not in artifact.get("bundles", {}):
            problems.append(f"model {key!r} references unknown bundle {m.get('bundle')!r}")
        for meas in m.get("measures", []):
            if meas not in artifact.get("measures", {}):
                problems.append(f"model {key!r} references unknown measure {meas!r}")
        if m.get("disabled"):
            if not m.get("reason"):
                problems.append(f"disabled model {key!r} has no reason")
            if "predicted" in m:
                problems.append(f"disabled model {key!r} must not carry predictions")
            continue
        enabled += 1
        pred = m.get("predicted")
        if not isinstance(pred, list) or len(pred) != len(observed):
            problems.append(f"model {key!r} predicted must align with observed")
            continue
        r2, mse = _metrics(observed, pred)
        if abs(r2 - m.get("cvR2", 1e9)) > 1e-4:
            problems.append(f"model {key!r} cvR2 {m.get('cvR2')} != recomputed {r2:.6f}")
        if abs(mse - m.get("cvMSE", 1e9)) > 1e-2:
            problems.append(f"model {key!r} cvMSE {m.get('cvMSE')} != recomputed {mse:.4f}")
        if m.get("featureCount") != len(_expected_cols(m, manifest)):
            problems.append(f"model {key!r} featureCount disagrees with its bundle x measures")

    if enabled == 0:
        problems.append("no enabled models in the catalog")
    return problems


def _expected_cols(model: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    try:
        return bundle_columns(model["bundle"], model["measures"], manifest=manifest)
    except Exception:  # pragma: no cover - defensive
        return []


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def _summary(artifact: dict[str, Any]) -> str:
    lines = [
        f"activity      : {artifact['activity']}",
        f"cohort.n      : {artifact['cohort']['n']}",
        f"folds         : {artifact['crossValidation']['nSplits']} "
        f"(train n/fold {artifact['crossValidation']['foldTrainN']})",
        f"models        : {len(artifact['models'])} "
        f"({sum(1 for m in artifact['models'] if not m['disabled'])} enabled)",
    ]
    for m in artifact["models"]:
        if m["disabled"]:
            lines.append(f"  {m['key']:34s} p={m['featureCount']:4d}  DISABLED")
        else:
            lines.append(
                f"  {m['key']:34s} p={m['featureCount']:4d}  cvR2={m['cvR2']:+.3f}  cvMSE={m['cvMSE']:.1f}"
            )
    return "\n".join(lines)


def cmd_refresh() -> int:
    frame = load_modeling_frame()
    artifact = build_catalog(frame)
    problems = validate_catalog(artifact)
    if problems:
        print("ERROR: built catalog failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    text = serialize(artifact)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    print(f"artifact sha256: {sha256_hex(text.encode('utf-8'))}")
    print(_summary(artifact))
    return 0


def cmd_check() -> int:
    if not ARTIFACT_PATH.exists():
        print(f"ERROR: {ARTIFACT_PATH} does not exist; run --refresh first.", file=sys.stderr)
        return 1
    on_disk = ARTIFACT_PATH.read_text(encoding="utf-8")
    try:
        artifact = json.loads(on_disk)
    except json.JSONDecodeError as exc:
        print(f"ERROR: catalog is not valid JSON: {exc}", file=sys.stderr)
        return 1
    problems = validate_catalog(artifact)
    if problems:
        print("ERROR: committed catalog failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if serialize(artifact) != on_disk:
        print("ERROR: committed catalog is not canonical (re-serialization differs).", file=sys.stderr)
        return 1
    print(f"OK: {ARTIFACT_PATH.relative_to(REPO_ROOT)} is valid and canonical.")
    print(f"artifact sha256: {sha256_hex(on_disk.encode('utf-8'))}")
    print(_summary(artifact))
    return 0


def cmd_print_upstream_hash() -> int:
    import urllib.request

    for key in ("brain_table", "phenotype_table"):
        spec = MANIFEST["source"][key]
        with urllib.request.urlopen(spec["url"], timeout=180) as response:  # noqa: S310
            raw = response.read()
        print(f"{spec['name']:24s} bytes={len(raw)} sha256={sha256_hex(raw)} pinned={spec['sha256']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute + write the catalog (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed catalog offline")
    mode.add_argument("--print-upstream-hash", action="store_true", help="report current source hashes")
    args = parser.parse_args(argv)
    if args.refresh:
        return cmd_refresh()
    if args.check:
        return cmd_check()
    return cmd_print_upstream_hash()


if __name__ == "__main__":
    raise SystemExit(main())
