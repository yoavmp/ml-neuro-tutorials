#!/usr/bin/env python3
"""Generate Exercise 8's JupyterLite template, portable copy, and reference.

WP47: migrate Exercise 8 ("Unsupervised Learning") to the same JupyterLite-
native, generator-authored architecture WP41/WP44/WP45/WP46 established for
Exercises 1-7 (see WPs/reports/WP41_MAINTAINER_GUIDE.md), following
scripts/generate_exercise_07_notebook.py's exact shape. Unlike Exercises 6/7,
this is a content redesign, not a line-for-line port: the legacy notebook
taught PCA/K-means almost entirely through supplied code and two embedded
iframes; this migration teaches the same material primarily through student
code, five short guided blanks, one native interactive activity, and six
checked conceptual questions (WP47 spec, "Authority and scope").

Data: reuses the exact same same-origin export Exercises 2, 4, 5, 6, and 7
already ship, book/lite/files/data/abide_age_brain.csv (360 fsCT predictors
+ age + group, 1004 participants). A second, new, Exercise-8-only sidecar
(book/lite/files/data/abide_age_brain_demographics.csv -- sex + site, plus a
verification age column) was exported by
scripts/export_abide_demographics_lite_data.py because the shared brain
table deliberately does not carry sex/site (WP41 section 3: "keep exports
slim") and this exercise's spec requires sex/site for *post-fit coloring
only* -- never as a PCA/K-means input. The new sidecar is row-for-row aligned
with the existing brain CSV by construction (both are the same
abide_modeling_data.load_modeling_frame() call, filtered to age.notna(), in
the frame's own original order, verified directly: see
scripts/export_abide_demographics_lite_data.py's own --check and
tests/test_export_abide_demographics_lite_data.py). No existing shared file
was modified.

Numbers verified directly against book/lite/files/data/abide_age_brain.csv
(and the new demographics sidecar) before writing a single generator line --
see the WP47 report for the full reasoning. The key finding, different from
WP46's Exercise 6/7 finding: PCA and K-means (and KNN's Euclidean distance)
are mathematically **invariant to column order** -- permuting the 360
fsCT_* columns changes nothing about explained variance, PC scores, or
cluster assignments, unlike a tree's greedy per-feature split search. Direct
verification against this CSV reproduces the legacy (network-sourced) audit
numbers for Sections 1-4 almost exactly (differences only in the 5th/6th
decimal, from the CSV's ~6-significant-figure rounding):
  PCA (all 1004 participants, 360 standardized features, n_components=50,
    random_state=0): PC1 explained variance = 36.1414%, cumulative at
    PC2/5/10/20/50 = 42.0024% / 49.4155% / 54.3078% / 60.0997% / 70.1822% --
    matches scripts/pca_kmeans_audit_result.json (computed from the network
    source) to 4 decimal places.
  K-means (N_CLUSTER_COMPONENTS=10, K_CANDIDATES=[1,2,3,4,5,6],
    random_state=0, n_init=10): inertia falls monotonically
    (196290.19 -> 65155.73); silhouette (k>=2 only) = 0.3784 (k=2),
    0.2650 (k=3, an exact match to the legacy audit's demo k=3 silhouette of
    0.265), 0.1923 (k=4), 0.1890 (k=5), 0.1936 (k=6) -- no strong elbow,
    consistent with the legacy notebook's own stated finding.
  Section 5 supervised pipeline (test_size=0.25, random_state=42,
    stratify=group; KFold(5, shuffle=True, random_state=13) on the 753-row
    development partition; component_grid=[5,10,20,50,100], k_grid=[5,10,20,40]):
    this notebook's own data source selects (n_components=20, k=5), mean CV
    MSE=24.9069 -- very close to, but not identical to, the legacy audit's
    (n_components=20, k=10), mean CV MSE=24.8286 (a near-tied margin of
    ~0.08 MSE between k=5 and k=10 at n_components=20, which the CSV's
    6-significant-figure rounding is enough to flip -- a genuine, honestly-
    computed difference in which near-tied candidate wins, not a bug;
    verified directly, not assumed). Locked-test MSE/R2 for this notebook's
    own selection: 19.1311 / 0.795060 (legacy, at its own k=10 selection:
    21.0491 / 0.774513). The raw-feature (no-PCA) KNN baseline is
    **order-invariant and matches the legacy audit exactly**: selected k=5,
    mean CV MSE=35.3979, locked-test MSE/R2=32.0452/0.656718 -- Euclidean
    distance over all 360 features does not depend on column order at all,
    unlike a tree's per-feature greedy split search.

Outputs:
  book/lite/files/exercise_08.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_08/exercise_08_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_08_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_08_reference.ipynb (--reference)

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

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_08.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_08" / "exercise_08_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_08_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_08_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 8, "templateVersion": TEMPLATE_VERSION},
}

N_PCA_COMPONENTS = 50
N_TOP_LOADINGS = 8

N_CLUSTER_COMPONENTS = 10
K_CANDIDATES = [1, 2, 3, 4, 5, 6]

ACTIVITY_RETAINED_PC_GRID = [2, 5, 10, 20, 50]
ACTIVITY_K_GRID = [2, 3, 4, 5, 6]
ACTIVITY_SEEDS = [0, 1, 2]
ACTIVITY_N_INIT = 10
ACTIVITY_DEFAULT_RETAINED_PC = 10
ACTIVITY_DEFAULT_K = 3
ACTIVITY_DEFAULT_SEED = 0
ACTIVITY_EXTERNAL_VARIABLES = {
    "group": "diagnosis (1=autism, 2=control)",
    "sex": "sex (1=male, 2=female)",
    "site": "acquisition site",
    "age": "age",
}

COMPONENT_GRID = [5, 10, 20, 50, 100]
K_GRID = [5, 10, 20, 40]
CV_RANDOM_STATE = 13

EXPECTED_PC1_EVR = 0.3614
EXPECTED_CUMVAR = {2: 0.4200, 5: 0.4942, 10: 0.5431, 20: 0.6010, 50: 0.7018}
EXPECTED_KMEANS_SILHOUETTE = {2: 0.3784, 3: 0.2650, 4: 0.1923, 5: 0.1890, 6: 0.1936}
EXPECTED_SELECTED_N_COMPONENTS = 20
EXPECTED_SELECTED_K = 5
EXPECTED_SELECTED_MEAN_CV_MSE = 24.9069
EXPECTED_TEST_MSE = 19.1311
EXPECTED_RAW_TEST_MSE = 32.0452


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
#
# WP47's own addition to this shared pattern: the question-checking helpers
# now carry the question CONTENT (prompt/options/correct answer) in this
# hidden cell's own _QUESTIONS dict, behind a short show_question(id)
# wrapper -- so a visible question cell never prints or displays a
# correct_index/correct_indices value (see "Multiple-choice answer
# visibility" in the WP47 spec). This is a readability/UX improvement, not
# real answer-key secrecy: the hidden cell is fully expandable, and a
# downloaded, fully offline, editable notebook must contain enough
# information to check an answer locally, so a technically curious student
# can always recover it from source or the running kernel. That honest limit
# is stated again in the WP47 report, not hidden from the student either
# (see the closing summary's own note).
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
import matplotlib.ticker as mticker
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
        table = pd.read_csv(_ABIDE_TSV_URL, sep="\\t")
    table = table.dropna(subset=["age"])
    return table[_ABIDE_LITE_FEATURES + ["age", "group"]].reset_index(drop=True)


def load_demographics_table():
    """Return sex and site for the same participants, in the same row
    order as load_abide_age_brain_table() -- for coloring an already-fitted
    plot only, never a PCA/K-means input.
    """
    from pathlib import Path

    local_path = Path("data/abide_age_brain_demographics.csv")
    if local_path.exists():
        table = pd.read_csv(local_path)
    else:
        table = pd.read_csv(_ABIDE_TSV_URL, sep="\\t")
        table = table.dropna(subset=["age"]).reset_index(drop=True)
    return table[["sex", "site"]].reset_index(drop=True)


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


# Question content lives here, not in the visible cell that displays it:
# a visible call like show_question("q-unsupervised-info") never prints or
# displays correct_index/correct_indices itself.
_QUESTIONS = {
    "q-unsupervised-explore": dict(
        kind="single",
        prompt=(
            "Without a target label, what can an unsupervised analysis help us "
            "explore?"
        ),
        options=[
            "Dimensions, patterns, and possible groups in the data -- without promising it has recovered real diagnostic classes.",
            "The exact diagnostic class of every participant, recovered directly from their brain measurements.",
            "Nothing useful -- without a target, there is no information left to analyze.",
        ],
        correct_index=0,
        feedback_correct="Correct: unsupervised methods describe structure that already exists in the data -- a starting point for a hypothesis, not a confirmed diagnostic result.",
    ),
    "q-unsupervised-info": dict(
        kind="single",
        prompt=(
            "With no target column supplied, what information can an unsupervised "
            "algorithm actually use to group or summarize participants?"
        ),
        options=[
            "Only the predictor measurements themselves -- their patterns, distances, and shared variance.",
            "The participants' diagnosis, sex, site, and age, which the algorithm reads automatically if they are in the table.",
            "Whatever labels we color the finished plot with, since those were used to fit the model.",
        ],
        correct_index=0,
        feedback_correct="Correct: PCA and K-means only ever see the predictor measurements. Coloring an already-fitted plot by diagnosis, sex, site, or age is an interpretation step after fitting, never an input to it.",
    ),
    "q-pca-separation": dict(
        kind="single",
        prompt="What can visible separation (or lack of separation) in a PC1-vs-PC2 scatter plot establish?",
        options=[
            "That the colored characteristic relates to some of the variance PCA captured -- not that PCA is a good predictor of it, and not that no relationship exists if the plot looks mixed.",
            "That PCA has successfully predicted the colored characteristic with high accuracy.",
            "That any two participants placed close together in the plot must share the same diagnosis.",
        ],
        correct_index=0,
        feedback_correct="Correct: PCA keeps the directions of greatest variance in the predictors, chosen without looking at the coloring variable at all -- visible structure is suggestive, not predictive proof, and a mixed-looking plot does not prove no relationship exists either.",
    ),
    "q-kmeans-reflection": dict(
        kind="single",
        prompt="As k increases, what happens to inertia and silhouette, and what does a higher silhouette score prove?",
        options=[
            "Inertia keeps decreasing (or staying flat) as k grows; silhouette can help compare candidate k values, but a higher score does not prove the clusters reflect a real biological or diagnostic category.",
            "Inertia always increases with k, while silhouette always decreases -- together they identify the one objectively correct k.",
            "Both inertia and silhouette increase with k, proving that more clusters are always a better scientific choice.",
        ],
        correct_index=0,
        feedback_correct="Correct: inertia (within-cluster squared distance) can only improve or stay the same as more centers are added; silhouette is useful evidence about separation, not proof of a real subtype.",
    ),
    "q-activity-kmeans": dict(
        kind="single",
        prompt="In the activity above, does increasing the number of retained components change which brain-measurement patterns feed K-means?",
        options=[
            "Yes -- K-means always clusters using every retained component you select, even though the scatter plot only ever shows PC1 and PC2.",
            "No -- K-means only ever uses PC1 and PC2, no matter how many components are retained.",
            "It depends on which external characteristic is selected for coloring.",
        ],
        correct_index=0,
        feedback_correct="Correct: the scatter plot is a 2-D window onto a higher-dimensional clustering -- retained-component count changes the actual input to K-means, while the external-characteristic selector only changes how the result is colored afterward.",
    ),
    "q-pipeline-leakage": dict(
        kind="single",
        prompt=(
            "Why must Section 5's pipeline refit StandardScaler and PCA inside "
            "every cross-validation fold, instead of reusing Section 2's "
            "pca_explore (fit once on all 1004 participants)?"
        ),
        options=[
            "pca_explore was fit using every participant, including ones that fall in a given fold's held-out validation rows -- reusing it lets information about those rows leak into preprocessing before they are ever scored, even though PCA never looks at the target.",
            "pca_explore cannot be reused because it was fit with a different number of components than Section 5 needs.",
            "There is no real difference -- reusing pca_explore would give the identical, correct cross-validation result.",
        ],
        correct_index=0,
        feedback_correct="Correct: StandardScaler/PCA must be fit on each fold's training rows only. Fitting them once on the full 1004-participant cohort first leaks every fold's own held-out rows into preprocessing -- a form of leakage that happens even though PCA never sees the target.",
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
    return code(source, "wp47-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp47-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 8: Unsupervised Learning", "wp47-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 8 of *Machine Learning for Neuroscience*. Every earlier
exercise predicted a target from labeled examples. This notebook asks a
different question: **what can we learn from brain measurements when no
target is supplied at all?**

In this notebook you will:

1. reduce many brain measurements to a smaller set of principal components,
   and examine what those components represent;
2. group participants with K-means, without using any target label;
3. explore how retained-component count and cluster count interact, in a
   live interactive activity;
4. use PCA correctly inside a supervised prediction pipeline, and see why it
   must be fit inside cross-validation, never before it.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 2 (regression) and Exercise 6 or 7 (any
tree-based exercise, for held-out validation habits).
""",
            "wp47-002-overview",
        ),
    ]


