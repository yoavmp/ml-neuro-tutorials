#!/usr/bin/env python3
"""Generate Exercise 3's JupyterLite template, portable copy, and reference.

WP44 Gate B: migrate Exercise 3 ("Classification and Metrics") to the same
JupyterLite-native, generator-authored architecture WP41/WP42 established for
Exercises 1 and 2 (see WPs/reports/WP41_MAINTAINER_GUIDE.md). One Python
module is the single authoritative source for the JupyterLite template, the
downloadable/Colab-compatible copy, and the completed reference notebook used
only by the test suite -- structurally synchronized by construction, exactly
like scripts/generate_exercise_02_notebook.py.

Data: this notebook reuses the exact same same-origin export Exercise 2
already ships, book/lite/files/data/abide_age_brain.csv (360 fsCT predictors
+ age + group, 1004 participants) -- it already carries the `group` diagnosis
column Exercise 2 never uses. No second, independent data export is created:
empirically verified (WP44) that loading this file, or the same pinned
fallback URL Exercise 2 already uses, reproduces the exact established
classification result bit-for-bit:
    accuracy=0.545817  AUC=0.569221  sensitivity=0.534483  specificity=0.555556
    confusion matrix: TN=75 FP=60 FN=54 TP=62  (n_train=753, n_test=251)
against scripts/classification_model_audit_result.json, the audit this
notebook's recipe/split/C_EXAMPLE preserve unchanged from the pre-migration
book/chapters/chapter_03/exercise_03.ipynb.

Outputs:
  book/lite/files/exercise_03.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_03/exercise_03_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_03_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_03_reference.ipynb (--reference)

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

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_03.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_03_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_03_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 3, "templateVersion": TEMPLATE_VERSION},
}

# Established, audited protocol (scripts/classification_model_audit_result.json)
# -- preserved unchanged by this migration.
C_EXAMPLE = 1.0
EXPECTED_ACCURACY = 0.545817
EXPECTED_AUC = 0.569221
EXPECTED_SENSITIVITY = 0.534483
EXPECTED_SPECIFICITY = 0.555556
EXPECTED_N_TRAIN = 753
EXPECTED_N_TEST = 251
EXPECTED_N_FEATURES = 360


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


# The setup cell's source below (SETUP_SOURCE_TEMPLATE) is plain text that
# becomes the notebook's own generated code -- it is not evaluated by this
# generator script. It duplicates, rather than imports,
# scripts/generate_exercise_02_notebook.py's CSS-scoping fix (WP42 Gate 1
# item 2: ipywidgets' own stylesheet gives checkbox/radio option text a fixed
# 300px width with nowrap+ellipsis, silently truncating long option text
# instead of wrapping it at a narrow viewport) because each generator module
# is a self-contained, independently regenerable source of truth (section
# 4.7) -- neither generator imports the other.
SETUP_SOURCE_TEMPLATE = '''
import sys
import warnings

# Same benign, pinned-kernel-wide MatplotlibDeprecationWarning Exercise 2's
# setup cell filters (confirmed there by live bisection to fire on every
# figure this browser kernel renders, regardless of plotting code) -- filtered
# here by the identical exact message match, never a blanket
# DeprecationWarning/MatplotlibDeprecationWarning suppression.
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
import ipywidgets as widgets
from IPython.display import display, HTML

{features_literal}


def load_abide_classification_table():
    """Return the classification table: 360 cortical-thickness predictors and
    `group`, ABIDE-II's own raw diagnosis code (1 = autism, 2 = control) --
    never a model feature itself, only the source of this notebook's target.

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout) -- the exact same file Exercise 2
    ships (it already carries `group`, unused there); falls back to the same
    pinned, checksummed public source this course already uses elsewhere (a
    bare downloaded .ipynb, or Colab, neither of which has the sibling data
    file). Both paths return identically shaped, identically ordered columns
    for the same 1004 participants (verified), so the rest of this notebook
    never needs to know which one ran.
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
    return table[_ABIDE_LITE_FEATURES + ["group"]].reset_index(drop=True)


