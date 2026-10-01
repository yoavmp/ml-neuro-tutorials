#!/usr/bin/env python3
"""Generate Exercise 4's JupyterLite template, portable copy, and reference.

WP45: migrate Exercise 4 ("Validation and Cross-Validation") to the same
JupyterLite-native, generator-authored architecture WP41/WP42/WP44
established for Exercises 1-3 (see WPs/reports/WP41_MAINTAINER_GUIDE.md).
One Python module is the single authoritative source for the JupyterLite
template, the downloadable/Colab-compatible copy, and the completed
reference notebook used only by the test suite -- structurally synchronized
by construction, exactly like scripts/generate_exercise_03_notebook.py.

Terminology note (WP45 spec): the pre-migration notebook's own outline line
("load the data for classification") is a misnomer -- the actual established
recipe predicts a continuous target (age, from Exercise 2's KNN worked
example) and reports ordinary regression MSE per fold, never a
classification metric on hard labels. Confirmed by reading
book/chapters/chapter_04/exercise_04.ipynb (pre-migration) in full: it uses
KNeighborsRegressor, age as a continuous target, and mean_squared_error
throughout. This migration preserves that recipe unchanged.

Data: reuses the exact same same-origin export Exercises 2 and 3 already
ship, book/lite/files/data/abide_age_brain.csv (360 fsCT predictors + age +
group, 1004 participants). No second, independent data export is created.

Numbers below were verified directly against this file before writing a
single generator line (WP45 report has the verification script/output):
  one-split KNN(k=20) test MSE=31.3768 R2=0.663879 (n_train=753, n_test=251)
    -- matches Exercise 2's own already-approved worked example (~31.4/0.664)
  Section 3 5-fold CV (KFold shuffle=True random_state=0, full 1004, k=20):
    fold MSEs [42.9136, 33.4213, 31.4953, 34.9089, 26.3213], mean 33.8121
  Section 4 widget: reproduces scripts/wp27_validation_audit_result.json's
    part_a_sample_size_stability bit-for-bit (spot-checked size=all seed=0)
  Section 5 nested CV: reproduces scripts/wp27_validation_audit_result.json's
    part_c_nested_cv bit-for-bit (mean outer MSE=33.3552, selected k per
    fold [15, 12, 10, 18, 15])

Outputs:
  book/lite/files/exercise_04.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_04/exercise_04_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_04_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_04_reference.ipynb (--reference)

Modes:
  --write   regenerate the selected output(s) on disk.
  --check   regenerate in memory and fail if a committed file is stale.
  --student / --reference / --all (default --all with --write or --check)
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_SIDECAR = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_age_brain.manifest.json"
NCV_DIAGRAM_IMAGE_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_04_nested_cv_diagram.png"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_04.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_04_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_04_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 4, "templateVersion": TEMPLATE_VERSION},
}

# Established, audited protocol -- preserved unchanged by this migration.
# scripts/wp27_validation_audit_result.json is the committed audit this
# notebook's Section 4 widget and Section 5 nested-CV activity are checked
# against; the one-split and Section 3 numbers were verified directly
# against book/lite/files/data/abide_age_brain.csv (see module docstring).
K_EXAMPLE = 20
EXPECTED_N_TRAIN = 753
EXPECTED_N_TEST = 251
EXPECTED_N_FEATURES = 360
EXPECTED_ONE_SPLIT_MSE = 31.3768
EXPECTED_ONE_SPLIT_R2 = 0.663879
EXPECTED_CV_MEAN_MSE = 33.8121
EXPECTED_CV_MEAN_R2 = 0.615255
NESTED_CANDIDATE_KS = [8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 40, 50]
EXPECTED_NESTED_MEAN_MSE = 33.3552
EXPECTED_NESTED_MEAN_R2 = 0.619821


def md(source: str, cell_id: str, attachments: dict | None = None) -> dict:
    c = new_markdown_cell(source.strip() + "\n")
    c["id"] = cell_id
    if attachments:
        c["attachments"] = attachments
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


# Duplicates (never imports) generate_exercise_02_notebook.py's setup-cell
# pattern -- each generator module is a self-contained, independently
# regenerable source of truth (WP41 maintainer guide section 4.7).
SETUP_SOURCE_TEMPLATE = '''
import sys
import warnings

warnings.filterwarnings("ignore", message=r"The (width|height|x|y) parameter as float was deprecated")

# WP48: same upstream threadpoolctl/Pyodide RuntimeWarning
# scripts/generate_exercise_02_notebook.py's setup cell documents and
# filters (reproduced live in this exact browser build, firing from
# threadpoolctl's own Pyodide shared-library introspection whenever a model
# is fit, including this notebook's one-split cell) -- same narrow,
# message-and-category-scoped filter, applied consistently rather than
# reinventing it per notebook.
warnings.filterwarnings(
    "ignore",
    message=r"JsProxy\\.as_object_map\\(\\) is deprecated",
    category=RuntimeWarning,
)

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
import ipywidgets as widgets
from IPython.display import display, HTML

{features_literal}


def load_abide_age_brain_table():
    """Return the age/brain table: 360 cortical-thickness predictors, age,
    and group (autism/control, used only to reproduce the established
    train/test split -- never a model feature).

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout); falls back to the same pinned,
    checksummed public source this course already uses elsewhere (a bare
    downloaded .ipynb, or Colab, neither of which has the sibling data
    file). Both paths return identically shaped, identically ordered
    columns, so the rest of this notebook never needs to know which one ran.
    """
    from pathlib import Path

    local_path = Path("data/abide_age_brain.csv")
    if local_path.exists():
        table = pd.read_csv(local_path)
    else:
        url = (
            "https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/"
            "e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/"
            "tu-machine-learning-yarkoni/data/abide2.tsv"
        )
        table = pd.read_csv(url, sep="\\t")
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


def make_multi_choice_question(prompt, options, correct_indices, feedback_correct="Correct.", feedback_incorrect="Not quite -- try again."):
    """A compact multiple-selection checked question. Returns a widget to display()."""
    correct = set(correct_indices)
    boxes = [
        widgets.Checkbox(value=False, description=opt, indent=False, layout=widgets.Layout(width="100%"))
        for opt in options
    ]
    button = widgets.Button(description="Check answer", button_style="primary")
    feedback = widgets.Output()

    def _on_click(_button):
        selected = {i for i, cb in enumerate(boxes) if cb.value}
        with feedback:
            feedback.clear_output(wait=True)
            print(feedback_correct if selected == correct else feedback_incorrect)

    button.on_click(_on_click)
    box = widgets.VBox(
        [_question_style_widget(), widgets.HTML(f"<b>{prompt}</b>")] + boxes + [button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("checked-question")
    return box


# Question content lives here, not in the visible cell that displays it: a
# visible call like show_question("q-inner-loop-data") never prints or
# displays a correct_index/correct_indices value (WP48's "Multiple-choice
# answer visibility" requirement -- see
# scripts/generate_exercise_08_notebook.py for the pattern this mirrors).
# This is visual concealment, not secure assessment: the hidden cell is
# fully expandable, and a downloaded, fully offline, editable notebook must
# contain enough information to check an answer locally, so a technically
# curious student can always recover it from source or the running kernel.
_QUESTIONS = {
    "q-single-split-vs-cv-stability": dict(
        kind="single",
        prompt=(
            "At a small sample size (for example, 30 or 50 participants), why can "
            "changing only the random seed swing the single-split test R^2 by a "
            "large amount, while the 5-fold cross-validation mean tends to move "
            "less?"
        ),
        options=[
            "The single split evaluates on only one held-out subset of participants, so which few participants land there matters a lot; cross-validation averages over several different held-out subsets, so unusually easy or hard subsets tend to cancel out.",
            "Cross-validation always uses more participants in total than a single split.",
            "KNN itself becomes a different algorithm when cross-validated.",
        ],
        correct_index=0,
        feedback_correct="Correct: averaging several held-out subsets, rather than reporting just one, is what makes cross-validation's summary more stable than a single split's.",
    ),
    "q-inner-loop-data": dict(
        kind="single",
        prompt=(
            "Inside the pipeline above, which participants does the inner "
            "GridSearchCV use to choose k for a given outer fold?"
        ),
        options=[
            "Only that outer fold's training data -- the outer fold's own test data is never used to select k.",
            "All 1004 participants, including the current outer fold's test data.",
            "Only the current outer fold's test data.",
        ],
        correct_index=0,
        feedback_correct="Correct: the inner loop selects k using only the outer fold's training data, so the outer test fold stays untouched by the tuning decision.",
    ),
    "q-outer-test-mse-meaning": dict(
        kind="single",
        prompt=(
            "What does the mean outer-test MSE (averaged across the 5 outer folds) "
            "actually estimate?"
        ),
        options=[
            "The performance of the complete tuning procedure -- choosing k with inner cross-validation, then evaluating that choice on data the inner loop never saw -- not the performance of one single, fixed k.",
            "The performance of whichever k happened to score best on the inner cross-validation.",
            "The performance of a KNN model with k chosen by looking at all the outer-test folds at once.",
        ],
        correct_index=0,
        feedback_correct="Correct: nested cross-validation's outer score estimates the tuning procedure's performance, which is what you would actually get by repeating this whole inner-selection process on new data.",
    ),
}


def show_question(question_id):
    q = _QUESTIONS[question_id]
    if q["kind"] == "single":
        widget = make_single_choice_question(
            q["prompt"],
            q["options"],
            q["correct_index"],
            q.get("feedback_correct", "Correct."),
            q.get("feedback_incorrect", "Not quite -- try again."),
        )
    else:
        widget = make_multi_choice_question(
            q["prompt"],
            q["options"],
            q["correct_indices"],
            q.get("feedback_correct", "Correct."),
            q.get("feedback_incorrect", "Not quite -- try again."),
        )
    display(widget)
'''.strip()


def _setup_cell(mode: str) -> dict:
    source = SETUP_SOURCE_TEMPLATE.replace("{features_literal}", _feature_list_literal())
    return code(source, "wp45-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp45-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 4: Validation and Cross-Validation", "wp45-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 4 of *Machine Learning for Neuroscience*. It reuses
Exercise 2's ABIDE-II age-prediction task and its fixed KNN predictor set
unchanged, and compares one train/test split with cross-validation. The
predictors were already fixed before this lesson -- nothing here selects,
adds, or removes a feature; feature selection is Exercise 5's topic.

In this notebook you will:

1. reuse Exercise 2's ABIDE age-prediction data and its fixed KNN predictors;
2. see one train/test split and its MSE, computed with the fixed `k` used
   throughout this notebook;
3. write code that evaluates the same fixed model with 5-fold cross-validation;
4. compare a single split with cross-validation across several sample sizes;
5. complete a guided nested cross-validation pipeline that tunes `k` and
   evaluates the tuning procedure honestly.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 2's regression and KNN material; comfort with
`pandas`, `numpy`, and the scikit-learn `fit` / `predict` / `Pipeline` pattern.
""",
            "wp45-002-overview",
        ),
    ]