def _section_1_learning_without_a_target() -> list[dict]:
    return [
        md("## 1. Learning Without a Target", "wp47-101-header"),
        md(
            """
Every earlier exercise was **supervised**: each participant had a target
value (age, diagnosis) that a model learned to predict, and we judged
success by held-out prediction accuracy. **Unsupervised** methods receive
only the input measurements -- no target column -- and instead describe
structure that already exists in the data: a smaller set of numbers that
summarizes many related measurements, a lower-dimensional space to
visualize participants in, or groups of participants with similar
measurement profiles. Nothing here replaces held-out testing; an
unsupervised result is a starting point for a hypothesis, not a confirmed
finding.
""",
            "wp47-102-intro",
        ),
        md(
            """
> **With no target column supplied, what information is actually left for an algorithm to use when it groups or summarizes participants?**
""",
            "wp47-103-think-first",
        ),
        code(
            """
try:
    df = load_abide_age_brain_table()
    demographics = load_demographics_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_age_brain_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under "
        "'Run the cell below first') before this one, then run this cell again."
    ) from exc

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
assert len(demographics) == len(df)

print(f"data table: {df.shape[0]} participants x {len(FEATURES)} cortical-thickness predictors")
print("diagnosis, sex, site, and age are loaded now only for LATER coloring/interpretation --")
print("they never enter PCA or K-means as inputs.")
""",
            "wp47-104-load",
        ),
        code(
            """
show_question("q-unsupervised-explore")
""",
            "wp47-105-q1",
        ),
        code(
            """
show_question("q-unsupervised-info")
""",
            "wp47-106-q2",
        ),
    ]


