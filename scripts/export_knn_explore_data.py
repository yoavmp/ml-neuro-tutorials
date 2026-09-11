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
* for every validation participant, its ``N_fit`` fitting-set target values
  **reordered by distance** (nearest first). This lets the browser recompute
  the exact observed-vs-predicted scatter for *any* chosen ``k`` with one
  client-side prefix mean, without ever seeing a brain feature, a distance, or
  a participant identifier -- only target-value floats, in neighbour order;
* (WP14 section 4.8) the same reordering for two more deterministic bootstrap
  resamples ("B", "C") of the fitting pool, alongside the original ("A"), so
  the browser can show how predictions at a fixed validation participant and
  a fixed k vary across different training-set draws -- an empirical
  training-sample-sensitivity ("variance-proxy") and systematic-smoothing
  ("bias-like-proxy") illustration, computed client-side, never touching the
  outer test set.

Both computations are validated against a real, independently-fitted
``Pipeline(StandardScaler(), KNeighborsRegressor(k))`` at representative ``k``
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

Output: ``book/_static/widgets/data/abide_knn_explore.json``.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute,
  validate, and write.
* ``--check``    (offline): re-validate the committed artifact and confirm it
  is byte-for-byte canonical.

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
    assert_brain_only,
    bundle_columns,
    load_modeling_frame,
    sha256_hex,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_knn_explore.json"
SCHEMA_VERSION = 2
DECIMALS = 4
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


def _sorted_neighbor_targets(X_query: Any, X_fit: Any, y_fit: Any):
    """For every row of X_query, the fitting-set y values sorted by ascending
    Euclidean distance (in already-scaled space). Shape (n_query, n_fit)."""
    import numpy as np

    d = np.linalg.norm(X_query[:, None, :] - X_fit[None, :, :], axis=2)
    order = np.argsort(d, axis=1, kind="stable")
    return y_fit[order]


def _r2_mse_curve(sorted_targets: Any, observed: Any) -> tuple[list[float], list[float]]:
    """Per-k R2/MSE for every k=1..n_fit, from cumulative means of
    `sorted_targets` (n_obs x n_fit, nearest-first)."""
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


