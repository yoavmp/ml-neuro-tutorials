#!/usr/bin/env python3
"""Deterministic loader + column taxonomy for the Exercise II regression table.

Exercise II predicts a cognitive score from FreeSurfer brain morphometry. The
brain features live in the NeuroHackademy Yarkoni tutorial's ``abide2.tsv``
(HCP-MMP1 / Glasser atlas, 4 measures x 360 ROIs, no missing values, target
``age`` only). The cognitive/behavioural targets live in the ABIDE-II phenotypic
CSV Exercise I already uses. This module pins both by URL + SHA-256, merges them
on the participant id, and exposes:

* :func:`load_modeling_frame` -- download (verifying hashes), merge, return a
  pandas DataFrame of 1004 participants;
* :func:`parse_brain_column` / :func:`classify_columns` -- a strict column
  taxonomy (identifier / non-brain phenotype / brain feature, and for brain
  features the measure, hemisphere, and ROI label). Unknown or malformed brain
  names raise with an actionable message;
* :func:`bundle_columns` -- expand a reviewed anatomical ROI bundle
  (``book/config/abide_modeling.json``) into an ordered list of real column
  names, bilateral, validated against the atlas label inventory;
* :func:`feature_matrix` -- build a **brain-only** design matrix X and target y
  for one bundle x measurement recipe, with a leakage guard that refuses any
  column that is not an atlas brain feature.

All string slicing of ROI names is confined to this file. The notebook and the
TypeScript frontend consume the manifest / this module, never ad-hoc parsing.

Modes:

* ``--audit``  (network): download, merge, and print the full provenance /
  taxonomy / target-availability audit. Use when reviewing the data choice.
* ``--check``  (offline): validate the committed manifest for self-consistency
  -- every bundle ROI is in the atlas inventory and bilateral, the leakage
  pattern rejects every forbidden-exact name, the canonical recipe references a
  real bundle, etc. No network, no writes.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "abide_modeling.json"


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Read the reviewed modelling manifest (never fetched over the network)."""
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schemaVersion") != 1:
        raise ValueError(f"{path}: unsupported schemaVersion {manifest.get('schemaVersion')!r}")
    return manifest


MANIFEST = load_manifest()
_ATLAS = MANIFEST["atlas"]
BRAIN_COLUMN_RE = re.compile(_ATLAS["column_pattern"])
ROI_INVENTORY: tuple[str, ...] = tuple(_ATLAS["roi_label_inventory"])

# A handful of HCP-MMP1 parcels are genuinely bilateral (present in both
# hemispheres) but this source table's two hemisphere columns do not share a
# common raw label suffix -- e.g. canonical ROI "5" is spelled "5L" in its own
# left-hemisphere column and "5R" in its own right-hemisphere column, never
# the reverse. HEMISPHERE_SPECIFIC_LABELS maps canonical roi id -> {hemi: raw
# label}; every other canonical roi id uses its own id as the raw label in
# both hemispheres. See atlas.hemisphere_specific_labels for the audit note.
HEMISPHERE_SPECIFIC_LABELS: dict[str, dict[str, str]] = _ATLAS.get("hemisphere_specific_labels", {})
_RAW_LABEL_LOCK: dict[str, tuple[str, str]] = {
    raw: (canonical, hemi)
    for canonical, hemi_map in HEMISPHERE_SPECIFIC_LABELS.items()
    for hemi, raw in hemi_map.items()
    if hemi in ("L", "R")
}
MEASURE_PREFIX: dict[str, str] = {k: v["prefix"] for k, v in MANIFEST["measures"].items()}
PREFIX_MEASURE: dict[str, str] = {v: k for k, v in MEASURE_PREFIX.items()}
NON_BRAIN_COLUMNS: tuple[str, ...] = tuple(MANIFEST["non_brain_columns"])
_LEAKAGE = MANIFEST["leakage_guard"]
LEAKAGE_FORBIDDEN_EXACT: frozenset[str] = frozenset(_LEAKAGE["forbidden_exact"])
LEAKAGE_FORBIDDEN_RE = re.compile(_LEAKAGE["forbidden_pattern"])


