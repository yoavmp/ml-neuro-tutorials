#!/usr/bin/env python3
"""Generate Exercise 9's JupyterLite template, portable copy, and reference.

WP51: migrate Exercise 9 ("Advanced Models" -> rebuilt here as PCR, PLS,
SVM/SVR, and kernels beyond SVM) to the same JupyterLite-native,
generator-authored architecture WP41/WP44/WP45/WP46/WP47 established for
Exercises 1-8 (see WPs/reports/WP41_MAINTAINER_GUIDE.md and
WPs/reports/WP50_MAINTAINER_GUIDE.md), following
scripts/generate_exercise_08_notebook.py's exact shape (hidden setup cell,
show_question() answer-key hiding, Blank-tagged student tasks, native
ipywidgets activities instead of the old standalone-app iframes, generous
sanity-check tolerances).

**Local-only scope (WP51):** this generator's outputs are NOT wired into
book/_toc.yml, book/_config.yml's exclude_patterns, book/config/
exercise_manifest.json, or book/_static/launch-buttons.js -- Exercise 9
stays excluded from the published Sphinx build and the WP49/WP50 release
gate exactly as before (see exercise_manifest.json's own $comment and
tests/test_exercise_manifest.py::test_only_exercises_1_through_8_are_migrated,
which this WP leaves untouched and green). The legacy, iframe-embedded
book/chapters/chapter_09/exercise_09.ipynb (excluded from the Sphinx source
set since WP49) is also left untouched -- it is dead, unbuilt content, not
the product this WP replaces. Wiring this generator's outputs into the live
site is deliberately deferred to a later, explicitly authorized deployment
WP (see WPs/WP51_ACTIVE_EXERCISE_09_LOCAL.md's own boundary).

Content: unlike Exercise 8, this is a near-total rewrite of the lesson, not
a migration of the same material -- the old Exercise 9 taught PCR/PLS and
SVM/kernels almost entirely through prose, two embedded standalone-app
iframes, and an embedded *historical* five-model nested-cross-validation
summary (computed previously, outside this notebook). This version teaches
the same material through a single reproducible ABIDE-II train/validation
split (reused throughout, never recombined into a second "test" layer),
five required student tasks (PCR, PLS, SVR, Ridge, KernelRidge) plus one
optional RBFSampler/Lasso challenge, two native ipywidgets activities (a
PCR-vs-PLS explorer on a small synthetic 2-D dataset, and an SVM
decision-boundary explorer on a small synthetic 2-D classification
dataset), and six checked conceptual questions. The old embedded nested-CV
summary is demoted to one clearly labeled, collapsed, non-graded
``<details>`` historical reference (its own dataset/split/procedure named
explicitly) -- its numbers are never copied into this notebook's own
conclusions, and nested cross-validation itself is not re-taught or re-run
here (Exercise 4's job).

Data: reuses the exact same same-origin export Exercises 2, 4, 5, 6, 7, and
8 already ship, book/lite/files/data/abide_age_brain.csv (360 fsCT_
cortical-thickness predictors + age + group, 1004 participants). No new
data asset is exported for this WP. The two interactive activities and the
RBFSampler-logistic-regression illustration use small, fixed-seed synthetic
data instead -- never ABIDE -- per the WP51 spec ("a small, separate
synthetic classification example is appropriate for the SVC boundary
visualization").

Numbers verified directly against book/lite/files/data/abide_age_brain.csv
(single split: train_test_split(..., test_size=0.25, random_state=42,
stratify=group), identical to every other exercise's own split convention)
before writing a single generator line -- see the WP51 report for the full
reasoning and every verification command. Headline results, this split:
  PCR (StandardScaler -> PCA -> LinearRegression), n_components in
    [2, 5, 10, 20, 50]: validation MSE = 51.138 / 44.488 / 34.808 / 31.943 /
    29.610 -- monotonically improving across this grid.
  PLS (StandardScaler -> PLSRegression(scale=False)), same grid:
    validation MSE = 39.935 / 29.658 / 38.797 / 48.906 / 49.555 -- best at
    n_components=5, then *worse* with more components (overfits the
    train/validation split actually used here). PLS's 5-component best
    (29.658) is close to, but not quite as good as, PCR's 50-component best
    (29.610) -- a genuine near-tie at very different component counts, not
    a universal ranking.
  SVR, on a fixed random 300-row subset of the 753-row training partition
    (SUBSET_SEED=0; kept small so RBF/linear SVR stay responsive in
    Pyodide -- see the module's own note on this below): linear C=1/C=10
    validation MSE = 94.996 / 99.755 (R2 negative at this subset size and
    kernel); RBF C=1/C=10/C=100 (gamma="scale") validation MSE = 60.886 /
    33.834 / 29.535 -- RBF clearly beats linear here, and higher C helps
    monotonically across this grid, on this particular subset.
  Ridge(alpha=100) on the full 753-row training partition: validation
    MSE=31.813, R2=+0.659. KernelRidge(kernel="rbf", alpha=0.1,
    gamma=0.001), same rows: validation MSE=21.924, R2=+0.765 -- the exact
    kernel trick clearly outperforms plain Ridge here.
  Optional challenge: plain Lasso(alpha=0.1) on the full 360 standardized
    features: 163/360 nonzero coefficients, validation MSE=29.877.
    RBFSampler(gamma=0.001, n_components=200, random_state=0) + the same
    Lasso(alpha=0.1): 15/200 nonzero coefficients (now on transformed
    features, never the original 360 brain regions), validation MSE=58.515
    -- a real, honestly-reported result, including that it is *worse* here
    than plain Lasso; the point of this optional cell is where sparsity now
    applies, not a performance claim.
  Synthetic SVC dataset (make_svc_dataset(), seed=33, n=140, 98 train / 42
    val): "linear" (two separated blobs) kernel=linear C=1: train
    acc=0.939, val acc=0.976, 23 support vectors. "nonlinear" (inner blob +
    outer ring) kernel=linear C=1: train acc=0.541, val acc=0.548, 98 (i.e.
    every training point is a) support vector -- a clean illustration of a
    linear boundary failing on a non-linearly-separable problem. Same
    "nonlinear" data, kernel=rbf C=1 gamma="scale" (this notebook's own
    compact demo and the activity's own default): train acc=0.949, val
    acc=0.952, 35 support vectors; C=10 reaches val acc=1.000 (linear/C=10)
    or 0.976 (rbf/C=10) on the "linear" set -- RBF/higher C help on this
    particular small dataset, not as a universal rule.
  RBFSampler + LogisticRegression, same "nonlinear" synthetic data,
    gamma=0.5 (sklearn's own gamma="scale" default for 2 standardized
    features, 1/(2*1)=0.5, kept explicit here since RBFSampler has no
    "scale" shortcut), n_components=50: plain LogisticRegression validation
    accuracy=0.476 (worse than chance on this split); after the RBFSampler
    feature map, validation accuracy=0.952 -- the same gap SVC's own
    linear-vs-RBF comparison shows, through a different (approximate,
    explicit-feature-map) mechanism.

A real runtime-budget decision, stated here rather than left implicit:
SVR(kernel="linear") on this table's full 753x360 training partition took
4-93 seconds locally per fit (worse for larger C, where more iterations are
needed) -- unacceptably slow for a browser-native Pyodide kernel with no
GPU and a single thread. Fitting on a fixed, documented 300-row random
subset instead (SVR_SUBSET_N=300, SVR_SUBSET_SEED=0) keeps every fit under
roughly 0.2s locally, and every number this notebook reports for SVR is
explicitly labeled as this subset's own result -- never implied to equal
what the full 753-row partition would have scored.

Outputs:
  book/lite/files/exercise_09.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_09/exercise_09_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_09_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_09_reference.ipynb (--reference)

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
SVR_BENCHMARK_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_svr_benchmark.json"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_09" / "exercise_09_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 9, "templateVersion": TEMPLATE_VERSION},
}

SPLIT_TEST_SIZE = 0.25
SPLIT_RANDOM_STATE = 42

PCR_PLS_COMPONENT_GRID = [2, 5, 10, 20, 50]
EXPECTED_PCR_MSE = {2: 51.138, 5: 44.488, 10: 34.808, 20: 31.943, 50: 29.610}
EXPECTED_PCR_R2 = {2: 0.452, 5: 0.523, 10: 0.627, 20: 0.658, 50: 0.683}
EXPECTED_PLS_MSE = {2: 39.935, 5: 29.658, 10: 38.797, 20: 48.906, 50: 49.555}
EXPECTED_PLS_R2 = {2: 0.572, 5: 0.682, 10: 0.584, 20: 0.476, 50: 0.469}
MSE_TOLERANCE = 6.0  # generous: absorbs reasonable implementation differences

SVR_SUBSET_N = 300
SVR_SUBSET_SEED = 0
SVR_PARAM_SETS = [
    {"kernel": "linear", "C": 1, "gamma": None, "epsilon": 1},
    {"kernel": "linear", "C": 10, "gamma": None, "epsilon": 1},
    {"kernel": "rbf", "C": 1, "gamma": "scale", "epsilon": 1},
    {"kernel": "rbf", "C": 10, "gamma": "scale", "epsilon": 1},
    {"kernel": "rbf", "C": 100, "gamma": "scale", "epsilon": 1},
]
EXPECTED_SVR_BEST_KERNEL = "rbf"
EXPECTED_SVR_BEST_C = 100
EXPECTED_SVR_BEST_MSE = 29.535

RIDGE_ALPHA = 100
EXPECTED_RIDGE_MSE = 31.813
KERNEL_RIDGE_ALPHA = 0.1
KERNEL_RIDGE_GAMMA = 0.001
EXPECTED_KERNEL_RIDGE_MSE = 21.924

SVC_DATASET_SEED = 33
SVC_DATASET_N = 140
SVC_DATASET_TRAIN_FRACTION = 0.7


def _svr_benchmark() -> dict:
    return json.loads(SVR_BENCHMARK_PATH.read_text())


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


# Duplicates (never imports) generate_exercise_08_notebook.py's setup-cell
# pattern -- each generator module is a self-contained, independently
# regenerable source of truth (WP41 maintainer guide section 4.7). The
# question-checking helpers carry question CONTENT in this hidden cell's own
# _QUESTIONS dict, behind a show_question(id) wrapper (WP47's "Multiple-
# choice answer visibility" convention) -- a readability improvement, not
# real answer-key secrecy: this is still a fully downloadable, offline,
# editable notebook (see the closing summary's own note).
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
    and group (autism/control, used only to stratify the train/validation
    split -- never a model feature).

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


# ipywidgets' own stylesheet gives a Dropdown's description label a fixed,
# fairly narrow width with no wrapping -- confirmed live (a real JupyterLite
# browser, desktop and 390px) to truncate/overlap a label like "Weight on
# PC1:" against its own control. style={"description_width": "initial"}
# (set per-widget below, where each control is built) is the primary fix;
# this CSS is the layout backstop that lets a row of controls wrap onto
# multiple lines at narrow widths instead of overflowing the page.
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
    fully correct, fully wrong, or partial selection, without
    revealing which specific statements were right or wrong."""
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
# reproducible across runs/reruns of the same cell (nothing here depends on
# wall-clock time or call order), but different across questions, so correct
# answers no longer land on the same position every time.
_QUESTIONS = {
    "q-pcr-vs-pls": dict(
        type="single",
        shuffle_seed=1,
        prompt=(
            "Both PCR and PLS build a small number of components from many "
            "correlated predictors. What is the key difference in how their "
            "components are built, and when might that matter?"
        ),
        options=[
            "PCR's components are chosen using X alone; PLS's components use the relationship between X and y, so PLS can prioritize a lower-variance direction that still predicts well, while PCR might discard it.",
            "There is no real difference -- both choose components identically, so one will always score at least as well as the other on any dataset.",
            "PLS also ignores y, but simply retains more components than PCR by default, which is why it sometimes scores differently.",
        ],
        correct_index=0,
        feedback_correct="Correct: PCR's components summarize variance in X only; PLS's components are built using X and y together, so PLS can keep a direction PCR would discard.",
    ),
    "q-leakage": dict(
        type="single",
        shuffle_seed=6,
        prompt=(
            "Why must StandardScaler and PCA (or PLSRegression) be fit only on "
            "X_train, never on the full X before the train/validation split?"
        ),
        options=[
            "Fitting them on the full dataset lets information from the validation rows leak into preprocessing, making the validation score optimistic -- even though PCA/PLS never look at the validation target directly.",
            "It doesn't actually matter, as long as the final model is only scored on X_val once.",
            "Fitting on the full dataset is required for PCA to work correctly; fitting on X_train alone would produce invalid components.",
        ],
        correct_index=0,
        feedback_correct="Correct: fitting preprocessing on rows the model will later be validated on leaks information into that preprocessing step, even when the step never looks at the target.",
    ),
    "q-c-gamma-epsilon": dict(
        type="multi",
        shuffle_seed=15,
        prompt="Which of the following statements about SVM/SVR parameters are true?",
        statements=[
            "Larger C pushes the model to fit training points more closely, tolerating fewer margin/error violations.",
            "For an RBF kernel, larger gamma makes the decision boundary more local and flexible.",
            "In SVR, a larger epsilon widens the band of regression error that receives no penalty at all.",
            "C mainly controls how many support vectors are allowed, independent of the margin width.",
            "For an RBF kernel, larger gamma always produces a smoother, less flexible boundary.",
            "epsilon is a classification-only parameter, used by SVC rather than SVR.",
        ],
        correct_indices={0, 1, 2},
        feedback_correct="Correct: larger C tightens the fit, larger RBF gamma makes the boundary more local/flexible, and larger epsilon widens SVR's no-penalty error band. The other three statements each get one of those backwards or apply it to the wrong parameter/model.",
    ),
    "q-train-vs-val": dict(
        type="single",
        shuffle_seed=10,
        prompt=(
            "In the SVM boundary activity, one setting reaches very high "
            "training accuracy but lower validation accuracy than a less "
            "flexible setting. What does this show?"
        ),
        options=[
            "A boundary that fits the training data extremely closely is not guaranteed to generalize -- training accuracy alone cannot establish that a model is better.",
            "The validation set must be mislabeled, since a model with higher training accuracy should always validate at least as well.",
            "This can only happen with the RBF kernel; a linear kernel can never show this pattern.",
        ],
        correct_index=0,
        feedback_correct="Correct: training accuracy reflects fit to the training rows only; a more flexible boundary can fit training noise at validation's expense.",
    ),
    "q-exact-vs-approx": dict(
        type="single",
        shuffle_seed=4,
        prompt=(
            "What is the relationship between ordinary Ridge regression and "
            "KernelRidge(kernel='rbf')?"
        ),
        options=[
            "KernelRidge(kernel='rbf') is the exact RBF-kernel counterpart of L2-regularized (Ridge) regression -- the same underlying regularized least-squares problem, solved with a different (kernel) parameterization.",
            "They are unrelated models that happen to share scikit-learn's Pipeline interface.",
            "KernelRidge(kernel='rbf') always produces identical predictions to Ridge, regardless of which alpha or gamma is chosen.",
        ],
        correct_index=0,
        feedback_correct="Correct: KernelRidge(kernel='rbf') solves the same L2-regularized regression problem as Ridge, exactly, in a kernel parameterization -- not an approximation, and not guaranteed to match Ridge's predictions unless alpha/gamma happen to be chosen equivalently.",
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
    return code(source, "wp51-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp51-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 9: Advanced Models", "wp51-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 9 of *Machine Learning for Neuroscience*. Every method
here answers the same question differently: how do we build a useful model
when we have many correlated predictors, or when the true relationship
might not be a straight line?

In this notebook you will:

1. compare principal component regression (PCR) and partial least squares
   (PLS) on the same ABIDE-II age-prediction task;
2. explore how a support vector machine's boundary depends on its kernel,
   `C`, and `gamma`, then build SVR pipelines for the same age-prediction
   task;
3. see where the "kernel trick" generalizes exactly beyond SVMs --
   `KernelRidge` solves the same regularized regression problem as `Ridge`,
   in a different (kernel) parameterization;
4. compare every method's validation performance, on the same participants
   and the same full feature set, in one table, and reflect on why a single
   split can never crown a universal winner.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 2 (regression), Exercise 4 (validation and
leakage), and Exercise 8 (PCA).
""",
            "wp51-002-overview",
        ),
    ]


def _section_1_load_and_split() -> list[dict]:
    return [
        md("## 1. Load the ABIDE-II Data and Make One Split", "wp51-101-header"),
        md(
            """
Every method compared in this notebook -- PCR, PLS, SVR, Ridge, and
KernelRidge -- is trained and validated on **exactly the same rows**: one
train/validation split of the familiar 1,004-participant, 360-predictor
ABIDE-II age-prediction table. Reusing the same rows throughout is what
makes the final comparison in Section 6 meaningful: every method's
validation score is a number about the same held-out participants, not an
artifact of a different, friendlier split.
""",
            "wp51-102-intro",
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

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=%(test_size)r, random_state=%(random_state)r, stratify=group
)
print(f"data table: {df.shape[0]} participants x {len(FEATURES)} cortical-thickness predictors")
print(f"X_train: {X_train.shape}   X_val: {X_val.shape}")
"""
            % {"test_size": SPLIT_TEST_SIZE, "random_state": SPLIT_RANDOM_STATE},
            "wp51-103-load-split",
        ),
    ]


def _section_2_pcr() -> list[dict]:
    grid_literal = repr(PCR_PLS_COMPONENT_GRID)
    expected_literal = repr(EXPECTED_PCR_MSE)
    return [
        md("## 2. Principal Component Regression (PCR)", "wp51-201-header"),
        md(
            """
**Principal component regression (PCR)** is ordinary linear regression
fit on principal-component scores instead of the original features:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA(n_components=...)),
    ("model", LinearRegression()),
])
```

PCA sees `X` but never `y`: it keeps the directions that explain the most
variance in the 360 cortical-thickness predictors, chosen with no idea
which direction (if any) relates to age. `StandardScaler` and `PCA` must
both be refit inside whatever data the model is trained on -- fitting them
on rows the model is later validated against leaks information, even though
neither step looks at the target.
""",
            "wp51-202-intro",
        ),
        md(
            f"""
### Your task: validation MSE across a few component counts

For each `n_components` in `{grid_literal}`, build the PCR pipeline above,
fit it on `X_train`/`y_train`, and record its **validation MSE** (ordinary,
positive mean squared error -- `mean_squared_error(y_val, pred)`, not a
negated scikit-learn scoring convention) and **validation R2**
(`r2_score(y_val, pred)`).

Required output name: `pcr_results` -- a list of dicts, one per entry of
the grid above, each shaped `{{"n_components": n, "val_mse": ..., "val_r2": ...}}`.
""",
            "wp51-203-instructions",
        ),
        blank(
            f"""
PCR_COMPONENT_GRID = {grid_literal}
pcr_results = []

# YOUR CODE HERE
# Hint: reuse the pipeline shape shown above, once per entry of
# PCR_COMPONENT_GRID, scored with the two metrics named above. PCA keeps
# random_state=0 so results are reproducible.
# Example shape only (not a real result):
# pcr_results.append({{"n_components": 2, "val_mse": 0.0, "val_r2": 0.0}})
""",
            f"""
PCR_COMPONENT_GRID = {grid_literal}
pcr_results = []

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

for n in PCR_COMPONENT_GRID:
    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("pca", PCA(n_components=n, random_state=0)),
        ("model", LinearRegression()),
    ])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_val)
    pcr_results.append({{"n_components": n, "val_mse": float(mean_squared_error(y_val, pred)), "val_r2": float(r2_score(y_val, pred))}})
print(pd.DataFrame(pcr_results))
""",
            "wp51-204-pcr-blank",
            tags=["wp51-activity-pcr"],
        ),
        code(
            f"""
# Run this to check your PCR results.
EXPECTED_PCR_MSE = {expected_literal}
EXPECTED_PCR_R2 = {repr(EXPECTED_PCR_R2)}
MSE_TOLERANCE = {MSE_TOLERANCE!r}
R2_TOLERANCE = 0.15

if "pcr_results" in globals() and pcr_results:
    by_n = {{r["n_components"]: r["val_mse"] for r in pcr_results}}
    r2_by_n = {{r["n_components"]: r.get("val_r2") for r in pcr_results}}
    if set(by_n) != set(PCR_COMPONENT_GRID):
        print(f"Not quite: expected one result per entry of PCR_COMPONENT_GRID ({{PCR_COMPONENT_GRID}}).")
    elif any(v is None for v in r2_by_n.values()):
        print("Not quite: each entry of pcr_results also needs a val_r2 key.")
    else:
        diffs = {{n: abs(by_n[n] - EXPECTED_PCR_MSE[n]) for n in by_n}}
        r2_diffs = {{n: abs(r2_by_n[n] - EXPECTED_PCR_R2[n]) for n in by_n}}
        if all(d <= MSE_TOLERANCE for d in diffs.values()) and all(d <= R2_TOLERANCE for d in r2_diffs.values()):
            print("Looks good: your PCR validation MSE/R2 match the expected values within tolerance.")
            for n in sorted(by_n):
                print(f"  n_components={{n:3d}}: val_mse={{by_n[n]:.2f}} (expected ~{{EXPECTED_PCR_MSE[n]:.1f}})  val_r2={{r2_by_n[n]:.2f}} (expected ~{{EXPECTED_PCR_R2[n]:.2f}})")
        else:
            print(
                "Some of your PCR validation MSE values differ from the expected numbers by more "
                "than a generous tolerance. That does not automatically mean something is wrong -- "
                "check that the pipeline is StandardScaler -> PCA(random_state=0) -> LinearRegression, "
                "fit on X_train/y_train only, before assuming this is an error."
            )
else:
    print("Not complete yet: define pcr_results above first.")
""",
            "wp51-205-pcr-check",
        ),
        md(
            """
### Plot validation MSE versus component count

Supplied: a ready-to-run plot of `pcr_results`, handled gracefully if it is
not complete yet.
""",
            "wp51-206-plot-intro",
        ),
        code(
            """
if "pcr_results" in globals() and len(pcr_results) == len(PCR_COMPONENT_GRID):
    pcr_df = pd.DataFrame(pcr_results).sort_values("n_components")
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(pcr_df["n_components"], pcr_df["val_mse"], marker="o")
    ax.set_xlabel("Number of retained components")
    ax.set_ylabel("Validation MSE")
    ax.set_title("PCR: validation MSE vs. component count")
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: finish the PCR task above first (pcr_results is missing or incomplete).")
""",
            "wp51-207-plot",
        ),
        code(
            """
show_question("q-leakage")
""",
            "wp51-208-q-leakage",
        ),
    ]


def _section_3_pls() -> list[dict]:
    grid_literal = repr(PCR_PLS_COMPONENT_GRID)
    expected_literal = repr(EXPECTED_PLS_MSE)
    return [
        md("## 3. Partial Least Squares (PLS)", "wp51-301-header"),
        md(
            """
PCR's components summarize variance in `X` alone. **PLS** builds its
components differently: using the relationship between `X` and `y`. As a
result, PLS can keep a direction that explains comparatively little
variance in `X` but relates strongly to `y` -- exactly the kind of
direction PCR risks discarding. Because PLS's components are built using
the target, the *entire* PLS fit (not just a final linear step) must happen
on training data only, never before a train/validation split.

```python
Pipeline([
    ("scale", StandardScaler()),
    # scale=False: the outer StandardScaler already standardized the
    # predictors, so PLSRegression's own internal scaling is turned off
    # here to avoid silently scaling twice.
    ("model", PLSRegression(n_components=..., scale=False)),
])
```

| | PCR | PLS |
|---|---|---|
| Components built from | `X` only | `X` and `y` together |
| Can discard a low-variance, high-signal direction? | Yes | Less likely |
| Risk of overfitting with many components | Lower (ignores `y`) | Higher (uses `y`) |
""",
            "wp51-302-intro",
        ),
        md(
            f"""
### Your task: repeat the comparison for PLS

Same grid, same rows, same required-output shape as Section 2: for each
`n_components` in `{grid_literal}`, fit the PLS pipeline above on
`X_train`/`y_train` and record its validation MSE and validation R2.

Required output name: `pls_results` -- same shape as `pcr_results`
(`{{"n_components": n, "val_mse": ..., "val_r2": ...}}` per grid entry).
""",
            "wp51-303-instructions",
        ),
        blank(
            f"""
PLS_COMPONENT_GRID = {grid_literal}
pls_results = []

# YOUR CODE HERE -- this closely mirrors the PCR task above; the pipeline's
# second step and PLSRegression's own scale=False are the only real change.
# Hint: from sklearn.cross_decomposition import PLSRegression
# PLSRegression's predict() returns a column vector -- call .ravel() on it
# before scoring.
# Example shape only (not a real result):
# pls_results.append({{"n_components": 2, "val_mse": 0.0, "val_r2": 0.0}})
""",
            f"""
PLS_COMPONENT_GRID = {grid_literal}
pls_results = []

from sklearn.cross_decomposition import PLSRegression

for n in PLS_COMPONENT_GRID:
    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("model", PLSRegression(n_components=n, scale=False)),
    ])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_val).ravel()
    pls_results.append({{"n_components": n, "val_mse": float(mean_squared_error(y_val, pred)), "val_r2": float(r2_score(y_val, pred))}})
print(pd.DataFrame(pls_results))
""",
            "wp51-304-pls-blank",
            tags=["wp51-activity-pls"],
        ),
        code(
            f"""
# Run this to check your PLS results.
EXPECTED_PLS_MSE = {expected_literal}
EXPECTED_PLS_R2 = {repr(EXPECTED_PLS_R2)}
MSE_TOLERANCE = {MSE_TOLERANCE!r}
R2_TOLERANCE = 0.15

if "pls_results" in globals() and pls_results:
    by_n = {{r["n_components"]: r["val_mse"] for r in pls_results}}
    r2_by_n = {{r["n_components"]: r.get("val_r2") for r in pls_results}}
    if set(by_n) != set(PLS_COMPONENT_GRID):
        print(f"Not quite: expected one result per entry of PLS_COMPONENT_GRID ({{PLS_COMPONENT_GRID}}).")
    elif any(v is None for v in r2_by_n.values()):
        print("Not quite: each entry of pls_results also needs a val_r2 key.")
    else:
        diffs = {{n: abs(by_n[n] - EXPECTED_PLS_MSE[n]) for n in by_n}}
        r2_diffs = {{n: abs(r2_by_n[n] - EXPECTED_PLS_R2[n]) for n in by_n}}
        if all(d <= MSE_TOLERANCE for d in diffs.values()) and all(d <= R2_TOLERANCE for d in r2_diffs.values()):
            print("Looks good: your PLS validation MSE/R2 match the expected values within tolerance.")
            for n in sorted(by_n):
                print(f"  n_components={{n:3d}}: val_mse={{by_n[n]:.2f}} (expected ~{{EXPECTED_PLS_MSE[n]:.1f}})  val_r2={{r2_by_n[n]:.2f}} (expected ~{{EXPECTED_PLS_R2[n]:.2f}})")
        else:
            print(
                "Some of your PLS validation MSE values differ from the expected numbers by more "
                "than a generous tolerance. That does not automatically mean something is wrong -- "
                "check that PLSRegression uses scale=False after an outer StandardScaler, fit on "
                "X_train/y_train only, before assuming this is an error."
            )
else:
    print("Not complete yet: define pls_results above first.")
""",
            "wp51-305-pls-check",
        ),
        md(
            """
### Plot both methods on the same axes

Supplied: PCR and PLS validation MSE, plotted together, handled gracefully
if either is not complete yet.
""",
            "wp51-306-plot-intro",
        ),
        code(
            """
have_pcr = "pcr_results" in globals() and len(pcr_results) == len(PCR_COMPONENT_GRID)
have_pls = "pls_results" in globals() and len(pls_results) == len(PLS_COMPONENT_GRID)

if have_pcr or have_pls:
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    if have_pcr:
        pcr_df = pd.DataFrame(pcr_results).sort_values("n_components")
        ax.plot(pcr_df["n_components"], pcr_df["val_mse"], marker="o", label="PCR")
    if have_pls:
        pls_df = pd.DataFrame(pls_results).sort_values("n_components")
        ax.plot(pls_df["n_components"], pls_df["val_mse"], marker="s", label="PLS")
    ax.set_xlabel("Number of retained components")
    ax.set_ylabel("Validation MSE")
    ax.set_title("PCR vs. PLS: validation MSE vs. component count")
    ax.legend()
    plt.tight_layout()
    plt.show()
    if not (have_pcr and have_pls):
        missing = "PCR" if not have_pcr else "PLS"
        print(f"Showing only the completed method -- finish the {missing} task above to see both.")
else:
    print("Not complete yet: finish the PCR and/or PLS tasks above first.")
""",
            "wp51-307-plot",
        ),
        code(
            """
show_question("q-pcr-vs-pls")
""",
            "wp51-308-q-pcr-pls",
        ),
        md(
            """
### Interactive activity -- PCR or PLS?

Below, a small synthetic 2-D dataset (two correlated, standardized
predictors) lets you control the **direction** of the true predictive
signal relative to PC1 (the highest-variance direction) and the number of
retained components. PCR and PLS are refit live on the same synthetic
train/validation split every time you change a control.

What stays fixed on screen as you change **Weight on PC1**: the predictor
coordinates themselves, and the PC1/PC2 directions -- both come only from
the predictors' own covariance, never from the target, so changing where
the target comes from cannot move them. What changes: point color now shows
the generated target itself, and two new arrows -- the true signal
direction (which rotates with **Weight on PC1**) and the direction PLS
actually learned from it -- update live, along with their labels and the
legend. The right-hand bar chart's y-axis range is fixed across every
control setting (computed from the worst case across the whole grid, plus
headroom), so bar heights stay visually comparable no matter which setting
you pick.
""",
            "wp51-309-widget-intro",
        ),
        code(
            """
# ---- "PCR or PLS?" -- native interactive synthetic-data activity ----
# Self-contained imports: this activity must work even if the PCR/PLS
# tasks above were left blank.
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
from sklearn.cross_decomposition import PLSRegression as _PLSRegression

_PCRPLS_SEED = 0
_PCRPLS_RHO = 0.7
_PCRPLS_N_OBS = 80
_PCRPLS_N_TRAIN = 56
_PCRPLS_NOISE_SD = 0.3
_PCRPLS_W1_OPTIONS = [0.0, 0.25, 0.5, 0.7071, 0.9, 1.0]  # weight on the PC1 direction
_PCRPLS_N_OPTIONS = [1, 2]


def _pcrpls_make_data(w1):
    # X2 and pc1_dir/pc2_dir depend only on _PCRPLS_SEED -- never on w1 --
    # so they stay fixed on screen as "Weight on PC1" changes. Only the
    # TARGET-dependent part (the signal direction/strength, and therefore
    # y2 and the two arrows drawn from it) moves with w1.
    rng = np.random.RandomState(_PCRPLS_SEED)
    X2 = rng.multivariate_normal([0.0, 0.0], [[1.0, _PCRPLS_RHO], [_PCRPLS_RHO, 1.0]], size=_PCRPLS_N_OBS)
    pc1_dir = np.array([1.0, 1.0]) / np.sqrt(2)
    pc2_dir = np.array([1.0, -1.0]) / np.sqrt(2)
    z1 = X2 @ pc1_dir
    z1 = (z1 - z1.mean()) / z1.std()
    z2_raw = X2 @ pc2_dir
    z2_raw = (z2_raw - z2_raw.mean()) / z2_raw.std()
    z2 = z2_raw - (z2_raw @ z1) / (z1 @ z1) * z1  # orthogonalize against z1
    z2 = (z2 - z2.mean()) / z2.std()

    w2 = np.sqrt(max(0.0, 1.0 - w1 ** 2))
    signal_dir = w1 * pc1_dir + w2 * pc2_dir  # the TRUE predictive direction, rotates with w1
    signal = w1 * z1 + w2 * z2

    noise_rng = np.random.RandomState(_PCRPLS_SEED + 1)
    noise = noise_rng.normal(0.0, 1.0, size=_PCRPLS_N_OBS)
    noise = noise - (noise @ z1) / (z1 @ z1) * z1 - (noise @ z2) / (z2 @ z2) * z2
    noise = _PCRPLS_NOISE_SD * (noise - noise.mean()) / noise.std()

    y2 = signal + noise
    y2 = y2 - y2.mean()

    split_rng = np.random.RandomState(_PCRPLS_SEED + 2)
    perm = split_rng.permutation(_PCRPLS_N_OBS)
    train_idx, val_idx = perm[:_PCRPLS_N_TRAIN], perm[_PCRPLS_N_TRAIN:]
    return X2, y2, train_idx, val_idx, pc1_dir, pc2_dir, signal_dir


def _pcrpls_fit_and_score(w1, n_components):
    X2, y2, train_idx, val_idx, pc1_dir, pc2_dir, signal_dir = _pcrpls_make_data(w1)
    Xtr2, Xval2 = X2[train_idx], X2[val_idx]
    ytr2, yval2 = y2[train_idx], y2[val_idx]

    pcr2 = Pipeline([("scale", StandardScaler()), ("pca", PCA(n_components=n_components, random_state=0)), ("model", LinearRegression())]).fit(Xtr2, ytr2)
    pls2 = Pipeline([("scale", StandardScaler()), ("model", _PLSRegression(n_components=n_components, scale=False))]).fit(Xtr2, ytr2)
    pcr_mse = mean_squared_error(yval2, pcr2.predict(Xval2))
    pls_mse = mean_squared_error(yval2, pls2.predict(Xval2).ravel())

    # The direction PLS actually learned, mapped back to original feature
    # space for display only (never used in any score above).
    pls_scaler = pls2.named_steps["scale"]
    pls_weights = pls2.named_steps["model"].x_weights_[:, 0] / pls_scaler.scale_
    pls_dir = pls_weights / np.linalg.norm(pls_weights)
    if pls_dir @ signal_dir < 0:
        pls_dir = -pls_dir  # arrow orientation only -- PLS has no sign convention of its own

    return X2, y2, train_idx, val_idx, pc1_dir, pc2_dir, signal_dir, pls_dir, pcr_mse, pls_mse


# Fixed y-axis range for the right-hand validation-MSE plot: computed
# ONCE, from the worst case across every allowed (Weight on PC1,
# Components) combination -- never recomputed per render -- so bar heights
# stay visually comparable across every setting the controls can reach.
_pcrpls_global_max_mse = max(
    max(_pcrpls_fit_and_score(w1, n)[-2:]) for w1 in _PCRPLS_W1_OPTIONS for n in _PCRPLS_N_OPTIONS
)
_PCRPLS_MSE_YLIM = _pcrpls_global_max_mse * 1.15

_pcrpls_w1_dd = widgets.Dropdown(options=_PCRPLS_W1_OPTIONS, value=0.25, description="Weight on PC1:", style={"description_width": "initial"})
_pcrpls_n_dd = widgets.Dropdown(options=_PCRPLS_N_OPTIONS, value=1, description="Components:", style={"description_width": "initial"})
_pcrpls_output = widgets.Output()


def _pcrpls_render(_change=None):
    w1 = _pcrpls_w1_dd.value
    n_components = _pcrpls_n_dd.value
    X2, y2, train_idx, val_idx, pc1_dir, pc2_dir, signal_dir, pls_dir, pcr_mse, pls_mse = _pcrpls_fit_and_score(w1, n_components)

    with _pcrpls_output:
        _pcrpls_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        # Target-dependent: point color (by the generated target y2) and the
        # two colored arrows below all move with w1. Train vs. validation is
        # shown by MARKER SHAPE (circle vs. triangle), not color, so it stays
        # visible alongside the target coloring.
        sca = axes[0].scatter(X2[train_idx, 0], X2[train_idx, 1], c=y2[train_idx], cmap="viridis", s=28, marker="o", edgecolors="0.3", linewidths=0.3, label="train")
        axes[0].scatter(X2[val_idx, 0], X2[val_idx, 1], c=y2[val_idx], cmap="viridis", s=46, marker="^", edgecolors="0.3", linewidths=0.3, label="validation")
        plt.colorbar(sca, ax=axes[0], label="generated target y", fraction=0.046, pad=0.04)

        # Fixed regardless of w1: the predictor coordinates, and PC1/PC2 --
        # both come only from X2's own covariance (see _pcrpls_make_data).
        axes[0].arrow(0, 0, 2 * pc1_dir[0], 2 * pc1_dir[1], color="black", width=0.015, length_includes_head=True)
        axes[0].annotate("PC1 (fixed)", 2.2 * pc1_dir, fontsize=8)
        axes[0].arrow(0, 0, 1.3 * pc2_dir[0], 1.3 * pc2_dir[1], color="0.4", width=0.015, length_includes_head=True)
        axes[0].annotate("PC2 (fixed)", 1.5 * pc2_dir, fontsize=8)

        # Target-dependent: the TRUE signal direction (rotates with w1) and
        # the direction PLS actually learned from this w1's own data.
        axes[0].arrow(0, 0, 2 * signal_dir[0], 2 * signal_dir[1], color="crimson", width=0.015, length_includes_head=True)
        axes[0].annotate("true signal", 2.2 * signal_dir, fontsize=8, color="crimson")
        axes[0].arrow(0, 0, 1.6 * pls_dir[0], 1.6 * pls_dir[1], color="tab:green", width=0.015, length_includes_head=True, linestyle="--")
        axes[0].annotate("PLS direction", 1.8 * pls_dir, fontsize=8, color="tab:green")

        axes[0].set_xlabel("feature 1"); axes[0].set_ylabel("feature 2")
        axes[0].set_title(f"Synthetic data (weight on PC1 = {w1:.2f})")
        axes[0].legend(fontsize=7, loc="lower right")
        axes[0].set_aspect("equal")

        axes[1].bar(["PCR", "PLS"], [pcr_mse, pls_mse], color=["tab:blue", "tab:green"])
        axes[1].set_ylim(0, _PCRPLS_MSE_YLIM)  # fixed across every setting -- bars stay comparable
        axes[1].set_ylabel("Validation MSE (synthetic data)")
        axes[1].set_title(f"{n_components} component(s)")
        plt.tight_layout()
        plt.show()
        print(f"weight on PC1={w1:.2f}  components={n_components}  PCR val MSE={pcr_mse:.3f}  PLS val MSE={pls_mse:.3f}")


_pcrpls_w1_dd.observe(_pcrpls_render, names="value")
_pcrpls_n_dd.observe(_pcrpls_render, names="value")
display(widgets.VBox([controls_row(_pcrpls_w1_dd, _pcrpls_n_dd), _pcrpls_output]))
_pcrpls_render()
""",
            "wp51-310-widget",
        ),
        md(
            """
A few questions worth exploring with the controls above (predict your
answer, then check it against what the activity shows):

- With one component, when does PLS clearly outperform PCR -- and when do
  they perform almost identically?
- Why do PCR and PLS become more similar once both components are
  retained?
- Does a component that explains more predictor variance necessarily
  predict the target better?

*(This activity uses entirely synthetic data -- not ABIDE -- clearly
labeled above.)*
""",
            "wp51-311-widget-note",
        ),
    ]


def _section_4_svm_and_svr() -> list[dict]:
    param_sets_literal = "[\n    " + ",\n    ".join(repr(p) for p in SVR_PARAM_SETS) + ",\n]"
    return [
        md("## 4. Support Vector Machines and SVR", "wp51-401-header"),
        md(
            """
A **support vector machine (SVM)** for classification looks for the
separating boundary with the largest possible **margin** -- the distance
from the boundary to the nearest training points on either side. Those
nearest points are the **support vectors**: the only training points that
determine where the boundary sits. `SVC` fits this boundary for
classification; `SVR` fits a regression version, where predictions within
an **epsilon-insensitive tube** around the observed value are not
penalized at all. Because both depend on distances and margins, scaling the
predictors first is a requirement, not an option -- exactly as it was for
KNN.

| Parameter | Meaning | Used by |
|---|---|---|
| `C` | How strongly the model penalizes margin violations/errors | `SVC` and `SVR` |
| `epsilon` | How much regression error is tolerated before any penalty applies | `SVR` only |
| `kernel` | The type of relationship the model can represent (`linear`, `poly`, `rbf`) | `SVC` and `SVR` |
| `gamma` | How local/flexible an RBF (or `poly`) relationship can become | `SVC` and `SVR` (RBF/`poly` only) |
| `degree` | The polynomial degree | `SVC` and `SVR` (`poly` only) |

Direct interpretations: smaller `C` means more regularization and greater
tolerance for violations; larger `C` means stronger pressure to fit every
training point, even at the cost of a narrower margin; larger RBF `gamma`
means a more local, potentially more complex boundary.
""",
            "wp51-402-intro",
        ),
        code(
            """
show_question("q-c-gamma-epsilon")
""",
            "wp51-403-q-params",
        ),
        md(
            """
### Interactive activity -- explore an SVM boundary

Choose a dataset, a kernel, `C`, and (for RBF/polynomial) `gamma`; the
boundary refits live on a small synthetic 2-D classification dataset
(never ABIDE). Train and validation points are shown with different
markers, support vectors are circled, and both accuracies are printed, so
you can watch training accuracy and validation accuracy move
independently.
""",
            "wp51-406-widget-intro",
        ),
        code(
            """
# ---- "Explore an SVM Boundary" -- native interactive activity ----
# Self-contained imports: this activity must work even if the PCR/PLS tasks
# above were left blank.
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC


def make_svc_dataset(kind, seed=%(seed)r, n=%(n)r, train_fraction=%(frac)r):
    \"\"\"A small, fixed-seed, entirely synthetic 2-D classification dataset --
    never ABIDE. kind="linear": two separated blobs. kind="nonlinear": an
    inner blob surrounded by a noisy outer ring (not linearly separable).
    Reused below and by Section 5's Ridge/KernelRidge illustration.
    \"\"\"
    rng = np.random.RandomState(seed)
    n_per = n // 2
    if kind == "linear":
        c0 = rng.normal(loc=[-1.5, 0.0], scale=0.9, size=(n_per, 2))
        c1 = rng.normal(loc=[1.5, 0.0], scale=0.9, size=(n - n_per, 2))
        X2 = np.vstack([c0, c1])
    else:
        inner = rng.normal(loc=[0.0, 0.0], scale=0.9, size=(n_per, 2))
        angles = np.linspace(0, 2 * np.pi, n - n_per, endpoint=False)
        radius = 3.0 + rng.normal(0.0, 0.4, size=len(angles))
        outer = np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)
        outer = outer + rng.normal(0.0, 0.3, size=outer.shape)
        X2 = np.vstack([inner, outer])
    y2 = np.array([0] * n_per + [1] * (n - n_per))

    split_rng = np.random.RandomState(seed + 100)
    idx0 = split_rng.permutation(np.where(y2 == 0)[0])
    idx1 = split_rng.permutation(np.where(y2 == 1)[0])
    n_train_per = int(round(train_fraction * n_per))
    train_idx = np.concatenate([idx0[:n_train_per], idx1[:n_train_per]])
    val_idx = np.concatenate([idx0[n_train_per:], idx1[n_train_per:]])
    return X2, y2, train_idx, val_idx


_svm_dataset_dd = widgets.Dropdown(options=[("Linearly separable blobs", "linear"), ("Nonlinear rings", "nonlinear")], value="nonlinear", description="Dataset:", style={"description_width": "initial"})
_svm_kernel_dd = widgets.Dropdown(options=["linear", "poly", "rbf"], value="rbf", description="Kernel:", style={"description_width": "initial"})
_svm_c_dd = widgets.Dropdown(options=[0.1, 1, 10, 100], value=1, description="C:", style={"description_width": "initial"})
_svm_gamma_dd = widgets.Dropdown(options=[("auto-scaled", "scale"), ("0.1", 0.1), ("1.0", 1.0), ("5.0", 5.0)], value="scale", description="gamma (RBF/poly):", style={"description_width": "initial"})
_svm_output = widgets.Output()


def _svm_render(_change=None):
    kind, kernel, C, gamma = _svm_dataset_dd.value, _svm_kernel_dd.value, _svm_c_dd.value, _svm_gamma_dd.value
    X2, y2, train_idx, val_idx = make_svc_dataset(kind)
    kwargs = {"kernel": kernel, "C": C}
    if kernel in ("rbf", "poly"):
        kwargs["gamma"] = gamma
    if kernel == "poly":
        kwargs["degree"] = 3
    pipe = Pipeline([("scale", StandardScaler()), ("svc", SVC(**kwargs))]).fit(X2[train_idx], y2[train_idx])
    svc = pipe.named_steps["svc"]
    Xs = pipe.named_steps["scale"].transform(X2)
    train_acc = pipe.score(X2[train_idx], y2[train_idx])
    val_acc = pipe.score(X2[val_idx], y2[val_idx])

    with _svm_output:
        _svm_output.clear_output(wait=True)
        xx, yy = np.meshgrid(np.linspace(Xs[:, 0].min() - 0.5, Xs[:, 0].max() + 0.5, 200),
                              np.linspace(Xs[:, 1].min() - 0.5, Xs[:, 1].max() + 0.5, 200))
        zz = svc.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

        fig, ax = plt.subplots(figsize=(5.5, 5))
        ax.contourf(xx, yy, zz, levels=[-1e9, 0, 1e9], colors=["#fde0dd", "#deebf7"], alpha=0.6)
        ax.contour(xx, yy, zz, levels=[-1, 0, 1], colors="k", linestyles=["--", "-", "--"], linewidths=1)
        ax.scatter(Xs[train_idx, 0], Xs[train_idx, 1], c=y2[train_idx], cmap="coolwarm", s=24, edgecolors="k", linewidths=0.4, marker="o", label="train")
        ax.scatter(Xs[val_idx, 0], Xs[val_idx, 1], c=y2[val_idx], cmap="coolwarm", s=36, edgecolors="k", linewidths=0.6, marker="^", label="validation")
        ax.scatter(Xs[svc.support_, 0], Xs[svc.support_, 1], s=100, facecolors="none", edgecolors="black", linewidths=1.2, label="support vectors")
        ax.set_title(f"{kernel} kernel, C={C}" + (f", gamma={gamma}" if kernel in ("rbf", "poly") else ""))
        ax.legend(fontsize=7, loc="lower right")
        plt.tight_layout()
        plt.show()
        print(f"dataset={kind}  kernel={kernel}  C={C}  gamma={gamma if kernel in ('rbf', 'poly') else 'n/a'}  "
              f"train accuracy={train_acc:.3f}  validation accuracy={val_acc:.3f}  "
              f"support vectors={len(svc.support_)} of {len(train_idx)}")


for _w in (_svm_dataset_dd, _svm_kernel_dd, _svm_c_dd, _svm_gamma_dd):
    _w.observe(_svm_render, names="value")
display(widgets.VBox([controls_row(_svm_dataset_dd, _svm_kernel_dd, _svm_c_dd, _svm_gamma_dd), _svm_output]))
_svm_render()
"""
            % {"seed": SVC_DATASET_SEED, "n": SVC_DATASET_N, "frac": SVC_DATASET_TRAIN_FRACTION},
            "wp51-407-widget",
        ),
        md(
            """
A few questions worth exploring with the controls above:

- Why can the linear kernel not separate the "Nonlinear rings" dataset
  well, no matter how large `C` gets?
- What happens to the number of support vectors as `C` grows very large?
- What happens to the boundary as RBF `gamma` grows very large -- and what
  does that do to training accuracy versus validation accuracy?

`SVR` uses the same ideas for a continuous outcome such as age, replacing
the classification margin with the epsilon-insensitive regression
objective described above.
""",
            "wp51-408-widget-note",
        ),
        code(
            """
show_question("q-train-vs-val")
""",
            "wp51-409-q-train-val",
        ),
        md(
            f"""
### Your task: SVR for ABIDE age prediction

`SVR` on the full 753-row training partition is slow in a browser kernel
(a linear-kernel fit alone can take tens of seconds per configuration,
worse at higher `C`) -- so this task fits on a **fixed random 300-row
subset** of `X_train`/`y_train` (`SVR_SUBSET_N={SVR_SUBSET_N}`,
`SVR_SUBSET_SEED={SVR_SUBSET_SEED}`), supplied below. **These are subset
scores, not full-dataset scores** -- do not treat them as what the full
753-row partition would have produced.

For each entry of the small parameter set below, build a scaled `SVR`
pipeline (`StandardScaler` -> `SVR(**params)`), fit it on the subset, and
record its validation MSE and R² (scored against the full `X_val`/`y_val`,
never the subset).

Required output name: `svr_results` -- a list of dicts, one per parameter
set, each shaped `{{"kernel": ..., "C": ..., "gamma": ..., "val_mse": ...,
"val_r2": ...}}`.
""",
            "wp51-410-instructions",
        ),
        blank(
            f"""
from sklearn.svm import SVR
from sklearn.metrics import r2_score

SVR_PARAM_SETS = {param_sets_literal}

_svr_subset_rng = np.random.RandomState({SVR_SUBSET_SEED!r})
_svr_subset_idx = _svr_subset_rng.choice(len(X_train), size={SVR_SUBSET_N!r}, replace=False)
X_train_svr_subset = X_train[_svr_subset_idx]
y_train_svr_subset = y_train[_svr_subset_idx]
svr_results = []

# YOUR CODE HERE
# Hint: build one scaled SVR pipeline per entry of SVR_PARAM_SETS -- skip
# any parameter whose value is None (gamma only means something for the
# rbf kernel). Train on the subset above; score against the full
# validation set named earlier in this notebook.
# Outside the browser, a wider search (e.g. GridSearchCV over a larger
# C/gamma grid) would normally replace this fixed short parameter list --
# not run here, since Pyodide has no GPU/multiple threads and
# GridSearchCV's own internal cross-validation would multiply an already
# slow fit cost several times over.
""",
            f"""
from sklearn.svm import SVR
from sklearn.metrics import r2_score

SVR_PARAM_SETS = {param_sets_literal}

_svr_subset_rng = np.random.RandomState({SVR_SUBSET_SEED!r})
_svr_subset_idx = _svr_subset_rng.choice(len(X_train), size={SVR_SUBSET_N!r}, replace=False)
X_train_svr_subset = X_train[_svr_subset_idx]
y_train_svr_subset = y_train[_svr_subset_idx]

svr_results = []
for params in SVR_PARAM_SETS:
    svr_kwargs = {{k: v for k, v in params.items() if v is not None}}
    pipe = Pipeline([("scale", StandardScaler()), ("svr", SVR(**svr_kwargs))])
    pipe.fit(X_train_svr_subset, y_train_svr_subset)
    pred = pipe.predict(X_val)
    svr_results.append({{
        **params,
        "val_mse": float(mean_squared_error(y_val, pred)),
        "val_r2": float(r2_score(y_val, pred)),
    }})
print(pd.DataFrame(svr_results))
""",
            "wp51-411-svr-blank",
            tags=["wp51-activity-svr"],
        ),
        code(
            f"""
# Run this to check your SVR results.
EXPECTED_SVR_BEST_KERNEL = {EXPECTED_SVR_BEST_KERNEL!r}
EXPECTED_SVR_BEST_C = {EXPECTED_SVR_BEST_C!r}
EXPECTED_SVR_BEST_MSE = {EXPECTED_SVR_BEST_MSE!r}
MSE_TOLERANCE = {MSE_TOLERANCE!r}

if "svr_results" in globals() and svr_results:
    if len(svr_results) != len(SVR_PARAM_SETS):
        print(f"Not quite: expected one result per entry of SVR_PARAM_SETS ({{len(SVR_PARAM_SETS)}} values).")
    else:
        best = min(svr_results, key=lambda r: r["val_mse"])
        if best["kernel"] == EXPECTED_SVR_BEST_KERNEL and best["C"] == EXPECTED_SVR_BEST_C and abs(best["val_mse"] - EXPECTED_SVR_BEST_MSE) <= MSE_TOLERANCE:
            print(f"Looks good: best config kernel={{best['kernel']}}, C={{best['C']}}, val_mse={{best['val_mse']:.2f}} "
                  f"(expected ~{{EXPECTED_SVR_BEST_MSE:.1f}}).")
        else:
            print(
                f"Your best configuration (kernel={{best['kernel']}}, C={{best['C']}}, val_mse={{best['val_mse']:.2f}}) "
                "differs from the expected result. That does not automatically mean something is wrong -- check "
                "that every pipeline was fit on X_train_svr_subset/y_train_svr_subset and scored on the full "
                "X_val/y_val before assuming this is an error."
            )
else:
    print("Not complete yet: define svr_results above first.")
""",
            "wp51-412-svr-check",
        ),
    ]


def _section_5_kernels_beyond_svm() -> list[dict]:
    return [
        md("## 5. Kernels Beyond SVM", "wp51-501-header"),
        md(
            """
A **kernel** is a similarity function between two observations -- a way of
asking "how alike are these two participants?" without necessarily
constructing every transformed feature explicitly. The **RBF kernel** used
by SVC/SVR above measures similarity that decays smoothly with distance:
two observations that are close together are very similar; far-apart
observations are treated as nearly unrelated.
""",
            "wp51-502-intro",
        ),
        code(
            """
# Supplied: RBF similarity as a function of distance, for two gamma values.
from sklearn.metrics.pairwise import rbf_kernel

distances = np.linspace(0, 5, 100).reshape(-1, 1)
origin = np.zeros((1, 1))
fig, ax = plt.subplots(figsize=(5, 3.5))
for gamma in (0.2, 1.0, 3.0):
    similarity = rbf_kernel(distances, origin, gamma=gamma).ravel()
    ax.plot(distances.ravel(), similarity, label=f"gamma={gamma}")
ax.set_xlabel("distance between two observations")
ax.set_ylabel("RBF similarity")
ax.set_title("RBF similarity decays with distance -- faster for larger gamma")
ax.legend()
plt.tight_layout()
plt.show()
""",
            "wp51-503-illustration",
        ),
        md(
            """
`Ridge` relates to this idea very directly: `KernelRidge(kernel="rbf")` is
the **exact** RBF-kernel counterpart of ordinary, L2-regularized (`Ridge`)
regression -- the same regularized least-squares problem, solved with a
different (kernel) parameterization, rather than an approximation of it.
That does not mean the two will produce identical predictions for any
`alpha`/`gamma` you happen to pick; it means the kernelized version is
exact for whatever parameters it is actually given.

### Your task: Ridge vs. the exact kernel trick

Fit **ordinary** `Ridge(alpha={ridge_alpha})` and
`KernelRidge(kernel="rbf", alpha={kr_alpha}, gamma={kr_gamma})` -- both
inside a `Pipeline` with `StandardScaler` -- on `X_train`/`y_train`, and
record each one's validation MSE and R² on `X_val`/`y_val`.

Required output names: `ridge_result` and `kernel_ridge_result` -- each a
dict shaped `{{"val_mse": ..., "val_r2": ...}}`. Use these exact names (not,
for example, reusing a bare `ridge_result`/`model` name from an earlier
exercise) so Section 6's comparison can find both.
""".format(
                ridge_alpha=RIDGE_ALPHA, kr_alpha=KERNEL_RIDGE_ALPHA, kr_gamma=KERNEL_RIDGE_GAMMA
            ),
            "wp51-504-ridge-kernelridge-instructions",
        ),
        blank(
            f"""
from sklearn.linear_model import Ridge
from sklearn.kernel_ridge import KernelRidge

# YOUR CODE HERE
# Hint: this is two short, independent fits, each needing its own scaler --
# Ridge(alpha={RIDGE_ALPHA!r}) for the first, KernelRidge(kernel="rbf",
# alpha={KERNEL_RIDGE_ALPHA!r}, gamma={KERNEL_RIDGE_GAMMA!r}) for the second.
""",
            f"""
from sklearn.linear_model import Ridge
from sklearn.kernel_ridge import KernelRidge

ridge_pipe = Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha={RIDGE_ALPHA!r}))]).fit(X_train, y_train)
ridge_pred = ridge_pipe.predict(X_val)
ridge_result = {{"val_mse": float(mean_squared_error(y_val, ridge_pred)), "val_r2": float(r2_score(y_val, ridge_pred))}}

kernel_ridge_pipe = Pipeline([
    ("scale", StandardScaler()),
    ("model", KernelRidge(kernel="rbf", alpha={KERNEL_RIDGE_ALPHA!r}, gamma={KERNEL_RIDGE_GAMMA!r})),
]).fit(X_train, y_train)
kernel_ridge_pred = kernel_ridge_pipe.predict(X_val)
kernel_ridge_result = {{"val_mse": float(mean_squared_error(y_val, kernel_ridge_pred)), "val_r2": float(r2_score(y_val, kernel_ridge_pred))}}
print("Ridge:       ", ridge_result)
print("KernelRidge: ", kernel_ridge_result)
""",
            "wp51-505-kernelridge-blank",
            tags=["wp51-activity-kernelridge"],
        ),
        code(
            f"""
# Run this to check your Ridge / KernelRidge results.
EXPECTED_RIDGE_MSE = {EXPECTED_RIDGE_MSE!r}
EXPECTED_KERNEL_RIDGE_MSE = {EXPECTED_KERNEL_RIDGE_MSE!r}
MSE_TOLERANCE = {MSE_TOLERANCE!r}

have_ridge = "ridge_result" in globals()
have_kernel_ridge = "kernel_ridge_result" in globals()
if have_ridge and have_kernel_ridge:
    ridge_ok = abs(ridge_result["val_mse"] - EXPECTED_RIDGE_MSE) <= MSE_TOLERANCE
    kr_ok = abs(kernel_ridge_result["val_mse"] - EXPECTED_KERNEL_RIDGE_MSE) <= MSE_TOLERANCE
    if ridge_ok and kr_ok:
        print(f"Looks good: Ridge val_mse={{ridge_result['val_mse']:.2f}} (expected ~{{EXPECTED_RIDGE_MSE}}), "
              f"KernelRidge val_mse={{kernel_ridge_result['val_mse']:.2f}} (expected ~{{EXPECTED_KERNEL_RIDGE_MSE}}).")
    else:
        print(
            "Your Ridge and/or KernelRidge validation MSE differs from the expected numbers by more than a "
            f"generous tolerance ({{ridge_result['val_mse']:.2f}} vs ~{{EXPECTED_RIDGE_MSE}}; "
            f"{{kernel_ridge_result['val_mse']:.2f}} vs ~{{EXPECTED_KERNEL_RIDGE_MSE}}). That does not automatically "
            f"mean something is wrong -- check alpha={RIDGE_ALPHA!r}/{KERNEL_RIDGE_ALPHA!r}, "
            f"gamma={KERNEL_RIDGE_GAMMA!r}, and that both pipelines were fit on X_train/y_train, before assuming "
            "this is an error."
        )
else:
    missing = [n for n, have in (("ridge_result", have_ridge), ("kernel_ridge_result", have_kernel_ridge)) if not have]
    print(f"Not complete yet: define {{', '.join(missing)}} above first.")
""",
            "wp51-506-kernelridge-check",
        ),
        code(
            """
show_question("q-exact-vs-approx")
""",
            "wp51-507-q-exact-approx",
        ),
    ]


def _section_6_compare_and_reflect(benchmark: dict) -> list[dict]:
    benchmark_literal = repr(
        {"val_mse": benchmark["val_mse"], "val_r2": benchmark["val_r2"], "n_train": benchmark["n_train"], "n_features": benchmark["n_features"]}
    )
    return [
        md("## 6. Compare and Reflect", "wp51-601-header"),
        md(
            f"""
Supplied: one table and plot assembling every method that was trained on
**all {benchmark["n_train"]} training participants and the same full
{benchmark["n_features"]}-feature matrix**, evaluated on the same
{benchmark["n_val"]} validation participants -- PCR, PLS, Ridge, and
KernelRidge from your own completed tasks above, plus a separate SVR row
computed the same way. If a section was skipped, that row is simply
missing, with a clear message -- never a traceback.

That separate SVR row is an **instructor/reference benchmark**, not your
own Section 4 SVR activity: your SVR task there deliberately fits on a
small, fixed subset of the training rows (a responsive, browser-friendly
exercise), so its own score is not comparable to the full-training-data
rows above it, and is reported on its own, below the table, instead of
being ranked inside it. The reference benchmark's own configuration was
chosen once, before anyone looked at its validation score -- it illustrates
an honest full-data SVR number, not necessarily the best one possible.

One more caution: comparing validation scores across several models and
settings, the way the table below does, is a useful **exploratory** signal
-- it is not the same as an unbiased estimate of final performance on
genuinely new data. Trying many settings and reporting the best one
inflates how good that best score looks, exactly the way Exercise 4's own
leakage lesson warned against for a single model's hyperparameters.
""",
            "wp51-602-compare-intro",
        ),
        code(
            f"""
SVR_BENCHMARK = {benchmark_literal}  # instructor/reference, full training data -- see the markdown above

_comparison_rows = []


def _best_of(results, label):
    if results:
        best = min(results, key=lambda r: r["val_mse"])
        row = {{"model": label, "val_mse": best["val_mse"]}}
        if "val_r2" in best:
            row["val_r2"] = best["val_r2"]
        _comparison_rows.append(row)
        return True
    return False


_missing = []
if not _best_of(globals().get("pcr_results"), "PCR (best n_components, full training data)"):
    _missing.append("pcr_results (Section 2)")
if not _best_of(globals().get("pls_results"), "PLS (best n_components, full training data)"):
    _missing.append("pls_results (Section 3)")

for name, label in (("ridge_result", "Ridge (full training data)"), ("kernel_ridge_result", "KernelRidge (RBF, full training data)")):
    result = globals().get(name)
    if result is not None:
        _comparison_rows.append({{"model": label, "val_mse": result["val_mse"], "val_r2": result.get("val_r2")}})
    else:
        _missing.append(f"{{name}} (Section 5)")

_comparison_rows.append({{
    "model": "SVR (instructor reference, full training data)",
    "val_mse": SVR_BENCHMARK["val_mse"],
    "val_r2": SVR_BENCHMARK["val_r2"],
}})

if _comparison_rows:
    comparison_df = pd.DataFrame(_comparison_rows).sort_values("val_mse").reset_index(drop=True)
    display(comparison_df.round(3))
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    x_positions = range(len(comparison_df))
    ax.bar(x_positions, comparison_df["val_mse"], color="#4c72b0")
    ax.set_xticks(x_positions)  # explicit tick positions before set_xticklabels -- avoids a Matplotlib warning
    ax.set_xticklabels(comparison_df["model"], rotation=25, ha="right")
    ax.set_ylabel("Validation MSE")
    ax.set_title("Full training data, same validation participants")
    plt.tight_layout()
    plt.show()
else:
    print("No completed results yet -- finish at least one task above to see a comparison.")

if _missing:
    print("Not included above (not yet completed): " + ", ".join(_missing))

# Your own SVR activity (Section 4) fit on a small SUBSET of the training
# partition, for runtime reasons -- never the full partition every row
# above was fit on -- so it is reported separately, never ranked against
# them.
if "svr_results" in globals() and svr_results:
    _svr_best = min(svr_results, key=lambda r: r["val_mse"])
    print(
        f"Your own SVR activity (Section 4, {{len(X_train_svr_subset)}}-row training subset) best result: "
        f"kernel={{_svr_best['kernel']}}, C={{_svr_best['C']}}, val_mse={{_svr_best['val_mse']:.2f}} -- "
        "not ranked above: it was fit on a subset, not the full training partition the table's rows use."
    )
else:
    print("Your own SVR activity (Section 4) is not complete yet -- even once it is, it won't be ranked in the table above (see why in the markdown).")
""",
            "wp51-603-compare",
        ),
        md(
            """
> **Looking at the table above, which model would you investigate further, and why?**

> **This notebook's comparison comes from exactly one train/validation split. Why can a single split never establish a universal "winner" among these methods?**
""",
            "wp51-604-reflection",
        ),
        md(
            """
### What should we remember?

- PCR's components summarize `X`'s own variance; PLS's components use `X`
  and `y` together -- neither is universally better.
- `StandardScaler`/PCA/PLS must be fit on training data only; fitting them
  before a split leaks information even when the step never looks at the
  target.
- `C`, `gamma`, and `epsilon` all trade flexibility against regularization
  for SVC/SVR -- and more flexibility is not automatically better on
  validation data, even when it helps on training data.
- `KernelRidge(kernel="rbf")` solves the same regularized regression
  problem as `Ridge`, exactly, in a kernel parameterization.
- A small-subset activity score and a full-training-data score answer
  different questions -- comparing them directly is misleading, even when
  both describe "SVR."
- Comparing several models and settings on one validation split is a useful
  exploratory signal, not an unbiased estimate of performance on new data.
- One split, one dataset, and one feature set can never crown a universal
  winner among the models compared here.

Collapsing this notebook's question-checking setup into one hidden cell
makes the question cells themselves easier to read; it is **not** secure
answer protection. This is still a fully downloadable, offline, editable
notebook, and a technically curious student can always recover an answer
key by expanding that cell or inspecting the running kernel.
""",
            "wp51-605-summary",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_load_and_split()

    def render_section(section_items: list) -> list[dict]:
        return [c.render(mode) if isinstance(c, Blank) else c for c in section_items]

    cells += render_section(_section_2_pcr())
    cells += render_section(_section_3_pls())
    cells += render_section(_section_4_svm_and_svr())
    cells += render_section(_section_5_kernels_beyond_svm())
    cells += _section_6_compare_and_reflect(_svr_benchmark())
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
