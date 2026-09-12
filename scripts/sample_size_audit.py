#!/usr/bin/env python3
"""Reproducible, training-only audit of small cortical-thickness feature
subsets for Exercise 2 Section 5's sample-size demonstration (WP15 §2).

Goal: decide -- empirically, and BEFORE looking at the locked outer test
set -- whether a small (<=12 column), defensible, bilateral cortical-
thickness bundle produces a clean "more training data -> more stable /
better held-out prediction" curve, so the isolated sample-size lesson does
not have to fight the full 360-feature recipe's real double-descent
instability (see ``regression_model_audit_result.json`` / WP14 §6 for that
finding, which remains true and is preserved unchanged in Section 2's main
worked example).

Design rules (WP15 §2.2/§2.3), enforced in code, not by inspection:

* every candidate has at most 12 genuine ``fsCT_`` columns (<=6 bilateral
  ROIs), is defined independently of participant ages/outcomes, has a
  reproducible anatomical or deterministic rationale, and uses only
  predictor columns (no diagnosis/site/id/other phenotype);
* candidates and the plotted-size sequence are predeclared in this module
  BEFORE any candidate is scored -- nothing here is chosen after seeing a
  result;
* every candidate is scored using ONLY the outer-TRAINING partition
  (``protocol.holdout_split``, matching Exercise 2's own locked split):
  an inner, fixed dev split of that training partition (identical
  parameters to ``knn.dev_split`` -- test_size=0.25, random_state=7,
  stratify=group -- already established and reviewed for exactly this
  "carve a fixed evaluation set out of the training partition" purpose)
  gives a fixed inner-fit pool (564 rows) to subsample from and a fixed
  inner-val pool (189 rows) to score against. The outer test set (251 rows)
  is never loaded as a scoring target anywhere in this module;
* the decision rule (``DecisionRule`` / :func:`evaluate_decision_rule`) is
  written and thresholds fixed before any candidate's numbers were computed
  for this audit;
* every predeclared candidate is scored and reported, including ones that
  do not pass.

Usage::

    python scripts/sample_size_audit.py --run     # network; prints + writes JSON
    python scripts/sample_size_audit.py --check   # offline; re-validate committed JSON

The committed JSON summary lives at
``scripts/sample_size_audit_result.json`` and is asserted by
``tests/test_sample_size_audit.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from abide_modeling_data import (  # noqa: E402
    MANIFEST,
    REPO_ROOT,
    assert_brain_only,
    load_modeling_frame,
    raw_label_for,
)

RESULT_PATH = REPO_ROOT / "scripts" / "sample_size_audit_result.json"

# --- predeclared candidates -------------------------------------------------
# Each: <=12 genuine fsCT_ columns (<=6 bilateral ROIs), both hemispheres,
# defined by a documented neuroanatomical rationale (or, for the last one, a
# deterministic atlas-order rule) -- never by a correlation with age or by
# looking at any score. Source-of-preference order (WP15 §2.2): no existing
# manifest bundle (book/config/abide_modeling.json "bundles") has <=12
# columns (the smallest, "sensorimotor", already has 20 ROIs / 40 columns),
# so every candidate here comes from source 2 (a small bilateral literature
# set) or source 3 (a deterministic atlas-order rule), in that order.
CANDIDATES: dict[str, dict[str, Any]] = {
    "sensorimotor_core": {
        "rois": ["4", "3a", "3b", "1", "2"],
        "source_preference": 2,
        "rationale": (
            "Primary motor cortex (BA4) plus primary somatosensory cortex "
            "(BA 3a/3b/1/2) -- the classic sensorimotor strip (Penfield & "
            "Rasmussen 1950 homunculus; HCP-MMP1 areas 4/3a/3b/1/2, Glasser "
            "et al. 2016). A minimal, maximally well-established anatomical "
            "system, chosen for its textbook clarity, independent of any "
            "age or cognition literature."
        ),
    },
    "early_visual": {
        "rois": ["V1", "V2", "V3", "V4"],
        "source_preference": 2,
        "rationale": (
            "Early visual hierarchy V1-V4 (Felleman & Van Essen 1991 "
            "canonical visual processing hierarchy; HCP-MMP1 areas "
            "V1/V2/V3/V4)."
        ),
    },
    "auditory_core_belt": {
        "rois": ["A1", "LBelt", "MBelt", "PBelt"],
        "source_preference": 2,
        "rationale": (
            "Primary auditory core (A1) plus its immediately surrounding "
            "belt regions (Kaas & Hackett 2000 core-belt-parabelt auditory "
            "hierarchy; HCP-MMP1 areas A1/LBelt/MBelt/PBelt)."
        ),
    },
    "atlas_order_every_30th": {
        "rois": None,  # filled in _candidate_rois() from atlas order alone
        "source_preference": 3,
        "rationale": (
            "Deterministic atlas-order sampling rule: every 30th canonical "
            "ROI id in atlas.roi_label_inventory (fixed indices 0, 30, 60, "
            "90, 120, 150 of the 180-entry inventory), chosen from column "
            "order / atlas structure alone, with no reference to region "
            "identity, age, or performance."
        ),
    },
}

# Predeclared training sizes for the inner audit (bounded by the inner-fit
# pool size, 564) -- fixed before any candidate was scored. The smallest
# size (40) is >= 3x the largest candidate p (12), satisfying the "smallest
# plotted training size is comfortably larger than p" requirement for every
# candidate simultaneously.
AUDIT_SIZES: list[int] = [40, 60, 90, 130, 200, 300, 564]
AUDIT_N_REP = 40
AUDIT_SEEDS: list[int] = [0, 1, 2]

# --- decision-rule thresholds (WP15 §2.3), fixed before any candidate was scored
MIN_N_OVER_P_AT_SMALLEST = 3.0          # "comfortably larger than p"
MIN_R2_GAIN_FIRST_TO_LAST = 0.05        # "clear overall upward trend"
MAX_CONSECUTIVE_DROP = 0.02             # "minor non-monotonicity acceptable"
MAX_SPREAD_FRACTION_AT_LARGEST = 0.35   # "instability narrows materially"
MAX_SEED_DISAGREEMENT = 0.15            # "not dependent on one lucky seed"
MIN_FINAL_MEDIAN_R2 = 0.15              # "remains meaningful ... not noise"


def _candidate_columns(rois: list[str]) -> list[str]:
    cols: list[str] = []
    for roi in rois:
        for hemi in ("L", "R"):
            raw = raw_label_for(roi, hemi)
            cols.append(f"fsCT_{hemi}_{raw}_ROI")
    assert_brain_only(cols)
    return cols


def _resolved_candidates() -> dict[str, dict[str, Any]]:
    """CANDIDATES with every ``rois``/``columns`` resolved (atlas-order rule
    filled in), independent of any run of the audit itself."""
    inv = list(MANIFEST["atlas"]["roi_label_inventory"])
    out: dict[str, dict[str, Any]] = {}
    for name, spec in CANDIDATES.items():
        rois = spec["rois"]
        if rois is None:
            rois = [inv[i] for i in range(0, len(inv), 30)][:6]
        cols = _candidate_columns(rois)
        if len(cols) > 12:
            raise ValueError(f"candidate {name!r} has {len(cols)} columns, exceeds the 12-column limit")
        out[name] = {**spec, "rois": rois, "columns": cols, "p": len(cols)}
    return out


def _splits(frame: Any):
    """Outer holdout (Exercise 2's own locked split) then an inner dev split
    of the TRAINING partition only, identical parameters to
    ``knn.dev_split``. Returns (fit_df, val_df); the outer test rows are
    never returned or touched by this function's caller."""
    import numpy as np
    from sklearn.model_selection import train_test_split

    from abide_modeling_data import is_brain_column

    has_age = frame["age"].notna()
    model_df = frame.loc[has_age].reset_index(drop=True)

    split = MANIFEST["protocol"]["holdout_split"]
    groups_all = model_df["group"].to_numpy()
    train_idx, _test_idx = train_test_split(
        np.arange(len(model_df)),
        test_size=split["test_size"],
        random_state=split["random_state"],
        stratify=groups_all,
    )
    train_df = model_df.iloc[train_idx].reset_index(drop=True)

    dev = MANIFEST["knn"]["dev_split"]
    train_groups = train_df["group"].to_numpy()
    fit_idx, val_idx = train_test_split(
        np.arange(len(train_df)),
        test_size=dev["test_size"],
        random_state=dev["random_state"],
        stratify=train_groups,
    )
    fit_df = train_df.iloc[fit_idx].reset_index(drop=True)
    val_df = train_df.iloc[val_idx].reset_index(drop=True)
    return fit_df, val_df


def _score_candidate(fit_df: Any, val_df: Any, cols: list[str]) -> list[dict[str, Any]]:
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X_fit = fit_df[cols].to_numpy(float)
    X_val = val_df[cols].to_numpy(float)
    y_fit = fit_df["age"].to_numpy(float)
    y_val = val_df["age"].to_numpy(float)
    p = len(cols)

    rows: list[dict[str, Any]] = []
    for n in AUDIT_SIZES:
        seed_meds, seed_los, seed_his = [], [], []
        for seed in AUDIT_SEEDS:
            rng = np.random.default_rng(seed)
            r2s = []
            for _ in range(AUDIT_N_REP):
                idx = rng.choice(len(y_fit), size=min(n, len(y_fit)), replace=False)
                pipe = make_pipeline(StandardScaler(), LinearRegression()).fit(X_fit[idx], y_fit[idx])
                r2s.append(r2_score(y_val, pipe.predict(X_val)))
            r2s = np.array(r2s)
            seed_meds.append(float(np.median(r2s)))
            seed_los.append(float(np.percentile(r2s, 10)))
            seed_his.append(float(np.percentile(r2s, 90)))
        rows.append(
            {
                "n": n,
                "p": p,
                "n_over_p": round(n / p, 4),
                "median_r2_by_seed": [round(v, 6) for v in seed_meds],
                "median_r2_mean_over_seeds": round(float(np.mean(seed_meds)), 6),
                "lo10_mean_over_seeds": round(float(np.mean(seed_los)), 6),
                "hi90_mean_over_seeds": round(float(np.mean(seed_his)), 6),
                "spread_mean_over_seeds": round(float(np.mean(np.array(seed_his) - np.array(seed_los))), 6),
            }
        )
    return rows


def evaluate_decision_rule(p: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pure function: apply the WP15 §2.3 decision rule to a candidate's
    already-computed audit rows. No model fitting, no network -- reused
    identically by ``--run`` (right after scoring) and ``--check`` (to
    re-verify the committed ``passes`` value from the committed rows)."""
    smallest = rows[0]
    largest = rows[-1]
    checks: dict[str, Any] = {}

    checks["smallest_size_comfortably_above_p"] = smallest["n_over_p"] >= MIN_N_OVER_P_AT_SMALLEST

    medians = [r["median_r2_mean_over_seeds"] for r in rows]
    checks["clear_upward_trend"] = (largest["median_r2_mean_over_seeds"] - smallest["median_r2_mean_over_seeds"]) >= MIN_R2_GAIN_FIRST_TO_LAST
    max_drop = max((medians[i] - medians[i + 1] for i in range(len(medians) - 1)), default=0.0)
    checks["no_dominant_reversal"] = max_drop <= MAX_CONSECUTIVE_DROP

    spread_first = smallest["spread_mean_over_seeds"]
    spread_last = largest["spread_mean_over_seeds"]
    checks["instability_narrows_materially"] = (
        spread_first <= 0 or (spread_last / spread_first) <= MAX_SPREAD_FRACTION_AT_LARGEST
    )

    seed_disagreement = max(
        (max(r["median_r2_by_seed"]) - min(r["median_r2_by_seed"])) for r in rows
    )
    checks["seed_robust"] = seed_disagreement <= MAX_SEED_DISAGREEMENT

    checks["final_model_meaningful"] = largest["median_r2_mean_over_seeds"] >= MIN_FINAL_MEDIAN_R2

    passes = all(checks.values())
    return {"checks": checks, "passes": passes, "max_consecutive_drop": round(max_drop, 6), "seed_disagreement": round(seed_disagreement, 6)}


def run_audit() -> dict[str, Any]:
    frame = load_modeling_frame()
    candidates = _resolved_candidates()
    fit_df, val_df = _splits(frame)

    results: dict[str, Any] = {
        "generated_by": "scripts/sample_size_audit.py --run",
        "source": {
            "pinnedCommit": MANIFEST["source"]["pinned_commit"],
            "brainTableSha256": MANIFEST["source"]["brain_table"]["sha256"],
        },
        "protocol": {
            "outer_holdout_split": MANIFEST["protocol"]["holdout_split"],
            "inner_dev_split": MANIFEST["knn"]["dev_split"],
            "inner_fit_n": int(len(fit_df)),
            "inner_val_n": int(len(val_df)),
            "note": (
                "The outer test set (251 rows, protocol.holdout_split) is never loaded as a "
                "scoring target anywhere in this audit. Every candidate is scored against the "
                "fixed inner-val partition (189 rows) carved from the outer-TRAINING partition "
                "only, using the same dev-split parameters already established for the KNN "
                "audit (knn.dev_split)."
            ),
            "sizes": AUDIT_SIZES,
            "n_rep": AUDIT_N_REP,
            "seeds": AUDIT_SEEDS,
        },
        "decision_rule_thresholds": {
            "min_n_over_p_at_smallest": MIN_N_OVER_P_AT_SMALLEST,
            "min_r2_gain_first_to_last": MIN_R2_GAIN_FIRST_TO_LAST,
            "max_consecutive_drop": MAX_CONSECUTIVE_DROP,
            "max_spread_fraction_at_largest": MAX_SPREAD_FRACTION_AT_LARGEST,
            "max_seed_disagreement": MAX_SEED_DISAGREEMENT,
            "min_final_median_r2": MIN_FINAL_MEDIAN_R2,
        },
        "candidates": [],
    }

    for name, spec in candidates.items():
        rows = _score_candidate(fit_df, val_df, spec["columns"])
        decision = evaluate_decision_rule(spec["p"], rows)
        results["candidates"].append(
            {
                "name": name,
                "rois": spec["rois"],
                "columns": spec["columns"],
                "p": spec["p"],
                "source_preference": spec["source_preference"],
                "rationale": spec["rationale"],
                "rows": rows,
                "decision": decision,
            }
        )

    passing = [c for c in results["candidates"] if c["decision"]["passes"]]
    if passing:
        # Preferred source order first (2 before 3); ties broken by the
        # order already fixed in CANDIDATES (declaration order), never by
        # which one scores highest -- the outer test set was never
        # consulted, and no candidate's own audit numbers are used as a
        # tie-break either.
        passing.sort(key=lambda c: (c["source_preference"], list(candidates).index(c["name"])))
        chosen = passing[0]
        results["selection"] = {
            "outcome": "small-subset",
            "selected": chosen["name"],
            "reason": (
                f"First predeclared candidate (declaration order, source preference "
                f"{chosen['source_preference']}) whose training-only audit passed every "
                f"decision-rule check. Passing candidates in order considered: "
                f"{[c['name'] for c in passing]}."
            ),
        }
    else:
        results["selection"] = {
            "outcome": "fallback-360",
            "selected": None,
            "reason": "No predeclared small candidate passed every decision-rule check; falling back to the full 360-feature CT recipe per WP15 §2.4.",
        }
    return results


def serialize(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def cmd_run() -> int:
    results = run_audit()
    text = serialize(results)
    RESULT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {RESULT_PATH.relative_to(REPO_ROOT)} ({len(text.encode())} bytes)")
    _print_table(results)
    return 0


def cmd_check() -> int:
    if not RESULT_PATH.exists():
        print(f"ERROR: {RESULT_PATH} missing; run --run first.", file=sys.stderr)
        return 1
    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    problems = validate(results)
    if problems:
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: {RESULT_PATH.relative_to(REPO_ROOT)} is self-consistent.")
    _print_table(results)
    return 0


def validate(results: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if results.get("source", {}).get("pinnedCommit") != MANIFEST["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    if results.get("protocol", {}).get("sizes") != AUDIT_SIZES:
        problems.append("protocol.sizes does not match the predeclared AUDIT_SIZES")
    names_seen = {c["name"] for c in results.get("candidates", [])}
    if names_seen != set(CANDIDATES):
        problems.append(f"candidates cover {names_seen}, expected {set(CANDIDATES)}")
    for c in results.get("candidates", []):
        if c["p"] > 12:
            problems.append(f"candidate {c['name']!r} has p={c['p']} > 12")
        recomputed = evaluate_decision_rule(c["p"], c["rows"])
        if recomputed["passes"] != c["decision"]["passes"]:
            problems.append(f"candidate {c['name']!r}: stored passes={c['decision']['passes']} does not match recomputed {recomputed['passes']}")
        if recomputed["checks"] != c["decision"]["checks"]:
            problems.append(f"candidate {c['name']!r}: stored checks do not match recomputed checks")
    sel = results.get("selection", {})
    passing_names = [c["name"] for c in results.get("candidates", []) if c["decision"]["passes"]]
    if passing_names and sel.get("outcome") != "small-subset":
        problems.append("candidates passed but selection.outcome is not 'small-subset'")
    if not passing_names and sel.get("outcome") != "fallback-360":
        problems.append("no candidate passed but selection.outcome is not 'fallback-360'")
    if sel.get("outcome") == "small-subset" and sel.get("selected") not in passing_names:
        problems.append("selection.selected is not one of the passing candidates")
    return problems


def _print_table(results: dict[str, Any]) -> None:
    print()
    print("=== predeclared candidates (training-only audit; outer test set never touched) ===")
    for c in results["candidates"]:
        status = "PASS" if c["decision"]["passes"] else "fail"
        print(f"\n  [{status}] {c['name']}  p={c['p']}  rois={c['rois']}  source_pref={c['source_preference']}")
        print(f"        rationale: {c['rationale']}")
        for row in c["rows"]:
            print(
                f"        n={row['n']:4d} n/p={row['n_over_p']:6.2f}  "
                f"median R2 (mean of {len(row['median_r2_by_seed'])} seeds)={row['median_r2_mean_over_seeds']:+7.3f}  "
                f"spread(90-10)={row['spread_mean_over_seeds']:.3f}"
            )
        print(f"        checks: {c['decision']['checks']}")
    print()
    print(f"=== selection: {results['selection']} ===")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="run the audit (network) and write the JSON summary")
    mode.add_argument("--check", action="store_true", help="re-validate the committed JSON summary (offline)")
    args = parser.parse_args(argv)
    return cmd_run() if args.run else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