def _section_2_pca() -> list[dict]:
    return [
        md("## 2. PCA: Representing Many Features with Fewer Dimensions", "wp47-201-header"),
        md(
            """
Principal component analysis (PCA) builds new axes -- **principal
components** -- as combinations of the original features: PC1 captures the
greatest available variance in the data; PC2 captures the greatest
*remaining* variance, subject to being orthogonal to PC1; each further
component continues the same pattern. Every participant gets a **score** on
each component; every original feature gets a **loading** -- how strongly,
and in which direction, it contributes to that component. **PCA is
dimensionality reduction and feature extraction, not feature selection**: it
never keeps a subset of the original measurements as-is -- every component
is a new combination of all of them.
""",
            "wp47-202-intro",
        ),
        md(
            f"""
### Fit PCA on the brain predictors

Standardize the 360-feature cortical-thickness table (every region is the
same unit, but regions differ in natural variability, so an unstandardized
PCA would be dominated by whichever regions happen to have the largest raw
variance), then fit PCA with `n_components={N_PCA_COMPONENTS}` and
`random_state=0`. Fit on the **brain predictors only** -- never on
diagnosis, sex, site, or age.

Required output names: `Xs` (standardized predictors), `pca_explore` (the
fitted `PCA` object), `X_pca` (the transformed participant-by-component
scores, `pca_explore.transform(Xs)`).
""",
            "wp47-203-pca-instructions",
        ),
        blank(
            f"""
# YOUR CODE HERE
# Xs = StandardScaler().fit_transform(df[FEATURES].to_numpy(float))
# pca_explore = PCA(n_components={N_PCA_COMPONENTS}, random_state=0).fit(Xs)
# X_pca = pca_explore.transform(Xs)
""",
            f"""
Xs = StandardScaler().fit_transform(df[FEATURES].to_numpy(float))
pca_explore = PCA(n_components={N_PCA_COMPONENTS}, random_state=0).fit(Xs)
X_pca = pca_explore.transform(Xs)
print(f"Xs: {{Xs.shape}}   X_pca: {{X_pca.shape}}")
print(f"PC1 explained variance = {{pca_explore.explained_variance_ratio_[0]:.1%}}")
""",
            "wp47-204-pca-blank",
            tags=["wp47-activity-pca"],
        ),
        code(
            f"""
# Run this to check your PCA fit.
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

EXPECTED_PC1_EVR = {EXPECTED_PC1_EVR}
EVR_TOLERANCE = 0.08  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("Xs", "pca_explore", "X_pca")):
    if Xs.shape != (len(df), len(FEATURES)):
        print(f"Not quite: expected Xs.shape == ({{len(df)}}, {{len(FEATURES)}}); got {{Xs.shape}}.")
    elif X_pca.shape[0] != len(df) or X_pca.shape[1] < 2:
        print("Not quite: X_pca should have one row per participant and at least 2 components.")
    elif not np.all(np.diff(pca_explore.explained_variance_ratio_) <= 1e-9):
        print("Not quite: explained_variance_ratio_ should be non-increasing (PC1 first).")
    else:
        pc1_evr = pca_explore.explained_variance_ratio_[0]
        if abs(pc1_evr - EXPECTED_PC1_EVR) <= EVR_TOLERANCE:
            print(f"Looks good: PC1 explained variance = {{pc1_evr:.1%}} (expected ~{{EXPECTED_PC1_EVR:.0%}}).")
        else:
            print(
                f"Your PC1 explained variance ({{pc1_evr:.1%}}) differs from the expected "
                f"result (~{{EXPECTED_PC1_EVR:.0%}}). That does not automatically mean something "
                "is wrong -- check that PCA was fit on standardized brain predictors only, with "
                "n_components=50 and random_state=0, before assuming this is an error."
            )
else:
    print("Not complete yet: define Xs, pca_explore, and X_pca above first.")
""",
            "wp47-205-pca-check",
        ),
        md(
            f"""
### Plot explained variance

Make a two-panel figure from your `pca_explore`:

- **left:** a bar chart of the individual explained variance ratio for
  principal components 1-15 (x-axis: PC number, y-axis: explained variance
  ratio, starting at 0);
- **right:** the *cumulative* explained variance for components 1-50 (x-axis:
  number of components retained, y-axis: cumulative explained variance as a
  percentage, starting at 0%), with a dashed horizontal line at 50% and an
  annotation marking PC1 alone.

Required output name: `pca_variance_fig`.
""",
            "wp47-206-variance-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# pca_variance_fig, axes = plt.subplots(1, 2, figsize=(11, 4))
# ...left: axes[0].bar(range(1, 16), pca_explore.explained_variance_ratio_[:15])...
# ...right: cumulative = np.cumsum(pca_explore.explained_variance_ratio_); plot PCs 1-50,
#    a dashed line at 50%, and annotate PC1's own cumulative value...
# plt.tight_layout()
# plt.show()
""",
            """
cumulative = np.cumsum(pca_explore.explained_variance_ratio_)
n_show_scree = 15
n_show_cum = min(50, len(cumulative))

pca_variance_fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].bar(range(1, n_show_scree + 1), pca_explore.explained_variance_ratio_[:n_show_scree])
axes[0].set_xlabel("Principal component")
axes[0].set_ylabel("Explained variance ratio")
axes[0].set_title(f"Scree plot (first {n_show_scree} components)")

axes[1].plot(range(1, n_show_cum + 1), cumulative[:n_show_cum] * 100, marker=".")
axes[1].scatter([1], [cumulative[0] * 100], color="crimson", zorder=5, s=40)
axes[1].annotate(
    f"PC1 alone: {cumulative[0]:.1%}",
    (1, cumulative[0] * 100),
    textcoords="offset points", xytext=(8, -10), fontsize=9, color="crimson",
)
axes[1].axhline(50, color="0.5", ls="--", lw=1)
axes[1].set_ylim(0, 100)
axes[1].yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
axes[1].set_xlabel("Number of components retained")
axes[1].set_ylabel("Cumulative explained variance")
axes[1].set_title(f"Cumulative explained variance (first {n_show_cum} components)")
plt.tight_layout()
plt.show()
""",
            "wp47-207-variance-blank",
            tags=["wp47-activity-variance"],
        ),
        code(
            f"""
# Run this to check your explained-variance figure.
EXPECTED_CUMVAR_50 = {EXPECTED_CUMVAR[50]}
CUMVAR_TOLERANCE = 0.1  # generous: absorbs reasonable implementation differences

if "pca_variance_fig" in globals():
    cum = np.cumsum(pca_explore.explained_variance_ratio_)
    cum_at_50 = cum[min(49, len(cum) - 1)]
    if not np.all(np.diff(cum) >= -1e-9):
        print("Not quite: cumulative explained variance should never decrease.")
    elif abs(cum_at_50 - EXPECTED_CUMVAR_50) <= CUMVAR_TOLERANCE:
        print(f"Looks good: cumulative explained variance through PC50 = {{cum_at_50:.1%}} (expected ~{{EXPECTED_CUMVAR_50:.0%}}).")
    else:
        print(
            f"Your cumulative explained variance through PC50 ({{cum_at_50:.1%}}) differs from "
            f"the expected result (~{{EXPECTED_CUMVAR_50:.0%}}). Check that the figure uses "
            "pca_explore's own explained_variance_ratio_ before assuming this is an error."
        )
else:
    print("Not complete yet: define pca_variance_fig above first.")
""",
            "wp47-208-variance-check",
        ),
        md(
            """
### Plot PC1 vs. PC2, colored by age

Make a scatter plot of every participant's `X_pca[:, 0]` against
`X_pca[:, 1]`, colored by **age** with a labeled, continuous colorbar, using
a **reversed sequential colormap** (for example `"viridis_r"`) so that
**brighter points are younger**. Age and every other external
characteristic are used here only to color an already-fitted plot -- never
as an input to PCA.

Required output name: `pca_scatter_fig`.
""",
            "wp47-209-scatter-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# pca_scatter_fig, ax = plt.subplots(figsize=(5.5, 5))
# scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=df["age"], cmap="viridis_r", s=8, alpha=0.6)
# ...colorbar labeled "Age (years)", axis labels, title...
# plt.tight_layout()
# plt.show()
""",
            """
pca_scatter_fig, ax = plt.subplots(figsize=(5.5, 5))
scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=df["age"], cmap="viridis_r", s=8, alpha=0.6)
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("Age (years) -- brighter = younger")
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_title("Every participant, PC1 vs. PC2, colored by age")
plt.tight_layout()
plt.show()
""",
            "wp47-210-scatter-blank",
            tags=["wp47-activity-scatter"],
        ),
        code(
            """
# Run this to check your PC1-vs-PC2 figure.
if "pca_scatter_fig" in globals():
    print("Looks good: pca_scatter_fig is defined. Visually confirm it shows every "
          "participant, colored by age with a labeled colorbar (brighter = younger).")
else:
    print("Not complete yet: define pca_scatter_fig above first.")
""",
            "wp47-211-scatter-check",
        ),
        md(
            """
Try re-coloring the same `X_pca[:, 0]`/`X_pca[:, 1]` scatter by diagnosis,
sex, or acquisition site instead -- all **categorical**, so a discrete
legend fits better than a continuous colorbar. Site has many levels; a
qualitative colormap (for example `"tab20"`) and a compact legend keep this
readable.
""",
            "wp47-212-scatter-alt-colors-intro",
        ),
        code(
            """
# Supplied: an example of re-coloring by a categorical characteristic
# (diagnosis here) -- not graded, just a pattern to reuse for sex/site.
if "X_pca" in globals():
    fig, ax = plt.subplots(figsize=(5.5, 5))
    group_labels = {1: "Autism", 2: "Control"}
    for group_value, label in group_labels.items():
        mask = (df["group"] == group_value).to_numpy()
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1], s=8, alpha=0.5, label=label)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Every participant, PC1 vs. PC2, colored by diagnosis")
    ax.legend(fontsize=8, markerscale=2)
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: complete the PCA task above first (X_pca is not defined).")
""",
            "wp47-212b-scatter-alt-colors",
        ),
        code(
            """
show_question("q-pca-separation")
""",
            "wp47-213-q-separation",
        ),
        md(
            """
### Inspect loadings on PC1 and PC2

For each of PC1 and PC2, plot the region names with the strongest (most
positive and most negative, or simply largest absolute value) loading --
preserving the sign of each loading, not just its magnitude. (PCA loading
signs can flip between runs or implementations without changing the
underlying solution; a flipped sign on every loading in a component is not
an error.) Avoid declaring any individual region causal or diagnostic from
this alone.

Required output name: `pca_loadings_fig`.
""",
            "wp47-214-loadings-instructions",
        ),
        blank(
            f"""
N_TOP = {N_TOP_LOADINGS}

# YOUR CODE HERE
# loadings = pca_explore.components_  # (n_components, 360)
# pca_loadings_fig, axes = plt.subplots(1, 2, figsize=(11, 4))
# ...for each of PC1 (loadings[0]) and PC2 (loadings[1]): find the N_TOP
#    largest-|loading| features, plot a horizontal bar chart preserving sign...
# plt.tight_layout()
# plt.show()
""",
            f"""
N_TOP = {N_TOP_LOADINGS}

loadings = pca_explore.components_  # (n_components, 360)
pca_loadings_fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for i, ax in enumerate(axes):
    order = np.argsort(-np.abs(loadings[i]))[:N_TOP]
    labels = [FEATURES[j].replace("fsCT_", "").replace("_ROI", "") for j in order]
    values = loadings[i][order]
    colors = ["#4c72b0" if v > 0 else "#c44e52" for v in values]
    ax.barh(range(N_TOP), values[::-1], color=colors[::-1])
    ax.set_yticks(range(N_TOP))
    ax.set_yticklabels(labels[::-1], fontsize=8)
    ax.set_xlabel("Loading")
    ax.set_title(f"Strongest individual regions, PC{{i + 1}}")
    ax.axvline(0, color="0.6", lw=0.8)
plt.tight_layout()
plt.show()
""",
            "wp47-215-loadings-blank",
            tags=["wp47-activity-loadings"],
        ),
        code(
            f"""
# Run this to check your loadings figure.
if "pca_loadings_fig" in globals():
    if "N_TOP" in globals() and 5 <= N_TOP <= 15:
        print(f"Looks good: pca_loadings_fig is defined, showing the top {{N_TOP}} regions per component.")
    else:
        print("Looks good: pca_loadings_fig is defined.")
else:
    print("Not complete yet: define pca_loadings_fig above first.")
""",
            "wp47-216-loadings-check",
        ),
        md(
            """
A few questions worth sitting with before moving on: does PC1 describe a
global cortical-thickness pattern, or a more regional one? Can a component
with less explained variance than PC1 still be scientifically useful? What
information is hidden when 360 dimensions are shown using only PC1 and PC2?
""",
            "wp47-217-loadings-note",
        ),
    ]


