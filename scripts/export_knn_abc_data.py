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
identifier is shipped, and (WP15 §3) neighbour target values are never stored
directly: for every query participant in each panel, this script stores a row
INDEX (nearest first) into that panel's own reference-pool target array, so
the browser reconstructs the exact k-nearest-neighbour mean with one
client-side prefix-mean per chosen k over ``refTargets[index]``. Because C's
reference pool (the 251 test rows) is smaller than A/B's (the 753 training
rows), every panel's neighbour list is truncated to the shared valid range
``1..min(n_train, n_test)`` = 1..251 -- the UI never offers a k value some
panel cannot support.

Panels A and B share the exact same reference pool (the 753 training rows'
targets, ``observedTrain``) -- only their QUERY sets differ (test rows for A,
the training rows themselves for B) -- so ``observedTrain`` is stored once and
both ``neighborIndexA``/``neighborIndexB`` index into it. Panel C is
self-referential against the 251 test rows (``observedTest``).

Split / recipe: exactly Exercise 2's own locked outer holdout
(``protocol.holdout_split``) on the canonical ``all-eligible x CT`` recipe
(p=360) -- the identical 753/251 participants used throughout this notebook.

Output: ``book/_static/widgets/data/abide_knn_abc_manifest.json`` +
``book/_static/widgets/data/abide_knn_abc.bin``.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute,
  validate, and write both files.
* ``--check``    (offline): re-validate the committed manifest + binary and
  confirm both are byte-for-byte canonical.
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
from binary_asset import BinaryAssetBuilder, decode_section  # noqa: E402

DATA_DIR = REPO_ROOT / "book" / "_static" / "widgets" / "data"
MANIFEST_PATH = DATA_DIR / "abide_knn_abc_manifest.json"
BINARY_PATH = DATA_DIR / "abide_knn_abc.bin"
SCHEMA_VERSION = 2
DISPLAY_DECIMALS = 3  # the rounding precision schema v1 used to display/round values at


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


def _sorted_neighbor_index(X_query: Any, X_ref: Any, top: int):
    """For every row of X_query, the reference-set row INDEX order, sorted by
    ascending Euclidean distance (already-scaled space), truncated to the
    nearest ``top`` entries. Shape (n_query, top); values in [0, n_ref)."""
    import numpy as np

    d = np.linalg.norm(X_query[:, None, :] - X_ref[None, :, :], axis=2)
    return np.argsort(d, axis=1, kind="stable")[:, :top]


def _validate_panel_against_sklearn(X_fit_raw, y_fit, X_query_raw, sorted_target_values, k_values: list[int]) -> None:
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
        cum = sorted_target_values[:, :k].sum(axis=1) / k
        if not np.allclose(real, cum, atol=1e-6):
            raise RuntimeError(
                f"knn-abc panel disagrees with sklearn KNeighborsRegressor at k={k}: "
                f"max abs diff {np.max(np.abs(real - cum))}"
            )


def _verify_float32_precision(index_u16: Any, ref_targets_f32: Any, ref_targets_f64: Any, k_values: list[int]) -> None:
    """Prove float32(ref targets) + uint16(index) reconstructs the same
    per-k means as the float64 computation, to the artifact's existing
    display rounding (WP15 §3.2)."""
    import numpy as np

    sorted_f64 = ref_targets_f64[index_u16]
    sorted_f32 = ref_targets_f32[index_u16].astype("float64")
    tol = 10 ** (-DISPLAY_DECIMALS)
    for k in k_values:
        mean_f64 = sorted_f64[:, :k].mean(axis=1)
        mean_f32 = sorted_f32[:, :k].mean(axis=1)
        diff = float(np.max(np.abs(mean_f64 - mean_f32)))
        if diff > tol:
            raise RuntimeError(f"float32 round-trip precision check failed at k={k}: max abs diff {diff}, tolerance {tol}")


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> tuple[dict[str, Any], bytes]:
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

    index_a = _sorted_neighbor_index(Xte_ab, Xtr_ab, top=k_max)  # n_test x k_max, into y_train
    index_b = _sorted_neighbor_index(Xtr_ab, Xtr_ab, top=k_max)  # n_train x k_max (self-inclusive), into y_train
    index_c = _sorted_neighbor_index(Xte_c, Xte_c, top=k_max)  # n_test x k_max (self-inclusive), into y_test

    sample_ks = sorted({k for k in (1, 5, 15, 17, 50, 100, k_max) if k <= k_max})
    _validate_panel_against_sklearn(X_train, y_train, X_test, y_train[index_a], sample_ks)
    _validate_panel_against_sklearn(X_train, y_train, X_train, y_train[index_b], sample_ks)
    _validate_panel_against_sklearn(X_test, y_test, X_test, y_test[index_c], sample_ks)

    # exact k=1 structural endpoint: B and C are perfect resubstitution
    # (every query point is its own nearest neighbour, distance 0); A is not.
    if not np.allclose(y_train[index_b][:, 0], y_train, atol=1e-9):
        raise RuntimeError("k=1: B's nearest neighbour is not each training row itself")
    if not np.allclose(y_test[index_c][:, 0], y_test, atol=1e-9):
        raise RuntimeError("k=1: C's nearest neighbour is not each test row itself")

    _verify_float32_precision(index_a, y_train.astype("float32"), y_train, sample_ks)
    _verify_float32_precision(index_b, y_train.astype("float32"), y_train, sample_ks)
    _verify_float32_precision(index_c, y_test.astype("float32"), y_test, sample_ks)

    builder = BinaryAssetBuilder()
    builder.add("observedTrain", "float32", y_train)
    builder.add("observedTest", "float32", y_test)
    builder.add("neighborIndexA", "uint16", index_a)
    builder.add("neighborIndexB", "uint16", index_b)
    builder.add("neighborIndexC", "uint16", index_c)
    blob = builder.build()

    src = manifest["source"]
    manifest_json: dict[str, Any] = {
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
        "binary": {
            "path": BINARY_PATH.name,
            "byteLength": len(blob),
            "sha256": sha256_hex(blob),
        },
        "sections": builder.sections,
    }
    return manifest_json, blob


