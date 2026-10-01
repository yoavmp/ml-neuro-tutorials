#!/usr/bin/env python3
"""Generate Exercise 7's JupyterLite template, portable copy, and reference.

WP46: migrate Exercise 7 ("Boosting and Gradient Boosting") to the same
JupyterLite-native, generator-authored architecture WP41/WP44/WP45/WP46
established for Exercises 1-6 (see WPs/reports/WP41_MAINTAINER_GUIDE.md),
following scripts/generate_exercise_06_notebook.py's exact shape.

Data: reuses the exact same same-origin export Exercises 2, 4, 5, and 6
already ship, book/lite/files/data/abide_age_brain.csv (360 fsCT predictors
+ age + group, 1004 participants). No second, independent data export is
created. As with Exercise 6 (see that generator's module docstring), the
legacy (pre-migration) canonical notebook loaded this cohort directly from
the pinned raw ABIDE-II TSV over the network; switching to the established
same-origin file changes the natural left-to-right column order fsCT_*
columns are encountered in. Sections that split the data a bounded number of
times at a shallow depth (the synthetic "Build a Boosted Model" activity,
which does not touch ABIDE data at all; the illustrative sklearn example;
the learning-rate/n_estimators sweep; the "Choosing When to Stop" curve; all
using max_depth<=2) reproduce the legacy audited numbers closely -- verified
directly against scripts/gradient_boosting_model_audit_result.json and
scripts/export_boosting_step_widget.py before writing a line here. The
deeper, order-sensitive computations (the 12-candidate cross-validated
pipeline search, and the max_depth=6 fair-comparison models in "Comparing
Tree-Based Models") select a genuinely different configuration on this data
source than the legacy audit: this notebook's own pipeline selects
(learning_rate=0.1, n_estimators=200, max_depth=2), not the legacy
(..., max_depth=3) -- a real, honestly-computed, and clearly explained
pre-migration difference, not an error. See the WP46 report for the full
before/after comparison; the numbers embedded below were verified directly
against the notebook's own data source, not copied from the legacy audit.

Numbers verified directly against book/lite/files/data/abide_age_brain.csv
before writing a single generator line:
  Section 1 data load: n_fit=564, n_val=189, n_train (development)=753,
    n_test=251 (locked) -- matches every other migrated exercise exactly.
  "Build a Boosted Model" (entirely synthetic, no ABIDE data; N=24, seed=7,
    formula/coefficients from book/config/abide_modeling.json's
    gradient_boosting.step_by_step): stage-0 training MSE and every later
    stage reproduce scripts/export_boosting_step_widget.py's own algorithm
    exactly, since this notebook replicates that algorithm verbatim.
  Section 3 sklearn illustration (n_estimators=100, learning_rate=0.05,
    max_depth=2, random_state=42): validation MSE=18.3254, R2=0.745349 --
    close to the legacy audit's 18.2258/0.746733 (this computation is not
    order-sensitive enough to diverge further at this shallow depth).
  Section 4 sweep (learning_rate=0.1, max_depth=2, N_TREES_VALUES=[10, 25,
    50, 100, 150, 200, 300]): validation MSE falls from 34.05 (10 trees) to
    a minimum of 18.73 (100-150 trees) and rises to 19.37 (300 trees) --
    the same underfit/best/slight-overfit shape the legacy audit reported
    (its own minimum: ~18.78 at 100-150 trees; 19.58 at 300 trees).
  Section 5 stop curve (learning_rate=0.1, max_depth=2, n_estimators=300,
    via staged_predict): training MSE falls to 0.81 by 300 trees while
    validation MSE bottoms out around 100-150 trees and rises to 19.37 by
    300 -- matches the legacy audit's own finding closely (0.81 train MSE
    at 300 trees is an exact match; validation shape is the same).
  Section 6 pipeline (12-candidate reduced grid: lr/n_estimators pairs
    [(0.03,50), (0.05,100), (0.1,100), (0.1,200)] x max_depth in [1,2,3],
    KFold(5, shuffle=True, random_state=13) on the 753-row development
    partition): selected (learning_rate=0.1, n_estimators=200,
    max_depth=2), mean CV MSE=27.4236; refit on all 753, evaluated once on
    the locked 251-row test set: test MSE=29.3842, R2=0.685223. Differs
    from the legacy audit's selected (..., max_depth=3), mean CV MSE=27.2085,
    test MSE=32.3679, R2=0.653261 -- the order-sensitivity difference
    documented above; both are genuine, honestly-computed selections from
    the same declared procedure, and this notebook's own number is the one
    embedded in its check cells.
  Section 7 comparison (fair_tree_settings=dict(max_depth=6,
    min_samples_leaf=5, random_state=42), fair_n_estimators=50,
    fair_max_features=19, on the same 753/251 split): single tree
    MSE=71.2880 R2=0.236332; Random Forest MSE=35.6616 R2=0.617978;
    gradient boosting reuses Section 6's own test_mse/test_r2
    (29.3842/0.685223) rather than a second locked-test read. Differs from
    the legacy audit's 70.13/0.249, 38.20/0.591, 32.37/0.653 for the same
    order-sensitivity reason; gradient boosting still has the lowest test
    MSE of the three, matching the legacy notebook's own finding.

Outputs:
  book/lite/files/exercise_07.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_07/exercise_07_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_07_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_07_reference.ipynb (--reference)

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

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_07.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_07" / "exercise_07_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_07_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_07_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 7, "templateVersion": TEMPLATE_VERSION},
}

SKLEARN_EXAMPLE_SETTINGS = dict(n_estimators=100, learning_rate=0.05, max_depth=2, random_state=42)

N_TREES_VALUES = [10, 25, 50, 100, 150, 200, 300]
SWEEP_LEARNING_RATE = 0.1
SWEEP_MAX_DEPTH = 2

STOP_LEARNING_RATE, STOP_MAX_DEPTH, STOP_N_ESTIMATORS = 0.1, 2, 300
STOP_N_TREES_GRID = [1, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300]

STEP_SEED = 7
STEP_N = 24
STEP_X_LOW, STEP_X_HIGH = 0.0, 10.0
STEP_C, STEP_A, STEP_FREQ, STEP_B, STEP_NOISE_SD = 5.0, 4.0, 0.9, 0.6, 1.2
STEP_LEARNING_RATES = [0.1, 0.3, 0.5, 1.0]
STEP_N_STAGES = 12

EXPLORER_LR_GRID = [0.01, 0.03, 0.05, 0.1, 0.2, 0.5]
EXPLORER_DEPTH_GRID = [1, 2, 3]
EXPLORER_N_TREES_GRID = [1, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300]
EXPLORER_DEFAULT_LR, EXPLORER_DEFAULT_DEPTH, EXPLORER_DEFAULT_N_TREES = 0.1, 2, 100

CV_PAIRS = [(0.03, 50), (0.05, 100), (0.1, 100), (0.1, 200)]
CV_DEPTH_GRID = [1, 2, 3]
CV_RANDOM_STATE = 13

FAIR_TREE_SETTINGS = dict(max_depth=6, min_samples_leaf=5, random_state=42)
FAIR_N_ESTIMATORS = 50
FAIR_MAX_FEATURES = 19

EXPECTED_SWEEP_MIN_VAL_MSE = 18.73
EXPECTED_CV_BEST_MEAN_MSE = 27.4236
EXPECTED_CV_TEST_MSE = 29.3842
EXPECTED_CV_TEST_R2 = 0.685223


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
    box-sizing: border-box;
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
# visible call like show_question("q-boosting-residuals") never prints or
# displays a correct_index/correct_indices value (WP48's "Multiple-choice
# answer visibility" requirement -- see
# scripts/generate_exercise_08_notebook.py for the pattern this mirrors).
# This is visual concealment, not secure assessment: the hidden cell is
# fully expandable, and a downloaded, fully offline, editable notebook must
# contain enough information to check an answer locally, so a technically
# curious student can always recover it from source or the running kernel.
_QUESTIONS = {
    "q-boosting-residuals": dict(
        kind="single",
        prompt="Does a new tree in gradient boosting predict the target directly, or the current residuals?",
        options=[
            "The current residuals -- the errors the ensemble still makes.",
            "The target directly, exactly like the first tree.",
            "The predictions of all previous trees combined.",
        ],
        correct_index=0,
        feedback_correct="Correct: every tree after the first is fit to what the ensemble still gets wrong, not to the original target.",
    ),
    "q-learning-rate-trees": dict(
        kind="single",
        prompt="Why does a smaller learning rate usually require more trees to reach the same fit?",
        options=[
            "Each tree's correction is scaled down more, so more corrections are needed to accumulate the same total change.",
            "A smaller learning rate makes each tree deeper.",
            "A smaller learning rate changes which features the trees can split on.",
        ],
        correct_index=0,
        feedback_correct="Correct: the learning rate only scales each stage's contribution; reaching a given fit with smaller steps takes more steps.",
    ),
    "q-boosting-vs-bagging": dict(
        kind="multi",
        prompt="Which of the following correctly distinguish boosting from bagging?",
        options=[
            "Boosting fits trees sequentially, each correcting the current ensemble's residuals; bagging fits trees independently on resampled data.",
            "Boosting combines trees with a weighted sum built up stage by stage; bagging combines trees by simple averaging.",
            "Boosting is guaranteed to always achieve lower test error than bagging.",
            "Both methods can overfit if allowed to add trees indefinitely, though the mechanism differs (boosting stages vs. tree count).",
        ],
        correct_indices={0, 1, 3},
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
    return code(source, "wp46-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp46-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 7: Boosting and Gradient Boosting", "wp46-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 7 of *Machine Learning for Neuroscience*. Exercise 6
compared a single tree with bagging and Random Forest, both of which train
their trees **independently** and average. This notebook asks what happens
if trees are instead trained **sequentially**, each one correcting the
errors left by the trees before it -- gradient boosting.

In this notebook you will:

1. distinguish boosting from bagging;
2. follow, step by step, how a boosted model corrects its own residuals;
3. explore how learning rate, number of trees, and tree depth interact;
4. select settings using development data and evaluate the locked test set
   exactly once; and
5. compare a single tree, Random Forest, and gradient boosting on identical
   held-out data.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

Gradient boosting is not guaranteed to outperform Random Forest on every
dataset -- this notebook reports what actually happens on this cohort, not a
universal ranking.

**Prerequisites:** Exercise 6's material on trees, bagging, and Random
Forest; comfort with `pandas`, `numpy`, and the scikit-learn `fit` /
`predict` pattern.
""",
            "wp46-002-overview",
        ),
    ]


