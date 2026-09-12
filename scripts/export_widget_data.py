#!/usr/bin/env python3
"""Deterministically export the ABIDE-II browser-activity data artifacts.

The browser-native EDA activities (``book/_static/widgets/``) must not fetch the
raw ABIDE-II phenotypic CSV at viewer runtime. This script pins that CSV by URL
+ SHA-256, extracts only a small, mostly identifier-free set of columns, and
writes byte-for-byte deterministic JSON artifacts that the widgets load as
same-origin static files.

Three artifacts are produced from the *same* pinned source:

* ``abide_histogram.json`` (activity ``eda-histogram``, WP03): the seven numeric
  variables of the curated teaching table, no identifier of any kind.
* ``abide_retention.json`` (activity ``eda-retention``, WP04): the approved
  complete-case candidate variables **plus** ``SITE_ID``. ``SITE_ID`` is the
  only identifier-shaped field allowed in the histogram/retention artifacts, and
  only in the retention artifact, because grouped retention summaries are
  impossible without a site-grouping label. It is a coarse, non-personal
  acquisition-site code; ``SUB_ID`` and every other participant identifier stay
  rejected here. The same retention artifact also backs the ``eda-correlation``
  activity.
* ``abide_table_inspection.json`` (activity ``table-inspection``, WP09 §11 /
  WP10 §2): every column of the 13-column curated teaching table, in the exact
  order of ``book/config/eda_phenotype_columns.json``. This activity shows real
  rows of the curated table so a student can compare what ``head()``, ``tail()``
  and ``sample()`` return, which means it needs the two identifier-shaped
  string columns ``SITE_ID`` and ``SUB_ID`` as non-selectable display columns.
  That two-name exception is confined to this one artifact; every other column
  is still a curated, non-identifier variable.

Modes:

* ``--refresh`` (network): download the pinned source, verify its SHA-256
  against ``SOURCE_SHA256``, rebuild the selected artifact(s), validate, and
  write. If the upstream bytes do not match the pinned hash the script fails
  loudly and writes nothing.
* ``--check`` (offline): re-validate the committed artifact(s) and confirm each
  is still byte-for-byte what this script would serialize. No network access.
* ``--print-upstream-hash`` (network): download the source and print its current
  SHA-256 without writing anything, to support an intentional, reviewed hash
  update (see ``interactive/README.md``).

``--artifact {histogram,retention,table-inspection,all}`` (default ``all``)
scopes ``--refresh`` and ``--check``. The bare WP03 invocations ``--refresh`` /
``--check`` keep working and now cover *all three* artifacts. Each named
selector only ever touches its own file -- refreshing one cannot rewrite or
delete another.

Determinism guarantees for every artifact:

* fixed key ordering (``sort_keys=True``) and compact separators;
* integer-valued observations serialized as JSON integers, other finite numbers
  as JSON floats, missing observations as JSON ``null``, documented category
  strings preserved verbatim;
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

# Histogram variables (WP03 §2.6, retrimmed in WP09 §7). All must be present in
# the local curated column authority and in the source; none may look like an
# identifier. These are exactly the numeric columns of the 13-column curated
# teaching table.
HISTOGRAM_VARIABLES = [
    "AGE_AT_SCAN",
    "FIQ",
    "VIQ",
    "PIQ",
    "SRS_TOTAL_RAW",
    "ADOS_G_TOTAL",
    "ADI_R_SOCIAL_TOTAL_A",
]

# Complete-case retention candidate variables (WP04 §"Candidate variables",
# retrimmed in WP09 §7 to the 13-column curated teaching table minus the two
# identifiers SITE_ID/SUB_ID; SITE_ID is re-added below as the grouping label).
# Grouped in the config; the export just needs the flat, ordered list. Each is
# in the curated authority and in the pinned source. Categorical variables are
# coded as integers in this source (DX_GROUP 1/2, SEX 1/2,
# HANDEDNESS_CATEGORY 1/2/3, CURRENT_MED_STATUS 0/1) and are exported as those
# documented codes, never imputed.
RETENTION_VARIABLES = [
    "DX_GROUP",
    "AGE_AT_SCAN",
    "SEX",
    "HANDEDNESS_CATEGORY",
    "FIQ",
    "VIQ",
    "PIQ",
    "CURRENT_MED_STATUS",
    "SRS_TOTAL_RAW",
    "ADOS_G_TOTAL",
    "ADI_R_SOCIAL_TOTAL_A",
]

# The single, deliberately narrow exception to identifier rejection. Only this
# exact name, and only in the retention artifact, is allowed through as a
# non-personal site-grouping label. Anything else identifier-shaped is refused.
SITE_FIELD = "SITE_ID"

# The ``table-inspection`` activity (WP09 §11, widened to the full curated table
# in WP10 §2) shows real rows of the curated table, so it needs both the
# site-grouping label and the study-assigned participant id ``SUB_ID`` -- seeing
# the identifier column is part of what head()/tail()/sample() are being
# compared on. These two exact names, and only in the table-inspection artifact,
# are allowed through as non-selectable string display columns.
TABLE_INSPECTION_IDENTIFIER_FIELDS = ("SITE_ID", "SUB_ID")

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_COLUMNS_PATH = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
WIDGET_DATA_DIR = REPO_ROOT / "book" / "_static" / "widgets" / "data"
HISTOGRAM_ARTIFACT_PATH = WIDGET_DATA_DIR / "abide_histogram.json"
RETENTION_ARTIFACT_PATH = WIDGET_DATA_DIR / "abide_retention.json"
TABLE_INSPECTION_ARTIFACT_PATH = WIDGET_DATA_DIR / "abide_table_inspection.json"

# Backwards-compatible alias for WP03 callers / tests.
ARTIFACT_PATH = HISTOGRAM_ARTIFACT_PATH

# Identifier-like column names are rejected outright (Rule 11). ``SITE_ID`` also
# matches this pattern by design; the retention builder/validator waves through
# *only* that exact name via an explicit allowlist argument.
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


def _site_label(value: Any) -> str:
    """Coerce one site cell to a non-empty string. Missing is rejected."""
    import pandas as pd

    if value is None or pd.isna(value):
        raise ValueError("SITE_ID has a missing value; site grouping requires a label on every row")
    text = str(value).strip()
    if not text:
        raise ValueError("SITE_ID has a blank value; site grouping requires a label on every row")
    return text


def _identifier_label(value: Any, field: str) -> str:
    """Coerce one identifier cell to a non-empty string. Missing is rejected.

    Integer ids (``SUB_ID`` is ``29006`` etc. in the source) are rendered
    without a trailing ``.0`` so the value matches the notebook's
    ``astype("string")`` display.
    """
    import pandas as pd

    if value is None or pd.isna(value):
        raise ValueError(f"{field} has a missing value; every displayed row needs one")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} has a blank value; every displayed row needs one")
    return text


def column_to_json_values(series: "Any") -> list[Any]:
    """Map a pandas Series to a list of int | float | None, in row order."""
    return [_observation(v) for v in series.tolist()]


def _check_exportable(name: str, allowed: set[str], frame: "Any") -> None:
    """Shared per-variable guard: not an identifier, curated, present in source."""
    if looks_like_identifier(name):
        raise ValueError(f"refusing to export identifier-like column: {name!r}")
    if name not in allowed:
        raise ValueError(
            f"{name!r} is not in the curated column authority "
            f"({ALLOWED_COLUMNS_PATH.name})"
        )
    if name not in frame.columns:
        raise ValueError(f"{name!r} is not present in the source CSV")


def build_artifact(
    frame: "Any",
    variables: list[str],
    allowed_columns: list[str],
) -> dict[str, Any]:
    """Build the deterministic histogram artifact dict from a parsed data frame."""
    allowed = set(allowed_columns)
    row_count = int(len(frame))

    for name in variables:
        _check_exportable(name, allowed, frame)

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


def build_retention_artifact(
    frame: "Any",
    variables: list[str],
    allowed_columns: list[str],
    site_field: str = SITE_FIELD,
) -> dict[str, Any]:
    """Build the deterministic complete-case retention artifact dict.

    Columns are ``site_field`` (documented strings, no missing) followed by the
    candidate ``variables`` (documented codes / numbers, ``null`` for missing).
    """
    allowed = set(allowed_columns)
    row_count = int(len(frame))

    if site_field != SITE_FIELD:
        raise ValueError(
            f"the retention artifact only permits {SITE_FIELD!r} as its site field, got {site_field!r}"
        )
    if site_field not in allowed:
        raise ValueError(f"{site_field!r} is not in the curated column authority")
    if site_field not in frame.columns:
        raise ValueError(f"{site_field!r} is not present in the source CSV")

    for name in variables:
        if name == site_field:
            raise ValueError(f"{site_field!r} is the site grouping label, not a selectable variable")
        _check_exportable(name, allowed, frame)

    site_values = [_site_label(v) for v in frame[site_field].tolist()]
    if len(site_values) != row_count:
        raise ValueError(f"site column length {len(site_values)} != row count {row_count}")

    columns: dict[str, list[Any]] = {site_field: site_values}
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

    # Deterministic site metadata, ordered by first appearance in the source.
    site_totals: dict[str, int] = {}
    for label in site_values:
        site_totals[label] = site_totals.get(label, 0) + 1
    sites_meta = [{"label": label, "total": total} for label, total in site_totals.items()]

    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "eda-retention",
        "source": {
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "sourceRows": row_count,
            "sourceColumns": int(frame.shape[1]),
        },
        "rowCount": row_count,
        "site": {
            "field": site_field,
            "siteCount": len(sites_meta),
            "sites": sites_meta,
        },
        "variables": variable_meta,
        "columns": columns,
    }


def build_table_inspection_artifact(
    frame: "Any",
    allowed_columns: list[str],
    identifier_fields: tuple[str, ...] = TABLE_INSPECTION_IDENTIFIER_FIELDS,
) -> dict[str, Any]:
    """Build the deterministic ``table-inspection`` artifact.

    The displayed columns are derived directly from the curated column authority
    (``allowed_columns``) so the artifact -- and the activity config tested
    against it -- can never drift from the canonical 13-column list. Exactly the
    two names in ``identifier_fields`` (``SITE_ID``, ``SUB_ID``) are emitted as
    non-empty strings; every other curated column is emitted as documented
    codes / numbers / ``null`` just like the retention artifact.
    """
    allowed = set(allowed_columns)
    row_count = int(len(frame))

    id_fields = tuple(identifier_fields)
    if id_fields != TABLE_INSPECTION_IDENTIFIER_FIELDS:
        raise ValueError(
            f"the table-inspection artifact only permits "
            f"{TABLE_INSPECTION_IDENTIFIER_FIELDS} as identifier columns, got {id_fields!r}"
        )
    for field in id_fields:
        if field not in allowed:
            raise ValueError(f"{field!r} is not in the curated column authority")
        if field not in frame.columns:
            raise ValueError(f"{field!r} is not present in the source CSV")

    variable_names = [c for c in allowed_columns if c not in id_fields]
    for name in variable_names:
        _check_exportable(name, allowed, frame)

    columns: dict[str, list[Any]] = {}
    for field in id_fields:
        labels = [_identifier_label(v, field) for v in frame[field].tolist()]
        if len(labels) != row_count:
            raise ValueError(f"identifier column {field!r} length {len(labels)} != row count {row_count}")
        columns[field] = labels

    variable_meta: list[dict[str, Any]] = []
    for name in variable_names:
        values = column_to_json_values(frame[name])
        if len(values) != row_count:
            raise ValueError(f"column {name!r} length {len(values)} != row count {row_count}")
        available = sum(1 for v in values if v is not None)
        columns[name] = values
        variable_meta.append(
            {"name": name, "availableN": available, "missingN": row_count - available}
        )

    site_field = id_fields[0]
    site_values = columns[site_field]
    site_totals: dict[str, int] = {}
    for label in site_values:
        site_totals[label] = site_totals.get(label, 0) + 1
    sites_meta = [{"label": label, "total": total} for label, total in site_totals.items()]

    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "table-inspection",
        "source": {
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "sourceRows": row_count,
            "sourceColumns": int(frame.shape[1]),
        },
        "rowCount": row_count,
        "columnOrder": list(allowed_columns),
        "identifierFields": list(id_fields),
        "site": {
            "field": site_field,
            "siteCount": len(sites_meta),
            "sites": sites_meta,
        },
        "variables": variable_meta,
        "columns": columns,
    }


def validate_table_inspection_artifact(
    artifact: Any,
    allowed_columns: list[str],
    identifier_fields: tuple[str, ...] = TABLE_INSPECTION_IDENTIFIER_FIELDS,
) -> list[str]:
    """Return human-readable problems for the ``table-inspection`` artifact.

    Enforces: ``columnOrder`` equals the curated authority exactly (order
    included); the column set matches ``columnOrder``; the two identifier
    columns are non-empty strings with no missing value; every other column is
    a curated, non-identifier number/null array; ``site`` and ``variables``
    metadata agree with the data.
    """
    allowed = set(allowed_columns)
    problems, row_count, columns = _validate_common(artifact, allowed, "table-inspection")
    if not isinstance(artifact, dict):
        return problems

    id_fields = tuple(identifier_fields)
    if id_fields != TABLE_INSPECTION_IDENTIFIER_FIELDS:
        problems.append(f"identifier fields must be {TABLE_INSPECTION_IDENTIFIER_FIELDS}, got {id_fields!r}")
    if artifact.get("identifierFields") != list(id_fields):
        problems.append(
            f"identifierFields must be {list(id_fields)!r}, got {artifact.get('identifierFields')!r}"
        )

    column_order = artifact.get("columnOrder")
    if column_order != list(allowed_columns):
        problems.append(
            "columnOrder must equal the curated column authority exactly "
            f"({allowed_columns!r}), got {column_order!r}"
        )
    elif set(columns) != set(column_order):
        problems.append(
            f"columns keys {sorted(columns)!r} do not match columnOrder {column_order!r}"
        )

    for name, values in columns.items():
        if name in id_fields:
            if not isinstance(values, list):
                problems.append(f"identifier column {name!r} is not an array")
                continue
            if row_count is not None and len(values) != row_count:
                problems.append(f"column {name!r} has {len(values)} values, expected {row_count}")
            for i, v in enumerate(values):
                if not isinstance(v, str) or v.strip() == "":
                    problems.append(f"identifier column {name!r}[{i}] is not a non-empty string: {v!r}")
                    break
            continue
        if looks_like_identifier(name):
            problems.append(f"identifier-like column present: {name!r}")
        if name not in allowed:
            problems.append(f"column {name!r} is not in the curated column authority")
        _validate_numeric_column(name, values, row_count, problems)

    _validate_variable_meta(artifact.get("variables"), columns, row_count, problems)
    # variables metadata must cover exactly the non-identifier columns.
    meta_names = {m.get("name") for m in artifact.get("variables", []) if isinstance(m, dict)}
    expected_var_names = {c for c in allowed_columns if c not in id_fields}
    if meta_names != expected_var_names:
        problems.append(
            f"variables metadata {sorted(meta_names)!r} must be exactly the "
            f"non-identifier curated columns {sorted(expected_var_names)!r}"
        )

    site_meta = artifact.get("site")
    site_field = id_fields[0]
    if not isinstance(site_meta, dict):
        problems.append("site metadata must be an object")
    elif site_field in columns and isinstance(columns[site_field], list):
        first_seen: dict[str, int] = {}
        for label in columns[site_field]:
            if isinstance(label, str):
                first_seen[label] = first_seen.get(label, 0) + 1
        if site_meta.get("field") != site_field:
            problems.append(f"site.field must be {site_field!r}, got {site_meta.get('field')!r}")
        if site_meta.get("siteCount") != len(first_seen):
            problems.append(
                f"site.siteCount {site_meta.get('siteCount')!r} != distinct labels {len(first_seen)}"
            )
        sites = site_meta.get("sites")
        if not isinstance(sites, list) or len(sites) != len(first_seen):
            problems.append("site.sites must list every distinct site exactly once")
        else:
            if [s.get("label") if isinstance(s, dict) else None for s in sites] != list(first_seen.keys()):
                problems.append("site.sites is not in first-appearance order of the SITE_ID column")
            total_sum = 0
            for s in sites:
                if not isinstance(s, dict):
                    continue
                if not isinstance(s.get("total"), int) or isinstance(s.get("total"), bool):
                    problems.append(f"site {s.get('label')!r}.total must be an integer")
                    continue
                if first_seen.get(s.get("label")) != s.get("total"):
                    problems.append(f"site {s.get('label')!r}.total {s.get('total')} != actual {first_seen.get(s.get('label'))}")
                total_sum += s["total"]
            if row_count is not None and total_sum != row_count:
                problems.append(f"site totals sum to {total_sum}, expected rowCount {row_count}")

    return problems


def _validate_common(artifact: Any, allowed: set[str], expected_activity: str) -> tuple[list[str], int | None, dict[str, Any]]:
    """Shared schemaVersion / activity / rowCount / columns-shape checks."""
    problems: list[str] = []

    if not isinstance(artifact, dict):
        return (["artifact is not a JSON object"], None, {})

    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(
            f"schemaVersion must be {SCHEMA_VERSION}, got {artifact.get('schemaVersion')!r}"
        )
    if artifact.get("activity") != expected_activity:
        problems.append(
            f"activity must be {expected_activity!r}, got {artifact.get('activity')!r}"
        )

    row_count = artifact.get("rowCount")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 1:
        problems.append(f"rowCount must be a positive integer, got {row_count!r}")
        row_count = None

    columns = artifact.get("columns")
    if not isinstance(columns, dict) or not columns:
        problems.append("columns must be a non-empty object")
        columns = {}

    source = artifact.get("source")
    if not isinstance(source, dict):
        problems.append("source metadata missing")
    else:
        if source.get("url") != SOURCE_URL:
            problems.append("source.url does not match the pinned SOURCE_URL")
        if source.get("sha256") != SOURCE_SHA256:
            problems.append("source.sha256 does not match the pinned SOURCE_SHA256")

    return (problems, row_count, columns)


def _validate_numeric_column(name: str, values: Any, row_count: int | None, problems: list[str]) -> None:
    if not isinstance(values, list):
        problems.append(f"column {name!r} is not an array")
        return
    if row_count is not None and len(values) != row_count:
        problems.append(f"column {name!r} has {len(values)} values, expected {row_count}")
    for i, v in enumerate(values):
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            problems.append(f"column {name!r}[{i}] is not number-or-null: {v!r}")
            break
        if isinstance(v, float) and not math.isfinite(v):
            problems.append(f"column {name!r}[{i}] is non-finite: {v!r}")
            break


def _validate_variable_meta(variables: Any, columns: dict[str, Any], row_count: int | None, problems: list[str]) -> None:
    if not isinstance(variables, list) or not variables:
        problems.append("variables metadata must be a non-empty array")
        return
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
        column = columns[name]
        if isinstance(column, list):
            actual_available = sum(1 for v in column if v is not None)
            if available != actual_available:
                problems.append(f"{name!r}.availableN {available} != actual {actual_available}")
        if row_count is not None and available + missing != row_count:
            problems.append(
                f"{name!r}.availableN + missingN != rowCount ({available}+{missing})"
            )


def validate_artifact(artifact: Any, allowed_columns: list[str]) -> list[str]:
    """Return a list of human-readable problems for the histogram artifact."""
    allowed = set(allowed_columns)
    problems, row_count, columns = _validate_common(artifact, allowed, "eda-histogram")
    if not isinstance(artifact, dict):
        return problems

    for name, values in columns.items():
        if looks_like_identifier(name):
            problems.append(f"identifier-like column present: {name!r}")
        if name not in allowed:
            problems.append(f"column {name!r} is not in the curated column authority")
        _validate_numeric_column(name, values, row_count, problems)

    _validate_variable_meta(artifact.get("variables"), columns, row_count, problems)
    return problems


def validate_retention_artifact(artifact: Any, allowed_columns: list[str], site_field: str = SITE_FIELD) -> list[str]:
    """Return a list of human-readable problems for the retention artifact.

    Enforces the narrow ``SITE_ID`` exception: exactly that one column is a
    non-personal grouping label with no missing values; every *other* column
    must be a curated, non-identifier candidate variable.
    """
    allowed = set(allowed_columns)
    problems, row_count, columns = _validate_common(artifact, allowed, "eda-retention")
    if not isinstance(artifact, dict):
        return problems

    if site_field != SITE_FIELD:
        problems.append(f"site field must be {SITE_FIELD!r}, got {site_field!r}")

    if site_field not in columns:
        problems.append(f"required site column {site_field!r} is missing")
    if site_field not in allowed:
        problems.append(f"site column {site_field!r} is not in the curated column authority")

    for name, values in columns.items():
        if name == site_field:
            if not isinstance(values, list):
                problems.append(f"column {name!r} is not an array")
                continue
            if row_count is not None and len(values) != row_count:
                problems.append(f"column {name!r} has {len(values)} values, expected {row_count}")
            for i, v in enumerate(values):
                if not isinstance(v, str) or v.strip() == "":
                    problems.append(f"site column {name!r}[{i}] is not a non-empty string: {v!r}")
                    break
            continue
        # Every non-site column must be a legitimate candidate variable.
        if looks_like_identifier(name):
            problems.append(f"identifier-like column present: {name!r}")
        if name not in allowed:
            problems.append(f"column {name!r} is not in the curated column authority")
        _validate_numeric_column(name, values, row_count, problems)

    _validate_variable_meta(artifact.get("variables"), columns, row_count, problems)

    # Site metadata consistency.
    site_meta = artifact.get("site")
    if not isinstance(site_meta, dict):
        problems.append("site metadata must be an object")
    elif site_field in columns and isinstance(columns[site_field], list):
        labels = columns[site_field]
        first_seen: dict[str, int] = {}
        for label in labels:
            if isinstance(label, str):
                first_seen[label] = first_seen.get(label, 0) + 1
        if site_meta.get("field") != site_field:
            problems.append(f"site.field must be {site_field!r}, got {site_meta.get('field')!r}")
        if site_meta.get("siteCount") != len(first_seen):
            problems.append(
                f"site.siteCount {site_meta.get('siteCount')!r} != distinct labels {len(first_seen)}"
            )
        sites = site_meta.get("sites")
        if not isinstance(sites, list) or len(sites) != len(first_seen):
            problems.append("site.sites must list every distinct site exactly once")
        else:
            meta_order = [s.get("label") if isinstance(s, dict) else None for s in sites]
            if meta_order != list(first_seen.keys()):
                problems.append("site.sites is not in first-appearance order of the SITE_ID column")
            total_sum = 0
            for s in sites:
                if not isinstance(s, dict):
                    continue
                label, total = s.get("label"), s.get("total")
                if not isinstance(total, int) or isinstance(total, bool):
                    problems.append(f"site {label!r}.total must be an integer")
                    continue
                if first_seen.get(label) != total:
                    problems.append(f"site {label!r}.total {total} != actual {first_seen.get(label)}")
                total_sum += total
            if row_count is not None and total_sum != row_count:
                problems.append(f"site totals sum to {total_sum}, expected rowCount {row_count}")

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


# --- Artifact registry -----------------------------------------------------------


class ArtifactSpec:
    """One committed artifact: how to build, validate, and where it lives."""

    def __init__(self, key: str, activity: str, path: Path, build, validate) -> None:
        self.key = key
        self.activity = activity
        self.path = path
        self._build = build
        self._validate = validate

    def build(self, frame: "Any", allowed: list[str]) -> dict[str, Any]:
        return self._build(frame, allowed)

    def validate(self, artifact: Any, allowed: list[str]) -> list[str]:
        return self._validate(artifact, allowed)


ARTIFACTS: dict[str, ArtifactSpec] = {
    "histogram": ArtifactSpec(
        "histogram",
        "eda-histogram",
        HISTOGRAM_ARTIFACT_PATH,
        lambda frame, allowed: build_artifact(frame, HISTOGRAM_VARIABLES, allowed),
        lambda artifact, allowed: validate_artifact(artifact, allowed),
    ),
    "retention": ArtifactSpec(
        "retention",
        "eda-retention",
        RETENTION_ARTIFACT_PATH,
        lambda frame, allowed: build_retention_artifact(frame, RETENTION_VARIABLES, allowed),
        lambda artifact, allowed: validate_retention_artifact(artifact, allowed),
    ),
    "table-inspection": ArtifactSpec(
        "table-inspection",
        "table-inspection",
        TABLE_INSPECTION_ARTIFACT_PATH,
        lambda frame, allowed: build_table_inspection_artifact(frame, allowed),
        lambda artifact, allowed: validate_table_inspection_artifact(artifact, allowed),
    ),
}


def _selected_specs(selector: str) -> list[ArtifactSpec]:
    if selector == "all":
        return list(ARTIFACTS.values())
    return [ARTIFACTS[selector]]


# --- Modes -------------------------------------------------------------------


def fetch_source(url: str = SOURCE_URL) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 (pinned https)
        return response.read()


def _summary(artifact: dict[str, Any]) -> str:
    lines = [
        f"activity      : {artifact['activity']}",
        f"schemaVersion : {artifact['schemaVersion']}",
        f"rowCount      : {artifact['rowCount']}",
        f"source.sha256 : {artifact['source']['sha256']}",
    ]
    if "site" in artifact:
        lines.append(f"site.field    : {artifact['site']['field']} ({artifact['site']['siteCount']} sites)")
    lines.append("variables     :")
    for meta in artifact["variables"]:
        lines.append(
            f"  {meta['name']:20} availableN={meta['availableN']:5} missingN={meta['missingN']:5}"
        )
    return "\n".join(lines)


def cmd_refresh(selector: str) -> int:
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

    exit_code = 0
    for spec in _selected_specs(selector):
        artifact = spec.build(frame, allowed)
        problems = spec.validate(artifact, allowed)
        if problems:
            print(f"ERROR: built {spec.key} artifact failed validation:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            exit_code = 1
            continue

        text = serialize(artifact)
        spec.path.parent.mkdir(parents=True, exist_ok=True)
        spec.path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {spec.path.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
        print(f"artifact sha256: {sha256_hex(text.encode('utf-8'))}")
        print(_summary(artifact))
    return exit_code


def cmd_check(selector: str) -> int:
    allowed = read_allowed_columns(ALLOWED_COLUMNS_PATH)
    exit_code = 0
    for spec in _selected_specs(selector):
        if not spec.path.exists():
            print(f"ERROR: {spec.path} does not exist; run --refresh first.", file=sys.stderr)
            exit_code = 1
            continue

        on_disk = spec.path.read_text(encoding="utf-8")
        try:
            artifact = json.loads(on_disk)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            print(f"ERROR: {spec.key} artifact is not valid JSON: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        problems = spec.validate(artifact, allowed)
        if problems:
            print(f"ERROR: committed {spec.key} artifact failed validation:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            exit_code = 1
            continue

        canonical = serialize(artifact)
        if canonical != on_disk:
            print(
                f"ERROR: committed {spec.key} artifact is not in canonical deterministic "
                "form (re-serialization differs). Re-run --refresh.",
                file=sys.stderr,
            )
            exit_code = 1
            continue

        print(f"OK: {spec.path.relative_to(REPO_ROOT)} is valid and canonical.")
        print(f"artifact sha256: {sha256_hex(on_disk.encode('utf-8'))}")
        print(_summary(artifact))
    return exit_code


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
    mode.add_argument("--refresh", action="store_true", help="download + verify + rewrite the artifact(s) (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed artifact(s) offline")
    mode.add_argument(
        "--print-upstream-hash",
        action="store_true",
        help="download the source and print its SHA-256 (no write)",
    )
    parser.add_argument(
        "--artifact",
        choices=("histogram", "retention", "table-inspection", "all"),
        default="all",
        help="which artifact --refresh / --check operates on (default: all)",
    )
    args = parser.parse_args(argv)

    if args.refresh:
        return cmd_refresh(args.artifact)
    if args.check:
        return cmd_check(args.artifact)
    return cmd_print_upstream_hash()


if __name__ == "__main__":
    raise SystemExit(main())