def _section_1() -> list[dict]:
    return [
        md("## 1. Data and setup", "wp45-101-header"),
        md(
            """
**Target:** age (a continuous measurement, in years). **Predictors:** the
same 360 bilateral cortical-thickness (`fsCT_`) columns Exercise 2 used,
fixed before this lesson. **Metric:** mean squared error (MSE) -- the same
regression metric Exercise 2 used, since the target here is continuous, not
a class label.
""",
            "wp45-102-intro",
        ),
        code(
            """
# Load the approved ABIDE-II age-prediction table: the same 1004-participant,
# 360-feature cortical-thickness table Exercise 2 uses.
try:
    df = load_abide_age_brain_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_age_brain_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under "
        "'Run the cell below first') before this one, then run this cell again."
    ) from exc

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
X = df[FEATURES].to_numpy(float)
y = df["age"].to_numpy(float)
groups = df["group"].to_numpy()  # 1 = autism, 2 = control; stratification key only, never a predictor

print(f"{len(df)} participants, {len(FEATURES)} brain predictors, target = age")
df[FEATURES[:3] + ["age"]].head()
""",
            "wp45-103-load",
        ),
        code(
            """
from sklearn.model_selection import train_test_split, KFold, cross_validate, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.metrics import mean_squared_error, r2_score
""",
            "wp45-103a-imports",
        ),
        md(
            """
The train/test split below reuses Exercise 2's exact fixed arguments, so
the two partitions here are identical to Exercise 2's own.
""",
            "wp45-104-split-intro",
        ),
        code(
            f"""
X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=42, stratify=groups
)
print(f"n_train = {{len(y_train)}}   n_test = {{len(y_test)}}   n_features = {{X.shape[1]}}")
""",
            "wp45-105-split",
        ),
        md(
            """
A reminder, already established in Exercise 2: KNN predicts a participant's
age by averaging the `k` training participants whose predictors are closest
to theirs, so scaling matters -- an unscaled predictor with a large numeric
range would dominate that distance just because of its units. A
scikit-learn `Pipeline` keeps `StandardScaler` bundled with the model, fit
on training data only and refit separately inside every fold below.
""",
            "wp45-106-reminder",
        ),
    ]