def _section_1_setup() -> list[dict]:
    return [
        md("## 1. From Bagging to Boosting", "wp46-101-header"),
        md(
            """
| Method | How trees are trained | Combined prediction | Main idea |
| --- | --- | --- | --- |
| Single tree | One tree | One prediction | Simple model |
| Bagging | Independently on resampled data | Average | Reduce variance |
| Random Forest | Independently with row and feature randomness | Average | Decorrelate trees |
| Gradient boosting | Sequentially to correct current errors | Weighted sum | Improve the model step by step |

Boosting trees depend on the trees fit before them, are usually shallow, and
build a complex nonlinear model as a sequence -- which also creates an
overfitting risk if too many corrective trees are added.
""",
            "wp46-102-table",
        ),
        md(
            """
> **Think first:** Averaging independent trees (bagging, Random Forest)
> cannot correct an error every tree shares. Why not? What risk comes from
> adding corrective trees indefinitely?
""",
            "wp46-103-think-first",
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
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
X = df[FEATURES].to_numpy(float)
y = df["age"].to_numpy(float)
groups = df["group"].to_numpy()  # 1 = autism, 2 = control; stratification key only, never a predictor

X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=42, stratify=groups
)
X_fit, X_val, y_fit, y_val = train_test_split(
    X_train, y_train, test_size=0.25, random_state=7, stratify=groups_train
)
print(f"{len(FEATURES)} predictors")
print(f"n_fit = {len(y_fit)}   n_val = {len(y_val)}   n_train (development) = {len(y_train)}   n_test = {len(y_test)} (locked; read once, in Section 6)")
""",
            "wp46-104-load",
        ),
    ]


def _section_2_build_boosted_model() -> list[dict]:
    return [
        md("## 2. Building a Model One Tree at a Time", "wp46-201-header"),
        md(
            r"""
Gradient boosting starts from a simple prediction -- the training-target
mean -- and repeatedly fits a shallow tree to the current **residual**
(the error the model still makes), then adds a scaled-down version of that
tree's prediction to the running total:

$$\hat y_i^{(0)}=\bar y \qquad r_i^{(m)}=y_i-\hat y_i^{(m-1)} \qquad \hat y_i^{(m)}=\hat y_i^{(m-1)}+\eta\, f_m(x_i)$$

Here $f_m$ is the shallow tree fit to that stage's residuals, and $\eta$
(the **learning rate**) controls how much of each new tree's prediction is
added. For squared-error loss, the negative gradient at each point is
exactly the residual -- which is why this method is called *gradient*
boosting even though each step only ever fits an ordinary regression tree.
""",
            "wp46-202-math",
        ),
        md(
            """
### Interactive Activity 1: Build a Boosted Model

The activity below uses a small, **simulated** 24-observation, one-predictor
dataset (not ABIDE observations) so every stage's correction can be seen
directly. Step through the stages, compare learning rates, and toggle
between a stage's raw tree output and its learning-rate-scaled correction.
""",
            "wp46-203-activity-intro",
        ),
        code(
            f"""
# ---- "Build a Boosted Model" -- native interactive (ported from the old iframe) ----

STEP_SEED = {STEP_SEED}
STEP_N = {STEP_N}
_step_rng = np.random.RandomState(STEP_SEED)
_step_x = _step_rng.uniform({STEP_X_LOW}, {STEP_X_HIGH}, STEP_N)
_step_noise = _step_rng.normal(0.0, {STEP_NOISE_SD}, STEP_N)
_step_y = {STEP_C} + {STEP_A} * np.sin({STEP_FREQ} * _step_x) + {STEP_B} * _step_x + _step_noise
_step_order = np.argsort(_step_x)
_step_x, _step_y = _step_x[_step_order], _step_y[_step_order]

STEP_LEARNING_RATES = {STEP_LEARNING_RATES!r}
STEP_N_STAGES = {STEP_N_STAGES}


def _fit_stump(x_vals, residual):
    stump = DecisionTreeRegressor(max_depth=1, random_state=0)
    stump.fit(x_vals.reshape(-1, 1), residual)
    return stump, stump.predict(x_vals.reshape(-1, 1))


def _build_stages(eta):
    mean_y = float(np.mean(_step_y))
    ensemble = np.full(STEP_N, mean_y)
    stages = [{{"ensemble": ensemble.copy(), "residual": _step_y - ensemble, "train_mse": np.mean((_step_y - ensemble) ** 2), "stump": None, "tree_pred": None, "scaled": None}}]
    for _ in range(STEP_N_STAGES):
        residual_before = _step_y - ensemble
        stump, tree_pred = _fit_stump(_step_x, residual_before)
        scaled = eta * tree_pred
        ensemble = ensemble + scaled
        stages.append({{
            "ensemble": ensemble.copy(),
            "residual": residual_before,
            "train_mse": np.mean((_step_y - ensemble) ** 2),
            "stump": stump,
            "tree_pred": tree_pred,
            "scaled": scaled,
        }})
    return stages


_step_stages_by_rate = {{eta: _build_stages(eta) for eta in STEP_LEARNING_RATES}}

_step_lr_dd = widgets.Dropdown(options=[(f"{{eta}}", eta) for eta in STEP_LEARNING_RATES], value=0.3, description="Learning rate:")
_step_stage_slider = widgets.IntSlider(min=0, max=STEP_N_STAGES, value=0, description="Stage:")
_step_prev_btn = widgets.Button(description="Previous Step")
_step_next_btn = widgets.Button(description="Next Step")
_step_scaled_toggle = widgets.Checkbox(value=False, description="Show the newest tree's correction after scaling by the learning rate")
_step_output = widgets.Output()


def _step_render(_change=None):
    stages = _step_stages_by_rate[_step_lr_dd.value]
    stage = _step_stage_slider.value
    cur = stages[stage]
    with _step_output:
        _step_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.4))

        axes[0].scatter(_step_x, _step_y, s=24, label="observations")
        axes[0].plot(_step_x, cur["ensemble"], color="tab:orange", label=f"ensemble at stage {{stage}}")
        axes[0].set_title("Observations and ensemble prediction")
        axes[0].legend(fontsize=7)

        axes[1].scatter(_step_x, cur["residual"], s=24, color="0.4", label="residual before this update")
        if stage > 0:
            label = "newest tree (scaled by learning rate)" if _step_scaled_toggle.value else "newest tree (fitted to residuals)"
            shown = cur["scaled"] if _step_scaled_toggle.value else cur["tree_pred"]
            order = np.argsort(_step_x)
            axes[1].step(_step_x[order], shown[order], where="mid", color="tab:green", label=label)
        axes[1].set_title("Residuals and the newest shallow tree")
        axes[1].legend(fontsize=7)

        mse_by_stage = [s["train_mse"] for s in stages]
        axes[2].plot(range(len(mse_by_stage)), mse_by_stage, marker="o", markersize=3, color="0.5")
        axes[2].plot(stage, mse_by_stage[stage], marker="o", markersize=9, color="tab:red")
        axes[2].set_xlabel("stage")
        axes[2].set_ylabel("training MSE")
        axes[2].set_title("Training MSE by stage")
        plt.tight_layout()
        plt.show()

        if stage == 0:
            print(f"Stage 0: the model predicts the training-target mean for every observation. Training MSE = {{cur['train_mse']:.2f}}.")
        else:
            print(f"Stage {{stage}}: a new shallow tree was fitted to the residuals left by stage {{stage - 1}} and added, scaled by learning rate {{_step_lr_dd.value}}. Training MSE = {{cur['train_mse']:.2f}}.")

    _step_prev_btn.disabled = stage == 0
    _step_next_btn.disabled = stage == STEP_N_STAGES


