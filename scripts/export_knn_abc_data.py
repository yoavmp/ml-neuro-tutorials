#!/usr/bin/env python3
"""Deterministically export the Exercise 3 Section 3 "honest vs invalid" KNN
interactive (WP14 section 4.4).

The browser activity ``knn-abc`` lets a student choose one ``k`` and see three
synchronized observed-vs-predicted panels, all standardized KNN regression for
``age`` on Exercise 2's own locked 753/251 outer train/test split and the
canonical 360-feature recipe:

* **A -- valid:** fit on the 753 training rows, evaluate the 251 test rows;
* **B -- resubstitution:** fit on the 753 training rows, evaluate those same
  training rows;
* **C -- invalid leakage:** fit on the 251 test rows, evaluate those same test
  rows.

As in ``export_knn_explore_data.py``, no brain feature or participant
identifier is shipped: for every query participant in each panel, this script
stores only its reference-pool target (age) values reordered nearest-first, so
the browser recomputes the exact k-nearest-neighbour mean with one client-side
prefix-mean per chosen k. Because C's reference pool (the 251 test rows) is
smaller than A/B's (the 753 training rows), every panel's neighbour list is
truncated to the shared valid range ``1..min(n_train, n_test)`` = 1..251 --
the UI never offers a k value some panel cannot support.

Split / recipe: exactly Exercise 2's own locked outer holdout
(``protocol.holdout_split``) on the canonical ``all-eligible x CT`` recipe
(p=360) -- the identical 753/251 participants used throughout this notebook.

Output: ``book/_static/widgets/data/abide_knn_abc.json``.

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

from abide_modeling_data import (  # noqa: E402
    MANIFEST,
    REPO_ROOT,
    assert_brain_only,
    bundle_columns,
    load_modeling_frame,
    sha256_hex,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_knn_abc.json"
SCHEMA_VERSION = 1
DECIMALS = 3


def _outer_split(frame: Any, manifest: dict[str, Any] | None = None):
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    knn_cfg = manifest["knn"]
    target = knn_cfg["target"]
    recipe = knn_cfg["canonical_recipe"]
    cols = bundle_columns(recipe["bundle"], recipe["measures"], available=frame.columns, manifest=manifest)
    assert_brain_only(cols)
    if target in cols:
        raise ValueError("leakage: target is in the feature list")

    present = frame[target].notna().to_numpy()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, target].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()

    hs = manifest["protocol"]["holdout_split"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups
    )
    return cols, X_train, X_test, y_train, y_test


def _sorted_neighbor_targets(X_query: Any, X_ref: Any, y_ref: Any, top: int):
    """For every row of X_query, the reference-set y values sorted by
    ascending Euclidean distance (already-scaled space), truncated to the
    nearest ``top`` entries. Shape (n_query, top)."""
    import numpy as np

    d = np.linalg.norm(X_query[:, None, :] - X_ref[None, :, :], axis=2)
    order = np.argsort(d, axis=1, kind="stable")[:, :top]
    return y_ref[order]


def _validate_panel_against_sklearn(X_fit_raw, y_fit, X_query_raw, sorted_targets, k_values: list[int]) -> None:
    import numpy as np
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    for k in k_values:
        real = (
            make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=k))
            .fit(X_fit_raw, y_fit)
            .predict(X_query_raw)
        )
        cum = sorted_targets[:, :k].sum(axis=1) / k
        if not np.allclose(real, cum, atol=1e-6):
            raise RuntimeError(
                f"knn-abc panel disagrees with sklearn KNeighborsRegressor at k={k}: "
                f"max abs diff {np.max(np.abs(real - cum))}"
            )


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    manifest = manifest or MANIFEST
    knn_cfg = manifest["knn"]
    target = knn_cfg["target"]

    cols, X_train, X_test, y_train, y_test = _outer_split(frame, manifest)
    n_train, n_test = len(y_train), len(y_test)
    k_max = min(n_train, n_test)

    # A / B: one pipeline, scaler fit on the training rows only.
    scaler_ab = StandardScaler().fit(X_train)
    Xtr_ab = scaler_ab.transform(X_train)
    Xte_ab = scaler_ab.transform(X_test)

    # C: a SEPARATE, deliberately invalid pipeline -- scaler fit on the test
    # rows. Isolated from A/B's scaler so C's leakage is not diluted.
    scaler_c = StandardScaler().fit(X_test)
    Xte_c = scaler_c.transform(X_test)

    sorted_a = _sorted_neighbor_targets(Xte_ab, Xtr_ab, y_train, top=k_max)  # n_test x k_max
    sorted_b = _sorted_neighbor_targets(Xtr_ab, Xtr_ab, y_train, top=k_max)  # n_train x k_max (self-inclusive)
    sorted_c = _sorted_neighbor_targets(Xte_c, Xte_c, y_test, top=k_max)  # n_test x k_max (self-inclusive)

    sample_ks = sorted({k for k in (1, 5, 15, 17, 50, 100, k_max) if k <= k_max})
    _validate_panel_against_sklearn(X_train, y_train, X_test, sorted_a, sample_ks)
    _validate_panel_against_sklearn(X_train, y_train, X_train, sorted_b, sample_ks)
    _validate_panel_against_sklearn(X_test, y_test, X_test, sorted_c, sample_ks)

    # exact k=1 structural endpoint: B and C are perfect resubstitution
    # (every query point is its own nearest neighbour, distance 0); A is not.
    if not np.allclose(sorted_b[:, 0], y_train, atol=1e-9):
        raise RuntimeError("k=1: B's nearest neighbour is not each training row itself")
    if not np.allclose(sorted_c[:, 0], y_test, atol=1e-9):
        raise RuntimeError("k=1: C's nearest neighbour is not each test row itself")

    src = manifest["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "knn-abc",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
            "phenotypeTableSha256": src["phenotype_table"]["sha256"],
        },
        "target": {
            "name": target,
            "label": manifest["targets"][target]["label"],
            "unit": manifest["targets"][target]["unit"],
        },
        "featureRecipe": {
            "bundle": knn_cfg["canonical_recipe"]["bundle"],
            "measures": knn_cfg["canonical_recipe"]["measures"],
            "featureCount": len(cols),
        },
        "split": {
            "outerHoldout": manifest["protocol"]["holdout_split"],
            "nTrain": n_train,
            "nTest": n_test,
            "kMax": k_max,
        },
        "selectedKFromAudit": knn_cfg["selected_k"],
        "observedTrain": [round(float(v), DECIMALS) for v in y_train],
        "observedTest": [round(float(v), DECIMALS) for v in y_test],
        "neighborTargetsA": [[round(float(v), DECIMALS) for v in row] for row in sorted_a],
        "neighborTargetsB": [[round(float(v), DECIMALS) for v in row] for row in sorted_b],
        "neighborTargetsC": [[round(float(v), DECIMALS) for v in row] for row in sorted_c],
    }


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "knn-abc":
        problems.append("activity must be 'knn-abc'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    split = artifact.get("split", {})
    n_train, n_test, k_max = split.get("nTrain"), split.get("nTest"), split.get("kMax")
    if not all(isinstance(v, int) for v in (n_train, n_test, k_max)):
        return problems + ["split.nTrain / nTest / kMax must be integers"]
    if k_max != min(n_train, n_test):
        problems.append("split.kMax must equal min(nTrain, nTest)")

    observed_train = artifact.get("observedTrain")
    observed_test = artifact.get("observedTest")
    if not isinstance(observed_train, list) or len(observed_train) != n_train:
        problems.append("observedTrain must align with split.nTrain")
    if not isinstance(observed_test, list) or len(observed_test) != n_test:
        problems.append("observedTest must align with split.nTest")

    panels = {
        "neighborTargetsA": n_test,
        "neighborTargetsB": n_train,
        "neighborTargetsC": n_test,
    }
    for key, n_rows in panels.items():
        rows = artifact.get(key)
        if not isinstance(rows, list) or len(rows) != n_rows:
            problems.append(f"{key} must have {n_rows} rows")
            continue
        for row in rows:
            if not isinstance(row, list) or len(row) != k_max:
                problems.append(f"{key} row must have kMax ({k_max}) entries")
                break

    # k=1 structural endpoint: B and C are exact resubstitution.
    b_rows, c_rows = artifact.get("neighborTargetsB"), artifact.get("neighborTargetsC")
    if isinstance(b_rows, list) and isinstance(observed_train, list) and len(b_rows) == len(observed_train):
        if any(abs(row[0] - obs) > 1e-6 for row, obs in zip(b_rows, observed_train)):
            problems.append("neighborTargetsB[:, 0] (k=1) must equal observedTrain -- each training row is its own nearest neighbour")
    if isinstance(c_rows, list) and isinstance(observed_test, list) and len(c_rows) == len(observed_test):
        if any(abs(row[0] - obs) > 1e-6 for row, obs in zip(c_rows, observed_test)):
            problems.append("neighborTargetsC[:, 0] (k=1) must equal observedTest -- each test row is its own nearest neighbour")

    selected_k = artifact.get("selectedKFromAudit")
    if not isinstance(selected_k, int) or not (1 <= selected_k <= (k_max or 0)):
        problems.append("selectedKFromAudit must be within [1, kMax]")

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
    s = artifact["split"]
    return (
        f"activity       : {artifact['activity']}\n"
        f"feature recipe : {artifact['featureRecipe']['bundle']} x "
        f"{'+'.join(artifact['featureRecipe']['measures'])} (p={artifact['featureRecipe']['featureCount']})\n"
        f"n_train        : {s['nTrain']}   n_test : {s['nTest']}   k_max (shared) : {s['kMax']}\n"
        f"default (audit-selected) k : {artifact['selectedKFromAudit']}"
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
    print(f"artifact sha256: {sha256_hex(on_disk.encode('utf-8'))}")
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
