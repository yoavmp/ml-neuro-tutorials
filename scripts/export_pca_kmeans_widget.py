#!/usr/bin/env python3
"""Precomputed PCA + K-means catalogue for Exercise 8's "Explore PCA and
K-Means" activity (WP33).

PCA is fit exactly **once** -- ``n_components=50``, on the standardized
360-cortical-thickness-feature table for the full 1004-participant eligible
cohort (``sklearn.preprocessing.StandardScaler`` then
``sklearn.decomposition.PCA(random_state=0)``) -- and every participant's
PC1/PC2 score is stored once. This is correct, not a shortcut: PCA
components are *nested*, so a component's scores never change when more
components are retained alongside it; fitting with ``n_components=50`` and
reading off the first two columns gives the identical PC1/PC2 the widget
would get from a separate ``n_components=2`` fit.

For every ``(retained_pc, k, seed)`` combination in
``unsupervised.kmeans_catalog`` (``book/config/abide_modeling.json``),
``sklearn.cluster.KMeans`` is fit on the first ``retained_pc`` columns of
that same score matrix -- never on PC1-PC2 alone, even though the scatter
plot the widget draws always shows only PC1-PC2 -- with an explicit
``n_init`` and ``random_state=seed``. External variables (diagnosis, sex,
site, age) are never inputs to PCA or K-means; they are stored once, per
participant, and joined onto cluster labels only in the browser, for
display.

Usage::

    python scripts/export_pca_kmeans_widget.py --refresh   # writes JSON
    python scripts/export_pca_kmeans_widget.py --check     # re-validate

Asserted by ``tests/test_export_pca_kmeans_widget_data.py``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "pca_kmeans_explorer.json"
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "abide_modeling.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from abide_modeling_data import MANIFEST, assert_brain_only, load_modeling_frame  # noqa: E402

CATALOG = MANIFEST["unsupervised"]["kmeans_catalog"]
RETAINED_PC_GRID: list[int] = CATALOG["retained_pc_grid"]
K_GRID: list[int] = CATALOG["k_grid"]
SEEDS: list[int] = CATALOG["seeds"]
N_INIT: int = CATALOG["n_init"]
EXTERNAL_VARIABLES: dict[str, str] = CATALOG["external_variables"]
MAX_RETAINED_PC = max(RETAINED_PC_GRID)


def _natural_order_columns(frame: Any) -> list[str]:
    return [c for c in frame.columns if c.startswith("fsCT_")]


def _combo_key(retained_pc: int, k: int, seed: int) -> str:
    return f"{retained_pc}|{k}|{seed}"


def build_data() -> dict[str, Any]:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    frame = load_modeling_frame()
    cols = _natural_order_columns(frame)
    assert_brain_only(cols)
    X = frame.loc[:, cols].to_numpy(dtype="float64")

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    pca = PCA(n_components=MAX_RETAINED_PC, random_state=0).fit(Xs)
    scores = pca.transform(Xs)  # (1004, 50); nested -- first k columns == a k-component fit

    n = scores.shape[0]
    pc1 = [round(float(v), 4) for v in scores[:, 0]]
    pc2 = [round(float(v), 4) for v in scores[:, 1]]

    external = {
        "group": [int(v) for v in frame["group"].to_numpy()],
        "sex": [str(v) for v in frame["sex"].to_numpy()],
        "site": [str(v) for v in frame["site"].to_numpy()],
        "age": [round(float(v), 2) for v in frame["age"].to_numpy()],
    }

    catalog: dict[str, Any] = {}
    for retained_pc in RETAINED_PC_GRID:
        sub = scores[:, :retained_pc]
        for seed in SEEDS:
            for k in K_GRID:
                km = KMeans(n_clusters=k, n_init=N_INIT, random_state=seed).fit(sub)
                labels = km.labels_
                sizes = [int((labels == c).sum()) for c in range(k)]
                # Silhouette is mathematically valid only for 2 <= k <= n-1
                # distinct labels; the declared k_grid (2..6) with n=1004
                # never violates this, but the guard is explicit rather than
                # assumed.
                sil = (
                    round(float(silhouette_score(sub, labels)), 4)
                    if 2 <= len(set(labels.tolist())) <= n - 1
                    else None
                )
                centers_pc1pc2 = [[round(float(c[0]), 4), round(float(c[1]), 4)] for c in km.cluster_centers_]
                catalog[_combo_key(retained_pc, k, seed)] = {
                    "retainedPc": retained_pc,
                    "k": k,
                    "seed": seed,
                    "clusterLabels": [int(v) for v in labels],
                    "inertia": round(float(km.inertia_), 2),
                    "silhouette": sil,
                    "clusterSizes": sizes,
                    "centersPC1PC2": centers_pc1pc2,
                }
                if sum(sizes) != n:
                    raise RuntimeError(f"{_combo_key(retained_pc, k, seed)}: cluster sizes do not sum to {n}")

    return {
        "schemaVersion": 1,
        "activity": "pca-kmeans-explorer",
        "cohortNote": (
            "PCA and K-means use the full 1004-participant eligible cohort and the same "
            "360-column cortical-thickness recipe as every other exercise. Diagnosis, sex, "
            "site, and age are never inputs to PCA or K-means -- they are stored here only for "
            "display, joined onto cluster labels after clustering."
        ),
        "nParticipants": n,
        "pca": {
            "nComponentsFit": MAX_RETAINED_PC,
            "note": (
                "Fit once (StandardScaler then PCA(n_components=50), random_state=0). PC1/PC2 "
                "scores are identical for every retained-PC count because PCA components are "
                "nested."
            ),
        },
        "participants": {"pc1": pc1, "pc2": pc2, "external": external},
        "externalVariableLabels": EXTERNAL_VARIABLES,
        "retainedPcGrid": RETAINED_PC_GRID,
        "kGrid": K_GRID,
        "seeds": SEEDS,
        "nInit": N_INIT,
        "catalog": catalog,
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
    n = data.get("nParticipants")
    if n != 1004:
        problems.append("nParticipants must be 1004")
        return problems

    participants = data.get("participants", {})
    if len(participants.get("pc1", [])) != n or len(participants.get("pc2", [])) != n:
        problems.append("participants.pc1/pc2 must have exactly nParticipants entries")
    external = participants.get("external", {})
    for key in ("group", "sex", "site", "age"):
        if len(external.get(key, [])) != n:
            problems.append(f"participants.external.{key} must have exactly nParticipants entries")

    catalog = data.get("catalog", {})
    retained = data.get("retainedPcGrid", [])
    ks = data.get("kGrid", [])
    seeds = data.get("seeds", [])
    expected_keys = {_combo_key(r, k, s) for r in retained for k in ks for s in seeds}
    got_keys = set(catalog.keys())
    if expected_keys != got_keys:
        missing = expected_keys - got_keys
        extra = got_keys - expected_keys
        if missing:
            problems.append(f"catalog missing {len(missing)} combination(s), e.g. {sorted(missing)[:3]}")
        if extra:
            problems.append(f"catalog has {len(extra)} unexpected combination(s), e.g. {sorted(extra)[:3]}")

    for key, entry in catalog.items():
        labels = entry.get("clusterLabels", [])
        if len(labels) != n:
            problems.append(f"catalog[{key}].clusterLabels must have exactly nParticipants entries")
            continue
        k = entry.get("k")
        if any(not (0 <= lbl < k) for lbl in labels):
            problems.append(f"catalog[{key}]: cluster labels must be in [0, k)")
        sizes = entry.get("clusterSizes", [])
        if len(sizes) != k or sum(sizes) != n:
            problems.append(f"catalog[{key}]: clusterSizes must have k entries summing to nParticipants")
        recomputed_sizes = [labels.count(c) for c in range(k)]
        if recomputed_sizes != sizes:
            problems.append(f"catalog[{key}]: clusterSizes does not match a fresh recount of clusterLabels")
        if len(entry.get("centersPC1PC2", [])) != k:
            problems.append(f"catalog[{key}]: centersPC1PC2 must have k entries")
        sil = entry.get("silhouette")
        if sil is not None and not (-1.0 <= sil <= 1.0):
            problems.append(f"catalog[{key}]: silhouette out of [-1, 1]")

    return problems


def cmd_check() -> int:
    # Offline: this artifact's source (the real ABIDE-II table) requires
    # network to reload, so --check validates structure + canonical
    # serialization only, the same convention scripts/export_regression_catalog.py
    # uses -- never a network-requiring semantic_diff against a fresh
    # recomputation (that comparison is what --refresh followed by `git diff`
    # is for). Contrast scripts/export_pca_projection_widget.py, whose data is
    # entirely synthetic and therefore safe to recompute offline in --check.
    if not OUT_PATH.exists():
        print(f"ERROR: {OUT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    on_disk = OUT_PATH.read_text(encoding="utf-8")
    data = json.loads(on_disk)
    problems = validate(data)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if serialize(data) != on_disk:
        print("ERROR: committed artifact is not canonical (re-serialization differs).", file=sys.stderr)
        return 1
    print(f"OK: {OUT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_summary(data)
    return 0


def _print_summary(data: dict[str, Any]) -> None:
    print(
        f"n={data['nParticipants']}  retainedPcGrid={data['retainedPcGrid']}  kGrid={data['kGrid']}  "
        f"seeds={data['seeds']}  combinations={len(data['catalog'])}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute and write the JSON artifact (network)")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON artifact (offline)")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