def _step_on_prev(_btn):
    _step_stage_slider.value = max(0, _step_stage_slider.value - 1)


def _step_on_next(_btn):
    _step_stage_slider.value = min(STEP_N_STAGES, _step_stage_slider.value + 1)


_step_lr_dd.observe(_step_render, names="value")
_step_stage_slider.observe(_step_render, names="value")
_step_scaled_toggle.observe(_step_render, names="value")
_step_prev_btn.on_click(_step_on_prev)
_step_next_btn.on_click(_step_on_next)
display(widgets.VBox([
    widgets.HBox([_step_lr_dd, _step_prev_btn, _step_next_btn]),
    _step_stage_slider,
    _step_scaled_toggle,
    _step_output,
]))
_step_render()
""",
            "wp46-204-step-widget",
        ),
        code(
            """
show_question("q-boosting-residuals")
""",
            "wp46-205-checked",
        ),
    ]


def _section_3_sklearn_example() -> list[dict]:
    return [
        md("## 3. Gradient Boosting with Scikit-Learn", "wp46-301-header"),
        md(
            f"""
`GradientBoostingRegressor` implements the same idea directly on the
ABIDE brain-thickness features. This illustrative example uses fixed
settings (not tuned) on the fitting/validation split; it does **not**
require feature scaling, like every tree-based model so far.
""",
            "wp46-302-intro",
        ),
        code(
            f"""
