#!/usr/bin/env python3
"""Generate Exercise 12's JupyterLite template, portable copy, and reference.

WP57: build Exercise 12 ("Common Mistakes and Pitfalls") as a local-only,
JupyterLite-native, generator-authored notebook in the exact architecture
WP41/WP44-WP47/WP51 established for Exercises 1-9 (hidden setup cell,
show_question() answer-key hiding, Blank-tagged student tasks, native
ipywidgets activities, generous sanity-check tolerances). See
scripts/generate_exercise_09_notebook.py for the pattern this module
duplicates (never imports -- each generator module is a self-contained,
independently regenerable source of truth, WP41 maintainer guide section
4.7).

**Local-only scope (WP57):** this is a from-scratch rebuild of the common-
mistakes casebook previously drafted (and locally reviewed) as the legacy
Exercise 10 (book/chapters/chapter_10/exercise_10.ipynb, WP38/WP38R),
reassigned to Exercise 12 because Exercise 10's own slot is occupied by
that legacy content and Exercise 11 is reserved. The legacy Exercise 10
notebook is left completely untouched -- preserved as a reviewable
historical source, not migrated or overwritten. This WP wires its outputs
into book/_toc.yml, book/_config.yml, and book/config/exercise_manifest.json
on this feature branch ONLY, for local author preview; none of this is
merged, pushed, or deployed (see WPs/WP57_ACTIVE_EXERCISE_12_COMMON_MISTAKES_LOCAL.md
and WPs/reports/WP57_REPORT.md for the full local-preview procedure and the
author's own later release decision).

Content: six independent cases plus a closing challenge, each following
run -> diagnose -> repair-or-compare -> inspect-the-consequence. Four
required student repair blanks (Cases 1, 2, 3, 5); Cases 4 and 6 are
interpretation-only. Two notebook-native ipywidgets activities (after Case
2 and after Case 3). The established same-origin ABIDE-II age/brain table
(book/lite/files/data/abide_age_brain.csv, reused from Exercises 2/4-9) is
used for Cases 1 and 3; Cases 2, 4, 5, and 6 use small, fixed-seed,
clearly-labeled synthetic data, chosen because the mechanism being taught
(target-informed PCA, extreme class imbalance, repeated-participant rows,
test-set peeking) needs full control over the generating process that a
real dataset cannot offer on demand.

Every number below was computed directly against the real data/generators
before writing a single generator line (see WPs/reports/WP57_REPORT.md for
the full verification transcript):

  Case 1 (ABIDE StandardScaler leakage; WP57R revision). One three-way
    split of the 1,004-participant, 360-predictor ABIDE-II age table --
    X_train (602), X_val (201), X_test (201), stratified by group,
    random_state=42 both stages -- shared with Case 3. The contaminated
    scaler is fit on X_train+X_val together (803 rows) -- NEVER X_test,
    which stays genuinely untouched for Case 3, unlike the WP57 original
    (which fit it on all 1,004 rows, including X_test). Feature
    fsCT_L_1_ROI's learned mean: contaminated (803 rows) = 2.371498,
    honest (X_train, 602 rows) = 2.371573 -- a difference of 0.000075; the
    largest such difference across all 360 features is 0.020635. The
    check cell no longer compares one feature to a loosely-toleranced
    constant (the WP57 original's TOLERANCE=0.01 was looser than the real
    diff and would have passed a leaky scaler by mistake) -- it compares
    scaler_honest.mean_ against X_train.mean(axis=0) directly, computed
    live, with TOLERANCE=1e-6; verified directly that a scaler fit on
    X_train passes (max diff ~1e-15, floating-point noise) and the
    supplied scaler_leaky fails (max diff 0.020635 >> 1e-6) -- see
    tests/test_exercise_12_reference_execution.py's
    test_case1_check_cell_passes_for_honest_and_fails_for_leaky.
    A second, score-level demonstration (KNeighborsRegressor, n_neighbors=5
    fixed before inspecting any result) compares leaky vs. honest scaling
    at three predetermined sizes, all drawn from the train+validation pool
    only (never X_test): full split (602/201) val MSE 32.715 (leaky) vs.
    32.390 (honest), leaky worse by 0.324; n=100 (fixed seed 0, 75/25
    train/val) 60.014 vs. 60.911, leaky *better* by 0.897; n=60 (same
    seed, 45/15) 10.334 vs. 10.630, leaky better by 0.296. Reported
    honestly as a small, direction-inconsistent effect -- not searched
    across seeds or sizes for a favorable result.
  Case 2 (synthetic PCA-with-y leakage; WP57R revision). n=200, x1/x2 ~
    N(0,1) independent, y = 1.5*x1 - 0.5*x2 + N(0,1) noise, seed=0;
    train/val split test_size=0.25, random_state=42. The WP57 original
    conflated two mistakes (PCA fit on ALL rows including held-out, AND y
    included as a column, with y additionally scaled 3x to force PC1
    dominance); this revision isolates ONE deliberate mistake: both paths
    now standardize their own input columns and fit PCA on TRAINING ROWS
    ONLY (no train/held-out leakage in the fitting scope for either path).
    The contaminated path's own three columns are [x1, x2, y] -- so
    transforming any row, including a held-out one, structurally requires
    that row's own y. Held-out R2: contaminated = 0.8973 (needs the
    held-out y as an input to produce), honest (columns [x1, x2] only,
    never needs y to transform a row) = 0.1209.
  Case 3 (ABIDE tree depth selection, same three-way split as Case 1).
    DecisionTreeRegressor(max_depth=d, random_state=0) for d in
    [1, 2, 3, 5, 10, None]: train/val/test MSE = 55.089/72.596/88.993,
    40.431/54.358/74.677, 28.966/46.895/58.856, 11.934/45.123/66.143,
    0.597/46.283/73.439, 0.000/46.524/74.740. Lowest-training-MSE picks
    depth=None (train MSE 0.0) -- test MSE 74.740. Lowest-validation-MSE
    picks depth=5 (val MSE 45.123) -- test MSE 66.143, genuinely better on
    the untouched test partition.
  Case 4 (synthetic 95:5 classifier). n=400, positive rate ~5% (seed=7);
    stratified split test_size=0.25, random_state=42 -> 100 validation
    rows, 5 of them positive. Always-predict-0: accuracy=0.95, confusion
    matrix [[95, 0], [5, 0]] (TN=95, FP=0, FN=5, TP=0), balanced
    accuracy=0.5, sensitivity=0.0, specificity=1.0, precision undefined
    (0/0 -- no positive predictions were ever made).
  Case 5 (synthetic repeated-participant rows). 40 participants x 8 rows
    each (n=320), seed=3: participant_signal ~ N(0, 2.0); predictor x =
    participant_signal + N(0, 0.15) ("epoch" noise); target y =
    participant_signal + N(0, 0.5). KNeighborsRegressor(n_neighbors=1).
    Row split (train_test_split, test_size=0.25, random_state=42): 38 of 40
    participants appear in both train and validation; val MSE=0.5375,
    val R2=0.8973. Group split (GroupShuffleSplit, test_size=0.25,
    random_state=42, groups=participant id): 0 participants appear in
    both; val MSE=0.6582, val R2=0.6219 -- lower, and honest.
  Case 6 (synthetic Ridge alpha chosen by peeking at the test set). n=150,
    10 features ~ N(0,1), seed=11; split test_size=0.3, random_state=42.
    Ridge alpha in [0.01, 0.1, 1, 10, 100], MSE evaluated directly on the
    test rows at every alpha: 7.584, 7.583, 7.573, 7.558, 9.679. Alpha=10
    is reported as "the" test MSE (7.558) -- but it was chosen by looking
    at that same test set five times first.

Outputs:
  book/lite/files/exercise_12.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_12/exercise_12_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_12_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_12_reference.ipynb (--reference)

Modes:
  --write   regenerate the selected output(s) on disk.
  --check   regenerate in memory and fail if a committed file is stale.
  --student / --reference / --all (default --all with --write or --check)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_SIDECAR = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.manifest.json"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_12.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_12" / "exercise_12_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_12_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_12_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 12, "templateVersion": TEMPLATE_VERSION},
}

# -- Case 1 / Case 3 shared ABIDE three-way split --------------------------
ABIDE_SPLIT_1_TEST_SIZE = 0.4  # first cut: 60% train / 40% rest
ABIDE_SPLIT_2_TEST_SIZE = 0.5  # second cut: rest -> 20% val / 20% test
ABIDE_SPLIT_RANDOM_STATE = 42

CASE1_WATCH_FEATURE_INDEX = 0
# scaler_leaky is fit on train+validation rows only (never X_test, which
# Case 3 later uses as a genuinely untouched partition) -- see the
# generator's own module docstring for the full reasoning.
CASE1_EXPECTED_MEAN_TRAIN_AND_VAL = 2.371498
CASE1_EXPECTED_MEAN_TRAIN = 2.371573
CASE1_EXPECTED_MAX_ABS_DIFF = 0.020635
CASE1_CHECK_TOLERANCE = 1e-6  # tight: scaler_honest.mean_ must equal X_train.mean(axis=0)

CASE1_KNN_K = 5  # fixed before inspecting any result below
CASE1_KNN_SMALL_SIZES = [100, 60]
CASE1_KNN_SMALL_SEED = 0
CASE1_KNN_SMALL_SPLIT_TEST_SIZE = 0.25
EXPECTED_CASE1_KNN_RESULTS = {
    "full": {"leaky_val_mse": 32.7146, "honest_val_mse": 32.3903},
    100: {"leaky_val_mse": 60.0136, "honest_val_mse": 60.9107},
    60: {"leaky_val_mse": 10.3340, "honest_val_mse": 10.6304},
}

TREE_DEPTH_GRID = [1, 2, 3, 5, 10, None]
EXPECTED_TREE_RESULTS = {
    1: {"train_mse": 55.089, "val_mse": 72.596, "test_mse": 88.993},
    2: {"train_mse": 40.431, "val_mse": 54.358, "test_mse": 74.677},
    3: {"train_mse": 28.966, "val_mse": 46.895, "test_mse": 58.856},
    5: {"train_mse": 11.934, "val_mse": 45.123, "test_mse": 66.143},
    10: {"train_mse": 0.597, "val_mse": 46.283, "test_mse": 73.439},
    None: {"train_mse": 0.000, "val_mse": 46.524, "test_mse": 74.740},
}
TREE_MSE_TOLERANCE = 3.0

# -- Case 2 synthetic constants --------------------------------------------
CASE2_SEED = 0
CASE2_N = 200
CASE2_SPLIT_TEST_SIZE = 0.25
CASE2_SPLIT_RANDOM_STATE = 42
CASE2_EXPECTED_CONTAMINATED_R2 = 0.8973
CASE2_EXPECTED_HONEST_R2 = 0.1209
CASE2_R2_TOLERANCE = 0.05

# -- Case 4 synthetic constants ---------------------------------------------
CASE4_SEED = 7
CASE4_N = 400
CASE4_POSITIVE_RATE = 0.05
CASE4_SPLIT_TEST_SIZE = 0.25
CASE4_SPLIT_RANDOM_STATE = 42

# -- Case 5 synthetic constants ---------------------------------------------
CASE5_SEED = 3
CASE5_N_PARTICIPANTS = 40
CASE5_ROWS_PER_PARTICIPANT = 8
CASE5_SIGNAL_SD = 2.0
CASE5_EPOCH_NOISE_SD = 0.15
CASE5_TARGET_NOISE_SD = 0.5
CASE5_SPLIT_TEST_SIZE = 0.25
CASE5_SPLIT_RANDOM_STATE = 42
CASE5_EXPECTED_ROW_R2 = 0.8973
CASE5_EXPECTED_GROUP_R2 = 0.6219
CASE5_R2_TOLERANCE = 0.1

# -- Case 6 synthetic constants ---------------------------------------------
CASE6_SEED = 11
CASE6_N = 150
CASE6_N_FEATURES = 10
CASE6_NOISE_SD = 3.0
CASE6_SPLIT_TEST_SIZE = 0.3
CASE6_SPLIT_RANDOM_STATE = 42
CASE6_ALPHAS = [0.01, 0.1, 1, 10, 100]
CASE6_EXPECTED_TEST_MSE = {0.01: 7.584, 0.1: 7.583, 1: 7.573, 10: 7.558, 100: 9.679}


def md(source: str, cell_id: str) -> dict:
    c = new_markdown_cell(source.strip() + "\n")
    c["id"] = cell_id
    return c


def code(source: str, cell_id: str, hidden: bool = False) -> dict:
    c = new_code_cell(source.strip() + "\n")
    c["id"] = cell_id
    if hidden:
        c["metadata"]["jupyter"] = {"source_hidden": True}
    return c


class Blank:
    """One YOUR CODE HERE activity: a (starter, solution) pair sharing an id."""

    def __init__(self, student_source: str, reference_source: str, cell_id: str, tags: list[str]):
        self.student_source = student_source
        self.reference_source = reference_source
        self.cell_id = cell_id
        self.tags = tags

    def render(self, mode: str) -> dict:
        source = self.student_source if mode == "student" else self.reference_source
        c = new_code_cell(source.strip() + "\n")
        c["id"] = self.cell_id
        if self.tags:
            c["metadata"]["tags"] = self.tags
        return c


def blank(student_source: str, reference_source: str, cell_id: str, tags: list[str] | None = None) -> Blank:
    return Blank(student_source, reference_source, cell_id, tags or [])


# --- the shared setup cell (hidden; infra, not teaching narrative) --------


def _feature_list_literal() -> str:
    sidecar = json.loads(DATA_SIDECAR.read_text())
    cols = sidecar["predictor_columns"]
    lines = ["_ABIDE_LITE_FEATURES = ["]
    for i in range(0, len(cols), 4):
        chunk = ", ".join(repr(c) for c in cols[i : i + 4])
        lines.append(f"    {chunk},")
    lines.append("]")
    return "\n".join(lines)


# Duplicates (never imports) generate_exercise_09_notebook.py's setup-cell
# pattern -- each generator module is a self-contained, independently
# regenerable source of truth (WP41 maintainer guide section 4.7).
SETUP_SOURCE_TEMPLATE = '''
import sys
import random
import warnings

warnings.filterwarnings("ignore", message=r"The (width|height|x|y) parameter as float was deprecated")

if sys.platform == "emscripten":
    # Running in the browser (JupyterLite). ipywidgets has no prebuilt
    # Pyodide package, unlike numpy/pandas/scikit-learn/matplotlib
    # (preloaded by the JupyterLite build, see book/lite/overrides.json),
    # so it is fetched here instead of by a student-run install cell.
    # Local Jupyter and Colab already have ipywidgets installed.
    import micropip

    await micropip.install(["ipywidgets"])

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML

{features_literal}

_ABIDE_TSV_URL = (
    "https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/"
    "e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/"
    "tu-machine-learning-yarkoni/data/abide2.tsv"
)


def load_abide_age_brain_table():
    """Return the age/brain table: 360 cortical-thickness predictors, age,
    and group (autism/control, used only to stratify splits -- never a
    model feature).

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout); falls back to the same pinned,
    checksummed public source this course already uses elsewhere.
    """
    from pathlib import Path

    local_path = Path("data/abide_age_brain.csv")
    if local_path.exists():
        table = pd.read_csv(local_path)
    else:
        table = pd.read_csv(_ABIDE_TSV_URL, sep="\\t")
    table = table.dropna(subset=["age"])
    return table[_ABIDE_LITE_FEATURES + ["age", "group"]].reset_index(drop=True)


_QUESTION_CSS = """
<style>
.checked-question .widget-checkbox { width: 100% !important; height: auto !important; }
.checked-question .widget-label-basic {
    width: 100% !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    height: auto !important;
}
.checked-question .widget-radio-box { width: 100% !important; }
.checked-question .widget-radio-box label {
    width: 100% !important;
    max-width: 100% !important;
    white-space: normal !important;
    height: auto !important;
    box-sizing: border-box;
    padding: 3px 0;
    line-height: 1.3;
}
</style>
"""


def _question_style_widget():
    return widgets.HTML(_QUESTION_CSS, layout=widgets.Layout(height="0px", margin="0px", padding="0px"))


_WIDGET_CONTROL_CSS = """
<style>
.widget-controls-row { flex-wrap: wrap !important; row-gap: 6px; column-gap: 12px; }
.widget-controls-row > * { margin: 2px 10px 2px 0 !important; max-width: 100%; }
.widget-controls-row .widget-label {
    width: auto !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
}
.widget-controls-row .widget-dropdown { width: auto !important; }
.widget-controls-row .widget-inline-hbox { width: auto !important; flex-wrap: nowrap; }
</style>
"""


def _widget_control_style_widget():
    return widgets.HTML(_WIDGET_CONTROL_CSS, layout=widgets.Layout(height="0px", margin="0px", padding="0px"))


def controls_row(*widgets_):
    """An HBox of controls that wraps instead of overflowing/overlapping at
    narrow widths, with every description label shown in full."""
    box = widgets.HBox(
        [_widget_control_style_widget(), *widgets_],
        layout=widgets.Layout(width="100%", flex_flow="row wrap"),
    )
    box.add_class("widget-controls-row")
    return box


def scatter_true_vs_pred(ax, y_true, pred, axis_range, title, point_kwargs=None):
    """A true-vs-predicted scatter with a shared, fixed axis range and a
    diagonal guide line -- used by more than one activity below so every
    toggle setting is visually comparable."""
    point_kwargs = point_kwargs or {}
    ax.scatter(y_true, pred, s=28, alpha=0.75, edgecolors="0.3", linewidths=0.3, **point_kwargs)
    lo, hi = axis_range
    ax.plot([lo, hi], [lo, hi], color="0.5", linestyle="--", linewidth=1, label="perfect prediction")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("True value")
    ax.set_ylabel("Predicted value")
    ax.set_title(title)


def make_single_choice_question(prompt, options, correct_index, feedback_correct="Correct.", feedback_incorrect="Not quite -- try again."):
    """A compact single-choice checked question. Returns a widget to display()."""
    radio = widgets.RadioButtons(options=list(options), description="", layout=widgets.Layout(width="100%"))
    button = widgets.Button(description="Check answer", button_style="primary")
    feedback = widgets.Output()

    def _on_click(_button):
        with feedback:
            feedback.clear_output(wait=True)
            print(feedback_correct if radio.index == correct_index else feedback_incorrect)

    button.on_click(_on_click)
    box = widgets.VBox(
        [_question_style_widget(), widgets.HTML(f"<b>{prompt}</b>"), radio, button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("checked-question")
    return box


def make_multi_choice_question(prompt, statements, correct_indices, feedback_correct="Correct."):
    """A "mark all correct answers" checked question: one checkbox per
    short statement; any subset may be selected. Feedback is sensible for a
    fully correct, fully wrong, or partial selection, without revealing
    which specific statements were right or wrong."""
    checkboxes = [
        widgets.Checkbox(value=False, description=s, indent=False, layout=widgets.Layout(width="100%"))
        for s in statements
    ]
    button = widgets.Button(description="Check answers", button_style="primary")
    feedback = widgets.Output()

    def _on_click(_button):
        selected = {i for i, cb in enumerate(checkboxes) if cb.value}
        with feedback:
            feedback.clear_output(wait=True)
            if selected == correct_indices:
                print(feedback_correct)
            else:
                n_right = len(selected & correct_indices)
                n_true = len(correct_indices)
                extra = len(selected - correct_indices)
                missed = len(correct_indices - selected)
                parts = [f"Not quite: {n_right} of {n_true} true statements selected."]
                if extra:
                    parts.append(f"{extra} selected statement(s) are not true.")
                if missed:
                    parts.append(f"{missed} true statement(s) were not selected.")
                print(" ".join(parts))

    button.on_click(_on_click)
    box = widgets.VBox(
        [_question_style_widget(), widgets.HTML(f"<b>{prompt}</b> <i>(mark all that are correct)</i>"), *checkboxes, button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("checked-question")
    return box


# Question content lives here, not in the visible cell that displays it: a
# visible call like show_question("q-leakage") never prints or displays a
# correct_index/correct_indices value. Every option/statement list below is
# written with its correct answer(s) first, for readability -- show_question
# shuffles the DISPLAYED order with a fixed, per-question seed --
# reproducible across runs/reruns of the same cell, but different across
# questions, so correct answers no longer land on the same position every
# time.
_QUESTIONS = {
    "q-scaler-leakage": dict(
        type="single",
        shuffle_seed=2,
        prompt=(
            "The flawed version above fit StandardScaler on the full table "
            "(train and held-out rows together) before any split. What "
            "information actually crossed the train/validation boundary?"
        ),
        options=[
            "The mean and standard deviation used to rescale every predictor -- computed using the held-out rows, even though the held-out rows' own labels were never looked at.",
            "Nothing meaningful crossed the boundary, because StandardScaler never looks at the target column.",
            "The held-out rows' age values were copied into the training labels.",
        ],
        correct_index=0,
        feedback_correct="Correct: StandardScaler's mean_/scale_ are themselves information about which rows were used to fit it. Fitting on held-out rows leaks their predictor values into preprocessing, even though no target was involved.",
    ),
    "q-pca-deployment": dict(
        type="single",
        shuffle_seed=9,
        prompt=(
            "Suppose this contaminated pipeline is handed a brand-new "
            "participant whose age is genuinely unknown. What would you "
            "need, that you would not actually have, to run that "
            "participant through the same transform used above?"
        ),
        options=[
            "The new participant's own age -- the exact value the model is supposed to predict -- because it was one of the three columns PCA was fit on.",
            "Nothing extra: the fitted PCA object only needs the two predictor columns to transform a new row.",
            "A larger sample size, since PCA always needs many rows to transform even one new observation.",
        ],
        correct_index=0,
        feedback_correct="Correct: because y was one of the columns PCA decomposed, reproducing that exact transform for a new row requires that row's own target -- which is precisely what you are trying to predict.",
    ),
    "q-train-vs-val-select": dict(
        type="single",
        shuffle_seed=14,
        prompt=(
            "The flawed version above picked the tree depth with the "
            "lowest TRAINING MSE. Why is training MSE a poor way to choose "
            "among model settings, in general?"
        ),
        options=[
            "Training MSE can always be driven toward zero by making the model more flexible (deeper trees, more parameters), so the lowest-training-MSE setting is often simply the most flexible one allowed -- regardless of how well it generalizes.",
            "Training MSE is computed incorrectly by scikit-learn for tree models, so its value cannot be trusted at all.",
            "Training MSE and validation MSE always agree once enough training data is available, so the choice should not matter here.",
        ],
        correct_index=0,
        feedback_correct="Correct: an unconstrained tree can memorize the training rows arbitrarily well, so the lowest-training-MSE setting tends to be whichever one overfits the most -- not whichever one will perform best on new data.",
    ),
    "q-tree-deploy": dict(
        type="single",
        shuffle_seed=5,
        prompt=(
            "Looking at the two depths marked on the curves above and "
            "their scores on the untouched test set, what does this "
            "comparison actually show?"
        ),
        options=[
            "A depth chosen for its training performance can genuinely generalize worse than a depth chosen for its validation performance -- validation performance is not guaranteed to win, but it is the honest basis for the choice.",
            "The test set must have been mislabeled, since a deeper tree with lower training error should always score at least as well on new data.",
            "This pattern only happens with decision trees; linear models chosen by training score never show it.",
        ],
        correct_index=0,
        feedback_correct="Correct: training-based selection can and does generalize worse here. Validation-based selection is not a guarantee of winning on every dataset -- it is simply the honest, deployment-relevant basis for the choice.",
    ),
    "q-classifier-metrics": dict(
        type="multi",
        shuffle_seed=18,
        prompt="Based on the confusion matrix above, which of the following statements are true?",
        statements=[
            "Sensitivity (recall for the positive class) is 0.0 -- the classifier caught none of the 5 true positive cases.",
            "Specificity is 1.0 -- every true negative was correctly identified as negative.",
            "Precision is undefined here, because the classifier never predicted the positive class at all (0 predicted positives).",
            "Balanced accuracy (the average of sensitivity and specificity) is 0.95, the same as plain accuracy.",
            "Because accuracy is 95%, at least one of the 5 positive cases must have been caught.",
            "A classifier that always predicts the majority class can still report high plain accuracy whenever that class is common.",
        ],
        correct_indices={0, 1, 2, 5},
        feedback_correct="Correct: sensitivity 0.0 and specificity 1.0 both follow directly from the confusion matrix; precision is undefined with zero predicted positives; and a majority-class classifier's accuracy simply tracks how common that class already is -- balanced accuracy here is 0.5, not 0.95, and high accuracy does not imply any positive case was caught.",
    ),
    "q-group-leakage": dict(
        type="single",
        shuffle_seed=11,
        prompt=(
            "With the random row split, a 1-nearest-neighbor model scored "
            "far better on validation than with the group-aware split. "
            "What let it do that?"
        ),
        options=[
            "With the row split, most validation rows had another row from the SAME participant sitting in the training set -- nearly identical in this predictor -- so the nearest neighbor was essentially a copy, not a genuine generalization to a new participant.",
            "The row split and the group split used different random seeds for the underlying data, so the comparison is not meaningful.",
            "1-nearest-neighbor models are always more accurate than other models on repeated-measures data, regardless of how the split is made.",
        ],
        correct_index=0,
        feedback_correct="Correct: because the predictor itself carries a stable, participant-specific signal, a row-level split lets the model match a held-out row to an almost-identical training row from the same participant -- not to information that would generalize to a genuinely new participant.",
    ),
    "q-test-peeking": dict(
        type="single",
        shuffle_seed=7,
        prompt=(
            "At which point did the test set stop being an untouched, "
            "one-time evaluation in the code above?"
        ),
        options=[
            "As soon as its score was computed for more than one candidate setting and used to decide which setting to keep -- from then on, the test score was guiding a choice, not just reporting on one.",
            "Only at the very end, when the chosen alpha's test MSE was printed as the final result.",
            "It never stopped being untouched, because the test rows themselves were never modified.",
        ],
        correct_index=0,
        feedback_correct="Correct: a test score becomes part of the decision the moment it is compared across candidates to choose among them -- regardless of whether the data itself was touched. After that point, it can no longer honestly stand in for a one-time, untouched evaluation.",
    ),
}


def show_question(question_id):
    q = _QUESTIONS[question_id]
    seed = q["shuffle_seed"]
    if q["type"] == "multi":
        order = list(range(len(q["statements"])))
        random.Random(seed).shuffle(order)
        shuffled_statements = [q["statements"][i] for i in order]
        shuffled_correct = {order.index(i) for i in q["correct_indices"]}
        widget = make_multi_choice_question(
            q["prompt"], shuffled_statements, shuffled_correct, q.get("feedback_correct", "Correct.")
        )
    else:
        order = list(range(len(q["options"])))
        random.Random(seed).shuffle(order)
        shuffled_options = [q["options"][i] for i in order]
        shuffled_correct = order.index(q["correct_index"])
        widget = make_single_choice_question(
            q["prompt"],
            shuffled_options,
            shuffled_correct,
            q.get("feedback_correct", "Correct."),
            q.get("feedback_incorrect", "Not quite -- try again."),
        )
    display(widget)
'''.strip()


def _setup_cell(mode: str) -> dict:
    source = SETUP_SOURCE_TEMPLATE.replace("{features_literal}", _feature_list_literal())
    return code(source, "wp57-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp57-000a-run-first",
    )


# --- title and overview ----------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 12: Common Mistakes and Pitfalls", "wp57-001-title"),
        md(
            """