def _section_2() -> list[dict]:
    return [
        md("## 2. One Train/Test Split", "wp45-201-header"),
        md(
            f"""
The cell below fits one KNN model, with `k = {K_EXAMPLE}` (the same fixed
value used in Exercise 2's own worked example), on the training partition
above and evaluates it once on the held-out test partition.
""",
            "wp45-202-intro",
        ),
        code(
            f"""
K_EXAMPLE = {K_EXAMPLE}  # the value used throughout this notebook, from Exercise 2's own worked example

one_split_model = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))
one_split_model.fit(X_train, y_train)
one_split_pred = one_split_model.predict(X_test)
one_split_mse = mean_squared_error(y_test, one_split_pred)
one_split_r2 = r2_score(y_test, one_split_pred)
print(f"one split: test MSE = {{one_split_mse:.1f}}   test R^2 = {{one_split_r2:.3f}}")
""",
            "wp45-203-onesplit",
        ),
        md(
            """
> This single number is an honest estimate of performance on participants
> the model never trained on -- but it depends on exactly which
> participants happened to land in the training set and which landed in the
> test set. A different split could give a somewhat different MSE for the
> exact same model and data. Section 4 lets you see this directly.
""",
            "wp45-204-reminder",
        ),
    ]


def _section_3() -> list[dict]:
    return [
        md("## 3. Evaluate the Same Model with Cross-Validation", "wp45-301-header"),
        md(
            f"""
**Cross-validation** partitions the data into several folds, fits the model
on all-but-one fold, evaluates it on the held-out fold, and repeats until
every fold has served as the held-out one once -- giving several performance
estimates from the same data instead of one.

Write code that runs 5-fold cross-validation of the **same fixed model**
(`k = {K_EXAMPLE}`, the same value as Section 2 -- this activity evaluates
one model, it does not choose `k`) on the **full** `X`/`y` (not just the
training partition above), and prints each fold's MSE and the mean MSE.

Hints:
- `KFold(n_splits=5, shuffle=True, random_state=0)` gives 5 reproducible
  folds; scikit-learn's `cross_validate(..., scoring="neg_mean_squared_error")`
  (or an equivalent loop over `kf.split(X)`) fits and scores each one. Put
  `StandardScaler` in the same `Pipeline`/`make_pipeline` as the model so it
  is refit separately inside every fold -- never fit once on all the data.
- scikit-learn's cross-validation scorers report **negative** MSE (so that,
  like every other scorer, a higher score is always better); negate it back
  to ordinary (positive) MSE before printing.
""",
            "wp45-302-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# 1. create the model/pipeline (StandardScaler + KNeighborsRegressor(k=K_EXAMPLE))
# 2. set up five folds (KFold(n_splits=5, shuffle=True, random_state=0))
# 3. for each fold: fit on that fold's training participants, predict its
#    validation participants, and record that fold's MSE -- ordinary
#    (positive) MSE, not cross_validate's negated scorer output
# 4. compute the mean of the five fold MSEs
#
# Required names: cv_fold_mse (5 values, one per fold), cv_mean_mse
""",
            f"""
cv_pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))
cv_folds = KFold(n_splits=5, shuffle=True, random_state=0)
cv_scores = cross_validate(cv_pipe, X, y, cv=cv_folds, scoring=("neg_mean_squared_error", "r2"))