def _bootstrap_training_sample(
    X_fit_raw: Any, y_fit: Any, X_val_raw: Any, seed: int
) -> dict[str, Any]:
    """One bootstrap resample (with replacement) of the fitting pool, refit
    with its own StandardScaler, and the resulting validation neighbour-target
    matrix. Independently validated against a real sklearn Pipeline."""
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

    sorted_val_b = _sorted_neighbor_targets(Xv_b, Xf_b, y_resampled)
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

    return {
        "fitTargetMean": round(fit_mean_b, 6),
        "neighborTargetsByProximity": [
            [round(float(v), DECIMALS) for v in row] for row in sorted_val_b
        ],
    }


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
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

    sorted_val = _sorted_neighbor_targets(Xv, Xf, y_fit)  # n_val x n_fit
    sorted_fit = _sorted_neighbor_targets(Xf, Xf, y_fit)  # n_fit x n_fit (self-inclusive)

    val_r2, val_mse = _r2_mse_curve(sorted_val, y_val)
    fit_r2, fit_mse = _r2_mse_curve(sorted_fit, y_fit)

    cum_val = np.cumsum(sorted_val, axis=1)
    ks = np.arange(1, n_fit + 1)
    pred_val_all_k = cum_val / ks[None, :]
    sample_ks = sorted({k for k in (1, 5, 15, 17, 50, 200, n_fit) if k <= n_fit})
    _validate_against_sklearn(Xf, y_fit, Xv, pred_val_all_k, sample_ks=sample_ks)

    # structural endpoint check: at k=n_fit, every validation prediction must
    # equal the fitting-set mean (this is asserted again, independently, by
    # tests/test_export_knn_explore_data.py and the notebook itself)
    fit_mean = float(np.mean(y_fit))
    if not np.allclose(pred_val_all_k[:, -1], fit_mean, atol=1e-6):
        raise RuntimeError("k=n_fit predictions are not all equal to the fitting-set mean")

    val_r2_arr = np.array(val_r2)
    validation_optimal_k = int(np.argmax(val_r2_arr)) + 1

    training_samples = {
        "A": {
            "fitTargetMean": round(fit_mean, 6),
            "neighborTargetsByProximity": [
                [round(float(v), DECIMALS) for v in row] for row in sorted_val
            ],
        }
    }
    for label, seed in BOOTSTRAP_SEEDS.items():
        training_samples[label] = _bootstrap_training_sample(X_fit, y_fit, X_val, seed)

    src = manifest["source"]
    return {
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
        "validationOptimalK": validation_optimal_k,
        "selectedKFromAudit": knn_cfg["selected_k"],
        "observedValidation": [round(float(v), DECIMALS) for v in y_val],
        "observedFitting": [round(float(v), DECIMALS) for v in y_fit],
        "neighborTargetsByProximity": [
            [round(float(v), DECIMALS) for v in row] for row in sorted_val
        ],
        "trainingSamples": training_samples,
        "curve": {
            "k": [int(k) for k in ks],
            "fitR2": fit_r2,
            "fitMSE": fit_mse,
            "valR2": val_r2,
            "valMSE": val_mse,
        },
    }


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "knn-explore":
        problems.append("activity must be 'knn-explore'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    split = artifact.get("split", {})
    n_fit = split.get("nFit")
    n_val = split.get("nValidation")
    if not isinstance(n_fit, int) or not isinstance(n_val, int):
        return problems + ["split.nFit / split.nValidation must be integers"]

    observed_val = artifact.get("observedValidation")
    observed_fit = artifact.get("observedFitting")
    neighbours = artifact.get("neighborTargetsByProximity")
    curve = artifact.get("curve", {})

    if not isinstance(observed_val, list) or len(observed_val) != n_val:
        problems.append("observedValidation must align with split.nValidation")
    if not isinstance(observed_fit, list) or len(observed_fit) != n_fit:
        problems.append("observedFitting must align with split.nFit")
    if not isinstance(neighbours, list) or len(neighbours) != n_val:
        problems.append("neighborTargetsByProximity must have one row per validation participant")
    else:
        for row in neighbours:
            if not isinstance(row, list) or len(row) != n_fit:
                problems.append("neighborTargetsByProximity row must have n_fit entries")
                break

    training_samples = artifact.get("trainingSamples")
    if not isinstance(training_samples, dict) or set(training_samples) != {"A", "B", "C"}:
        problems.append("trainingSamples must have exactly keys A, B, C")
    else:
        for label, sample in training_samples.items():
            rows = sample.get("neighborTargetsByProximity") if isinstance(sample, dict) else None
            if not isinstance(rows, list) or len(rows) != n_val:
                problems.append(f"trainingSamples.{label}.neighborTargetsByProximity must have one row per validation participant")
                continue
            for row in rows:
                if not isinstance(row, list) or len(row) != n_fit:
                    problems.append(f"trainingSamples.{label}.neighborTargetsByProximity row must have n_fit entries")
                    break
            fit_mean_b = sample.get("fitTargetMean") if isinstance(sample, dict) else None
            if not isinstance(fit_mean_b, (int, float)):
                problems.append(f"trainingSamples.{label}.fitTargetMean must be numeric")
            elif rows and len(rows[0]) == n_fit:
                # structural endpoint: k=n_fit predicts this sample's own mean
                k_nfit_pred = sum(rows[0]) / n_fit
                if abs(k_nfit_pred - fit_mean_b) > 1e-3:
                    problems.append(f"trainingSamples.{label}: k=n_fit prediction does not match fitTargetMean")

    if isinstance(neighbours, list) and isinstance(training_samples, dict) and isinstance(training_samples.get("A"), dict):
        if training_samples["A"].get("neighborTargetsByProximity") != neighbours:
            problems.append("trainingSamples.A.neighborTargetsByProximity must equal the top-level neighborTargetsByProximity")
        if isinstance(artifact.get("fitTargetMean"), (int, float)) and training_samples["A"].get("fitTargetMean") != artifact.get("fitTargetMean"):
            problems.append("trainingSamples.A.fitTargetMean must equal the top-level fitTargetMean")

    k_list = curve.get("k")
    if not isinstance(k_list, list) or k_list != list(range(1, n_fit + 1)):
        problems.append("curve.k must be exactly [1, 2, ..., n_fit]")
    for key in ("fitR2", "fitMSE", "valR2", "valMSE"):
        vals = curve.get(key)
        if not isinstance(vals, list) or len(vals) != n_fit:
            problems.append(f"curve.{key} must have n_fit entries")

    # endpoint checks
    if isinstance(k_list, list) and k_list and observed_fit and isinstance(curve.get("fitR2"), list):
        if abs(curve["fitR2"][0] - 1.0) > 1e-6:
            problems.append("curve.fitR2 at k=1 must be (numerically) 1.0 -- perfect resubstitution")
        fit_mean = artifact.get("fitTargetMean")
        if fit_mean is not None and abs(curve["fitR2"][-1]) > 1e-3:
            problems.append("curve.fitR2 at k=n_fit must be (numerically) ~0.0 -- the constant-mean predictor")

    identifier_token = ("id", "sub", "subject", "site", "participant")
    for key in artifact.keys():
        if key.lower() in identifier_token:
            problems.append(f"artifact has an identifier-shaped key: {key!r}")

    vok = artifact.get("validationOptimalK")
    if isinstance(vok, int) and isinstance(curve.get("valR2"), list):
        best_val_r2 = max(curve["valR2"])
        if abs(curve["valR2"][vok - 1] - best_val_r2) > 1e-9:
            problems.append("validationOptimalK does not point at the argmax of curve.valR2")

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def _summary(artifact: dict[str, Any]) -> str:
    s = artifact["split"]
    return (
        f"activity            : {artifact['activity']}\n"
        f"feature recipe      : {artifact['featureRecipe']['bundle']} x "
        f"{'+'.join(artifact['featureRecipe']['measures'])} (p={artifact['featureRecipe']['featureCount']})\n"
        f"n_outer_train       : {s['nOuterTrain']}   n_fit : {s['nFit']}   n_val : {s['nValidation']}\n"
        f"fitting-set mean    : {artifact['fitTargetMean']}\n"
        f"validation-optimal k: {artifact['validationOptimalK']} "
        f"(valR2={artifact['curve']['valR2'][artifact['validationOptimalK'] - 1]})\n"
        f"audit-selected k    : {artifact['selectedKFromAudit']} "
        f"(valR2={artifact['curve']['valR2'][artifact['selectedKFromAudit'] - 1]})\n"
        f"k=1   fitR2={artifact['curve']['fitR2'][0]}  valR2={artifact['curve']['valR2'][0]}\n"
        f"k=n_fit fitR2={artifact['curve']['fitR2'][-1]}  valR2={artifact['curve']['valR2'][-1]}"
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
