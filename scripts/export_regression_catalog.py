#!/usr/bin/env python3
"""Deterministically export the Exercise II feature-set comparison catalog.

The browser activity ``regression-compare`` (book/_static/widgets/) lets a
student pick a measurement subset x anatomical ROI bundle for two models and
compares their held-out performance side by side. Re-implementing
scikit-learn in JavaScript would be fragile, so this script pre-computes a
finite, audited catalog of model results offline and the browser only switches
between them.

Output: ``book/_static/widgets/data/abide_regression_models.json``.

WP19 correction: this activity previously scored every entry with a hidden
5-fold ``KFold`` / ``cross_val_predict`` procedure. Early lessons no longer
teach or use cross-validation, so every catalog entry now uses the **same**
fixed, reproducible train/test split (``protocol.holdout_split`` --
identical to Exercise 2's own Section 2 worked example and Exercise 3):
``train_test_split(test_size=0.25, random_state=42, stratify=group)`` on the
same eligible cohort (age present after requiring usable brain data, n=1004).
Every entry shares the exact same 753 training / 251 test participants, so
the observed test-target vector is stored once and each model carries only
its held-out test-set predictions. Preprocessing (``StandardScaler``) is
fitted on the training participants only, inside a ``Pipeline``. No
participant identifiers, no raw brain features, no training scores.

Recipes come from ``book/config/abide_modeling.json`` (``catalog`` block).
An entry whose feature count reaches ``0.7 * n_train`` is emitted as
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
SCHEMA_VERSION = 2
PRED_DECIMALS = 4
TARGET = MANIFEST["catalog"]["target"]
IDENTIFIABILITY_FRACTION = 0.7


def _pipeline():
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LinearRegression())


def _metrics(observed: "Any", predicted: "Any") -> tuple[float, float]:
    import numpy as np

    obs = np.asarray(observed, dtype="float64")
    pred = np.asarray(predicted, dtype="float64")
    ss_res = float(np.sum((obs - pred) ** 2))
    ss_tot = float(np.sum((obs - obs.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    mse = float(np.mean((obs - pred) ** 2))
    return r2, mse


def _split_indices(n: int, groups: "Any", manifest: dict[str, Any]) -> tuple["Any", "Any"]:
    """The one fixed, reproducible train/test split (WP19): identical to
    Exercise 2 Section 2 / Exercise 3's own outer holdout split. Returns
    (idx_train, idx_test) -- the same participant indices are reused for
    every bundle x measure combination below."""
    import numpy as np
    from sklearn.model_selection import train_test_split

    hs = manifest["protocol"]["holdout_split"]
    idx = np.arange(n)
    idx_train, idx_test = train_test_split(
        idx, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups
    )
    return idx_train, idx_test


def build_catalog(frame: "Any", manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    import numpy as np

    manifest = manifest or MANIFEST
    cat = manifest["catalog"]
    hs = manifest["protocol"]["holdout_split"]

    present = frame[TARGET].notna().to_numpy()
    y_full = frame.loc[present, TARGET].to_numpy(dtype="float64")
    groups_full = frame.loc[present, "group"].to_numpy()
    n = int(len(y_full))

    idx_train, idx_test = _split_indices(n, groups_full, manifest)
    n_train, n_test = int(len(idx_train)), int(len(idx_test))
    overlap = set(idx_train.tolist()) & set(idx_test.tolist())
    if overlap:
        raise RuntimeError("train/test participant overlap in the shared holdout split")

    observed_test = [round(float(v), PRED_DECIMALS) for v in y_full[idx_test]]
    p_bound = IDENTIFIABILITY_FRACTION * n_train

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
                    f"{p} features vs {n_train} training rows: ordinary least "
                    f"squares is not numerically defensible here (no regularisation in this activity)."
                )
                models.append(entry)
                continue
            X_full, y_chk, _ = feature_matrix(frame, bundle, measures, TARGET, manifest=manifest)
            if not np.allclose(y_chk, y_full):
                raise RuntimeError(f"{key}: cohort mismatch with the shared target vector")
            X_train, X_test = X_full[idx_train], X_full[idx_test]
            y_train = y_full[idx_train]
            pipe = _pipeline()
            pipe.fit(X_train, y_train)
            pred_test = pipe.predict(X_test)
            r2, mse = _metrics(y_full[idx_test], pred_test)
            entry["disabled"] = False
            entry["predicted"] = [round(float(v), PRED_DECIMALS) for v in pred_test]
            entry["testR2"] = round(r2, 6)
            entry["testMSE"] = round(mse, 4)
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
            "label": manifest["targets"][TARGET]["label"],
            "unit": manifest["targets"][TARGET]["unit"],
        },
        "cohort": {
            "n": n,
            "requirement": f"{TARGET} recorded after requiring complete brain data",
            "diagnosisNote": "held-out participants from the same 17 ABIDE-II sites; not unseen scanners",
        },
        "holdoutSplit": {
            "testSize": hs["test_size"],
            "randomState": hs["random_state"],
            "stratify": hs["stratify"],
            "nTrain": n_train,
            "nTest": n_test,
        },
        "preprocessing": "Pipeline(StandardScaler, LinearRegression) fit on the training participants only",
        "observedTest": observed_test,
        "bundles": {
            b: {
                "label": (
                    "All eligible ROIs"
                    if b == "all-eligible"
                    else manifest["bundles"][b]["label"]
                ),
                "rois": (
                    list(manifest["atlas"]["roi_label_inventory"])
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

    observed = artifact.get("observedTest")
    hs = artifact.get("holdoutSplit", {})
    n = artifact.get("cohort", {}).get("n")
    n_train = hs.get("nTrain")
    n_test = hs.get("nTest")
    if not isinstance(observed, list) or not observed:
        problems.append("observedTest must be a non-empty array")
        return problems
    if n_test != len(observed):
        problems.append(f"holdoutSplit.nTest {n_test} != len(observedTest) {len(observed)}")
    if not isinstance(n_train, int) or not isinstance(n_test, int) or n_train + n_test != n:
        problems.append(f"holdoutSplit.nTrain + nTest must equal cohort.n ({n})")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in observed):
        problems.append("observedTest must be numeric (int or float) target values")

    identifier_token = ("id", "sub", "subject", "site", "participant")
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
            problems.append(f"model {key!r} predicted must align with observedTest")
            continue
        r2, mse = _metrics(observed, pred)
        if abs(r2 - m.get("testR2", 1e9)) > 1e-4:
            problems.append(f"model {key!r} testR2 {m.get('testR2')} != recomputed {r2:.6f}")
        if abs(mse - m.get("testMSE", 1e9)) > 1e-2:
            problems.append(f"model {key!r} testMSE {m.get('testMSE')} != recomputed {mse:.4f}")
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
    hs = artifact["holdoutSplit"]
    lines = [
        f"activity      : {artifact['activity']}",
        f"cohort.n      : {artifact['cohort']['n']}",
        f"holdout split : n_train={hs['nTrain']} n_test={hs['nTest']} "
        f"(test_size={hs['testSize']}, seed={hs['randomState']})",
        f"models        : {len(artifact['models'])} "
        f"({sum(1 for m in artifact['models'] if not m['disabled'])} enabled)",
    ]
    for m in artifact["models"]:
        if m["disabled"]:
            lines.append(f"  {m['key']:34s} p={m['featureCount']:4d}  DISABLED")
        else:
            lines.append(
                f"  {m['key']:34s} p={m['featureCount']:4d}  testR2={m['testR2']:+.3f}  testMSE={m['testMSE']:.1f}"
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