def _reconstruct_logical(manifest_json: dict[str, Any], blob: bytes) -> dict[str, Any]:
    sections = manifest_json["sections"]
    observed_train = decode_section(blob, sections["observedTrain"])
    observed_test = decode_section(blob, sections["observedTest"])
    index_a = decode_section(blob, sections["neighborIndexA"])
    index_b = decode_section(blob, sections["neighborIndexB"])
    index_c = decode_section(blob, sections["neighborIndexC"])
    return {
        "observedTrain": observed_train,
        "observedTest": observed_test,
        "neighborTargetsA": observed_train[index_a],
        "neighborTargetsB": observed_train[index_b],
        "neighborTargetsC": observed_test[index_c],
    }


def validate_artifact(manifest_json: Any, blob: bytes, manifest: dict[str, Any] | None = None) -> list[str]:
    import numpy as np

    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(manifest_json, dict):
        return ["manifest is not a JSON object"]
    if manifest_json.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if manifest_json.get("activity") != "knn-abc":
        problems.append("activity must be 'knn-abc'")

    src = manifest_json.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    binary_meta = manifest_json.get("binary", {})
    if binary_meta.get("byteLength") != len(blob):
        problems.append(f"binary.byteLength {binary_meta.get('byteLength')} != actual {len(blob)}")
    if binary_meta.get("sha256") != sha256_hex(blob):
        problems.append("binary.sha256 does not match the actual binary file")

    sections = manifest_json.get("sections", {})
    required_sections = {"observedTrain", "observedTest", "neighborIndexA", "neighborIndexB", "neighborIndexC"}
    if set(sections) != required_sections:
        problems.append(f"sections keys {set(sections)} != required {required_sections}")
        return problems
    for name, sec in sections.items():
        end = sec["byteOffset"] + sec["byteLength"]
        if end > len(blob):
            problems.append(f"section {name!r} extends past the end of the binary file")
        if sec["byteOffset"] % 4 != 0:
            problems.append(f"section {name!r} byteOffset {sec['byteOffset']} is not 4-byte aligned")

    split = manifest_json.get("split", {})
    n_train, n_test, k_max = split.get("nTrain"), split.get("nTest"), split.get("kMax")
    if not all(isinstance(v, int) for v in (n_train, n_test, k_max)):
        return problems + ["split.nTrain / nTest / kMax must be integers"]
    if k_max != min(n_train, n_test):
        problems.append("split.kMax must equal min(nTrain, nTest)")

    if sections["observedTrain"]["shape"] != [n_train]:
        problems.append("observedTrain shape must be [nTrain]")
    if sections["observedTest"]["shape"] != [n_test]:
        problems.append("observedTest shape must be [nTest]")
    if sections["neighborIndexA"]["shape"] != [n_test, k_max]:
        problems.append("neighborIndexA shape must be [nTest, kMax]")
    if sections["neighborIndexB"]["shape"] != [n_train, k_max]:
        problems.append("neighborIndexB shape must be [nTrain, kMax]")
    if sections["neighborIndexC"]["shape"] != [n_test, k_max]:
        problems.append("neighborIndexC shape must be [nTest, kMax]")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in manifest_json.keys():
        if key.lower() in identifier_token:
            problems.append(f"manifest has an identifier-shaped key: {key!r}")

    try:
        idx_a = decode_section(blob, sections["neighborIndexA"])
        idx_b = decode_section(blob, sections["neighborIndexB"])
        idx_c = decode_section(blob, sections["neighborIndexC"])
        if idx_a.size and (int(idx_a.min()) < 0 or int(idx_a.max()) >= (n_train or 0)):
            problems.append("neighborIndexA has an out-of-range index")
        if idx_b.size and (int(idx_b.min()) < 0 or int(idx_b.max()) >= (n_train or 0)):
            problems.append("neighborIndexB has an out-of-range index")
        if idx_c.size and (int(idx_c.min()) < 0 or int(idx_c.max()) >= (n_test or 0)):
            problems.append("neighborIndexC has an out-of-range index")

        logical = _reconstruct_logical(manifest_json, blob)
    except (ValueError, KeyError, IndexError) as exc:
        problems.append(f"could not decode/reconstruct sections: {exc}")
        return problems

    observed_train, observed_test = logical["observedTrain"], logical["observedTest"]
    b_rows, c_rows = logical["neighborTargetsB"], logical["neighborTargetsC"]
    if b_rows.shape[0] == len(observed_train) and not np.allclose(b_rows[:, 0], observed_train, atol=1e-3):
        problems.append("neighborTargetsB[:, 0] (k=1) must equal observedTrain -- each training row is its own nearest neighbour")
    if c_rows.shape[0] == len(observed_test) and not np.allclose(c_rows[:, 0], observed_test, atol=1e-3):
        problems.append("neighborTargetsC[:, 0] (k=1) must equal observedTest -- each test row is its own nearest neighbour")

    selected_k = manifest_json.get("selectedKFromAudit")
    if not isinstance(selected_k, int) or not (1 <= selected_k <= (k_max or 0)):
        problems.append("selectedKFromAudit must be within [1, kMax]")

    return problems