## How This Notebook Works

This is Exercise 12 of *Machine Learning for Neuroscience*. Every method
you have used so far can also be used incorrectly in a way that still runs
without error -- **that is the real danger**. This notebook is a short tour
of six such cases.

Each case below contains code that runs without any error and produces a
plausible-looking result -- but in most cases, that result is either
invalid or needlessly poor. The pattern repeats throughout: **run** the
supplied code, **diagnose** what actually happened, **repair** it or
compare it against a corrected version, then **inspect the consequence**
of the difference. Section headings describe what each case is about, not
what is wrong with it -- working that out is the point.

Written-answer cells (bold questions in a blockquote) are ordinary
Markdown: double-click one to edit it, type your answer, then press
Shift+Enter to render it back. Your answer is saved with the rest of this
notebook, including in **Download my notebook**.

**Prerequisites:** Exercise 2 (regression), Exercise 3 (classification and
metrics), Exercise 4 (validation and cross-validation), Exercise 6
(decision trees), and Exercise 8 (PCA).
""",
            "wp57-002-overview",
        ),
    ]


# --- Case 1: Preparing the Predictors ---------------------------------------


def _case1() -> list[dict]:
    return [
        md("## 1. Preparing the Predictors", "wp57-101-header"),
        md(
            """
This case reuses the familiar 1,004-participant, 360-predictor ABIDE-II
age table. Here it is split **three ways**: a training partition, a
validation partition (used for a model-setting decision in Case 3), and a
test partition (an untouched partition, checked only once, also used in
Case 3). All three stay fixed for the rest of this notebook.
""",
            "wp57-102-intro",
        ),
        code(
            """