# scikit-learn reports NEGATIVE MSE; negate it back to ordinary (positive) MSE.
cv_fold_mse = -cv_scores["test_neg_mean_squared_error"]
cv_fold_r2 = cv_scores["test_r2"]
cv_mean_mse = cv_fold_mse.mean()
cv_mean_r2 = cv_fold_r2.mean()
for i, (fold_mse, fold_r2) in enumerate(zip(cv_fold_mse, cv_fold_r2), start=1):
    print(f"fold {{i}}: MSE = {{fold_mse:.1f}}   R^2 = {{fold_r2:.3f}}")
print(f"mean MSE = {{cv_mean_mse:.1f}}   (sd {{cv_fold_mse.std():.1f}})")
print(f"mean R^2 = {{cv_mean_r2:.3f}}")
""",
            "wp45-303-blank",
            tags=["wp45-activity-cv"],
        ),
        code(
            f"""
# Run this to check your cross-validation results.
EXPECTED_CV_MEAN_MSE = {EXPECTED_CV_MEAN_MSE}
MSE_TOLERANCE = 8.0  # generous: absorbs reasonable, equally valid fold orderings

if "cv_fold_mse" in globals() and "cv_mean_mse" in globals():
    import numpy as np
    fold_mses = np.asarray(cv_fold_mse, dtype=float)
    if len(fold_mses) != 5:
        print(f"Not quite: found {{len(fold_mses)}} fold MSE values; 5-fold cross-validation should give exactly 5.")
    elif not np.isfinite(fold_mses).all() or (fold_mses < 0).any():
        print("Not quite: every fold MSE should be a finite, non-negative number.")
    elif abs(cv_mean_mse - EXPECTED_CV_MEAN_MSE) <= MSE_TOLERANCE:
        print(f"Looks good: 5 fold MSEs, mean MSE = {{cv_mean_mse:.1f}} (expected ~{{EXPECTED_CV_MEAN_MSE:.1f}}).")
    else:
        print(
            f"Your mean MSE ({{cv_mean_mse:.1f}}) differs from the expected result "
            f"(~{{EXPECTED_CV_MEAN_MSE:.1f}}). That does not automatically mean something "
            "is wrong -- check that you used k=K_EXAMPLE, the full X/y, and "
            "KFold(n_splits=5, shuffle=True, random_state=0) before assuming this is an error."
        )
