#!/usr/bin/env python3
"""Deterministically export the Exercise 5 "Shrink the Coefficients" activity data.

The browser activity ``regularization-explore`` (book/_static/widgets/) lets a
student choose Linear Regression, Ridge, or Lasso and move a regularization
strength (alpha) control, and see how the fitted model's predictions,
coefficients, and train/validation error change. Re-implementing
scikit-learn's ``Ridge``/``Lasso`` fitting in JavaScript would be fragile, so
this script pre-computes, once and deterministically, every (model, alpha)
configuration the widget can show, and the browser only switches between them.

Output: ``book/_static/widgets/data/regularization_explore.json``.

Recipe: the same p=360 ``all-eligible x CT`` predictors Exercises 2 and 4 use
(``book/config/abide_modeling.json`` -> ``regularization.canonical_recipe``),
split with the identical outer holdout (``protocol.holdout_split``) and then
the identical dev split (``regularization.dev_split``, same as
``knn.dev_split``) into a fitting subset (n_fit=564) and a validation subset
(n_val=189). ``StandardScaler`` is fit on the fitting subset only. The outer
TEST partition (251 rows) never appears in this artifact at all -- the
activity only ever shows training/validation numbers, matching this course's
"no test results in the tuning playground" rule (Exercise 4 section 5, reused
here).

Alpha grids (``regularization.ridge_alpha_grid`` / ``lasso_alpha_grid`` in the
manifest, audited in ``scripts/regularization_model_audit.py``):
``np.logspace(-1, 5, 25)`` (ridge), ``np.logspace(-3, 1, 25)`` (lasso).

Coefficient display: rather than attempting to label all 360 predictors, the
artifact tracks a small fixed set of features -- the union of the 12
largest-magnitude standardized coefficients at Ridge's own best-validation
alpha and at Lasso's own best-validation alpha -- and reports each tracked
feature's coefficient at every alpha in both grids (and its one unregularized
value), so the same bars can be compared, growing or shrinking, as alpha or
model changes. This is a display choice, stated as such in the activity's own
config text, not a second feature-selection step.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute
  every configuration, validate, and write.
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
    feature_matrix,
    load_modeling_frame,
    sha256_hex,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "regularization_explore.json"
SCHEMA_VERSION = 1
PRED_DECIMALS = 3
COEF_DECIMALS = 4
N_TRACKED_PER_MODEL = 12

REG = MANIFEST["regularization"]
RECIPE = REG["canonical_recipe"]
HOLDOUT_SPLIT = MANIFEST["protocol"]["holdout_split"]
DEV_SPLIT = REG["dev_split"]


def _ridge_alphas() -> list[float]:
    import numpy as np

    return [float(a) for a in np.logspace(-1, 5, 25)]


def _lasso_alphas() -> list[float]:
    import numpy as np

    return [float(a) for a in np.logspace(-3, 1, 25)]


def build_artifact(frame: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.linear_model import Lasso, LinearRegression, Ridge
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    cols = bundle_columns(RECIPE["bundle"], RECIPE["measures"], available=frame.columns)
    assert_brain_only(cols)
    X, y, _ = feature_matrix(frame, RECIPE["bundle"], RECIPE["measures"], REG["target"])
    groups = frame.loc[frame[REG["target"]].notna(), "group"].to_numpy()

    X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
        X, y, groups, test_size=HOLDOUT_SPLIT["test_size"], random_state=HOLDOUT_SPLIT["random_state"], stratify=groups
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=DEV_SPLIT["test_size"], random_state=DEV_SPLIT["random_state"], stratify=groups_train
    )

    scaler = StandardScaler().fit(X_fit)
    Xf, Xv = scaler.transform(X_fit), scaler.transform(X_val)

    def _metrics(m: Any) -> dict[str, Any]:
        pred_fit, pred_val = m.predict(Xf), m.predict(Xv)
        return {
            "trainMSE": round(float(mean_squared_error(y_fit, pred_fit)), 4),
            "valMSE": round(float(mean_squared_error(y_val, pred_val)), 4),
            "trainR2": round(float(r2_score(y_fit, pred_fit)), 6),
            "valR2": round(float(r2_score(y_val, pred_val)), 6),
            "nonzeroCount": int(np.sum(np.abs(m.coef_) > 1e-10)),
            "coefNorm": round(float(np.linalg.norm(m.coef_)), 4),
            "predictedValidation": [round(float(v), PRED_DECIMALS) for v in pred_val],
        }

    linear = LinearRegression().fit(Xf, y_fit)

    ridge_alphas = _ridge_alphas()
    lasso_alphas = _lasso_alphas()
    ridge_models = [Ridge(alpha=a).fit(Xf, y_fit) for a in ridge_alphas]
    lasso_models = [Lasso(alpha=a, max_iter=20000, tol=1e-3).fit(Xf, y_fit) for a in lasso_alphas]

    ridge_val_mse = [mean_squared_error(y_val, m.predict(Xv)) for m in ridge_models]
    lasso_val_mse = [mean_squared_error(y_val, m.predict(Xv)) for m in lasso_models]
    ridge_best_i = int(np.argmin(ridge_val_mse))
    lasso_best_i = int(np.argmin(lasso_val_mse))

    top_ridge = set(np.argsort(-np.abs(ridge_models[ridge_best_i].coef_))[:N_TRACKED_PER_MODEL].tolist())
    top_lasso = set(np.argsort(-np.abs(lasso_models[lasso_best_i].coef_))[:N_TRACKED_PER_MODEL].tolist())
    tracked_idx = sorted(top_ridge | top_lasso)
    tracked_features = [cols[j] for j in tracked_idx]

    def _tracked_coefs(m: Any) -> list[float]:
        return [round(float(m.coef_[j]), COEF_DECIMALS) for j in tracked_idx]

    linear_entry = {**_metrics(linear), "coefficients": _tracked_coefs(linear)}
    ridge_entry = {
        "alphaGrid": ridge_alphas,
        "bestAlphaIndex": ridge_best_i,
        "perAlpha": [
            {**_metrics(m), "coefficients": _tracked_coefs(m)} for m in ridge_models
        ],
    }
    lasso_entry = {
        "alphaGrid": lasso_alphas,
        "bestAlphaIndex": lasso_best_i,
        "perAlpha": [
            {**_metrics(m), "coefficients": _tracked_coefs(m)} for m in lasso_models
        ],
    }

    src = MANIFEST["source"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "regularization-explore",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
            "phenotypeTableSha256": src["phenotype_table"]["sha256"],
        },
        "target": {
            "name": REG["target"],
            "label": MANIFEST["targets"][REG["target"]]["label"],
            "unit": MANIFEST["targets"][REG["target"]]["unit"],
        },
        "featureRecipe": {
            "bundle": RECIPE["bundle"],
            "measures": RECIPE["measures"],
            "featureCount": len(cols),
        },
        "split": {
            "outerHoldout": {
                "testSize": HOLDOUT_SPLIT["test_size"],
                "randomState": HOLDOUT_SPLIT["random_state"],
                "stratify": HOLDOUT_SPLIT["stratify"],
                "nTrain": int(len(y_train)),
                "nTest": int(len(y_test)),
            },
            "devSplit": {
                "testSize": DEV_SPLIT["test_size"],
                "randomState": DEV_SPLIT["random_state"],
                "stratify": DEV_SPLIT["stratify"],
                "nFit": int(len(y_fit)),
                "nVal": int(len(y_val)),
            },
        },
        "observedFitting": [round(float(v), PRED_DECIMALS) for v in y_fit],
        "observedValidation": [round(float(v), PRED_DECIMALS) for v in y_val],
        "trackedFeatures": tracked_features,
        "models": {
            "linear": linear_entry,
            "ridge": ridge_entry,
            "lasso": lasso_entry,
        },
    }


def validate_artifact(artifact: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "regularization-explore":
        problems.append("activity must be 'regularization-explore'")

    src = artifact.get("source", {})
    if src.get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")

    n_val = artifact.get("split", {}).get("devSplit", {}).get("nVal")
    observed_val = artifact.get("observedValidation")
    if not isinstance(observed_val, list) or len(observed_val) != n_val:
        problems.append("observedValidation length must equal split.devSplit.nVal")

    tracked = artifact.get("trackedFeatures", [])
    if not tracked:
        problems.append("trackedFeatures must be non-empty")

    models = artifact.get("models", {})
    lin = models.get("linear", {})
    if len(lin.get("coefficients", [])) != len(tracked):
        problems.append("models.linear.coefficients must align with trackedFeatures")
    if len(lin.get("predictedValidation", [])) != n_val:
        problems.append("models.linear.predictedValidation must align with observedValidation")

    for family in ("ridge", "lasso"):
        entry = models.get(family, {})
        alphas = entry.get("alphaGrid", [])
        per_alpha = entry.get("perAlpha", [])
        if len(alphas) != len(per_alpha) or not alphas:
            problems.append(f"models.{family}: alphaGrid/perAlpha length mismatch")
            continue
        best_i = entry.get("bestAlphaIndex")
        if best_i in (0, len(alphas) - 1):
            problems.append(f"models.{family}: best validation alpha sits at a grid boundary (index {best_i})")
        for i, pa in enumerate(per_alpha):
            if len(pa.get("coefficients", [])) != len(tracked):
                problems.append(f"models.{family}.perAlpha[{i}].coefficients must align with trackedFeatures")
            if len(pa.get("predictedValidation", [])) != n_val:
                problems.append(f"models.{family}.perAlpha[{i}].predictedValidation must align with observedValidation")

    if models.get("ridge", {}).get("perAlpha", [{}])[0].get("valMSE") is not None:
        ridge_best = min(pa["valMSE"] for pa in models["ridge"]["perAlpha"])
        lin_val = lin.get("valMSE")
        if lin_val is not None and ridge_best >= lin_val:
            problems.append("ridge's best validation MSE should improve on the unregularised linear baseline here")

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
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
    raw_bytes = len(text.encode("utf-8"))
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({raw_bytes} bytes)")
    print(f"artifact sha256: {sha256_hex(text.encode('utf-8'))}")
    print(f"tracked features: {len(artifact['trackedFeatures'])}")
    for family in ("linear", "ridge", "lasso"):
        m = artifact["models"][family]
        if family == "linear":
            print(f"  linear  valMSE={m['valMSE']:.1f}")
        else:
            best = m["perAlpha"][m["bestAlphaIndex"]]
            print(f"  {family:6s}  best alpha={m['alphaGrid'][m['bestAlphaIndex']]:.4g}  valMSE={best['valMSE']:.1f}  nnz={best['nonzeroCount']}")
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
