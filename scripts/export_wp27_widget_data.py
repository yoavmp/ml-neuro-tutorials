#!/usr/bin/env python3
"""Export the three Exercise 4 (WP27) interactive-activity data artifacts.

Reshapes the single committed audit result
(``scripts/wp27_validation_audit_result.json``, produced by
``scripts/wp27_validation_audit.py --run``) into three small, activity-scoped
JSON files the browser runtime loads directly -- no recomputation happens
here, so every number a student sees traces back to the one audited source of
truth:

* ``book/_static/widgets/data/wp27_validation_stability.json``
  ("One Split or Several Folds?", Section 2);
* ``book/_static/widgets/data/wp27_validation_lock_test.json``
  ("Choose k Before Revealing the Test Set", Section 5);
* ``book/_static/widgets/data/wp27_nested_cv_explorer.json``
  ("Look Inside Nested Cross-Validation", Section 6-7).

Each ships only aggregated model results -- no brain features, no
participant identifiers.

Modes (exactly one required):

* ``--write``  -- regenerate the three artifacts from the committed audit
  result (offline; no network).
* ``--check``  -- regenerate in memory and fail if a committed artifact is
  stale or missing. Used by CI. No network, no writes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wp27_validation_audit import RESULT_PATH as AUDIT_RESULT_PATH  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "book" / "_static" / "widgets" / "data"

STABILITY_PATH = DATA_DIR / "wp27_validation_stability.json"
LOCK_TEST_PATH = DATA_DIR / "wp27_validation_lock_test.json"
NESTED_CV_PATH = DATA_DIR / "wp27_nested_cv_explorer.json"


def _source(audit: dict[str, Any]) -> dict[str, Any]:
    return audit["source"]


def build_stability(audit: dict[str, Any]) -> dict[str, Any]:
    a = audit["part_a_sample_size_stability"]
    sizes_out = []
    for s in a["sizes"]:
        size_key = str(s["sample_size"])
        single = [
            {
                "seed": e["seed"],
                "valid": e["valid"],
                **({k: v for k, v in e.items() if k not in ("seed", "valid")}),
            }
            for e in s["single_split"]
        ]
        cv_by_folds = {}
        for folds_key, entries in s["cv_by_folds"].items():
            cv_by_folds[folds_key] = [
                {
                    "seed": e["seed"],
                    "valid": e["valid"],
                    **({k: v for k, v in e.items() if k not in ("seed", "valid", "folds")}),
                }
                for e in entries
            ]
        sizes_out.append(
            {
                "sizeKey": size_key,
                "label": "All eligible" if size_key == "all" else str(s["n_actual"]),
                "nActual": s["n_actual"],
                "singleSplit": single,
                "cvByFolds": cv_by_folds,
                "instabilityMeaningful": s["instability_meaningful"],
                "anyNegativeSingleSplitR2": s["any_negative_single_split_r2"],
                "anyNegativeCv5MeanR2": s["any_negative_cv5_mean_r2"],
            }
        )
    return {
        "schemaVersion": 1,
        "activity": "validation-stability",
        "source": _source(audit),
        "fixedK": a["fixed_k"],
        "singleSplitTestSize": a["single_split_test_size"],
        "splitSeeds": a["split_seeds"],
        "foldOptions": a["fold_options"],
        "sizes": sizes_out,
        "sizesWithMeaningfulInstability": [str(x) for x in a["sizes_with_meaningful_instability"]],
        "instabilityRequiresSmallN": a["instability_requires_small_n"],
    }


def build_lock_test(audit: dict[str, Any]) -> dict[str, Any]:
    b = audit["part_b_train_val_test_tuning"]
    rows = [
        {
            "k": r["k"],
            "trainMse": r["train_mse"],
            "trainR2": r["train_r2"],
            "valMse": r["val_mse"],
            "valR2": r["val_r2"],
            "testMseIfLocked": r["test_mse_if_locked"],
            "testR2IfLocked": r["test_r2_if_locked"],
        }
        for r in b["rows"]
    ]
    return {
        "schemaVersion": 1,
        "activity": "validation-lock-test",
        "source": _source(audit),
        "nFit": b["n_fit"],
        "nVal": b["n_val"],
        "nTest": b["n_outer_test"],
        "featureCount": b["feature_count"],
        "candidateKs": b["candidate_ks"],
        "rows": rows,
        "trainingSelectedK": b["training_selected_k"],
        "validationSelectedK": b["validation_selected_k"],
    }


def build_nested_cv(audit: dict[str, Any]) -> dict[str, Any]:
    c = audit["part_c_nested_cv"]
    fold_rows = [
        {
            "outerFold": r["outer_fold"],
            "nTrain": r["n_train"],
            "nTest": r["n_test"],
            "innerMseByK": r["inner_mse_by_k"],
            "selectedK": r["selected_k"],
            "bestInnerMse": r["best_inner_mse"],
            "outerTestMse": r["outer_test_mse"],
            "outerTestR2": r["outer_test_r2"],
        }
        for r in c["fold_rows"]
    ]
    return {
        "schemaVersion": 1,
        "activity": "nested-cv-explorer",
        "source": _source(audit),
        "candidateKs": c["candidate_ks"],
        "nOuter": c["n_outer"],
        "nInner": c["n_inner"],
        "featureCount": c["feature_count"],
        "foldRows": fold_rows,
        "selectedKPerFold": c["selected_k_per_fold"],
        "selectedKVariesAcrossFolds": c["selected_k_varies_across_folds"],
        "meanOuterTestMse": c["mean_outer_test_mse"],
        "stdOuterTestMse": c["std_outer_test_mse"],
        "meanOuterTestR2": c["mean_outer_test_r2"],
        "stdOuterTestR2": c["std_outer_test_r2"],
    }


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


BUILDERS = {
    STABILITY_PATH: build_stability,
    LOCK_TEST_PATH: build_lock_test,
    NESTED_CV_PATH: build_nested_cv,
}


def cmd_write() -> int:
    if not AUDIT_RESULT_PATH.exists():
        print(f"ERROR: {AUDIT_RESULT_PATH} missing; run scripts/wp27_validation_audit.py --run first.", file=sys.stderr)
        return 1
    audit = json.loads(AUDIT_RESULT_PATH.read_text(encoding="utf-8"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path, builder in BUILDERS.items():
        text = serialize(builder(audit))
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(REPO_ROOT)} ({len(text.encode('utf-8'))} bytes)")
    return 0


def cmd_check() -> int:
    if not AUDIT_RESULT_PATH.exists():
        print(f"ERROR: {AUDIT_RESULT_PATH} missing; run scripts/wp27_validation_audit.py --run first.", file=sys.stderr)
        return 1
    audit = json.loads(AUDIT_RESULT_PATH.read_text(encoding="utf-8"))
    exit_code = 0
    for path, builder in BUILDERS.items():
        expected = serialize(builder(audit))
        if not path.exists():
            print(f"ERROR: {path} is missing. Run scripts/export_wp27_widget_data.py --write.", file=sys.stderr)
            exit_code = 1
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"ERROR: {path} is stale. Run scripts/export_wp27_widget_data.py --write.", file=sys.stderr)
            exit_code = 1
            continue
        print(f"OK: {path.relative_to(REPO_ROOT)} is up to date.")
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="(re)generate the three artifacts (offline)")
    mode.add_argument("--check", action="store_true", help="fail if a committed artifact is stale or missing")
    args = parser.parse_args(argv)
    return cmd_write() if args.write else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
