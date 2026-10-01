#!/usr/bin/env python3
"""Generate Exercise 6's JupyterLite template, portable copy, and reference.

WP46: migrate Exercise 6 ("Decision Trees") to the same JupyterLite-native,
generator-authored architecture WP41/WP44/WP45 established for Exercises
1-5 (see WPs/reports/WP41_MAINTAINER_GUIDE.md), following
scripts/generate_exercise_05_notebook.py's exact shape.

Data: reuses the exact same same-origin export Exercises 2, 4, and 5 already
ship, book/lite/files/data/abide_age_brain.csv (360 fsCT predictors + age +
group, 1004 participants). No second, independent data export is created.
The legacy (pre-migration) canonical notebook loaded this same cohort
directly from the pinned raw ABIDE-II TSV over the network; this migration
switches it to the established same-origin file instead (matching every
other migrated exercise, and the JupyterLite no-network-dependency
requirement), which changes the natural left-to-right column order fsCT_*
columns are encountered in. This does not affect any result computed by
splitting the data at most a few times and comparing named features (single
tree, both complexity curves): those reproduce the legacy audited numbers to
4+ decimal places, verified directly against
scripts/decision_tree_model_audit_result.json before writing a line here. It
does perturb the *fair model-comparison* section (deep, order-sensitive
DecisionTreeRegressor/BaggingRegressor/RandomForestRegressor fits on all 360
features): float rounding already present in the shipped CSV (~6 significant
figures, present since Exercise 2) occasionally flips a near-tied deep split,
producing a real but small, honestly-computed difference from the legacy
numbers. See the WP46 report for the exact before/after comparison; the
numbers embedded below were verified directly against the notebook's own
data source, not copied from the legacy audit.

Numbers verified directly against book/lite/files/data/abide_age_brain.csv
before writing a single generator line:
  Section 1 single tree (SMALL_TREE_FEATURES = fsCT_L_3a_ROI, fsCT_R_2_ROI;
    max_depth=3, min_samples_leaf=20, random_state=42; n_fit=564, n_val=189):
    8 leaves, depth 3, val MSE=45.9783, val R2=0.361081 -- matches
    scripts/decision_tree_model_audit_result.json.single_tree exactly.
  Section 2 complexity curve (p=360, min_samples_leaf=5, random_state=42,
    depths 1-10, same dev split): best depth=2, val MSE=41.6389 -- matches
    the audit's complexity_curve exactly.
  Section 2 classification-depth contrast (development-only, 753 of 1004,
    251 outer-test excluded and proven disjoint, StratifiedKFold(5,
    shuffle=True, random_state=42), min_samples_leaf=5, depths 1-10): best
    depth=5, val AUC=0.5712, depth-2 AUC=0.5337, margin=0.0375 over depth 2
    -- close to but not bit-identical to the legacy audit's 0.5672/0.5337/
    0.0335 (same order-sensitivity reason as above; the depth-2 point, which
    the legacy notebook's own text also cites, matches to 4 decimals). The
    inclusion rule (depth >= 3 and margin >= 0.01) still passes, so the
    figure is still audited and kept, per WP46's explicit condition.
  Section 3 "One tree or many?" ensemble replicates: not asserted to a
    hardcoded number (the widget recomputes live from the notebook's own
    data every time it runs); sanity-checked only for the qualitative
    finding the legacy activity taught (bagging and Random Forest reduce
    variance across replicates relative to a single tree; variance falls as
    n_trees grows) -- verified true against this data source.
  Section 4 "Model comparison" (KFold(5, shuffle=True, random_state=100),
    full eligible cohort n=1004, p=360, tree_settings max_depth=6,
    min_samples_leaf=5, random_state=42; n_estimators=50; max_features=19):
    Single tree mean MSE=56.7434 R2=0.320100; Bagging mean MSE=32.7764
    R2=0.635601; Random Forest mean MSE=34.0980 R2=0.621148 -- close to but
    not bit-identical to the legacy audit's 57.4426/32.6774/34.33 for the
    same reason as the classification curve above (deep, order-sensitive
    fits); bagging still edges out Random Forest here, reported honestly,
    matching the legacy notebook's own finding.

Outputs:
  book/lite/files/exercise_06.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_06/exercise_06_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_06_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_06_reference.ipynb (--reference)

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

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_06.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_06" / "exercise_06_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_06_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_06_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 6, "templateVersion": TEMPLATE_VERSION},
}

SMALL_TREE_FEATURES = ["fsCT_L_3a_ROI", "fsCT_R_2_ROI"]
SMALL_TREE_ALIASES = {"fsCT_L_3a_ROI": "Left 3a thickness", "fsCT_R_2_ROI": "Right area 2 thickness"}
SMALL_TREE_SETTINGS = dict(max_depth=3, min_samples_leaf=20, random_state=42)

MAX_DEPTHS = list(range(1, 11))
COMPLEXITY_SETTINGS = dict(min_samples_leaf=5, random_state=42)

ENSEMBLE_TREE_SETTINGS = dict(max_depth=6, min_samples_leaf=5, random_state=42)
ENSEMBLE_N_TREES_GRID = [1, 5, 10, 25, 50, 100]
ENSEMBLE_REPLICATE_SEEDS = [0, 1, 2]
ENSEMBLE_REPLICATE_FRACTION = 0.7
RANDOM_FOREST_MAX_FEATURES = 19

FAIR_CV_RANDOM_STATE = 100
FAIR_N_ESTIMATORS = 50

GREEDY_SEED = 17
GREEDY_N = 16
GREEDY_MU, GREEDY_SD = 5.5, 2.0
GREEDY_INTERCEPT, GREEDY_BETA1, GREEDY_BETA2, GREEDY_GAMMA, GREEDY_NOISE_SD = 20.0, 6.0, 5.0, 1.5, 2.5

EXPECTED_SMALL_TREE_VAL_MSE = 45.9783
EXPECTED_COMPLEXITY_BEST_DEPTH = 2
EXPECTED_COMPLEXITY_BEST_VAL_MSE = 41.6389


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
    and group (autism/control, used both to reproduce the established
    train/test split and, in Section 2, as the classification target --
    never a regression feature).

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
# visible call like show_question("q-greedy-splitting") never prints or
# displays a correct_index/correct_indices value (WP48's "Multiple-choice
# answer visibility" requirement -- see
# scripts/generate_exercise_08_notebook.py for the pattern this mirrors).
# This is visual concealment, not secure assessment: the hidden cell is
# fully expandable, and a downloaded, fully offline, editable notebook must
# contain enough information to check an answer locally, so a technically
# curious student can always recover it from source or the running kernel.
_QUESTIONS = {
    "q-greedy-splitting": dict(
        kind="single",
        prompt="Why is this splitting procedure called 'greedy'?",
        options=[
            "Each split is chosen to minimize error at that node right now, without considering whether a different split would produce a better tree several levels later.",
            "It always produces the tree with the lowest possible training error among all possible trees.",
            "It requires more computation than trying every possible tree shape.",
        ],
        correct_index=0,
        feedback_correct="Correct: greedy splitting is locally optimal at each node, not guaranteed to be globally optimal for the whole tree.",
    ),
    "q-depth-selection": dict(
        kind="single",
        prompt="Which depth should we select before predicting the test set?",
        options=[
            "The depth that minimizes validation MSE.",
            "The depth that minimizes training MSE.",
            "The depth that minimizes test MSE, checked after trying each depth.",
        ],
        correct_index=0,
        feedback_correct="Correct: training MSE keeps falling as depth grows (it always prefers the most flexible tree), and checking the test set to choose a depth would spend it before the final, honest evaluation. If two depths tie on validation MSE, the shallower (simpler) one is the safer choice.",
    ),
    "q-bagging-forest-variance": dict(
        kind="multi",
        prompt="Which of the following correctly describe why bagging and Random Forest usually beat a single tree here?",
        options=[
            "Averaging many trees trained on different resamples reduces sensitivity to any one training sample (variance reduction).",
            "Random Forest's random feature subset at each split further decorrelates its trees, which can reduce variance beyond bagging alone.",
            "Bagging and Random Forest are guaranteed to always outperform a single tree on every dataset.",
            "A single deterministic tree, given the same training data and settings, is not sensitive to which training sample it happened to see.",
        ],
        correct_indices={0, 1},
    ),
    "q-bagging-reduces-variance": dict(
        kind="single",
        prompt="Bagging fits many trees on bootstrap resamples and averages their predictions. What does this primarily reduce?",
        options=[
            "The model's sensitivity to which particular training sample it saw (variance).",
            "The model's systematic tendency to under- or over-predict in some region, regardless of training sample (bias).",
            "The number of features the model considers.",
        ],
        correct_index=0,
        feedback_correct="Correct: averaging over resamples targets variance; it does not change what the underlying tree family can represent.",
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
        md("# Exercise 6: Decision Trees", "wp46-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 6 of *Machine Learning for Neuroscience*. It reuses
Exercise 2, 4, and 5's exact ABIDE-II age-prediction data, target, and fixed
75/25 train/test split, and introduces a model family that fits by
recursively splitting the data instead of fitting a single linear equation.

In this notebook you will:

1. fit and read a single regression tree;
2. choose a tree's depth using a validation curve, not training performance;
3. compare a single tree with bagging and Random Forest, native interactives
   included; and
4. run a fair, identical-fold comparison across all three, producing your
   own summary table.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercises 2, 4, and 5's material; comfort with `pandas`,
`numpy`, and the scikit-learn `fit` / `predict` pattern.
""",
            "wp46-002-overview",
        ),
    ]