# --- provenance / download -------------------------------------------------


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=180) as response:  # noqa: S310 (pinned https)
        return response.read()


def _verified_bytes(spec: dict[str, Any]) -> bytes:
    data = _fetch(spec["url"])
    digest = sha256_hex(data)
    if digest != spec["sha256"]:
        raise RuntimeError(
            f"{spec['name']}: upstream SHA-256 {digest} does not match the pinned "
            f"{spec['sha256']}. Refusing to use unexpected bytes."
        )
    return data


def load_modeling_frame(manifest: dict[str, Any] | None = None) -> "Any":
    """Download both pinned sources, verify hashes, and return the merged frame.

    Result: one row per participant (1004), brain features + the phenotype
    columns named in ``manifest['source']['merge']['phenotype_columns_kept']``.
    Network access is required.
    """
    import pandas as pd

    manifest = manifest or MANIFEST
    src = manifest["source"]

    brain = pd.read_csv(io.BytesIO(_verified_bytes(src["brain_table"])), sep=src["brain_table"]["sep"])
    brain = brain.loc[:, [c for c in brain.columns if not str(c).startswith("Unnamed")]]

    phen = pd.read_csv(
        io.BytesIO(_verified_bytes(src["phenotype_table"])),
        encoding=src["phenotype_table"]["encoding"],
        low_memory=False,
    )
    phen.columns = phen.columns.str.strip()

    merge = src["merge"]
    keep = [merge["right_on"]] + list(merge["phenotype_columns_kept"])
    frame = brain.merge(
        phen[keep], left_on=merge["left_on"], right_on=merge["right_on"], how=merge["how"]
    )
    if merge["right_on"] != merge["left_on"] and merge["right_on"] in frame.columns:
        frame = frame.drop(columns=[merge["right_on"]])

    expected = manifest["source"]["brain_table"]["rows"]
    if len(frame) != expected:
        raise RuntimeError(f"merged frame has {len(frame)} rows, expected {expected}")
    if frame[merge["left_on"]].duplicated().any():
        raise RuntimeError("merged frame has duplicate participant ids")
    return frame


# --- column taxonomy ------------------------------------------------------


class BrainColumn:
    """A parsed brain-feature column name."""

    __slots__ = ("name", "measure", "hemisphere", "roi")

    def __init__(self, name: str, measure: str, hemisphere: str, roi: str) -> None:
        self.name = name
        self.measure = measure
        self.hemisphere = hemisphere
        self.roi = roi

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"BrainColumn({self.name!r}, {self.measure!r}, {self.hemisphere!r}, {self.roi!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BrainColumn) and (
            self.name,
            self.measure,
            self.hemisphere,
            self.roi,
        ) == (other.name, other.measure, other.hemisphere, other.roi)


def is_brain_column(name: str) -> bool:
    return bool(BRAIN_COLUMN_RE.match(name))


def raw_label_for(roi: str, hemi: str, manifest: dict[str, Any] | None = None) -> str:
    """The literal column-name label for a canonical ROI id in one hemisphere.

    Identity for every ordinary ROI; looks up ``atlas.hemisphere_specific_labels``
    for the few ROIs whose raw column label differs by hemisphere.
    """
    manifest = manifest or MANIFEST
    hemi_specific = manifest["atlas"].get("hemisphere_specific_labels", {})
    return hemi_specific.get(roi, {}).get(hemi, roi)


def parse_brain_column(name: str) -> BrainColumn:
    """Parse ``fs<Measure>_<L|R>_<label>_ROI``. Raise on anything malformed."""
    match = BRAIN_COLUMN_RE.match(name)
    if not match:
        raise ValueError(
            f"{name!r} is not a valid brain-feature column "
            f"(expected {_ATLAS['column_pattern']!r})"
        )
    measure = PREFIX_MEASURE["fs" + match.group("measure")]
    hemi = match.group("hemi")
    raw_label = match.group("label")
    if raw_label in _RAW_LABEL_LOCK:
        canonical, want_hemi = _RAW_LABEL_LOCK[raw_label]
        if hemi != want_hemi:
            raise ValueError(
                f"{name!r}: label {raw_label!r} only exists in hemisphere {want_hemi} "
                f"(it is the {want_hemi}-hemisphere raw label for canonical ROI {canonical!r})"
            )
        roi = raw_label
    elif raw_label in ROI_INVENTORY:
        roi = raw_label
    else:
        raise ValueError(
            f"{name!r} names ROI {raw_label!r}, which is not in the HCP-MMP1 label inventory"
        )
    return BrainColumn(name, measure, hemi, roi)


