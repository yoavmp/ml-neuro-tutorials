#!/usr/bin/env python3
"""Deterministic synthetic 2-D point cloud for Exercise 8's "Find the Best
Projection" activity (WP33).

The dataset is entirely synthetic -- 40 observations on two continuous
variables, drawn from a fixed, mean-zero, correlated Gaussian
(``unsupervised.projection_activity`` in ``book/config/abide_modeling.json``)
with a seed decided before generation. The sample is exactly mean-centered
after drawing (its own empirical mean is (0, 0), not just the population
mean), so the browser widget's projection math -- projecting onto the
student's chosen angle, the variance captured, and the reconstruction MSE --
is pure closed-form trigonometry over this fixed cloud, with no model
fitting and no Python runtime in the browser.

This script also precomputes the *true* PC1 direction (via the sample
covariance's eigendecomposition) and its explained-variance ratio, used only
after the student presses "Show PC1" -- the answer must never be visible
before that.

Usage::

    python scripts/export_pca_projection_widget.py --refresh   # writes JSON
    python scripts/export_pca_projection_widget.py --check     # re-validate

Asserted by ``tests/test_export_pca_projection_widget_data.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "pca_projection.json"
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "abide_modeling.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from semantic_json_compare import DEFAULT_ABS_TOL, semantic_diff  # noqa: E402

_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
_PROJ = _MANIFEST["unsupervised"]["projection_activity"]

N_OBSERVATIONS: int = _PROJ["n_observations"]
SEED: int = _PROJ["seed"]
SIGMA_X: float = _PROJ["sigma_x"]
SIGMA_Y: float = _PROJ["sigma_y"]
RHO: float = _PROJ["rho"]


def _generate() -> Any:
    import numpy as np

    cov = [[SIGMA_X**2, RHO * SIGMA_X * SIGMA_Y], [RHO * SIGMA_X * SIGMA_Y, SIGMA_Y**2]]
    rng = np.random.RandomState(SEED)
    pts = rng.multivariate_normal([0.0, 0.0], cov, size=N_OBSERVATIONS)
    # Exact sample centering: the *stored* cloud's own empirical mean is
    # (0, 0), so the browser never needs to separately track/subtract a mean.
    pts = pts - pts.mean(axis=0)
    return pts


def _true_pc1(pts: Any) -> dict[str, Any]:
    import numpy as np

    n = pts.shape[0]
    cov_hat = (pts.T @ pts) / n  # population covariance; points are already centered
    evals, evecs = np.linalg.eigh(cov_hat)
    order = np.argsort(-evals)
    evals = evals[order]
    evecs = evecs[:, order]
    angle_deg = float(np.degrees(np.arctan2(evecs[1, 0], evecs[0, 0])) % 180.0)
    total_variance = float(evals.sum())
    return {
        "angleDeg": round(angle_deg, 3),
        "explainedVarianceRatio": round(float(evals[0] / total_variance), 6),
        "totalVariance": round(total_variance, 6),
    }


def build_data() -> dict[str, Any]:
    pts = _generate()
    observations = [{"id": i, "x": round(float(p[0]), 4), "y": round(float(p[1]), 4)} for i, p in enumerate(pts)]
    true_pc1 = _true_pc1(pts)

    return {
        "schemaVersion": 1,
        "activity": "pca-projection",
        "syntheticDataNote": (
            "This dataset is simulated: 40 points on two continuous variables, drawn from a "
            "fixed, correlated, mean-zero distribution and seed. It is used to build intuition "
            "for projecting onto an axis, not to reproduce a real measurement -- these are not "
            "ABIDE observations."
        ),
        "generatingProcess": {
            "distribution": "mean-zero correlated Gaussian",
            "sigmaX": SIGMA_X,
            "sigmaY": SIGMA_Y,
            "rho": RHO,
            "nObservations": N_OBSERVATIONS,
            "seed": SEED,
            "seedNote": "Fixed before generation; no seed search.",
            "centeringNote": "The stored cloud is exactly sample-mean-centered: its own empirical mean is (0, 0).",
        },
        "featureX": {"name": "x", "label": "Feature 1"},
        "featureY": {"name": "y", "label": "Feature 2"},
        "observations": observations,
        "totalVariance": true_pc1["totalVariance"],
        "truePc1": {"angleDeg": true_pc1["angleDeg"], "explainedVarianceRatio": true_pc1["explainedVarianceRatio"]},
        "angleSliderDeg": dict(_PROJ["angle_slider_deg"]),
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
    import numpy as np

    problems: list[str] = []
    obs = data.get("observations", [])
    if len(obs) != N_OBSERVATIONS:
        problems.append(f"observations count must be exactly {N_OBSERVATIONS}")
        return problems

    xs = np.array([o["x"] for o in obs])
    ys = np.array([o["y"] for o in obs])
    if abs(float(xs.mean())) > 1e-2 or abs(float(ys.mean())) > 1e-2:
        problems.append("observations must be (near-exactly) mean-centered")

    total_var = float(np.mean(xs**2) + np.mean(ys**2))
    if abs(total_var - data.get("totalVariance", -1)) > 1e-2:
        problems.append(f"totalVariance ({data.get('totalVariance')}) does not match a fresh recomputation ({total_var:.4f})")

    true_pc1 = data.get("truePc1", {})
    angle = true_pc1.get("angleDeg")
    if angle is None or not (0.0 <= angle <= 180.0):
        problems.append("truePc1.angleDeg must be in [0, 180]")
    else:
        theta = np.radians(angle)
        u = np.array([np.cos(theta), np.sin(theta)])
        t = xs * u[0] + ys * u[1]
        variance_captured = float(np.mean(t**2))
        evr = variance_captured / total_var if total_var > 0 else 0.0
        if abs(evr - true_pc1.get("explainedVarianceRatio", -1)) > 1e-2:
            problems.append(
                f"truePc1.explainedVarianceRatio ({true_pc1.get('explainedVarianceRatio')}) does not match a "
                f"fresh recomputation at the stored angle ({evr:.4f})"
            )
        # The true PC1 direction must actually be (locally) variance-maximizing:
        # a small perturbation should not increase captured variance.
        for delta in (-1.0, 1.0):
            theta2 = np.radians(angle + delta)
            u2 = np.array([np.cos(theta2), np.sin(theta2)])
            t2 = xs * u2[0] + ys * u2[1]
            if float(np.mean(t2**2)) > variance_captured + 1e-6:
                problems.append("truePc1.angleDeg is not a local variance maximum")
                break

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
    print(
        f"n={len(data['observations'])}  totalVariance={data['totalVariance']:.2f}  "
        f"truePC1 angle={data['truePc1']['angleDeg']:.1f} deg  "
        f"EVR={data['truePc1']['explainedVarianceRatio']:.3f}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute and write the JSON artifact")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
