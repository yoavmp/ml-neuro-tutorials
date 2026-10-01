#!/usr/bin/env python3
"""Export sex/site (plus a verification age column) as a same-origin
JupyterLite asset for Exercise 8 (WP47).

Exercise 8's unsupervised sections color a completed PCA/K-means plot by
diagnosis, sex, acquisition site, and age -- but never use any of those as
model inputs. ``book/lite/files/data/abide_age_brain.csv`` (the established
same-origin export Exercises 2, 4, 5, 6, and 7 already share) deliberately
carries only the 360 cortical-thickness predictors plus ``age``/``group``
(WP41 section 3: "keep exports slim -- only the columns a notebook actually
needs"), so it has no ``sex``/``site`` columns. Rather than widen that shared
file -- a change every other migrated exercise's committed checksum and tests
would have to absorb, which WP47's own scope explicitly avoids -- this script
exports a second, small, Exercise-8-only sidecar with exactly the two extra
fields, row-for-row aligned with the existing export.

Row alignment is not assumed: both this script and ``export_abide_lite_data.py``
start from the identical ``abide_modeling_data.load_modeling_frame()`` call,
filtered to the same ``age`` non-null mask, in the frame's own original order
(no sort/shuffle in either script) -- so the two exports are aligned by
construction. This script's own ``age`` column is included purely as a cheap,
explicit, row-by-row alignment check against the committed
``abide_age_brain.csv`` (both this script's ``--check`` and
``tests/test_export_abide_demographics_lite_data.py`` assert the two ``age``
columns match exactly), never as a value a notebook should read from this
file (notebooks read ``age`` from the existing brain table, as before).

The public-fallback path (a bare downloaded notebook or Colab, neither of
which has either sidecar file) needs no second URL: the one pinned,
checksummed ABIDE-II TSV every other exercise's fallback already points at
carries ``sex``/``site``/``age``/``group`` directly (verified directly against
the live source before writing this script -- see the WP47 report).

Modes:
  --write   (network) regenerate the CSV + manifest from the pinned source.
  --check   (offline) validate the committed CSV against its own manifest and
            against the committed abide_age_brain.csv's age column (same row
            order). No network.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from abide_modeling_data import load_modeling_frame  # noqa: E402

OUT_DIR = REPO_ROOT / "book" / "lite" / "files" / "data"
CSV_PATH = OUT_DIR / "abide_age_brain_demographics.csv"
SIDECAR_PATH = OUT_DIR / "abide_age_brain_demographics.manifest.json"
BRAIN_CSV_PATH = OUT_DIR / "abide_age_brain.csv"

TARGET = "age"
SEX_LABELS = {1: "Male", 2: "Female"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def write() -> None:
    frame = load_modeling_frame()
    present = frame[TARGET].notna().to_numpy()
    sub = frame.loc[present, ["age", "sex", "site"]].reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["age", "sex", "site"])
        for row in sub.itertuples(index=False):
            writer.writerow([f"{row.age:.6f}", f"{int(row.sex)}", row.site])

    sidecar = {
        "schemaVersion": 1,
        "source": "abide_modeling_data.load_modeling_frame(), filtered to age.notna() -- identical mask/order to export_abide_lite_data.py",
        "file": CSV_PATH.name,
        "sha256": _sha256(CSV_PATH),
        "participant_count": int(len(sub)),
        "columns": ["age", "sex", "site"],
        "sex_labels": SEX_LABELS,
        "alignment_note": (
            "Row-for-row aligned with the committed abide_age_brain.csv: this "
            "file's own 'age' column is included only to let --check and "
            "tests/test_export_abide_demographics_lite_data.py verify that "
            "alignment directly, never for a notebook to read 'age' from here."
        ),
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=2) + "\n")
    print(f"wrote {CSV_PATH.relative_to(REPO_ROOT)} ({sidecar['participant_count']} participants)")


def check() -> None:
    problems: list[str] = []
    if not CSV_PATH.exists() or not SIDECAR_PATH.exists():
        raise SystemExit(f"missing {CSV_PATH} or {SIDECAR_PATH}; run --write first")

    sidecar = json.loads(SIDECAR_PATH.read_text())
    actual_sha = _sha256(CSV_PATH)
    if actual_sha != sidecar["sha256"]:
        problems.append(f"checksum mismatch: file={actual_sha} manifest={sidecar['sha256']}")

    with CSV_PATH.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    if header != ["age", "sex", "site"]:
        problems.append(f"header {header!r} != ['age', 'sex', 'site']")
    if len(rows) != sidecar["participant_count"]:
        problems.append(f"row count {len(rows)} != manifest participant_count {sidecar['participant_count']}")

    if not BRAIN_CSV_PATH.exists():
        problems.append(f"{BRAIN_CSV_PATH} missing; cannot verify row alignment")
    else:
        with BRAIN_CSV_PATH.open() as f:
            brain_reader = csv.reader(f)
            brain_header = next(brain_reader)
            age_idx = brain_header.index("age")
            brain_ages = [r[age_idx] for r in brain_reader]
        demo_ages = [r[0] for r in rows]
        if len(brain_ages) != len(demo_ages):
            problems.append(f"row count differs from abide_age_brain.csv: {len(demo_ages)} vs {len(brain_ages)}")
        else:
            mismatches = sum(1 for a, b in zip(brain_ages, demo_ages) if a != b)
            if mismatches:
                problems.append(f"{mismatches} row(s) misaligned with abide_age_brain.csv's age column")

    if problems:
        raise SystemExit("abide_age_brain_demographics export check failed:\n- " + "\n- ".join(problems))
    print(f"OK: {CSV_PATH.relative_to(REPO_ROOT)} matches its manifest and is row-aligned with abide_age_brain.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenerate from the network (writes files)")
    group.add_argument("--check", action="store_true", help="validate committed files offline")
    args = parser.parse_args()
    if args.write:
        write()
    else:
        check()


if __name__ == "__main__":
    main()