gb_model = GradientBoostingRegressor(**{SKLEARN_EXAMPLE_SETTINGS!r})
gb_model.fit(X_fit, y_fit)
gb_pred = gb_model.predict(X_val)
gb_val_mse = mean_squared_error(y_val, gb_pred)
gb_val_r2 = r2_score(y_val, gb_pred)
print(f"validation MSE = {{gb_val_mse:.1f}}   validation R2 = {{gb_val_r2:.3f}}")
""",
            "wp46-303-example",
        ),
        md(
            """
| Parameter | Meaning | Effect of increasing it |
| --- | --- | --- |
| `n_estimators` | Number of sequential trees | More corrections, and greater overfitting risk |
| `learning_rate` | Contribution of each new tree | Faster, less cautious updates |
| `max_depth` | Complexity of each tree | More complex corrections |
| `subsample` | Fraction of training rows used per tree | Adds randomness below 1.0 |
""",
            "wp46-304-table",
        ),
    ]


def _section_4_rate_and_trees() -> list[dict]:
    return [
        md("## 4. Learning Rate and Number of Trees", "wp46-401-header"),
        md(
            """
Learning rate and number of trees trade off: a smaller learning rate makes
each correction more cautious, so more trees are usually needed to reach
the same fit. Tree depth also matters: deeper trees make more complex
corrections per stage.
""",
            "wp46-402-intro",
        ),
        md(
            f"""
Fixing `learning_rate = {SWEEP_LEARNING_RATE}` and `max_depth = {SWEEP_MAX_DEPTH}`,
train one `GradientBoostingRegressor` per entry of `N_TREES_VALUES` on
`X_fit`/`y_fit`, score each on `X_val`/`y_val`, and plot validation MSE
against `n_estimators`. Use `random_state=42` for every model, so the only
thing changing across models is `n_estimators`.

Required output names: `boosting_sweep_results` (a list of dicts, one per
entry of `N_TREES_VALUES`, each `{{"n_estimators": n, "val_mse": mse}}`) and
`boosting_sweep_fig` (the resulting Matplotlib figure).
""",
            "wp46-403-instructions",
        ),
        blank(
            f"""
N_TREES_VALUES = {N_TREES_VALUES!r}

# YOUR CODE HERE
# boosting_sweep_results = []
# for n in N_TREES_VALUES:
#     m = GradientBoostingRegressor(learning_rate={SWEEP_LEARNING_RATE}, max_depth={SWEEP_MAX_DEPTH}, n_estimators=n, random_state=42)
#     ...fit on X_fit/y_fit, predict X_val, record {{"n_estimators": n, "val_mse": ...}}...
#
# boosting_sweep_fig, ax = plt.subplots()
# ...plot val_mse against n_estimators from boosting_sweep_results...
# plt.show()
""",
            f"""
N_TREES_VALUES = {N_TREES_VALUES!r}

boosting_sweep_results = []
for n in N_TREES_VALUES:
    m = GradientBoostingRegressor(learning_rate={SWEEP_LEARNING_RATE}, max_depth={SWEEP_MAX_DEPTH}, n_estimators=n, random_state=42)
    m.fit(X_fit, y_fit)
    pred = m.predict(X_val)
    boosting_sweep_results.append({{"n_estimators": n, "val_mse": mean_squared_error(y_val, pred)}})

boosting_sweep_fig, ax = plt.subplots(figsize=(5.6, 3.6))
ax.plot([r["n_estimators"] for r in boosting_sweep_results], [r["val_mse"] for r in boosting_sweep_results], marker="o")
ax.set_xlabel("n_estimators")
ax.set_ylabel("validation MSE (years$^2$)")
ax.set_title(f"Validation MSE vs. number of trees (learning_rate={SWEEP_LEARNING_RATE})")
plt.tight_layout()
plt.show()
""",
            "wp46-404-blank",
            tags=["wp46-activity-sweep"],
        ),
        code(
            f"""
# Run this to check your sweep results.
EXPECTED_SWEEP_MIN_VAL_MSE = {EXPECTED_SWEEP_MIN_VAL_MSE}
SWEEP_MSE_TOLERANCE = 8.0  # generous: absorbs reasonable implementation differences

