#!/usr/bin/env python3
"""Deterministically export the ABIDE-II histogram activity data artifact.

The browser-native EDA histogram activity (``book/_static/widgets/``) must not
fetch the raw ABIDE-II phenotypic CSV at viewer runtime. This script pins that
CSV by URL + SHA-256, extracts only a small identifier-free set of numeric
columns, and writes a byte-for-byte deterministic JSON artifact that the widget
loads as a same-origin static file.

Two explicit modes:

* ``--refresh`` (network): download the pinned source, verify its SHA-256
  against ``SOURCE_SHA256``, rebuild the artifact, validate it, and write
  ``book/_static/widgets/data/abide_histogram.json``. If the upstream bytes do
  not match the pinned hash the script fails loudly and writes nothing.
* ``--check`` (offline): re-validate the committed artifact and confirm it is
  still byte-for-byte what this script would serialize. No network access.

A third helper, ``--print-upstream-hash``, downloads the source and prints its
current SHA-256 without writing anything, to support an intentional, reviewed
hash update (see ``interactive/README.md``).

Determinism guarantees for the artifact:

* fixed key ordering (``sort_keys=True``) and compact separators;
* integer-valued observations serialized as JSON integers, other finite numbers
  as JSON floats, missing observations as JSON ``null``;
* ``NaN``/``Infinity`` tokens are rejected (``allow_nan=False``);
* a single trailing newline; no timestamps or machine-specific paths.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

# --- Pinned provenance -------------------------------------------------------

# ABIDE-II phenotypic CSV, pinned to an immutable commit in the NeuroHackademy
# 2020 curriculum mirror (the same source the notebook used before WP03).
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "neurohackademy/nh2020-curriculum/"
    "e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/"
    "tu-machine-learning-yarkoni/data/abide2_phenotypic.csv"
)

# SHA-256 of the exact source bytes. To update this intentionally: run
# ``--print-upstream-hash``, review the upstream change, then edit this constant
# and re-run ``--refresh``. Never let the script normalize an unexpected change.
SOURCE_SHA256 = "537e541114884f63a2e736ba4d223a816dd013f701e56fb223ebe42e219e06f6"

SCHEMA_VERSION = 1

# Initial histogram variables (WP03 §2.6). All must be present in the local
# curated-column authority and in the source; none may look like an identifier.
HISTOGRAM_VARIABLES = [
    "AGE_AT_SCAN",
    "FIQ",
    "VIQ",
    "PIQ",
    "ADOS_G_TOTAL",
    "ADOS_2_TOTAL",
    "SRS_TOTAL_RAW",
    "SCQ_TOTAL",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_COLUMNS_PATH = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_histogram.json"

# Identifier-like column names are rejected outright (WP03 §2.11, Rule 11).
_IDENTIFIER_TOKEN = re.compile(
    r"(?:^|_)(?:ID|IDS|UID|GUID|MRN|SUB|SUBJECT|SUBID|PARTICIPANT|NAME|EMAIL|DOB)(?:$|_)",
    re.IGNORECASE,
)


# --- Pure helpers (unit-tested) -------------------------------------------------


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def looks_like_identifier(name: str) -> bool:
    """True if a column name looks like a participant/site identifier."""
    return bool(_IDENTIFIER_TOKEN.search(name))


def read_allowed_columns(path: Path) -> list[str]:
    """Read the local curated-column authority. Never fetched over the network."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(c, str) for c in raw):
        raise ValueError(f"{path} must be a JSON array of strings")
    return raw


def parse_csv(data: bytes) -> "Any":
    """Parse the ABIDE CSV bytes exactly as the notebook did (latin-1, stripped)."""
    import pandas as pd

    frame = pd.read_csv(io.BytesIO(data), encoding="latin-1", low_memory=False)
    frame.columns = frame.columns.str.strip()
    return frame


def _observation(value: Any) -> Any:
    """Coerce one cell to a JSON observation: int, float, or None.

    Missing -> None. Integer-valued -> int. Other finite -> float. NaN/inf raise.
    """
    import pandas as pd

    if value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite observation: {value!r}")
    if number.is_integer():
        return int(number)
    return number