def _section_3_kmeans() -> list[dict]:
    return [
        md("## 3. K-Means on Your PCA Result", "wp47-301-header"),
        md(
            """
**Clustering** groups observations so that members of the same group are
more similar to each other than to members of other groups -- without using
any target label. **K-means** repeats four steps: (1) initialize `k` cluster
centers; (2) assign each participant to its nearest center; (3) update each
center to the mean of the participants currently assigned to it; (4) repeat
2-3 until assignments stop changing. K-means minimizes the sum of squared
distances from each participant to its assigned center -- it does not
discover a guaranteed biological truth. There is often **no single
objectively correct `k`**: inertia (what K-means minimizes) always decreases
as `k` grows, so look for where adding another cluster stops helping much;
silhouette score describes how well-separated clusters are, on a scale from
-1 to 1, but a higher score alone **does not establish a biological
subtype** -- it only describes how cleanly the chosen features separate into
groups.
""",
            "wp47-302-intro",
        ),
        code(
            f"""
# Supplied: a small, fixed choice of how many retained components and
# candidate cluster counts to try -- sliced directly from your own X_pca,
# never by fitting a new, separate PCA.
N_CLUSTER_COMPONENTS = {N_CLUSTER_COMPONENTS}
K_CANDIDATES = {K_CANDIDATES!r}
""",
            "wp47-303-constants",
        ),
        md(
            f"""
Fit `KMeans` once per entry of `K_CANDIDATES`, on
`X_pca[:, :N_CLUSTER_COMPONENTS]` (an explicit `n_init` and fixed
`random_state`, for reproducibility -- use `n_init=10, random_state=0`).
Record each `k`'s inertia; record silhouette score too, **except for k=1**,
where silhouette is not defined. Plot inertia vs. `k` and silhouette vs. `k`
in two separate figures.

Required output names: `kmeans_results` (a list of dicts, one per entry of
`K_CANDIDATES`, each `{{"k": k, "inertia": ..., "silhouette": ... or None}}`),
`kmeans_inertia_fig`, `kmeans_silhouette_fig`.
""",
            "wp47-304-kmeans-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# cluster_X = X_pca[:, :N_CLUSTER_COMPONENTS]
# kmeans_results = []
# for k in K_CANDIDATES:
#     km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(cluster_X)
#     sil = silhouette_score(cluster_X, km.labels_) if k >= 2 else None
#     kmeans_results.append({"k": k, "inertia": km.inertia_, "silhouette": sil})
#
# kmeans_inertia_fig, ax = plt.subplots()
# ...plot inertia against k from kmeans_results...
# plt.show()
#
# kmeans_silhouette_fig, ax = plt.subplots()
# ...plot silhouette against k from kmeans_results, skipping k=1...
# plt.show()
""",
            """
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

cluster_X = X_pca[:, :N_CLUSTER_COMPONENTS]
kmeans_results = []
for k in K_CANDIDATES:
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(cluster_X)
    sil = float(silhouette_score(cluster_X, km.labels_)) if k >= 2 else None
    kmeans_results.append({"k": k, "inertia": float(km.inertia_), "silhouette": sil})

kmeans_inertia_fig, ax = plt.subplots(figsize=(5.2, 3.6))
ax.plot([r["k"] for r in kmeans_results], [r["inertia"] for r in kmeans_results], marker="o")
ax.set_xlabel("k (number of clusters)")
ax.set_ylabel("Inertia")
ax.set_title(f"Inertia vs. k (first {N_CLUSTER_COMPONENTS} components)")
plt.tight_layout()
plt.show()

sil_results = [r for r in kmeans_results if r["silhouette"] is not None]
kmeans_silhouette_fig, ax = plt.subplots(figsize=(5.2, 3.6))
ax.plot([r["k"] for r in sil_results], [r["silhouette"] for r in sil_results], marker="o", color="tab:orange")
ax.set_xlabel("k (number of clusters)")
ax.set_ylabel("Silhouette score")
ax.set_title("Silhouette vs. k (k=1 excluded -- undefined)")
plt.tight_layout()
plt.show()
""",
            "wp47-305-kmeans-blank",
            tags=["wp47-activity-kmeans"],
        ),
        code(
            f"""
# Run this to check your K-means results.
EXPECTED_SIL_AT_3 = {EXPECTED_KMEANS_SILHOUETTE[3]}
SIL_TOLERANCE = 0.15  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("kmeans_results", "kmeans_inertia_fig", "kmeans_silhouette_fig")):
    if len(kmeans_results) != len(K_CANDIDATES):
        print(f"Not quite: expected one result per entry of K_CANDIDATES ({{len(K_CANDIDATES)}} values).")
    elif any(r["k"] > 1 and r["silhouette"] is None for r in kmeans_results):
        print("Not quite: every k >= 2 should have a silhouette score (only k=1 should be None).")
    else:
        inertias = [r["inertia"] for r in kmeans_results]
        if not all(a >= b - 1e-6 for a, b in zip(inertias, inertias[1:])):
            print("Not quite: inertia should never increase as k grows.")
        else:
            sil_at_3 = next((r["silhouette"] for r in kmeans_results if r["k"] == 3), None)
            if sil_at_3 is not None and abs(sil_at_3 - EXPECTED_SIL_AT_3) <= SIL_TOLERANCE:
                print(f"Looks good: silhouette at k=3 = {{sil_at_3:.3f}} (expected ~{{EXPECTED_SIL_AT_3:.3f}}); inertia decreases with k.")
            else:
                print(
                    "Your results differ somewhat from the expected numbers. That does not "
                    "automatically mean something is wrong -- check that K-means was fit on "
                    "X_pca[:, :N_CLUSTER_COMPONENTS] with n_init=10, random_state=0, before "
                    "assuming this is an error."
                )
else:
    print("Not complete yet: define kmeans_results, kmeans_inertia_fig, and kmeans_silhouette_fig above first.")
""",
            "wp47-306-kmeans-check",
        ),
        code(
            """
show_question("q-kmeans-reflection")
""",
            "wp47-307-q-kmeans-reflection",
        ),
    ]


def _section_4_interactive_activity() -> list[dict]:
    seeds_literal = repr(ACTIVITY_SEEDS)
    retained_literal = repr(ACTIVITY_RETAINED_PC_GRID)
    k_literal = repr(ACTIVITY_K_GRID)
    ext_literal = repr(ACTIVITY_EXTERNAL_VARIABLES)
    return [
        md("## 4. Interactive Activity -- Explore PCA and K-Means", "wp47-401-header"),
        md(
            f"""
Choose how many principal components to retain, a number of clusters `k`,
and a seed; then pick an external characteristic to color the result by
*after* clustering. Clustering always uses **every retained component you
select**, even though the scatter plot shows only PC1 and PC2. This activity
reuses your own completed `X_pca` from Section 2 when it is available;
otherwise it falls back to an independently computed projection and says so
explicitly below.
""",
            "wp47-402-intro",
        ),
        code(
            f"""
# ---- "Explore PCA and K-Means" -- native interactive (ported from the old iframe) ----
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

_ACTIVITY_RETAINED_PC_GRID = {retained_literal}
_ACTIVITY_K_GRID = {k_literal}
_ACTIVITY_SEEDS = {seeds_literal}
_ACTIVITY_N_INIT = {ACTIVITY_N_INIT}
_ACTIVITY_EXTERNAL_VARIABLES = {ext_literal}

if "X_pca" in globals() and "pca_explore" in globals():
    _activity_scores = X_pca
    _activity_source_note = "your own completed PCA from Section 2"
else:
    _activity_Xs_fallback = StandardScaler().fit_transform(df[FEATURES].to_numpy(float))
    _activity_pca_fallback = PCA(n_components=max(_ACTIVITY_RETAINED_PC_GRID), random_state=0).fit(_activity_Xs_fallback)
    _activity_scores = _activity_pca_fallback.transform(_activity_Xs_fallback)
    _activity_source_note = "a fixed, independently computed PCA (complete Section 2's PCA task above to use your own X_pca here instead)"
print(f"This activity is using: {{_activity_source_note}}.")

_activity_external = {{
    "group": df["group"].to_numpy(),
    "sex": demographics["sex"].to_numpy(),
    "site": demographics["site"].to_numpy(),
    "age": df["age"].to_numpy(),
}}

_activity_cache = {{}}  # (retained_pc, k, seed) -> {{"labels":..., "inertia":..., "silhouette":...}}
for _retained in _ACTIVITY_RETAINED_PC_GRID:
    _sub = _activity_scores[:, :_retained]
    for _seed in _ACTIVITY_SEEDS:
        for _k in _ACTIVITY_K_GRID:
            _km = KMeans(n_clusters=_k, n_init=_ACTIVITY_N_INIT, random_state=_seed).fit(_sub)
            _sil = float(silhouette_score(_sub, _km.labels_))
            _activity_cache[(_retained, _k, _seed)] = {{
                "labels": _km.labels_,
                "inertia": float(_km.inertia_),
                "silhouette": _sil,
                "centers": _km.cluster_centers_[:, :2],
            }}

_act_retained_dd = widgets.Dropdown(options=_ACTIVITY_RETAINED_PC_GRID, value={ACTIVITY_DEFAULT_RETAINED_PC!r}, description="Retained PCs:")
_act_k_dd = widgets.Dropdown(options=_ACTIVITY_K_GRID, value={ACTIVITY_DEFAULT_K!r}, description="k:")
_act_seed_dd = widgets.Dropdown(options=_ACTIVITY_SEEDS, value={ACTIVITY_DEFAULT_SEED!r}, description="Seed:")
_act_external_dd = widgets.Dropdown(
    options=[(label, key) for key, label in _ACTIVITY_EXTERNAL_VARIABLES.items()],
    value="group",
    description="Color by:",
)
_act_output = widgets.Output()


def _act_render(_change=None):
    retained, k, seed, ext_key = _act_retained_dd.value, _act_k_dd.value, _act_seed_dd.value, _act_external_dd.value
    entry = _activity_cache[(retained, k, seed)]
    labels = entry["labels"]
    with _act_output:
        _act_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))

        axes[0].scatter(_activity_scores[:, 0], _activity_scores[:, 1], c=labels, cmap="tab10", s=8, alpha=0.6)
        axes[0].scatter(entry["centers"][:, 0], entry["centers"][:, 1], c="black", marker="x", s=60)
        axes[0].set_xlabel("PC1")
        axes[0].set_ylabel("PC2")
        axes[0].set_title(f"K-means labels (k={{k}}, {{retained}} retained PCs)")

        ext_values = _activity_external[ext_key]
        if ext_key in ("group", "sex", "site"):
            categories = sorted(set(ext_values.tolist()), key=str)
            cmap = plt.get_cmap("tab20", max(len(categories), 1))
            for i, cat in enumerate(categories):
                mask = ext_values == cat
                axes[1].scatter(_activity_scores[mask, 0], _activity_scores[mask, 1], s=8, alpha=0.6, color=cmap(i), label=str(cat))
            axes[1].legend(fontsize=6, markerscale=2, ncol=2 if len(categories) > 6 else 1)
        else:
            sc = axes[1].scatter(_activity_scores[:, 0], _activity_scores[:, 1], c=ext_values, cmap="viridis_r", s=8, alpha=0.6)
            plt.colorbar(sc, ax=axes[1], label="Age (years) -- brighter = younger")
        axes[1].set_xlabel("PC1")
        axes[1].set_ylabel("PC2")
        axes[1].set_title(f"Colored by {{_ACTIVITY_EXTERNAL_VARIABLES[ext_key]}} (after clustering)")

        inertias = [_activity_cache[(retained, kk, seed)]["inertia"] for kk in _ACTIVITY_K_GRID]
        sils = [_activity_cache[(retained, kk, seed)]["silhouette"] for kk in _ACTIVITY_K_GRID]
        ax2 = axes[2]
        ax2.plot(_ACTIVITY_K_GRID, inertias, marker="o", color="tab:blue", label="inertia")
        ax2.set_xlabel("k")
        ax2.set_ylabel("inertia", color="tab:blue")
        ax3 = ax2.twinx()
        ax3.plot(_ACTIVITY_K_GRID, sils, marker="s", color="tab:orange", label="silhouette")
        ax3.set_ylabel("silhouette", color="tab:orange")
        ax2.axvline(k, color="0.6", linestyle="--")
        ax2.set_title("Inertia and silhouette across k")
        plt.tight_layout()
        plt.show()

        sizes = {{int(c): int((labels == c).sum()) for c in range(k)}}
        print(f"retained PCs={{retained}}  k={{k}}  seed={{seed}}  cluster sizes={{sizes}}  silhouette={{entry['silhouette']:.3f}}")