else:
    print("Not complete yet: define cv_fold_mse and cv_mean_mse above first.")
""",
            "wp45-304-check",
        ),
        md(
            """
Five folds give five MSE values from the *same* participants and the *same*
fixed `k` -- they differ because each fold holds out a different subset of
participants, not because the model changed. This is model **evaluation**,
not model **tuning**: `k` stayed fixed throughout. Section 5 introduces
tuning.
""",
            "wp45-305-note",
        ),
    ]


# --- Section 4: One Split or Several Folds? (native widget) ---------------

_SAMPLE_SIZES_LITERAL = "[30, 50, 75, 100, 150, 250, 500, 'all']"


def _section_4() -> list[dict]:
    return [
        md("## 4. One Split or Several Folds?", "wp45-401-header"),
        md(
            """
With the full eligible cohort (1004 participants), a single split and
5-fold cross-validation usually give broadly similar answers. That is not
true at every sample size: at small sample sizes, the single-split test
score can swing widely depending on which participants happened to land in
the test set -- for some seeds it can even fall below zero R², worse than
always predicting the training-set mean age.

Choose a sample size and a random seed below. The seed changes only how the
same pool of participants is partitioned into splits/folds, never which
participants are in the pool -- so any difference you see between seeds is
purely due to which participants fell on each side.
""",
            "wp45-402-intro",
        ),
        code(
            """
_STABILITY_SAMPLE_SIZES = [30, 50, 75, 100, 150, 250, 500, "all"]
_STABILITY_POOL_MASTER_SEED = 20270  # one fixed permutation of the eligible cohort; pools nest


def _stability_pools(n_eligible):
    rng = np.random.default_rng(_STABILITY_POOL_MASTER_SEED)
    order = rng.permutation(n_eligible)
    pools = {}
    for size in _STABILITY_SAMPLE_SIZES:
        n = n_eligible if size == "all" else min(size, n_eligible)
        pools[size] = order[:n]
    return pools


def _stability_single_split(Xs, ys, seed):
    Xtr, Xte, ytr, yte = train_test_split(Xs, ys, test_size=0.25, random_state=seed)
    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE)).fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    return mean_squared_error(yte, pred), r2_score(yte, pred)


def _stability_cv(Xs, ys, seed, folds=5):
    kf = KFold(n_splits=folds, shuffle=True, random_state=seed)
    pipe = make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))
    scores = cross_validate(pipe, Xs, ys, cv=kf, scoring=("neg_mean_squared_error", "r2"))
    return (-scores["test_neg_mean_squared_error"]).mean(), scores["test_r2"].mean()