try:
    df = load_abide_age_brain_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_age_brain_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under "
        "'Run the cell below first') before this one, then run this cell again."
    ) from exc

from sklearn.model_selection import train_test_split

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
X = df[FEATURES].to_numpy(float)
y = df["age"].to_numpy(float)
group = df["group"].to_numpy()

X_train, X_rest, y_train, y_rest, group_train, group_rest = train_test_split(
    X, y, group, test_size=%(split1)r, random_state=%(seed)r, stratify=group
)
X_val, X_test, y_val, y_test, group_val, group_test = train_test_split(
    X_rest, y_rest, group_rest, test_size=%(split2)r, random_state=%(seed)r, stratify=group_rest
)
print(f"data table: {df.shape[0]} participants x {len(FEATURES)} cortical-thickness predictors")
print(f"X_train: {X_train.shape}   X_val: {X_val.shape}   X_test: {X_test.shape}")
"""
            % {"split1": ABIDE_SPLIT_1_TEST_SIZE, "split2": ABIDE_SPLIT_2_TEST_SIZE, "seed": ABIDE_SPLIT_RANDOM_STATE},
            "wp57-103-load-split",
        ),
        md(
            """
### First, the Code

Below, `StandardScaler` is fit once, on the training and validation rows
together -- before anything is split further -- never on `X_test`, which
stays reserved, genuinely untouched, for Case 3. It then rescales
`X_train` for a simple linear model.
""",
            "wp57-104-run-it-intro",
        ),
        code(
            """
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