def _section_1_one_tree() -> list[dict]:
    aliases_literal = ", ".join(f"{k!r}: {v!r}" for k, v in SMALL_TREE_ALIASES.items())
    return [
        md("## 1. One Regression Tree", "wp46-101-header"),
        md(
            """
A **regression tree** predicts a numeric target by asking a sequence of
yes/no questions about the predictors. Each internal question is a **node**;
following the answers down to an unsplit endpoint reaches a **leaf**, whose
prediction is the mean target value of the training participants who landed
there. Because a tree only ever compares one feature to a threshold at a
time, it does **not** require feature scaling -- unlike the distance-based
and penalized-regression models in Exercises 4 and 5.
""",
            "wp46-102-intro",
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

from sklearn.model_selection import train_test_split, KFold, StratifiedKFold
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, plot_tree
from sklearn.ensemble import BaggingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, roc_auc_score

FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
X = df[FEATURES].to_numpy(float)
y = df["age"].to_numpy(float)
groups = df["group"].to_numpy()  # 1 = autism, 2 = control; stratification key, and Section 2's classification target

X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=42, stratify=groups
)
X_fit, X_val, y_fit, y_val = train_test_split(
    X_train, y_train, test_size=0.25, random_state=7, stratify=groups_train
)
print(f"{len(FEATURES)} predictors")
print(f"n_fit = {len(y_fit)}   n_val = {len(y_val)}   n_test = {len(y_test)} (locked; not used in this notebook)")
""",
            "wp46-103-load",
        ),
        code(
            f"""
SMALL_TREE_FEATURES = {SMALL_TREE_FEATURES!r}
small_idx = [FEATURES.index(f) for f in SMALL_TREE_FEATURES]

small_tree = DecisionTreeRegressor(**{SMALL_TREE_SETTINGS!r})
small_tree.fit(X_fit[:, small_idx], y_fit)
small_tree_pred = small_tree.predict(X_val[:, small_idx])
small_tree_val_mse = mean_squared_error(y_val, small_tree_pred)
small_tree_val_r2 = r2_score(y_val, small_tree_pred)
print(f"leaves = {{small_tree.get_n_leaves()}}   depth = {{small_tree.get_depth()}}")
print(f"validation MSE = {{small_tree_val_mse:.1f}}   validation R2 = {{small_tree_val_r2:.3f}}")
""",
            "wp46-104-small-tree",
        ),
        md(
            """
`SMALL_TREE_FEATURES` are two cortical-thickness regions chosen ahead of
time for having the largest training-partition correlation with age within a
small anatomical bundle -- not a search across all 360 predictors. Short
display labels below are for the diagram only; the notebook's own code
always uses the real column names.
""",
            "wp46-105-aliases-note",
        ),
        code(
            f"""
SMALL_TREE_ALIASES = {{{aliases_literal}}}


def format_tree_diagram(tree, feature_names, aliases):
    \"\"\"Relabel plot_tree's default text ('X[0] <= t\\nsquared_error = ...\\n
    samples = n\\nvalue = v') with short aliases, 'Mean age =', and, for
    leaves, 'Predicted age ='.\"\"\"
    fig, ax = plt.subplots(figsize=(9, 5))
    artists = plot_tree(tree, feature_names=[aliases.get(f, f) for f in feature_names], ax=ax)
    is_leaf = tree.tree_.children_left == -1
    order = []

    def _walk(node_id):
        order.append(node_id)
        if not is_leaf[node_id]:
            _walk(tree.tree_.children_left[node_id])
            _walk(tree.tree_.children_right[node_id])

    _walk(0)
    for node_id, artist in zip(order, artists):
        n = tree.tree_.n_node_samples[node_id]
        v = tree.tree_.value[node_id][0][0]
        if is_leaf[node_id]:
            artist.set_text(f"Leaf\\nPredicted age = {{v:.1f}}\\nn = {{n}}")
        else:
            lines = artist.get_text().split("\\n")
            artist.set_text(f"{{lines[0]}}\\nMean age = {{v:.1f}}\\nn = {{n}}")
    ax.set_title("Resulting Regression Tree")
    return fig


format_tree_diagram(small_tree, SMALL_TREE_FEATURES, SMALL_TREE_ALIASES)
plt.show()
""",
            "wp46-106-diagram",
        ),
        md(
            """
### Two-dimensional partition plot

Because this tree uses only two features, its predictions can be drawn as a
map: each axis-aligned gray line is one split boundary, and the
piecewise-constant coloring in each rectangular region is that leaf's
predicted age.
""",
            "wp46-107-partition-header",
        ),
        code(
            """
def draw_partition_boundaries(tree, ax, x_range, y_range):
    \"\"\"Recursively draw each split as a line segment clipped to its own
    parent's bounding box (not the full plot), so a child split never
    overdraws past the region it actually applies to.\"\"\"
    ct = tree.tree_

    def _walk(node_id, xlo, xhi, ylo, yhi):
        if ct.children_left[node_id] == -1:
            return
        feat, thr = ct.feature[node_id], ct.threshold[node_id]
        if feat == 0:
            ax.plot([thr, thr], [ylo, yhi], color="0.4", linewidth=1)
            _walk(ct.children_left[node_id], xlo, thr, ylo, yhi)
            _walk(ct.children_right[node_id], thr, xhi, ylo, yhi)
        else:
            ax.plot([xlo, xhi], [thr, thr], color="0.4", linewidth=1)
            _walk(ct.children_left[node_id], xlo, xhi, ylo, thr)
            _walk(ct.children_right[node_id], xlo, xhi, thr, yhi)

    _walk(0, *x_range, *y_range)


x_vals = X_fit[:, small_idx[0]]
y_vals = X_fit[:, small_idx[1]]
xg, yg = np.meshgrid(
    np.linspace(x_vals.min(), x_vals.max(), 200),
    np.linspace(y_vals.min(), y_vals.max(), 200),
)
zg = small_tree.predict(np.column_stack([xg.ravel(), yg.ravel()])).reshape(xg.shape)

fig, ax = plt.subplots(figsize=(6, 5))
mesh = ax.pcolormesh(xg, yg, zg, cmap="viridis", shading="auto", alpha=0.85)
ax.scatter(x_vals, y_vals, c=y_fit, cmap="viridis", edgecolor="white", linewidth=0.3, s=18)
draw_partition_boundaries(small_tree, ax, (x_vals.min(), x_vals.max()), (y_vals.min(), y_vals.max()))
ax.set_xlabel(SMALL_TREE_ALIASES[SMALL_TREE_FEATURES[0]])
ax.set_ylabel(SMALL_TREE_ALIASES[SMALL_TREE_FEATURES[1]])
ax.set_title("Predicted age by region (piecewise constant)")
fig.colorbar(mesh, ax=ax, label="predicted age")
plt.tight_layout()
plt.show()
""",
            "wp46-108-partition",
        ),
        md(
            """
Vertical boundary segments are splits on the first feature; horizontal
segments split on the second. Predictions are constant within each
rectangle (piecewise constant), and every boundary is axis-aligned -- a tree
can never draw a diagonal decision boundary.
""",
            "wp46-109-partition-note",
        ),
        md(
            """
> **Think first:** Why must every split boundary in the plot above be
> either perfectly vertical or perfectly horizontal? What would it mean for
> a leaf to contain only one participant? Why might a very deep tree
> memorize its training participants rather than generalize?
""",
            "wp46-110-think-first",
        ),
    ]


def _section_1b_greedy_activity() -> list[dict]:
    return [
        md("## 2. Build a Tree Greedily", "wp46-201-header"),
        md(
            r"""
A tree is fit **greedily**: at each node, it picks the single split (a
feature and a threshold) that most reduces prediction error *right now*,
without looking ahead to how later splits might turn out. For a leaf
containing values $\{y_i\}$, the best constant prediction is the mean
$\bar y$, and the leaf's error is the mean squared error,
$\mathrm{MSE}=\frac1n\sum_i (y_i-\bar y)^2$. A candidate split into a left
group $L$ and right group $R$ is scored by the sample-size-weighted MSE of
its two children,
$\frac{n_L}{n}\mathrm{MSE}(L)+\frac{n_R}{n}\mathrm{MSE}(R)$ -- the split
that minimizes this weighted MSE is chosen.
""",
            "wp46-202-math",
        ),
        md(
            """
The activity below uses a small, **simulated** 16-observation dataset with
two brain measures (not real ABIDE data) so every candidate split can be
seen and compared by hand. Pick a feature and a candidate threshold, lock
your answer, then reveal the true greedy-optimal split for that node. The
activity always moves on to the next node using the true optimal split, not
your own proposal, so an early miss does not derail the rest of the walk.
""",
            "wp46-203-activity-intro",
        ),
        code(
            f"""
# ---- "Build a Tree Greedily" -- native interactive (ported from the old iframe) ----

GREEDY_SEED = {GREEDY_SEED}
GREEDY_N = {GREEDY_N}
_greedy_rng = np.random.RandomState(GREEDY_SEED)
_gx1 = _greedy_rng.normal({GREEDY_MU}, {GREEDY_SD}, GREEDY_N)
_gx2 = _greedy_rng.normal({GREEDY_MU}, {GREEDY_SD}, GREEDY_N)


def _z(v):
    return (v - v.mean()) / v.std()


_gy = (
    {GREEDY_INTERCEPT}
    + {GREEDY_BETA1} * _z(_gx1)
    + {GREEDY_BETA2} * _z(_gx2)
    + {GREEDY_GAMMA} * _z(_gx1) * _z(_gx2)
    + _greedy_rng.normal(0, {GREEDY_NOISE_SD}, {GREEDY_N})
)
GREEDY_FEATURES = {{"x1": "Brain measure 1", "x2": "Brain measure 2"}}


def _split_mse(values, mask):
    left, right = values[mask], values[~mask]
    if len(left) == 0 or len(right) == 0:
        return None
    n = len(values)
    left_mse = np.mean((left - left.mean()) ** 2)
    right_mse = np.mean((right - right.mean()) ** 2)
    return (len(left) / n) * left_mse + (len(right) / n) * right_mse


def _candidate_thresholds(values):
    ordered = np.sort(np.unique(values))
    return (ordered[:-1] + ordered[1:]) / 2


def _best_split(active_ids):
    values = {{"x1": _gx1[active_ids], "x2": _gx2[active_ids]}}
    targets = _gy[active_ids]
    parent_mse = np.mean((targets - targets.mean()) ** 2)
    best = None
    for feat in ("x1", "x2"):
        for thr in _candidate_thresholds(values[feat]):
            mse = _split_mse(targets, values[feat] <= thr)
            if mse is None:
                continue
            reduction = parent_mse - mse
            if best is None or reduction > best["reduction"]:
                best = {{"feature": feat, "threshold": thr, "splitMSE": mse, "reduction": reduction}}
    return parent_mse, best


class _GreedyState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.round = 0  # 0 = root, 1 = root's left child, 2 = root's right child
        self.active_ids = list(range(GREEDY_N))
        self.root_right_ids = None  # queued for round 2 once round 0 is accepted
        self.history = []  # accepted (feature, threshold, xlo, xhi, ylo, yhi) for drawn boundaries
        self.locked = None
        self.revealed = False


_greedy_state = _GreedyState()

_greedy_feature_dd = widgets.Dropdown(options=[("Brain measure 1", "x1"), ("Brain measure 2", "x2")], description="Feature:")
_greedy_threshold_dd = widgets.Dropdown(description="Threshold:")
_greedy_lock_btn = widgets.Button(description="Lock My Answer", button_style="primary")
_greedy_reveal_btn = widgets.Button(description="Reveal Best Split", disabled=True)
_greedy_continue_btn = widgets.Button(description="Continue to Next Node", disabled=True)
_greedy_reset_btn = widgets.Button(description="Reset Tree")
_greedy_output = widgets.Output()


def _refresh_thresholds(_change=None):
    values = _gx1[_greedy_state.active_ids] if _greedy_feature_dd.value == "x1" else _gx2[_greedy_state.active_ids]
    cands = _candidate_thresholds(values)
    _greedy_threshold_dd.options = [(f"{{t:.2f}}", t) for t in cands]


_greedy_feature_dd.observe(_refresh_thresholds, names="value")


def _greedy_render(_change=None):
    with _greedy_output:
        _greedy_output.clear_output(wait=True)
        parent_mse, optimal = _best_split(_greedy_state.active_ids)
        round_names = ["Root", "Left child", "Right child"]
        print(f"Round {{_greedy_state.round + 1}} of 3: {{round_names[_greedy_state.round]}} ({{len(_greedy_state.active_ids)}} observations, parent MSE = {{parent_mse:.2f}})")

        fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
        ax = axes[0]
        active = np.array(_greedy_state.active_ids)
        inactive = np.array([i for i in range(GREEDY_N) if i not in _greedy_state.active_ids])
        sc = ax.scatter(_gx1[active], _gx2[active], c=_gy[active], cmap="viridis", s=70, edgecolor="k")
        if len(inactive):
            ax.scatter(_gx1[inactive], _gx2[inactive], c="0.85", s=40)
        for feat, thr, xlo, xhi, ylo, yhi in _greedy_state.history:
            if feat == "x1":
                ax.plot([thr, thr], [ylo, yhi], "k--", linewidth=1)
            else:
                ax.plot([xlo, xhi], [thr, thr], "k--", linewidth=1)
        if _greedy_state.locked is not None:
            feat, thr = _greedy_state.locked
            xlo, xhi = _gx1.min() - 0.5, _gx1.max() + 0.5
            ylo, yhi = _gx2.min() - 0.5, _gx2.max() + 0.5
            if feat == "x1":
                ax.plot([thr, thr], [ylo, yhi], color="tab:orange", linewidth=2, label="your proposal")
            else:
                ax.plot([xlo, xhi], [thr, thr], color="tab:orange", linewidth=2, label="your proposal")
        if _greedy_state.revealed:
            feat, thr = optimal["feature"], optimal["threshold"]
            xlo, xhi = _gx1.min() - 0.5, _gx1.max() + 0.5
            ylo, yhi = _gx2.min() - 0.5, _gx2.max() + 0.5
            if feat == "x1":
                ax.plot([thr, thr], [ylo, yhi], color="tab:green", linewidth=2, linestyle=":", label="greedy optimum")
            else:
                ax.plot([xlo, xhi], [thr, thr], color="tab:green", linewidth=2, linestyle=":", label="greedy optimum")
        ax.set_xlabel(GREEDY_FEATURES["x1"])
        ax.set_ylabel(GREEDY_FEATURES["x2"])
        ax.legend(fontsize=7, loc="best")
        fig.colorbar(sc, ax=ax, label="target value")

        ax2 = axes[1]
        values = _gx1[active] if _greedy_feature_dd.value == "x1" else _gx2[active]
        cands = _candidate_thresholds(values)
        scores = [_split_mse(_gy[active], values <= t) for t in cands]
        colors = ["tab:orange" if _greedy_state.locked == (_greedy_feature_dd.value, t) else "0.6" for t in cands]
        if _greedy_state.revealed and optimal["feature"] == _greedy_feature_dd.value:
            colors = [
                "tab:green" if abs(t - optimal["threshold"]) < 1e-9 else c
                for t, c in zip(cands, colors)
            ]
        ax2.bar(range(len(cands)), scores, color=colors)
        ax2.set_xticks([])
        ax2.set_ylabel("weighted split MSE")
        ax2.set_title(f"Candidate thresholds: {{GREEDY_FEATURES[_greedy_feature_dd.value]}}")
        plt.tight_layout()
        plt.show()

        if _greedy_state.locked is not None:
            feat, thr = _greedy_state.locked
            your_mse = _split_mse(_gy[active], (_gx1[active] if feat == "x1" else _gx2[active]) <= thr)
            your_reduction = parent_mse - your_mse
            print(f"Your proposal: split {{GREEDY_FEATURES[feat]}} <= {{thr:.2f}}   split MSE = {{your_mse:.2f}}   reduction = {{your_reduction:.2f}}")
        if _greedy_state.revealed:
            print(
                f"Greedy optimum: split {{GREEDY_FEATURES[optimal['feature']]}} <= {{optimal['threshold']:.2f}}   "
                f"split MSE = {{optimal['splitMSE']:.2f}}   reduction = {{optimal['reduction']:.2f}}"
            )
            left_mask = (_gx1[active] if optimal["feature"] == "x1" else _gx2[active]) <= optimal["threshold"]
            print(
                f"Left child: n={{int(left_mask.sum())}}, mean={{_gy[active][left_mask].mean():.1f}}   "
                f"Right child: n={{int((~left_mask).sum())}}, mean={{_gy[active][~left_mask].mean():.1f}}"
            )


def _on_lock(_btn):
    _greedy_state.locked = (_greedy_feature_dd.value, _greedy_threshold_dd.value)
    _greedy_state.revealed = False
    _greedy_reveal_btn.disabled = False
    _greedy_continue_btn.disabled = True
    _greedy_render()


def _on_reveal(_btn):
    _greedy_state.revealed = True
    _greedy_continue_btn.disabled = _greedy_state.round >= 2
    _greedy_render()


def _on_continue(_btn):
    if _greedy_state.round >= 2:
        return
    _, optimal = _best_split(_greedy_state.active_ids)
    active = np.array(_greedy_state.active_ids)
    xlo, xhi = _gx1.min() - 0.5, _gx1.max() + 0.5
    ylo, yhi = _gx2.min() - 0.5, _gx2.max() + 0.5
    _greedy_state.history.append((optimal["feature"], optimal["threshold"], xlo, xhi, ylo, yhi))
    mask = (_gx1[active] if optimal["feature"] == "x1" else _gx2[active]) <= optimal["threshold"]
    if _greedy_state.round == 0:
        # Root split accepted: queue its right child for round 2, and
        # descend into its left child now (root, left-child, right-child --
        # not a further split of the left child).
        _greedy_state.root_right_ids = list(active[~mask])
        _greedy_state.active_ids = list(active[mask])
    else:
        _greedy_state.active_ids = _greedy_state.root_right_ids
    _greedy_state.round += 1
    _greedy_state.locked = None
    _greedy_state.revealed = False
    _greedy_reveal_btn.disabled = True
    _greedy_continue_btn.disabled = True
    _refresh_thresholds()
    _greedy_render()


def _on_reset(_btn):
    _greedy_state.reset()
    _greedy_reveal_btn.disabled = True
    _greedy_continue_btn.disabled = True
    _refresh_thresholds()
    _greedy_render()


_greedy_lock_btn.on_click(_on_lock)
_greedy_reveal_btn.on_click(_on_reveal)
_greedy_continue_btn.on_click(_on_continue)
_greedy_reset_btn.on_click(_on_reset)
_refresh_thresholds()
display(widgets.VBox([
    widgets.HBox([_greedy_feature_dd, _greedy_threshold_dd]),
    widgets.HBox([_greedy_lock_btn, _greedy_reveal_btn, _greedy_continue_btn, _greedy_reset_btn]),
    _greedy_output,
]))
_greedy_render()
""",
            "wp46-204-greedy-widget",
        ),
        md(
            "> **Did your proposed split ever match the greedy optimum exactly, and why does a tree never reconsider a split once it moves to the next node?**",
            "wp46-205-reflection",
        ),
        code(
            """
show_question("q-greedy-splitting")
""",
            "wp46-206-checked",
        ),
    ]


def _section_2_how_large() -> list[dict]:
    return [
        md("## 3. How Large Should the Tree Be?", "wp46-301-header"),
        md(
            """
| Hyperparameter | Effect of increasing it |
| --- | --- |
| `max_depth` | Allows more splits; more flexible, more overfitting risk |
| `min_samples_leaf` | Forces larger, more stable leaves; less flexible |
| `ccp_alpha` | Prunes weak splits after fitting; larger values give smaller trees |

As in Exercise 4, the right amount of flexibility is chosen by comparing
**training** and **validation** error across a range of settings, using the
validation partition -- never the locked test set.
""",
            "wp46-302-table",
        ),
        code(
            f"""
MAX_DEPTHS = {MAX_DEPTHS!r}
""",
            "wp46-303-depths",
        ),
        md(
            f"""
Fit one `DecisionTreeRegressor(max_depth=d, {', '.join(f'{k}={v!r}' for k, v in COMPLEXITY_SETTINGS.items())})`
per depth in `MAX_DEPTHS`, on `X_fit`/`y_fit`, and record both its training
MSE (on `X_fit`/`y_fit`) and its validation MSE (on `X_val`/`y_val`). Then
plot both curves against depth on the same axes.

Required output names: `tree_depth_train_mse`, `tree_depth_val_mse` (one
value per entry of `MAX_DEPTHS`, in the same order), `tree_depth_fig` (the
resulting Matplotlib figure).
""",
            "wp46-304-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# tree_depth_train_mse = []
# tree_depth_val_mse = []
# for d in MAX_DEPTHS:
#     t = DecisionTreeRegressor(max_depth=d, min_samples_leaf=5, random_state=42)
#     ...fit on X_fit/y_fit, score train and validation MSE, append both...
#
# tree_depth_fig, ax = plt.subplots()
# ...plot tree_depth_train_mse and tree_depth_val_mse against MAX_DEPTHS, with a legend...
# plt.show()
""",
            """
tree_depth_train_mse = []
tree_depth_val_mse = []
for d in MAX_DEPTHS:
    t = DecisionTreeRegressor(max_depth=d, min_samples_leaf=5, random_state=42)
    t.fit(X_fit, y_fit)
    tree_depth_train_mse.append(mean_squared_error(y_fit, t.predict(X_fit)))
    tree_depth_val_mse.append(mean_squared_error(y_val, t.predict(X_val)))

tree_depth_fig, ax = plt.subplots(figsize=(5.6, 3.6))
ax.plot(MAX_DEPTHS, tree_depth_train_mse, marker="o", label="training MSE")
ax.plot(MAX_DEPTHS, tree_depth_val_mse, marker="o", label="validation MSE")
ax.set_xlabel("max_depth")
ax.set_ylabel("MSE (years$^2$)")
ax.set_title("Training and validation MSE vs. tree depth")
ax.legend()
plt.tight_layout()
plt.show()
""",
            "wp46-305-blank",
            tags=["wp46-activity-depth"],
        ),
        code(
            f"""
# Run this to check your depth-sweep results.
EXPECTED_BEST_DEPTH = {EXPECTED_COMPLEXITY_BEST_DEPTH}
EXPECTED_BEST_VAL_MSE = {EXPECTED_COMPLEXITY_BEST_VAL_MSE}
DEPTH_MSE_TOLERANCE = 8.0  # generous: absorbs reasonable implementation differences

if all(name in globals() for name in ("tree_depth_train_mse", "tree_depth_val_mse")):
    if len(tree_depth_train_mse) != len(MAX_DEPTHS) or len(tree_depth_val_mse) != len(MAX_DEPTHS):
        print(f"Not quite: expected one value per entry of MAX_DEPTHS ({{len(MAX_DEPTHS)}} depths).")
    elif not (np.all(np.isfinite(tree_depth_train_mse)) and np.all(np.isfinite(tree_depth_val_mse))):
        print("Not quite: every MSE should be a finite number.")
    elif np.any(np.array(tree_depth_train_mse) < 0) or np.any(np.array(tree_depth_val_mse) < 0):
        print("Not quite: MSE cannot be negative.")
    else:
        best_i = int(np.argmin(tree_depth_val_mse))
        best_depth = MAX_DEPTHS[best_i]
        best_val = tree_depth_val_mse[best_i]
        if abs(best_val - EXPECTED_BEST_VAL_MSE) <= DEPTH_MSE_TOLERANCE:
            print(f"Looks good: best depth by validation MSE = {{best_depth}} (MSE = {{best_val:.1f}}, expected ~{{EXPECTED_BEST_VAL_MSE:.1f}} at depth {{EXPECTED_BEST_DEPTH}}).")
        else:
            print(
                f"Your best validation MSE ({{best_val:.1f}} at depth {{best_depth}}) differs from the expected "
                f"result (~{{EXPECTED_BEST_VAL_MSE:.1f}} at depth {{EXPECTED_BEST_DEPTH}}). That does not "
                "automatically mean something is wrong -- check that each tree was fit on X_fit/y_fit and "
                "scored on X_fit/y_fit (train) and X_val/y_val (validation) before assuming this is an error."
            )
else:
    print("Not complete yet: define tree_depth_train_mse and tree_depth_val_mse above first.")
""",
            "wp46-306-check",
        ),
        code(
            """
show_question("q-depth-selection")
""",
            "wp46-307-checked",
        ),
        md(
            """
Once a depth is selected this way, a common next step is to refit a tree at
that depth on the *combined* training-and-validation data before the one
final test evaluation -- using every available development participant for
the final fit, now that the depth decision no longer depends on holding any
of them out. This notebook does not require that extra refit; it is
mentioned here because you will see the same pattern, made explicit, in
Exercise 7's complete pipeline.
""",
            "wp46-308-refit-note",
        ),
        md(
            """
### A second look: does the same pattern hold for a different task?

The curve above chooses tree depth to predict **age** (a continuous value,
scored by MSE, lower is better). The cell below asks the same
"how much depth helps" question for a *different* task on the same brain
measurements -- classifying autism versus control (a category, scored by
ROC AUC, higher is better) -- using only the 753 development participants
Exercise 3 trained on; the 251 locked outer-test participants are excluded
and proven so below.
""",
            "wp46-309-classification-intro",
        ),
        code(
            """
y_eligible = (groups == 1).astype(int)  # 1 = autism, 0 = control
subjects_eligible = np.arange(len(df))
dev_pos, test_pos, y_cls_dev, y_cls_test = train_test_split(
    subjects_eligible, y_eligible, test_size=0.25, random_state=42, stratify=y_eligible
)
dev_pos = np.sort(dev_pos)
test_pos = np.sort(test_pos)
dev_subjects, test_subjects = set(dev_pos.tolist()), set(test_pos.tolist())
assert dev_subjects.isdisjoint(test_subjects)
assert dev_subjects | test_subjects == set(subjects_eligible.tolist())
print(f"eligible = {len(subjects_eligible)}   development = {len(dev_pos)}   outer test (excluded) = {len(test_pos)}")

X_cls, y_cls = X[dev_pos], y_eligible[dev_pos]
cls_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cls_val_auc = []
for d in MAX_DEPTHS:
    fold_auc = []
    for tr, va in cls_cv.split(X_cls, y_cls):
        clf = DecisionTreeClassifier(max_depth=d, min_samples_leaf=5, random_state=42).fit(X_cls[tr], y_cls[tr])
        fold_auc.append(roc_auc_score(y_cls[va], clf.predict_proba(X_cls[va])[:, 1]))
    cls_val_auc.append(np.mean(fold_auc))

best_cls_i = int(np.argmax(cls_val_auc))
print(f"best depth = {MAX_DEPTHS[best_cls_i]}   best validation AUC = {cls_val_auc[best_cls_i]:.3f}   depth-2 AUC = {cls_val_auc[1]:.3f}")

fig, ax = plt.subplots(figsize=(5.6, 3.6))
ax.plot(MAX_DEPTHS, cls_val_auc, marker="o", color="tab:purple")
ax.set_xlabel("max_depth")
ax.set_ylabel("validation ROC AUC (higher is better)")
ax.set_title("Classification: predicting autism diagnosis (development data only)")
plt.tight_layout()
plt.show()
""",
            "wp46-310-classification",
        ),
        md(
            """
This second curve uses a different scoring rule (ROC AUC, higher is
better) than the first (MSE, lower is better) -- do not compare the two
curves' numeric values directly. A depth that helps one task is not
guaranteed to help the other. Both AUC values here are close to 0.5
(chance), so this contrast illustrates the *pattern* of a validation curve
on a harder problem, and does **not** mean classifying autism is inherently
more (or less) complex than predicting age.
""",
            "wp46-311-classification-note",
        ),
    ]