# Keeps every checked question's option text wrapping within the notebook's
# own width, at any viewport, instead of being cut off with an ellipsis.
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
'''.strip()


def _setup_cell(mode: str) -> dict:
    source = SETUP_SOURCE_TEMPLATE.replace("{features_literal}", _feature_list_literal())
    return code(source, "wp44-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp44-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 3: Classification and Metrics", "wp44-001-title"),
        md(
            """
## What this notebook covers

Exercise 2 asked a **regression** question -- predicting age from cortical
structure. This notebook returns to ABIDE-II's own central scientific
question: predicting **autism diagnosis**, a categorical label, from the
same 360 cortical-thickness measurements. You will build one
logistic-regression classifier, evaluate it with a confusion matrix and
classification metrics, and explore how the decision threshold and class
imbalance change what those metrics show.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 2's train/test workflow, `StandardScaler`,
`Pipeline`/`fit`/`predict` in scikit-learn, and evaluating a model on
held-out participants.
""",
            "wp44-002-overview",
        ),
    ]


def _section_1() -> list[dict]:
    return [
        md("## 1. Data and setup", "wp44-101-header"),
        code(
            """
# Load the approved ABIDE-II classification table: the same 1004-participant,
# 360-feature cortical-thickness table used throughout this course.
try:
    df = load_abide_classification_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_classification_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under 'Run "
        "the cell below first') before this one, then run this cell again."
    ) from exc
print(f"{len(df)} participants, {df.shape[1] - 1} brain predictors")
df.head()
""",
            "wp44-102-load",
        ),
        md(
            """
`group` is ABIDE-II's own raw diagnosis code, not yet the label this
notebook will model with.
""",
            "wp44-103-labels-intro",
        ),
        code(
            """
# Verify the raw codes before mapping anything -- never infer a mapping from
# column order or alphabetical sorting.
observed_codes = sorted(df["group"].unique())
assert observed_codes == [1, 2], f"unexpected group codes: {observed_codes}"

# This notebook encodes the modelling target as 0 = control, 1 = autism.
diagnosis_label = df["group"].map({1: "autism", 2: "control"})
class_counts = diagnosis_label.value_counts()
print(f"{class_counts['autism']} autism (group=1 -> 1), {class_counts['control']} control (group=2 -> 0)")
""",
            "wp44-104-labels",
        ),
        md(
            "> **This table's target (diagnosis) is categorical, not a "
            "continuous measurement like Exercise 2's age. What does that "
            "change about how you would evaluate a model's predictions?**",
            "wp44-105-reflection",
        ),
    ]


def _section_2() -> list[dict]:
    return [
        md("## 2. From a linear score to a probability", "wp44-201-header"),
        md(
            r"""
Logistic regression starts like linear regression: a weighted sum of the
standardized features plus an intercept, $z = w \cdot x + b$. That score $z$
is passed through the **sigmoid** function to become a probability between 0
and 1:

$$P(Y=1\mid X)=\frac{1}{1+e^{-z}}$$

A **decision threshold**, commonly 0.50, then converts the probability into
a predicted class: probability at or above the threshold predicts autism,
below it predicts control.
""",
            "wp44-202-intro",
        ),
        code(
            """
# A small, clean sigmoid figure: any real-valued score maps to (0, 1).
import matplotlib.pyplot as plt


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


z_grid = np.linspace(-8, 8, 200)
fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(z_grid, sigmoid(z_grid), color="#2a6f9e", lw=2)
ax.axhline(0.5, color="0.6", lw=1, ls=":")
ax.axvline(0, color="0.6", lw=1, ls=":")
ax.set_xlabel("linear score z")
ax.set_ylabel("P(Y = 1 | X)")
ax.set_title("The sigmoid function")
plt.tight_layout()
plt.show()
""",
            "wp44-203-sigmoid",
        ),
        code(
            """
display(make_single_choice_question(
    "Two participants receive autism probabilities of 0.48 and 0.52. At the "
    "default 0.50 threshold their predicted labels differ. What does that "
    "imply about their underlying model evidence?",
    [
        "It must be very different -- opposite predicted labels always mean opposite evidence.",
        "It can be nearly identical -- the sigmoid is continuous, so a tiny change in the linear score crossing the threshold flips the label while barely changing the model's actual evidence.",
        "It cannot be compared without also knowing the true diagnosis.",
    ],
    correct_index=1,
    feedback_correct="Correct: a predicted label is a summary of a probability, and near a threshold that summary can be almost arbitrary.",
))
""",
            "wp44-204-checked",
        ),
    ]


def _section_3() -> list[dict]:
    cells: list[dict] = [
        md("## 3. One logistic-regression model", "wp44-301-header"),
        md(
            """
**Target:** diagnosis (`group`, recoded autism=1 / control=0). **Positive
class:** autism. **Negative class:** control. **Predictors:** the 360
bilateral cortical-thickness (`fsCT_`) columns -- no diagnosis-derived
field, participant id, age, sex, or site is a predictor. **Split:** a
stratified 75/25 train/test split, `random_state=42` -- the same fixed seed
used throughout this course. **Model:** `StandardScaler` (fit on training
rows only) then `LogisticRegression`, using `C = 1.0` for this worked
example, chosen in advance rather than tuned. A later lesson introduces
systematic methods for selecting `C`.
""",
            "wp44-302-intro",
        ),
        code(
            """
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, roc_curve

C_EXAMPLE = 1.0  # fixed by course design for this worked example, not tuned
""",
            "wp44-303-imports",
        ),
        md("### Select the predictor columns", "wp44-311-header"),
        md(
            """
Write code that builds `FEATURES`: every column in `df` whose name starts
with `fsCT_` (the cortical-thickness columns). There should be exactly 360.
""",
            "wp44-312-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# FEATURES = ...\n",
            """
FEATURES = [c for c in df.columns if c.startswith("fsCT_")]
""",
            "wp44-313-blank",
            tags=["wp44-activity-features"],
        ),
        code(
            f"""
# Run this to check your FEATURES selection.
if "FEATURES" in globals():
    non_fsct = [c for c in FEATURES if not c.startswith("fsCT_")]
    non_numeric = [c for c in FEATURES if not pd.api.types.is_numeric_dtype(df[c])]
    if non_fsct:
        print(f"Not quite: {{len(non_fsct)}} selected column(s) do not start with 'fsCT_', e.g. {{non_fsct[:3]}}.")
    elif non_numeric:
        print(f"Not quite: {{len(non_numeric)}} selected column(s) are not numeric, e.g. {{non_numeric[:3]}}.")
    elif len(FEATURES) != {EXPECTED_N_FEATURES}:
        print(f"FEATURES has {{len(FEATURES)}} columns; the established recipe uses exactly {EXPECTED_N_FEATURES}.")
    else:
        print(f"Looks good: {{len(FEATURES)}} fsCT_ columns selected, e.g. {{FEATURES[:3]}}.")
else:
    print("Not complete yet: define FEATURES above first.")
""",
            "wp44-314-check",
        ),
        md("### Build X and y", "wp44-321-header"),
        md(
            """
Write code that builds `X` (the `FEATURES` columns of `df`, as a NumPy
array) and `y` (the binary diagnosis target, 0 = control / 1 = autism, from
`df["group"]`, as established in Section 1).
""",
            "wp44-322-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# X = ...\n# y = ...\n",
            """
X = df[FEATURES].to_numpy(float)
y = (df["group"] == 1).astype(int).to_numpy()
""",
            "wp44-323-blank",
            tags=["wp44-activity-xy"],
        ),
        code(
            """
# Run this to check your X and y.
if "X" in globals() and "y" in globals():
    if len(X) != len(y) or len(X) != len(df):
        print(f"Not quite: X has {len(X)} rows and y has {len(y)} rows; both should have one row per participant ({len(df)}).")
    elif not np.isfinite(X).all():
        print("Not quite: X contains non-finite values -- check that FEATURES only selects numeric brain columns.")
    elif set(np.unique(y)) != {0, 1}:
        print(f"Not quite: y should contain only 0 and 1; found {sorted(set(np.unique(y)))}.")
    else:
        n_pos, n_neg = int(y.sum()), int((y == 0).sum())
        print(f"Looks good: X shape {X.shape}, y has {n_pos} autism (1) and {n_neg} control (0).")
else:
    print("Not complete yet: define X and y above first.")
""",
            "wp44-324-check",
        ),
        md("### Make the train/test split", "wp44-331-header"),
        md(
            f"""
Write code that makes the established split: `train_test_split(X, y,
test_size=0.25, random_state=42, stratify=y)`, producing `X_train`,
`X_test`, `y_train`, `y_test`.
""",
            "wp44-332-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# X_train, X_test, y_train, y_test = ...\n",
            """
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)
""",
            "wp44-333-blank",
            tags=["wp44-activity-split"],
        ),
        code(
            f"""
# Run this to check your split.
if all(name in globals() for name in ("X_train", "X_test", "y_train", "y_test")):
    if len(y_train) != {EXPECTED_N_TRAIN} or len(y_test) != {EXPECTED_N_TEST}:
        print(
            f"Your split has n_train={{len(y_train)}}, n_test={{len(y_test)}}; "
            f"the established split (test_size=0.25, random_state=42, stratify=y) "
            f"gives exactly n_train={EXPECTED_N_TRAIN}, n_test={EXPECTED_N_TEST}. "
            "Check those exact arguments."
        )
    else:
        print(f"n_train = {{len(y_train)}}   n_test = {{len(y_test)}}   n_features = {{X_train.shape[1]}}")
        print(f"train autism rate = {{y_train.mean():.3f}}   test autism rate = {{y_test.mean():.3f}}")
else:
    print("Not complete yet: define X_train, X_test, y_train, and y_test above first.")
""",
            "wp44-334-check",
        ),
        md(
            """
### Fit the model

Uses your `X_train`, `X_test`, `y_train`, and `y_test` from above.
""",
            "wp44-341-header",
        ),
        code(
            """
try:
    model = make_pipeline(StandardScaler(), LogisticRegression(C=C_EXAMPLE, max_iter=5000))
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
    print("predicted labels and probabilities computed for the held-out test set.")
    print(f"Every metric below uses only these {len(y_test)} test participants -- none of them were used to fit the model.")
except NameError as exc:
    raise RuntimeError(
        "X_train/X_test/y_train/y_test are not defined yet. Complete the "
        "FEATURES, X/y, and train/test split activities above first, then "
        "run this cell again."
    ) from exc
""",
            "wp44-342-fit",
        ),
        md(
            "A small paired sample of the held-out test set -- predicted "
            "label versus predicted probability, for the same participants:",
            "wp44-351-header",
        ),
        code(
            """
if all(name in globals() for name in ("y_test", "y_pred", "y_proba")):
    sample = pd.DataFrame({
        "actual": np.where(y_test[:8] == 1, "autism", "control"),
        "predicted label": np.where(y_pred[:8] == 1, "autism", "control"),
        "predicted probability (autism)": np.round(y_proba[:8], 3),
    })
    display(sample)
else:
    print("Not complete yet: complete Section 3's activities above first.")
""",
            "wp44-352-sample",
        ),
        md(
            "> **The confusion matrix and accuracy in Section 4 use "
            "`y_pred` (a decision label). The ROC curve and AUC use "
            "`y_proba` (a score/probability). Why does it matter which of "
            "the two a measure uses?**",
            "wp44-353-reflection",
        ),
    ]
    return cells


def _section_4() -> list[dict]:
    cells: list[dict] = [
        md("## 4. Classification outcomes and metrics", "wp44-401-header"),
        md(
            """
A confusion matrix counts every combination of actual and predicted
diagnosis on the held-out test set. Rows are the **actual** diagnosis,
columns are the **predicted** diagnosis, and autism is the positive class:

| Outcome | Interpretation |
|---|---|
| True negative (TN) | A control participant is classified as control. |
| False positive (FP) | A control participant is classified as autistic. |
| False negative (FN) | An autistic participant is classified as control. |
| True positive (TP) | An autistic participant is classified as autistic. |

$$\\mathrm{Accuracy}=\\frac{TP+TN}{TP+TN+FP+FN}\\qquad
\\mathrm{Sensitivity}=\\frac{TP}{TP+FN}\\qquad
\\mathrm{Specificity}=\\frac{TN}{TN+FP}$$

**Sensitivity** (recall for autism) is the proportion of actually-autistic
participants detected; **specificity** (recall for controls) is the
proportion of actually-control participants correctly identified. The
**ROC curve** plots sensitivity against the false-positive rate
($1-\\mathrm{specificity}$) as the threshold sweeps across every possible
value; **AUC** summarizes ranking performance independent of any one
threshold (0.5 = chance-level ranking, 1.0 = perfect ranking).
""",
            "wp44-402-table",
        ),
        md("### Build the confusion matrix and report accuracy, sensitivity, specificity", "wp44-411-header"),
        md(
            """
Write code that:
- computes the confusion matrix from `y_test` and `y_pred` (`labels=[0, 1]`
  so index 0 = control, index 1 = autism on both axes);
- plots it (e.g. `matplotlib`'s `imshow` or a labelled table) with TN, FP,
  FN, TP clearly marked;
- prints accuracy, sensitivity, and specificity.
""",
            "wp44-412-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# cm = confusion_matrix(...)\n# accuracy = ...\n# sensitivity = ...\n# specificity = ...\n",
            """
cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
accuracy = accuracy_score(y_test, y_pred)
sensitivity = tp / (tp + fn)
specificity = tn / (tn + fp)

fig, ax = plt.subplots(figsize=(3.6, 3.6))
ax.imshow(cm, cmap="Blues")
ax.set_xticks([0, 1]); ax.set_xticklabels(["control", "autism"])
ax.set_yticks([0, 1]); ax.set_yticklabels(["control", "autism"])
ax.set_xlabel("predicted"); ax.set_ylabel("actual")
labels = np.array([[f"TN = {tn}", f"FP = {fp}"], [f"FN = {fn}", f"TP = {tp}"]])
for i in range(2):
    for j in range(2):
        ax.text(j, i, labels[i, j], ha="center", va="center")
ax.set_title("Confusion matrix, held-out test set")
plt.tight_layout()
plt.show()

print(f"accuracy    = {accuracy:.3f}")
print(f"sensitivity = {sensitivity:.3f}  (proportion of autistic participants detected)")
print(f"specificity = {specificity:.3f}  (proportion of control participants correctly identified)")
""",
            "wp44-413-blank",
            tags=["wp44-activity-metrics"],
        ),
        code(
            f"""
# Run this to check your confusion-matrix results.
EXPECTED_ACCURACY = {EXPECTED_ACCURACY}
EXPECTED_SENSITIVITY = {EXPECTED_SENSITIVITY}
EXPECTED_SPECIFICITY = {EXPECTED_SPECIFICITY}
TOLERANCE = 0.03  # generous: absorbs reasonable implementation differences

if "accuracy" in globals() and "sensitivity" in globals() and "specificity" in globals():
    assert np.isfinite(accuracy) and np.isfinite(sensitivity) and np.isfinite(specificity)
    close = (
        abs(accuracy - EXPECTED_ACCURACY) <= TOLERANCE
        and abs(sensitivity - EXPECTED_SENSITIVITY) <= TOLERANCE
        and abs(specificity - EXPECTED_SPECIFICITY) <= TOLERANCE
    )
    if close:
        print(
            f"Looks good: accuracy={{accuracy:.3f}}, sensitivity={{sensitivity:.3f}}, "
            f"specificity={{specificity:.3f}} are within the expected range."
        )
    else:
        print(
            f"Your result (accuracy={{accuracy:.3f}}, sensitivity={{sensitivity:.3f}}, "
            f"specificity={{specificity:.3f}}) differs from the expected result "
            f"(accuracy~{{EXPECTED_ACCURACY:.3f}}, sensitivity~{{EXPECTED_SENSITIVITY:.3f}}, "
            f"specificity~{{EXPECTED_SPECIFICITY:.3f}}). That does not automatically mean "
            "something is wrong -- a different valid implementation can shift these "
            "numbers slightly. Check that you used y_test/y_pred from Section 3 "
            "before assuming this is an error."
        )
else:
    print("Not complete yet: define accuracy, sensitivity, and specificity above first.")
""",
            "wp44-414-check",
        ),
        md("### Plot the ROC curve and report AUC", "wp44-421-header"),
        md(
            """
Write code that computes the ROC curve from `y_test` and `y_proba`
(`roc_curve`), plots it against the chance-level diagonal, and prints the
AUC (`roc_auc_score`).
""",
            "wp44-422-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# fpr, tpr, _ = roc_curve(...)\n# auc = roc_auc_score(...)\n",
            """
fpr, tpr, _ = roc_curve(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)

fig, ax = plt.subplots(figsize=(4.6, 4.4))
ax.plot(fpr, tpr, color="#2a6f9e", lw=2, label=f"ROC curve (AUC = {auc:.3f})")
ax.plot([0, 1], [0, 1], "--", color="0.5", lw=1.2, label="Chance-level ranking")
ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate (sensitivity)")
ax.set_title("ROC curve, held-out test set")
ax.legend(loc="lower right", fontsize=8)
plt.tight_layout()
plt.show()

print(f"AUC = {auc:.3f}  (0.5 = chance-level ranking, 1.0 = perfect ranking)")
""",
            "wp44-423-blank",
            tags=["wp44-activity-roc"],
        ),
        code(
            f"""
# Run this to check your AUC.
EXPECTED_AUC = {EXPECTED_AUC}
AUC_TOLERANCE = 0.03

if "auc" in globals():
    assert np.isfinite(auc)
    if abs(auc - EXPECTED_AUC) <= AUC_TOLERANCE:
        print(f"Looks good: AUC={{auc:.3f}} is within the expected range (~{{EXPECTED_AUC:.3f}}).")
    else:
        print(
            f"Your AUC ({{auc:.3f}}) differs from the expected result (~{{EXPECTED_AUC:.3f}}). "
            "That does not automatically mean something is wrong -- check that you used "
            "y_proba (not y_pred) from Section 3."
        )
else:
    print("Not complete yet: define auc above first.")
""",
            "wp44-424-check",
        ),
    ]
    return cells


def _section_5() -> list[dict]:
    return [
        md("## 5. Choosing a decision threshold", "wp44-501-header"),
        md(
            """
The control below uses the **exact same fixed test-set probabilities**
computed in Section 3 -- moving the threshold never refits the model. It
recomputes, live, the confusion matrix, accuracy, sensitivity, and
specificity.
""",
            "wp44-502-intro",
        ),
        code(
            """
threshold = 0.50  # starting point; move the slider or type a value below

_threshold_output = widgets.Output()


def _threshold_refit(t):
    with _threshold_output:
        _threshold_output.clear_output(wait=True)
        if not all(name in globals() for name in ("y_test", "y_proba")):
            print("Complete Section 3 first: y_test and y_proba are not defined yet.")
            return
        thr_pred = (y_proba >= t).astype(int)
        thr_cm = confusion_matrix(y_test, thr_pred, labels=[0, 1])
        thr_tn, thr_fp, thr_fn, thr_tp = thr_cm[0, 0], thr_cm[0, 1], thr_cm[1, 0], thr_cm[1, 1]
        thr_accuracy = accuracy_score(y_test, thr_pred)
        thr_sensitivity = thr_tp / (thr_tp + thr_fn) if (thr_tp + thr_fn) else float("nan")
        thr_specificity = thr_tn / (thr_tn + thr_fp) if (thr_tn + thr_fp) else float("nan")
        pct_predicted_autism = 100 * thr_pred.mean()
        print(f"threshold = {t:.2f}")
        print(f"TN = {thr_tn}   FP = {thr_fp}   FN = {thr_fn}   TP = {thr_tp}")
        print(f"accuracy = {thr_accuracy:.3f}  sensitivity = {thr_sensitivity:.3f}  specificity = {thr_specificity:.3f}")
        print(f"predicted autism = {pct_predicted_autism:.1f}%   (AUC is unchanged by the threshold)")


threshold_slider = widgets.FloatSlider(value=threshold, min=0.01, max=0.99, step=0.01, description="threshold:")
threshold_input = widgets.BoundedFloatText(value=threshold, min=0.01, max=0.99, step=0.01, description="exact:")


def _on_threshold_change(change):
    if change["name"] == "value":
        threshold_input.value = change["new"]
        threshold_slider.value = change["new"]
        _threshold_refit(change["new"])


threshold_slider.observe(_on_threshold_change, names="value")
threshold_input.observe(_on_threshold_change, names="value")
display(widgets.VBox([threshold_slider, threshold_input, _threshold_output]))
_threshold_refit(threshold_slider.value)
""",
            "wp44-503-widget",
        ),
        code(
            """
display(make_single_choice_question(
    "If failing to identify an autistic participant were considered more "
    "costly than falsely flagging a control, would you generally lower or "
    "raise the decision threshold?",
    [
        "Lower it -- this predicts autism more readily, increasing sensitivity (fewer false negatives) at the cost of specificity.",
        "Raise it -- this predicts autism more readily, increasing sensitivity at the cost of specificity.",
        "The threshold cannot change this tradeoff.",
    ],
    correct_index=0,
    feedback_correct="Correct: a lower threshold predicts autism more readily, which can only increase or hold constant the number of participants predicted autistic -- more true positives caught, but also more false positives.",
))
""",
            "wp44-504-checked",
        ),
    ]


def _section_6() -> list[dict]:
    return [
        md("## 6. Class imbalance and misleading accuracy", "wp44-601-header"),
        md(
            """
This notebook's cohort (463 autism, 541 control) is only mildly imbalanced.
Real diagnostic cohorts are often far more skewed. The control below
resamples real ABIDE participants -- control always the majority class --
into six class ratios (50:50 through 95:5) from a fixed total cohort of 400
participants, refitting the **same fixed model** (`C = C_EXAMPLE`) at every
ratio. 400 was chosen so that even the sparsest ratio, 95:5, stays
meaningfully sparse (20 autism participants) while a stratified 25% test
partition still keeps a handful of autism participants.
""",
            "wp44-602-intro",
        ),
        code(
            """
class_ratio = "90:10"  # starting point; choose a different ratio below

_RATIO_TABLE = {
    "50:50": (0.50, 0.50), "60:40": (0.60, 0.40), "70:30": (0.70, 0.30),
    "80:20": (0.80, 0.20), "90:10": (0.90, 0.10), "95:5": (0.95, 0.05),
}
_IMBALANCE_COHORT_SIZE = 400
_imbalance_output = widgets.Output()


def _imbalance_refit(ratio):
    with _imbalance_output:
        _imbalance_output.clear_output(wait=True)
        if not all(name in globals() for name in ("X", "y")):
            print("Complete Section 3's X/y activity first.")
            return
        majority_pct, minority_pct = _RATIO_TABLE[ratio]
        n_majority = round(_IMBALANCE_COHORT_SIZE * majority_pct)
        n_minority = _IMBALANCE_COHORT_SIZE - n_majority

        rng = np.random.default_rng(20000)  # fixed cohort draw, independent of the split seed
        majority_idx = np.flatnonzero(y == 0)
        minority_idx = np.flatnonzero(y == 1)
        chosen = np.concatenate([
            rng.choice(majority_idx, size=n_majority, replace=False),
            rng.choice(minority_idx, size=n_minority, replace=False),
        ])
        X_cohort, y_cohort = X[chosen], y[chosen]

        Xtr, Xte, ytr, yte = train_test_split(
            X_cohort, y_cohort, test_size=0.25, random_state=42, stratify=y_cohort
        )
        imb_model = make_pipeline(StandardScaler(), LogisticRegression(C=C_EXAMPLE, max_iter=5000)).fit(Xtr, ytr)
        imb_pred = imb_model.predict(Xte)

        imb_cm = confusion_matrix(yte, imb_pred, labels=[0, 1])
        imb_tn, imb_fp, imb_fn, imb_tp = imb_cm[0, 0], imb_cm[0, 1], imb_cm[1, 0], imb_cm[1, 1]
        imb_accuracy = accuracy_score(yte, imb_pred)
        imb_sensitivity = imb_tp / (imb_tp + imb_fn) if (imb_tp + imb_fn) else float("nan")
        imb_specificity = imb_tn / (imb_tn + imb_fp) if (imb_tn + imb_fp) else float("nan")
        imb_balanced_accuracy = (imb_sensitivity + imb_specificity) / 2
        n_test_pos = int(yte.sum())
        n_test_neg = len(yte) - n_test_pos
        imb_baseline = max(n_test_pos, n_test_neg) / len(yte)

        fig, ax = plt.subplots(figsize=(4.4, 3.2))
        ax.bar(["model", "majority-class\\nbaseline"], [imb_accuracy, imb_baseline], color=["#2a6f9e", "#b5622f"])
        ax.set_ylim(0, 1)
        ax.set_ylabel("accuracy")
        ax.set_title(f"Model vs. baseline accuracy at {ratio}")
        plt.tight_layout()
        plt.show()

        print(f"cohort: {len(y_cohort)} participants ({n_majority} control, {n_minority} autism)")
        print(f"model accuracy = {imb_accuracy:.3f}   majority-class baseline = {imb_baseline:.3f}")
        print(f"sensitivity = {imb_sensitivity:.3f}  specificity = {imb_specificity:.3f}  balanced accuracy = {imb_balanced_accuracy:.3f}")


ratio_dropdown = widgets.Dropdown(options=list(_RATIO_TABLE), value=class_ratio, description="ratio:")
ratio_dropdown.observe(lambda change: _imbalance_refit(change["new"]) if change["name"] == "value" else None, names="value")
display(ratio_dropdown, _imbalance_output)
_imbalance_refit(ratio_dropdown.value)
""",
            "wp44-603-widget",
        ),
        md(
            "As class imbalance increases, predicting only the majority "
            "class (control) produces increasingly high accuracy on its own "
            "-- without the model having learned anything about autism. "
            "Comparing model accuracy against the majority-class baseline "
            "for comparison -- computed on the same test partition -- and "
            "inspecting sensitivity, specificity, and balanced accuracy, is "
            "what exposes this.",
            "wp44-605-explanation",
        ),
        md(
            "> **As you move from 50:50 toward 95:5, predict which measures "
            "will most clearly reveal a failing classifier, then try a few "
            "ratios and check your prediction.**",
            "wp44-604-reflection",
        ),
    ]


def _summary() -> list[dict]:
    return [
        md(
            """
## In summary

- Logistic regression outputs probabilities before class labels; a decision
  threshold turns a probability into a prediction.
- A confusion matrix identifies the kinds of correct and incorrect
  decisions a classifier makes; sensitivity and specificity summarize it
  from the autism and control perspectives respectively.
- A chosen threshold changes the confusion matrix and every measure derived
  from labels -- it never changes AUC, which depends only on the
  probabilities' ranking.
- Accuracy should be interpreted relative to class balance and an
  appropriate baseline: a classifier that predicts only the majority class
  can score a high accuracy while detecting none of the minority class.
""",
            "wp44-701-summary",
        ),
        code(
            """
display(make_single_choice_question(
    "Why is predict_proba(), not predict(), needed to compute the ROC curve and AUC?",
    [
        "predict() only returns the label already decided at one fixed threshold -- a single point, not a curve; predict_proba() gives the probability needed to sweep every possible threshold.",
        "predict_proba() is faster to compute than predict().",
        "predict() cannot be called on a held-out test set.",
    ],
    correct_index=0,
))
""",
            "wp44-702-checked",
        ),
        code(
            """
display(make_single_choice_question(
    "What generally happens to false negatives when the decision threshold is lowered?",
    [
        "They generally decrease -- a lower threshold predicts autism more readily, so fewer actually-autistic participants are missed.",
        "They generally increase.",
        "They are unaffected by the threshold.",
    ],
    correct_index=0,
))
""",
            "wp44-703-checked",
        ),
        code(
            """
display(make_multi_choice_question(
    "Why can 95% accuracy describe a useless classifier under severe class imbalance, and what should you look at instead?",
    [
        "At a severe enough imbalance, predicting the majority class for everyone can itself reach ~95% accuracy while detecting none of the minority class.",
        "Comparing accuracy to the majority-class baseline for the same test partition exposes this.",
        "Sensitivity, specificity, balanced accuracy, and AUC can reveal what accuracy alone conceals.",
        "95% accuracy is always reliable regardless of class balance.",
    ],
    correct_indices={0, 1, 2},
))
""",
            "wp44-704-checked",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1()
    cells += _section_2()
    section_3 = _section_3()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_3]
    section_4 = _section_4()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_4]
    cells += _section_5()
    cells += _section_6()
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
