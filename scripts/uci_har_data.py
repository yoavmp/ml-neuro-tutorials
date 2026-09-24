#!/usr/bin/env python3
"""Loader + shared modelling code for the UCI HAR compact subset (WP38 sec 8).

The public UCI "Human Activity Recognition Using Smartphones" dataset
(https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones,
DOI 10.24432/C54S4K, CC BY 4.0) is 10,299 sensor-window rows from 30
participants performing six activities. The full archive (~58 MB) is never
committed to this repository; instead a compact derived table -- participant
id, activity label, and a fixed, interpretable 18-feature subset chosen by
measurement family (never by association with the activity label) -- is
committed at ``book/data/uci_har/uci_har_compact.csv.gz``, with provenance at
``book/data/uci_har/provenance.json``.

Notebook execution and CI are always offline: :func:`load_compact_table`
only ever reads the committed compact file. Fetching the original archive
(network) is the maintainer-only refresh path in
``scripts/export_uci_har_data.py``.

This module also holds the one shared implementation of the grouped-vs-random
fold comparison (:func:`fold_assignment`, :func:`run_cv`,
:func:`compute_fold_comparison`) used by both
``scripts/har_group_leakage_audit.py`` (the mandatory preflight / audit) and
``scripts/export_har_fold_widget_data.py`` (the browser activity) so the
notebook, audit, and frontend never maintain separate copies of the same
numbers (WP38 sec 13).
"""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "book" / "data" / "uci_har"
COMPACT_CSV_PATH = DATA_DIR / "uci_har_compact.csv.gz"
PROVENANCE_PATH = DATA_DIR / "provenance.json"

# The predeclared 18-feature subset (WP38 sec 8.1), chosen by measurement
# family (mean/std of body acceleration, gravity acceleration, and body
# angular velocity on each axis) -- never by association with the activity
# label. These are the official UCI HAR feature names, confirmed present
# verbatim in this archive version's features.txt.
FEATURE_SUBSET: tuple[str, ...] = (
    "tBodyAcc-mean()-X", "tBodyAcc-mean()-Y", "tBodyAcc-mean()-Z",
    "tBodyAcc-std()-X", "tBodyAcc-std()-Y", "tBodyAcc-std()-Z",
    "tGravityAcc-mean()-X", "tGravityAcc-mean()-Y", "tGravityAcc-mean()-Z",
    "tGravityAcc-std()-X", "tGravityAcc-std()-Y", "tGravityAcc-std()-Z",
    "tBodyGyro-mean()-X", "tBodyGyro-mean()-Y", "tBodyGyro-mean()-Z",
    "tBodyGyro-std()-X", "tBodyGyro-std()-Y", "tBodyGyro-std()-Z",
)

ACTIVITY_LABELS: dict[int, str] = {
    1: "WALKING",
    2: "WALKING_UPSTAIRS",
    3: "WALKING_DOWNSTAIRS",
    4: "SITTING",
    5: "STANDING",
    6: "LAYING",
}

PARTICIPANT_COLUMN = "participant_id"
ACTIVITY_ID_COLUMN = "activity_id"
ACTIVITY_LABEL_COLUMN = "activity_label"
COMPACT_COLUMNS: tuple[str, ...] = (PARTICIPANT_COLUMN, ACTIVITY_ID_COLUMN, ACTIVITY_LABEL_COLUMN) + FEATURE_SUBSET

K_VALUES: tuple[int, ...] = (1, 3, 5, 11, 25)
N_SPLITS = 5
SPLIT_SEED = 42


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_compact_table(path: Path = COMPACT_CSV_PATH) -> Any:
    """Read the committed compact table. Offline; no network access."""
    import pandas as pd

    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        frame = pd.read_csv(fh)
    missing = [c for c in COMPACT_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"{path}: missing expected column(s) {missing}")
    return frame[list(COMPACT_COLUMNS)]


def load_provenance(path: Path = PROVENANCE_PATH) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


# --- shared grouped-vs-random fold comparison -------------------------------


def fold_assignment(splitter: Any, X: Any, y: Any, groups: Any | None = None) -> Any:
    """Return an array mapping each row to its validation-fold index."""
    import numpy as np

    fold_id = np.full(len(X), -1, dtype=int)
    splits = splitter.split(X, y) if groups is None else splitter.split(X, y, groups=groups)
    for i, (_, val_idx) in enumerate(splits):
        fold_id[val_idx] = i
    return fold_id