WATCH_FEATURE = FEATURES[%(idx)r]

X_train_and_val = np.concatenate([X_train, X_val])
scaler_leaky = StandardScaler().fit(X_train_and_val)  # fit on train + validation rows -- never X_test
X_train_scaled_leaky = scaler_leaky.transform(X_train)

leaky_model = LinearRegression().fit(X_train_scaled_leaky, y_train)
print(f"Learned mean for {WATCH_FEATURE}: {scaler_leaky.mean_[%(idx)r]:.6f}")
print("The model trains and predicts without any error.")
"""
            % {"idx": CASE1_WATCH_FEATURE_INDEX},
            "wp57-105-run-it",
        ),
        md(
            """
### Think first

> **What information crossed the train/validation boundary here, and did
> it include the target (`age`)?**
""",
            "wp57-106-diagnose-prompt",
        ),
        code(
            """
show_question("q-scaler-leakage")
""",
            "wp57-107-q-scaler-leakage",
        ),
        md(
            """
### Repair

Refit `StandardScaler` using **only** `X_train` -- ideally inside a
`Pipeline` together with the linear model, so the same rule automatically
applies every time this code is reused with a different split.

Required output name: `scaler_honest` -- the `StandardScaler` instance,
fit on `X_train` only.
""",
            "wp57-108-instructions",
        ),
        blank(
            """
scaler_honest = None

# YOUR CODE HERE
# Hint: fit a fresh StandardScaler using X_train only -- never
# X_train_and_val, X_rest, X_val, or X_test. Consider wrapping
# StandardScaler and the linear model together using scikit-learn's
# Pipeline class.
""",
            """
from sklearn.pipeline import Pipeline

scaler_honest = StandardScaler().fit(X_train)
honest_pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("model", LinearRegression()),
]).fit(X_train, y_train)
""",
            "wp57-109-case1-blank",
            tags=["wp57-activity-scaler"],
        ),
        code(
            """
# Run this to check your repair.
TOLERANCE = %(tol)r  # tight: scaler_honest.mean_ must equal X_train's own feature means

if "scaler_honest" in globals() and scaler_honest is not None:
    expected_mean_vector = X_train.mean(axis=0)
    max_diff = float(np.max(np.abs(scaler_honest.mean_ - expected_mean_vector)))
    if max_diff <= TOLERANCE:
        print(f"Looks good: scaler_honest's learned mean matches X_train's own feature means (largest difference {max_diff:.2e}).")
        leaky_max_diff = float(np.max(np.abs(scaler_leaky.mean_ - expected_mean_vector)))
        print(f"For comparison, the contaminated scaler's mean differs from X_train's own means by up to {leaky_max_diff:.6f} across features -- small here, but real.")
        print(
            "This check compares your scaler's learned mean vector to X_train's own feature means; it "
            "cannot by itself prove every possible solution is leakage-free -- that still comes from "
            "fitting on X_train alone."
        )
    else:
        print(
            f"Not quite: scaler_honest's learned mean differs from X_train's own feature means by up to "
            f"{max_diff:.6f}, more than this tight tolerance allows. Check that it was fit on X_train only "
            f"(not X_train_and_val, X_rest, X_val, or X_test)."
        )
else:
    print("Not complete yet: define scaler_honest above first.")
"""
            % {"tol": CASE1_CHECK_TOLERANCE},
            "wp57-110-case1-check",
        ),
        md(
            """
### Consequence

The difference above is small -- a few thousandths, for the feature shown
-- in this 602-participant training partition. That does not mean the
mistake is harmless in general: in a smaller study, for example one with
only 60 participants, the same kind of leak could shift the learned
statistics by considerably more, since each participant then carries a
much larger share of the total. Whether the effect ends up small or large
depends on the data and the sample size -- not on whether the mistake
happened at all.
""",
            "wp57-111-consequence",
        ),
        md(
            """
### Does It Change a Prediction Score?

The mean-vector difference above is small. Does it actually change what a
model predicts? Ordinary `LinearRegression` with an intercept is
mathematically unaffected by a *consistent* rescaling of every feature, so
it cannot show this either way -- a scale-**sensitive** model is needed
instead. Below, a `KNeighborsRegressor` (`n_neighbors` fixed before looking
at any result) is fit twice -- once using each scaler -- and scored on the
same held-out rows: first at the existing split's full size, then (since a
602-participant difference may be too small to show much) at two smaller,
fixed-seed sample sizes. All three draws come only from the train/validation
rows already in use above -- never from `X_test`, which stays reserved for
Case 3.
""",
            "wp57-112-knn-intro",
        ),
        code(
            """
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error


def _case1_compare_knn(X_tr, y_tr, X_va, y_va):
    train_and_val = np.concatenate([X_tr, X_va])
    leaky_scaler = StandardScaler().fit(train_and_val)
    honest_scaler = StandardScaler().fit(X_tr)
    leaky_pred = (
        KNeighborsRegressor(n_neighbors=CASE1_KNN_K)
        .fit(leaky_scaler.transform(X_tr), y_tr)
        .predict(leaky_scaler.transform(X_va))
    )
    honest_pred = (
        KNeighborsRegressor(n_neighbors=CASE1_KNN_K)
        .fit(honest_scaler.transform(X_tr), y_tr)
        .predict(honest_scaler.transform(X_va))
    )
    return {
        "n_train": len(X_tr),
        "n_val": len(X_va),
        "leaky_val_mse": float(mean_squared_error(y_va, leaky_pred)),
        "honest_val_mse": float(mean_squared_error(y_va, honest_pred)),
    }


CASE1_KNN_K = %(k)r  # fixed before inspecting any result below

case1_knn_results = {}
case1_knn_results["full"] = _case1_compare_knn(X_train, y_train, X_val, y_val)

# Smaller, fixed-seed sample sizes -- drawn only from the train/validation
# pool already in use, never from X_test.
_case1_pool_X = np.concatenate([X_train, X_val])
_case1_pool_y = np.concatenate([y_train, y_val])
_case1_pool_group = np.concatenate([group_train, group_val])

for n_total in %(sizes)s:
    sub_idx, _ = train_test_split(
        np.arange(len(_case1_pool_X)), train_size=n_total, random_state=%(small_seed)r, stratify=_case1_pool_group
    )
    sub_X, sub_y, sub_group = _case1_pool_X[sub_idx], _case1_pool_y[sub_idx], _case1_pool_group[sub_idx]
    tr_idx, va_idx = train_test_split(
        np.arange(n_total), test_size=%(small_test_size)r, random_state=%(small_seed)r, stratify=sub_group
    )
    case1_knn_results[n_total] = _case1_compare_knn(sub_X[tr_idx], sub_y[tr_idx], sub_X[va_idx], sub_y[va_idx])

