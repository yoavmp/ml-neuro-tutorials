#!/usr/bin/env python3
"""Compute Exercise 9's instructor/reference full-training-data SVR benchmark.

WP52 item 13: Exercise 9's own SVR task fits on a fixed 300-row SUBSET of
the training partition (see scripts/generate_exercise_09_notebook.py's
module docstring for why: a browser-native Pyodide kernel has no GPU and a
single thread, and a full-partition SVR fit is too slow there). That
subset's own scores are a responsive teaching exercise, not a measurement of
what the full 753-row training partition would produce -- they must never
be ranked against PCR/PLS/Ridge/KernelRidge, which the notebook always fits
on the full training partition.

This script computes that separate, full-training-data SVR number OFFLINE
(outside the browser, where runtime is not a constraint), with a
configuration chosen BEFORE looking at any validation outcome, and writes it
to scripts/reference_notebooks/exercise_09_svr_benchmark.json. The generator
(scripts/generate_exercise_09_notebook.py) reads that JSON and embeds its
numbers into Section 6's comparison, explicitly labeled as an instructor/
reference benchmark -- never as the student's own subset result, and never
copied from the old pre-WP51 nested-cross-validation summary.

Why these parameters, chosen without tuning: SVR()'s own scikit-learn
defaults (kernel="rbf", C=1.0, gamma="scale", epsilon=0.1), inside a
StandardScaler pipeline -- the simplest defensible "not tuned against this
validation set" choice available: the library's own out-of-the-box
configuration, decided before this script ever computed a validation score.
This is not claimed to be the best possible SVR configuration, only an
honest, reproducible, undertuned one -- see the resulting val_mse/val_r2
below, which do not uniformly beat every other method here.

Split: identical to every other exercise/every other model in this
notebook -- train_test_split(..., test_size=0.25, random_state=42,
stratify=group) on book/lite/files/data/abide_age_brain.csv.

Modes:
  --write   recompute and write the JSON artifact.
  --check   recompute in memory and fail if the committed JSON is stale.

Run:
    .venv/bin/python scripts/compute_exercise_09_svr_benchmark.py --write
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.csv"
OUT_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_svr_benchmark.json"

SPLIT_TEST_SIZE = 0.25
SPLIT_RANDOM_STATE = 42


def compute() -> dict:
    df = pd.read_csv(DATA_PATH).dropna(subset=["age"])
    features = [c for c in df.columns if c.startswith("fsCT_")]
    X = df[features].to_numpy(float)
    y = df["age"].to_numpy(float)
    group = df["group"].to_numpy()

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=SPLIT_TEST_SIZE, random_state=SPLIT_RANDOM_STATE, stratify=group
    )

    pipe = Pipeline([("scale", StandardScaler()), ("model", SVR())])
    t0 = time.time()
    pipe.fit(X_train, y_train)
    fit_seconds = time.time() - t0
    pred = pipe.predict(X_val)

    params = pipe.named_steps["model"].get_params()
    print(f"fit took {fit_seconds:.4f}s (not persisted -- wall-clock timing is not reproducible)")
    return {
        "description": (
            "Instructor/reference full-training-data SVR benchmark for "
            "Exercise 9, Section 6 -- NOT the student's own small-subset "
            "SVR activity result, and NOT the old pre-migration nested-CV "
            "summary. Computed offline by scripts/compute_exercise_09_svr_"
            "benchmark.py."
        ),
        "model": "SVR (scikit-learn library defaults, StandardScaler-scaled, full training partition)",
        "params": {"kernel": params["kernel"], "C": params["C"], "gamma": params["gamma"], "epsilon": params["epsilon"]},
        "params_chosen_without_validation_tuning": True,
        "split": {
            "test_size": SPLIT_TEST_SIZE,
            "random_state": SPLIT_RANDOM_STATE,
            "stratify": "group",
            "source": "book/lite/files/data/abide_age_brain.csv",
        },
        "n_train": int(X_train.shape[0]),
        "n_val": int(X_val.shape[0]),
        "n_features": int(X_train.shape[1]),
        "val_mse": round(float(mean_squared_error(y_val, pred)), 3),
        "val_r2": round(float(r2_score(y_val, pred)), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = compute()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.write:
        if OUT_PATH.exists() and OUT_PATH.read_text() == text:
            print("up to date")
        else:
            OUT_PATH.write_text(text)
            print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if not OUT_PATH.exists() or OUT_PATH.read_text() != text:
            raise SystemExit(f"stale (run --write): {OUT_PATH.relative_to(REPO_ROOT)}")
        print("OK: up to date")


if __name__ == "__main__":
    main()