if "boosting_sweep_results" in globals():
    if len(boosting_sweep_results) != len(N_TREES_VALUES):
        print(f"Not quite: expected one result per entry of N_TREES_VALUES ({{len(N_TREES_VALUES)}} values).")
    elif any((not np.isfinite(r["val_mse"])) or r["val_mse"] < 0 for r in boosting_sweep_results):
        print("Not quite: every val_mse should be a finite, nonnegative number.")
    else:
        best = min(r["val_mse"] for r in boosting_sweep_results)
        if abs(best - EXPECTED_SWEEP_MIN_VAL_MSE) <= SWEEP_MSE_TOLERANCE:
            print(f"Looks good: minimum validation MSE across the sweep = {{best:.1f}} (expected ~{{EXPECTED_SWEEP_MIN_VAL_MSE:.1f}}).")
        else:
            print(
                f"Your minimum validation MSE ({{best:.1f}}) differs from the expected "
                f"result (~{{EXPECTED_SWEEP_MIN_VAL_MSE:.1f}}). That does not automatically "
                "mean something is wrong -- check that every model was fit on X_fit/y_fit and "
                "scored on X_val/y_val, with learning_rate/max_depth/random_state fixed, before "
                "assuming this is an error."
            )
else:
    print("Not complete yet: define boosting_sweep_results above first.")
""",
            "wp46-405-check",
        ),
        md(
            """
### Interactive Activity 2: Explore the Boosting Parameters

This activity uses only the fitting and validation subsets -- **the locked
outer test set is never part of this activity**. The whole
(learning rate x depth) grid below is precomputed once (using
`staged_predict` to get every tree-count step from one fit per pair, not a
fresh fit per tree count), so the controls only look up and redraw.
""",
            "wp46-406-activity2-intro",
        ),
        code(
            f"""
# ---- "Explore the Boosting Parameters" -- native interactive (ported from the old iframe) ----

_EXPLORER_LR_GRID = {EXPLORER_LR_GRID!r}
_EXPLORER_DEPTH_GRID = {EXPLORER_DEPTH_GRID!r}
_EXPLORER_N_TREES_GRID = {EXPLORER_N_TREES_GRID!r}
_explorer_cache = {{}}  # (lr, depth) -> {{"train_mse": [...], "val_mse": [...]}} aligned to _EXPLORER_N_TREES_GRID

for _lr in _EXPLORER_LR_GRID:
    for _depth in _EXPLORER_DEPTH_GRID:
        _m = GradientBoostingRegressor(
            learning_rate=_lr, max_depth=_depth, n_estimators=max(_EXPLORER_N_TREES_GRID), random_state=42
        ).fit(X_fit, y_fit)
        _train_staged = list(_m.staged_predict(X_fit))
        _val_staged = list(_m.staged_predict(X_val))
        _explorer_cache[(_lr, _depth)] = {{
            "train_mse": [mean_squared_error(y_fit, _train_staged[n - 1]) for n in _EXPLORER_N_TREES_GRID],
            "val_mse": [mean_squared_error(y_val, _val_staged[n - 1]) for n in _EXPLORER_N_TREES_GRID],
        }}

_explorer_lr_dd = widgets.Dropdown(options=_EXPLORER_LR_GRID, value={EXPLORER_DEFAULT_LR!r}, description="Learning rate:")
_explorer_depth_dd = widgets.Dropdown(options=_EXPLORER_DEPTH_GRID, value={EXPLORER_DEFAULT_DEPTH!r}, description="Tree depth:")
_explorer_ntrees_slider = widgets.SelectionSlider(options=_EXPLORER_N_TREES_GRID, value={EXPLORER_DEFAULT_N_TREES!r}, description="Number of trees:")
_explorer_output = widgets.Output()


def _explorer_render(_change=None):
    lr, depth, n = _explorer_lr_dd.value, _explorer_depth_dd.value, _explorer_ntrees_slider.value
    cached = _explorer_cache[(lr, depth)]
    n_idx = _EXPLORER_N_TREES_GRID.index(n)
    with _explorer_output:
        _explorer_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.8))

        axes[0].plot(_EXPLORER_N_TREES_GRID, cached["train_mse"], marker="o", label="training MSE")
        axes[0].plot(_EXPLORER_N_TREES_GRID, cached["val_mse"], marker="o", label="validation MSE")
        axes[0].axvline(n, color="0.5", linestyle="--")
        axes[0].set_xscale("log")
        axes[0].set_xlabel("number of trees")
        axes[0].set_ylabel("MSE (years$^2$)")
        axes[0].set_title(f"Training/validation MSE (learning_rate={{lr}}, depth={{depth}})")
        axes[0].legend(fontsize=7)

        heat = np.array([[_explorer_cache[(lr2, depth)]["val_mse"][i] for i in range(len(_EXPLORER_N_TREES_GRID))] for lr2 in _EXPLORER_LR_GRID])
        im = axes[1].imshow(heat, aspect="auto", cmap="viridis_r", origin="lower")
        axes[1].set_xticks(range(len(_EXPLORER_N_TREES_GRID)))
        axes[1].set_xticklabels(_EXPLORER_N_TREES_GRID, rotation=45, fontsize=7)
        axes[1].set_yticks(range(len(_EXPLORER_LR_GRID)))
        axes[1].set_yticklabels(_EXPLORER_LR_GRID, fontsize=7)
        axes[1].set_xlabel("number of trees")
        axes[1].set_ylabel("learning rate")
        axes[1].set_title(f"Validation MSE across learning rate x trees (depth={{depth}})")
        axes[1].scatter([n_idx], [_EXPLORER_LR_GRID.index(lr)], marker="s", facecolor="none", edgecolor="white", s=90)
        fig.colorbar(im, ax=axes[1], label="validation MSE")
        plt.tight_layout()
        plt.show()

        print(
            f"learning rate = {{lr}}   depth = {{depth}}   trees = {{n}}   "
            f"training MSE = {{cached['train_mse'][n_idx]:.1f}}   "
            f"validation MSE = {{cached['val_mse'][n_idx]:.1f}} (lower is better)"
        )


_explorer_lr_dd.observe(_explorer_render, names="value")
_explorer_depth_dd.observe(_explorer_render, names="value")
_explorer_ntrees_slider.observe(_explorer_render, names="value")
display(widgets.VBox([widgets.HBox([_explorer_lr_dd, _explorer_depth_dd]), _explorer_ntrees_slider, _explorer_output]))
_explorer_render()
""",
            "wp46-407-explorer-widget",
        ),
        code(
            """
show_question("q-learning-rate-trees")
""",
            "wp46-408-checked",
        ),
    ]


def _section_5_stopping() -> list[dict]:
    return [
        md("## 5. Choosing When to Stop", "wp46-501-header"),
        code(
            f"""