for size_label, r in case1_knn_results.items():
    diff = r["leaky_val_mse"] - r["honest_val_mse"]
    direction = "worse" if diff > 0 else ("better" if diff < 0 else "identical")
    label = "full split" if size_label == "full" else f"n={size_label}"
    print(
        f"{label} (n_train={r['n_train']}, n_val={r['n_val']}): "
        f"leaky val MSE={r['leaky_val_mse']:.3f}  honest val MSE={r['honest_val_mse']:.3f}  "
        f"(leaky {direction} by {abs(diff):.3f})"
    )
"""
            % {
                "k": CASE1_KNN_K,
                "sizes": repr(CASE1_KNN_SMALL_SIZES),
                "small_seed": CASE1_KNN_SMALL_SEED,
                "small_test_size": CASE1_KNN_SMALL_SPLIT_TEST_SIZE,
            },
            "wp57-113-knn-compare",
        ),
        md(
            """
At every size tried here, the difference is small, and at the two smaller
sizes the contaminated scaler actually scores *better*, not worse -- a
legitimate possible outcome, since a small leak's effect is not guaranteed
to go in any particular direction. What stays true regardless of the
score: the contaminated scaler used information from rows it will later be
evaluated on, and a genuinely new participant would not be available to
fit it that way.
""",
            "wp57-114-knn-wrapup",
        ),
    ]


# --- Case 2: Two Components -------------------------------------------------


def _case2() -> list[dict]:
    return [
        md("## 2. Two Components", "wp57-201-header"),
        md(
            """
This case uses a small, synthetic regression example (not ABIDE data):
200 observations, two predictors `x1`/`x2`, and a target `y` built from
them plus noise, so the true relationship is known and controllable.
""",
            "wp57-202-intro",
        ),
        md(
            """
### First, the Code

Below, each path applies the same recipe: standardize its own input
columns (fit on training rows only), then fit a 1-component PCA on those
scaled training rows. The contaminated path's input columns are `x1`,
`x2`, and `y` itself -- so transforming *any* row through this fitted
pipeline, including a held-out one, requires that row's own `y`. The
resulting component is then used to predict `y`, including on held-out
rows whose own `y` it already needed.
""",
            "wp57-203-run-it-intro",
        ),
        code(
            """
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

rng = np.random.RandomState(%(seed)r)
n = %(n)r
x1 = rng.normal(0, 1, n)
x2 = rng.normal(0, 1, n)
noise = rng.normal(0, 1, n)
case2_y = 1.5 * x1 - 0.5 * x2 + noise  # synthetic -- not ABIDE

case2_train_idx, case2_val_idx = train_test_split(
    np.arange(n), test_size=%(test_size)r, random_state=%(split_seed)r
)

# The matrix PCA decomposes includes y itself as a column. The scaler and
# PCA below are both fit on TRAINING ROWS ONLY -- but because y is one of
# the columns, transforming ANY row (including a held-out one) still
# requires that row's own y.
contaminated_cols = np.column_stack([x1, x2, case2_y])
contaminated_scaler = StandardScaler().fit(contaminated_cols[case2_train_idx])
pca_contaminated = PCA(n_components=1, random_state=0).fit(
    contaminated_scaler.transform(contaminated_cols[case2_train_idx])
)

contaminated_scores_train = pca_contaminated.transform(
    contaminated_scaler.transform(contaminated_cols[case2_train_idx])
).ravel()
contaminated_scores_val = pca_contaminated.transform(
    contaminated_scaler.transform(contaminated_cols[case2_val_idx])  # needs the held-out y!
).ravel()

contaminated_model = LinearRegression().fit(
    contaminated_scores_train.reshape(-1, 1), case2_y[case2_train_idx]
)
contaminated_pred_val = contaminated_model.predict(contaminated_scores_val.reshape(-1, 1))
contaminated_r2 = r2_score(case2_y[case2_val_idx], contaminated_pred_val)
print(f"Contaminated pipeline, held-out R2: {contaminated_r2:.4f}")
"""
            % {
                "seed": CASE2_SEED,
                "n": CASE2_N,
                "test_size": CASE2_SPLIT_TEST_SIZE,
                "split_seed": CASE2_SPLIT_RANDOM_STATE,
            },
            "wp57-204-run-it",
        ),
        md(
            """
### Think first

> **To run a genuinely new participant through this exact pipeline, what
> would you need that you would not actually have?**
""",
            "wp57-205-diagnose-prompt",
        ),
        code(
            """
show_question("q-pca-deployment")
""",
            "wp57-206-q-pca-deployment",
        ),
        md(
            """
### Repair

Build a **predictor-only** matrix (`x1`, `x2` -- never `y`). Standardize
it (fit on `case2_train_idx` rows only), fit a 1-component PCA on those
same scaled training rows, then transform the held-out rows with that
same fitted scaler and PCA. Fit the linear regression on the training
rows' component, and score it on the held-out rows.

Required output name: `honest_pca_r2` -- the held-out R2 of this
predictor-only pipeline.
""",
            "wp57-207-instructions",
        ),
        blank(
            """
honest_pca_r2 = None

# YOUR CODE HERE
# Hint: build a predictor-only matrix from x1 and x2 alone -- never
# including case2_y. Standardize it, fit on the training rows only, then
# fit a 1-component PCA on those same scaled training rows. Apply that
# same fitted scaler and PCA to the validation rows to get their
# component scores -- no y needed anywhere in this path.
""",
            """
predictor_only_cols = np.column_stack([x1, x2])
honest_scaler = StandardScaler().fit(predictor_only_cols[case2_train_idx])
pca_honest = PCA(n_components=1, random_state=0).fit(
    honest_scaler.transform(predictor_only_cols[case2_train_idx])
)
honest_scores_train = pca_honest.transform(
    honest_scaler.transform(predictor_only_cols[case2_train_idx])
).ravel()
honest_scores_val = pca_honest.transform(
    honest_scaler.transform(predictor_only_cols[case2_val_idx])
).ravel()

honest_model = LinearRegression().fit(honest_scores_train.reshape(-1, 1), case2_y[case2_train_idx])
honest_pred_val = honest_model.predict(honest_scores_val.reshape(-1, 1))
honest_pca_r2 = r2_score(case2_y[case2_val_idx], honest_pred_val)
""",
            "wp57-208-case2-blank",
            tags=["wp57-activity-pca"],
        ),
        code(
            """
# Run this to check your repair.
EXPECTED_HONEST_R2 = %(expected)r
TOLERANCE = %(tol)r

if "honest_pca_r2" in globals() and honest_pca_r2 is not None:
    diff = abs(honest_pca_r2 - EXPECTED_HONEST_R2)
    print(f"Contaminated pipeline (needs the held-out y as input): held-out R2 = {contaminated_r2:.4f}  -- INVALID, do not use")
    print(f"Honest pipeline (predictor-only):                      held-out R2 = {honest_pca_r2:.4f}")
    if diff <= TOLERANCE:
        print("Looks good: your honest R2 is close to the directly verified value.")
    else:
        print(
            "Your honest R2 differs from the expected value by more than a generous tolerance. "
            "That alone does not prove an error -- check that PCA was fit on case2_train_idx rows "
            "of the predictor-only matrix, never on case2_y."
        )
else:
    print("Not complete yet: define honest_pca_r2 above first.")
"""
            % {"expected": CASE2_EXPECTED_HONEST_R2, "tol": CASE2_R2_TOLERANCE},
            "wp57-209-case2-check",
        ),
        md(
            """
### Consequence

The contaminated pipeline's held-out R2 looks strong -- and it is
meaningless: computing it required already knowing every held-out
participant's own age, since age was one of the three columns the
component was built from. The honest pipeline's R2 is far lower, but it
is the only one of the two that could ever be applied to a real new
participant, since it never needs that participant's own age to run.
""",
            "wp57-210-consequence",
        ),
        md(
            """
### Interactive activity -- a result that knows the answer

Toggle between the contaminated and honest pipelines below. Both are
refit from scratch inside the toggle, so this works even if the repair
above was left blank. Axis ranges and the diagonal "perfect prediction"
guide line are identical in both views, so only the points move.
""",
            "wp57-211-widget-intro",
        ),
        code(
            """
# ---- "A result that knows the answer" -- native interactive activity ----
# Self-contained imports and data: this activity must work even if the
# Case 2 repair above was left blank.
from sklearn.decomposition import PCA as _PCA
from sklearn.linear_model import LinearRegression as _LinearRegression
from sklearn.model_selection import train_test_split as _train_test_split
from sklearn.metrics import r2_score as _r2_score

from sklearn.preprocessing import StandardScaler as _StandardScaler

_W_SEED, _W_N = %(seed)r, %(n)r
_w_rng = np.random.RandomState(_W_SEED)
_w_x1 = _w_rng.normal(0, 1, _W_N)
_w_x2 = _w_rng.normal(0, 1, _W_N)
_w_noise = _w_rng.normal(0, 1, _W_N)
_w_y = 1.5 * _w_x1 - 0.5 * _w_x2 + _w_noise
_w_train_idx, _w_val_idx = _train_test_split(np.arange(_W_N), test_size=%(test_size)r, random_state=%(split_seed)r)


