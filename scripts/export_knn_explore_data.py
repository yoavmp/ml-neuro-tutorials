#!/usr/bin/env python3
"""Deterministically export the Exercise 3 KNN "vary k" activity data.

The browser activity ``knn-explore`` (book/_static/widgets/) lets a student move
a slider across every integer ``k`` from 1 through ``N_fit`` and see standardized
KNN regression for ``age`` refit at that ``k`` -- fitting error, validation
error, and an observed-vs-predicted validation scatter -- entirely offline, no
Python kernel.

Re-implementing scikit-learn's neighbour search in the browser would be
fragile, so this script precomputes, once and deterministically:

* the per-``k`` fitting and validation R2/MSE curve, for every integer
  ``k`` from 1 through ``N_fit`` (via the "sort distances once, cumulative-sum
  the targets" trick -- WP13 section 4.6 -- rather than refitting
  ``KNeighborsRegressor`` ``N_fit`` separate times);
* for every validation participant, the **row index** (nearest first) of its
  ``N_fit`` fitting-set neighbours, rather than their target values directly
  (WP15 §3: a compact binary format -- see below). The browser reconstructs
  the exact observed-vs-predicted scatter for *any* chosen k with one
  client-side prefix mean over ``fitTargets[index]``, without ever seeing a
  brain feature, a distance, or a participant identifier -- only a small
  target-value array plus small-integer indices into it;
* (WP14 section 4.8) the same index reordering for two more deterministic
  bootstrap resamples ("B", "C") of the fitting pool, alongside the original
  ("A"), so the browser can show how predictions at a fixed validation
  participant and a fixed k vary across different training-set draws -- an
  empirical training-sample-sensitivity ("variance-proxy") and
  systematic-smoothing ("bias-like-proxy") illustration, computed
  client-side, never touching the outer test set.

Both computations are validated against a real, independently-fitted
``Pipeline(StandardScaler(), KNeighborsRegressor(k))`` at representative ``k``
before anything is written.

WP15 §3 compact binary format
------------------------------

Schema v2 (WP13/WP14) stored, per training sample, an explicit
``n_validation x n_fit`` matrix of ALREADY-REORDERED target values as JSON
floats (three such matrices, one of them -- "A" -- a byte-for-byte duplicate
of the top-level baseline matrix). Schema v3 stores instead:

* each training sample's own reference-pool target array ONCE, as a flat
  little-endian float32 array (``observedFitting`` doubles as sample A's own
  pool; B/C get their own resampled ``fitTargetsB``/``fitTargetsC``);
* one ``n_validation x n_fit`` matrix of little-endian **uint16 row indices**
  into that sample's own target array (nearest-first), per sample --
  ``neighborIndexA/B/C``. A's index matrix also stands in for the removed
  top-level "baseline" matrix (they were always identical -- WP14's own
  validation already proved ``trainingSamples.A == top-level`` byte-for-byte,
  so schema v3 simply never duplicates that storage in the first place);
* the five per-k curve series, still small (``N_fit`` entries each), as flat
  float32 arrays.

All of this lives in one deterministic binary file
(``abide_knn_explore.bin``), described by a small JSON manifest
(``abide_knn_explore_manifest.json``) giving every section's dtype, shape,
byte offset/length, and the whole file's SHA-256 digest
(``scripts/binary_asset.py``; the matching browser decoder is
``interactive/src/binary-asset.ts``). float32 is proven sufficient, not
assumed: :func:`_verify_float32_precision` recomputes the full curve/endpoint
values from the float32-round-tripped arrays and asserts they still match the
float64 computation at the artifact's existing 4-decimal display rounding
before anything is written.

Split protocol (``book/config/abide_modeling.json`` -> ``knn``):

1. Exercise 2's own locked outer holdout split
   (``protocol.holdout_split``: ``test_size=0.25, random_state=42,
   stratify=group``) on the canonical ``all-eligible x CT`` recipe (p=360) --
   the SAME 753/251 participants as Exercise 2's own workflow. The outer test
   partition (251 rows) never appears in this artifact at all.
2. ``knn.dev_split`` (``test_size=0.25, random_state=7, stratify=group``)
   further splits the 753-row outer-TRAINING partition only, into a fitting
   subset (``N_fit`` = 564) and a validation subset (``N_val`` = 189).

Output: ``book/_static/widgets/data/abide_knn_explore_manifest.json`` +
``book/_static/widgets/data/abide_knn_explore.bin``.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute,
  validate, and write both files.
* ``--check``    (offline): re-validate the committed manifest + binary and
  confirm both are byte-for-byte canonical.

Determinism: manifest JSON uses ``sort_keys`` + compact separators, no
timestamps; the binary is little-endian, 4-byte-aligned, built the same way
every time from the same inputs (proven by ``tests/test_binary_asset.py``'s
own determinism test and this script's own two-build comparison in CI via
``jupyter-book build`` x2, WP15 §5.12).
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
MANIFEST_PATH = DATA_DIR / "abide_knn_explore_manifest.json"
BINARY_PATH = DATA_DIR / "abide_knn_explore.bin"
SCHEMA_VERSION = 3
DISPLAY_DECIMALS = 4  # the rounding precision schema v2 used to display/round values at
TARGET = MANIFEST["knn"]["target"]

# WP14 section 4.8: three deterministic alternative training-set selections
# from the SAME fitting pool, used by the enhanced explorer's variance/bias
# proxy panels. "A" is the fitting pool itself (already computed above); "B"
# and "C" are equal-sized bootstrap resamples (with replacement) of it, each
# with its own StandardScaler refit on its own resampled rows -- a genuine
# "what if you had drawn a different training sample" re-fit, not a relabel.
BOOTSTRAP_SEEDS = {"B": 101, "C": 102}


def _outer_split(frame: Any, manifest: dict[str, Any] | None = None):
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    target = manifest["knn"]["target"]
    recipe = manifest["knn"]["canonical_recipe"]
    cols = bundle_columns(recipe["bundle"], recipe["measures"], available=frame.columns, manifest=manifest)
    assert_brain_only(cols)
    if target in cols:
        raise ValueError("leakage: target is in the feature list")

    present = frame[target].notna().to_numpy()
    X = frame.loc[present, cols].to_numpy(dtype="float64")
    y = frame.loc[present, target].to_numpy(dtype="float64")
    groups = frame.loc[present, "group"].to_numpy()

    hs = manifest["protocol"]["holdout_split"]
    X_train, X_test, y_train, y_test, g_train, g_test = train_test_split(
        X, y, groups, test_size=hs["test_size"], random_state=hs["random_state"], stratify=groups
    )
    return cols, X_train, y_train, g_train


def _dev_split(X_train: Any, y_train: Any, g_train: Any, manifest: dict[str, Any] | None = None):
    from sklearn.model_selection import train_test_split

    manifest = manifest or MANIFEST
    ds = manifest["knn"]["dev_split"]
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=ds["test_size"], random_state=ds["random_state"], stratify=g_train
    )
    return X_fit, X_val, y_fit, y_val


def _sorted_neighbor_index(X_query: Any, X_fit: Any):
    """For every row of X_query, the fitting-set row INDEX order, sorted by
    ascending Euclidean distance (in already-scaled space). Shape
    (n_query, n_fit); values in [0, n_fit)."""
    import numpy as np

    d = np.linalg.norm(X_query[:, None, :] - X_fit[None, :, :], axis=2)
    return np.argsort(d, axis=1, kind="stable")


def _r2_mse_curve(sorted_targets: Any, observed: Any) -> tuple[list[float], list[float]]:
    """Per-k R2/MSE for every k=1..n_fit, from cumulative means of
    `sorted_targets` (n_obs x n_fit, nearest-first target VALUES)."""
    import numpy as np

    n_fit = sorted_targets.shape[1]
    cum = np.cumsum(sorted_targets, axis=1)
    ks = np.arange(1, n_fit + 1)
    pred_all_k = cum / ks[None, :]  # n_obs x n_fit

    obs = observed[:, None]
    ss_res = np.sum((obs - pred_all_k) ** 2, axis=0)
    ss_tot = float(np.sum((observed - observed.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    mse = np.mean((obs - pred_all_k) ** 2, axis=0)
    return [round(float(v), 6) for v in r2], [round(float(v), 4) for v in mse]


def _validate_against_sklearn(X_fit, y_fit, X_val, pred_val_all_k, sample_ks: list[int]) -> None:
    import numpy as np
    from sklearn.neighbors import KNeighborsRegressor

    for k in sample_ks:
        real = KNeighborsRegressor(n_neighbors=k).fit(X_fit, y_fit).predict(X_val)
        mine = pred_val_all_k[:, k - 1]
        if not np.allclose(real, mine, atol=1e-6):
            raise RuntimeError(
                f"cumulative-sum predictions disagree with sklearn KNeighborsRegressor at k={k}: "
                f"max abs diff {np.max(np.abs(real - mine))}"
            )


def _bootstrap_training_sample(X_fit_raw: Any, y_fit: Any, X_val_raw: Any, seed: int) -> dict[str, Any]:
    """One bootstrap resample (with replacement) of the fitting pool, refit
    with its own StandardScaler. Returns its own resampled target array and
    the validation neighbour-INDEX matrix (into that array), independently
    validated against a real sklearn Pipeline."""
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    n_fit = len(y_fit)
    rng = np.random.default_rng(seed)
    idx = rng.choice(n_fit, size=n_fit, replace=True)
    X_resampled_raw = X_fit_raw[idx]
    y_resampled = y_fit[idx]

    scaler_b = StandardScaler().fit(X_resampled_raw)
    Xf_b = scaler_b.transform(X_resampled_raw)
    Xv_b = scaler_b.transform(X_val_raw)

    index_b = _sorted_neighbor_index(Xv_b, Xf_b)  # n_val x n_fit
    sorted_val_b = y_resampled[index_b]
    cum_b = np.cumsum(sorted_val_b, axis=1)
    ks = np.arange(1, n_fit + 1)
    pred_val_all_k_b = cum_b / ks[None, :]

    sample_ks = sorted({k for k in (1, 5, 15, 17, 50, 200, n_fit) if k <= n_fit})
    for k in sample_ks:
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler as _SS

        real = (
            make_pipeline(_SS(), KNeighborsRegressor(n_neighbors=k))
            .fit(X_resampled_raw, y_resampled)
            .predict(X_val_raw)
        )
        mine = pred_val_all_k_b[:, k - 1]
        if not np.allclose(real, mine, atol=1e-6):
            raise RuntimeError(
                f"bootstrap sample (seed={seed}): cumulative-sum predictions disagree with sklearn "
                f"at k={k}: max abs diff {np.max(np.abs(real - mine))}"
            )

    fit_mean_b = float(np.mean(y_resampled))
    if not np.allclose(pred_val_all_k_b[:, -1], fit_mean_b, atol=1e-6):
        raise RuntimeError(f"bootstrap sample (seed={seed}): k=n_fit predictions are not all equal to its own mean")

    return {"targets": y_resampled, "index": index_b, "fitTargetMean": round(fit_mean_b, 6)}


def _verify_float32_precision(
    sorted_val_values_f64: Any,
    targets_f32: Any,
    index_u16: Any,
    y_val: Any,
) -> None:
    """Prove -- not assume -- that reconstructing nearest-first target values
    from the float32 target array + uint16 index matrix reproduces the
    float64-computed curve to the artifact's existing 4-decimal display
    rounding (WP15 §3.2: "unless comparison proves 64-bit precision is
    required..."). Raises if it does not."""
    import numpy as np

    reconstructed = targets_f32[index_u16].astype("float64")
    r2_f64, mse_f64 = _r2_mse_curve(sorted_val_values_f64, y_val)
    r2_f32, mse_f32 = _r2_mse_curve(reconstructed, y_val)
    r2_diff = max(abs(a - b) for a, b in zip(r2_f64, r2_f32))
    mse_diff = max(abs(a - b) for a, b in zip(mse_f64, mse_f32))
    # Both r2_f64/mse_f64 and r2_f32/mse_f32 are independently rounded to
    # DISPLAY_DECIMALS places (_r2_mse_curve); comparing two independently
    # rounded values at exactly that same quantum can differ by up to one
    # full quantum from double-rounding alone, with no real precision loss.
    # A 2x margin absorbs that without hiding genuine float32 inadequacy
    # (which would show up as a difference many quanta wide, not one).
    tol = 2 * 10 ** (-DISPLAY_DECIMALS)
    if r2_diff > tol or mse_diff > tol:
        raise RuntimeError(
            f"float32 round-trip precision check failed: max |R2 diff|={r2_diff}, "
            f"max |MSE diff|={mse_diff}, tolerance={tol} (float32 is insufficient; use float64)"
        )


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> tuple[dict[str, Any], bytes]:
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    manifest = manifest or MANIFEST
    knn_cfg = manifest["knn"]
    target = knn_cfg["target"]

    cols, X_train, y_train, g_train = _outer_split(frame, manifest)
    X_fit, X_val, y_fit, y_val = _dev_split(X_train, y_train, g_train, manifest)
    n_fit, n_val = len(y_fit), len(y_val)

    scaler = StandardScaler().fit(X_fit)
    Xf = scaler.transform(X_fit)
    Xv = scaler.transform(X_val)

    index_a = _sorted_neighbor_index(Xv, Xf)  # n_val x n_fit, indices into y_fit
    index_fit_self = _sorted_neighbor_index(Xf, Xf)  # n_fit x n_fit self-inclusive, for the fit curve only

    sorted_val_values = y_fit[index_a]
    sorted_fit_values = y_fit[index_fit_self]
    val_r2, val_mse = _r2_mse_curve(sorted_val_values, y_val)
    fit_r2, fit_mse = _r2_mse_curve(sorted_fit_values, y_fit)

    cum_val = np.cumsum(sorted_val_values, axis=1)
    ks = np.arange(1, n_fit + 1)
    pred_val_all_k = cum_val / ks[None, :]
    sample_ks = sorted({k for k in (1, 5, 15, 17, 50, 200, n_fit) if k <= n_fit})
    _validate_against_sklearn(Xf, y_fit, Xv, pred_val_all_k, sample_ks=sample_ks)

    # structural endpoint check: at k=n_fit, every validation prediction must
    # equal the fitting-set mean (re-asserted independently by
    # tests/test_export_knn_explore_data.py and the notebook itself)
    fit_mean = float(np.mean(y_fit))
    if not np.allclose(pred_val_all_k[:, -1], fit_mean, atol=1e-6):
        raise RuntimeError("k=n_fit predictions are not all equal to the fitting-set mean")

    val_r2_arr = np.array(val_r2)
    validation_optimal_k = int(np.argmax(val_r2_arr)) + 1

    sample_b = _bootstrap_training_sample(X_fit, y_fit, X_val, BOOTSTRAP_SEEDS["B"])
    sample_c = _bootstrap_training_sample(X_fit, y_fit, X_val, BOOTSTRAP_SEEDS["C"])

    _verify_float32_precision(sorted_val_values, y_fit.astype("float32"), index_a.astype("uint16"), y_val)
    _verify_float32_precision(
        sample_b["targets"].astype("float64")[sample_b["index"]],
        sample_b["targets"].astype("float32"),
        sample_b["index"].astype("uint16"),
        y_val,
    )
    _verify_float32_precision(
        sample_c["targets"].astype("float64")[sample_c["index"]],
        sample_c["targets"].astype("float32"),
        sample_c["index"].astype("uint16"),
        y_val,
    )

    builder = BinaryAssetBuilder()
    builder.add("observedValidation", "float32", y_val)
    builder.add("observedFitting", "float32", y_fit)
    builder.add("fitTargetsB", "float32", sample_b["targets"])
    builder.add("fitTargetsC", "float32", sample_c["targets"])
    builder.add("neighborIndexA", "uint16", index_a)
    builder.add("neighborIndexB", "uint16", sample_b["index"])
    builder.add("neighborIndexC", "uint16", sample_c["index"])
    builder.add("curveFitR2", "float32", np.array(fit_r2))
    builder.add("curveFitMSE", "float32", np.array(fit_mse))
    builder.add("curveValR2", "float32", np.array(val_r2))
    builder.add("curveValMSE", "float32", np.array(val_mse))
    blob = builder.build()

    src = manifest["source"]
    manifest_json: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "knn-explore",
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
            "devSplit": knn_cfg["dev_split"],
            "nOuterTrain": int(len(y_train)),
            "nFit": n_fit,
            "nValidation": n_val,
        },
        "fitTargetMean": round(fit_mean, 6),
        "trainingSampleMeans": {
            "A": round(fit_mean, 6),
            "B": sample_b["fitTargetMean"],
            "C": sample_c["fitTargetMean"],
        },
        "validationOptimalK": validation_optimal_k,
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
    """Decode the binary blob back into the SAME logical arrays schema v2
    stored directly, for validation purposes (mirrors the browser loader's
    own reconstruction, interactive/src/knn-explore-data.ts)."""
    sections = manifest_json["sections"]
    observed_validation = decode_section(blob, sections["observedValidation"])
    observed_fitting = decode_section(blob, sections["observedFitting"])
    fit_targets_b = decode_section(blob, sections["fitTargetsB"])
    fit_targets_c = decode_section(blob, sections["fitTargetsC"])
    index_a = decode_section(blob, sections["neighborIndexA"])
    index_b = decode_section(blob, sections["neighborIndexB"])
    index_c = decode_section(blob, sections["neighborIndexC"])
    return {
        "observedValidation": observed_validation,
        "observedFitting": observed_fitting,
        "neighborTargetsByProximity": observed_fitting[index_a],
        "trainingSamples": {
            "A": {"neighborTargetsByProximity": observed_fitting[index_a], "fitTargetMean": manifest_json["trainingSampleMeans"]["A"]},
            "B": {"neighborTargetsByProximity": fit_targets_b[index_b], "fitTargetMean": manifest_json["trainingSampleMeans"]["B"]},
            "C": {"neighborTargetsByProximity": fit_targets_c[index_c], "fitTargetMean": manifest_json["trainingSampleMeans"]["C"]},
        },
        "curve": {
            "fitR2": decode_section(blob, sections["curveFitR2"]),
            "fitMSE": decode_section(blob, sections["curveFitMSE"]),
            "valR2": decode_section(blob, sections["curveValR2"]),
            "valMSE": decode_section(blob, sections["curveValMSE"]),
        },
    }