def _section_3_ensemble() -> list[dict]:
    return [
        md("## 4. From One Tree to an Ensemble", "wp46-401-header"),
        md(
            r"""
A single tree can be sensitive to exactly which participants it was trained
on. The cell below fits the same tree settings on three different random
70%-without-replacement subsamples of the fitting partition and prints each
one's root split -- a different sample can pick a different first question
entirely.
""",
            "wp46-402-sensitivity-intro",
        ),
        code(
            f"""
for seed in (0, 1, 2):
    sub_idx = np.random.RandomState(seed).choice(len(X_fit), size=round({ENSEMBLE_REPLICATE_FRACTION} * len(X_fit)), replace=False)
    t = DecisionTreeRegressor(**{ENSEMBLE_TREE_SETTINGS!r}).fit(X_fit[sub_idx], y_fit[sub_idx])
    root_feature = FEATURES[t.tree_.feature[0]]
    print(f"seed {{seed}}: root split on {{root_feature}} <= {{t.tree_.threshold[0]:.3f}}")
""",
            "wp46-403-sensitivity",
        ),
        md(
            r"""
A single tree is **deterministic given its training data** -- what varies
above is the training sample itself. **Bagging** (bootstrap aggregating)
fits many trees, each on its own bootstrap resample of the training data,
and averages their predictions:
$\hat y_{\text{bagging}}=\frac1B\sum_{b=1}^{B}\hat y^{(b)}$. **Random
Forest** adds a second source of randomness: at every split, each tree may
only consider a random subset of features, which decorrelates the trees
further.

| Method | How trees are trained | Features considered per split | Combined prediction |
| --- | --- | --- | --- |
| Single tree | One training sample | All available features | One tree |
| Bagging | Bootstrap sample per tree | All available features | Average |
| Random Forest | Bootstrap sample per tree | Random feature subset | Average |
""",
            "wp46-404-bagging-explain",
        ),
        md("## 5. One Tree or Many?", "wp46-501-header"),
        md(
            """
> **Think first:** Averaging many trees reduces *variance* (sensitivity to
> the training sample). Does it also reduce *bias* (a tree family's
> systematic tendency to under- or over-predict in some region)? Why might
> bagging and Random Forest perform similarly here, or differently?
""",
            "wp46-502-think-first",
        ),
        code(
            f"""
# ---- "One tree or many?" -- native interactive (ported from the old iframe) ----
# Every model in a replicate trains on the identical 70%-without-replacement
# subsample of the fitting partition and is scored on the identical fixed
# validation partition; the whole (replicate x n_trees) grid is computed
# once here and cached, so the controls below only look up and redraw --
# they never refit anything.

_ENS_N_TREES_GRID = {ENSEMBLE_N_TREES_GRID!r}
_ens_replicate_seeds = {ENSEMBLE_REPLICATE_SEEDS!r}
_ens_cache = {{}}  # (seed, n_trees) -> {{"single": mse, "bagging": mse, "random_forest": mse}}

for _seed in _ens_replicate_seeds:
    _sub_idx = np.random.RandomState(_seed).choice(
        len(X_fit), size=round({ENSEMBLE_REPLICATE_FRACTION} * len(X_fit)), replace=False
    )
    _Xs, _ys = X_fit[_sub_idx], y_fit[_sub_idx]
    _single_pred = DecisionTreeRegressor(**{ENSEMBLE_TREE_SETTINGS!r}).fit(_Xs, _ys).predict(X_val)
    _single_mse = mean_squared_error(y_val, _single_pred)
    for _n in _ENS_N_TREES_GRID:
        _bag = BaggingRegressor(
            DecisionTreeRegressor(**{ENSEMBLE_TREE_SETTINGS!r}), n_estimators=_n, random_state=42
        ).fit(_Xs, _ys)
        _rf = RandomForestRegressor(
            n_estimators=_n, max_features={RANDOM_FOREST_MAX_FEATURES}, **{ENSEMBLE_TREE_SETTINGS!r}
        ).fit(_Xs, _ys)
        _ens_cache[(_seed, _n)] = {{
            "single": _single_mse,
            "bagging": mean_squared_error(y_val, _bag.predict(X_val)),
            "random_forest": mean_squared_error(y_val, _rf.predict(X_val)),
        }}

_ens_ntrees_dd = widgets.Dropdown(options=_ENS_N_TREES_GRID, value=_ENS_N_TREES_GRID[-2], description="Number of trees:")
_ens_output = widgets.Output()


def _ens_render(_change=None):
    n = _ens_ntrees_dd.value
    with _ens_output:
        _ens_output.clear_output(wait=True)
        singles = [_ens_cache[(s, n)]["single"] for s in _ens_replicate_seeds]
        baggings = [_ens_cache[(s, n)]["bagging"] for s in _ens_replicate_seeds]
        forests = [_ens_cache[(s, n)]["random_forest"] for s in _ens_replicate_seeds]
        summary = pd.DataFrame(
            {{
                "model": ["Single tree", "Bagging", "Random Forest"],
                "mean_val_mse": [np.mean(singles), np.mean(baggings), np.mean(forests)],
                "sd_across_replicates": [np.std(singles), np.std(baggings), np.std(forests)],
            }}
        ).set_index("model")
        display(summary.round(2))

        fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.6))
        ax = axes[0]
        ax.boxplot([singles, baggings, forests], tick_labels=["Single", "Bagging", "Random\\nForest"])
        ax.set_ylabel("MSE (years$^2$)")
        ax.set_title(f"Validation MSE across {{len(_ens_replicate_seeds)}} replicates (n_trees={{n}})")

        ax2 = axes[1]
        bag_means = [np.mean([_ens_cache[(s, m)]["bagging"] for s in _ens_replicate_seeds]) for m in _ENS_N_TREES_GRID]
        rf_means = [np.mean([_ens_cache[(s, m)]["random_forest"] for s in _ens_replicate_seeds]) for m in _ENS_N_TREES_GRID]
        single_mean = np.mean([_ens_cache[(s, _ENS_N_TREES_GRID[0])]["single"] for s in _ens_replicate_seeds])
        ax2.plot(_ENS_N_TREES_GRID, bag_means, marker="o", label="Bagging")
        ax2.plot(_ENS_N_TREES_GRID, rf_means, marker="o", label="Random Forest")
        ax2.axhline(single_mean, color="0.4", linestyle="--", label="Single tree (fixed)")
        ax2.set_xscale("log")
        ax2.set_xlabel("number of trees")
        ax2.set_ylabel("MSE (years$^2$)")
        ax2.set_title("Effect of ensemble size")
        ax2.legend(fontsize=8)
        plt.tight_layout()
        plt.show()
        print(f"number of trees = {{n}}   bagging mean MSE = {{np.mean(baggings):.1f}}   Random Forest mean MSE = {{np.mean(forests):.1f}}")


_ens_ntrees_dd.observe(_ens_render, names="value")
display(widgets.VBox([_ens_ntrees_dd, _ens_output]))
_ens_render()
""",
            "wp46-503-ensemble-widget",
        ),
        md(
            "> **As you change the number of trees, does the single-tree line move, and at which point does adding more trees stop visibly helping?**",
            "wp46-504-reflection",
        ),
        code(
            """
show_question("q-bagging-forest-variance")
""",
            "wp46-505-checked",
        ),
    ]