def _widget2_fit(path):
    cols = np.column_stack([_w_x1, _w_x2, _w_y]) if path == "contaminated" else np.column_stack([_w_x1, _w_x2])
    # Both paths: standardize, then fit PCA -- using TRAINING rows only.
    # The contaminated path's own columns include y, so transforming any
    # row (train or held-out) still requires that row's own y.
    scaler = _StandardScaler().fit(cols[_w_train_idx])
    pca = _PCA(n_components=1, random_state=0).fit(scaler.transform(cols[_w_train_idx]))
    scores_train = pca.transform(scaler.transform(cols[_w_train_idx])).ravel()
    scores_val = pca.transform(scaler.transform(cols[_w_val_idx])).ravel()
    model = _LinearRegression().fit(scores_train.reshape(-1, 1), _w_y[_w_train_idx])
    pred_val = model.predict(scores_val.reshape(-1, 1))
    r2 = _r2_score(_w_y[_w_val_idx], pred_val)
    return pred_val, r2


# Fixed, shared axis range across BOTH toggle settings, computed once from
# the worst case of either path -- so switching never rescales the plot.
_w_true_val = _w_y[_w_val_idx]
_w_pred_contaminated, _w_r2_contaminated = _widget2_fit("contaminated")
_w_pred_honest, _w_r2_honest = _widget2_fit("honest")
_w_all_vals = np.concatenate([_w_true_val, _w_pred_contaminated, _w_pred_honest])
_w_lo, _w_hi = _w_all_vals.min() - 0.5, _w_all_vals.max() + 0.5

_widget2_toggle = widgets.Dropdown(
    options=[("Contaminated pipeline (y is an input column)", "contaminated"), ("Honest pipeline (predictor-only)", "honest")],
    value="contaminated",
    description="Pipeline:",
    style={"description_width": "initial"},
)
_widget2_output = widgets.Output()


def _widget2_render(_change=None):
    path = _widget2_toggle.value
    pred_val = _w_pred_contaminated if path == "contaminated" else _w_pred_honest
    r2 = _w_r2_contaminated if path == "contaminated" else _w_r2_honest
    label = "Contaminated (y is an input column)" if path == "contaminated" else "Honest (predictor-only)"
    color = "crimson" if path == "contaminated" else "tab:green"

    with _widget2_output:
        _widget2_output.clear_output(wait=True)
        fig, ax = plt.subplots(figsize=(5, 4.6))
        scatter_true_vs_pred(ax, _w_true_val, pred_val, (_w_lo, _w_hi), f"{label}\\nheld-out R2 = {r2:.4f}", point_kwargs={"color": color})
        ax.legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        plt.show()
        print(f"pipeline={path}  held-out R2={r2:.4f}")


_widget2_toggle.observe(_widget2_render, names="value")
display(controls_row(_widget2_toggle), _widget2_output)
_widget2_render()
"""
            % {
                "seed": CASE2_SEED,
                "n": CASE2_N,
                "test_size": CASE2_SPLIT_TEST_SIZE,
                "split_seed": CASE2_SPLIT_RANDOM_STATE,
            },
            "wp57-212-widget",
        ),
    ]


# --- Case 3: Picking a Tree -------------------------------------------------


def _case3() -> list[dict]:
    grid_literal = repr(TREE_DEPTH_GRID)
    return [
        md("## 3. Picking a Tree", "wp57-301-header"),
        md(
            """
This case reuses Case 1's three-way ABIDE-II split: `X_train`/`y_train` for
fitting, `X_val`/`y_val` for the model-setting decision below, and
`X_test`/`y_test` -- untouched until the very end -- for checking the
consequence of that decision.
""",
            "wp57-302-intro",
        ),
        md(
            f"""
### First, the Code

Below, a `DecisionTreeRegressor` is fit at each depth in `{grid_literal}`
(`None` means no depth limit). The depth with the **lowest training MSE**
is selected and reported.
""",
            "wp57-303-run-it-intro",
        ),
        code(
            """
try:
    X_train, X_val, X_test
except NameError as exc:
    raise RuntimeError(
        "X_train/X_val/X_test are not defined yet. Run Case 1's loading "
        "cell above (the one that prints 'X_train: ...') before this one, "
        "then run this cell again."
    ) from exc

from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error

TREE_DEPTH_GRID = %(grid)s
tree_fits = {}
for depth in TREE_DEPTH_GRID:
    tree = DecisionTreeRegressor(max_depth=depth, random_state=0).fit(X_train, y_train)
    train_mse = mean_squared_error(y_train, tree.predict(X_train))
    tree_fits[depth] = {"model": tree, "train_mse": train_mse}

depth_by_train_mse = min(tree_fits, key=lambda d: tree_fits[d]["train_mse"])
print(f"Depth chosen by lowest TRAINING MSE: {depth_by_train_mse!r}  (training MSE = {tree_fits[depth_by_train_mse]['train_mse']:.3f})")
"""
            % {"grid": grid_literal},
            "wp57-304-run-it",
        ),
        md(
            """
### Think first

> **Why is the lowest-training-MSE depth a poor basis for choosing which
> model to use, and what score should guide the choice instead?**
""",
            "wp57-305-diagnose-prompt",
        ),
        code(
            """
show_question("q-train-vs-val-select")
""",
            "wp57-306-q-train-vs-val",
        ),
        md(
            """
### Repair

For every depth already fit above (`tree_fits`), compute its **validation**
MSE on `X_val`/`y_val`, then select the depth with the **lowest validation
MSE** instead.

Required output names: `tree_val_results` -- a list of dicts, one per
depth, shaped `{"depth": d, "train_mse": ..., "val_mse": ...}`; and
`depth_by_val_mse` -- the selected depth.
""",
            "wp57-307-instructions",
        ),
        blank(
            """
tree_val_results = []
depth_by_val_mse = None

# YOUR CODE HERE
# Hint: reuse tree_fits[depth]["model"] -- no need to refit. For each
# depth, predict on X_val/y_val with mean_squared_error, then pick the
# depth whose val_mse is lowest.
# Example shape only (not a real result):
# tree_val_results.append({"depth": 1, "train_mse": 0.0, "val_mse": 0.0})
""",
            """
tree_val_results = []
for depth in TREE_DEPTH_GRID:
    model = tree_fits[depth]["model"]
    val_mse = mean_squared_error(y_val, model.predict(X_val))
    tree_val_results.append({"depth": depth, "train_mse": tree_fits[depth]["train_mse"], "val_mse": val_mse})

depth_by_val_mse = min(tree_val_results, key=lambda r: r["val_mse"])["depth"]
""",
            "wp57-308-case3-blank",
            tags=["wp57-activity-tree"],
        ),
        code(
            """
# Run this to check your repair.
EXPECTED_VAL_MSE = {%(expected_val)s}
TOLERANCE = %(tol)r

if tree_val_results and depth_by_val_mse is not None:
    by_depth = {r["depth"]: r["val_mse"] for r in tree_val_results}
    if set(by_depth) != set(TREE_DEPTH_GRID):
        print(f"Not quite: expected one result per entry of TREE_DEPTH_GRID ({TREE_DEPTH_GRID}).")
    else:
        diffs = {d: abs(by_depth[d] - EXPECTED_VAL_MSE[d]) for d in by_depth}
        if all(d <= TOLERANCE for d in diffs.values()):
            print("Looks good: your validation MSE values match the expected values within tolerance.")
            print(f"Depth chosen by lowest VALIDATION MSE: {depth_by_val_mse!r}")
        else:
            print(
                "Some validation MSE values differ from the expected numbers by more than a generous "
                "tolerance. That alone does not prove an error -- check that each model was scored on "
                "X_val/y_val, reusing the models already fit in tree_fits."
            )
else:
    print("Not complete yet: define tree_val_results and depth_by_val_mse above first.")
"""
            % {"expected_val": ", ".join(f"{d!r}: {EXPECTED_TREE_RESULTS[d]['val_mse']!r}" for d in TREE_DEPTH_GRID), "tol": TREE_MSE_TOLERANCE},
            "wp57-309-case3-check",
        ),
        md(
            """
### Plot training and validation MSE across depths

Supplied: a ready-to-run plot.
""",
            "wp57-310-plot-intro",
        ),
        code(
            """
if tree_val_results and depth_by_val_mse is not None:
    plot_df = pd.DataFrame(tree_val_results)
    plot_df["depth_label"] = plot_df["depth"].apply(lambda d: "None" if d is None else str(d))
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    ax.plot(plot_df["depth_label"], plot_df["train_mse"], marker="o", label="training MSE")
    ax.plot(plot_df["depth_label"], plot_df["val_mse"], marker="s", label="validation MSE")
    ax.set_xlabel("Max tree depth")
    ax.set_ylabel("Mean squared error")
    ax.set_title("Training vs. validation MSE across depths")
    ax.legend()
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: finish the repair above first.")
""",
            "wp57-311-plot",
        ),
        md(
            """
### Consequence

Below, both choices -- the depth picked by training MSE, and the depth
picked by validation MSE -- are finally scored on `X_test`/`y_test`, which
neither choice has seen until now.
""",
            "wp57-312-consequence-intro",
        ),
        code(
            """
if tree_val_results and depth_by_val_mse is not None:
    test_mse_by_train_choice = mean_squared_error(y_test, tree_fits[depth_by_train_mse]["model"].predict(X_test))
    test_mse_by_val_choice = mean_squared_error(y_test, tree_fits[depth_by_val_mse]["model"].predict(X_test))
    print(f"Depth chosen by TRAINING MSE ({depth_by_train_mse!r}):   test MSE = {test_mse_by_train_choice:.3f}  -- chosen using a score that rewards memorization")
    print(f"Depth chosen by VALIDATION MSE ({depth_by_val_mse!r}):   test MSE = {test_mse_by_val_choice:.3f}  -- chosen using a held-out score")
