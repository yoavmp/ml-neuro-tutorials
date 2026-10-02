#!/usr/bin/env python3
"""Generate Exercise 5's JupyterLite template, portable copy, and reference.

WP45: migrate Exercise 5 ("Regularization and Feature Selection") to the
same JupyterLite-native, generator-authored architecture WP41/WP42/WP44
established for Exercises 1-3 (see WPs/reports/WP41_MAINTAINER_GUIDE.md),
following scripts/generate_exercise_04_notebook.py's exact shape (built in
the same WP45).

Data: reuses the exact same same-origin export Exercises 2-4 already ship,
book/lite/files/data/abide_age_brain.csv (360 fsCT predictors + age + group,
1004 participants). No second, independent data export is created.

The seven predefined ROI bundles for Section 2's feature-set comparison are
read, at GENERATION time only (never at notebook runtime), from the
already-audited widget data book/_static/widgets/data/abide_regression_models.json
(the same source the pre-migration iframe activity used) and embedded as a
literal column-name list per bundle -- the same pattern
scripts/generate_exercise_03_notebook.py uses for its 360-column feature
list via DATA_SIDECAR. Scoped to the cortical-thickness (CT) measurement
only, matching every other fixed predictor recipe in this notebook (Section
3 onward use the same 360 fsCT_ columns); the other measurement types
(surface area, volume, gyrification) that the legacy iframe widget also
offered are not loaded anywhere else in this notebook and are out of this
migration's scope (documented in the WP45 report as a deliberate trim).

Numbers below were verified directly against book/lite/files/data/abide_age_brain.csv
before writing a single generator line (WP45 report has the verification
script/output), and the Section 2 bundle numbers additionally reproduce
book/_static/widgets/data/abide_regression_models.json's own precomputed
"models" entries bit-for-bit:
  bundle R^2/MSE (StandardScaler+LinearRegression, same 42-seed 75/25 split):
    frontoparietal (78 feat) MSE=52.7045 R2=0.435406
    frontal        (42 feat) MSE=55.7944 R2=0.402307
    parietal       (42 feat) MSE=53.5800 R2=0.426028
    temporal       (36 feat) MSE=55.1640 R2=0.409059
    occipital      (46 feat) MSE=49.3453 R2=0.471392
    sensorimotor   (40 feat) MSE=49.9171 R2=0.465267
    all-eligible  (360 feat) MSE=49.5544 R2=0.469152
  Section 3 SelectKBest(f_regression) CV grid on X_train/y_train, K_GRID =
    [5,10,20,40,80,160,360]: best k by CV = 80 (cv_mse=40.8251); fixed-k=80
    selection (train-only) -> selected_test_mse=39.3416, r2=0.578556; the
    full-feature linear-regression baseline (identical split/protocol) ->
    MSE=49.5544, R2=0.469152.
  Section 4 Ridge(alpha=1.0), train-only-scaled pipeline, held-out test:
    MSE=48.7896 R2=0.477344 nnz=360. Lasso(alpha=0.1), same protocol:
    MSE=29.8770 R2=0.679945 nnz=163 (the reference notebook's own Lasso
    choice, used only as the check cell's tolerance anchor -- students
    choose their own alpha).
  Section 5 Lasso alpha tuned by CV (train-only pipeline+search, test set
    read once after selection): selected alpha=0.21544, test MSE=30.8750,
    R2=0.669254, nonzero=88/360.

Outputs:
  book/lite/files/exercise_05.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_05/exercise_05_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_05_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_05_reference.ipynb (--reference)

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
BUNDLE_SOURCE = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_regression_models.json"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_05.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_05" / "exercise_05_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_05_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_05_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 5, "templateVersion": TEMPLATE_VERSION},
}

BUNDLE_ORDER = [
    "frontoparietal",
    "frontal",
    "parietal",
    "temporal",
    "occipital",
    "sensorimotor",
    "all-eligible",
]
BUNDLE_LABELS = {
    "frontoparietal": "Frontoparietal",
    "frontal": "Prefrontal only",
    "parietal": "Parietal only",
    "temporal": "Lateral temporal (comparison)",
    "occipital": "Occipital / early visual (comparison)",
    "sensorimotor": "Sensorimotor (comparison)",
    "all-eligible": "All eligible ROIs",
}
# WP14 audit (see book/config/abide_modeling.json's atlas.hemisphere_specific_labels):
# the only HCP-MMP1 parcel whose two hemisphere columns do not share a raw
# suffix -- canonical ROI "5" is 'fsCT_L_5L_ROI' / 'fsCT_R_5R_ROI'.
_HEMISPHERE_SPECIFIC_LABELS = {"5": {"L": "5L", "R": "5R"}}

K_GRID = [5, 10, 20, 40, 80, 160, 360]
K_SELECT = 80
RIDGE_ALPHA_EXAMPLE = 1.0
LASSO_ALPHA_EXAMPLE = 0.1
EXPECTED_FULL_BASELINE_MSE = 49.5544
EXPECTED_SELECTED_TEST_MSE = 39.3416
EXPECTED_RIDGE_TEST_MSE = 48.7896
EXPECTED_LASSO_EXAMPLE_TEST_MSE = 29.8770
EXPECTED_LASSO_CV_TEST_MSE = 30.8750


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


def _raw_label(roi: str, hemi: str) -> str:
    return _HEMISPHERE_SPECIFIC_LABELS.get(roi, {}).get(hemi, roi)


def _bundle_features_literal() -> str:
    source = json.loads(BUNDLE_SOURCE.read_text())
    bundles = source["bundles"]
    lines = ["_FEATURE_BUNDLES = {"]
    for key in BUNDLE_ORDER:
        rois = bundles[key]["rois"]
        feats = [f"fsCT_{h}_{_raw_label(roi, h)}_ROI" for roi in rois for h in ("L", "R")]
        lines.append(f"    {key!r}: [")
        for i in range(0, len(feats), 4):
            chunk = ", ".join(repr(c) for c in feats[i : i + 4])
            lines.append(f"        {chunk},")
        lines.append("    ],")
    lines.append("}")
    labels_literal = ", ".join(f"{k!r}: {v!r}" for k, v in BUNDLE_LABELS.items())
    lines.append(f"_FEATURE_BUNDLE_LABELS = {{{labels_literal}}}")
    return "\n".join(lines)


# Duplicates (never imports) generate_exercise_02_notebook.py's setup-cell
# pattern -- each generator module is a self-contained, independently
# regenerable source of truth (WP41 maintainer guide section 4.7).
SETUP_SOURCE_TEMPLATE = '''
import sys
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

{bundles_literal}


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
# visible call like show_question("q-selectkbest-leakage") never prints or
# displays a correct_index/correct_indices value. This is visual concealment,
# not secure assessment: the hidden cell is fully expandable, and a downloaded,
# fully offline, editable notebook must contain enough information to check an
# answer locally, so a technically curious student can always recover it from
# source or the running kernel.
_QUESTIONS = {
    "q-selectkbest-leakage": dict(
        kind="single",
        prompt=(
            "Why must SelectKBest be fit on X_train/y_train only, rather than on "
            "the full X/y before splitting?"
        ),
        options=[
            "Fitting it on all participants would let information from the test set influence which predictors the model is allowed to see -- data leakage that makes the test score an overly optimistic estimate.",
            "SelectKBest only works on training data for implementation reasons unrelated to leakage.",
            "It would make the notebook run more slowly.",
        ],
        correct_index=0,
        feedback_correct="Correct: a feature selector is a fitting step like any other, and must never see the test set before evaluation.",
    ),
    "q-alpha-tuning-leakage": dict(
        kind="single",
        prompt=(
            "Why does tuning alpha with cross-validation on the training set, "
            "rather than by checking which alpha gives the lowest held-out test "
            "MSE, matter?"
        ),
        options=[
            "Choosing alpha by minimizing the test MSE directly would use the test set to make a modeling decision, so the final test score would no longer be an honest estimate of performance on new participants.",
            "Cross-validation always selects a smaller alpha than checking the test set would.",
            "It does not matter, as long as the final number reported is the test MSE.",
        ],
        correct_index=0,
        feedback_correct="Correct: any decision that uses the test set, including choosing a hyperparameter, compromises the test set as an honest final evaluation.",
    ),
    "q-ridge-lasso-properties": dict(
        kind="multi",
        prompt="Which of the following are true about Ridge and Lasso coefficients?",
        options=[
            "Ridge shrinks coefficients toward zero but rarely sets any exactly to zero.",
            "Lasso can set some coefficients to exactly zero, dropping those predictors.",
            "Both methods require predictors to be standardized for the penalty to be fair.",
            "Ridge always produces a smaller held-out MSE than Lasso.",
        ],
        correct_indices={0, 1, 2},
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
    source = SETUP_SOURCE_TEMPLATE.replace("{features_literal}", _feature_list_literal()).replace(
        "{bundles_literal}", _bundle_features_literal()
    )
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
        md("# Exercise 5: Regularization and Feature Selection", "wp45-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 5 of *Machine Learning for Neuroscience*. It reuses
Exercise 2 and Exercise 4's exact ABIDE-II age-prediction data, target, and
fixed 75/25 train/test split, and asks a question those notebooks set
aside: how do we decide which predictors to include?

In this notebook you will:

1. compare several predefined cortical-thickness feature sets;
2. select features using training-data associations with the target, inside
   a leakage-safe procedure;
3. fit Ridge and Lasso regression and compare their coefficients;
4. tune Lasso's regularization strength with cross-validation.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 2's regression material and Exercise 4's
validation and cross-validation material; comfort with `pandas`, `numpy`,
and the scikit-learn `fit` / `predict` / `Pipeline` pattern.
""",
            "wp45-002-overview",
        ),
    ]