_act_retained_dd.observe(_act_render, names="value")
_act_k_dd.observe(_act_render, names="value")
_act_seed_dd.observe(_act_render, names="value")
_act_external_dd.observe(_act_render, names="value")
display(widgets.VBox([widgets.HBox([_act_retained_dd, _act_k_dd, _act_seed_dd]), _act_external_dd, _act_output]))
_act_render()
""",
            "wp47-403-widget",
        ),
        md(
            """
Try comparing `k=2`, `k=3`, and a larger `k` at the same retained-component
count: does a larger `k` reveal genuinely new structure, or does it mainly
split an existing pattern into more, smaller groups? Then try coloring by
**age** -- a visible age gradient across clusters would suggest K-means may
be discretizing a continuous developmental pattern into a small number of
bins, which is not the same as discovering a natural category. **These
clusters must never be called autism subtypes** on this evidence alone;
confirming a genuine subtype would need independent replication and clinical
validation this exploratory activity does not attempt.
""",
            "wp47-404-activity-note",
        ),
        code(
            """
show_question("q-activity-kmeans")
""",
            "wp47-405-q-activity",
        ),
    ]


def _section_5_supervised_pipeline() -> list[dict]:
    component_grid_literal = repr(COMPONENT_GRID)
    k_grid_literal = repr(K_GRID)
    return [
        md("## 5. Using PCA in a Supervised Pipeline", "wp47-501-header"),
        md(
            """