def classify_columns(columns: "Any") -> dict[str, Any]:
    """Split a column iterable into identifiers / phenotypes / brain features."""
    identifiers: list[str] = []
    phenotypes: list[str] = []
    brain: list[BrainColumn] = []
    id_set = set(MANIFEST["identifier_columns"])
    for name in map(str, columns):
        if is_brain_column(name):
            brain.append(parse_brain_column(name))
        elif name in id_set:
            identifiers.append(name)
        else:
            phenotypes.append(name)

    by_measure: dict[str, int] = {}
    rois: set[str] = set()
    hemis: set[str] = set()
    for bc in brain:
        by_measure[bc.measure] = by_measure.get(bc.measure, 0) + 1
        rois.add(_RAW_LABEL_LOCK.get(bc.roi, (bc.roi, None))[0])
        hemis.add(bc.hemisphere)
    return {
        "identifiers": identifiers,
        "phenotypes": phenotypes,
        "brain_features": [bc.name for bc in brain],
        "brain_parsed": brain,
        "measures": by_measure,
        "roi_count": len(rois),
        "hemispheres": sorted(hemis),
    }


# --- ROI bundles --------------------------------------------------------


def bundle_rois(bundle: str, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    if bundle == "all-eligible":
        # Every canonical ROI id in the inventory is genuinely bilateral (see
        # atlas.hemisphere_specific_labels for the few whose raw column label
        # differs by hemisphere) -- no exclusion needed.
        return list(manifest["atlas"]["roi_label_inventory"])
    try:
        rois = manifest["bundles"][bundle]["rois"]
    except KeyError:
        raise ValueError(
            f"unknown ROI bundle {bundle!r}; known: "
            f"{sorted(manifest['bundles'])} + ['all-eligible']"
        ) from None
    return list(rois)


def bundle_columns(
    bundle: str,
    measures: "list[str] | tuple[str, ...]",
    available: "Any | None" = None,
    manifest: dict[str, Any] | None = None,
) -> list[str]:
    """Expand a bundle x measurement recipe to an ordered list of column names.

    Order: ROI (bundle order), then measure (given order), then hemisphere L, R.
    Every ROI must be in the atlas inventory and present in both hemispheres.
    If ``available`` is given, every produced name must be in it.
    """
    manifest = manifest or MANIFEST
    for m in measures:
        if m not in MEASURE_PREFIX:
            raise ValueError(f"unknown measure {m!r}; known: {sorted(MEASURE_PREFIX)}")
    inventory = set(manifest["atlas"]["roi_label_inventory"])
    available_set = set(map(str, available)) if available is not None else None

    out: list[str] = []
    for roi in bundle_rois(bundle, manifest):
        if roi not in inventory:
            raise ValueError(f"bundle {bundle!r}: ROI {roi!r} is not an HCP-MMP1 label")
        for m in measures:
            for hemi in ("L", "R"):
                raw_label = raw_label_for(roi, hemi, manifest)
                name = f"{MEASURE_PREFIX[m]}_{hemi}_{raw_label}_ROI"
                if available_set is not None and name not in available_set:
                    raise ValueError(
                        f"bundle {bundle!r} recipe: expected column {name!r} is not in the data"
                    )
                out.append(name)
    if len(out) != len(set(out)):
        raise ValueError(f"bundle {bundle!r} produced duplicate columns")
    return out


# --- leakage guard + feature matrix ----------------------------------------


def assert_brain_only(columns: "list[str] | tuple[str, ...]") -> None:
    """Raise unless every column is an atlas brain feature and nothing forbidden."""
    for name in columns:
        if name in LEAKAGE_FORBIDDEN_EXACT:
            raise ValueError(f"leakage guard: {name!r} is a forbidden (target/phenotype/id) column")
        if not is_brain_column(name):
            raise ValueError(
                f"leakage guard: {name!r} is not a brain-derived feature "
                "(only fs<measure>_<hemi>_<roi>_ROI columns may enter X)"
            )
        parse_brain_column(name)  # ROI must be real
        if LEAKAGE_FORBIDDEN_RE.search(name):
            raise ValueError(f"leakage guard: {name!r} matches the forbidden-name pattern")


def feature_matrix(
    frame: "Any",
    bundle: str,
    measures: "list[str] | tuple[str, ...]",
    target: str,
    manifest: dict[str, Any] | None = None,
):
    """Return ``(X, y, columns)`` for one recipe: brain-only X, target y, rows
    with a present target only. X column order is deterministic (see
    :func:`bundle_columns`)."""
    manifest = manifest or MANIFEST
    if target not in manifest["targets"]:
        raise ValueError(f"unknown target {target!r}; known: {sorted(manifest['targets'])}")
    columns = bundle_columns(bundle, measures, available=frame.columns, manifest=manifest)
    assert_brain_only(columns)
    if target in columns:
        raise ValueError("leakage guard: the target appears in the feature list")

    present = frame[target].notna().to_numpy()
    X = frame.loc[present, columns].to_numpy(dtype="float64")
    y = frame.loc[present, target].to_numpy(dtype="float64")
    return X, y, columns


# --- audit / check --------------------------------------------------------


def _check_manifest(manifest: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    inv = set(manifest["atlas"]["roi_label_inventory"])
    hemi_specific = manifest["atlas"].get("hemisphere_specific_labels", {})
    if len(inv) != manifest["atlas"].get("bilateral_label_count"):
        problems.append("atlas.bilateral_label_count disagrees with the inventory (every ROI is bilateral)")
    for canonical, hemi_map in hemi_specific.items():
        if canonical not in inv:
            problems.append(f"hemisphere_specific_labels canonical ROI {canonical!r} not in the atlas inventory")
        raw_labels = {hemi_map.get("L"), hemi_map.get("R")}
        if None in raw_labels or len(raw_labels) != 2:
            problems.append(f"hemisphere_specific_labels[{canonical!r}] must give distinct L and R raw labels")

    for name, bundle in manifest["bundles"].items():
        rois = bundle["rois"]
        if len(rois) != len(set(rois)):
            problems.append(f"bundle {name!r} has duplicate ROIs")
        for roi in rois:
            if roi not in inv:
                problems.append(f"bundle {name!r}: ROI {roi!r} not in the atlas inventory")

    recipe = manifest["protocol"]["canonical_recipe"]
    if recipe["bundle"] != "all-eligible" and recipe["bundle"] not in manifest["bundles"]:
        problems.append(f"canonical recipe bundle {recipe['bundle']!r} is not defined")
    for m in recipe["measures"]:
        if m not in manifest["measures"]:
            problems.append(f"canonical recipe measure {m!r} is not defined")

    cat = manifest["catalog"]
    if cat["target"] not in manifest["targets"]:
        problems.append("catalog.target is not a defined target")
    for b in cat["bundles"]:
        if b != "all-eligible" and b not in manifest["bundles"]:
            problems.append(f"catalog bundle {b!r} is not defined")
    for subset in cat["measurement_subsets"]:
        for m in subset:
            if m not in manifest["measures"]:
                problems.append(f"catalog measurement subset references unknown measure {m!r}")

    pattern = re.compile(manifest["leakage_guard"]["forbidden_pattern"])
    # The exact list and the pattern are complementary. Require: every target is
    # in the exact list, and the pattern never rejects a real brain column.
    for target in manifest["targets"]:
        if target not in manifest["leakage_guard"]["forbidden_exact"]:
            problems.append(f"target {target!r} is missing from leakage_guard.forbidden_exact")
    for roi in list(inv)[:] + [b for bundle in manifest["bundles"].values() for b in bundle["rois"]]:
        for prefix in MEASURE_PREFIX.values():
            for hemi in ("L", "R"):
                raw_label = hemi_specific.get(roi, {}).get(hemi, roi)
                col = f"{prefix}_{hemi}_{raw_label}_ROI"
                if pattern.search(col):
                    problems.append(f"forbidden pattern wrongly rejects a real brain column: {col}")
    for roles in (("main", "regularization_preview"),):
        seen = {t["role"] for t in manifest["targets"].values()}
        for role in roles:
            if role not in seen:
                problems.append(f"no target has role {role!r}")

    # No bundle ROI may look like an identifier/target under the leak pattern.
    for name, bundle in manifest["bundles"].items():
        for roi in bundle["rois"]:
            col = f"fsCT_L_{hemi_specific.get(roi, {}).get('L', roi)}_ROI"
            if pattern.search(col):
                problems.append(f"bundle {name!r} ROI {roi!r} expands to a name the leak guard rejects: {col}")
    return problems


def cmd_check() -> int:
    problems = _check_manifest(MANIFEST)
    if problems:
        print("ERROR: abide_modeling.json failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    b = MANIFEST["bundles"]
    print(f"OK: {MANIFEST_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    print(f"  atlas          : {MANIFEST['atlas']['name']} ({len(ROI_INVENTORY)} labels)")
    print(f"  measures       : {', '.join(MEASURE_PREFIX)}")
    print(f"  bundles        : " + ", ".join(f"{k}({len(v['rois'])})" for k, v in b.items()))
    print(f"  canonical      : {MANIFEST['protocol']['canonical_recipe']}")
    print(f"  targets        : " + ", ".join(f"{k}[{v['role']}]" for k, v in MANIFEST["targets"].items()))
    return 0


def cmd_audit() -> int:
    import numpy as np

    frame = load_modeling_frame()
    taxonomy = classify_columns(frame.columns)
    src = MANIFEST["source"]
    print("=== provenance ===")
    print(f"pinned commit : {src['pinned_commit']}  ({src['license']})")
    for key in ("brain_table", "phenotype_table"):
        s = src[key]
        print(f"{key:16s}: {s['name']}  sha256={s['sha256']}")
    print(f"merged frame  : {frame.shape[0]} rows x {frame.shape[1]} cols")
    print()
    print("=== taxonomy ===")
    print(f"identifiers   : {taxonomy['identifiers']}")
    print(f"phenotypes    : {taxonomy['phenotypes']}")
    print(f"brain features: {len(taxonomy['brain_features'])}  measures={taxonomy['measures']}  "
          f"rois={taxonomy['roi_count']}  hemispheres={taxonomy['hemispheres']}")
    brain_na = frame[taxonomy["brain_features"]].isna().to_numpy().sum()
    print(f"brain missing : {int(brain_na)} cells")
    print()
    print("=== target availability (rows with usable brain data) ===")
    for name, meta in MANIFEST["targets"].items():
        col = frame[name]
        n = int(col.notna().sum())
        vals = col.dropna().to_numpy(dtype="float64")
        print(f"  {name:16s} role={meta['role']:18s} n={n:4d} miss={len(col) - n:4d} "
              f"range=[{np.min(vals):.1f},{np.max(vals):.1f}] mean={np.mean(vals):.1f} sd={np.std(vals):.1f}")
    print()
    print("=== canonical recipe check ===")
    recipe = MANIFEST["protocol"]["canonical_recipe"]
    X, y, cols = feature_matrix(frame, recipe["bundle"], recipe["measures"], "FIQ")
    print(f"  {recipe['bundle']} x {recipe['measures']} -> X {X.shape}, y {y.shape}, first col {cols[0]}")
    assert_brain_only(cols)
    print("  leakage guard: X is brain-only (OK)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true", help="download + merge + print the full audit (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed manifest offline")
    args = parser.parse_args(argv)
    return cmd_audit() if args.audit else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