def serialize_manifest(manifest_json: dict[str, Any]) -> str:
    return json.dumps(manifest_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def _summary(manifest_json: dict[str, Any]) -> str:
    s = manifest_json["split"]
    b = manifest_json["binary"]
    return (
        f"activity       : {manifest_json['activity']}\n"
        f"feature recipe : {manifest_json['featureRecipe']['bundle']} x "
        f"{'+'.join(manifest_json['featureRecipe']['measures'])} (p={manifest_json['featureRecipe']['featureCount']})\n"
        f"n_train        : {s['nTrain']}   n_test : {s['nTest']}   k_max (shared) : {s['kMax']}\n"
        f"default (audit-selected) k : {manifest_json['selectedKFromAudit']}\n"
        f"binary payload : {b['byteLength']} bytes  sha256={b['sha256']}"
    )


def cmd_refresh() -> int:
    frame = load_modeling_frame()
    manifest_json, blob = build_artifact(frame)
    problems = validate_artifact(manifest_json, blob)
    if problems:
        print("ERROR: built artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BINARY_PATH.write_bytes(blob)
    manifest_text = serialize_manifest(manifest_json)
    MANIFEST_PATH.write_text(manifest_text, encoding="utf-8", newline="\n")
    print(f"wrote {BINARY_PATH.relative_to(REPO_ROOT)} ({len(blob)} bytes)")
    print(f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)} ({len(manifest_text.encode('utf-8'))} bytes)")
    print(_summary(manifest_json))
    return 0


def cmd_check() -> int:
    if not MANIFEST_PATH.exists() or not BINARY_PATH.exists():
        print(f"ERROR: {MANIFEST_PATH} / {BINARY_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    try:
        manifest_json = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        print(f"ERROR: manifest is not valid JSON: {exc}", file=sys.stderr)
        return 1
    blob = BINARY_PATH.read_bytes()
    problems = validate_artifact(manifest_json, blob)
    if problems:
        print("ERROR: committed artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if serialize_manifest(manifest_json) != manifest_text:
        print("ERROR: committed manifest is not canonical (re-serialization differs).", file=sys.stderr)
        return 1
    print(f"OK: {MANIFEST_PATH.relative_to(REPO_ROOT)} + {BINARY_PATH.relative_to(REPO_ROOT)} are valid and canonical.")
    print(_summary(manifest_json))
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