K-nearest neighbours predicts a participant's age from the ages of the
training participants whose cortical-thickness profiles are closest to
theirs -- the Euclidean distance between two participants' 360 brain
measurements. In a space with hundreds of dimensions, many directions carry
little information about age, and those directions still count in every
distance calculation. PCA can replace the 360 original features with a
smaller set of component scores before KNN ever calculates a distance:

```python
Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA()),
    ("model", KNeighborsRegressor()),
])
```

PCA here is still **feature extraction, not feature selection** -- every
retained component is a combination of all 360 original measurements. The
number of retained components and `k` are both model parameters, chosen the
same way any other model parameter is chosen: by cross-validation on the
training-and-validation data only, with `StandardScaler` and `PCA` refit
inside every fold. PCA is **not guaranteed** to help KNN -- it keeps the
directions that explain the most variation in the cortical-thickness
features themselves, which were never chosen with age in mind.
""",
            "wp47-502-intro",
        ),
        md(
            """
> **Why might PCA help KNN more directly than it helps a model that does not calculate distances between participants?**
""",
            "wp47-503-think-first",
        ),
        code(
            """
from sklearn.model_selection import train_test_split, KFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

has_age = df["age"].notna()
X_full = df.loc[has_age, FEATURES].to_numpy(float)
y_full = df.loc[has_age, "age"].to_numpy(float)
groups_full = df.loc[has_age, "group"].to_numpy()

