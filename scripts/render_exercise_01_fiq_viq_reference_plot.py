#!/usr/bin/env python3
"""Render Exercise 1's FIQ-vs-VIQ reference image from the actual course data.

Computes the same paired-dropna, same-observations Pearson r the student
activity asks for, against the committed curated 13-column ABIDE-II export,
and saves the PNG that scripts/generate_exercise_01_notebook.py embeds
(base64, as a cell attachment) into the FIQ-vs-VIQ activity. Offline: reads
only the committed CSV, no network.

Run:
    .venv/bin/python scripts/render_exercise_01_fiq_viq_reference_plot.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_phenotypes.csv"
OUT_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_01_fiq_viq_reference.png"


def main() -> None:
    data = pd.read_csv(CSV_PATH)
    paired = data[["FIQ", "VIQ"]].dropna()
    r = paired["FIQ"].corr(paired["VIQ"])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(paired["FIQ"], paired["VIQ"], s=12, alpha=0.4, color="#2a6f9e")
    ax.set_xlabel("FIQ (full-scale IQ)")
    ax.set_ylabel("VIQ (verbal IQ)")
    ax.set_title(f"FIQ vs VIQ (n={len(paired)}, Pearson r = {r:.2f})")
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=110)
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}  (n={len(paired)}, r={r:.2f})")


if __name__ == "__main__":
    main()
