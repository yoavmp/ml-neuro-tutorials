#!/usr/bin/env python3
"""Build the compact, legally reusable UCI HAR course subset (WP38 sec 8.1).

Downloads and SHA-256-verifies the public UCI "Human Activity Recognition
Using Smartphones" archive, extracts participant id, activity label, and the
fixed 18-feature subset (``uci_har_data.FEATURE_SUBSET``), and writes:

* ``book/data/uci_har/uci_har_compact.csv.gz`` -- the compact derived table
  (10,299 rows: train + test recombined, in the original archive's row
  order), compressed;
* ``book/data/uci_har/provenance.json`` -- dataset title/authors, source URL,
  DOI, CC BY 4.0 attribution, original archive version/date, original
  archive checksum, this extraction script's path, and the derived file's
  own checksum.

This is a maintainer-only, explicit refresh path. Notebook execution and CI
are always offline and use only the committed compact table
(``uci_har_data.load_compact_table``); this script's network mode is never
invoked automatically.

Modes (exactly one required):

* ``--refresh``  (network): download the archive, verify checksums, extract,
  build and write the compact table + provenance.
* ``--check``    (offline): re-validate the committed compact table and
  provenance for internal consistency and the checksums they claim about
  each other. No network access.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uci_har_data import (  # noqa: E402
    ACTIVITY_LABELS,
    COMPACT_CSV_PATH,
    COMPACT_COLUMNS,
    DATA_DIR,
    FEATURE_SUBSET,
    PROVENANCE_PATH,
    REPO_ROOT,
    sha256_hex,
)

ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip"
ARCHIVE_SHA256 = "c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031"
INNER_ARCHIVE_NAME = "UCI HAR Dataset.zip"
INNER_ARCHIVE_SHA256 = "2045e435c955214b38145fb5fa00776c72814f01b203fec405152dac7d5bfeb0"
ARCHIVE_VERSION = "Version 1.0 (per the archive's own README.txt)"

DATASET_TITLE = "Human Activity Recognition Using Smartphones"
DATASET_AUTHORS = (
    "Jorge L. Reyes-Ortiz, Davide Anguita, Alessandro Ghio, Luca Oneto, Xavier Parra"
)
DATASET_SOURCE_URL = "https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones"
DATASET_DOI = "https://doi.org/10.24432/C54S4K"
DATASET_LICENSE = "CC BY 4.0"


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=180) as response:  # noqa: S310 (pinned https)
        return response.read()


def _extract_split(zf: zipfile.ZipFile, split: str, feature_positions: list[int]) -> Any:
    import pandas as pd

    base = f"UCI HAR Dataset/{split}"
    with zf.open(f"{base}/X_{split}.txt") as fh:
        X_full = pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8"), sep=r"\s+", header=None)
    with zf.open(f"{base}/y_{split}.txt") as fh:
        y = pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8"), header=None, names=["activity_id"])
    with zf.open(f"{base}/subject_{split}.txt") as fh:
        subject = pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8"), header=None, names=["participant_id"])

    subset = X_full[feature_positions].copy()
    subset.columns = list(FEATURE_SUBSET)
    out = pd.concat([subject, y, subset], axis=1)
    out["activity_label"] = out["activity_id"].map(ACTIVITY_LABELS)
    return out[list(COMPACT_COLUMNS)]


def build_compact_table() -> tuple[Any, dict[str, Any]]:
    """Download + verify the archive; return (compact_dataframe, extraction_meta)."""
    outer_bytes = _fetch(ARCHIVE_URL)
    outer_digest = sha256_hex(outer_bytes)
    if outer_digest != ARCHIVE_SHA256:
        raise RuntimeError(f"outer archive SHA-256 {outer_digest} does not match pinned {ARCHIVE_SHA256}")

    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer_zf:
        inner_bytes = outer_zf.read(INNER_ARCHIVE_NAME)
    inner_digest = sha256_hex(inner_bytes)
    if inner_digest != INNER_ARCHIVE_SHA256:
        raise RuntimeError(f"inner archive SHA-256 {inner_digest} does not match pinned {INNER_ARCHIVE_SHA256}")

    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner_zf:
        with inner_zf.open("UCI HAR Dataset/features.txt") as fh:
            import pandas as pd

            features = pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8"), sep=r"\s+", header=None, names=["idx", "name"])
        name_to_first_position: dict[str, int] = {}
        for i, n in enumerate(features["name"].tolist()):
            name_to_first_position.setdefault(n, i)
        missing_names = [n for n in FEATURE_SUBSET if n not in name_to_first_position]
        if missing_names:
            raise RuntimeError(f"archive is missing expected official feature name(s): {missing_names}")
        feature_positions = [name_to_first_position[n] for n in FEATURE_SUBSET]

        train = _extract_split(inner_zf, "train", feature_positions)
        test = _extract_split(inner_zf, "test", feature_positions)

    import pandas as pd

    compact = pd.concat([train, test], ignore_index=True)

    meta = {
        "outerArchiveSha256": outer_digest,
        "innerArchiveSha256": inner_digest,
        "featurePositions0Indexed": feature_positions,
        "nRows": int(len(compact)),
        "nParticipants": int(compact["participant_id"].nunique()),
        "nActivities": int(compact["activity_id"].nunique()),
    }
    return compact, meta


def write_compact_table(compact: Any, path: Path = COMPACT_CSV_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_text = compact.to_csv(index=False, lineterminator="\n")
    with gzip.GzipFile(path, mode="wb", mtime=0) as gz:
        gz.write(csv_text.encode("utf-8"))
    return sha256_hex(path.read_bytes())


def build_provenance(meta: dict[str, Any], derived_sha256: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "dataset": {
            "title": DATASET_TITLE,
            "authors": DATASET_AUTHORS,
            "sourceUrl": DATASET_SOURCE_URL,
            "doi": DATASET_DOI,
            "license": DATASET_LICENSE,
            "archiveVersion": ARCHIVE_VERSION,
        },
        "originalArchive": {
            "url": ARCHIVE_URL,
            "sha256": ARCHIVE_SHA256,
            "innerArchiveName": INNER_ARCHIVE_NAME,
            "innerArchiveSha256": INNER_ARCHIVE_SHA256,
        },
        "extraction": {
            "script": "scripts/export_uci_har_data.py",
            "chosenColumns": list(COMPACT_COLUMNS),
            "featureSubset": list(FEATURE_SUBSET),
            "featurePositions0Indexed": meta["featurePositions0Indexed"],
            "note": (
                "participant_id, activity_id, activity_label, and the 18 official "
                "feature columns below are read directly from X_{split}.txt / "
                "y_{split}.txt / subject_{split}.txt for split in (train, test) and "
                "concatenated train-then-test, in each split's original row order. "
                "No target-informed selection: the 18 columns were chosen in advance "
                "by measurement family (mean/std of body acceleration, gravity "
                "acceleration, and body angular velocity on each axis), not by "
                "predictive performance."
            ),
        },
        "derivedFile": {
            "path": "book/data/uci_har/uci_har_compact.csv.gz",
            "sha256": derived_sha256,
            "nRows": meta["nRows"],
            "nParticipants": meta["nParticipants"],
            "nActivities": meta["nActivities"],
        },
    }


def validate_provenance(provenance: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if provenance.get("schemaVersion") != 1:
        problems.append("schemaVersion must be 1")
    ds = provenance.get("dataset", {})
    if ds.get("sourceUrl") != DATASET_SOURCE_URL:
        problems.append("dataset.sourceUrl does not match the pinned source URL")
    if ds.get("doi") != DATASET_DOI:
        problems.append("dataset.doi does not match the pinned DOI")
    if ds.get("license") != DATASET_LICENSE:
        problems.append("dataset.license must be CC BY 4.0")
    arc = provenance.get("originalArchive", {})
    if arc.get("sha256") != ARCHIVE_SHA256:
        problems.append("originalArchive.sha256 does not match the pinned archive checksum")
    if arc.get("innerArchiveSha256") != INNER_ARCHIVE_SHA256:
        problems.append("originalArchive.innerArchiveSha256 does not match the pinned inner-archive checksum")
    ext = provenance.get("extraction", {})
    if ext.get("featureSubset") != list(FEATURE_SUBSET):
        problems.append("extraction.featureSubset does not match uci_har_data.FEATURE_SUBSET")
    derived = provenance.get("derivedFile", {})
    if not COMPACT_CSV_PATH.exists():
        problems.append(f"{COMPACT_CSV_PATH} is missing")
    else:
        on_disk_sha = sha256_hex(COMPACT_CSV_PATH.read_bytes())
        if derived.get("sha256") != on_disk_sha:
            problems.append("derivedFile.sha256 does not match the committed compact table's actual checksum")
    if derived.get("nRows") != 10299:
        problems.append("derivedFile.nRows must be 10299 (the full archive's window count)")
    if derived.get("nParticipants") != 30:
        problems.append("derivedFile.nParticipants must be 30")
    if derived.get("nActivities") != 6:
        problems.append("derivedFile.nActivities must be 6")
    return problems


def cmd_refresh() -> int:
    compact, meta = build_compact_table()
    derived_sha256 = write_compact_table(compact)
    provenance = build_provenance(meta, derived_sha256)
    problems = validate_provenance(provenance)
    if problems:
        print("ERROR: built provenance failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {COMPACT_CSV_PATH.relative_to(REPO_ROOT)} (sha256={derived_sha256})")
    print(f"wrote {PROVENANCE_PATH.relative_to(REPO_ROOT)}")
    print(json.dumps(meta, indent=2))
    return 0


def cmd_check() -> int:
    if not PROVENANCE_PATH.exists():
        print(f"ERROR: {PROVENANCE_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    problems = validate_provenance(provenance)
    if problems:
        print("ERROR: committed provenance/compact table failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    from uci_har_data import load_compact_table

    frame = load_compact_table()
    if len(frame) != 10299:
        problems.append(f"compact table has {len(frame)} rows, expected 10299")
    if frame["participant_id"].nunique() != 30:
        problems.append("compact table does not have exactly 30 participants")
    if sorted(frame["activity_id"].unique()) != sorted(ACTIVITY_LABELS):
        problems.append("compact table activity ids do not match ACTIVITY_LABELS")
    if problems:
        print("ERROR:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {PROVENANCE_PATH.relative_to(REPO_ROOT)} and {COMPACT_CSV_PATH.relative_to(REPO_ROOT)} are valid.")
    print(f"  rows={len(frame)} participants={frame['participant_id'].nunique()} activities={frame['activity_id'].nunique()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="download + verify + write the compact table (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed compact table offline")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
