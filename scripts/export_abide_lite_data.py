#!/usr/bin/env python3
"""Export the Exercise 2 age/brain table as a same-origin JupyterLite asset.

WP41 moves Exercise 2 into a JupyterLite notebook. That browser notebook must
load its data without any Git access, GitHub token, or repository visibility
(section 4.4) -- it cannot rely on ``urllib`` reaching a private-looking
raw.githubusercontent.com URL the way the old Jupyter Book notebook did. So
this script pre-computes the *exact* canonical-recipe table (see
``book/config/abide_modeling.json``: bundle "all-eligible", measure "CT",
target "age" -- 360 bilateral cortical-thickness columns, unchanged from the
approved recipe) once, offline from the student's point of view, and commits
it as a plain CSV under ``book/lite/files/data/``, where JupyterLite serves it
as an ordinary static file alongside the notebook.

The downloaded/Colab copy of the notebook does *not* get this file (the
download contract in section 3.3 only covers the .ipynb itself), so it still
falls back to the original pinned, checksummed network fetch. Both paths go
through the one small ``load_abide_age_brain_table`` helper embedded in the
notebook (see ``scripts/generate_exercise_02_notebook.py``), so the choice of
data source never appears in student-facing code.

A sidecar ``abide_age_brain.manifest.json`` records the exported file's
sha256, row count (participants), and column count (predictors, excluding the
target) so both this script's own ``--check`` and the notebook's own runtime
assertion can validate the table by checksum, schema, participant count, and
predictor count (section 4.4).

Modes:
  --write   (network) regenerate the CSV + manifest from the pinned source.
  --check   (offline) validate the committed CSV against its own manifest and
            against ``book/config/abide_modeling.json`` (360 predictors, the
            canonical recipe). No network.
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

from abide_modeling_data import (  # noqa: E402
    MANIFEST,
    feature_matrix,
    load_modeling_frame,
)

OUT_DIR = REPO_ROOT / "book" / "lite" / "files" / "data"
CSV_PATH = OUT_DIR / "abide_age_brain.csv"
SIDECAR_PATH = OUT_DIR / "abide_age_brain.manifest.json"

TARGET = "age"
BUNDLE = "all-eligible"
MEASURES = ["CT"]
EXPECTED_PREDICTOR_COUNT = 360


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def write() -> None:
    frame = load_modeling_frame()
    X, y, columns = feature_matrix(frame, BUNDLE, MEASURES, TARGET, MANIFEST)
    if len(columns) != EXPECTED_PREDICTOR_COUNT:
        raise SystemExit(
            f"canonical recipe produced {len(columns)} predictors, expected {EXPECTED_PREDICTOR_COUNT}"
        )
    # "group" (1=autism, 2=control) is not a predictor -- it never enters X --
    # but the notebook's established train/test split is stratified by it, so
    # it must travel with the export or the split could not be reproduced
    # bit-for-bit from this file alone.
    present = frame[TARGET].notna().to_numpy()
    group = frame.loc[present, "group"].to_numpy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([*columns, TARGET, "group"])
        for row_x, row_y, row_g in zip(X, y, group):
            writer.writerow([*(f"{v:.6f}" for v in row_x), f"{row_y:.6f}", f"{row_g:.0f}"])

    sidecar = {
        "schemaVersion": 1,
        "source": "book/config/abide_modeling.json canonical_recipe (bundle=all-eligible, measures=[CT], target=age)",
        "file": CSV_PATH.name,
        "sha256": _sha256(CSV_PATH),
        "participant_count": int(X.shape[0]),
        "predictor_count": int(X.shape[1]),
        "target_column": TARGET,
        "predictor_columns": columns,
        "extra_columns": ["group"],
        "extra_columns_note": "group (1=autism, 2=control) is not a predictor; it is only the stratification key for the established train/test split.",
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=2) + "\n")
    print(
        f"wrote {CSV_PATH.relative_to(REPO_ROOT)} "
        f"({sidecar['participant_count']} participants x {sidecar['predictor_count']} predictors)"
    )


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

    if header[-1] != "group":
        problems.append(f"last column {header[-1]!r} != 'group'")
    if header[-2] != sidecar["target_column"]:
        problems.append(f"second-to-last column {header[-2]!r} != target_column {sidecar['target_column']!r}")
    predictors = header[:-2]
    if predictors != sidecar["predictor_columns"]:
        problems.append("header predictor columns do not match manifest predictor_columns")
    if len(predictors) != sidecar["predictor_count"]:
        problems.append(f"predictor_count {len(predictors)} != manifest {sidecar['predictor_count']}")
    if len(predictors) != EXPECTED_PREDICTOR_COUNT:
        problems.append(f"predictor_count {len(predictors)} != canonical recipe {EXPECTED_PREDICTOR_COUNT}")
    if len(rows) != sidecar["participant_count"]:
        problems.append(f"row count {len(rows)} != manifest participant_count {sidecar['participant_count']}")

    recipe = MANIFEST["protocol"]["canonical_recipe"]
    if recipe["bundle"] != BUNDLE or recipe["measures"] != MEASURES:
        problems.append(
            f"manifest canonical_recipe {recipe['bundle']!r}/{recipe['measures']!r} "
            f"no longer matches this export's {BUNDLE!r}/{MEASURES!r}"
        )
    if MANIFEST["catalog"]["target"] != TARGET:
        problems.append(f"manifest catalog target {MANIFEST['catalog']['target']!r} != {TARGET!r}")

    if problems:
        raise SystemExit("abide_age_brain export check failed:\n- " + "\n- ".join(problems))
    print(f"OK: {CSV_PATH.relative_to(REPO_ROOT)} matches its manifest and the canonical recipe")


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