_stop_model = GradientBoostingRegressor(
    learning_rate={STOP_LEARNING_RATE}, max_depth={STOP_MAX_DEPTH}, n_estimators={STOP_N_ESTIMATORS}, random_state=42
).fit(X_fit, y_fit)
_stop_train_staged = list(_stop_model.staged_predict(X_fit))
_stop_val_staged = list(_stop_model.staged_predict(X_val))
STOP_N_TREES_GRID = {STOP_N_TREES_GRID!r}
stop_train_mse = [mean_squared_error(y_fit, _stop_train_staged[n - 1]) for n in STOP_N_TREES_GRID]
stop_val_mse = [mean_squared_error(y_val, _stop_val_staged[n - 1]) for n in STOP_N_TREES_GRID]
best_stop_i = int(np.argmin(stop_val_mse))

fig, ax = plt.subplots(figsize=(5.6, 3.6))
ax.plot(STOP_N_TREES_GRID, stop_train_mse, marker="o", label="training MSE")
ax.plot(STOP_N_TREES_GRID, stop_val_mse, marker="o", label="validation MSE")
ax.axvline(STOP_N_TREES_GRID[best_stop_i], color="0.5", linestyle="--", label="best validation point")
ax.set_xscale("log")
ax.set_xlabel("number of trees")
ax.set_ylabel("MSE (years$^2$)")
ax.set_title("Training and validation MSE vs. number of trees")
ax.legend(fontsize=8)
plt.tight_layout()
plt.show()
for n, tr, va in zip(STOP_N_TREES_GRID, stop_train_mse, stop_val_mse):
    print(f"n_trees={{n:>4}}   train MSE={{tr:6.2f}}   val MSE={{va:6.2f}}")
""",
            "wp46-502-stop-curve",
        ),
        md(
            """
Training MSE keeps falling as more trees are added. Validation MSE falls,
reaches a minimum, then rises again -- the same underfitting/overfitting
pattern Exercise 6 showed for tree depth, now playing out across the number
of boosting stages. This is also the basis for **early stopping**: halting
training once validation performance stops improving.

> **If 300 trees have lower training MSE but higher validation MSE than 120 trees, which model should be selected, and why?**
""",
            "wp46-503-note",
        ),
    ]


def _section_6_pipeline() -> list[dict]:
    pairs_literal = ", ".join(f"({lr}, {n})" for lr, n in CV_PAIRS)
    return [
        md("## 6. A Complete Gradient-Boosting Pipeline", "wp46-601-header"),
        md(
            """
A complete, leakage-safe model-selection pipeline:

1. preserve a locked test set;
2. perform cross-validation only within the training-and-validation
   (development) data;
3. compare a small parameter grid;
4. select a configuration by **mean cross-validation MSE**;
5. refit the selected configuration on all training-and-validation
   participants;
6. evaluate the locked test set **exactly once**.

A full grid over `learning_rate in [0.03, 0.05, 0.1]`, `n_estimators in [50,
100, 200]`, and `max_depth in [1, 2, 3]` has 27 candidates. Cross-validating
all 27 with 5 folds costs roughly ten times longer than most model runs in
these practice notebooks, so this notebook evaluates a smaller 12-candidate
grid instead: 4 representative `(learning_rate, n_estimators)` pairs, each
crossed with all 3 depths. It still spans shallow/deeper trees and
low/medium/high learning rates and tree counts. In your own work, define a
manageable search *before* you evaluate any candidates, rather than removing
settings after seeing their scores.
""",
            "wp46-602-intro",
        ),
        md(
            f"""
Complete the pipeline below using `GridSearchCV`. Build `param_grid` as a
*list* of parameter dicts -- one dict per `(learning_rate, n_estimators)`
pair, each offering all of `max_depth_grid` -- so `GridSearchCV` evaluates
exactly the 12 declared candidates, not a full 27-candidate cross product.
Use `KFold(n_splits=5, shuffle=True, random_state={CV_RANDOM_STATE})` on
`X_train`/`y_train` (training-and-validation data; the locked test set is
not involved yet). `GridSearchCV`'s default `refit=True` automatically refits
the best configuration on all of `X_train`/`y_train` once the search
finishes (steps 4-5 together) -- then predict `X_test` **once**.

Required output names: `boosting_search` (the fitted `GridSearchCV`),
`boosting_best_model` (`boosting_search.best_estimator_`),
`boosting_test_mse`, `boosting_test_r2`.
""",
            "wp46-603-instructions",
        ),
        blank(
            f"""
lr_n_estimators_pairs = [{pairs_literal}]
max_depth_grid = {CV_DEPTH_GRID!r}

# YOUR CODE HERE
# param_grid = [
#     {{"learning_rate": [lr], "n_estimators": [n], "max_depth": max_depth_grid}}
#     for lr, n in lr_n_estimators_pairs
# ]
# cv = KFold(n_splits=5, shuffle=True, random_state={CV_RANDOM_STATE})
# boosting_search = GridSearchCV(GradientBoostingRegressor(random_state=42), param_grid, scoring="neg_mean_squared_error", cv=cv)
# boosting_search.fit(X_train, y_train)  # development data only
# boosting_best_model = boosting_search.best_estimator_
# boosting_test_pred = ...  # boosting_best_model.predict(X_test) -- the locked test set, read once
# boosting_test_mse = ...
# boosting_test_r2 = ...
""",
            f"""
lr_n_estimators_pairs = [{pairs_literal}]
max_depth_grid = {CV_DEPTH_GRID!r}

param_grid = [
    {{"learning_rate": [lr], "n_estimators": [n], "max_depth": max_depth_grid}}
    for lr, n in lr_n_estimators_pairs
]
cv = KFold(n_splits=5, shuffle=True, random_state={CV_RANDOM_STATE})
boosting_search = GridSearchCV(
    GradientBoostingRegressor(random_state=42), param_grid, scoring="neg_mean_squared_error", cv=cv
)
boosting_search.fit(X_train, y_train)  # development data only
boosting_best_model = boosting_search.best_estimator_

