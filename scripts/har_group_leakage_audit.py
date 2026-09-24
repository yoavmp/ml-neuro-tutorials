#!/usr/bin/env python3
"""Mandatory UCI HAR preflight audit for Exercise 10 (WP38 sec 8.2).

Compares ordinary 5-fold cross-validation (``StratifiedKFold``) against
participant-grouped 5-fold cross-validation (``StratifiedGroupKFold``, groups
= participant id) for ``Pipeline(StandardScaler(), KNeighborsClassifier())``
at k in (1, 3, 5, 11, 25), on the committed compact 18-feature subset
(``uci_har_data.load_compact_table``, offline). This script's ``--run``
recomputes and writes the full result (including the four inclusion
conditions from WP38 sec 8.2); ``--check`` re-validates the committed JSON is
current and canonical.

The shared computation (fold assignment, per-k CV, participant-overlap
counts) lives in ``scripts/uci_har_data.py`` and is reused unchanged by
``scripts/export_har_fold_widget_data.py`` for the browser activity, so the
notebook, this audit, and the frontend never maintain separate copies of the
same numbers.

Inclusion conditions (all four must hold; WP38 sec 8.2):

1. ordinary splitting places participant data across training and validation
   in every fold;
2. grouped splitting has zero participant overlap;
3. ordinary splitting is more optimistic by at least 0.03 in accuracy or
   macro-F1 for at least two of the five predeclared k values;
4. the direction is not supported solely by one anomalous fold -- for every
   k that qualifies under condition 3, at least 3 of its 5 per-fold gaps
   (ordinary minus grouped, accuracy or macro-F1) must be positive.

Usage::

    python scripts/har_group_leakage_audit.py --run     # offline; recomputes + writes JSON
    python scripts/har_group_leakage_audit.py --check   # offline; re-validates committed JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uci_har_data import K_VALUES, REPO_ROOT, compute_fold_comparison, load_compact_table  # noqa: E402

RESULT_PATH = REPO_ROOT / "scripts" / "har_group_leakage_audit_result.json"
SCHEMA_VERSION = 1
GAP_THRESHOLD = 0.03
MIN_QUALIFYING_K = 2
MIN_POSITIVE_FOLDS = 3


def _condition_checks(comparison: dict[str, Any]) -> dict[str, Any]:
    cond1 = comparison["participantsCrossingFoldsOrdinary"] > 0
    cond2 = comparison["participantsCrossingFoldsGrouped"] == 0 and comparison["groupedFoldsDisjoint"]

    qualifying_ks = [
        r["k"] for r in comparison["kResults"] if r["accGap"] >= GAP_THRESHOLD or r["f1Gap"] >= GAP_THRESHOLD
    ]
    cond3 = len(qualifying_ks) >= MIN_QUALIFYING_K

    per_k_positive_folds = {}
    for r in comparison["kResults"]:
        acc_per_fold_gap = [o - g for o, g in zip(r["ordinary"]["accPerFold"], r["grouped"]["accPerFold"])]
        f1_per_fold_gap = [o - g for o, g in zip(r["ordinary"]["f1PerFold"], r["grouped"]["f1PerFold"])]
        positive = sum(1 for a, f in zip(acc_per_fold_gap, f1_per_fold_gap) if a > 0 or f > 0)
        per_k_positive_folds[r["k"]] = positive
    cond4 = all(per_k_positive_folds[k] >= MIN_POSITIVE_FOLDS for k in qualifying_ks) if qualifying_ks else False

    overall = cond1 and cond2 and cond3 and cond4
    return {
        "condition1ParticipantsCrossOrdinary": cond1,
        "condition2GroupedDisjoint": cond2,
        "condition3QualifyingKCount": len(qualifying_ks),
        "condition3Qualifies": cond3,
        "condition3QualifyingKValues": qualifying_ks,
        "condition4PerKPositiveFolds": per_k_positive_folds,
        "condition4Qualifies": cond4,
        "overallPass": overall,
    }


def build_result(frame: Any) -> dict[str, Any]:
    comparison = compute_fold_comparison(frame, K_VALUES)
    conditions = _condition_checks(comparison)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "audit": "har_group_leakage_preflight",
        "kValues": list(K_VALUES),
        "comparison": comparison,
        "conditions": conditions,
    }


def validate_result(result: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if result.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if result.get("kValues") != list(K_VALUES):
        problems.append("kValues does not match uci_har_data.K_VALUES")
    comparison = result.get("comparison", {})
    if comparison.get("nRows") != 10299 or comparison.get("nParticipants") != 30:
        problems.append("comparison row/participant counts are unexpected")
    if len(comparison.get("kResults", [])) != len(K_VALUES):
        problems.append("kResults does not cover every predeclared k value")
    return problems


def serialize(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _print_table(result: dict[str, Any]) -> None:
    comparison = result["comparison"]
    print(f"rows={comparison['nRows']} participants={comparison['nParticipants']} activities={comparison['nActivities']}")
    print(f"observations per participant: {comparison['observationsPerParticipant']}")
    print(f"participants crossing folds -- ordinary: {comparison['participantsCrossingFoldsOrdinary']}, grouped: {comparison['participantsCrossingFoldsGrouped']}")
    print()
    print(f"{'k':>4} {'ord_acc':>8} {'grp_acc':>8} {'acc_gap':>8} {'ord_f1':>8} {'grp_f1':>8} {'f1_gap':>8}")
    for r in comparison["kResults"]:
        o, g = r["ordinary"], r["grouped"]
        print(f"{r['k']:>4} {o['accMean']:.4f}  {g['accMean']:.4f}  {r['accGap']:+.4f}  {o['f1Mean']:.4f}  {g['f1Mean']:.4f}  {r['f1Gap']:+.4f}")
    print()
    c = result["conditions"]
    print(f"condition 1 (ordinary crosses folds)      : {c['condition1ParticipantsCrossOrdinary']}")
    print(f"condition 2 (grouped fully disjoint)      : {c['condition2GroupedDisjoint']}")
    print(f"condition 3 (>=2 k with gap>=0.03)        : {c['condition3Qualifies']}  (qualifying k: {c['condition3QualifyingKValues']})")
    print(f"condition 4 (not one anomalous fold)      : {c['condition4Qualifies']}  (positive folds per k: {c['condition4PerKPositiveFolds']})")
    print(f"OVERALL PREFLIGHT                         : {'PASS' if c['overallPass'] else 'FAIL'}")


def cmd_run() -> int:
    frame = load_compact_table()
    result = build_result(frame)
    problems = validate_result(result)
    if problems:
        print("ERROR: built result failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    RESULT_PATH.write_text(serialize(result), encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)}")
    _print_table(result)
    return 0 if result["conditions"]["overallPass"] else 1


def cmd_check() -> int:
    if not RESULT_PATH.exists():
        print(f"ERROR: {RESULT_PATH} missing; run --run first.", file=sys.stderr)
        return 1
    on_disk = RESULT_PATH.read_text(encoding="utf-8")
    frame = load_compact_table()
    recomputed = build_result(frame)
    if serialize(recomputed) != on_disk:
        print("ERROR: committed result does not match a fresh recomputation from the committed compact table.", file=sys.stderr)
        return 1
    problems = validate_result(recomputed)
    if problems:
        print("ERROR:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {RESULT_PATH.relative_to(REPO_ROOT)} is valid, canonical, and reproducible from the committed data.")
    _print_table(recomputed)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="recompute from the committed compact table + write JSON")
    mode.add_argument("--check", action="store_true", help="validate the committed JSON is current + canonical")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