def _section_1_data() -> list[dict]:
    return [
        md("## 1. Data and Setup", "wp45-101-header"),
        md(
            """
This notebook reuses Exercise 2 and Exercise 4's exact ABIDE-II data table,
target (age), fixed 360-column cortical-thickness feature recipe, and fixed
train/test split -- nothing about the data or the split changes here.
""",
            "wp45-102-intro",
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

from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.metrics import mean_squared_error, r2_score

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
X = df[FEATURES].to_numpy(float)
y = df["age"].to_numpy(float)
groups = df["group"].to_numpy()  # 1 = autism, 2 = control; stratification key only, never a predictor

X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=42, stratify=groups
)
print(f"{len(FEATURES)} predictors, e.g. {FEATURES[:3]}")
print(f"n_train = {len(y_train)}   n_test = {len(y_test)}   n_features = {X.shape[1]}")
""",
            "wp45-103-load",
        ),
    ]


def _section_2_predefined() -> list[dict]:
    return [
        md("## 2. Compare Predefined Feature Sets", "wp45-201-header"),
        md(
            """
Prior knowledge can define a feature set before model fitting. Cortical
structure changes with age across most of the brain, not in one
circumscribed system (Bethlehem et al., 2022,
[doi:10.1038/s41586-022-04554-y](https://doi.org/10.1038/s41586-022-04554-y);
Storsve et al., 2014,
[doi:10.1523/JNEUROSCI.0391-14.2014](https://doi.org/10.1523/JNEUROSCI.0391-14.2014)),
so there is no single small region set this course's own age literature
prefers. The bundles below are used simply as several differently sized,
differently located cortical-thickness comparisons, each chosen before
looking at how well it predicts age in this cohort.

Choose two bundles below. Both models use the same fixed cohort, the same
train/test split, and the same `StandardScaler` + `LinearRegression`
procedure -- so any difference you see is a real difference between feature
sets, not a difference in evaluation.
""",
            "wp45-202-intro",
        ),
        code(
            """
_bundle_cache = {}


def _bundle_eval(bundle_key):
    if bundle_key in _bundle_cache:
        return _bundle_cache[bundle_key]
    feats = _FEATURE_BUNDLES[bundle_key]
    Xb = df[feats].to_numpy(float)
    Xb_train, Xb_test, yb_train, yb_test = train_test_split(
        Xb, y, test_size=0.25, random_state=42, stratify=groups
    )
    model = make_pipeline(StandardScaler(), LinearRegression()).fit(Xb_train, yb_train)
    pred = model.predict(Xb_test)
    result = {
        "n_features": len(feats),
        "mse": mean_squared_error(yb_test, pred),
        "r2": r2_score(yb_test, pred),
    }
    _bundle_cache[bundle_key] = result
    return result


_bundle_options = [(_FEATURE_BUNDLE_LABELS[k], k) for k in _FEATURE_BUNDLES]
bundle_a_dropdown = widgets.Dropdown(options=_bundle_options, value="frontoparietal", description="Model A:")
bundle_b_dropdown = widgets.Dropdown(options=_bundle_options, value="occipital", description="Model B:")
_bundle_output = widgets.Output()


def _bundle_refresh(_change=None):
    with _bundle_output:
        _bundle_output.clear_output(wait=True)
        a = _bundle_eval(bundle_a_dropdown.value)
        b = _bundle_eval(bundle_b_dropdown.value)
        summary = pd.DataFrame(
            [
                {"model": "A: " + _FEATURE_BUNDLE_LABELS[bundle_a_dropdown.value], **a},
                {"model": "B: " + _FEATURE_BUNDLE_LABELS[bundle_b_dropdown.value], **b},
            ]
        ).set_index("model")
        display(summary.round(3))

        fig, ax = plt.subplots(figsize=(4.4, 3.0))
        ax.bar(["A", "B"], [a["r2"], b["r2"]], color=["#2a6f9e", "#b5622f"])
        ax.set_ylabel("held-out R^2")
        ax.set_title("Predefined feature-set comparison")
        plt.tight_layout()
        plt.show()


bundle_a_dropdown.observe(_bundle_refresh, names="value")
bundle_b_dropdown.observe(_bundle_refresh, names="value")
display(widgets.VBox([bundle_a_dropdown, bundle_b_dropdown, _bundle_output]))
_bundle_refresh()
""",
            "wp45-204-widget",
        ),
        md(
            """
Trying several feature sets on the same evaluation data is **exploratory comparison**.
If we choose the best-looking set, that choice must be
included inside a new validation procedure before reporting final
performance.
""",
            "wp45-205-note",
        ),
        md(
            '> **Set both models to different bundles above, including "All eligible ROIs". What happens to the feature count and R² as you add more predictors -- does it always improve?**',
            "wp45-206-reflection",
        ),
    ]


def _section_2b_bridge() -> list[dict]:
    return [
        md(
            """
Even if a large bundle like "All eligible ROIs" performs best among these
predefined sets, could another *combination* of features work better? A
predefined set is based on domain knowledge, chosen independently of this
cohort's target values. A set **selected using the training observations**
is different -- and is what the rest of this notebook builds.
""",
            "wp45-211-bridge",
        ),
    ]


def _section_3_select() -> list[dict]:
    return [
        md("## 3. Select Features Using the Data", "wp45-301-header"),
        md(
            """
Instead of choosing a feature set from prior knowledge, we can rank
features by how strongly each one, on its own, relates to age, and use that
ranking to select a subset. A **feature selector** must be fit on training
data only -- exactly like `StandardScaler` -- or the test set's own
information would leak into which predictors the model is allowed to see.

The cell below cross-validates several candidate retained-feature counts
(`K_GRID`) with `SelectKBest(score_func=f_regression)` inside a `Pipeline`,
using only the training partition. `f_regression` ranks each feature by its
own individual association with the target -- it does not try every
combination of features.
""",
            "wp45-302-intro",
        ),
        code(
            f"""
K_GRID = {K_GRID}

select_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("select", SelectKBest(score_func=f_regression)),
    ("lr", LinearRegression()),
])
select_cv = KFold(n_splits=5, shuffle=True, random_state=0)
select_grid = GridSearchCV(
    select_pipe, {{"select__k": K_GRID}}, scoring="neg_mean_squared_error", cv=select_cv, n_jobs=-1
)
select_grid.fit(X_train, y_train)

select_results = pd.DataFrame({{
    "k": K_GRID,
    "cv_mse": -select_grid.cv_results_["mean_test_score"],
}})
print(f"best k by cross-validation: {{select_grid.best_params_['select__k']}}")

fig, ax = plt.subplots(figsize=(5.6, 3.4))
ax.plot(select_results["k"], select_results["cv_mse"], marker="o")
ax.set_xscale("log")
ax.set_xlabel("retained features, k (log scale)")
ax.set_ylabel("cross-validation MSE (lower is better)")
ax.set_title("SelectKBest: retained-feature count vs cross-validation MSE")
plt.tight_layout()
plt.show()
select_results.round(2)
""",
            "wp45-303-curve",
        ),
        md(
            """
Cross-validation MSE improves as `k` grows, reaches a minimum, then gets
worse again at `k = 360` (every feature) -- selecting more features does
not always improve validation performance.
""",
            "wp45-304-note",
        ),
        md(
            f"""
### Select the {K_SELECT} best features and evaluate them

Using `K_SELECT = {K_SELECT}` (the value this course's own cross-validation
search above selected), write code that:
- fits `SelectKBest(score_func=f_regression, k=K_SELECT)` on `X_train`,
  `y_train` **only**;
- builds `selected_features` (the selected column names, from `FEATURES`);
- fits a `StandardScaler` + `LinearRegression` pipeline, `selected_model`,
  on the selected training columns only;
- evaluates it on the selected test columns, storing the held-out MSE as
  `selected_test_mse`.

Required names: `selected_features`, `selected_model`, `selected_test_mse`.
""",
            "wp45-305-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# selector = SelectKBest(score_func=f_regression, k=K_SELECT).fit(X_train, y_train)
# selected_features = ...
# selected_model = ...
# selected_test_mse = ...
""",
            f"""
K_SELECT = {K_SELECT}

selector = SelectKBest(score_func=f_regression, k=K_SELECT).fit(X_train, y_train)
selected_idx = selector.get_support(indices=True)
selected_features = [FEATURES[i] for i in selected_idx]

selected_model = make_pipeline(StandardScaler(), LinearRegression())
selected_model.fit(X_train[:, selected_idx], y_train)
selected_pred = selected_model.predict(X_test[:, selected_idx])
selected_test_mse = mean_squared_error(y_test, selected_pred)
print(f"selected {{len(selected_features)}} features, e.g. {{selected_features[:5]}}")
print(f"selected-feature held-out MSE = {{selected_test_mse:.1f}}")
""",
            "wp45-306-blank",
            tags=["wp45-activity-select"],
        ),
        code(
            f"""
# Run this to check your feature-selection results.
EXPECTED_SELECTED_TEST_MSE = {EXPECTED_SELECTED_TEST_MSE}
SELECT_MSE_TOLERANCE = 6.0  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("selected_features", "selected_model", "selected_test_mse")):
    if len(selected_features) != K_SELECT:
        print(f"Not quite: selected_features has {{len(selected_features)}} names; K_SELECT = {{K_SELECT}}.")
    elif not set(selected_features).issubset(set(FEATURES)):
        print("Not quite: selected_features should be a subset of FEATURES.")
    elif abs(selected_test_mse - EXPECTED_SELECTED_TEST_MSE) <= SELECT_MSE_TOLERANCE:
        print(f"Looks good: {{len(selected_features)}} features selected, held-out MSE = {{selected_test_mse:.1f}} (expected ~{{EXPECTED_SELECTED_TEST_MSE:.1f}}).")
    else:
        print(
            f"Your held-out MSE ({{selected_test_mse:.1f}}) differs from the expected "
            f"result (~{{EXPECTED_SELECTED_TEST_MSE:.1f}}). That does not automatically "
            "mean something is wrong -- check that the selector was fit on X_train/y_train "
            "only before assuming this is an error."
        )
else:
    print("Not complete yet: define selected_features, selected_model, and selected_test_mse above first.")
""",
            "wp45-307-check",
        ),
        md(
            """
The cell below compares your selected-feature result against a full-feature
linear-regression baseline, trained and evaluated with the same split and
protocol. It uses your actual `selected_test_mse` -- never a substitute.
""",
            "wp45-308-compare-intro",
        ),
        code(
            """
if "selected_test_mse" in globals():
    full_model = make_pipeline(StandardScaler(), LinearRegression()).fit(X_train, y_train)
    full_test_mse = mean_squared_error(y_test, full_model.predict(X_test))
    comparison = pd.DataFrame(
        [
            {"model": f"selected ({len(selected_features)} features)", "held_out_mse": selected_test_mse},
            {"model": f"full feature set ({len(FEATURES)} features)", "held_out_mse": full_test_mse},
        ]
    ).set_index("model")
    display(comparison.round(2))
    better = "the selected-feature model" if selected_test_mse < full_test_mse else "the full-feature model"
    print(f"On this split, {better} has the lower held-out MSE.")
else:
    print("Not complete yet: complete the feature-selection activity above first.")
""",
            "wp45-309-compare",
        ),
        code(
            """
show_question("q-selectkbest-leakage")
""",
            "wp45-310-checked",
        ),
    ]


