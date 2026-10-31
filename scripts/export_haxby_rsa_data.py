#!/usr/bin/env python3
"""Build Exercise 11's prepared Haxby RSA export (WP61 Gate A).

Downloads the Haxby et al. (2001) visual-object-category fMRI dataset for
subject 2 (nilearn's own documented default subject for
``nilearn.datasets.fetch_haxby``), derives one ventral-temporal (VT)
voxel-response pattern per stimulus category per scanning run, and writes:

* ``book/lite/files/data/haxby_rsa_patterns.csv`` -- the small derived
  export (one row per run x category, one column per retained VT voxel).
  This is what the student notebook loads -- never the ~300 MB raw
  functional file.
* ``book/lite/files/data/haxby_rsa_patterns.manifest.json`` -- dataset
  citation/source/license, the exact mask used, every preprocessing choice
  (block detection, hemodynamic-onset handling, per-run z-scoring),
  dimensions, exclusions, the checks performed, and the derived file's own
  sha256.

Method (stated here, not only in the manifest, since this is the part a
reviewer most needs to audit):

1. Fetch subject 2's ``bold.nii.gz`` (4D functional run), ``labels.txt``
   (per-TR condition label + run/``chunks`` number), and ``mask4_vt.nii.gz``
   (the broad ventral-temporal mask -- nilearn's ``mask_vt`` attribute).
   Deliberately NOT ``mask8_face_vt``/``mask8_house_vt``/``mask8b_*``: those
   are voxel-selective for the exact face/house contrast this exercise later
   evaluates, which would make the RSA face-hypothesis comparison circular.
2. Within each run, z-score every retained voxel's BOLD time series (mean 0,
   sd 1 across that run's own TRs only) -- a simple per-run baseline/scale
   correction, done separately per run so no cross-run drift or scanner
   baseline difference leaks into the patterns.
3. Within each run, find contiguous spans of identical condition label in
   ``labels.txt`` (its own ``chunks`` column marks run boundaries). For
   every non-"rest" span (one stimulus block), drop its first
   ``HRF_ONSET_TRS_DROPPED`` TRs before averaging: the BOLD hemodynamic
   response lags neural/stimulus onset by several seconds, so a block's
   earliest TRs still partly reflect the previous condition. The remaining
   TRs of the block are averaged (voxel-wise, on the already z-scored
   series) into that run/category's pattern.
4. Verify every retained run contains exactly one block for every one of
   the 8 non-"rest" categories, and that both the odd-run subset and the
   even-run subset independently cover all 8 categories (required for the
   notebook's split-half reliability section).

Modes (exactly one required):

* ``--refresh``  (network): download via nilearn, verify, extract, write
  the CSV + manifest.
* ``--check``    (offline): re-validate the committed CSV/manifest for
  internal consistency and the checksum they claim about each other. No
  network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = REPO_ROOT / "book" / "lite" / "files" / "data" / "haxby_rsa_patterns.csv"
OUT_MANIFEST = REPO_ROOT / "book" / "lite" / "files" / "data" / "haxby_rsa_patterns.manifest.json"

SUBJECT = 2  # nilearn.datasets.fetch_haxby's own documented default subject
HRF_ONSET_TRS_DROPPED = 2
MIN_BLOCK_TRS_AFTER_DROP = 3  # if a block is too short to safely drop this many, drop fewer instead

DATASET_TITLE = "Haxby et al. (2001) visual object category representation (ventral temporal cortex)"
DATASET_CITATION = (
    "Haxby, J. V., Gobbini, M. I., Furey, M. L., Ishai, A., Schouten, J. L., & Pietrini, P. (2001). "
    "Distributed and overlapping representations of faces and objects in ventral temporal cortex. "
    "Science, 293(5539), 2425-2430. https://doi.org/10.1126/science.1063736"
)
DATASET_SOURCE_URL = "http://data.pymvpa.org/datasets/haxby2001/"
DATASET_LICENSE = (
    "nilearn's own dataset description (nilearn.datasets.description.haxby2001) lists this dataset's "
    "license as \"unknown\" -- there is no explicit license grant from the original distributor. The "
    "data has been openly distributed for research and teaching since 2010 via the PyMVPA project's "
    "data repository (the URL above), with Haxby et al. (2001) as the expected attribution; this "
    "derived course export is shared on that same open-reuse basis and carries the same citation "
    "requirement, not a stronger license than the source data itself carries."
)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch_haxby_subject():
    from nilearn import datasets

    return datasets.fetch_haxby(subjects=[SUBJECT], fetch_stimuli=False, verbose=1)


def _contiguous_blocks(labels: np.ndarray) -> list[tuple[str, int, int]]:
    """Return (label, start, end) for every contiguous run-local span."""
    blocks: list[tuple[str, int, int]] = []
    start = 0
    n = len(labels)
    for i in range(1, n + 1):
        if i == n or labels[i] != labels[start]:
            blocks.append((str(labels[start]), start, i))
            start = i
    return blocks


def build_patterns() -> tuple[pd.DataFrame, dict[str, Any]]:
    import nibabel as nib

    data = _fetch_haxby_subject()
    func_path = data.func[0]
    labels_path = data.session_target[0]
    mask_path = data.mask_vt[0]

    func_img = nib.load(func_path)
    tr_seconds = float(func_img.header.get_zooms()[3])
    mask = nib.load(mask_path).get_fdata().astype(bool)
    n_voxels = int(mask.sum())
    if n_voxels == 0:
        raise RuntimeError(f"ventral-temporal mask at {mask_path} is empty")

    # Only the masked voxels are ever materialized in full (func_img itself
    # is ~300 MB uncompressed; masking immediately after loading keeps peak
    # memory to this small VT voxel set x timepoints, not the whole volume).
    full = func_img.get_fdata(dtype=np.float32)
    voxel_ts = full[mask].astype(np.float64)  # shape (n_voxels, n_trs)
    del full

    labels_df = pd.read_csv(labels_path, sep=r"\s+")
    if list(labels_df.columns) != ["labels", "chunks"]:
        raise RuntimeError(f"unexpected labels.txt columns: {list(labels_df.columns)}")
    if voxel_ts.shape[1] != len(labels_df):
        raise RuntimeError(
            f"func volume count ({voxel_ts.shape[1]}) does not match labels.txt row count ({len(labels_df)})"
        )

    all_labels = labels_df["labels"].to_numpy()
    all_chunks = labels_df["chunks"].to_numpy()
    runs = sorted(int(r) for r in np.unique(all_chunks))
    categories = sorted(set(all_labels.tolist()) - {"rest"})

    records: list[dict[str, Any]] = []
    run_category_block_counts: dict[int, dict[str, int]] = {}
    block_len_observations: list[int] = []
    drop_observations: list[int] = []

    for run in runs:
        run_rows = np.where(all_chunks == run)[0]
        run_labels = all_labels[run_rows]
        run_voxels = voxel_ts[:, run_rows]  # (n_voxels, n_trs_in_run)

        # Per-run z-score, voxel-wise, across every TR of this run (stimulus
        # and rest alike) -- done separately per run so cross-run baseline
        # drift never mixes into any pattern.
        mean = run_voxels.mean(axis=1, keepdims=True)
        std = run_voxels.std(axis=1, keepdims=True)
        std = np.where(std == 0, 1.0, std)
        run_voxels_z = (run_voxels - mean) / std

        counts: dict[str, int] = {}
        for label, start, end in _contiguous_blocks(run_labels):
            if label == "rest":
                continue
            counts[label] = counts.get(label, 0) + 1
            block_len = end - start
            block_len_observations.append(block_len)
            drop = min(HRF_ONSET_TRS_DROPPED, max(0, block_len - MIN_BLOCK_TRS_AFTER_DROP))
            drop_observations.append(drop)
            keep_start = start + drop
            if keep_start >= end:
                keep_start = start
            pattern = run_voxels_z[:, keep_start:end].mean(axis=1)
            records.append({"run": run, "category": label, "_pattern": pattern, "block_len": block_len, "trs_dropped": drop})
        run_category_block_counts[run] = counts

    # Collapse any category that appeared in more than one block in the same
    # run (not expected by the documented Haxby block design, but handled
    # rather than silently dropped) by averaging those blocks' patterns.
    grouped: dict[tuple[int, str], list[np.ndarray]] = {}
    for rec in records:
        grouped.setdefault((rec["run"], rec["category"]), []).append(rec["_pattern"])

    rows = []
    for (run, category), patterns in sorted(grouped.items()):
        avg_pattern = np.mean(patterns, axis=0)
        row = {"run": run, "category": category}
        for i, v in enumerate(avg_pattern):
            row[f"voxel_{i:0{len(str(n_voxels - 1))}d}"] = float(v)
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values(["run", "category"]).reset_index(drop=True)

    exclusions: list[str] = []
    for run in runs:
        counts = run_category_block_counts.get(run, {})
        missing = sorted(set(categories) - set(counts))
        multiple = {k: v for k, v in counts.items() if v != 1}
        if missing:
            exclusions.append(f"run {run}: missing block(s) for category/categories {missing}")
        if multiple:
            exclusions.append(f"run {run}: category/categories with more than one block, averaged together: {multiple}")
    if not exclusions:
        exclusions.append("none: every retained run contained exactly one contiguous block per category")

    odd_runs = [r for r in runs if r % 2 == 1]
    even_runs = [r for r in runs if r % 2 == 0]
    odd_categories = set(frame[frame["run"].isin(odd_runs)]["category"])
    even_categories = set(frame[frame["run"].isin(even_runs)]["category"])
    odd_even_ok = odd_categories == set(categories) and even_categories == set(categories)

    meta = {
        "trSeconds": tr_seconds,
        "nVoxels": n_voxels,
        "nRuns": len(runs),
        "runs": runs,
        "categories": categories,
        "nRows": int(len(frame)),
        "exclusions": exclusions,
        "blockLenObserved": sorted(set(block_len_observations)),
        "trsDroppedObserved": sorted(set(drop_observations)),
        "oddRuns": odd_runs,
        "evenRuns": even_runs,
        "oddEvenEachCoverAllCategories": bool(odd_even_ok),
    }
    return frame, meta


def write_csv(frame: pd.DataFrame) -> str:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    csv_text = frame.to_csv(index=False, lineterminator="\n")
    OUT_CSV.write_text(csv_text, encoding="utf-8")
    return sha256_hex(OUT_CSV.read_bytes())


def build_manifest(meta: dict[str, Any], derived_sha256: str) -> dict[str, Any]:
    n_voxel_cols = meta["nVoxels"]
    return {
        "schemaVersion": 1,
        "dataset": {
            "title": DATASET_TITLE,
            "citation": DATASET_CITATION,
            "sourceUrl": DATASET_SOURCE_URL,
            "archiveFile": f"subj{SUBJECT}-2010.01.14.tar.gz",
            "nilearnFetcher": f"nilearn.datasets.fetch_haxby(subjects=[{SUBJECT}])",
            "subject": SUBJECT,
            "license": DATASET_LICENSE,
            "trSeconds": meta["trSeconds"],
        },
        "maskUsed": {
            "file": "mask4_vt.nii.gz",
            "nilearnAttribute": "mask_vt",
            "nVoxels": n_voxel_cols,
            "description": (
                "Broad ventral-temporal cortex mask -- not face- or house-selective. "
                "Deliberately NOT mask8_face_vt.nii.gz / mask8_house_vt.nii.gz / mask8b_*_vt.nii.gz, "
                "which are voxel-selective for the exact face/house contrast this exercise evaluates "
                "and would make that comparison circular if used to choose voxels."
            ),
        },
        "extraction": {
            "script": "scripts/export_haxby_rsa_data.py",
            "perRunVoxelZScore": (
                "each retained voxel's BOLD time series is z-scored (mean 0, sd 1) within each run "
                "separately, using every TR of that run, before any block averaging"
            ),
            "blockDetection": "contiguous spans of identical per-TR condition label (labels.txt's labels column, grouped by its chunks run column)",
            "hrfOnsetTrsDropped": HRF_ONSET_TRS_DROPPED,
            "hrfOnsetRationale": (
                "the BOLD hemodynamic response lags neural/stimulus onset by several seconds; at this "
                "dataset's TR, a block's first TRs still partly reflect the preceding condition and are "
                "excluded from the category pattern rather than averaged in"
            ),
            "blockLengthsObservedTrs": meta["blockLenObserved"],
            "trsDroppedObserved": meta["trsDroppedObserved"],
            "categoryPatternDefinition": "mean of the z-scored voxel values over a block's retained (post-onset-drop) TRs -- one pattern per (run, category)",
            "note": "patterns are category-level, run-level averages; neither the original picture-by-picture presentation order nor a separate response per individual image survives this extraction.",
            "runsRetained": meta["runs"],
            "categories": meta["categories"],
            "exclusions": meta["exclusions"],
            "oddEvenCheck": {
                "oddRuns": meta["oddRuns"],
                "evenRuns": meta["evenRuns"],
                "eachSubsetCoversAllCategories": meta["oddEvenEachCoverAllCategories"],
            },
        },
        "derivedFile": {
            "path": "book/lite/files/data/haxby_rsa_patterns.csv",
            "sha256": derived_sha256,
            "nRows": meta["nRows"],
            "nVoxelColumns": n_voxel_cols,
            "columns": "run, category, then one voxel_#### column per retained ventral-temporal voxel",
        },
    }


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if manifest.get("schemaVersion") != 1:
        problems.append("schemaVersion must be 1")
    ds = manifest.get("dataset", {})
    if ds.get("sourceUrl") != DATASET_SOURCE_URL:
        problems.append("dataset.sourceUrl does not match the pinned source URL")
    if ds.get("subject") != SUBJECT:
        problems.append(f"dataset.subject must be {SUBJECT}")
    mask = manifest.get("maskUsed", {})
    if mask.get("file") != "mask4_vt.nii.gz":
        problems.append("maskUsed.file must be mask4_vt.nii.gz (the broad VT mask)")
    extraction = manifest.get("extraction", {})
    odd_even = extraction.get("oddEvenCheck", {})
    if not odd_even.get("eachSubsetCoversAllCategories"):
        problems.append("extraction.oddEvenCheck.eachSubsetCoversAllCategories must be true")
    derived = manifest.get("derivedFile", {})
    if not OUT_CSV.exists():
        problems.append(f"{OUT_CSV} is missing")
    else:
        on_disk_sha = sha256_hex(OUT_CSV.read_bytes())
        if derived.get("sha256") != on_disk_sha:
            problems.append("derivedFile.sha256 does not match the committed CSV's actual checksum")
    if derived.get("nVoxelColumns", 0) < 50:
        problems.append("derivedFile.nVoxelColumns looks implausibly small for a ventral-temporal mask")
    return problems


def cmd_refresh() -> int:
    frame, meta = build_patterns()
    derived_sha256 = write_csv(frame)
    manifest = build_manifest(meta, derived_sha256)
    problems = validate_manifest(manifest)
    if problems:
        print("ERROR: built manifest failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_CSV.relative_to(REPO_ROOT)} (sha256={derived_sha256})")
    print(f"wrote {OUT_MANIFEST.relative_to(REPO_ROOT)}")
    print(json.dumps(meta, indent=2))
    return 0


def cmd_check() -> int:
    if not OUT_MANIFEST.exists():
        print(f"ERROR: {OUT_MANIFEST} missing; run --refresh first.", file=sys.stderr)
        return 1
    manifest = json.loads(OUT_MANIFEST.read_text(encoding="utf-8"))
    problems = validate_manifest(manifest)
    if problems:
        print("ERROR: committed manifest/CSV failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    frame = pd.read_csv(OUT_CSV)
    expected_rows = manifest["derivedFile"]["nRows"]
    if len(frame) != expected_rows:
        problems.append(f"CSV has {len(frame)} rows, expected {expected_rows}")
    if sorted(frame["category"].unique()) != sorted(manifest["extraction"]["categories"]):
        problems.append("CSV categories do not match manifest.extraction.categories")
    if sorted(frame["run"].unique().tolist()) != sorted(manifest["extraction"]["runsRetained"]):
        problems.append("CSV runs do not match manifest.extraction.runsRetained")
    if problems:
        print("ERROR:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {OUT_MANIFEST.relative_to(REPO_ROOT)} and {OUT_CSV.relative_to(REPO_ROOT)} are valid.")
    print(f"  rows={len(frame)} runs={frame['run'].nunique()} categories={frame['category'].nunique()} voxel_cols={manifest['derivedFile']['nVoxelColumns']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="download via nilearn + verify + write the CSV/manifest (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed CSV/manifest offline")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