boosting_test_pred = boosting_best_model.predict(X_test)  # the locked test set, read once
boosting_test_mse = mean_squared_error(y_test, boosting_test_pred)
boosting_test_r2 = r2_score(y_test, boosting_test_pred)
print(f"selected settings: {{boosting_search.best_params_}}   mean CV MSE = {{-boosting_search.best_score_:.1f}}")
print(f"locked-test MSE = {{boosting_test_mse:.1f}}   locked-test R2 = {{boosting_test_r2:.3f}} (evaluated once)")
""",
            "wp46-604-blank",
            tags=["wp46-activity-pipeline"],
        ),
        code(
            f"""
# Run this to check your pipeline results.
EXPECTED_CV_BEST_MEAN_MSE = {EXPECTED_CV_BEST_MEAN_MSE}
EXPECTED_TEST_MSE = {EXPECTED_CV_TEST_MSE}
PIPELINE_MSE_TOLERANCE = 8.0  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("boosting_search", "boosting_best_model", "boosting_test_mse", "boosting_test_r2")):
    n_candidates = len(boosting_search.cv_results_["params"])
    if n_candidates != 12:
        print(f"Not quite: expected 12 candidates (4 (learning_rate, n_estimators) pairs x 3 depths); found {{n_candidates}}.")
    elif not np.isfinite(boosting_test_mse) or boosting_test_mse < 0:
        print("Not quite: boosting_test_mse should be a finite, nonnegative number.")
    else:
        best_mean_mse = -boosting_search.best_score_
        if abs(boosting_test_mse - EXPECTED_TEST_MSE) <= PIPELINE_MSE_TOLERANCE:
            print(f"Looks good: selected {{boosting_search.best_params_}}, mean CV MSE = {{best_mean_mse:.1f}}, locked-test MSE = {{boosting_test_mse:.1f}} (expected ~{{EXPECTED_TEST_MSE:.1f}}).")
        else:
            print(
                f"Your locked-test MSE ({{boosting_test_mse:.1f}}) differs from the expected "
                f"result (~{{EXPECTED_TEST_MSE:.1f}}). That does not automatically mean something "
                "is wrong -- check that the search only ever saw X_train/y_train, and that X_test "
                "was predicted exactly once, before assuming this is an error."
            )
else:
    print("Not complete yet: define boosting_search, boosting_best_model, boosting_test_mse, and boosting_test_r2 above first.")
""",
            "wp46-605-check",
        ),
        md(
            "The cell below builds `boosting_cv_results` -- a tidy table of "
            "every candidate's mean and spread of cross-validation MSE -- "
            "from your fitted `boosting_search`.",
            "wp46-606-results-intro",
        ),
        code(
            """
if "boosting_search" in globals():
    boosting_cv_results = pd.DataFrame(boosting_search.cv_results_["params"])
    boosting_cv_results["mean_cv_mse"] = -boosting_search.cv_results_["mean_test_score"]
    boosting_cv_results["sd_cv_mse"] = boosting_search.cv_results_["std_test_score"]
    display(boosting_cv_results.sort_values(["max_depth", "learning_rate", "n_estimators"]).round(2))
else:
    print("Not complete yet: complete the pipeline activity above first.")
""",
            "wp46-607-results",
        ),
        md(
            """
The selected configuration is the one with the lowest mean cross-validation
MSE on training-and-validation data alone; the test set played no part in
choosing it. Grid size has a real computational cost in the browser --
evaluating even this reduced 12-candidate grid with 5-fold cross-validation
takes noticeably longer than a single model fit, which is exactly why this
notebook does not evaluate the full 27-candidate grid.
""",
            "wp46-608-note",
        ),
        md(
            f"""
### Two views of the same cross-validation results

Using your `boosting_cv_results` table, make two grouped bar charts of
**mean cross-validation MSE** (not test scores):

- **A)** grouped by `n_estimators` and `learning_rate`, holding
  `max_depth = 2` fixed (label this value on the plot);
- **B)** grouped by `n_estimators` and `max_depth`, holding
  `learning_rate = 0.1` fixed (label this value on the plot).

Label axes, the grouping/legend, the held-fixed value, and that lower is
better on both plots.

Required output names: `boosting_bar_fig_a`, `boosting_bar_fig_b`.
""",
            "wp46-609-bar-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# slice_a = boosting_cv_results[boosting_cv_results["max_depth"] == 2].sort_values(["learning_rate", "n_estimators"])
# boosting_bar_fig_a, ax = plt.subplots()
# ...one bar per row of slice_a, labeled by (learning_rate, n_estimators), y = mean_cv_mse...
# ...axis labels, "max_depth = 2 (fixed)" in the title, "lower is better" noted...
# plt.show()
#
# slice_b = boosting_cv_results[boosting_cv_results["learning_rate"] == 0.1].sort_values(["n_estimators", "max_depth"])
# boosting_bar_fig_b, ax = plt.subplots()
# ...one bar per row of slice_b, labeled by (n_estimators, max_depth), y = mean_cv_mse...
# ...axis labels, "learning_rate = 0.1 (fixed)" in the title, "lower is better" noted...
# plt.show()
""",
            """
slice_a = boosting_cv_results[boosting_cv_results["max_depth"] == 2].sort_values(["learning_rate", "n_estimators"])
labels_a = [f"lr={row.learning_rate}\\nn={row.n_estimators}" for row in slice_a.itertuples()]
boosting_bar_fig_a, ax = plt.subplots(figsize=(5.6, 3.6))
ax.bar(labels_a, slice_a["mean_cv_mse"], yerr=slice_a["sd_cv_mse"], capsize=4, color="#2a6f9e")
ax.set_ylabel("mean CV MSE (lower is better)")
ax.set_title("A) CV MSE by n_estimators and learning_rate (max_depth = 2, fixed)")
plt.tight_layout()
plt.show()

slice_b = boosting_cv_results[boosting_cv_results["learning_rate"] == 0.1].sort_values(["n_estimators", "max_depth"])
labels_b = [f"n={row.n_estimators}\\ndepth={row.max_depth}" for row in slice_b.itertuples()]
boosting_bar_fig_b, ax = plt.subplots(figsize=(5.6, 3.6))
ax.bar(labels_b, slice_b["mean_cv_mse"], yerr=slice_b["sd_cv_mse"], capsize=4, color="#b5622f")
ax.set_ylabel("mean CV MSE (lower is better)")
ax.set_title("B) CV MSE by n_estimators and max_depth (learning_rate = 0.1, fixed)")
plt.tight_layout()
plt.show()
""",
            "wp46-610-bar-blank",
            tags=["wp46-activity-bars"],
        ),
        code(
            """
# Run this to check your two grouped bar charts.
if all(name in globals() for name in ("boosting_bar_fig_a", "boosting_bar_fig_b")):
    slice_a_check = boosting_cv_results[boosting_cv_results["max_depth"] == 2]
    slice_b_check = boosting_cv_results[boosting_cv_results["learning_rate"] == 0.1]
    if len(slice_a_check) < 2 or len(slice_b_check) < 2:
        print("Not quite: each fixed slice should have at least 2 candidates to compare as grouped bars.")
    else:
        print(f"Looks good: plot A compares {len(slice_a_check)} candidates at max_depth=2; plot B compares {len(slice_b_check)} candidates at learning_rate=0.1, both from boosting_cv_results.")
else:
    print("Not complete yet: define boosting_bar_fig_a and boosting_bar_fig_b above first.")
""",
            "wp46-611-bar-check",
        ),
    ]