X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X_full, y_full, groups_full, test_size=0.25, random_state=42, stratify=groups_full
)
print(f"n_train (development) = {len(y_train)}   n_test = {len(y_test)} (locked; read once, below)")
""",
            "wp47-504-split",
        ),
        md(
            f"""
Supplied: the complete, leakage-safe comparison. `StandardScaler` and `PCA`
are fit **inside** the `Pipeline`, so they are refit independently on every
cross-validation fold's own training rows -- never once on Section 2's full
1004-participant `Xs`/`pca_explore`, which would leak each fold's own
held-out rows into preprocessing before they are scored. Candidate component
counts: `{COMPONENT_GRID!r}`; candidate `k` values: `{K_GRID!r}`. Every
(components, `k`) combination is scored by 5-fold cross-validation restricted
to the training-and-validation data; the identical `k` grid, under the
identical folds, also selects a standardized KNN model on the original 360
features (no PCA step), for a fair comparison. The locked test set is read
exactly once, after both selections are already fixed.
""",
            "wp47-505-pipeline-intro",
        ),
        code(
            f"""
component_grid = {component_grid_literal}
k_grid = {k_grid_literal}
cv = KFold(n_splits=5, shuffle=True, random_state={CV_RANDOM_STATE})
fold_splits = list(cv.split(X_train))