def validate_artifact(manifest_json: Any, blob: bytes, manifest: dict[str, Any] | None = None) -> list[str]:
    import numpy as np

    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(manifest_json, dict):
        return ["manifest is not a JSON object"]
    if manifest_json.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if manifest_json.get("activity") != "knn-explore":
        problems.append("activity must be 'knn-explore'")

    src = manifest_json.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    binary_meta = manifest_json.get("binary", {})
    if binary_meta.get("byteLength") != len(blob):
        problems.append(f"binary.byteLength {binary_meta.get('byteLength')} != actual {len(blob)}")
    if binary_meta.get("sha256") != sha256_hex(blob):
        problems.append("binary.sha256 does not match the actual binary file")

    sections = manifest_json.get("sections", {})
    required_sections = {
        "observedValidation", "observedFitting", "fitTargetsB", "fitTargetsC",
        "neighborIndexA", "neighborIndexB", "neighborIndexC",
        "curveFitR2", "curveFitMSE", "curveValR2", "curveValMSE",
    }
    if set(sections) != required_sections:
        problems.append(f"sections keys {set(sections)} != required {required_sections}")
        return problems  # everything below assumes the sections exist
    for name, sec in sections.items():
        end = sec["byteOffset"] + sec["byteLength"]
        if end > len(blob):
            problems.append(f"section {name!r} extends past the end of the binary file")
        if sec["byteOffset"] % 4 != 0:
            problems.append(f"section {name!r} byteOffset {sec['byteOffset']} is not 4-byte aligned")

    split = manifest_json.get("split", {})
    n_fit, n_val = split.get("nFit"), split.get("nValidation")
    if not isinstance(n_fit, int) or not isinstance(n_val, int):
        return problems + ["split.nFit / split.nValidation must be integers"]

    if sections["observedValidation"]["shape"] != [n_val]:
        problems.append("observedValidation shape must be [nValidation]")
    if sections["observedFitting"]["shape"] != [n_fit]:
        problems.append("observedFitting shape must be [nFit]")
    for label in ("A", "B", "C"):
        key = f"neighborIndex{label}"
        if sections[key]["shape"] != [n_val, n_fit]:
            problems.append(f"{key} shape must be [nValidation, nFit]")
    for label in ("B", "C"):
        key = f"fitTargets{label}"
        if sections[key]["shape"] != [n_fit]:
            problems.append(f"{key} shape must be [nFit]")
    for key in ("curveFitR2", "curveFitMSE", "curveValR2", "curveValMSE"):
        if sections[key]["shape"] != [n_fit]:
            problems.append(f"{key} shape must be [nFit]")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in manifest_json.keys():
        if key.lower() in identifier_token:
            problems.append(f"manifest has an identifier-shaped key: {key!r}")

    # Any shape/offset/length problem already recorded above means decoding
    # below could raise (e.g. a reshape failure) rather than produce a
    # comparable array; report that as one more problem instead of crashing.
    try:
        # index bounds: every index must be a valid row into its own target array
        idx_a = decode_section(blob, sections["neighborIndexA"])
        idx_b = decode_section(blob, sections["neighborIndexB"])
        idx_c = decode_section(blob, sections["neighborIndexC"])
        if idx_a.size and (int(idx_a.min()) < 0 or int(idx_a.max()) >= n_fit):
            problems.append("neighborIndexA has an out-of-range index")
        if idx_b.size and (int(idx_b.min()) < 0 or int(idx_b.max()) >= n_fit):
            problems.append("neighborIndexB has an out-of-range index")
        if idx_c.size and (int(idx_c.min()) < 0 or int(idx_c.max()) >= n_fit):
            problems.append("neighborIndexC has an out-of-range index")

        # k=1 / k=n_fit structural endpoints, and A == baseline, via reconstruction
        logical = _reconstruct_logical(manifest_json, blob)
    except (ValueError, KeyError, IndexError) as exc:
        problems.append(f"could not decode/reconstruct sections: {exc}")
        return problems
    fit_r2 = logical["curve"]["fitR2"]
    if len(fit_r2) and abs(float(fit_r2[0]) - 1.0) > 1e-3:
        problems.append("curve.fitR2 at k=1 must be (numerically) 1.0 -- perfect resubstitution")
    if len(fit_r2) and abs(float(fit_r2[-1])) > 1e-2:
        problems.append("curve.fitR2 at k=n_fit must be (numerically) ~0.0 -- the constant-mean predictor")

    for label in ("A", "B", "C"):
        rows = logical["trainingSamples"][label]["neighborTargetsByProximity"]
        mean = logical["trainingSamples"][label]["fitTargetMean"]
        if rows.shape[0]:
            preds_at_k_nfit = rows.mean(axis=1)  # k=n_fit prediction = mean over ALL n_fit neighbours
            if not np.allclose(preds_at_k_nfit, mean, atol=1e-2):
                problems.append(f"trainingSamples.{label}: k=n_fit prediction does not match its fitTargetMean")

    if not np.array_equal(logical["trainingSamples"]["A"]["neighborTargetsByProximity"], logical["neighborTargetsByProximity"]):
        problems.append("trainingSamples.A must reconstruct to the same values as the top-level baseline")

    vok = manifest_json.get("validationOptimalK")
    val_r2 = logical["curve"]["valR2"]
    if isinstance(vok, int) and len(val_r2):
        best = float(np.max(val_r2))
        if abs(float(val_r2[vok - 1]) - best) > 1e-4:
            problems.append("validationOptimalK does not point at the argmax of curve.valR2")

    return problems


def serialize_manifest(manifest_json: dict[str, Any]) -> str:
    return json.dumps(manifest_json, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def _summary(manifest_json: dict[str, Any]) -> str:
    s = manifest_json["split"]
    b = manifest_json["binary"]
    return (
        f"activity            : {manifest_json['activity']}\n"
        f"feature recipe      : {manifest_json['featureRecipe']['bundle']} x "
        f"{'+'.join(manifest_json['featureRecipe']['measures'])} (p={manifest_json['featureRecipe']['featureCount']})\n"
        f"n_outer_train       : {s['nOuterTrain']}   n_fit : {s['nFit']}   n_val : {s['nValidation']}\n"
        f"fitting-set mean    : {manifest_json['fitTargetMean']}\n"
        f"validation-optimal k: {manifest_json['validationOptimalK']}\n"
        f"audit-selected k    : {manifest_json['selectedKFromAudit']}\n"
        f"binary payload      : {b['byteLength']} bytes  sha256={b['sha256']}"
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