def _section_7_comparison() -> list[dict]:
    return [
        md("## 7. Comparing Tree-Based Models", "wp46-701-header"),
        md(
            f"""
A final, honest comparison across model families: the same fixed settings
Exercise 6 used for its single tree and Random Forest
(`fair_tree_settings = {FAIR_TREE_SETTINGS!r}`, `n_estimators={FAIR_N_ESTIMATORS}`,
`max_features={FAIR_MAX_FEATURES}`, not retuned here), fit on
`X_train`/`y_train` and evaluated on the locked `X_test`/`y_test`. Gradient
boosting's row reuses Section 6's own `boosting_test_mse`/`boosting_test_r2`
rather than reading the test set a second time.
""",
            "wp46-702-intro",
        ),
        code(
            f"""
fair_tree_settings = {FAIR_TREE_SETTINGS!r}
fair_n_estimators = {FAIR_N_ESTIMATORS}
fair_max_features = {FAIR_MAX_FEATURES}

_fair_single = DecisionTreeRegressor(**fair_tree_settings).fit(X_train, y_train)
_fair_forest = RandomForestRegressor(n_estimators=fair_n_estimators, max_features=fair_max_features, **fair_tree_settings).fit(X_train, y_train)
_fair_single_pred = _fair_single.predict(X_test)
_fair_forest_pred = _fair_forest.predict(X_test)

comparison_rows = [
    {{"model": "Single tree", "locked_test_mse": mean_squared_error(y_test, _fair_single_pred), "locked_test_r2": r2_score(y_test, _fair_single_pred)}},
    {{"model": "Random Forest", "locked_test_mse": mean_squared_error(y_test, _fair_forest_pred), "locked_test_r2": r2_score(y_test, _fair_forest_pred)}},
]
if "boosting_test_mse" in globals():
    comparison_rows.append({{"model": "Gradient boosting", "locked_test_mse": boosting_test_mse, "locked_test_r2": boosting_test_r2}})
    comparison_table = pd.DataFrame(comparison_rows).set_index("model")
    display(comparison_table.round(3))
else:
    print("Complete Section 6's pipeline activity first to add gradient boosting to this comparison.")
    display(pd.DataFrame(comparison_rows).set_index("model").round(3))
""",
            "wp46-703-comparison",
        ),
        md(
            """
On this split, gradient boosting achieves the lowest locked-test MSE of the
three -- a single, consistent held-out comparison, not proof that gradient
boosting universally wins.

<details>
<summary><b>Where does XGBoost fit?</b> (click to expand)</summary>

XGBoost is a widely used, more efficient and more heavily regularized
implementation of the same gradient-boosting idea -- additional
regularization terms, optimized tree construction, and engineering for
large datasets. Its interface mirrors scikit-learn's:

```python
from xgboost import XGBRegressor
model = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=3)
model.fit(X_train, y_train)
```

This notebook does not install, import, or execute `xgboost`.

</details>
""",
            "wp46-704-xgboost",
        ),
    ]


def _section_8_conclusion() -> list[dict]:
    return [
        md("## 8. What Should We Remember?", "wp46-801-header"),
        md(
            """
- Gradient boosting trains trees **sequentially**, each one correcting the
  residuals left by the ensemble so far, unlike bagging and Random Forest's
  independent trees.
- The learning rate scales each new tree's contribution; smaller learning
  rates need more trees to reach a comparable fit.
- More trees eventually overfit: training MSE keeps falling while
  validation MSE bottoms out and rises again, the same pattern as tree
  depth in Exercise 6.
- A complete pipeline selects settings using cross-validation on
  development data only, then evaluates the locked test set exactly once.
- Gradient boosting is not guaranteed to beat Random Forest; on this
  cohort's held-out split it had the lowest test MSE of the three models
  compared.

### Questions to take away

1. What is the key difference between how bagging/Random Forest and
   gradient boosting combine their trees?
2. Why does averaging independent trees fail to correct an error every
   tree shares, while boosting can?
3. Why does a smaller learning rate usually require more trees?
4. Why can training MSE keep improving even after validation MSE starts
   getting worse?
5. Why must the locked test set stay untouched until the very last step?
6. Is XGBoost a different modeling principle, or an engineering-focused
   extension of the same idea?
""",
            "wp46-802-summary",
        ),
        code(
            """
show_question("q-boosting-vs-bagging")
""",
            "wp46-803-checked",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_setup()
    cells += _section_2_build_boosted_model()
    cells += _section_3_sklearn_example()
    section_4 = _section_4_rate_and_trees()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_4]
    cells += _section_5_stopping()
    section_6 = _section_6_pipeline()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_6]
    cells += _section_7_comparison()
    cells += _section_8_conclusion()
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