if all(name in globals() for name in ("X", "y")):
    _stability_pools_cache = _stability_pools(len(y))

    _stability_size_dropdown = widgets.Dropdown(
        options=[(str(s), s) for s in _STABILITY_SAMPLE_SIZES], value=100, description="sample size:"
    )
    _stability_seed_dropdown = widgets.Dropdown(
        options=[0, 1, 2, 3, 4], value=0, description="seed:"
    )
    _stability_output = widgets.Output()

    def _stability_refit(_change=None):
        with _stability_output:
            _stability_output.clear_output(wait=True)
            size = _stability_size_dropdown.value
            seed = _stability_seed_dropdown.value
            idx = _stability_pools_cache[size]
            Xp, yp = X[idx], y[idx]
            n = len(yp)
            if n < 20:
                print(f"n = {n} is too small for a stable 75/25 split and 5-fold CV at k={K_EXAMPLE}.")
                return
            single_mse, single_r2 = _stability_single_split(Xp, yp, seed)
            cv_mse, cv_r2 = _stability_cv(Xp, yp, seed)
            print(f"sample size = {n}   seed = {seed}   k = {K_EXAMPLE}")
            print(f"single split:       test MSE = {single_mse:.1f}   test R^2 = {single_r2:+.3f}")
            print(f"5-fold CV (mean):   test MSE = {cv_mse:.1f}   test R^2 = {cv_r2:+.3f}")

    _stability_size_dropdown.observe(_stability_refit, names="value")
    _stability_seed_dropdown.observe(_stability_refit, names="value")
    display(widgets.VBox([_stability_size_dropdown, _stability_seed_dropdown, _stability_output]))
    _stability_refit()
else:
    print("Complete Section 1 first: X and y are not defined yet.")
""",
            "wp45-403-widget",
        ),
        code(
            """
show_question("q-single-split-vs-cv-stability")
""",
            "wp45-404-checked",
        ),
    ]


# --- Section 5: Nested cross-validation ------------------------------------

# WP48: this diagram used to be raw HTML with every fold block's size and
# color carried only by an inline style="..." attribute -- JupyterLab/
# JupyterLite's markdown-HTML sanitizer strips that attribute, which a live
# screenshot confirmed: only the loose headings, fold numbers, and arrows
# survived, with no visible colored blocks at all. A rendered image sent as
# a notebook attachment (nbformat's own mechanism, already used for
# scripts/generate_exercise_02_notebook.py's Activity 3B reference image)
# is always allowed through -- in JupyterLite, local Jupyter, and Colab
# alike -- so it replaces the HTML entirely. Render with
# scripts/render_exercise_04_nested_cv_diagram.py; this is a fixed
# conceptual illustration, not derived from student data.
NCV_DIAGRAM_IMAGE_FILENAME = "exercise_04_nested_cv_diagram.png"


def _ncv_diagram_attachments() -> dict:
    encoded = base64.b64encode(NCV_DIAGRAM_IMAGE_PATH.read_bytes()).decode("ascii")
    return {NCV_DIAGRAM_IMAGE_FILENAME: {"image/png": encoded}}


def _ncv_diagram_markdown() -> str:
    alt_text = (
        "Nested cross-validation diagram: on the left, 5 outer iterations, "
        "each a row of 5 blocks with one outer-test block (yellow) rotating "
        "position and the rest outer-training (blue); iteration 2 is "
        "outlined. An arrow leads to the right panel, zoomed into that "
        "outlined iteration's outer-training data: 5 inner iterations, each "
        "a row of 5 blocks with one inner-validation block (orange) "
        "rotating and the rest inner-training (green). A second arrow leads "
        "to three captioned steps: inner folds select k; refit the selected "
        "k on all of this outer fold's training data; score once on this "
        "outer fold's own held-out test block. A footer note states this "
        "repeats for every outer fold, and the 5 outer-test scores are then "
        "averaged into the nested-CV estimate."
    )
    return f"![{alt_text}](attachment:{NCV_DIAGRAM_IMAGE_FILENAME})"

def _section_5() -> list[dict]:
    return [
        md("## 5. Nested Cross-Validation", "wp45-501-header"),
        md(
            """
Section 3 evaluated one fixed `k`. What if `k` itself needs choosing?
**Nested cross-validation** reuses the same participants for both tuning
and evaluation, without letting the two mix: an **inner** cross-validation
chooses `k`, using only the current outer fold's training data; an
**outer** cross-validation evaluates the complete tuning procedure --
inner selection included -- on data the inner loop never saw.
""",
            "wp45-502-intro",
        ),
        md(
            _ncv_diagram_markdown(),
            "wp45-503-diagram",
            attachments=_ncv_diagram_attachments(),
        ),
        md(
            f"""
