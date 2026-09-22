#!/usr/bin/env python3
"""Deterministic synthetic 2-D regression dataset for Exercise 9's
"PCR or PLS?" activity (WP34).

The dataset is entirely synthetic -- 60 observations on two continuous,
standardized, correlated features (``advanced_models.pcr_pls_activity`` in
``book/config/abide_modeling.json``). In their own PCA space, PC1 (the
higher-variance direction) explains 85% of the two features' variance and
PC2 (the lower-variance direction) explains 15%. The target is a fixed
linear combination of the PC1 and PC2 scores plus Gaussian noise; only the
two coefficients (``beta_pc1``, ``beta_pc2``) change across the three
presets ("weak"/"moderate"/"strong" alignment with the lower-variance
direction) -- the predictor cloud and the 40/20 train/validation split stay
fixed throughout.

For every (method, n_components, preset) combination, this script fits
scikit-learn's PCR (``StandardScaler`` -> ``PCA`` -> ``LinearRegression``)
or PLS (``StandardScaler`` -> ``PLSRegression(scale=False)``) pipeline on
the fixed training rows only and evaluates on the fixed validation rows;
nothing is fit live in the browser.

Usage::

    python scripts/export_pcr_pls_widget.py --refresh   # writes JSON
    python scripts/export_pcr_pls_widget.py --check     # re-validate

Asserted by ``tests/test_export_pcr_pls_widget_data.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "pcr_pls_explore.json"
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "abide_modeling.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from semantic_json_compare import DEFAULT_ABS_TOL, semantic_diff  # noqa: E402

_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
_CFG = _MANIFEST["advanced_models"]["pcr_pls_activity"]

N_OBSERVATIONS: int = _CFG["n_observations"]
N_TRAIN: int = _CFG["n_train"]
SEED: int = _CFG["seed"]
RHO: float = _CFG["rho"]
NOISE_SD: float = _CFG["noise_sd"]
COMPONENT_GRID: list[int] = _CFG["component_grid"]
PRESETS: dict[str, dict[str, Any]] = _CFG["presets"]
PRESET_KEYS: list[str] = sorted(PRESETS.keys())
METHODS = ("pcr", "pls")


def _generate_points() -> Any:
    import numpy as np

    rng = np.random.RandomState(SEED)
    cov = [[1.0, RHO], [RHO, 1.0]]
    pts = rng.multivariate_normal([0.0, 0.0], cov, size=N_OBSERVATIONS)
    return pts


def _pc_scores(pts: Any) -> tuple[Any, Any, Any]:
    """PC1/PC2 scores + the two unit directions, in closed form (rho fixed,
    equal marginal variances) -- PC1 = (1,1)/sqrt(2), PC2 = (1,-1)/sqrt(2)."""
    import numpy as np

    u1 = np.array([1.0, 1.0]) / np.sqrt(2.0)
    u2 = np.array([1.0, -1.0]) / np.sqrt(2.0)
    pc1 = pts @ u1
    pc2 = pts @ u2
    return pc1, pc2, np.stack([u1, u2])


def _targets_for_preset(pc1: Any, pc2: Any, preset: str, noise_rng: Any) -> Any:
    p = PRESETS[preset]
    signal = p["beta_pc1"] * pc1 + p["beta_pc2"] * pc2
    noise = noise_rng.normal(0.0, NOISE_SD, size=len(pc1))
    return signal + noise


def _train_val_indices() -> tuple[list[int], list[int]]:
    import numpy as np

    rng = np.random.RandomState(SEED + 1)
    perm = rng.permutation(N_OBSERVATIONS)
    train_idx = sorted(perm[:N_TRAIN].tolist())
    val_idx = sorted(perm[N_TRAIN:].tolist())
    return train_idx, val_idx


def _fit_pcr(X_tr: Any, y_tr: Any, n_components: int) -> tuple[Any, Any]:
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    pipe = Pipeline(
        [("scale", StandardScaler()), ("pca", PCA(n_components=n_components, random_state=0)), ("model", LinearRegression())]
    ).fit(X_tr, y_tr)
    scaler: Any = pipe.named_steps["scale"]
    pca: Any = pipe.named_steps["pca"]
    direction = pca.components_[0] / scaler.scale_
    direction = direction / (direction**2).sum() ** 0.5
    return pipe, direction


def _fit_pls(X_tr: Any, y_tr: Any, n_components: int) -> tuple[Any, Any]:
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    pipe = Pipeline(
        [("scale", StandardScaler()), ("pls", PLSRegression(n_components=n_components, scale=False))]
    ).fit(X_tr, y_tr)
    scaler: Any = pipe.named_steps["scale"]
    pls: Any = pipe.named_steps["pls"]
    direction = pls.x_weights_[:, 0] / scaler.scale_
    direction = direction / (direction**2).sum() ** 0.5
    return pipe, direction


def _catalog_key(method: str, n_components: int, preset: str) -> str:
    return f"{method}|{n_components}|{preset}"


def build_data() -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import mean_squared_error

    pts = _generate_points()
    pc1, pc2, directions = _pc_scores(pts)
    train_idx, val_idx = _train_val_indices()
    X = pts

    noise_rng = np.random.RandomState(SEED + 2)
    targets: dict[str, list[float]] = {}
    for preset in PRESET_KEYS:
        y = _targets_for_preset(pc1, pc2, preset, noise_rng)
        targets[preset] = [round(float(v), 4) for v in y]

    catalog: dict[str, Any] = {}
    for preset in PRESET_KEYS:
        y_full = np.array(targets[preset])
        y_tr, y_va = y_full[train_idx], y_full[val_idx]
        X_tr, X_va = X[train_idx], X[val_idx]
        for n_components in COMPONENT_GRID:
            for method in METHODS:
                if method == "pcr":
                    pipe, direction = _fit_pcr(X_tr, y_tr, n_components)
                    construction_note = (
                        "PCR's component(s) are chosen to explain the most variance in the two predictors "
                        "themselves, without ever looking at the target."
                    )
                else:
                    pipe, direction = _fit_pls(X_tr, y_tr, n_components)
                    construction_note = (
                        "PLS's component(s) are chosen using the covariance between the predictors and the "
                        "target, so a direction that predicts well can be favored even if it explains less "
                        "predictor variance."
                    )
                pred_tr = np.asarray(pipe.predict(X_tr)).reshape(-1)
                pred_va = np.asarray(pipe.predict(X_va)).reshape(-1)
                key = _catalog_key(method, n_components, preset)
                catalog[key] = {
                    "method": method,
                    "nComponents": n_components,
                    "preset": preset,
                    "firstComponentDirection": [round(float(direction[0]), 4), round(float(direction[1]), 4)],
                    "trainMse": round(float(mean_squared_error(y_tr, pred_tr)), 4),
                    "valMse": round(float(mean_squared_error(y_va, pred_va)), 4),
                    "valPredictions": [round(float(v), 4) for v in pred_va],
                    "constructionNote": construction_note,
                }

    return {
        "schemaVersion": 1,
        "activity": "pcr-pls-explore",
        "syntheticDataNote": (
            "This dataset is simulated: 60 points on two standardized, correlated predictors, drawn from a "
            "fixed distribution and seed. It is used to build intuition for how PCR and PLS construct "
            "components differently, not to reproduce a real measurement -- these are not ABIDE observations."
        ),
        "generatingProcess": {
            "nObservations": N_OBSERVATIONS,
            "nTrain": N_TRAIN,
            "nVal": N_OBSERVATIONS - N_TRAIN,
            "rho": RHO,
            "noiseSd": NOISE_SD,
            "seed": SEED,
            "seedNote": "Fixed before generation; no seed search.",
            "pc1ExplainedVarianceRatio": round((1.0 + RHO) / 2.0, 4),
            "pc2ExplainedVarianceRatio": round((1.0 - RHO) / 2.0, 4),
        },
        "featureX": {"name": "f1", "label": "Feature 1 (standardized)"},
        "featureY": {"name": "f2", "label": "Feature 2 (standardized)"},
        "points": [{"id": i, "x": round(float(p[0]), 4), "y": round(float(p[1]), 4)} for i, p in enumerate(pts)],
        "trainIds": train_idx,
        "valIds": val_idx,
        "presets": {
            key: {"label": PRESETS[key]["label"], "betaPc1": PRESETS[key]["beta_pc1"], "betaPc2": PRESETS[key]["beta_pc2"]}
            for key in PRESET_KEYS
        },
        "targets": targets,
        "methods": list(METHODS),
        "componentGrid": COMPONENT_GRID,
        "catalog": catalog,
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_refresh() -> int:
    data = build_data()
    text = serialize(data)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_summary(data)
    return 0


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    points = data.get("points", [])
    if len(points) != N_OBSERVATIONS:
        problems.append(f"points count must be exactly {N_OBSERVATIONS}")
        return problems
    if sorted(data.get("trainIds", []) + data.get("valIds", [])) != list(range(N_OBSERVATIONS)):
        problems.append("trainIds + valIds must partition every point exactly once")
    if len(data.get("trainIds", [])) != N_TRAIN:
        problems.append(f"trainIds must have exactly {N_TRAIN} entries")

    for preset in PRESET_KEYS:
        if len(data.get("targets", {}).get(preset, [])) != N_OBSERVATIONS:
            problems.append(f"targets[{preset}] must have exactly {N_OBSERVATIONS} entries")

    catalog = data.get("catalog", {})
    expected_keys = {_catalog_key(m, n, p) for m in METHODS for n in COMPONENT_GRID for p in PRESET_KEYS}
    got_keys = set(catalog.keys())
    if expected_keys != got_keys:
        missing = expected_keys - got_keys
        extra = got_keys - expected_keys
        if missing:
            problems.append(f"catalog missing {len(missing)} combination(s), e.g. {sorted(missing)[:3]}")
        if extra:
            problems.append(f"catalog has {len(extra)} unexpected combination(s), e.g. {sorted(extra)[:3]}")

    for key, entry in catalog.items():
        if len(entry.get("valPredictions", [])) != N_OBSERVATIONS - N_TRAIN:
            problems.append(f"catalog[{key}].valPredictions must have exactly {N_OBSERVATIONS - N_TRAIN} entries")
        direction = entry.get("firstComponentDirection", [])
        if len(direction) != 2:
            problems.append(f"catalog[{key}].firstComponentDirection must have exactly 2 entries")
        else:
            norm = (direction[0] ** 2 + direction[1] ** 2) ** 0.5
            if abs(norm - 1.0) > 1e-2:
                problems.append(f"catalog[{key}].firstComponentDirection must be a unit vector, got norm {norm:.4f}")
        if entry.get("trainMse", -1) < 0 or entry.get("valMse", -1) < 0:
            problems.append(f"catalog[{key}]: MSE must be non-negative")

    return problems


def cmd_check() -> int:
    if not OUT_PATH.exists():
        print(f"ERROR: {OUT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    recomputed = build_data()
    mismatch = semantic_diff(data, recomputed, abs_tol=DEFAULT_ABS_TOL)
    if mismatch is not None:
        print("ERROR: committed artifact does not match a fresh recomputation.", file=sys.stderr)
        print(f"  - {mismatch}", file=sys.stderr)
        return 1
    problems = validate(data)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {OUT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(data)
    return 0


def _print_summary(data: dict[str, Any]) -> None:
    gp = data["generatingProcess"]
    print(
        f"n={gp['nObservations']} (train={gp['nTrain']}, val={gp['nVal']})  "
        f"PC1 EVR={gp['pc1ExplainedVarianceRatio']:.2f}  PC2 EVR={gp['pc2ExplainedVarianceRatio']:.2f}"
    )
    for preset in PRESET_KEYS:
        for method in METHODS:
            e1 = data["catalog"][_catalog_key(method, 1, preset)]
            print(f"  preset={preset:9s} method={method:3s} ncomp=1  valMSE={e1['valMse']:.3f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute and write the JSON artifact")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
