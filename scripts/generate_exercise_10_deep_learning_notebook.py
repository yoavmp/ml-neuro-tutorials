#!/usr/bin/env python3
"""Generate Exercise 10's Colab/local-only Deep Learning notebook (WP58).

**Local-only scope (WP58):** this is a from-scratch Exercise 10 ("Deep
Learning") built on a feature branch for local author review only. It does
NOT touch book/_toc.yml, book/_config.yml, book/config/exercise_manifest.json,
book/chapters/chapter_10/placeholder.md (the live published stub), or
book/chapters/chapter_10/exercise_10.ipynb (the preserved legacy WP38/WP38R
"Examples and Common Mistakes" notebook) -- that file and its own portable
copy (book/downloads/chapter_10/exercise_10_portable.ipynb) are left
completely untouched, inspectable in the working tree exactly as before
this WP, at their existing paths; this WP's own outputs use different
filenames (exercise_10_deep_learning_portable.ipynb /
exercise_10_deep_learning_reference.ipynb) specifically so there is no
collision or ambiguity between the two. Nothing here is merged, pushed,
built into the Jupyter Book site, or deployed.

**Why this notebook has no JupyterLite template (Gate A finding):** this
course's actual pinned browser kernel is jupyterlite-pyodide-kernel==0.8.5,
which bundles Pyodide v314.0.5 (Python 3.14.2, wasm32/emscripten). WP58
verified directly against that exact build (not a generic browser demo):
(1) the build's own published lockfile
(https://cdn.jsdelivr.net/pyodide/v314.0.5/full/pyodide-lock.json) lists 356
packages and does not include torch; (2) a real headless-Chromium session
loaded that exact pyodide.mjs and called
``await micropip.install("torch")``, which failed with
``ValueError: Can't find a pure Python 3 wheel for 'torch'.`` -- PyTorch has
no official wasm32 wheel on PyPI or in Pyodide's package set. So this
notebook is built for Python 3.11 in Google Colab and ordinary local
Jupyter only, per Gate A item 2 of WPs/WP58_ACTIVE_EXERCISE_10_DEEP_LEARNING.md.
The live book page stays the existing "coming later" placeholder
(book/chapters/chapter_10/placeholder.md, unchanged); whether/how to offer
Exercise 10 as a Colab-only download on the real site is left as an open
release decision for the course author (see the report).

**Data (Gate A item 3, verified against the real pinned source, network
audit in WPs/reports/WP58_REPORT.md):** the NeuroHackademy/Yarkoni
``abide2.tsv`` (pinned commit e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b,
CC-BY-4.0, same source book/config/abide_modeling.json already pins for
Exercises 2-9) carries four structural MRI feature families per participant
-- cortical thickness (fsCT), cortical surface area (fsArea), grey-matter
volume (fsVol), and local gyrification index (fsLGI) -- each a complete,
zero-missing, bilateral 360-column block (180 HCP-MMP1/Glasser ROIs x 2
hemispheres) for all 1,004 participants, confirmed live (not assumed) via
``scripts/abide_modeling_data.py --audit``. This notebook uses all four
families together (1,440 structural predictors), unlike Exercises 2-9 and
the "earlier cortical-thickness-only notebooks," which use fsCT alone (360
predictors). The classification target is the table's native ``group``
column (autism=1, control=0; 463/541 of 1,004, 0 missing) -- never a
demographic/clinical column, never site, never a participant id.

Outputs:
  book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb (--student)
  scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb (--reference)

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
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from abide_modeling_data import bundle_columns, MANIFEST  # noqa: E402

PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_10" / "exercise_10_deep_learning_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_10_deep_learning_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp58": {"exercise": 10, "templateVersion": TEMPLATE_VERSION, "runtime": "colab-or-local-only"},
}

# -- data source (pinned, same source as book/config/abide_modeling.json) --
BRAIN_TABLE_URL = MANIFEST["source"]["brain_table"]["url"]
BRAIN_TABLE_SHA256 = MANIFEST["source"]["brain_table"]["sha256"]
FEATURE_MEASURES = ["CT", "Area", "Vol", "LGI"]
FEATURE_COLUMNS = bundle_columns("all-eligible", FEATURE_MEASURES, manifest=MANIFEST)
assert len(FEATURE_COLUMNS) == 1440, len(FEATURE_COLUMNS)

# -- split / training constants (every number verified live before writing
# a single cell below -- see WPs/reports/WP58_REPORT.md for the full
# verification transcript) --
SPLIT_1_TEST_SIZE = 0.4  # first cut: 60% train / 40% rest
SPLIT_2_TEST_SIZE = 0.5  # second cut: rest -> 20% val / 20% test
SPLIT_RANDOM_STATE = 42
BATCH_SIZE = 64
HIDDEN_1 = 128
HIDDEN_2 = 32
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
MAX_EPOCHS = 50
PATIENCE = 8
TORCH_SEED = 42
# Chosen by checking validation accuracy/balanced accuracy across a small
# grid (0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10) -- never the test set.
# C=0.003 gave the best validation balanced accuracy (0.598).
LOGREG_C = 0.003

EARLIER_EXERCISE_3_ACCURACY = 0.5458  # fsCT-only, 360 features, same group target (scripts/classification_model_audit_result.json)
EARLIER_EXERCISE_3_AUC = 0.5692


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
    lines = ["_FEATURE_COLUMNS = ["]
    for i in range(0, len(FEATURE_COLUMNS), 4):
        chunk = ", ".join(repr(c) for c in FEATURE_COLUMNS[i : i + 4])
        lines.append(f"    {chunk},")
    lines.append("]")
    return "\n".join(lines)


SETUP_SOURCE_TEMPLATE = '''
import hashlib
import io
import random
import urllib.request
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display

warnings.filterwarnings("ignore", message=r"The (width|height|x|y) parameter as float was deprecated")

{features_literal}

_ABIDE2_TSV_URL = {brain_table_url!r}
_ABIDE2_TSV_SHA256 = {brain_table_sha256!r}


def load_abide_structural_table():
    """Fetch the pinned ABIDE-II structural table (network required) and
    return a DataFrame with the 1,440 structural predictors (cortical
    thickness, surface area, grey-matter volume, local gyrification index)
    plus "group" (1=autism, 2=control). Verifies the download's SHA-256
    against the pinned value before using it -- this is the same source
    book/config/abide_modeling.json already pins for Exercises 2-9, just
    with three more feature families included.
    """
    with urllib.request.urlopen(_ABIDE2_TSV_URL, timeout=180) as response:
        raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != _ABIDE2_TSV_SHA256:
        raise RuntimeError(
            f"downloaded abide2.tsv sha256 {{digest}} does not match the pinned "
            f"{{_ABIDE2_TSV_SHA256}}. Refusing to use unexpected bytes."
        )
    table = pd.read_csv(io.BytesIO(raw), sep="\\t")
    table = table.loc[:, [c for c in table.columns if not str(c).startswith("Unnamed")]]
    return table[_FEATURE_COLUMNS + ["group"]].reset_index(drop=True)


_QUESTION_CSS = """
<style>
.checked-question .widget-radio-box {{ width: 100% !important; }}
.checked-question .widget-radio-box label {{
    width: 100% !important;
    max-width: 100% !important;
    white-space: normal !important;
    height: auto !important;
    box-sizing: border-box;
    padding: 3px 0;
    line-height: 1.3;
}}
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
        [_question_style_widget(), widgets.HTML(f"<b>{{prompt}}</b>"), radio, button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("checked-question")
    return box


def plot_learning_curves(train_losses, val_losses, best_epoch):
    fig, ax = plt.subplots(figsize=(6, 4))
    epochs = range(1, len(train_losses) + 1)
    ax.plot(epochs, train_losses, label="training loss", marker="o", markersize=3)
    ax.plot(epochs, val_losses, label="validation loss", marker="o", markersize=3)
    ax.axvline(best_epoch, color="0.4", linestyle="--", linewidth=1, label=f"best epoch ({{best_epoch}})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("BCEWithLogitsLoss")
    ax.set_title("Training and validation loss by epoch")
    ax.legend()
    fig.tight_layout()
    return fig, ax


def confusion_counts(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    return tn, fp, fn, tp


def classification_report_row(name, y_true, probs):
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

    pred = (np.asarray(probs) >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_counts(y_true, pred)
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    try:
        auc = roc_auc_score(y_true, probs)
    except ValueError:
        auc = float("nan")
    return {{
        "model": name,
        "accuracy": accuracy_score(y_true, pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, pred),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "roc_auc": auc,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }}
'''.format(
    features_literal=_feature_list_literal(),
    brain_table_url=BRAIN_TABLE_URL,
    brain_table_sha256=BRAIN_TABLE_SHA256,
)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp58-000a-run-first",
    )


def _setup_cell() -> dict:
    return code(SETUP_SOURCE_TEMPLATE + _questions_source_block(), "wp58-000-setup", hidden=True)


# --- title and overview ----------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 10: Deep Learning", "wp58-001-title"),
        md(
            """
**This notebook runs in Google Colab or ordinary local Jupyter (Python
3.11 or later) only.** It is not available through this course's in-browser
JupyterLite launcher: PyTorch has no official build for the WebAssembly
environment JupyterLite runs in, and this course's own pinned browser
kernel does not have it available either (verified directly, not assumed
-- see the note at the end of Section 1). Open this notebook directly in
Colab (upload it or open it from Google Drive/GitHub) or in a local
Jupyter installation.

## What this notebook covers

This is Exercise 10 of the Machine Learning for Neuroscience practice
series. The lecture already introduced layers, dense networks, losses,
epochs, and training loops; here you build and train a small one yourself.

In this notebook, you will:

1. load the data and see how many participants and structural features are available
2. split the data, build PyTorch tensors, and inspect a batch
3. define a small fully connected network
4. complete key parts of the training and evaluation loops, then train it
5. evaluate the trained network once on the test set and compare it with a baseline
6. answer questions about what the network is doing and why certain choices matter
""",
            "wp58-002-overview",
        ),
    ]


# --- Section 1: setup and task ---------------------------------------------


def _section_1() -> list[dict]:
    return [
        md("## 1. Setup and the Task", "wp58-101-header"),
        md(
            """
**The task.** Classify each participant in the ABIDE-II dataset as autism
or control, using several structural MRI measures derived from each
participant's cortical surface. This is the same kind of classification
task as Exercise 3, but with more feature families available to the model.
""",
            "wp58-102-task",
        ),
        code(
            """
try:
    import torch
except ImportError:
    %pip install torch
    import torch

import torch.nn as nn

print("PyTorch version:", torch.__version__)
""",
            "wp58-103-install-torch",
        ),
        md(
            """
### Loading the data

The table below comes from the same pinned ABIDE-II source
(NeuroHackademy/Yarkoni tutorial, CC-BY-4.0) that Exercises 2-9 use. Those
earlier notebooks used only one structural measure, **cortical thickness**
(360 columns: 180 brain regions x 2 hemispheres). Here we add three more
structural measures derived from the same cortical surface reconstruction:
**cortical surface area**, **grey-matter volume**, and **local
gyrification index** (a measure of how folded the cortical surface is).
Together, that is 4 measures x 180 regions x 2 hemispheres = 1,440
structural predictors, for the same 1,004 participants.
""",
            "wp58-104-data-intro",
        ),
        code(
            """
try:
    df = load_abide_structural_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_structural_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under "
        "'Run the cell below first') before this one, then run this cell again."
    ) from exc

X_all = df[_FEATURE_COLUMNS].to_numpy(dtype="float64")
y_all = (df["group"].to_numpy() == 1).astype("float64")  # autism=1, control=0

n_autism = int(y_all.sum())
n_control = int((y_all == 0).sum())
print(f"participants: {df.shape[0]}")
print(f"structural features: {X_all.shape[1]} (4 families x 180 regions x 2 hemispheres)")
print(f"class counts: autism={n_autism} ({n_autism/len(y_all):.1%})  control={n_control} ({n_control/len(y_all):.1%})")
print(f"missing values in X_all: {int(pd.isna(X_all).sum())}")
""",
            "wp58-105-load-data",
        ),
        md(
            """
This table has **zero missing values** in these structural columns. Real
neuroimaging tables are not always this complete, so Section 2 still fits
a missing-value step as part of the standard recipe -- it simply will have
nothing to do here.

> **Note on the JupyterLite limitation (Gate A).** This course's browser
> notebook platform (JupyterLite) runs Python inside the browser via
> Pyodide. The exact Pyodide build this course currently pins
> (jupyterlite-pyodide-kernel 0.8.5, Pyodide v314.0.5) does not include
> PyTorch in its package set, and PyPI has no PyTorch wheel for that
> WebAssembly platform either -- so `pip install torch` cannot succeed
> there. This was verified directly against that build, not assumed. The
> course author will decide separately whether and how to offer this
> exercise on the live site; for now, use Colab or local Jupyter.
""",
            "wp58-106-jupyterlite-note",
        ),
    ]


# --- Section 2: hold-out design and tensors --------------------------------


def _section_2() -> list[dict]:
    return [
        md("## 2. Hold-Out Design and Tensors", "wp58-201-header"),
        md(
            """
We split the 1,004 participants into three groups **before** touching any
feature scaling: a training set, a validation set (used to make decisions
about the network and its training), and a test set that is evaluated
exactly once, at the very end, in Section 5. All three splits are
stratified by diagnosis so each group has a similar autism/control
balance.
""",
            "wp58-202-split-intro",
        ),
        code(
            f"""
from sklearn.model_selection import train_test_split

X_train, X_rest, y_train, y_rest = train_test_split(
    X_all, y_all, test_size={SPLIT_1_TEST_SIZE!r}, random_state={SPLIT_RANDOM_STATE!r}, stratify=y_all
)
X_val, X_test, y_val, y_test = train_test_split(
    X_rest, y_rest, test_size={SPLIT_2_TEST_SIZE!r}, random_state={SPLIT_RANDOM_STATE!r}, stratify=y_rest
)

print(f"X_train: {{X_train.shape}}   X_val: {{X_val.shape}}   X_test: {{X_test.shape}}")
for name, y in [("train", y_train), ("val", y_val), ("test", y_test)]:
    print(f"  {{name}}: autism={{int(y.sum())}}  control={{int((y == 0).sum())}}")
""",
            "wp58-203-split",
        ),
        md(
            """
### Missing values and scaling -- fit on training rows only

`SimpleImputer` and `StandardScaler` are both **fit on `X_train` only**,
then used to *transform* `X_val` and `X_test`. Fitting either step on
validation or test rows would let information about those rows (their
means, their scales) leak into numbers the model is trained on --
overstating how well the model will generalize to genuinely new
participants.
""",
            "wp58-204-scaling-intro",
        ),
        code(
            """
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

imputer = SimpleImputer(strategy="mean").fit(X_train)
X_train_i = imputer.transform(X_train)
X_val_i = imputer.transform(X_val)
X_test_i = imputer.transform(X_test)

scaler = StandardScaler().fit(X_train_i)
X_train_s = scaler.transform(X_train_i).astype("float32")
X_val_s = scaler.transform(X_val_i).astype("float32")
X_test_s = scaler.transform(X_test_i).astype("float32")

print("scaled training features: mean", round(float(X_train_s.mean()), 4), "std", round(float(X_train_s.std()), 4))
""",
            "wp58-205-fit-scale",
        ),
        md(
            """
### Tensors and batches

Now turn the scaled NumPy arrays into PyTorch tensors, and group the
training rows into batches with a `DataLoader`. A `TensorDataset` pairs
each feature row with its label; a `DataLoader` then serves them in
shuffled batches of a fixed size (`BATCH_SIZE`), which is what the
training loop in Section 4 will iterate over.

**Your task:** convert `X_train_s`/`X_val_s`/`X_test_s` and
`y_train`/`y_val`/`y_test` into `float32` tensors (labels as column
vectors, shape `(n, 1)`, since `BCEWithLogitsLoss` expects predictions and
targets to have matching shapes), then build a `TensorDataset` and
`DataLoader` for the training and validation sets.
""",
            "wp58-206-tensor-intro",
        ),
        blank(
            f"""
BATCH_SIZE = {BATCH_SIZE!r}

# Convert each array to a float32 tensor. Labels need shape (n, 1), to
# match the shape BCEWithLogitsLoss expects for its predictions.
X_train_t = ...  # YOUR CODE HERE
y_train_t = ...  # YOUR CODE HERE

X_val_t = ...    # YOUR CODE HERE
y_val_t = ...    # YOUR CODE HERE

X_test_t = ...   # YOUR CODE HERE
y_test_t = ...   # YOUR CODE HERE

# Pair each feature tensor with its label tensor, then batch the training
# set (shuffled) and the validation set (not shuffled -- order does not
# matter for evaluation, so shuffling it would be wasted work).
train_dataset = ...  # YOUR CODE HERE
train_loader = ...   # YOUR CODE HERE

val_dataset = ...  # YOUR CODE HERE
val_loader = ...   # YOUR CODE HERE
""",
            f"""
BATCH_SIZE = {BATCH_SIZE!r}

X_train_t = torch.tensor(X_train_s, dtype=torch.float32)
y_train_t = torch.tensor(y_train, dtype=torch.float32).reshape(-1, 1)

X_val_t = torch.tensor(X_val_s, dtype=torch.float32)
y_val_t = torch.tensor(y_val, dtype=torch.float32).reshape(-1, 1)

X_test_t = torch.tensor(X_test_s, dtype=torch.float32)
y_test_t = torch.tensor(y_test, dtype=torch.float32).reshape(-1, 1)

train_dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

val_dataset = torch.utils.data.TensorDataset(X_val_t, y_val_t)
val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
""",
            "wp58-207-tensors-blank",
            tags=["wp58-activity-tensors"],
        ),
        code(
            """
# Run this to check your tensors and batches.
_required = ["X_train_t", "y_train_t", "X_val_t", "y_val_t", "X_test_t", "y_test_t", "train_loader", "val_loader"]
_missing = [name for name in _required if name not in globals() or globals()[name] is Ellipsis]
if _missing:
    print(f"Not finished yet -- these are still missing or unfilled: {', '.join(_missing)}.")
else:
    problems = []
    if X_train_t.dtype != torch.float32 or y_train_t.dtype != torch.float32:
        problems.append("X_train_t and y_train_t must both have dtype torch.float32.")
    if y_train_t.ndim != 2 or y_train_t.shape[1] != 1:
        problems.append(f"y_train_t should have shape (n, 1); got {tuple(y_train_t.shape)}.")
    if X_train_t.shape[0] != y_train_t.shape[0]:
        problems.append("X_train_t and y_train_t must have the same number of rows.")
    if not torch.isfinite(X_train_t).all():
        problems.append("X_train_t contains non-finite values (NaN or inf).")
    if problems:
        for p in problems:
            print("Not quite:", p)
    else:
        xb, yb = next(iter(train_loader))
        print(f"One training batch: xb.shape={tuple(xb.shape)}  yb.shape={tuple(yb.shape)}  yb unique values={sorted(set(yb.flatten().tolist()))}")
        print("Looks good: tensors are float32, shapes line up, and values are finite.")
""",
            "wp58-208-tensors-check",
        ),
    ]


# --- Section 3: build a fully connected network ----------------------------


def _section_3() -> list[dict]:
    return [
        md("## 3. Build a Fully Connected Network", "wp58-301-header"),
        md(
            f"""
Now define the network: an `nn.Module` with two modest hidden layers
({HIDDEN_1} units, then {HIDDEN_2} units -- chosen, along with the learning
rate below, by comparing a handful of configurations on the *validation*
set only, never the test set) and a nonlinear activation (`ReLU`) between
layers. The final layer outputs **one raw logit per participant** -- not a
probability. We pass that logit directly to `nn.BCEWithLogitsLoss`, which
combines a sigmoid and binary cross-entropy in one numerically stable step;
applying `sigmoid` ourselves before this loss would double up that step and
is a common mistake to avoid.

**Your task:** fill in the three linear layers (sizes are given in the
`__init__` signature) and the `forward` method that chains them together
with the activations.
""",
            "wp58-302-model-intro",
        ),
        blank(
            """
class AutismClassifierNet(nn.Module):
    def __init__(self, input_dim, hidden1, hidden2):
        super().__init__()
        # Three linear layers: input_dim -> hidden1 -> hidden2 -> 1 output logit.
        self.fc1 = ...   # YOUR CODE HERE
        self.act1 = nn.ReLU()
        self.fc2 = ...   # YOUR CODE HERE
        self.act2 = nn.ReLU()
        self.fc3 = ...   # YOUR CODE HERE -- one output logit, no activation on this layer

    def forward(self, x):
        # Chain each linear layer with its activation, except the last layer.
        x = ...   # YOUR CODE HERE
        x = ...   # YOUR CODE HERE
        return ...  # YOUR CODE HERE
""",
            """
class AutismClassifierNet(nn.Module):
    def __init__(self, input_dim, hidden1, hidden2):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden1)
        self.act1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.act2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden2, 1)

    def forward(self, x):
        x = self.act1(self.fc1(x))
        x = self.act2(self.fc2(x))
        return self.fc3(x)
""",
            "wp58-303-model-blank",
            tags=["wp58-activity-model"],
        ),
        code(
            f"""
# Run this to check your model definition.
if "AutismClassifierNet" not in globals():
    print("Not finished yet -- AutismClassifierNet is not defined.")
else:
    try:
        _probe = AutismClassifierNet(X_train_t.shape[1], {HIDDEN_1!r}, {HIDDEN_2!r})
        _out = _probe(X_train_t[:5])
    except Exception as exc:
        print(f"Not quite -- building or running the model raised an error: {{exc}}")
    else:
        if tuple(_out.shape) != (5, 1):
            print(f"Not quite: forward(X_train_t[:5]) should have shape (5, 1); got {{tuple(_out.shape)}}.")
        else:
            print(f"Looks good: forward() on 5 rows returns shape {{tuple(_out.shape)}} (one logit per row).")
""",
            "wp58-304-model-check",
        ),
    ]


# --- Section 4: train and validate ------------------------------------------


def _section_4() -> list[dict]:
    return [
        md("## 4. Train and Validate", "wp58-401-header"),
        md(
            """
A training epoch repeats, for every batch: a **forward pass** (compute
predictions), compute the **loss**, reset gradients from the previous
batch (`optimizer.zero_grad()`), **backpropagate** (`loss.backward()`,
which fills in `.grad` on every parameter), then take an **optimizer
step** (`optimizer.step()`, which updates the parameters using those
gradients). `model.train()` and `model.eval()` switch layers like dropout
or batch normalization between their training and inference behavior --
this model has neither, but setting the mode explicitly is good practice
and is required once you add layers that do depend on it.

**Your task:** complete the four missing lines below: the forward pass and
loss inside `train_one_epoch`, and the forward pass and loss inside
`evaluate`.
""",
            "wp58-402-loop-intro",
        ),
        blank(
            """
def train_one_epoch(model, loader, optimizer, loss_fn):
    model.train()
    running_loss = 0.0
    n_rows = 0
    for xb, yb in loader:
        optimizer.zero_grad()
        logits = ...   # YOUR CODE HERE: run the model on this batch of inputs
        loss = ...      # YOUR CODE HERE: compute this batch's loss from logits and yb
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * xb.size(0)
        n_rows += xb.size(0)
    return running_loss / n_rows


def evaluate(model, loader, loss_fn):
    model.eval()
    running_loss = 0.0
    n_rows = 0
    all_probs, all_targets = [], []
    with torch.no_grad():
        for xb, yb in loader:
            logits = ...   # YOUR CODE HERE: same forward pass as in train_one_epoch
            loss = ...      # YOUR CODE HERE: same loss computation as in train_one_epoch
            running_loss += loss.item() * xb.size(0)
            n_rows += xb.size(0)
            all_probs.append(torch.sigmoid(logits))
            all_targets.append(yb)
    probs = torch.cat(all_probs).numpy().ravel()
    targets = torch.cat(all_targets).numpy().ravel()
    return running_loss / n_rows, probs, targets
""",
            """
def train_one_epoch(model, loader, optimizer, loss_fn):
    model.train()
    running_loss = 0.0
    n_rows = 0
    for xb, yb in loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss = loss_fn(logits, yb)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * xb.size(0)
        n_rows += xb.size(0)
    return running_loss / n_rows


def evaluate(model, loader, loss_fn):
    model.eval()
    running_loss = 0.0
    n_rows = 0
    all_probs, all_targets = [], []
    with torch.no_grad():
        for xb, yb in loader:
            logits = model(xb)
            loss = loss_fn(logits, yb)
            running_loss += loss.item() * xb.size(0)
            n_rows += xb.size(0)
            all_probs.append(torch.sigmoid(logits))
            all_targets.append(yb)
    probs = torch.cat(all_probs).numpy().ravel()
    targets = torch.cat(all_targets).numpy().ravel()
    return running_loss / n_rows, probs, targets
""",
            "wp58-403-loop-blank",
            tags=["wp58-activity-loop"],
        ),
        code(
            """
# Run this to check your training/evaluation functions on one epoch.
if "train_one_epoch" not in globals() or "evaluate" not in globals():
    print("Not finished yet -- train_one_epoch and/or evaluate are not defined.")
else:
    try:
        _probe_model = AutismClassifierNet(X_train_t.shape[1], HIDDEN_1, HIDDEN_2) if "HIDDEN_1" in globals() else AutismClassifierNet(X_train_t.shape[1], 128, 32)
        _probe_loss = nn.BCEWithLogitsLoss()
        _probe_opt = torch.optim.Adam(_probe_model.parameters(), lr=1e-3)
        _train_loss = train_one_epoch(_probe_model, train_loader, _probe_opt, _probe_loss)
        _val_loss, _val_probs, _val_targets = evaluate(_probe_model, val_loader, _probe_loss)
    except Exception as exc:
        print(f"Not quite -- running one epoch raised an error: {exc}")
    else:
        problems = []
        if not (0.0 < _train_loss < 5.0):
            problems.append(f"train_one_epoch returned an unusual loss value ({_train_loss:.4f}); expected a small positive number.")
        if not (_val_probs.min() >= 0.0 and _val_probs.max() <= 1.0):
            problems.append("evaluate's returned probabilities should all be between 0 and 1 (did you apply sigmoid?).")
        if len(_val_probs) != len(y_val):
            problems.append(f"evaluate returned {len(_val_probs)} probabilities; expected one per validation row ({len(y_val)}).")
        if problems:
            for p in problems:
                print("Not quite:", p)
        else:
            print(f"Looks good: one training epoch ran (train_loss={_train_loss:.4f}), and evaluate() returned {len(_val_probs)} valid probabilities.")
""",
            "wp58-404-loop-check",
        ),
        md(
            """
### Training with early stopping

The cell below trains the real model for up to `MAX_EPOCHS` epochs, using
your `train_one_epoch` and `evaluate` functions, with a fixed random seed
for reproducibility. After every epoch, it checks the validation loss: if
it has not improved for `PATIENCE` epochs in a row, training stops early,
and the model's weights are rolled back to whichever epoch had the best
(lowest) validation loss -- not necessarily the final epoch. This keeps an
overfit final state from being reported as "the" trained model.

This cell trains the network exactly once per normal run of this notebook
-- not on every edit of the cells above it.
""",
            "wp58-405-train-intro",
        ),
        code(
            f"""
import random

_required = ["AutismClassifierNet", "train_one_epoch", "evaluate", "train_loader", "val_loader", "X_train_t"]
_missing = [name for name in _required if name not in globals() or globals()[name] is Ellipsis]
if _missing:
    raise RuntimeError(
        "Not ready yet -- go back and complete the earlier blank(s) for: "
        + ", ".join(_missing)
        + " (Sections 2-4) before running this cell."
    )

random.seed({TORCH_SEED!r})
np.random.seed({TORCH_SEED!r})
torch.manual_seed({TORCH_SEED!r})

HIDDEN_1 = {HIDDEN_1!r}
HIDDEN_2 = {HIDDEN_2!r}
LEARNING_RATE = {LEARNING_RATE!r}
WEIGHT_DECAY = {WEIGHT_DECAY!r}
MAX_EPOCHS = {MAX_EPOCHS!r}
PATIENCE = {PATIENCE!r}
LOGREG_C = {LOGREG_C!r}  # used later, in Section 5's baseline comparison

model = AutismClassifierNet(X_train_t.shape[1], HIDDEN_1, HIDDEN_2)
loss_fn = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

train_losses, val_losses = [], []
best_val_loss = float("inf")
best_state = None
best_epoch = -1
epochs_no_improve = 0

for epoch in range(MAX_EPOCHS):
    train_loss = train_one_epoch(model, train_loader, optimizer, loss_fn)
    val_loss, _, _ = evaluate(model, val_loader, loss_fn)
    train_losses.append(train_loss)
    val_losses.append(val_loss)

    if val_loss < best_val_loss - 1e-4:
        best_val_loss = val_loss
        best_state = {{k: v.clone() for k, v in model.state_dict().items()}}
        best_epoch = epoch
        epochs_no_improve = 0
    else:
        epochs_no_improve += 1

    if epochs_no_improve >= PATIENCE:
        print(f"Early stopping after epoch {{epoch + 1}} (best epoch: {{best_epoch + 1}}, best val_loss: {{best_val_loss:.4f}})")
        break
else:
    print(f"Reached MAX_EPOCHS={{MAX_EPOCHS}} without triggering early stopping (best epoch: {{best_epoch + 1}})")

model.load_state_dict(best_state)
model.eval()
print(f"Restored weights from epoch {{best_epoch + 1}} (lowest validation loss: {{best_val_loss:.4f}}).")
""",
            "wp58-406-train-run",
        ),
        code(
            """
fig, ax = plot_learning_curves(train_losses, val_losses, best_epoch + 1)
plt.show()
""",
            "wp58-407-plot-curves",
        ),
        code(
            """
# A quick sanity check on the training run.
problems = []
if len(train_losses) < 2:
    problems.append("training ran for fewer than 2 epochs; something stopped it too early.")
if min(val_losses) != best_val_loss:
    problems.append("best_val_loss does not match the minimum of val_losses; check the early-stopping bookkeeping.")
if train_losses[-1] >= train_losses[0]:
    problems.append("training loss did not decrease at all from the first to the last epoch run -- check train_one_epoch.")
if problems:
    for p in problems:
        print("Check this:", p)
else:
    print(f"Looks good: trained for {len(train_losses)} epoch(s), training loss fell from {train_losses[0]:.4f} to {train_losses[-1]:.4f}, "
          f"and the restored weights are from the best validation epoch ({best_epoch + 1}).")
""",
            "wp58-408-train-check",
        ),
    ]


# --- Section 5: final evaluation and comparison -----------------------------


def _section_5() -> list[dict]:
    return [
        md("## 5. Final Evaluation and Comparison", "wp58-501-header"),
        md(
            """
Now -- for the first and only time -- evaluate the trained network on
`X_test`/`y_test`. This happens exactly once, after every choice about the
network (architecture, learning rate, number of epochs) was already made
using only the training and validation sets.

We compare three things on the same test participants, with the same 1,440
features: a **dummy baseline** that always predicts the majority class seen
in training, a **regularized logistic regression** fit on the same
train-only-scaled features (its regularization strength was likewise
chosen by checking validation performance across a small grid, never the
test set), and the **trained network**.
""",
            "wp58-502-eval-intro",
        ),
        code(
            """
with torch.no_grad():
    test_logits = model(X_test_t)
    test_probs_nn = torch.sigmoid(test_logits).numpy().ravel()

from sklearn.linear_model import LogisticRegression

logreg = LogisticRegression(C=LOGREG_C, max_iter=5000, random_state=42).fit(X_train_s, y_train)
test_probs_logreg = logreg.predict_proba(X_test_s)[:, 1]

majority_class = 0.0 if (y_train == 0).sum() >= (y_train == 1).sum() else 1.0
test_probs_dummy = np.full_like(y_test, majority_class)

rows = [
    classification_report_row("dummy (majority class)", y_test, test_probs_dummy),
    classification_report_row(f"logistic regression (C={LOGREG_C})", y_test, test_probs_logreg),
    classification_report_row("neural network", y_test, test_probs_nn),
]
comparison_table = pd.DataFrame(rows).set_index("model")
comparison_table
""",
            "wp58-503-compare",
        ),
        code(
            """
fig, ax = plt.subplots(figsize=(6, 4))
metrics_to_plot = ["accuracy", "balanced_accuracy", "roc_auc"]
x = np.arange(len(comparison_table))
width = 0.25
for i, metric in enumerate(metrics_to_plot):
    ax.bar(x + i * width, comparison_table[metric], width, label=metric)
ax.axhline(0.5, color="0.5", linestyle="--", linewidth=1, label="chance")
ax.set_xticks(x + width)
ax.set_xticklabels(comparison_table.index, rotation=15, ha="right")
ax.set_ylim(0, 1)
ax.set_title("Test-set comparison (evaluated once)")
ax.legend()
fig.tight_layout()
plt.show()
""",
            "wp58-504-compare-plot",
        ),
        md(
            f"""
### Reading this comparison honestly

Report whatever `comparison_table` actually shows -- do not expect the
network to beat the baseline, and do not expect either model to clear 60%
accuracy. With roughly 600 training participants and 1,440 features, both
models are working with a hard problem: more features than this course's
earlier cortical-thickness-only models had, but not more participants, and
autism spectrum disorder's structural MRI signature is subtle and
heterogeneous across sites and individuals. For context only -- **not** as
a directly controlled comparison, since the feature set, split, and model
all differ -- Exercise 3's cortical-thickness-only logistic regression on
this same `group` target reached {EARLIER_EXERCISE_3_ACCURACY:.1%} test
accuracy (AUC {EARLIER_EXERCISE_3_AUC:.3f}).

> **Note on exact numbers.** Every number in this section is computed live
> by the cells above and may differ slightly from one PyTorch version or
> machine to another, even with the fixed random seed used here -- CPU
> floating-point operations are not guaranteed bit-identical across
> hardware/library versions. Expect similar magnitude and direction, not an
> exact digit match to any number printed in this cell's own text.
""",
            "wp58-505-honest-reading",
        ),
    ]


# --- Section 6: interpretation and limits -----------------------------------


_QUESTIONS = {
    "q-tensor-shape": dict(
        shuffle_seed=3,
        prompt=(
            "X_train_t has shape (602, 1440) and y_train_t has shape (602, 1). "
            "What does the first dimension of each tensor represent, and why "
            "must the two match?"
        ),
        options=[
            "The number of participants in the training set; each row of X_train_t and the matching row of y_train_t describe the same participant, so a prediction can be matched to the right label.",
            "The number of structural features; it must match because PyTorch requires inputs and labels to have the same number of columns.",
            "The batch size used by the DataLoader; it is unrelated to how many participants are in the training set.",
        ],
        correct_index=0,
        feedback_correct="Correct: the first dimension is the number of rows (participants). X and y must agree on it so every feature row lines up with its own label.",
    ),
    "q-logits-loss": dict(
        shuffle_seed=8,
        prompt=(
            "The network's final layer outputs one raw logit per participant, "
            "with no sigmoid applied before BCEWithLogitsLoss. Why?"
        ),
        options=[
            "BCEWithLogitsLoss combines a sigmoid and binary cross-entropy internally, in a way that is more numerically stable than computing sigmoid and the loss as two separate steps.",
            "Logits are required because scikit-learn's LogisticRegression also outputs logits.",
            "Applying a sigmoid before this loss would make the gradients too large for Adam to handle.",
        ],
        correct_index=0,
        feedback_correct="Correct: BCEWithLogitsLoss's internal log-sum-exp formulation avoids the numerical instability of computing sigmoid and log-loss separately.",
    ),
    "q-gradient-update": dict(
        shuffle_seed=13,
        prompt=(
            "Suppose optimizer.zero_grad() were accidentally removed from "
            "train_one_epoch, leaving loss.backward() and optimizer.step() in "
            "place. What would happen across batches?"
        ),
        options=[
            "Gradients from each new batch would accumulate on top of gradients from every previous batch, so each update would reflect more than just the current batch.",
            "Nothing would change; zero_grad() only matters for the very first batch of training.",
            "Training would stop immediately with a shape-mismatch error.",
        ],
        correct_index=0,
        feedback_correct="Correct: PyTorch accumulates gradients by default. Without zero_grad(), .grad keeps growing across batches instead of reflecting only the current one.",
    ),
    "q-train-only-scaling": dict(
        shuffle_seed=21,
        prompt=(
            "SimpleImputer and StandardScaler are both fit on X_train only, "
            "then used only to transform X_val and X_test. Why not fit them on "
            "all 1,004 participants before splitting?"
        ),
        options=[
            "Fitting on the full dataset would let information about validation/test rows (their means and scales) influence what the model trains on, overstating how well it will generalize to genuinely new participants.",
            "Fitting on the full dataset is statistically fine; the course only avoids it to save computation time.",
            "StandardScaler raises an error if it is fit on more than 1,000 rows.",
        ],
        correct_index=0,
        feedback_correct="Correct: fitting preprocessing on rows the model will later be evaluated on is a form of data leakage, even though no label is involved.",
    ),
    "q-overfitting-earlystop": dict(
        shuffle_seed=6,
        prompt=(
            "During training, train_loss kept decreasing every epoch, but "
            "val_loss decreased for a few epochs and then started rising. What "
            "does the early-stopping rule in this notebook do in response?"
        ),
        options=[
            "It keeps the model weights from whichever epoch had the lowest validation loss, rather than the weights from the final epoch -- the rising val_loss after that point indicates the network is starting to overfit the training rows.",
            "It increases the batch size automatically until val_loss also decreases.",
            "It is expected and nothing is done about it; the final epoch's weights are always used regardless of val_loss.",
        ],
        correct_index=0,
        feedback_correct="Correct: a falling train_loss with a rising val_loss is the classic overfitting signature. Restoring the best-validation-epoch weights avoids reporting an overfit final state.",
    ),
    "q-test-set-choices": dict(
        shuffle_seed=17,
        prompt=(
            "This notebook chose the number of epochs (via early stopping) and "
            "the hidden-layer sizes using only X_val/y_val, then evaluated on "
            "X_test exactly once. Why not simply try several configurations and "
            "keep whichever one scores best on X_test?"
        ),
        options=[
            "Using the test set to choose among configurations turns it into another validation set; the reported test score would then overestimate how the chosen model performs on truly new participants.",
            "It would work just as well; the course avoids it only because scikit-learn's train_test_split does not support reusing a split twice.",
            "The test set is too small for this; a larger one could be used to choose hyperparameters safely.",
        ],
        correct_index=0,
        feedback_correct="Correct: any choice made by looking at test performance -- even just picking among a few configurations -- contaminates the test set's role as an honest, one-time check.",
    ),
}


# _QUESTIONS and show_question are embedded as literal source into the
# hidden setup cell (see _questions_source_block/_setup_cell) -- a visible
# call like show_question("q-tensor-shape") in a lesson cell never prints or
# displays a correct_index. Every options list above is written with its
# correct answer first, for readability; show_question shuffles the
# DISPLAYED order with a fixed, per-question seed (reproducible across
# reruns of the same cell, different across questions).


def _questions_source_block() -> str:
    questions_json = json.dumps(_QUESTIONS, indent=4)
    return f'''

_QUESTIONS = {questions_json}


def show_question(question_id):
    q = _QUESTIONS[question_id]
    order = list(range(len(q["options"])))
    random.Random(q["shuffle_seed"]).shuffle(order)
    shuffled_options = [q["options"][i] for i in order]
    shuffled_correct = order.index(q["correct_index"])
    display(make_single_choice_question(
        q["prompt"], shuffled_options, shuffled_correct, q.get("feedback_correct", "Correct."),
    ))
'''


def _show_question_call(question_id: str, cell_id: str) -> dict:
    return code(f'show_question("{question_id}")', cell_id)


def _section_6() -> list[dict]:
    cells = [
        md("## 6. Interpretation and Limits", "wp58-601-header"),
        md("**Check your understanding.**", "wp58-602-check-intro"),
    ]
    for qid, cell_id in [
        ("q-tensor-shape", "wp58-603-q1"),
        ("q-logits-loss", "wp58-604-q2"),
        ("q-gradient-update", "wp58-605-q3"),
        ("q-train-only-scaling", "wp58-606-q4"),
        ("q-overfitting-earlystop", "wp58-607-q5"),
        ("q-test-set-choices", "wp58-608-q6"),
    ]:
        cells.append(_show_question_call(qid, cell_id))
    cells.append(
        md(
            """
### What this does and does not show

A fully connected network can model nonlinear interactions between
features that a linear model like logistic regression cannot represent
directly, and in principle it can make better use of more data and more
features as both grow. But this cohort is small (1,004 participants spread
across 17 sites) and clinically and biologically heterogeneous, and adding
features without adding participants gives a flexible model more ways to
fit noise in the training set rather than real signal.

Structural MRI measures gathered across many sites and scanners are also
known to carry site/scanner effects that compete with the signal of
interest. Saponaro et al. (2022, *NeuroImage: Clinical*) harmonized 221
structural morphometric features (cortical thickness, grey-matter volume,
white-matter volume, and subcortical volumes from FreeSurfer) across 1,638
participants from 37 sites spanning ABIDE I and II, and found that a
classifier's cross-validated AUC rose from 0.58 before harmonization to
0.67 after it -- the same underlying case-control signal, substantially
easier to recover once multi-site batch effects were removed. This
notebook's data is not harmonized across its 17 sites, which is one
plausible, concrete reason neither model here reaches a high score; it is
a structural-MRI finding, distinct from the motion/data-quality literature
specific to **functional** MRI.

None of this supports a diagnostic or causal claim about autism from these
features, and a middling score here does not mean this general approach
has hit some definitive ceiling -- better harmonization, more
participants, or different features could change these numbers. Report
what you actually measured, not what you expected to measure.
""",
            "wp58-609-wrapup",
        )
    )
    return cells


# --- assembly ---------------------------------------------------------------


def build_cells(mode: str) -> list[dict]:
    cells: list[dict] = []
    cells.extend(_title_and_overview())
    cells.append(_run_first_notice())
    cells.append(_setup_cell())
    cells.extend(_section_1())
    for c in _section_2():
        cells.append(c.render(mode) if isinstance(c, Blank) else c)
    for c in _section_3():
        cells.append(c.render(mode) if isinstance(c, Blank) else c)
    for c in _section_4():
        cells.append(c.render(mode) if isinstance(c, Blank) else c)
    cells.extend(_section_5())
    cells.extend(_section_6())
    return cells


def build_notebook(mode: str) -> "nbformat.NotebookNode":
    nb = new_notebook()
    nb["metadata"] = dict(KERNELSPEC)
    nb["cells"] = build_cells(mode)
    nbformat.validate(nb)
    return nb


def _write_if_changed(nb: "nbformat.NotebookNode", path: Path) -> bool:
    new_text = nbformat.writes(nb, version=4)
    if path.exists() and path.read_text() == new_text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--write", action="store_true")
    mode_group.add_argument("--check", action="store_true")
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument("--student", action="store_true")
    target_group.add_argument("--reference", action="store_true")
    target_group.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    targets = []
    if args.student:
        targets = ["student"]
    elif args.reference:
        targets = ["reference"]
    else:
        targets = ["student", "reference"]

    stale = []
    for target in targets:
        path = PORTABLE_PATH if target == "student" else REFERENCE_PATH
        nb = build_notebook(target)
        if args.write:
            changed = _write_if_changed(nb, path)
            print(f"{'wrote' if changed else 'unchanged'}: {path.relative_to(REPO_ROOT)}")
        else:
            new_text = nbformat.writes(nb, version=4)
            if not path.exists() or path.read_text() != new_text:
                stale.append(path)
    if args.check and stale:
        print("STALE (run with --write to regenerate):", file=sys.stderr)
        for p in stale:
            print(f"  - {p.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    if args.check:
        print("OK: all selected outputs match their generator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