Complete the pipeline below: an outer `KFold` splits the full cohort; for
each outer fold, an inner `GridSearchCV` selects `k` from `NESTED_CANDIDATE_KS`
using only that outer fold's training data; the selected model is then
evaluated once on that outer fold's test data. Because each outer fold's
training data contains different participants, different outer folds
*can* select different `k` -- the inner cross-validation does not have to
agree with itself from fold to fold.
""",
            "wp45-504-instructions",
        ),
        blank(
            f"""
NESTED_CANDIDATE_KS = {NESTED_CANDIDATE_KS}
N_OUTER, N_INNER = 5, 5
OUTER_SEED, INNER_SEED = 100, 101

outer_cv = KFold(n_splits=N_OUTER, shuffle=True, random_state=OUTER_SEED)
inner_cv = KFold(n_splits=N_INNER, shuffle=True, random_state=INNER_SEED)

nested_rows = []
for fold_i, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]

    # YOUR CODE HERE
    # 1. build a Pipeline(StandardScaler(), KNeighborsRegressor()) and wrap
    #    it in a GridSearchCV over {{"knn__n_neighbors": NESTED_CANDIDATE_KS}},
    #    scoring="neg_mean_squared_error", cv=inner_cv;
    # 2. fit that GridSearchCV on X_tr, y_tr ONLY (never X_te/y_te);
    # 3. selected_k = ... (the fitted search's best n_neighbors)
    # 4. pred = ... (the fitted search's predictions on X_te)
    # 5. append a dict with keys "outer_fold", "selected_k", "outer_test_mse",
    #    "outer_test_r2" to nested_rows (use mean_squared_error/r2_score on
    #    y_te and pred)

nested = pd.DataFrame(nested_rows)
nested.round(3)
""",
            f"""
NESTED_CANDIDATE_KS = {NESTED_CANDIDATE_KS}
N_OUTER, N_INNER = 5, 5
OUTER_SEED, INNER_SEED = 100, 101

outer_cv = KFold(n_splits=N_OUTER, shuffle=True, random_state=OUTER_SEED)
inner_cv = KFold(n_splits=N_INNER, shuffle=True, random_state=INNER_SEED)

nested_rows = []
for fold_i, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]

    pipe = Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsRegressor())])
    grid = GridSearchCV(
        pipe,
        param_grid={{"knn__n_neighbors": NESTED_CANDIDATE_KS}},
        scoring="neg_mean_squared_error",
        cv=inner_cv,
    )
    grid.fit(X_tr, y_tr)  # only this outer fold's TRAINING data
    selected_k = grid.best_params_["knn__n_neighbors"]
    pred = grid.predict(X_te)  # the outer TEST fold, evaluated once

    nested_rows.append({{
        "outer_fold": fold_i + 1,
        "selected_k": selected_k,
        "outer_test_mse": mean_squared_error(y_te, pred),
        "outer_test_r2": r2_score(y_te, pred),
    }})

nested = pd.DataFrame(nested_rows)
nested.round(3)
""",
            "wp45-505-blank",
            tags=["wp45-activity-nested-cv"],
        ),
        code(
            f"""
# Run this to check your nested cross-validation results.
EXPECTED_NESTED_MEAN_MSE = {EXPECTED_NESTED_MEAN_MSE}
NESTED_MSE_TOLERANCE = 10.0  # generous: absorbs reasonable implementation differences

if "nested" in globals() and len(nested) > 0:
    if len(nested) != 5:
        print(f"Not quite: found {{len(nested)}} outer-fold rows; 5-fold outer cross-validation should give exactly 5.")
    elif not set(nested["selected_k"]).issubset(set(NESTED_CANDIDATE_KS)):
        print("Not quite: every selected_k should come from NESTED_CANDIDATE_KS.")
    elif not (nested["outer_test_mse"] >= 0).all():
        print("Not quite: every outer_test_mse should be non-negative.")
    else:
        mean_mse = nested["outer_test_mse"].mean()
        if abs(mean_mse - EXPECTED_NESTED_MEAN_MSE) <= NESTED_MSE_TOLERANCE:
            print(f"Looks good: mean outer-test MSE = {{mean_mse:.1f}} (expected ~{{EXPECTED_NESTED_MEAN_MSE:.1f}}).")
        else:
            print(
                f"Your mean outer-test MSE ({{mean_mse:.1f}}) differs from the expected "
                f"result (~{{EXPECTED_NESTED_MEAN_MSE:.1f}}). That does not automatically "
                "mean something is wrong -- check that the inner GridSearchCV only ever "
                "sees this outer fold's training data before assuming this is an error."
            )
        print(f"selected k per outer fold: {{list(nested['selected_k'])}}")