pca_knn_rows = []
for n in component_grid:
    for k in k_grid:
        fold_mse = []
        for train_idx, val_idx in fold_splits:
            pipe = Pipeline([
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=n, random_state=0)),
                ("model", KNeighborsRegressor(n_neighbors=k)),
            ])
            pipe.fit(X_train[train_idx], y_train[train_idx])
            pred = pipe.predict(X_train[val_idx])
            fold_mse.append(mean_squared_error(y_train[val_idx], pred))
        pca_knn_rows.append({{"n_components": n, "k": k, "mean_cv_mse": float(np.mean(fold_mse))}})

pca_knn_cv_df = pd.DataFrame(pca_knn_rows)
best_pca_knn = pca_knn_cv_df.loc[pca_knn_cv_df["mean_cv_mse"].idxmin()]
selected_n, selected_k = int(best_pca_knn["n_components"]), int(best_pca_knn["k"])

raw_knn_rows = []
for k in k_grid:
    fold_mse = []
    for train_idx, val_idx in fold_splits:
        pipe = Pipeline([
            ("scale", StandardScaler()),
            ("model", KNeighborsRegressor(n_neighbors=k)),
        ])
        pipe.fit(X_train[train_idx], y_train[train_idx])
        pred = pipe.predict(X_train[val_idx])
        fold_mse.append(mean_squared_error(y_train[val_idx], pred))
    raw_knn_rows.append({{"k": k, "mean_cv_mse": float(np.mean(fold_mse))}})

raw_knn_cv_df = pd.DataFrame(raw_knn_rows)
best_raw_knn = raw_knn_cv_df.loc[raw_knn_cv_df["mean_cv_mse"].idxmin()]
selected_raw_k = int(best_raw_knn["k"])

pca_knn_pipe = Pipeline([
    ("scale", StandardScaler()),
    ("pca", PCA(n_components=selected_n, random_state=0)),
    ("model", KNeighborsRegressor(n_neighbors=selected_k)),
]).fit(X_train, y_train)
pca_knn_test_pred = pca_knn_pipe.predict(X_test)
pca_knn_test_mse = mean_squared_error(y_test, pca_knn_test_pred)
pca_knn_test_r2 = r2_score(y_test, pca_knn_test_pred)

raw_knn_pipe = Pipeline([
    ("scale", StandardScaler()),
    ("model", KNeighborsRegressor(n_neighbors=selected_raw_k)),
]).fit(X_train, y_train)
raw_knn_test_pred = raw_knn_pipe.predict(X_test)
raw_knn_test_mse = mean_squared_error(y_test, raw_knn_test_pred)
raw_knn_test_r2 = r2_score(y_test, raw_knn_test_pred)

results_df = pd.DataFrame([
    {{"model": f"PCA({{selected_n}}) + KNN(k={{selected_k}})", "test_MSE": pca_knn_test_mse, "test_R2": pca_knn_test_r2}},
    {{"model": f"KNN(k={{selected_raw_k}}), 360 raw features", "test_MSE": raw_knn_test_mse, "test_R2": raw_knn_test_r2}},
])
""",
            "wp47-506-pipeline",
        ),
        code(
            """
print("cross-validation results (training-and-validation data only), best 5 of "
      f"{len(pca_knn_cv_df)} (n_components, k) combinations:")
display(pca_knn_cv_df.sort_values("mean_cv_mse").head(5).reset_index(drop=True).round(2))
print(f"\\nselected: n_components={selected_n}, k={selected_k}  "
      f"(mean CV MSE = {best_pca_knn['mean_cv_mse']:.1f})")
print(f"raw-feature KNN selected: k={selected_raw_k}  "
      f"(mean CV MSE = {best_raw_knn['mean_cv_mse']:.1f})")
print()
display(results_df.round(3))
""",
            "wp47-507-results",
        ),
        md(
            """
PCA before KNN is not a guarantee of better prediction on every dataset --
this notebook reports the observed result for this cohort and split, not a
universal rule. A few things worth remembering: fitting `StandardScaler` and
`PCA` before splitting into cross-validation folds leaks information about
validation rows into preprocessing, even though PCA never sees the target
`y`; PCA remains feature extraction, never a subset of the original
measurements; and reducing dimensionality before computing distances is a
different reason to use PCA than reducing dimensionality before fitting a
linear coefficient.
""",
            "wp47-508-takeaway",
        ),
        code(
            """
show_question("q-pipeline-leakage")
""",
            "wp47-509-q-leakage",
        ),
    ]


def _section_6_conclusion() -> list[dict]:
    return [
        md("## 6. What Should We Remember?", "wp47-601-header"),
        md(
            """
- PCA creates lower-dimensional combinations of the original features --
  never a subset of the original measurements -- and is invariant to the
  order those features happen to be stored in.
- Loadings help interpret what a component represents; preserve sign, since
  it can flip between equally valid solutions.
- K-means groups similar observations but does not prove natural or
  biological categories; a higher silhouette score is evidence, not proof.
- `k` and retained-component count are judged using quantitative evidence
  (inertia, silhouette) *and* scientific usefulness -- not one universal
  rule.
- In supervised work, `StandardScaler` and `PCA` must be fitted inside the
  cross-validation loop, never once before it, and the locked test set is
  read exactly once.

Collapsing this notebook's question-checking setup into one hidden cell
makes the question cells themselves easier to read; it is **not** secure
answer protection. This is still a fully downloadable, offline, editable
notebook, and a technically curious student can always recover an answer key
by expanding that cell or inspecting the running kernel.

### Questions to take away

1. What is the difference between feature extraction and feature selection?
2. Why must PC2 be orthogonal to PC1?
3. What does a K-means cluster center represent geometrically?
4. Could two different, equally reasonable choices of `k` both be defensible
   for the same dataset?
5. Why does fitting PCA outside a cross-validation loop leak information,
   even though PCA does not use the target?
6. Why are PCA and K-means invariant to the order the original 360 features
   are stored in, while a decision tree's chosen splits are not?
""",
            "wp47-602-summary",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_learning_without_a_target()
    section_2 = _section_2_pca()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_2]
    section_3 = _section_3_kmeans()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_3]
    cells += _section_4_interactive_activity()
    cells += _section_5_supervised_pipeline()
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
