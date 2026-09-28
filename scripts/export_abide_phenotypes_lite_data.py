#!/usr/bin/env python3
"""Export Exercise 1's curated phenotype table as a same-origin JupyterLite asset.

WP42 Gate 2 moves Exercise 1 into a JupyterLite notebook, which must load its
data without Git access, a GitHub token, or repository visibility (same
constraint WP41 solved for Exercise 2 -- see export_abide_lite_data.py).

Rather than re-fetching the pinned upstream CSV over the network (a second,
independent path that could drift from the already-approved values), this
script derives the export OFFLINE from the already-committed, already-
validated ``abide_table_inspection.json`` (see export_widget_data.py), which
holds exactly the 13-column curated teaching table
(book/config/eda_phenotype_columns.json) in
``book/_static/widgets/data/abide_table_inspection.json``'s own established
column order. This guarantees the notebook's table is byte-identical in
content to what the existing browser-native EDA widgets already show,
without a second network fetch that could disagree with it.

A sidecar ``abide_phenotypes.manifest.json`` records the exported file's
sha256, row count, and column list so both this script's own ``--check`` and
the notebook's own runtime assertion can validate the table (schema +
checksum + row count), the same contract WP41's data export uses.

Modes:
  --write   (offline) rebuild the CSV + manifest from the committed
            table-inspection artifact.
  --check   (offline) validate the committed CSV against its own manifest and
            against the curated column authority. No network, either mode.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CURATED_COLUMNS_PATH = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
SOURCE_ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_table_inspection.json"

OUT_DIR = REPO_ROOT / "book" / "lite" / "files" / "data"
CSV_PATH = OUT_DIR / "abide_phenotypes.csv"
SIDECAR_PATH = OUT_DIR / "abide_phenotypes.manifest.json"

EXPECTED_ROW_COUNT = 1114


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_curated_columns() -> list[str]:
    return json.loads(CURATED_COLUMNS_PATH.read_text())


def _rows_from_source(columns: list[str]) -> list[list]:
    source = json.loads(SOURCE_ARTIFACT_PATH.read_text())
    if source["columnOrder"] != columns:
        raise SystemExit(
            "abide_table_inspection.json column order no longer matches "
            "eda_phenotype_columns.json -- update this script's assumptions"
        )
    n = source["rowCount"]
    column_values = {name: source["columns"][name] for name in columns}
    rows = []
    for i in range(n):
        rows.append(["" if column_values[name][i] is None else column_values[name][i] for name in columns])
    return rows


def write() -> None:
    columns = _load_curated_columns()
    rows = _rows_from_source(columns)
    if len(rows) != EXPECTED_ROW_COUNT:
        raise SystemExit(f"expected {EXPECTED_ROW_COUNT} rows, got {len(rows)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    sidecar = {
        "schemaVersion": 1,
        "source": "book/_static/widgets/data/abide_table_inspection.json (already-approved curated 13-column teaching table)",
        "file": CSV_PATH.name,
        "sha256": _sha256(CSV_PATH),
        "row_count": len(rows),
        "columns": columns,
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, indent=2) + "\n")
    print(f"wrote {CSV_PATH.relative_to(REPO_ROOT)} ({sidecar['row_count']} rows x {len(columns)} columns)")


def check() -> None:
    problems: list[str] = []
    if not CSV_PATH.exists() or not SIDECAR_PATH.exists():
        raise SystemExit(f"missing {CSV_PATH} or {SIDECAR_PATH}; run --write first")

    sidecar = json.loads(SIDECAR_PATH.read_text())
    actual_sha = _sha256(CSV_PATH)
    if actual_sha != sidecar["sha256"]:
        problems.append(f"checksum mismatch: file={actual_sha} manifest={sidecar['sha256']}")

    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    columns = _load_curated_columns()
    if header != columns:
        problems.append("CSV header does not match book/config/eda_phenotype_columns.json")
    if header != sidecar["columns"]:
        problems.append("CSV header does not match manifest columns")
    if len(rows) != sidecar["row_count"]:
        problems.append(f"row count {len(rows)} != manifest row_count {sidecar['row_count']}")
    if len(rows) != EXPECTED_ROW_COUNT:
        problems.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    if problems:
        raise SystemExit("abide_phenotypes export check failed:\n- " + "\n- ".join(problems))
    print(f"OK: {CSV_PATH.relative_to(REPO_ROOT)} matches its manifest and the curated column authority")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenerate from the committed table-inspection artifact")
    group.add_argument("--check", action="store_true", help="validate committed files offline")
    args = parser.parse_args()
    if args.write:
        write()
    else:
        check()


if __name__ == "__main__":
    main()
