#!/usr/bin/env python3
"""Deterministic synthetic 2-D classification datasets for Exercise 9's
"Explore an SVM Boundary" activity (WP34).

Two entirely synthetic, fixed-split, two-dimensional binary-classification
datasets (``advanced_models.svm_activity`` in
``book/config/abide_modeling.json``) -- never ABIDE observations -- one
approximately linearly separable (two Gaussian blobs) and one not (an inner
class surrounded by an outer ring plus noise). For every (dataset, kernel,
C, gamma) combination in the declared bounded grid, ``sklearn.svm.SVC`` is
fit once on the fixed training rows; support vectors, training/validation
accuracy, and a fixed decision-grid mesh (for a smooth but compact Plotly
contour) are all precomputed here. Nothing is fit live in the browser.

Usage::

    python scripts/export_svm_explorer_widget.py --refresh   # writes JSON
    python scripts/export_svm_explorer_widget.py --check     # re-validate

Asserted by ``tests/test_export_svm_explorer_widget_data.py``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "svm_explorer.json"
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "abide_modeling.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from semantic_json_compare import DEFAULT_ABS_TOL, semantic_diff  # noqa: E402

_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
_CFG = _MANIFEST["advanced_models"]["svm_activity"]

N_OBSERVATIONS: int = _CFG["n_observations"]
N_TRAIN: int = _CFG["n_train"]
SEED: int = _CFG["seed"]
KERNELS: list[str] = _CFG["kernel_options"]
POLY_DEGREE: int = _CFG["poly_degree"]
C_GRID: list[float] = _CFG["c_grid"]
GAMMA_GRID: list[float] = _CFG["gamma_grid"]
GRID_RES: int = _CFG["decision_grid_resolution"]
DATASETS = ("linear", "nonlinear")


def _generate_linear(rng: Any) -> tuple[Any, Any]:
    import numpy as np

    n_per_class = N_OBSERVATIONS // 2
    class0 = rng.normal(loc=[-1.5, -1.5], scale=1.0, size=(n_per_class, 2))
    class1 = rng.normal(loc=[1.5, 1.5], scale=1.0, size=(N_OBSERVATIONS - n_per_class, 2))
    X = np.vstack([class0, class1])
    y = np.array([0] * n_per_class + [1] * (N_OBSERVATIONS - n_per_class))
    return X, y


def _generate_nonlinear(rng: Any) -> tuple[Any, Any]:
    import numpy as np

    n_per_class = N_OBSERVATIONS // 2
    # Inner class: a blob near the origin, noisy enough to overlap the ring's
    # inner edge a little -- an easy setting is still perfectly separable,
    # but an overly aggressive (very large C / very large RBF gamma) setting
    # visibly overfits a few near-boundary points instead of generalizing.
    inner = rng.normal(loc=[0.0, 0.0], scale=0.9, size=(n_per_class, 2))
    # Outer class: a noisy ring around the inner blob.
    angles = np.linspace(0, 2 * np.pi, N_OBSERVATIONS - n_per_class, endpoint=False)
    radius = 2.6 + rng.normal(0.0, 0.45, size=len(angles))
    outer = np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)
    outer = outer + rng.normal(0.0, 0.25, size=outer.shape)
    X = np.vstack([inner, outer])
    y = np.array([0] * n_per_class + [1] * (N_OBSERVATIONS - n_per_class))
    # A handful of deterministic label flips near the boundary give very
    # high C / very large gamma something concrete to overfit -- a stable
    # pedagogical property of this fixed dataset, not something recomputed
    # per control choice.
    order = np.argsort(np.abs(np.linalg.norm(X, axis=1) - 2.0))
    flip_ids = order[:4]
    y[flip_ids] = 1 - y[flip_ids]
    return X, y


def _generate(dataset: str, seed_offset: int) -> tuple[Any, Any]:
    import numpy as np

    rng = np.random.RandomState(SEED + seed_offset)
    if dataset == "linear":
        return _generate_linear(rng)
    return _generate_nonlinear(rng)


def _train_val_indices(n: int, y: Any, seed_offset: int) -> tuple[list[int], list[int]]:
    import numpy as np

    rng = np.random.RandomState(SEED + 100 + seed_offset)
    idx0 = [i for i in range(n) if y[i] == 0]
    idx1 = [i for i in range(n) if y[i] == 1]
    rng.shuffle(idx0)
    rng.shuffle(idx1)
    n_train_per_class = N_TRAIN // 2
    train = sorted(idx0[:n_train_per_class] + idx1[:n_train_per_class])
    val = sorted(idx0[n_train_per_class:] + idx1[n_train_per_class:])
    return train, val


def _decision_grid_bounds(X: Any, pad_frac: float = 0.2) -> tuple[float, float, float, float]:
    import numpy as np

    x_min, x_max = float(np.min(X[:, 0])), float(np.max(X[:, 0]))
    y_min, y_max = float(np.min(X[:, 1])), float(np.max(X[:, 1]))
    x_pad = (x_max - x_min) * pad_frac
    y_pad = (y_max - y_min) * pad_frac
    return x_min - x_pad, x_max + x_pad, y_min - y_pad, y_max + y_pad


def _combo_key(dataset: str, kernel: str, c: float, gamma: Any) -> str:
    gamma_part = "na" if kernel == "linear" else str(gamma)
    return f"{dataset}|{kernel}|{c}|{gamma_part}"


def build_data() -> dict[str, Any]:
    import warnings

    import numpy as np
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    convergence_warnings: list[str] = []
    datasets: dict[str, Any] = {}
    for i, dataset in enumerate(DATASETS):
        X, y = _generate(dataset, i)
        train_idx, val_idx = _train_val_indices(len(y), y, i)
        x_min, x_max, y_min, y_max = _decision_grid_bounds(X)
        xs = np.linspace(x_min, x_max, GRID_RES)
        ys = np.linspace(y_min, y_max, GRID_RES)
        datasets[dataset] = {
            "points": [{"id": j, "x": round(float(p[0]), 4), "y": round(float(p[1]), 4), "label": int(y[j])} for j, p in enumerate(X)],
            "trainIds": train_idx,
            "valIds": val_idx,
            "gridX": [round(float(v), 4) for v in xs],
            "gridY": [round(float(v), 4) for v in ys],
        }

        catalog: dict[str, Any] = {}
        # SVC is fit on STANDARDIZED coordinates (scaling is a requirement for
        # a margin-based model); gridX/gridY/points above stay in the
        # original, easy-to-read coordinate space for plotting, and the
        # scaler transforms the mesh before every prediction.
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va, y_va = X[val_idx], y[val_idx]
        mesh_x, mesh_y = np.meshgrid(xs, ys)
        mesh_points = np.column_stack([mesh_x.ravel(), mesh_y.ravel()])

        for kernel in KERNELS:
            gammas: list[Any] = [None] if kernel == "linear" else GAMMA_GRID
            for c in C_GRID:
                for gamma in gammas:
                    kwargs: dict[str, Any] = {"kernel": kernel, "C": c}
                    if kernel == "poly":
                        kwargs["degree"] = POLY_DEGREE
                    if gamma is not None:
                        kwargs["gamma"] = gamma
                    pipe = Pipeline([("scale", StandardScaler()), ("svc", SVC(**kwargs))])
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always", ConvergenceWarning)
                        pipe.fit(X_tr, y_tr)
                        for w in caught:
                            if issubclass(w.category, ConvergenceWarning):
                                convergence_warnings.append(f"{dataset}/{kernel}/C={c}/gamma={gamma}: {w.message}")
                    clf = pipe.named_steps["svc"]
                    train_acc = float(pipe.score(X_tr, y_tr))
                    val_acc = float(pipe.score(X_va, y_va))
                    grid_pred = pipe.predict(mesh_points).reshape(mesh_x.shape).astype(int)
                    support_indices = [int(train_idx[i]) for i in clf.support_.tolist()]
                    key = _combo_key(dataset, kernel, c, gamma)
                    # decisionGrid values are always 0/1 class labels; a
                    # digit-string per row (never removing a resolution cell)
                    # avoids the JSON pretty-printer's one-line-per-number
                    # blow-up a plain nested-array-of-ints encoding would get.
                    catalog[key] = {
                        "dataset": dataset,
                        "kernel": kernel,
                        "c": c,
                        "gamma": gamma,
                        "trainAccuracy": round(train_acc, 4),
                        "valAccuracy": round(val_acc, 4),
                        "nSupportVectors": int(len(support_indices)),
                        "supportVectorIds": support_indices,
                        "decisionGrid": ["".join(str(v) for v in row) for row in grid_pred.tolist()],
                    }
        datasets[dataset]["catalog"] = catalog

    if convergence_warnings:
        print("CONVERGENCE WARNINGS (recorded, not silently discarded):", file=sys.stderr)
        for w in convergence_warnings:
            print(f"  - {w}", file=sys.stderr)

    return {
        "schemaVersion": 1,
        "activity": "svm-explorer",
        "syntheticDataNote": (
            "Both datasets are simulated: fixed, seeded two-dimensional points with a binary label, used to "
            "build intuition for margins, support vectors, and kernel boundaries -- these are not ABIDE "
            "observations."
        ),
        "kernelOptions": KERNELS,
        "polyDegree": POLY_DEGREE,
        "cGrid": C_GRID,
        "gammaGrid": GAMMA_GRID,
        "datasets": datasets,
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_refresh() -> int:
    data = build_data()
    text = serialize(data)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    raw_bytes = text.encode("utf-8")
    gz_bytes = gzip.compress(raw_bytes, compresslevel=9)
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    print(f"  uncompressed: {len(raw_bytes)} bytes ({len(raw_bytes) / 1024:.1f} KiB)")
    print(f"  gzip -9:      {len(gz_bytes)} bytes ({len(gz_bytes) / 1024:.1f} KiB)")
    _print_summary(data)
    return 0


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for dataset in DATASETS:
        d = data.get("datasets", {}).get(dataset)
        if d is None:
            problems.append(f"datasets.{dataset} missing")
            continue
        points = d.get("points", [])
        if len(points) != N_OBSERVATIONS:
            problems.append(f"datasets.{dataset}.points must have exactly {N_OBSERVATIONS} entries")
        if sorted(d.get("trainIds", []) + d.get("valIds", [])) != list(range(N_OBSERVATIONS)):
            problems.append(f"datasets.{dataset}: trainIds + valIds must partition every point exactly once")
        if len(d.get("gridX", [])) != GRID_RES or len(d.get("gridY", [])) != GRID_RES:
            problems.append(f"datasets.{dataset}: gridX/gridY must have exactly {GRID_RES} entries")

        catalog = d.get("catalog", {})
        expected_keys = set()
        for kernel in KERNELS:
            gammas = [None] if kernel == "linear" else GAMMA_GRID
            for c in C_GRID:
                for gamma in gammas:
                    expected_keys.add(_combo_key(dataset, kernel, c, gamma))
        got_keys = set(catalog.keys())
        if expected_keys != got_keys:
            missing = expected_keys - got_keys
            extra = got_keys - expected_keys
            if missing:
                problems.append(f"datasets.{dataset}.catalog missing {len(missing)}, e.g. {sorted(missing)[:3]}")
            if extra:
                problems.append(f"datasets.{dataset}.catalog has {len(extra)} extra, e.g. {sorted(extra)[:3]}")

        for key, entry in catalog.items():
            sv_ids = entry.get("supportVectorIds", [])
            if entry.get("nSupportVectors") != len(sv_ids):
                problems.append(f"datasets.{dataset}.catalog[{key}]: nSupportVectors does not match supportVectorIds length")
            train_id_set = set(d.get("trainIds", []))
            if not set(sv_ids).issubset(train_id_set):
                problems.append(f"datasets.{dataset}.catalog[{key}]: support vectors must come only from training rows")
            grid = entry.get("decisionGrid", [])
            if len(grid) != GRID_RES or any(len(row) != GRID_RES for row in grid):
                problems.append(f"datasets.{dataset}.catalog[{key}]: decisionGrid must be {GRID_RES} rows of {GRID_RES} chars")
            elif any(ch not in "01" for row in grid for ch in row):
                problems.append(f"datasets.{dataset}.catalog[{key}]: decisionGrid rows must contain only '0'/'1' characters")
            for acc_key in ("trainAccuracy", "valAccuracy"):
                v = entry.get(acc_key)
                if v is None or not (0.0 <= v <= 1.0):
                    problems.append(f"datasets.{dataset}.catalog[{key}].{acc_key} must be in [0, 1]")

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
    for dataset in DATASETS:
        d = data["datasets"][dataset]
        print(f"{dataset}: n={len(d['points'])}  combinations={len(d['catalog'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute and write the JSON artifact")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