def run_cv(fold_ids: Any, k: int, X: Any, y: Any, n_splits: int = N_SPLITS) -> dict[str, Any]:
    """5-fold CV (using a precomputed fold assignment) for one k, returning
    per-fold accuracy/macro-F1 plus a fixed confusion matrix from the first
    fold (fold 0), for display purposes only."""
    import numpy as np
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    accs, f1s, confusions = [], [], []
    for f in range(n_splits):
        train_idx = np.where(fold_ids != f)[0]
        val_idx = np.where(fold_ids == f)[0]
        pipe = Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsClassifier(n_neighbors=k))])
        pipe.fit(X[train_idx], y[train_idx])
        pred = pipe.predict(X[val_idx])
        accs.append(float(accuracy_score(y[val_idx], pred)))
        f1s.append(float(f1_score(y[val_idx], pred, average="macro")))
        confusions.append(confusion_matrix(y[val_idx], pred, labels=sorted(ACTIVITY_LABELS)).tolist())
    return {
        "accPerFold": [round(a, 6) for a in accs],
        "f1PerFold": [round(f, 6) for f in f1s],
        "accMean": round(float(np.mean(accs)), 6),
        "f1Mean": round(float(np.mean(f1s)), 6),
        "confusionPerFold": confusions,
    }


def compute_fold_comparison(frame: Any, k_values: tuple[int, ...] = K_VALUES) -> dict[str, Any]:
    """The one shared computation: ordinary vs. participant-grouped 5-fold
    CV for KNN at each predeclared k, plus participant/fold overlap counts.
    Used by both the audit script and the browser-data exporter."""
    from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

    X = frame[list(FEATURE_SUBSET)].to_numpy(dtype="float64")
    y = frame[ACTIVITY_ID_COLUMN].to_numpy()
    subject = frame[PARTICIPANT_COLUMN].to_numpy()

    ordinary_splitter = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SPLIT_SEED)
    grouped_splitter = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SPLIT_SEED)

    ordinary_fold = fold_assignment(ordinary_splitter, X, y)
    grouped_fold = fold_assignment(grouped_splitter, X, y, groups=subject)

    import pandas as pd

    df = pd.DataFrame({"subject": subject, "ord_fold": ordinary_fold, "grp_fold": grouped_fold})
    ord_folds_per_subject = df.groupby("subject")["ord_fold"].nunique()
    grp_folds_per_subject = df.groupby("subject")["grp_fold"].nunique()
    n_participants = int(df["subject"].nunique())
    n_cross_ordinary = int((ord_folds_per_subject > 1).sum())
    n_cross_grouped = int((grp_folds_per_subject > 1).sum())

    counts = df["subject"].value_counts()
    obs_per_participant = {
        "min": int(counts.min()),
        "median": float(counts.median()),
        "max": int(counts.max()),
        "mean": round(float(counts.mean()), 2),
    }

    k_results = []
    for k in k_values:
        ordinary = run_cv(ordinary_fold, k, X, y)
        grouped = run_cv(grouped_fold, k, X, y)
        k_results.append(
            {
                "k": k,
                "ordinary": ordinary,
                "grouped": grouped,
                "accGap": round(ordinary["accMean"] - grouped["accMean"], 6),
                "f1Gap": round(ordinary["f1Mean"] - grouped["f1Mean"], 6),
            }
        )

    # fold assignment diagram: which fold each participant lands in, for both methods
    participant_folds = []
    for sub_id in sorted(df["subject"].unique()):
        sub_rows = df.loc[df["subject"] == sub_id]
        participant_folds.append(
            {
                "participantId": int(sub_id),
                "ordinaryFolds": sorted(int(f) for f in sub_rows["ord_fold"].unique()),
                "groupedFold": int(sub_rows["grp_fold"].iloc[0]),
                "nObservations": int(len(sub_rows)),
            }
        )

    return {
        "nRows": int(len(frame)),
        "nParticipants": n_participants,
        "nActivities": len(ACTIVITY_LABELS),
        "observationsPerParticipant": obs_per_participant,
        "participantsCrossingFoldsOrdinary": n_cross_ordinary,
        "participantsCrossingFoldsGrouped": n_cross_grouped,
        "groupedFoldsDisjoint": n_cross_grouped == 0,
        "nSplits": N_SPLITS,
        "splitSeed": SPLIT_SEED,
        "kResults": k_results,
        "participantFolds": participant_folds,
    }