else:
    print("Not complete yet: finish the repair above first.")
""",
            "wp57-313-consequence",
        ),
        md(
            """
### Interactive activity -- which tree gets deployed?

Toggle between the two selection rules below. Both rules choose from the
same precomputed grid and the same split, so switching is instant -- no
refitting happens inside the toggle.
""",
            "wp57-314-widget-intro",
        ),
        code(
            """
# ---- "Which tree gets deployed?" -- native interactive activity ----
# Self-contained: reuses the top-level X_train/X_val/X_test/y_train/y_val/
# y_test from Case 1 (always defined, never a blank), but precomputes its
# own fits independently of the Case 3 repair above, so it works even if
# that repair was left blank.
_w3_depth_grid = %(grid)s
_w3_fits = {}
for _d in _w3_depth_grid:
    _w3_tree = DecisionTreeRegressor(max_depth=_d, random_state=0).fit(X_train, y_train)
    _w3_fits[_d] = {
        "train_mse": mean_squared_error(y_train, _w3_tree.predict(X_train)),
        "val_mse": mean_squared_error(y_val, _w3_tree.predict(X_val)),
        "test_mse": mean_squared_error(y_test, _w3_tree.predict(X_test)),
        "test_pred": _w3_tree.predict(X_test),
    }

_w3_all_test_vals = np.concatenate([y_test] + [f["test_pred"] for f in _w3_fits.values()])
_w3_lo, _w3_hi = _w3_all_test_vals.min() - 2, _w3_all_test_vals.max() + 2

_widget3_toggle = widgets.Dropdown(
    options=[("Lowest training MSE", "train"), ("Lowest validation MSE", "val")],
    value="train",
    description="Choose depth by:",
    style={"description_width": "initial"},
)
_widget3_output = widgets.Output()


def _widget3_render(_change=None):
    rule = _widget3_toggle.value
    key = "train_mse" if rule == "train" else "val_mse"
    chosen_depth = min(_w3_fits, key=lambda d: _w3_fits[d][key])
    chosen = _w3_fits[chosen_depth]
    depth_labels = ["None" if d is None else str(d) for d in _w3_depth_grid]

    with _widget3_output:
        _widget3_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].plot(depth_labels, [_w3_fits[d]["train_mse"] for d in _w3_depth_grid], marker="o", label="training MSE")
        axes[0].plot(depth_labels, [_w3_fits[d]["val_mse"] for d in _w3_depth_grid], marker="s", label="validation MSE")
        chosen_label = "None" if chosen_depth is None else str(chosen_depth)
        axes[0].axvline(chosen_label, color="crimson", linestyle="--", linewidth=1, label=f"chosen depth = {chosen_label}")
        axes[0].set_xlabel("Max tree depth")
        axes[0].set_ylabel("Mean squared error")
        axes[0].set_title(f"Selection rule: lowest {'training' if rule == 'train' else 'validation'} MSE")
        axes[0].legend(fontsize=8)

        scatter_true_vs_pred(
            axes[1], y_test, chosen["test_pred"], (_w3_lo, _w3_hi),
            f"Depth {chosen_label} on the untouched test set\\ntest MSE = {chosen['test_mse']:.2f} (for context only -- not used to choose)",
        )
        axes[1].legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        plt.show()
        print(f"rule={rule}  chosen_depth={chosen_label}  test_mse={chosen['test_mse']:.2f}")


_widget3_toggle.observe(_widget3_render, names="value")
display(controls_row(_widget3_toggle), _widget3_output)
_widget3_render()
"""
            % {"grid": grid_literal},
            "wp57-315-widget",
        ),
        code(
            """
show_question("q-tree-deploy")
""",
            "wp57-316-q-tree-deploy",
        ),
    ]


# --- Case 4: A High-Accuracy Classifier -------------------------------------


def _case4() -> list[dict]:
    return [
        md("## 4. A High-Accuracy Classifier", "wp57-401-header"),
        md(
            """
This case uses a small, synthetic, reproducible classification task (not
ABIDE data) with a strongly imbalanced outcome: about 5% of rows are
positive, 95% are negative.
""",
            "wp57-402-intro",
        ),
        md(
            """
### First, the Code

A classifier that always predicts the majority class (negative) is scored
on held-out rows, using accuracy alone.
""",
            "wp57-403-run-it-intro",
        ),
        code(
            """
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

case4_rng = np.random.RandomState(%(seed)r)
case4_n = %(n)r
case4_y = (case4_rng.rand(case4_n) < %(rate)r).astype(int)  # synthetic -- ~5%% positive

case4_train_idx, case4_val_idx = train_test_split(
    np.arange(case4_n), test_size=%(test_size)r, random_state=%(split_seed)r, stratify=case4_y
)
case4_pred_majority = np.zeros(len(case4_val_idx), dtype=int)  # "always predict negative"
case4_accuracy = accuracy_score(case4_y[case4_val_idx], case4_pred_majority)
print(f"Accuracy: {case4_accuracy:.2f}")
"""
            % {
                "seed": CASE4_SEED,
                "n": CASE4_N,
                "rate": CASE4_POSITIVE_RATE,
                "test_size": CASE4_SPLIT_TEST_SIZE,
                "split_seed": CASE4_SPLIT_RANDOM_STATE,
            },
            "wp57-404-run-it",
        ),
        md(
            """
### Think first

95% accuracy sounds like a strong result -- on its own, it hides what the
classifier actually did. Below, a fuller picture: the confusion matrix and
several metrics computed from it.
""",
            "wp57-405-diagnose-intro",
        ),
        code(
            """
from sklearn.metrics import confusion_matrix, balanced_accuracy_score

case4_cm = confusion_matrix(case4_y[case4_val_idx], case4_pred_majority, labels=[0, 1])
tn, fp, fn, tp = case4_cm.ravel()
sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
specificity = tn / (tn + fp) if (tn + fp) else float("nan")
precision = tp / (tp + fp) if (tp + fp) else None  # undefined with zero predicted positives
balanced_acc = balanced_accuracy_score(case4_y[case4_val_idx], case4_pred_majority)

print(f"Confusion matrix (rows=true, cols=predicted, order=[negative, positive]):\\n{case4_cm}")
print(f"Sensitivity (recall for positive): {sensitivity:.3f}")
print(f"Specificity (recall for negative): {specificity:.3f}")
print("Precision: undefined -- the classifier never predicted the positive class" if precision is None else f"Precision: {precision:.3f}")
print(f"Balanced accuracy: {balanced_acc:.3f}")
print(f"Plain accuracy was {case4_accuracy:.2f} -- balanced accuracy tells a very different story.")
""",
            "wp57-406-diagnose-code",
        ),
        md(
            """
If this classifier were screening participants for a follow-up scan,
accuracy alone would have hidden the fact that it would miss **every
single** participant who actually needed that follow-up (sensitivity 0.0),
while looking "95% accurate" the entire time. Specificity alone would miss
the same problem from the opposite side: a classifier can have perfect
specificity by never flagging anyone.
""",
            "wp57-407-interpretation",
        ),
        code(
            """
show_question("q-classifier-metrics")
""",
            "wp57-408-q-classifier-metrics",
        ),
    ]


# --- Case 5: Many Rows per Participant --------------------------------------


def _case5() -> list[dict]:
    return [
        md("## 5. Many Rows per Participant", "wp57-501-header"),
        md(
            """