def _section_4_comparison() -> list[dict]:
    return [
        md("## 6. Model Comparison", "wp46-601-header"),
        md(
            f"""
A fair comparison across model families uses **identical cross-validation
folds** for every model, and fixes each model's complexity settings in
advance (no tuning on these same folds). None of the three models below
needs feature scaling, unlike Exercise 4's `KNeighborsRegressor` example.

Using `KFold(n_splits=5, shuffle=True, random_state={FAIR_CV_RANDOM_STATE})`
on the full cohort (`X`, `y`, all 1004 participants), fit
`DecisionTreeRegressor(**tree_settings)`,
`BaggingRegressor(DecisionTreeRegressor(**tree_settings), n_estimators={FAIR_N_ESTIMATORS}, random_state=42)`,
and
`RandomForestRegressor(n_estimators={FAIR_N_ESTIMATORS}, max_features={RANDOM_FOREST_MAX_FEATURES}, **tree_settings)`
(`tree_settings = {ENSEMBLE_TREE_SETTINGS!r}`) on the *same* fold splits --
compute each model's fold splits from one shared `cv.split(X)` call, not a
fresh `cross_val_score` per model, so every model sees exactly the same
five train/validation partitions. Collect each model's per-fold MSE and R^2.

Required output name: `tree_cv_fold_results` -- a dict keyed by model name,
each value a dict with `"mse"` and `"r2"` lists (one entry per fold, in
fold order). A supplied cell below uses it to build `tree_cv_summary`, a
readable table of means and spreads.
""",
            "wp46-602-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# cv = KFold(n_splits=5, shuffle=True, random_state=100)
# tree_settings = dict(max_depth=6, min_samples_leaf=5, random_state=42)
# models = {
#     "Single tree": DecisionTreeRegressor(**tree_settings),
#     "Bagging": BaggingRegressor(DecisionTreeRegressor(**tree_settings), n_estimators=50, random_state=42),
#     "Random Forest": RandomForestRegressor(n_estimators=50, max_features=19, **tree_settings),
# }
# tree_cv_fold_results = {name: {"mse": [], "r2": []} for name in models}
# for train_idx, val_idx in cv.split(X):
#     ...fit each model on X[train_idx]/y[train_idx], predict X[val_idx],
#     ...append mean_squared_error(...) and r2_score(...) to tree_cv_fold_results[name]
""",
            """
cv = KFold(n_splits=5, shuffle=True, random_state=100)
tree_settings = dict(max_depth=6, min_samples_leaf=5, random_state=42)
models = {
    "Single tree": DecisionTreeRegressor(**tree_settings),
    "Bagging": BaggingRegressor(DecisionTreeRegressor(**tree_settings), n_estimators=50, random_state=42),
    "Random Forest": RandomForestRegressor(n_estimators=50, max_features=19, **tree_settings),
}
tree_cv_fold_results = {name: {"mse": [], "r2": []} for name in models}
for train_idx, val_idx in cv.split(X):
    X_tr, X_va = X[train_idx], X[val_idx]
    y_tr, y_va = y[train_idx], y[val_idx]
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_va)
        tree_cv_fold_results[name]["mse"].append(mean_squared_error(y_va, pred))
        tree_cv_fold_results[name]["r2"].append(r2_score(y_va, pred))
print({name: round(float(np.mean(v["mse"])), 2) for name, v in tree_cv_fold_results.items()})
""",
            "wp46-603-blank",
            tags=["wp46-activity-comparison"],
        ),
        code(
            """
# Run this to check your model-comparison results.
if "tree_cv_fold_results" in globals():
    if set(tree_cv_fold_results) != {"Single tree", "Bagging", "Random Forest"}:
        print(f"Not quite: expected keys 'Single tree', 'Bagging', 'Random Forest'; got {sorted(tree_cv_fold_results)}.")
    elif any(len(v["mse"]) != 5 or len(v["r2"]) != 5 for v in tree_cv_fold_results.values()):
        print("Not quite: each model should have exactly 5 fold MSE values and 5 fold R2 values.")
    else:
        single_mean = np.mean(tree_cv_fold_results["Single tree"]["mse"])
        bagging_mean = np.mean(tree_cv_fold_results["Bagging"]["mse"])
        forest_mean = np.mean(tree_cv_fold_results["Random Forest"]["mse"])
        if bagging_mean < single_mean and forest_mean < single_mean:
            print(f"Looks good: single tree mean MSE = {single_mean:.1f}, both ensembles score lower (bagging {bagging_mean:.1f}, Random Forest {forest_mean:.1f}).")
        else:
            print(
                f"Your single-tree mean MSE ({single_mean:.1f}) is not clearly higher than both ensembles' "
                f"(bagging {bagging_mean:.1f}, Random Forest {forest_mean:.1f}). That does not automatically "
                "mean something is wrong -- check that all three models used the identical cv.split(X) folds "
                "before assuming this is an error."
            )
else:
    print("Not complete yet: define tree_cv_fold_results above first.")
""",
            "wp46-604-check",
        ),
        md(
            "The cell below builds `tree_cv_summary` from your fold results "
            "and plots it, with error bars showing spread across folds.",
            "wp46-605-summary-intro",
        ),
        code(
            """
if "tree_cv_fold_results" in globals():
    tree_cv_summary = pd.DataFrame(
        [
            {
                "model": name,
                "mean_mse": np.mean(v["mse"]),
                "sd_mse": np.std(v["mse"]),
                "mean_r2": np.mean(v["r2"]),
            }
            for name, v in tree_cv_fold_results.items()
        ]
    ).set_index("model")
    display(tree_cv_summary.round(3))

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.bar(
        tree_cv_summary.index,
        tree_cv_summary["mean_mse"],
        yerr=tree_cv_summary["sd_mse"],
        capsize=4,
        color=["#5c5674", "#2a6f9e", "#b5622f"],
    )
    ax.set_ylabel("mean cross-validation MSE (lower is better)")
    ax.set_title("Model comparison: identical folds, fixed settings")
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: complete the model-comparison activity above first.")
""",
            "wp46-606-summary",
        ),
        md(
            """
Bagging and Random Forest substantially outperform a single tree here, and
in this comparison bagging is marginally better than Random Forest -- not a
general rule, since Random Forest's extra feature-subsampling randomness is
not guaranteed to help on every dataset.
""",
            "wp46-607-note",
        ),
        md(
            "> **Which of the three models above has the lowest mean cross-validation MSE? Is the gap between bagging and Random Forest here large enough that you would expect it to hold on a different random split?**",
            "wp46-608-reflection",
        ),
    ]


def _section_5_conclusion() -> list[dict]:
    return [
        md("## 7. What Should We Remember?", "wp46-701-header"),
        md(
            """
- A regression tree predicts by recursively splitting on one feature at a
  time; leaves predict the mean of the training participants who land
  there. Trees do not require feature scaling.
- Splitting is greedy: each split minimizes error at that node only, with
  no lookahead to later splits.
- Deeper trees fit the training data better but generalize worse; depth (or
  another complexity control) should be chosen by validation performance,
  not training performance, and the test set is read once, at the end.
- A single tree is sensitive to its training sample. Bagging averages trees
  fit on bootstrap resamples to reduce that sensitivity; Random Forest adds
  random feature subsets at each split to decorrelate the trees further.
- A fair comparison across model families uses identical cross-validation
  folds and fixed (not tuned-on-the-same-folds) complexity settings for
  every model.

Next practice: boosting, which builds trees **sequentially**, each one
correcting the errors left by the trees before it.

### Questions to take away

1. Why can a tree's split boundaries only ever be vertical or horizontal
   lines (in a two-feature plot), never diagonal?
2. Why is choosing tree depth by training MSE alone a bad idea?
3. What does bagging change about how each tree is trained? What does
   Random Forest change in addition?
4. Why must every model in a fair comparison use the same cross-validation
   folds?
5. Is "Random Forest always beats a single tree" a fact you can rely on, or
   an empirical tendency that can fail on a given dataset?
""",
            "wp46-702-summary",
        ),
        code(
            """
show_question("q-bagging-reduces-variance")
""",
            "wp46-703-checked",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_one_tree()
    cells += _section_1b_greedy_activity()
    section_2 = _section_2_how_large()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_2]
    cells += _section_3_ensemble()
    section_4 = _section_4_comparison()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_4]
    cells += _section_5_conclusion()
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
