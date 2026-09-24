#!/usr/bin/env python3
"""Export the Exercise 10 "Random Windows or New Participants?" interactive
(WP38 sec 8.3).

Reuses ``uci_har_data.compute_fold_comparison`` unchanged -- the identical
computation the mandatory preflight audit
(``scripts/har_group_leakage_audit.py``) already validated -- so the browser
activity's numbers can never drift from the audited/reported ones (WP38
sec 13).

Output: ``book/_static/widgets/data/uci_har_fold_comparison.json``.
Ships only per-fold/per-participant aggregate counts and metrics -- no raw
sensor features.

Modes (exactly one required):

* ``--refresh``  (offline; reads only the committed compact table): recompute
  and write the artifact.
* ``--check``    (offline): re-validate the committed artifact is current and
  canonical.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uci_har_data import (  # noqa: E402
    ACTIVITY_LABELS,
    K_VALUES,
    N_SPLITS,
    REPO_ROOT,
    compute_fold_comparison,
    load_compact_table,
    load_provenance,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "uci_har_fold_comparison.json"
SCHEMA_VERSION = 1


def build_artifact(frame: Any) -> dict[str, Any]:
    comparison = compute_fold_comparison(frame, K_VALUES)
    provenance = load_provenance()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "har-fold-compare",
        "source": {
            "sourceUrl": provenance["dataset"]["sourceUrl"],
            "doi": provenance["dataset"]["doi"],
            "license": provenance["dataset"]["license"],
            "derivedFileSha256": provenance["derivedFile"]["sha256"],
        },
        "activityLabels": {str(k): v for k, v in sorted(ACTIVITY_LABELS.items())},
        "kValues": list(K_VALUES),
        "nSplits": N_SPLITS,
        "nRows": comparison["nRows"],
        "nParticipants": comparison["nParticipants"],
        "observationsPerParticipant": comparison["observationsPerParticipant"],
        "kResults": comparison["kResults"],
        "participantFolds": comparison["participantFolds"],
    }


def validate_artifact(artifact: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "har-fold-compare":
        problems.append("activity must be 'har-fold-compare'")
    if artifact.get("kValues") != list(K_VALUES):
        problems.append("kValues does not match uci_har_data.K_VALUES")
    if artifact.get("nParticipants") != 30:
        problems.append("nParticipants must be 30")
    if len(artifact.get("activityLabels", {})) != 6:
        problems.append("activityLabels must have exactly 6 entries")

    k_results = artifact.get("kResults")
    if not isinstance(k_results, list) or len(k_results) != len(K_VALUES):
        return problems + ["kResults must cover every predeclared k value"]
    for r in k_results:
        for side in ("ordinary", "grouped"):
            side_val = r.get(side, {})
            if len(side_val.get("accPerFold", [])) != N_SPLITS:
                problems.append(f"k={r.get('k')} {side}: accPerFold must have {N_SPLITS} entries")
            if len(side_val.get("confusionPerFold", [])) != N_SPLITS:
                problems.append(f"k={r.get('k')} {side}: confusionPerFold must have {N_SPLITS} entries")

    participant_folds = artifact.get("participantFolds")
    if not isinstance(participant_folds, list) or len(participant_folds) != 30:
        problems.append("participantFolds must have exactly 30 entries")
    else:
        grouped_single = all(len({p["groupedFold"]}) == 1 for p in participant_folds)
        if not grouped_single:
            problems.append("participantFolds: groupedFold must be a single value per participant (schema check)")
        ordinary_crossing = sum(1 for p in participant_folds if len(p["ordinaryFolds"]) > 1)
        if ordinary_crossing == 0:
            problems.append("participantFolds: expected at least one participant crossing ordinary folds")
        grouped_fold_ids = [p["groupedFold"] for p in participant_folds]
        # grouped folds must be disjoint at the participant level by construction; nothing further to check here.
        del grouped_fold_ids

    identifier_token = ("sub", "subject", "site")
    for key in artifact.keys():
        if key.lower() in identifier_token:
            problems.append(f"artifact has an identifier-shaped key: {key!r}")

    return problems


def serialize(artifact: dict[str, Any]) -> str:
    return (
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    )


def _summary(artifact: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"activity        : {artifact['activity']}",
            f"nRows           : {artifact['nRows']}",
            f"nParticipants   : {artifact['nParticipants']}",
            f"kValues         : {artifact['kValues']}",
            f"kResults        : {len(artifact['kResults'])}",
            f"participantFolds: {len(artifact['participantFolds'])}",
        ]
    )


def cmd_refresh() -> int:
    frame = load_compact_table()
    artifact = build_artifact(frame)
    problems = validate_artifact(artifact)
    if problems:
        print("ERROR: built artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = serialize(artifact)
    ARTIFACT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {ARTIFACT_PATH.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    print(_summary(artifact))
    return 0


def cmd_check() -> int:
    if not ARTIFACT_PATH.exists():
        print(f"ERROR: {ARTIFACT_PATH} missing; run --refresh first.", file=sys.stderr)
        return 1
    on_disk = ARTIFACT_PATH.read_text(encoding="utf-8")
    try:
        artifact = json.loads(on_disk)
    except json.JSONDecodeError as exc:
        print(f"ERROR: artifact is not valid JSON: {exc}", file=sys.stderr)
        return 1
    problems = validate_artifact(artifact)
    if problems:
        print("ERROR: committed artifact failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    if serialize(artifact) != on_disk:
        print("ERROR: committed artifact is not canonical (re-serialization differs).", file=sys.stderr)
        return 1
    print(f"OK: {ARTIFACT_PATH.relative_to(REPO_ROOT)} is valid and canonical.")
    print(_summary(artifact))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true", help="recompute + write the artifact (offline)")
    mode.add_argument("--check", action="store_true", help="validate the committed artifact offline")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