This case uses small, synthetic data representing repeated observations
per participant -- for example, repeated trials or epochs (not ABIDE
observations, which do not contain repeated rows per participant in this
course's table). 40 synthetic participants each contribute 8 rows.
""",
            "wp57-502-intro",
        ),
        md(
            """
### First, the Code

Rows are split **at random**, ignoring which participant each row came
from, and a 1-nearest-neighbor regressor is fit and scored.
""",
            "wp57-503-run-it-intro",
        ),
        code(
            """
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score

case5_rng = np.random.RandomState(%(seed)r)
N_PARTICIPANTS, ROWS_PER_PARTICIPANT = %(n_participants)r, %(rows_per)r
case5_participant_id = np.repeat(np.arange(N_PARTICIPANTS), ROWS_PER_PARTICIPANT)
case5_n = len(case5_participant_id)

# Each participant has a stable, participant-level signal, observed with
# small per-row ("epoch") noise -- rows from the SAME participant look
# almost identical to each other, and different from other participants'.
participant_signal = case5_rng.normal(0, %(signal_sd)r, N_PARTICIPANTS)
case5_x = participant_signal[case5_participant_id] + case5_rng.normal(0, %(epoch_noise_sd)r, case5_n)
case5_y = participant_signal[case5_participant_id] + case5_rng.normal(0, %(target_noise_sd)r, case5_n)
case5_X = case5_x.reshape(-1, 1)

row_train_idx, row_val_idx = train_test_split(np.arange(case5_n), test_size=%(test_size)r, random_state=%(split_seed)r)
row_overlap = len(set(case5_participant_id[row_train_idx]) & set(case5_participant_id[row_val_idx]))

row_model = KNeighborsRegressor(n_neighbors=1).fit(case5_X[row_train_idx], case5_y[row_train_idx])
row_pred = row_model.predict(case5_X[row_val_idx])
row_val_r2 = r2_score(case5_y[row_val_idx], row_pred)
print(f"Participants appearing in BOTH train and validation: {row_overlap} of {N_PARTICIPANTS}")
print(f"Validation R2 (random row split): {row_val_r2:.4f}")
"""
            % {
                "seed": CASE5_SEED,
                "n_participants": CASE5_N_PARTICIPANTS,
                "rows_per": CASE5_ROWS_PER_PARTICIPANT,
                "signal_sd": CASE5_SIGNAL_SD,
                "epoch_noise_sd": CASE5_EPOCH_NOISE_SD,
                "target_noise_sd": CASE5_TARGET_NOISE_SD,
                "test_size": CASE5_SPLIT_TEST_SIZE,
                "split_seed": CASE5_SPLIT_RANDOM_STATE,
            },
            "wp57-504-run-it",
        ),
        md(
            """
### Think first and repair

The overlap count above already answers the diagnosis: most participants
appear on both sides of the random row split. Repair the split using
`GroupShuffleSplit` with `groups=case5_participant_id`, so every
participant lands entirely in training or entirely in validation, then
refit and rescore.

Required output names: `group_overlap` -- the number of participants
appearing in both the grouped training and validation sets (should be
`0`); and `group_val_r2` -- the resulting validation R2.
""",
            "wp57-505-instructions",
        ),
        blank(
            """
group_overlap = None
group_val_r2 = None

# YOUR CODE HERE
# Hint: use GroupShuffleSplit from sklearn.model_selection, passing
# groups=case5_participant_id so every participant lands entirely on one
# side of the split, then refit the same kind of model and rescore.
""",
            """
gss = GroupShuffleSplit(n_splits=1, test_size=%(test_size)r, random_state=%(split_seed)r)
group_train_idx, group_val_idx = next(gss.split(case5_X, case5_y, groups=case5_participant_id))
group_overlap = len(set(case5_participant_id[group_train_idx]) & set(case5_participant_id[group_val_idx]))

group_model = KNeighborsRegressor(n_neighbors=1).fit(case5_X[group_train_idx], case5_y[group_train_idx])
group_pred = group_model.predict(case5_X[group_val_idx])
group_val_r2 = r2_score(case5_y[group_val_idx], group_pred)
"""
            % {"test_size": CASE5_SPLIT_TEST_SIZE, "split_seed": CASE5_SPLIT_RANDOM_STATE},
            "wp57-506-case5-blank",
            tags=["wp57-activity-group"],
        ),
        code(
            """
# Run this to check your repair.
EXPECTED_GROUP_R2 = %(expected)r
TOLERANCE = %(tol)r

if group_overlap is not None and group_val_r2 is not None:
    if group_overlap != 0:
        print(f"Not quite: group_overlap is {group_overlap}, expected 0 -- check that groups=case5_participant_id was passed to GroupShuffleSplit.")
    elif abs(group_val_r2 - EXPECTED_GROUP_R2) <= TOLERANCE:
        print(f"Looks good: participant overlap is 0, and group_val_r2={group_val_r2:.4f} is close to the expected value.")
        print(f"Compare: row-split (leaky) R2 = {row_val_r2:.4f}  vs.  group-split (honest) R2 = {group_val_r2:.4f}")
    else:
        print(
            "group_overlap is correctly 0, but group_val_r2 differs from the expected value by more "
            "than a generous tolerance. Check the GroupShuffleSplit split_size/random_state and the model fit."
        )
else:
    print("Not complete yet: define group_overlap and group_val_r2 above first.")
"""
            % {"expected": CASE5_EXPECTED_GROUP_R2, "tol": CASE5_R2_TOLERANCE},
            "wp57-507-case5-check",
        ),
        md(
            """
### Consequence

The random row split's validation score looks better -- not because the
model generalizes better, but because most validation rows had an
almost-identical training row from the *same participant* for the
1-nearest-neighbor model to match against. The group split's lower score
is the honest one: it reflects performance on participants the model never
saw in any form during training.
""",
            "wp57-508-consequence",
        ),
        code(
            """
show_question("q-group-leakage")
""",
            "wp57-509-q-group-leakage",
        ),
    ]


# --- Case 6: One Last Setting to Try (closing challenge) -------------------


def _case6() -> list[dict]:
    return [
        md("## 6. One Last Setting to Try", "wp57-601-header"),
        md(
            """
This closing case uses one more small, synthetic regression example (not
ABIDE data): 150 observations, 10 predictors, and a `Ridge` regression
with a choice of regularization strength (`alpha`) still to be made.
""",
            "wp57-602-intro",
        ),
        md(
            """
### First, the Code

Below, five candidate `alpha` values are each scored directly on the
**test** rows, and the best-scoring one is reported as "the" test MSE.
""",
            "wp57-603-run-it-intro",
        ),
        code(
            """
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

case6_rng = np.random.RandomState(%(seed)r)
case6_n, case6_n_features = %(n)r, %(n_features)r
case6_X = case6_rng.normal(0, 1, (case6_n, case6_n_features))
case6_true_w = case6_rng.normal(0, 1, case6_n_features)
case6_y = case6_X @ case6_true_w + case6_rng.normal(0, %(noise_sd)r, case6_n)

case6_train_idx, case6_test_idx = train_test_split(np.arange(case6_n), test_size=%(test_size)r, random_state=%(split_seed)r)

case6_candidate_alphas = %(alphas)s
best_alpha, best_test_mse = None, float("inf")
for alpha in case6_candidate_alphas:
    model = Ridge(alpha=alpha).fit(case6_X[case6_train_idx], case6_y[case6_train_idx])
    test_mse = mean_squared_error(case6_y[case6_test_idx], model.predict(case6_X[case6_test_idx]))
    print(f"alpha={alpha:>6}: test MSE = {test_mse:.3f}")
    if test_mse < best_test_mse:
        best_alpha, best_test_mse = alpha, test_mse

print(f"\\nBest alpha found: {best_alpha}  --  reported as the untouched test MSE: {best_test_mse:.3f}")
"""
            % {
                "seed": CASE6_SEED,
                "n": CASE6_N,
                "n_features": CASE6_N_FEATURES,
                "noise_sd": CASE6_NOISE_SD,
                "test_size": CASE6_SPLIT_TEST_SIZE,
                "split_seed": CASE6_SPLIT_RANDOM_STATE,
                "alphas": repr(CASE6_ALPHAS),
            },
            "wp57-604-run-it",
        ),
        md(
            """
### Think first

> **At which point did the test set stop being an untouched, one-time
> evaluation?**
""",
            "wp57-605-diagnose-prompt",
        ),
        code(
            """
show_question("q-test-peeking")
""",
            "wp57-606-q-test-peeking",
        ),
        md(
            """
### The corrected workflow, in words

No corrected code runs here -- the fix is procedural, not a different
formula. The alpha search above should instead happen on a validation
split (or by cross-validation) carved out of the *training* rows alone,
never touching the test rows. Once a single alpha is chosen that way, the
test rows are used exactly once, to report a final score for the model
that was already fully decided beforehand. If that one test score then
motivates trying yet another setting, a fresh, never-before-touched test
set is needed to report honestly on it -- the original test rows have
already done their one job.

> **Looking back across all six cases, name one check you will now add to your own future analyses.**
""",
            "wp57-607-corrected-workflow",
        ),
    ]


# --- assembly ---------------------------------------------------------------


def _all_specs() -> list:
    specs: list = [_run_first_notice(), _setup_cell_placeholder()]
    specs += _title_and_overview()
    specs += _case1()
    specs += _case2()
    specs += _case3()
    specs += _case4()
    specs += _case5()
    specs += _case6()
    return specs


def _setup_cell_placeholder():
    return "__SETUP__"


def build_notebook(mode: str) -> nbformat.NotebookNode:
    nb = new_notebook()
    nb["metadata"] = dict(KERNELSPEC)
    cells = []
    for spec in _all_specs():
        if spec == "__SETUP__":
            cells.append(_setup_cell(mode))
        elif isinstance(spec, Blank):
            cells.append(spec.render(mode))
        else:
            cells.append(spec)
    nb["cells"] = cells
    return nb


def _serialize(mode: str) -> str:
    return nbformat.writes(build_notebook(mode), version=4)


def _write_or_check(path: Path, text: str, write: bool) -> bool:
    if write:
        if path.exists() and path.read_text() == text:
            print(f"up to date: {path.relative_to(REPO_ROOT)}")
            return True
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"wrote {path.relative_to(REPO_ROOT)}")
        return True
    else:
        if not path.exists() or path.read_text() != text:
            print(f"stale (run --write): {path.relative_to(REPO_ROOT)}")
            return False
        print(f"OK: up to date: {path.relative_to(REPO_ROOT)}")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--write", action="store_true")
    mode_group.add_argument("--check", action="store_true")
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument("--student", action="store_true")
    target_group.add_argument("--reference", action="store_true")
    target_group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    do_student = args.student or args.all or not (args.student or args.reference)
    do_reference = args.reference or args.all or not (args.student or args.reference)

    write = args.write
    ok = True
    if do_student:
        text = _serialize("student")
        ok &= _write_or_check(LITE_TEMPLATE_PATH, text, write)
        ok &= _write_or_check(PORTABLE_PATH, text, write)
        ok &= _write_or_check(LITE_FILES_PORTABLE_COPY_PATH, text, write)
    if do_reference:
        text = _serialize("reference")
        ok &= _write_or_check(REFERENCE_PATH, text, write)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
