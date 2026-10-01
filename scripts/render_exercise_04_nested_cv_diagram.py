#!/usr/bin/env python3
"""Render Exercise 4's nested-cross-validation diagram as a static PNG.

WP48: replaces a raw-HTML/inline-CSS markdown diagram
(``_NCV_DIAGRAM_HTML`` in scripts/generate_exercise_04_notebook.py) whose
fold-color bars rendered as invisible/ineffective in a real JupyterLite
notebook -- live screenshot evidence showed only the loose headings,
fold numbers, and arrows, with no visible colored blocks. Root cause:
every block's size AND color came from an inline ``style="..."`` attribute
on a bare ``<span>``, and JupyterLab/JupyterLite's markdown-HTML sanitizer
strips the ``style`` attribute from raw HTML by default -- confirmed by the
symptom pattern (plain text content survives, anything carried only by
``style=`` vanishes).

A rendered image sidesteps that sanitizer entirely: ``<img>`` (via a
notebook `attachment:`, the same nbformat mechanism
scripts/generate_exercise_02_notebook.py already uses for Activity 3B's
reference image and the bias-variance conceptual figure) is always allowed
through, in JupyterLite, local Jupyter, and Colab alike.

No student data or recipe numbers are read here -- this is a fixed
conceptual illustration, like the bias-variance figure, so N_OUTER/N_INNER
below are deliberately hard-coded to match
scripts/generate_exercise_04_notebook.py's own nested-CV blank
(``N_OUTER, N_INNER = 5, 5``) rather than imported from it.

Run:
    .venv/bin/python scripts/render_exercise_04_nested_cv_diagram.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_04_nested_cv_diagram.png"

N_OUTER = 5
N_INNER = 5
ZOOM_OUTER_ROW = 1  # 0-indexed; row 2 of 5, matching the prior diagram's choice

# Same palette the prior HTML diagram used (its CSS custom-property
# fallback colors), so the diagram's own established color meanings
# (outer train/test, inner train/val) do not change for anyone who already
# knows this course's convention.
COLOR_OUTER_TRAIN = "#a9c2e3"
COLOR_OUTER_TEST = "#e6c368"
COLOR_INNER_TRAIN = "#a3cbae"
COLOR_INNER_VAL = "#e0a877"
COLOR_ACCENT = "#dd5f1b"
COLOR_INK = "#1b1826"
COLOR_MUTED = "#5c5674"

BLOCK_W = 0.9
BLOCK_H = 0.62
BLOCK_GAP = 0.08
ROW_GAP = 0.32


def _fold_row(ax, x0, y0, n, highlight_idx, color_fill, color_other, outline=False):
    """Draw one row of n square-ish fold blocks; highlight_idx is filled
    with color_fill, every other block with color_other."""
    for i in range(n):
        x = x0 + i * (BLOCK_W + BLOCK_GAP)
        color = color_fill if i == highlight_idx else color_other
        rect = Rectangle(
            (x, y0), BLOCK_W, BLOCK_H,
            facecolor=color, edgecolor=COLOR_INK, linewidth=0.8, zorder=2,
        )
        ax.add_patch(rect)
    if outline:
        width = n * BLOCK_W + (n - 1) * BLOCK_GAP
        ax.add_patch(
            Rectangle(
                (x0 - 0.08, y0 - 0.08), width + 0.16, BLOCK_H + 0.16,
                facecolor="none", edgecolor=COLOR_ACCENT, linewidth=2.2, zorder=3,
            )
        )


def _legend_swatch(ax, x, y, color, label):
    ax.add_patch(Rectangle((x, y - 0.17), 0.34, 0.26, facecolor=color, edgecolor=COLOR_INK, linewidth=0.7, zorder=2))
    ax.text(x + 0.46, y, label, fontsize=9.5, va="center", ha="left", color=COLOR_INK)


def main() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 5.6), dpi=150)
    ax.set_xlim(0, 15.6)
    ax.set_ylim(0, 7.3)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # --- legend (top) ----------------------------------------------------
    legend_y = 7.0
    _legend_swatch(ax, 0.0, legend_y, COLOR_OUTER_TRAIN, "Outer training")
    _legend_swatch(ax, 3.1, legend_y, COLOR_OUTER_TEST, "Outer test")
    _legend_swatch(ax, 5.9, legend_y, COLOR_INNER_TRAIN, "Inner training")
    _legend_swatch(ax, 8.9, legend_y, COLOR_INNER_VAL, "Inner validation")

    # --- left panel: outer cross-validation -------------------------------
    left_x0 = 0.55
    top_y = 6.3
    ax.text(left_x0, top_y + 0.35, "Outer cross-validation", fontsize=11.5, fontweight="bold", color=COLOR_INK)
    ax.text(
        left_x0, top_y + 0.02,
        "5 outer iterations; the outer-test block (yellow) rotates.\nOutlined row: zoomed into on the right.",
        fontsize=8.3, color=COLOR_MUTED, va="top",
    )
    rows_top = top_y - 1.1
    for row in range(N_OUTER):
        y = rows_top - row * (BLOCK_H + ROW_GAP)
        ax.text(left_x0 - 0.3, y + BLOCK_H / 2, str(row + 1), fontsize=9, ha="right", va="center", color=COLOR_MUTED)
        _fold_row(
            ax, left_x0, y, N_OUTER, highlight_idx=row,
            color_fill=COLOR_OUTER_TEST, color_other=COLOR_OUTER_TRAIN,
            outline=(row == ZOOM_OUTER_ROW),
        )

    # --- arrow 1: left panel -> right panel --------------------------------
    arrow_y = rows_top - ZOOM_OUTER_ROW * (BLOCK_H + ROW_GAP) + BLOCK_H / 2
    left_end_x = left_x0 + N_OUTER * (BLOCK_W + BLOCK_GAP)
    right_x0 = left_end_x + 1.35
    ax.add_patch(
        FancyArrowPatch(
            (left_end_x + 0.15, arrow_y), (right_x0 - 0.2, arrow_y),
            arrowstyle="-|>", mutation_scale=16, color=COLOR_MUTED, linewidth=1.6, zorder=2,
        )
    )
    ax.text(
        (left_end_x + right_x0) / 2 + 0.07, arrow_y + 0.3, "zoom into\nouter-training", fontsize=7.6,
        color=COLOR_MUTED, ha="center", va="bottom", style="italic",
    )

    # --- right panel: inner cross-validation, zoomed from the outlined row
    ax.text(right_x0, top_y + 0.35, "Inner cross-validation", fontsize=11.5, fontweight="bold", color=COLOR_INK)
    ax.text(
        right_x0, top_y + 0.02,
        f"Zoomed from outer iteration {ZOOM_OUTER_ROW + 1}'s training data: 5 inner\n"
        "iterations; the inner-validation block (orange) rotates.",
        fontsize=8.3, color=COLOR_MUTED, va="top",
    )
    for row in range(N_INNER):
        y = rows_top - row * (BLOCK_H + ROW_GAP)
        ax.text(right_x0 - 0.3, y + BLOCK_H / 2, str(row + 1), fontsize=9, ha="right", va="center", color=COLOR_MUTED)
        _fold_row(
            ax, right_x0, y, N_INNER, highlight_idx=row,
            color_fill=COLOR_INNER_VAL, color_other=COLOR_INNER_TRAIN,
        )

    # --- arrow 2: right panel -> captions ----------------------------------
    right_end_x = right_x0 + N_INNER * (BLOCK_W + BLOCK_GAP)
    caption_x0 = right_end_x + 1.0
    ax.add_patch(
        FancyArrowPatch(
            (right_end_x + 0.15, arrow_y), (caption_x0 - 0.15, arrow_y),
            arrowstyle="-|>", mutation_scale=16, color=COLOR_MUTED, linewidth=1.6, zorder=2,
        )
    )

    # --- captions: the procedure, in order --------------------------------
    captions = [
        (COLOR_INNER_VAL, "Inner folds select k"),
        (COLOR_INK, "Refit the selected k on all of\nthis outer fold's training data"),
        (COLOR_OUTER_TEST, "Score once on this outer\nfold's own held-out test block"),
    ]
    cap_y = rows_top + BLOCK_H - 0.15
    for color, text in captions:
        ax.add_patch(Rectangle((caption_x0, cap_y - 0.62), 0.07, 0.62, facecolor=color, edgecolor="none", zorder=2))
        ax.text(caption_x0 + 0.22, cap_y - 0.08, text, fontsize=8.6, color=COLOR_INK, va="top")
        cap_y -= 1.0

    # --- footer: repeat/average note ---------------------------------------
    ax.text(
        left_x0, rows_top - N_OUTER * (BLOCK_H + ROW_GAP) + 0.05,
        "Repeat for every outer fold (5 total), then average the 5 outer-test scores --\n"
        "that average is the nested-CV estimate of the whole tuning procedure, not of one fixed k.",
        fontsize=8.6, color=COLOR_INK, va="top",
    )

    fig.savefig(OUT_PATH, dpi=150, facecolor="white", bbox_inches="tight", pad_inches=0.15)
    print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
