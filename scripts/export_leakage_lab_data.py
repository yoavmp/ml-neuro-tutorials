#!/usr/bin/env python3
"""Deterministically export the Exercise 10 leakage-lab interactive (WP38 sec 6).

The browser activity ``leakage-lab`` lets a student pick a preprocessing
operation (scaling / feature selection / PCA), a sample size, and a
predeclared split seed, then compares a correct pipeline (the operation is
fit on training rows only) against a leaky variant (the same operation is fit
on the full sampled cohort -- train and test rows together -- before the
outer split). Every entry shares the age-regression target and holdout
convention used throughout Exercises 2/4/5 (``book/config/abide_modeling.json``
``protocol``); see ``leakage_lab`` in that manifest for the three scenarios'
predeclared bundles/feature counts and exact workflows.

For each (scenario, sample size, seed) in ``leakage_lab.sample_sizes`` x
``leakage_lab.seeds``, a fixed cohort is drawn once (``frame.sample(n=...,
random_state=seed)``, or the full eligible frame when sample size equals the
eligible count) and one outer ``train_test_split(test_size=0.25,
random_state=seed)`` is computed -- the identical rows and split are reused
for both the correct and leaky variant of that entry, so the comparison is
paired (WP38 sec 6.3). No seed, sample size, or feature count is chosen after
seeing a result.

Every scenario uses the same estimator, ``KNeighborsRegressor(n_neighbors=15)``
(WP38R sec 4): unlike ordinary least squares, KNN's distance-based predictions
are sensitive to feature scale and to which features/components are present,
so the scaling and PCA scenarios are not guaranteed to show a zero gap the way
they would under linear regression. ``n_neighbors=15`` is a fixed,
predeclared course-design value, not tuned from these results, and is valid
at every predeclared sample size (comfortably below the smallest training
fold of 45 rows at ``sample_size=60``).

Output: ``book/_static/widgets/data/abide_leakage_lab.json``.
Ships only aggregated per-entry metrics (MSE, R2, row counts) -- no brain
features, no participant identifiers.

Modes (exactly one required):

* ``--refresh``  (network): download + verify the pinned sources, recompute
  every (scenario, sample size, seed) combination, validate, and write.
* ``--check``    (offline): re-validate the committed artifact and confirm it
  is byte-for-byte canonical.
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
    bundle_columns,
    load_modeling_frame,
)

ARTIFACT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_leakage_lab.json"
SCHEMA_VERSION = 1


def _scenario_columns(frame: Any, scenario: dict[str, Any]) -> list[str]:
    cols = bundle_columns(scenario["bundle"], scenario["measures"], available=frame.columns)
    assert_brain_only(cols)
    return cols


def _eligible_frame(frame: Any, target: str) -> Any:
    return frame.loc[frame[target].notna()].reset_index(drop=True)


def _cohort(frame: Any, sample_size: int, seed: int) -> Any:
    if sample_size >= len(frame):
        return frame
    return frame.sample(n=sample_size, random_state=seed).reset_index(drop=True)


def _split(cohort: Any, seed: int):
    from sklearn.model_selection import train_test_split

    idx = cohort.index.to_numpy()
    train_idx, test_idx = train_test_split(idx, test_size=0.25, random_state=seed)
    return train_idx, test_idx


def _mse_r2(y_true: Any, y_pred: Any) -> tuple[float, float]:
    from sklearn.metrics import mean_squared_error, r2_score

    return (
        round(float(mean_squared_error(y_true, y_pred)), 6),
        round(float(r2_score(y_true, y_pred)), 6),
    )


def _scaling_entry(X: Any, y: Any, train_idx: Any, test_idx: Any) -> dict[str, Any]:
    import numpy as np
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    # correct: split first, fit the scaler on training rows only.
    correct = Pipeline([("scaler", StandardScaler()), ("model", KNeighborsRegressor(n_neighbors=15))])
    correct.fit(X[train_idx], y[train_idx])
    correct_mse, correct_r2 = _mse_r2(y[test_idx], correct.predict(X[test_idx]))

    # leaky: fit the scaler on every sampled row (train+test) before splitting.
    leaky_scaler = StandardScaler().fit(X)
    X_scaled = leaky_scaler.transform(X)
    leaky_model = KNeighborsRegressor(n_neighbors=15).fit(X_scaled[train_idx], y[train_idx])
    leaky_mse, leaky_r2 = _mse_r2(y[test_idx], leaky_model.predict(X_scaled[test_idx]))

    return {
        "correct": {"mse": correct_mse, "r2": correct_r2},
        "leaky": {"mse": leaky_mse, "r2": leaky_r2},
    }


def _feature_selection_entry(X: Any, y: Any, train_idx: Any, test_idx: Any, k: int) -> dict[str, Any]:
    from sklearn.feature_selection import SelectKBest, f_regression
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    # correct: a single pipeline fit on training rows only -- selection,
    # scaling, and the model all learn from the training partition alone.
    correct = Pipeline(
        [
            ("select", SelectKBest(f_regression, k=k)),
            ("scaler", StandardScaler()),
            ("model", KNeighborsRegressor(n_neighbors=15)),
        ]
    )
    correct.fit(X[train_idx], y[train_idx])
    correct_mse, correct_r2 = _mse_r2(y[test_idx], correct.predict(X[test_idx]))

    # leaky: rank/select using every sampled row (train+test) and the target,
    # before splitting. Only the selection step is leaky; scaling and the
    # model are still fit on training rows only.
    leaky_selector = SelectKBest(f_regression, k=k).fit(X, y)
    X_selected = leaky_selector.transform(X)
    leaky_model = Pipeline([("scaler", StandardScaler()), ("model", KNeighborsRegressor(n_neighbors=15))])
    leaky_model.fit(X_selected[train_idx], y[train_idx])
    leaky_mse, leaky_r2 = _mse_r2(y[test_idx], leaky_model.predict(X_selected[test_idx]))

    return {
        "correct": {"mse": correct_mse, "r2": correct_r2},
        "leaky": {"mse": leaky_mse, "r2": leaky_r2},
    }


def _pca_entry(X: Any, y: Any, train_idx: Any, test_idx: Any, n_components: int) -> dict[str, Any]:
    from sklearn.decomposition import PCA
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    correct = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=n_components, random_state=0)),
            ("model", KNeighborsRegressor(n_neighbors=15)),
        ]
    )
    correct.fit(X[train_idx], y[train_idx])
    correct_mse, correct_r2 = _mse_r2(y[test_idx], correct.predict(X[test_idx]))

    leaky_prep = Pipeline([("scaler", StandardScaler()), ("pca", PCA(n_components=n_components, random_state=0))])
    leaky_prep.fit(X)
    X_pca = leaky_prep.transform(X)
    leaky_model = KNeighborsRegressor(n_neighbors=15).fit(X_pca[train_idx], y[train_idx])
    leaky_mse, leaky_r2 = _mse_r2(y[test_idx], leaky_model.predict(X_pca[test_idx]))

    return {
        "correct": {"mse": correct_mse, "r2": correct_r2},
        "leaky": {"mse": leaky_mse, "r2": leaky_r2},
    }


def build_artifact(frame: Any, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or MANIFEST
    lab = manifest["leakage_lab"]
    target = lab["target"]
    eligible = _eligible_frame(frame, target)

    scenario_defs = lab["scenarios"]
    scenario_cols = {name: _scenario_columns(eligible, spec) for name, spec in scenario_defs.items()}

    entries: list[dict[str, Any]] = []
    for sample_size in lab["sample_sizes"]:
        for seed in lab["seeds"]:
            cohort = _cohort(eligible, sample_size, seed)
            train_idx, test_idx = _split(cohort, seed)
            y = cohort[target].to_numpy(dtype="float64")

            for scenario_name, spec in scenario_defs.items():
                X = cohort[scenario_cols[scenario_name]].to_numpy(dtype="float64")
                if scenario_name == "scaling":
                    metrics = _scaling_entry(X, y, train_idx, test_idx)
                elif scenario_name == "feature_selection":
                    metrics = _feature_selection_entry(X, y, train_idx, test_idx, spec["selected_feature_count"])
                elif scenario_name == "pca":
                    metrics = _pca_entry(X, y, train_idx, test_idx, spec["component_count"])
                else:  # pragma: no cover - manifest is fixed
                    raise ValueError(f"unknown scenario {scenario_name!r}")

                entries.append(
                    {
                        "scenario": scenario_name,
                        "sampleSize": sample_size,
                        "seed": seed,
                        "nTrain": int(len(train_idx)),
                        "nTest": int(len(test_idx)),
                        **metrics,
                    }
                )

    src = manifest["source"]
    scenarios_out = {
        name: {
            "bundle": spec["bundle"],
            "measures": spec["measures"],
            "featureCount": spec["feature_count"],
            "model": spec["model"],
            "leakyWorkflow": spec["leaky_workflow"],
            "correctWorkflow": spec["correct_workflow"],
            **({"selectedFeatureCount": spec["selected_feature_count"]} if "selected_feature_count" in spec else {}),
            **({"componentCount": spec["component_count"]} if "component_count" in spec else {}),
        }
        for name, spec in scenario_defs.items()
    }

    return {
        "schemaVersion": SCHEMA_VERSION,
        "activity": "leakage-lab",
        "source": {
            "pinnedCommit": src["pinned_commit"],
            "brainTableSha256": src["brain_table"]["sha256"],
        },
        "target": target,
        "sampleSizes": lab["sample_sizes"],
        "seeds": lab["seeds"],
        "scenarios": scenarios_out,
        "entries": entries,
    }


def validate_artifact(artifact: Any, manifest: dict[str, Any] | None = None) -> list[str]:
    manifest = manifest or MANIFEST
    problems: list[str] = []
    if not isinstance(artifact, dict):
        return ["artifact is not a JSON object"]
    if artifact.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if artifact.get("activity") != "leakage-lab":
        problems.append("activity must be 'leakage-lab'")

    lab = manifest["leakage_lab"]
    src = artifact.get("source", {})
    if src.get("pinnedCommit") != manifest["source"]["pinned_commit"]:
        problems.append("source.pinnedCommit does not match the manifest")
    if artifact.get("target") != lab["target"]:
        problems.append("target does not match the manifest")
    if artifact.get("sampleSizes") != lab["sample_sizes"]:
        problems.append("sampleSizes does not match the manifest")
    if artifact.get("seeds") != lab["seeds"]:
        problems.append("seeds does not match the manifest")

    expected_scenarios = set(lab["scenarios"])
    if set(artifact.get("scenarios", {})) != expected_scenarios:
        problems.append("scenarios keys do not match the manifest")

    entries = artifact.get("entries")
    if not isinstance(entries, list) or not entries:
        return problems + ["entries must be a non-empty array"]

    expected_keys = {
        (scenario, size, seed)
        for scenario in expected_scenarios
        for size in lab["sample_sizes"]
        for seed in lab["seeds"]
    }
    seen: set[tuple[str, int, int]] = set()
    required_fields = {"scenario", "sampleSize", "seed", "nTrain", "nTest", "correct", "leaky"}
    for e in entries:
        key = (e.get("scenario"), e.get("sampleSize"), e.get("seed"))
        if key in seen:
            problems.append(f"duplicate entry for {key}")
        seen.add(key)
        missing = required_fields - set(e)
        if missing:
            problems.append(f"entry {key}: missing field(s) {sorted(missing)}")
            continue
        if e["nTrain"] + e["nTest"] != (e["sampleSize"] if e["sampleSize"] in lab["sample_sizes"] else None):
            expected_total = e["sampleSize"]
            if e["nTrain"] + e["nTest"] != expected_total:
                problems.append(f"entry {key}: nTrain+nTest does not equal sampleSize")
        for side in ("correct", "leaky"):
            side_val = e[side]
            if set(side_val) != {"mse", "r2"}:
                problems.append(f"entry {key}: {side} must have exactly mse/r2")
                continue
            if side_val["mse"] < 0:
                problems.append(f"entry {key}: {side}.mse must be non-negative")

    if seen != expected_keys:
        problems.append("entries do not cover every (scenario, sample size, seed) combination exactly once")

    identifier_token = ("id", "sub", "subject", "site", "participant")
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
    lines = [
        f"activity     : {artifact['activity']}",
        f"target       : {artifact['target']}",
        f"sampleSizes  : {artifact['sampleSizes']}",
        f"seeds        : {artifact['seeds']}",
        f"scenarios    : {sorted(artifact['scenarios'])}",
        f"entries      : {len(artifact['entries'])}",
    ]
    return "\n".join(lines)


def cmd_refresh() -> int:
    frame = load_modeling_frame()
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
    mode.add_argument("--refresh", action="store_true", help="recompute + write the artifact (network)")
    mode.add_argument("--check", action="store_true", help="validate the committed artifact offline")
    args = parser.parse_args(argv)
    return cmd_refresh() if args.refresh else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