def column_to_json_values(series: "Any") -> list[Any]:
    """Map a pandas Series to a list of int | float | None, in row order."""
    return [_observation(v) for v in series.tolist()]


def build_artifact(
    frame: "Any",
    variables: list[str],
    allowed_columns: list[str],
) -> dict[str, Any]:
    """Build the deterministic artifact dict from a parsed data frame."""
    allowed = set(allowed_columns)
    row_count = int(len(frame))

    for name in variables:
        if looks_like_identifier(name):
            raise ValueError(f"refusing to export identifier-like column: {name!r}")
        if name not in allowed:
            raise ValueError(
                f"{name!r} is not in the curated column authority "
                f"({ALLOWED_COLUMNS_PATH.name})"
            )
        if name not in frame.columns:
            raise ValueError(f"{name!r} is not present in the source CSV")

    columns: dict[str, list[Any]] = {}
    variable_meta: list[dict[str, Any]] = []
    for name in variables:
        values = column_to_json_values(frame[name])
        if len(values) != row_count:
            raise ValueError(f"column {name!r} length {len(values)} != row count {row_count}")
        available = sum(1 for v in values if v is not None)
        columns[name] = values
        variable_meta.append(
            {
                "name": name,
                "availableN": available,
                "missingN": row_count - available,
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "eda-histogram",
        "source": {
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "sourceRows": row_count,
            "sourceColumns": int(frame.shape[1]),
        },
        "rowCount": row_count,
        "variables": variable_meta,
        "columns": columns,
    }


def validate_artifact(artifact: Any, allowed_columns: list[str]) -> list[str]:
    """Return a list of human-readable problems. Empty list == valid."""
    problems: list[str] = []
    allowed = set(allowed_columns)

    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]

    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(
            f"schemaVersion must be {SCHEMA_VERSION}, got {artifact.get('schemaVersion')!r}"
        )

    row_count = artifact.get("rowCount")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 1:
        problems.append(f"rowCount must be a positive integer, got {row_count!r}")
        row_count = None

    columns = artifact.get("columns")
    if not isinstance(columns, dict) or not columns:
        problems.append("columns must be a non-empty object")
        columns = {}

    for name, values in columns.items():
        if looks_like_identifier(name):
            problems.append(f"identifier-like column present: {name!r}")
        if name not in allowed:
            problems.append(f"column {name!r} is not in the curated column authority")
        if not isinstance(values, list):
            problems.append(f"column {name!r} is not an array")
            continue
        if row_count is not None and len(values) != row_count:
            problems.append(
                f"column {name!r} has {len(values)} values, expected {row_count}"
            )
        for i, v in enumerate(values):
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                problems.append(f"column {name!r}[{i}] is not number-or-null: {v!r}")
                break
            if isinstance(v, float) and not math.isfinite(v):
                problems.append(f"column {name!r}[{i}] is non-finite: {v!r}")
                break

    source = artifact.get("source")
    if not isinstance(source, dict):
        problems.append("source metadata missing")
    else:
        if source.get("url") != SOURCE_URL:
            problems.append("source.url does not match the pinned SOURCE_URL")
        if source.get("sha256") != SOURCE_SHA256:
            problems.append("source.sha256 does not match the pinned SOURCE_SHA256")

    variables = artifact.get("variables")
    if not isinstance(variables, list) or not variables:
        problems.append("variables metadata must be a non-empty array")
    else:
        for meta in variables:
            if not isinstance(meta, dict):
                problems.append("variables entry is not an object")
                continue
            name = meta.get("name")
            if name not in columns:
                problems.append(f"variables entry {name!r} has no matching column")
                continue
            available = meta.get("availableN")
            missing = meta.get("missingN")
            if not isinstance(available, int) or isinstance(available, bool):
                problems.append(f"{name!r}.availableN must be an integer")
                continue
            if not isinstance(missing, int) or isinstance(missing, bool):
                problems.append(f"{name!r}.missingN must be an integer")
                continue
            actual_available = sum(1 for v in columns[name] if v is not None)
            if available != actual_available:
                problems.append(
                    f"{name!r}.availableN {available} != actual {actual_available}"
                )
            if row_count is not None and available + missing != row_count:
                problems.append(
                    f"{name!r}.availableN + missingN != rowCount ({available}+{missing})"
                )

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    """Byte-for-byte deterministic JSON text with a single trailing newline."""
    return (
        json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


# --- Modes -------------------------------------------------------------------


def fetch_source(url: str = SOURCE_URL) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 (pinned https)
        return response.read()


def _summary(artifact: dict[str, Any]) -> str:
    lines = [
        f"schemaVersion : {artifact['schemaVersion']}",
        f"rowCount      : {artifact['rowCount']}",
        f"source.sha256 : {artifact['source']['sha256']}",
        "variables     :",
    ]
    for meta in artifact["variables"]:
        lines.append(
            f"  {meta['name']:16} availableN={meta['availableN']:5} missingN={meta['missingN']:5}"
        )
    return "\n".join(lines)


def cmd_refresh() -> int:
    print(f"downloading {SOURCE_URL}")
    data = fetch_source()
    digest = sha256_hex(data)
    print(f"downloaded {len(data)} bytes, sha256={digest}")
    if digest != SOURCE_SHA256:
        print(
            "ERROR: upstream SHA-256 does not match the pinned SOURCE_SHA256.\n"
            f"  pinned  : {SOURCE_SHA256}\n"
            f"  upstream: {digest}\n"
            "Refusing to overwrite the committed teaching artifact. If this change "
            "is intentional, review it and update SOURCE_SHA256 in this script.",
            file=sys.stderr,
        )
        return 2

    allowed = read_allowed_columns(ALLOWED_COLUMNS_PATH)
    frame = parse_csv(data)
    artifact = build_artifact(frame, HISTOGRAM_VARIABLES, allowed)
    problems = validate_artifact(artifact, allowed)
    if problems:
        print("ERROR: built artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    text = serialize(artifact)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    print(f"artifact sha256: {sha256_hex(text.encode('utf-8'))}")
    print(_summary(artifact))
    return 0


def cmd_check() -> int:
    if not ARTIFACT_PATH.exists():
        print(f"ERROR: {ARTIFACT_PATH} does not exist; run --refresh first.", file=sys.stderr)
        return 1

    allowed = read_allowed_columns(ALLOWED_COLUMNS_PATH)
    on_disk = ARTIFACT_PATH.read_text(encoding="utf-8")

    try:
        artifact = json.loads(on_disk)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        print(f"ERROR: artifact is not valid JSON: {exc}", file=sys.stderr)
        return 1

    problems = validate_artifact(artifact, allowed)
    if problems:
        print("ERROR: committed artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    canonical = serialize(artifact)
    if canonical != on_disk:
        print(
            "ERROR: committed artifact is not in canonical deterministic form "
            "(re-serialization differs). Re-run --refresh.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {ARTIFACT_PATH.relative_to(REPO_ROOT)} is valid and canonical.")
    print(f"artifact sha256: {sha256_hex(on_disk.encode('utf-8'))}")
    print(_summary(artifact))
    return 0


def cmd_print_upstream_hash() -> int:
    data = fetch_source()
    print(f"bytes : {len(data)}")
    print(f"sha256: {sha256_hex(data)}")
    print(f"pinned: {SOURCE_SHA256}")
    print("match : " + ("yes" if sha256_hex(data) == SOURCE_SHA256 else "NO"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="download + verify + rewrite the artifact (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed artifact offline")
    mode.add_argument(
        "--print-upstream-hash",
        action="store_true",
        help="download the source and print its SHA-256 (no write)",
    )
    args = parser.parse_args(argv)

    if args.refresh:
        return cmd_refresh()
    if args.check:
        return cmd_check()
    return cmd_print_upstream_hash()


if __name__ == "__main__":
    raise SystemExit(main())
