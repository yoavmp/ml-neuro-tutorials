#!/usr/bin/env python3
"""Render the Activity 3B reference image from the approved current result.

Fits the exact Section 1/3 pipeline (established recipe, split, and scaler)
against the same-origin ABIDE-II export and saves the observed-vs-predicted
PNG that scripts/generate_exercise_02_notebook.py embeds (base64, portably)
into Activity 3B. Offline: reads only the committed CSV, no network.

Run:
    .venv/bin/python scripts/render_exercise_02_reference_plot.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.csv"
OUT_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_02_observed_vs_predicted.png"


def main() -> None:
    data = pd.read_csv(CSV_PATH)
    features = [c for c in data.columns if c not in ("age", "group")]
    X = data[features].to_numpy()
    y = data["age"].to_numpy()
    groups = data["group"].to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=groups
    )
    scaler = StandardScaler().fit(X_train)
    model = LinearRegression().fit(scaler.transform(X_train), y_train)
    y_pred = model.predict(scaler.transform(X_test))
    test_r2 = r2_score(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(4.4, 4.4))
    lims = [min(y_test.min(), y_pred.min()) - 3, max(y_test.max(), y_pred.max()) + 3]
    ax.plot(lims, lims, "--", color="0.4", lw=1, label="Perfect prediction")
    ax.scatter(y_test, y_pred, s=16, alpha=0.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal")
    ax.set_xlabel("observed age (years)")
    ax.set_ylabel("predicted age (years, held-out)")
    ax.set_title(f"Linear regression, held-out R^2 = {test_r2:.3f}")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=110)
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}  (R^2={test_r2:.3f})")


if __name__ == "__main__":
    main()