else:
    print("Not complete yet: complete the nested cross-validation pipeline above first.")
""",
            "wp45-506-check",
        ),
        md(
            """
With this denser candidate grid, the outer folds may not all agree on
`selected_k` -- different outer folds *can* select different values,
because each outer training set contains different participants. They are
not guaranteed to disagree, only permitted to. The best *inner*
cross-validation score is not reported as a final performance estimate: it
is biased toward whichever candidate happened to look best on the data used
to choose it. The **outer**-test MSE and R², averaged over folds that never
influenced any tuning decision, estimate the performance of the whole
tuning procedure -- not of one fixed model.
""",
            "wp45-507-note",
        ),
        md(
            "> **In your own words, why is it acceptable -- even expected -- for different outer folds to select different values of k, rather than being a sign that something went wrong?**",
            "wp45-507b-reflection",
        ),
        code(
            """
show_question("q-inner-loop-data")
""",
            "wp45-508-checked",
        ),
        code(
            """
show_question("q-outer-test-mse-meaning")
""",
            "wp45-509-checked",
        ),
    ]


def _summary() -> list[dict]:
    return [
        md(
            """
## In summary

- One train/test split is an honest but single estimate; its exact number
  depends on which participants land in each subset, and that dependence is
  most visible at small sample sizes. Cross-validation evaluates the same
  fixed model across several partitions instead of one.
- scikit-learn's cross-validation scorers report negative MSE so that a
  higher score is always better across every scorer -- negate it back to
  ordinary MSE before interpreting it.
- Nested cross-validation keeps tuning and evaluation separate: an inner
  loop chooses `k`, an outer loop evaluates the whole procedure on data the
  inner loop never saw. Different outer folds can select different `k`
  values, because each has different training data.
- No single validation strategy is always correct -- the right one depends
  on dataset size and on whether the model is being tuned or only evaluated.

Next practice: regularization and feature selection.
""",
            "wp45-601-summary",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1()
    cells += _section_2()
    section_3 = _section_3()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_3]
    cells += _section_4()
    section_5 = _section_5()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_5]
    cells += _summary()
    return cells


def build_notebook(mode: str) -> nbformat.NotebookNode:
    nb = new_notebook()
    nb["metadata"] = dict(KERNELSPEC)
    nb["cells"] = _build_cells(mode)
    return nb


def _serialize(nb: nbformat.NotebookNode) -> str:
    return nbformat.writes(nb, version=4)


def _write_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return False
    path.write_text(text)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--student", action="store_true")
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        raise SystemExit("exactly one of --write or --check is required")
    do_student = args.student or not args.reference
    do_reference = args.reference or not args.student

    changed: list[str] = []
    stale: list[str] = []

    if do_student:
        nb = build_notebook("student")
        text = _serialize(nb)
        for path in (LITE_TEMPLATE_PATH, PORTABLE_PATH, LITE_FILES_PORTABLE_COPY_PATH):
            if args.write:
                if _write_if_changed(path, text):
                    changed.append(str(path.relative_to(REPO_ROOT)))
            else:
                if not path.exists() or path.read_text() != text:
                    stale.append(str(path.relative_to(REPO_ROOT)))

    if do_reference:
        nb = build_notebook("reference")
        text = _serialize(nb)
        if args.write:
            if _write_if_changed(REFERENCE_PATH, text):
                changed.append(str(REFERENCE_PATH.relative_to(REPO_ROOT)))
        else:
            if not REFERENCE_PATH.exists() or REFERENCE_PATH.read_text() != text:
                stale.append(str(REFERENCE_PATH.relative_to(REPO_ROOT)))

    if args.write:
        if changed:
            print("wrote:\n  " + "\n  ".join(changed))
        else:
            print("up to date")
    else:
        if stale:
            raise SystemExit("stale (run --write):\n  " + "\n  ".join(stale))
        print("OK: all requested outputs are up to date")


if __name__ == "__main__":
    main()
