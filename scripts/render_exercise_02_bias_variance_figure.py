#!/usr/bin/env python3
"""Render Section 6's conceptual bias-variance illustration to a PNG.

WP42 Gate 1 item 5: this figure has always been a fixed, non-data-dependent
schematic (smooth idealised curves, not measured from the ABIDE data) --
exactly the kind of "opaque plotting code" the spec asks to replace with a
static image attachment, the same way Activity 3B's approved result already
works (see render_exercise_02_reference_plot.py). Offline: no data, no
network.

Run:
    .venv/bin/python scripts/render_exercise_02_bias_variance_figure.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_02_bias_variance_conceptual.png"


def main() -> None:
    flexibility = np.linspace(0.02, 1, 200)
    bias_sq = (1 - flexibility) ** 2 * 2.2
    variance = flexibility ** 2.2 * 2.0
    irreducible = np.full_like(flexibility, 0.35)
    expected_test_error = bias_sq + variance + irreducible

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(flexibility, bias_sq, label="squared bias", color="#2a6f9e")
    ax.plot(flexibility, variance, label="variance", color="#b5622f")
    ax.plot(flexibility, irreducible, label="irreducible error", color="0.6", ls=":")
    ax.plot(flexibility, expected_test_error, label="expected test error", color="black", lw=2)
    ax.set_xlabel("model flexibility (small k -> large k, right to left)")
    ax.set_ylabel("error (schematic units)")
    ax.set_title("The classic bias-variance tradeoff")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=110)
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