def _section_4_ridge_lasso() -> list[dict]:
    return [
        md("## 4. Ridge and Lasso Regression", "wp45-401-header"),
        md(
            r"""
Ordinary linear regression chooses coefficients to minimize the sum of
squared errors, with no penalty on their size. **Regularization** adds a
penalty on the coefficients' size to that objective:

$$\text{Ridge:}\quad \mathrm{SSE}+\alpha\sum_j\beta_j^2 \qquad\qquad \text{Lasso:}\quad \mathrm{SSE}+\alpha\sum_j|\beta_j|$$

Ridge shrinks every coefficient toward zero but rarely reaches exactly
zero, so it keeps (a shrunk version of) every predictor. Lasso's penalty
can drive individual coefficients to exactly zero, dropping those
predictors from the fitted model entirely -- embedded feature selection.
$\alpha$ controls the penalty's strength for either model; predictors must
be standardized first (fit on training data only), or an unstandardized
predictor with large numeric values would be penalized differently just
because of its units.
""",
            "wp45-402-explain",
        ),
        md(
            """
### A fully worked Ridge example

`alpha = {ridge_alpha}` here is the value used in this example -- not
tuned. Scaling is fit on the training partition only, inside the same
pipeline as the model.
""".replace("{ridge_alpha}", str(RIDGE_ALPHA_EXAMPLE)),
            "wp45-403-ridge-intro",
        ),
        code(
            f"""
RIDGE_ALPHA_EXAMPLE = {RIDGE_ALPHA_EXAMPLE}  # the value used in this example

ridge_model = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA_EXAMPLE))
ridge_model.fit(X_train, y_train)
ridge_pred = ridge_model.predict(X_test)
ridge_mse = mean_squared_error(y_test, ridge_pred)
ridge_nonzero = int(np.sum(np.abs(ridge_model.named_steps["ridge"].coef_) > 1e-10))
print(f"Ridge (alpha={{RIDGE_ALPHA_EXAMPLE}}): held-out MSE = {{ridge_mse:.1f}}   nonzero coefficients = {{ridge_nonzero}} / {{len(FEATURES)}}")
""",
            "wp45-404-ridge",
        ),
        md(
            """
### Choose a Lasso alpha

Write code that fits `Lasso` on the same training participants (`X_train`,
`y_train`), inside a `StandardScaler` pipeline fit on training data only,
using a single `alpha` you choose (`0.1`, Ridge's `alpha` above, and values
a few times larger or smaller are all reasonable starting points), then
evaluates it on the held-out test set.

Required names: `lasso_model`, `lasso_pred`, `lasso_mse`.
""",
            "wp45-405-lasso-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# LASSO_ALPHA = ...  # your choice
# lasso_model = ...
# lasso_pred = ...
# lasso_mse = ...
""",
            f"""
LASSO_ALPHA = {LASSO_ALPHA_EXAMPLE}  # a reasonable starting choice

lasso_model = make_pipeline(StandardScaler(), Lasso(alpha=LASSO_ALPHA, max_iter=20000))
lasso_model.fit(X_train, y_train)
lasso_pred = lasso_model.predict(X_test)
lasso_mse = mean_squared_error(y_test, lasso_pred)
lasso_nonzero = int(np.sum(np.abs(lasso_model.named_steps["lasso"].coef_) > 1e-10))
print(f"Lasso (alpha={{LASSO_ALPHA}}): held-out MSE = {{lasso_mse:.1f}}   nonzero coefficients = {{lasso_nonzero}} / {{len(FEATURES)}}")
""",
            "wp45-406-blank",
            tags=["wp45-activity-lasso"],
        ),
        code(
            """
# Run this to check your Lasso result.
if all(name in globals() for name in ("lasso_model", "lasso_pred", "lasso_mse")):
    if len(lasso_pred) != len(y_test):
        print(f"Not quite: lasso_pred has {len(lasso_pred)} values; it should have one prediction per test row ({len(y_test)}).")
    elif not np.isfinite(lasso_mse):
        print("Not quite: lasso_mse should be a finite number.")
    else:
        coefs = lasso_model.named_steps["lasso"].coef_
        nnz = int(np.sum(np.abs(coefs) > 1e-10))
        print(f"Looks good: held-out MSE = {lasso_mse:.1f}, {nnz} of {len(FEATURES)} coefficients are nonzero.")
        if nnz == len(FEATURES):
            print("None of your coefficients reached exactly zero -- try a larger alpha if you want Lasso's feature-selection effect to show up here.")
else:
    print("Not complete yet: define lasso_model, lasso_pred, and lasso_mse above first.")
""",
            "wp45-407-check",
        ),
        md(
            "The cell below compares full-feature linear regression, Ridge, "
            "and Lasso under the same split and MSE convention, using your "
            "actual Lasso result.",
            "wp45-408-compare-intro",
        ),
        code(
            """
if all(name in globals() for name in ("ridge_mse", "lasso_mse")):
    linear_model = make_pipeline(StandardScaler(), LinearRegression()).fit(X_train, y_train)
    linear_mse = mean_squared_error(y_test, linear_model.predict(X_test))
    linear_nonzero = len(FEATURES)

    table = pd.DataFrame(
        [
            {"model": "Linear regression", "held_out_mse": linear_mse, "nonzero_coefficients": linear_nonzero},
            {"model": f"Ridge (alpha={RIDGE_ALPHA_EXAMPLE})", "held_out_mse": ridge_mse, "nonzero_coefficients": ridge_nonzero},
            {"model": "Lasso (your alpha)", "held_out_mse": lasso_mse, "nonzero_coefficients": lasso_nonzero},
        ]
    ).set_index("model")
    display(table.round(2))

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar(table.index, table["held_out_mse"], color=["#5c5674", "#2a6f9e", "#b5622f"])
    ax.set_ylabel("held-out MSE (lower is better)")
    ax.set_title("Linear regression vs. Ridge vs. Lasso")
    plt.xticks(rotation=12, ha="right")
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: complete the Ridge and Lasso cells above first.")
""",
            "wp45-409-compare",
        ),
        md(
            "> **Which of the three models above uses the fewest predictors? Does that model also have the lowest held-out MSE? Must it?**",
            "wp45-410-reflection",
        ),
    ]


def _section_5_lasso_cv() -> list[dict]:
    return [
        md("## 5. Tune Lasso Alpha with Cross-Validation", "wp45-501-header"),
        md(
            """
Section 4 asked you to guess a single Lasso `alpha`. As in Exercise 4,
tuning should use training data only, and the test set should be read once,
after the tuning decision is locked in.

Write code that builds a train-only pipeline/search: `StandardScaler` +
`Lasso` inside a `Pipeline`, wrapped in a `GridSearchCV` over
`LASSO_ALPHAS`, scored by MSE, cross-validated on `X_train`/`y_train`. Fit
it, then evaluate the best pipeline on the held-out test set **once**.

Required names: `lasso_cv_model` (the fitted `GridSearchCV`),
`lasso_cv_alpha` (the selected alpha), `lasso_cv_pred` (test-set
predictions), `lasso_cv_test_mse` (held-out MSE). These are separate from
Section 4's `lasso_model`/`lasso_pred`/`lasso_mse`, so both stay inspectable.
""",
            "wp45-502-instructions",
        ),
        blank(
            """
LASSO_ALPHAS = list(np.logspace(-3, 1, 25))

# YOUR CODE HERE
# 1. build a Pipeline(StandardScaler(), Lasso(max_iter=20000, tol=1e-3));
# 2. wrap it in a GridSearchCV over {"lasso__alpha": LASSO_ALPHAS},
#    scoring="neg_mean_squared_error", cv=KFold(n_splits=5, shuffle=True, random_state=0);
# 3. lasso_cv_model = ...  (fit that GridSearchCV on X_train, y_train ONLY)
# 4. lasso_cv_alpha = ...  (the fitted search's best alpha)
# 5. lasso_cv_pred = ...   (the fitted search's predictions on X_test)
# 6. lasso_cv_test_mse = ...
""",
            """
LASSO_ALPHAS = list(np.logspace(-3, 1, 25))

lasso_cv_pipe = Pipeline([("scaler", StandardScaler()), ("lasso", Lasso(max_iter=20000, tol=1e-3))])
lasso_cv_search_cv = KFold(n_splits=5, shuffle=True, random_state=0)
lasso_cv_model = GridSearchCV(
    lasso_cv_pipe, {"lasso__alpha": LASSO_ALPHAS}, scoring="neg_mean_squared_error", cv=lasso_cv_search_cv, n_jobs=-1
)
lasso_cv_model.fit(X_train, y_train)  # only the training partition
lasso_cv_alpha = lasso_cv_model.best_params_["lasso__alpha"]

lasso_cv_pred = lasso_cv_model.predict(X_test)  # the test set, read once
lasso_cv_test_mse = mean_squared_error(y_test, lasso_cv_pred)
print(f"selected alpha = {lasso_cv_alpha:.4g}")
print(f"held-out MSE = {lasso_cv_test_mse:.1f}")
""",
            "wp45-503-blank",
            tags=["wp45-activity-lasso-cv"],
        ),
        code(
            f"""
# Run this to check your tuned Lasso results.
EXPECTED_LASSO_CV_TEST_MSE = {EXPECTED_LASSO_CV_TEST_MSE}
LASSO_CV_TOLERANCE = 8.0  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("lasso_cv_alpha", "lasso_cv_pred", "lasso_cv_test_mse")):
    if len(lasso_cv_pred) != len(y_test):
        print(f"Not quite: lasso_cv_pred has {{len(lasso_cv_pred)}} values; it should have one prediction per test row ({{len(y_test)}}).")
    elif abs(lasso_cv_test_mse - EXPECTED_LASSO_CV_TEST_MSE) <= LASSO_CV_TOLERANCE:
        print(f"Looks good: selected alpha = {{lasso_cv_alpha:.4g}}, held-out MSE = {{lasso_cv_test_mse:.1f}} (expected ~{{EXPECTED_LASSO_CV_TEST_MSE:.1f}}).")
    else:
        print(
            f"Your held-out MSE ({{lasso_cv_test_mse:.1f}}) differs from the expected "
            f"result (~{{EXPECTED_LASSO_CV_TEST_MSE:.1f}}). That does not automatically "
            "mean something is wrong -- check that the search only ever saw X_train/y_train "
            "before assuming this is an error."
        )
else:
    print("Not complete yet: define lasso_cv_alpha, lasso_cv_pred, and lasso_cv_test_mse above first.")
""",
            "wp45-504-check",
        ),
        md(
            "The cell below extracts coefficients from your fitted tuned "
            "pipeline and reports how many are exactly zero.",
            "wp45-505-coef-intro",
        ),
        code(
            """
if "lasso_cv_model" in globals():
    tuned_coefs = lasso_cv_model.best_estimator_.named_steps["lasso"].coef_
    n_zero = int(np.sum(np.abs(tuned_coefs) <= 1e-10))
    n_nonzero = len(tuned_coefs) - n_zero
    print(f"{n_nonzero} of {len(FEATURES)} coefficients are nonzero (tolerance 1e-10); {n_zero} are exactly zero.")

    order = np.argsort(-np.abs(tuned_coefs))[:20]
    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    ax.barh(range(len(order)), tuned_coefs[order][::-1], color="#2a6f9e")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([FEATURES[i] for i in order][::-1], fontsize=7)
    ax.set_xlabel("coefficient (standardized features)")
    ax.set_title("20 largest-magnitude coefficients, tuned Lasso")
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: complete the Lasso cross-validation activity above first.")
""",
            "wp45-506-coef",
        ),
        code(
            """
show_question("q-alpha-tuning-leakage")
""",
            "wp45-507-checked",
        ),
    ]


def _section_6_conclusion() -> list[dict]:
    return [
        md("## 6. How Do We Choose a Feature-Selection Method?", "wp45-601-header"),
        md(
            """
Correlation-based ranking (Section 3) and Lasso (Sections 4-5) are two ways
to select features. Two more are common enough to know about:

| Method              | Main idea                                    | Main caution                                                |
| -------------------- | --------------------------------------------- | --------------------------------------------------------------- |
| Univariate filtering | Rank features one at a time                   | Ignores combinations among predictors                          |
| Sequential (stepwise) selection | Add or remove features one at a time, by cross-validated performance | Computationally expensive; retrains a model at every step |
| Ridge / Lasso        | Penalize coefficient size during fitting      | Ridge rarely reaches exactly zero; Lasso can, but only along one path |

There is no universally best method. The choice depends on the research
question, the number of predictors relative to the sample size, how
strongly predictors overlap, whether interpretation or prediction is the
main goal, and the computational budget. Features chosen using the target
must always be selected within the training data and evaluated on unseen
participants.
""",
            "wp45-602-table",
        ),
        md(
            """
## In summary

- Predefined feature selection can use anatomy or prior literature, decided
  independently of the current target data. Data-driven feature selection
  must use training data only; consulting test participants while selecting
  features is data leakage.
- Comparing several predefined feature sets on the same evaluation
  procedure is exploratory, useful for narrowing options -- not itself a
  final performance claim.
- A feature selector belongs inside cross-validation, refit on each
  training fold, exactly like `StandardScaler`. Selecting more features does
  not always improve validation performance.
- Ridge shrinks every coefficient toward zero without usually reaching
  exactly zero; Lasso can shrink coefficients to exactly zero, embedding
  feature selection inside the fit. Predictors must be standardized before
  that penalty is fair.
- Tuning alpha with cross-validation on the training set, then evaluating
  once on the test set, keeps tuning separate from the final performance
  estimate -- exactly as Exercise 4 established.

Next practice: decision trees.
""",
            "wp45-603-summary",
        ),
        code(
            """
show_question("q-ridge-lasso-properties")
""",
            "wp45-604-checked",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_data()
    cells += _section_2_predefined()
    cells += _section_2b_bridge()
    section_3 = _section_3_select()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_3]
    section_4 = _section_4_ridge_lasso()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_4]
    section_5 = _section_5_lasso_cv()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_5]
    cells += _section_6_conclusion()
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
