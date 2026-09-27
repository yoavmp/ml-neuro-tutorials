#!/usr/bin/env python3
"""Generate Exercise 2's JupyterLite template, portable copy, and reference.

WP41 section 4.7: one authoritative structured source for Exercise 2, so the
JupyterLite template, the downloadable/Colab-compatible notebook, and the
completed reference notebook used only for automated testing stay
structurally synchronized by construction instead of by hand-editing three
files. Prompts, headings, starter code, variable names, and activity order
come from the single cell list built by ``_build_cells`` below.

Every "YOUR CODE HERE" activity is declared once, as a ``(starter, solution)``
pair; ``--student`` renders the starter side (what students see) and
``--reference`` renders the solution side (a fully worked notebook used only
by the test suite, never published). Everything else is identical between
the two renders, which is what "structurally synchronized" means here.

Because this notebook must run unmodified in JupyterLite, a downloaded local
Jupyter, and Colab (section 3.4, 4.4), it uses only standard portable APIs
(ipywidgets + Matplotlib) and never a JupyterLite-only API. The one thing
that legitimately differs by environment -- where the data file lives -- is
handled by one small helper in the collapsed setup cell, never in student-
facing code.

Outputs:
  book/lite/files/exercise_02.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_02/exercise_02_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_02_portable.ipynb           (--student, same file,
                                                          served copy -- see
                                                          LITE_FILES_PORTABLE_COPY_PATH)
  scripts/reference_notebooks/exercise_02_reference.ipynb (--reference)

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
REFERENCE_IMAGE_SCRIPT = REPO_ROOT / "scripts" / "render_exercise_02_reference_plot.py"
REFERENCE_IMAGE_PATH = REPO_ROOT / "book" / "lite" / "files" / "data" / "exercise_02_observed_vs_predicted.png"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_02.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb"
# WP41R blocker 3: `book/downloads/` is excluded from the Jupyter Book source
# scan and is not copied into `_build/html/` (see book/_config.yml) -- it
# only ever existed as a raw-GitHub-served artifact for the older chapters
# that link to it that way. Exercise 2's transition page must not depend on
# that (see scripts/generate_exercise_02_transition_page.py), so the same
# byte-identical content is also written here, next to the JupyterLite
# template -- `jupyter lite build` already copies this whole directory
# verbatim into `_build/html/lite/files/`, same-origin, working regardless
# of repository visibility. PORTABLE_PATH remains the canonical committed
# copy (consistent with every other chapter, and what Colab/local-Jupyter
# instructions elsewhere refer to); this is a second, identical output, not
# a second source of truth.
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_02_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_02_reference.ipynb"

TEMPLATE_VERSION = 2

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 2, "templateVersion": TEMPLATE_VERSION},
}


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


def blank(student_source: str, reference_source: str, cell_id: str, tags: list[str] | None = None) -> "Blank":
    return Blank(student_source, reference_source, cell_id, tags or [])


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


def _reference_image_data_uri() -> str:
    return base64.b64encode(REFERENCE_IMAGE_PATH.read_bytes()).decode("ascii")


SETUP_SOURCE_TEMPLATE = '''
import sys

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
from IPython.display import display

{features_literal}


def load_abide_age_brain_table():
    """Return the age/brain table: 360 cortical-thickness predictors, age,
    and group (autism/control, used only to reproduce the established
    train/test split -- never a model feature).

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout); falls back to the same
    pinned, checksummed public source this course already uses elsewhere
    (a bare downloaded .ipynb, or Colab, neither of which has the sibling
    data file). Both paths return identically shaped, identically ordered
    columns, so the rest of this notebook never needs to know which one
    ran.
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


def make_single_choice_question(prompt, options, correct_index, feedback_correct="Correct.", feedback_incorrect="Not quite -- try again."):
    """A compact single-choice checked question. Returns a widget to display()."""
    radio = widgets.RadioButtons(options=list(options), description="", layout=widgets.Layout(width="max-content"))
    button = widgets.Button(description="Check answer", button_style="primary")
    feedback = widgets.Output()

    def _on_click(_button):
        with feedback:
            feedback.clear_output(wait=True)
            print(feedback_correct if radio.index == correct_index else feedback_incorrect)

    button.on_click(_on_click)
    return widgets.VBox([widgets.HTML(f"<b>{prompt}</b>"), radio, button, feedback])


def make_multi_choice_question(prompt, options, correct_indices, feedback_correct="Correct.", feedback_incorrect="Not quite -- try again."):
    """A compact multiple-selection checked question. Returns a widget to display()."""
    correct = set(correct_indices)
    boxes = [widgets.Checkbox(value=False, description=opt, indent=False) for opt in options]
    button = widgets.Button(description="Check answer", button_style="primary")
    feedback = widgets.Output()

    def _on_click(_button):
        selected = {i for i, cb in enumerate(boxes) if cb.value}
        with feedback:
            feedback.clear_output(wait=True)
            print(feedback_correct if selected == correct else feedback_incorrect)

    button.on_click(_on_click)
    return widgets.VBox([widgets.HTML(f"<b>{prompt}</b>")] + boxes + [button, feedback])
'''.strip()


def _setup_cell(mode: str) -> dict:
    # Plain string substitution, not str.format(): the template is full of
    # f-strings and dict literals whose braces must NOT be treated as format
    # placeholders.
    source = SETUP_SOURCE_TEMPLATE.replace("{features_literal}", _feature_list_literal())
    return code(source, "wp41-000-setup", hidden=True)


def _run_first_notice() -> dict:
    # WP41R blocker 1: the setup cell's INPUT is collapsed (hidden=True,
    # above) and, before this notice existed, was also the very first thing
    # in the notebook -- nothing told a student it was there or that it had
    # to run before anything else. A fresh JupyterLite kernel has no
    # variables at all until this cell runs, so skipping it (easy to do:
    # click straight into a later cell and run only that one) surfaces as a
    # bare `NameError` on `load_abide_age_brain_table` several cells later,
    # not here. This notice, unlike the cell it describes, is never
    # collapsed.
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp41-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 2: Regression and Bias-Variance Trade-Off", "wp41-001-title"),
        md(
            """
## What this notebook covers

You will use linear regression and k-nearest-neighbours (KNN) regression to
predict a participant's **age** from their ABIDE-II brain measurements. Some
cells are supplied and ready to run; others ask you to write a few lines
yourself, answer a question in writing, or answer a checked question with
immediate feedback. Along the way you will explore how model complexity
trades bias against variance.
""",
            "wp41-002-overview",
        ),
    ]


def _section_1() -> list[dict]:
    return [
        md("## Section 1 — Load data and prepare the split", "wp41-101-header"),
        code(
            """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
""",
            "wp41-102-imports",
        ),
        code(
            """
# Load the established ABIDE-II age/brain table.
try:
    data = load_abide_age_brain_table()
except NameError as exc:
    raise RuntimeError(
        "load_abide_age_brain_table is not defined yet. Run this notebook's "
        "first code cell (collapsed, at the very top, under 'Run the cell "
        "below first') before this one, then run this cell again."
    ) from exc
FEATURES = [c for c in data.columns if c not in ("age", "group")]
print(f"{len(data)} participants, {len(FEATURES)} brain predictors")
data.head()
""",
            "wp41-103-load",
        ),
        code(
            """
# Define the target (age) and the feature matrix, then make the established
# reproducible split: 25% held out, stratified by diagnostic group so train
# and test have a similar autism/control mix.
X = data[FEATURES].to_numpy()
y = data["age"].to_numpy()
groups = data["group"].to_numpy()

X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(
    X, y, groups, test_size=0.25, random_state=42, stratify=groups
)
print(f"n_train = {len(y_train)}   n_test = {len(y_test)}")
""",
            "wp41-104-split",
        ),
        code(
            """
# Fit the scaler on training predictors only, then transform both sets.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
""",
            "wp41-105-scale",
        ),
    ]


def _section_2() -> list[dict]:
    cells: list[dict] = [
        md("## Section 2 — Inspect the split before modelling", "wp41-201-header"),
        md(
            "A practical check before fitting anything: are the train and test "
            "targets reasonably similar, and which features look related to age?",
            "wp41-202-intro",
        ),
        md("### Activity 2A — Compare target distributions", "wp41-203-2a-header"),
        md(
            """
Write code that:
- plots `y_train` and `y_test` using the **same bins and axis range**;
- reports n, mean, standard deviation, minimum, and maximum for each;
- uses readable labels and a legend.
""",
            "wp41-204-2a-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n",
            """
bins = np.linspace(min(y_train.min(), y_test.min()), max(y_train.max(), y_test.max()), 25)
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(y_train, bins=bins, alpha=0.6, label=f"train (n={len(y_train)})", density=True)
ax.hist(y_test, bins=bins, alpha=0.6, label=f"test (n={len(y_test)})", density=True)
ax.set_xlabel("age (years)")
ax.set_ylabel("density")
ax.set_title("Train vs. test age distribution")
ax.legend()
plt.show()

for name, arr in [("train", y_train), ("test", y_test)]:
    print(f"{name}: n={len(arr)}  mean={arr.mean():.1f}  sd={arr.std():.1f}  min={arr.min():.1f}  max={arr.max():.1f}")
""",
            "wp41-205-2a-blank",
            tags=["wp41-activity-2a"],
        ),
        md(
            "> Are the two distributions similar enough for this exercise? Name one "
            "similarity and one difference. Do not choose model settings from the "
            "test distribution.\n\nYOUR ANSWER HERE",
            "wp41-206-2a-answer",
        ),
    ]
    cells.append(_activity_2a_checked_question())
    cells += [
        md("### Activity 2B — Find features correlated with age", "wp41-208-2b-header"),
        md(
            """
Write **training-only** code that:
- calculates the Pearson correlation between every brain feature and `y_train`;
- sorts by absolute correlation;
- displays and plots the ten strongest relationships, preserving sign;
- uses shortened, readable region labels.
""",
            "wp41-209-2b-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n",
            """
train_df = pd.DataFrame(X_train, columns=FEATURES)
correlations = train_df.apply(lambda col: np.corrcoef(col, y_train)[0, 1])
top10 = correlations.reindex(correlations.abs().sort_values(ascending=False).index[:10])
short_labels = [c.replace("fsCT_", "").replace("_ROI", "") for c in top10.index]

fig, ax = plt.subplots(figsize=(6, 4))
colors = ["#2a6f9e" if v > 0 else "#b5622f" for v in top10.values]
ax.barh(short_labels[::-1], top10.values[::-1], color=colors[::-1])
ax.set_xlabel("Pearson correlation with age (training rows only)")
ax.set_title("Ten strongest age-correlated features")
plt.tight_layout()
plt.show()
display(top10.rename("correlation").to_frame())
""",
            "wp41-210-2b-blank",
            tags=["wp41-activity-2b"],
        ),
        md(
            "> Which two or three features do you expect to have large fitted "
            "coefficients, and why?\n\nYOUR ANSWER HERE",
            "wp41-211-2b-prediction",
        ),
    ]
    return cells


def _activity_2a_checked_question() -> dict:
    return code(
        """
display(make_multi_choice_question(
    "Which uses of the test target y_test are allowed at this point in the notebook?",
    [
        "Plotting its distribution to sanity-check the split (as above).",
        "Choosing which features to use because they correlate well with y_test.",
        "Reporting its mean and standard deviation.",
        "Tuning the model's settings so the test score looks better.",
    ],
    correct_indices={0, 2},
))
""",
        "wp41-207-2a-checked",
    )


def _section_3() -> list[dict]:
    cells: list[dict] = [
        md("## Section 3 — Fit linear regression", "wp41-301-header"),
        md("This is your first regression workflow, so it is supplied in full.", "wp41-302-intro"),
        code(
            """
model = LinearRegression()
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)
test_r2 = r2_score(y_test, y_pred)
test_mse = mean_squared_error(y_test, y_pred)
print(f"held-out R^2 = {test_r2:.3f}")
print(f"held-out MSE = {test_mse:.1f}  (RMSE {test_mse ** 0.5:.1f} years)")
""",
            "wp41-303-fit",
        ),
        md("### Activity 3A — Inspect coefficients", "wp41-304-3a-header"),
        md(
            """
Write code that:
- pairs the 360 feature names with their fitted coefficients;
- sorts by absolute magnitude;
- selects a readable number of the largest positive and negative coefficients;
- draws a labelled horizontal bar plot;
- describes the coefficient axis correctly for **standardized** predictors.
""",
            "wp41-305-3a-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n",
            """
coefs = pd.Series(model.coef_, index=FEATURES)
top_coefs = coefs.reindex(coefs.abs().sort_values(ascending=False).index[:10])
short_labels = [c.replace("fsCT_", "").replace("_ROI", "") for c in top_coefs.index]

fig, ax = plt.subplots(figsize=(6, 4))
colors = ["#2a6f9e" if v > 0 else "#b5622f" for v in top_coefs.values]
ax.barh(short_labels[::-1], top_coefs.values[::-1], color=colors[::-1])
ax.set_xlabel("fitted coefficient (years per 1 SD of standardized cortical thickness)")
ax.set_title("Ten largest-magnitude linear-regression coefficients")
plt.tight_layout()
plt.show()
""",
            "wp41-306-3a-blank",
            tags=["wp41-activity-3a"],
        ),
        md(
            "> Compare this ranking with Activity 2B's correlation ranking. Which "
            "features appear on both lists, and which do not?\n\nYOUR ANSWER HERE",
            "wp41-307-3a-answer",
        ),
        code(
            """
display(make_multi_choice_question(
    "Why can a feature's correlation with age and its fitted regression coefficient tell different stories?",
    [
        "Correlation is a marginal (feature-by-itself) relationship; a coefficient is conditional on every other feature already being in the model.",
        "Correlated predictors can share credit: a coefficient can shrink even for a feature with a strong marginal correlation once correlated neighbours absorb that signal.",
        "Coefficients are computed on the test set, so they answer a different question than a training-only correlation.",
        "The two measures are mathematically identical whenever the model is linear.",
    ],
    correct_indices={0, 1},
))
""",
            "wp41-308-3a-checked",
        ),
        md(
            "Marginal correlations and multivariable coefficients need not rank "
            "features identically -- a feature can correlate strongly with age on "
            "its own yet receive a small coefficient once correlated neighbouring "
            "regions are already in the model, and vice versa.",
            "wp41-309-3a-note",
        ),
        md("### Activity 3B — Create an observed-versus-predicted plot", "wp41-310-3b-header"),
        md(
            """
Create an observed-versus-predicted scatter plot from `y_test` and `y_pred`.
Your plot should have:

- observed age on the x-axis, predicted age on the y-axis;
- a visible perfect-prediction diagonal;
- readable axis labels;
- a useful title.

For reference, here is the approved current result:
""",
            "wp41-311-3b-instructions",
        ),
        md(
            _reference_image_markdown(),
            "wp41-312-3b-reference-image",
            attachments=_reference_image_attachments(),
        ),
        blank(
            "# YOUR CODE HERE\n",
            """
fig, ax = plt.subplots(figsize=(4.4, 4.4))
lims = [min(y_test.min(), y_pred.min()) - 3, max(y_test.max(), y_pred.max()) + 3]
ax.plot(lims, lims, "--", color="0.4", lw=1, label="Perfect prediction")
ax.scatter(y_test, y_pred, s=16, alpha=0.5)
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect("equal")
ax.set_xlabel("observed age (years)")
ax.set_ylabel("predicted age (years, held-out)")
ax.set_title(f"Linear regression, held-out R^2 = {test_r2:.3f}")
ax.legend(loc="upper left", fontsize=8)
plt.show()
""",
            "wp41-313-3b-blank",
            tags=["wp41-activity-3b"],
        ),
        md(
            "> How closely do the held-out points track the diagonal? Where do "
            "the largest errors fall?\n\nYOUR ANSWER HERE",
            "wp41-314-3b-answer",
        ),
    ]
    return cells


REFERENCE_IMAGE_FILENAME = "exercise_02_observed_vs_predicted.png"


def _reference_image_attachments() -> dict:
    # WP41R blocker 2: a notebook *attachment* keeps the huge base64 payload
    # out of the cell's visible markdown source. The bytes still live in the
    # .ipynb JSON (cell["attachments"]), but a student who clicks into this
    # cell to leave/re-enter edit mode sees only the short
    # "attachment:<filename>" reference below, not a page-length data URI --
    # and this is core nbformat, not a JupyterLite-only trick, so it renders
    # the same way in JupyterLite, local Jupyter/nbclient, and Colab.
    return {REFERENCE_IMAGE_FILENAME: {"image/png": _reference_image_data_uri()}}


def _reference_image_markdown() -> str:
    return f"![Approved observed-vs-predicted result](attachment:{REFERENCE_IMAGE_FILENAME})"


def _section_4() -> list[dict]:
    return [
        md("## Section 4 — Correct and misleading evaluation", "wp41-401-header"),
        md(
            "Same fixed split, same recipe, three ways to score the same model.",
            "wp41-402-intro",
        ),
        code(
            """
train_pred = model.predict(X_train_scaled)
train_r2 = r2_score(y_train, train_pred)
train_mse = mean_squared_error(y_train, train_pred)

# A deliberately INVALID model: fit on the test rows, scored on those same
# test rows. Note n_test (251) is smaller than the number of features (360),
# so this fit is not just optimistic -- it is underdetermined.
invalid_model = LinearRegression().fit(X_test_scaled, y_test)
invalid_pred = invalid_model.predict(X_test_scaled)
invalid_r2 = r2_score(y_test, invalid_pred)
invalid_mse = mean_squared_error(y_test, invalid_pred)

comparison = pd.DataFrame(
    {
        "fit on": ["training rows", "training rows", "test rows (INVALID)"],
        "evaluated on": ["test rows", "training rows", "same test rows"],
        "R^2": [test_r2, train_r2, invalid_r2],
        "MSE": [test_mse, train_mse, invalid_mse],
    },
    index=["A. correct", "B. training score", "C. invalid"],
)
display(comparison.round(3))
""",
            "wp41-403-panels",
        ),
        md(
            "**B is not a competing model.** A high training score next to a "
            "lower test score is the signature of a model fitting noise it "
            "cannot reproduce on new data. **C is not a competing model "
            "either** -- with 360 features and only 251 test rows, fitting on "
            "the test rows is underdetermined and reproduces those rows almost "
            "exactly, which is not the same as learning something that "
            "generalises.",
            "wp41-404-explanation",
        ),
        code(
            """
display(make_single_choice_question(
    "Which evaluation can estimate performance for a new participant?",
    ["A. correct", "B. training score", "C. invalid"],
    correct_index=0,
    feedback_correct="Correct: only scoring on held-out rows the model never touched during fitting estimates performance on a new participant.",
    feedback_incorrect="Not quite -- both training-row evaluation and fitting on test rows are misleading.",
))
""",
            "wp41-405-checked",
        ),
    ]


def _section_5() -> list[dict]:
    return [
        md("## Section 5 — Build KNN regression yourselves", "wp41-501-header"),
        md(
            "KNN predicts a participant's age from the ages of the `k` nearest "
            "training participants (by feature distance). `k` controls model "
            "complexity: it is yours to build this time.",
            "wp41-502-intro",
        ),
        md(
            """
Write code that:
1. imports `KNeighborsRegressor`;
2. creates a model with `k=20`;
3. fits it on `X_train_scaled` and `y_train`;
4. predicts `X_test_scaled`;
5. calculates R² and MSE;
6. produces an observed-versus-predicted plot;
7. compares it with linear regression in the answer cell below.
""",
            "wp41-503-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# from sklearn.neighbors import ...
# knn_model = ...
# knn_pred = ...
# knn_r2 = ...
# knn_mse = ...
""",
            """
from sklearn.neighbors import KNeighborsRegressor

knn_model = KNeighborsRegressor(n_neighbors=20)
knn_model.fit(X_train_scaled, y_train)
knn_pred = knn_model.predict(X_test_scaled)
knn_r2 = r2_score(y_test, knn_pred)
knn_mse = mean_squared_error(y_test, knn_pred)
print(f"KNN (k=20) held-out R^2 = {knn_r2:.3f}")
print(f"KNN (k=20) held-out MSE = {knn_mse:.1f}  (RMSE {knn_mse ** 0.5:.1f} years)")

fig, ax = plt.subplots(figsize=(4.4, 4.4))
lims = [min(y_test.min(), knn_pred.min()) - 3, max(y_test.max(), knn_pred.max()) + 3]
ax.plot(lims, lims, "--", color="0.4", lw=1, label="Perfect prediction")
ax.scatter(y_test, knn_pred, s=16, alpha=0.5)
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect("equal")
ax.set_xlabel("observed age (years)")
ax.set_ylabel("predicted age (years, held-out)")
ax.set_title(f"KNN (k=20), held-out R^2 = {knn_r2:.3f}")
ax.legend(loc="upper left", fontsize=8)
plt.show()
""",
            "wp41-504-blank",
            tags=["wp41-activity-5"],
        ),
        md(
            "> How does KNN (k=20) compare with linear regression on this same "
            "split?\n\nYOUR ANSWER HERE",
            "wp41-505-answer",
        ),
        code(
            """
# A graceful check: verifies your KNN result without breaking later,
# independent sections if something above is still incomplete.
if "knn_pred" in globals() and "knn_r2" in globals():
    assert len(knn_pred) == len(y_test), "knn_pred should have one prediction per test row"
    assert np.isfinite(knn_r2) and np.isfinite(knn_mse), "R^2 and MSE should be finite numbers"
    print("Looks good: knn_pred, knn_r2, and knn_mse are all present and finite.")
else:
    print("Not complete yet: define knn_pred, knn_r2, and knn_mse above first.")
""",
            "wp41-506-check",
        ),
    ]


def _section_6() -> list[dict]:
    return [
        md("## Section 6 — Bias and variance", "wp41-601-header"),
        md(
            r"""
For a model predicting outcome $Y$ from features $X$, the expected squared
prediction error on a new observation decomposes as

$$\mathbb{E}\left[(Y-\hat f(X))^2\right] = \operatorname{Bias}(\hat f(X))^2 + \operatorname{Var}(\hat f(X)) + \sigma^2.$$

For KNN, `k` controls this directly:

- **small `k`** means greater model complexity, lower bias, and higher variance;
- **large `k`** means lower model complexity, higher bias, and lower variance.
""",
            "wp41-602-theory",
        ),
        code(
            """
# CONCEPTUAL illustration only -- smooth idealised curves, not measured from
# the ABIDE data. Section 7 computes the empirical analogue.
flexibility = np.linspace(0.02, 1, 200)
bias_sq = (1 - flexibility) ** 2 * 2.2
variance = flexibility ** 2.2 * 2.0
irreducible = np.full_like(flexibility, 0.35)
expected_test_error = bias_sq + variance + irreducible

fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.plot(flexibility, bias_sq, label="squared bias", color="#2a6f9e")
ax.plot(flexibility, variance, label="variance", color="#b5622f")
ax.plot(flexibility, irreducible, label="irreducible error", color="0.6", ls=":")
ax.plot(flexibility, expected_test_error, label="expected test error", color="black", lw=2)
ax.set_xlabel("model flexibility (small k -> large k, right to left)")
ax.set_ylabel("error (schematic units)")
ax.set_title("The classic bias-variance tradeoff")
ax.legend(fontsize=8)
plt.show()
""",
            "wp41-603-figure",
        ),
        code(
            """
display(make_single_choice_question(
    "Which of these changes increases KNN's model complexity?",
    ["Decreasing k", "Increasing k", "Model complexity does not depend on k"],
    correct_index=0,
))
""",
            "wp41-604-checked",
        ),
    ]


def _knn_sweep_code() -> str:
    return """
# This section uses only the outer-training partition (X_train, y_train) --
# the outer test set from Sections 3-5 is never touched here. Split it again
# into a fitting group and a validation group.
X_fit, X_val, y_fit, y_val = train_test_split(
    X_train, y_train, test_size=0.25, random_state=7, stratify=groups_train
)
N_FIT = len(y_fit)

scaler_dev = StandardScaler().fit(X_fit)
Xf = scaler_dev.transform(X_fit)
Xv = scaler_dev.transform(X_val)


def _sorted_neighbor_targets(X_query, X_ref, y_ref):
    d = np.linalg.norm(X_query[:, None, :] - X_ref[None, :, :], axis=2)
    order = np.argsort(d, axis=1, kind="stable")
    return y_ref[order]


sorted_val = _sorted_neighbor_targets(Xv, Xf, y_fit)
sorted_fit = _sorted_neighbor_targets(Xf, Xf, y_fit)
ks = np.arange(1, N_FIT + 1)
val_pred_by_k = np.cumsum(sorted_val, axis=1) / ks
fit_pred_by_k = np.cumsum(sorted_fit, axis=1) / ks
val_mse = ((val_pred_by_k - y_val[:, None]) ** 2).mean(axis=0)
fit_mse = ((fit_pred_by_k - y_fit[:, None]) ** 2).mean(axis=0)
val_optimal_k = int(ks[np.argmin(val_mse)])
print(f"fitting participants = {N_FIT}   validation participants = {len(y_val)}")
print(f"k with lowest validation error = {val_optimal_k}")
""".strip()


def _section_7() -> list[dict]:
    return [
        md("## Section 7 — Performance across model complexity", "wp41-701-header"),
        code(_knn_sweep_code(), "wp41-702-sweep"),
        code(
            """
# Model complexity increases as k decreases, so plot against 1/k and let
# larger complexity run left to right. Integer k values stay visible as
# tick labels on a companion top axis.
complexity = 1.0 / ks

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(complexity, fit_mse, label="fitting MSE (resubstitution)", color="#2a6f9e")
ax.plot(complexity, val_mse, label="validation MSE", color="#b5622f")
ax.axvline(1.0 / val_optimal_k, color="0.6", lw=1, ls=":")
ax.set_xlabel("Model complexity")
ax.set_ylabel("mean squared error (years$^2$)")
ax.set_title("Fitting vs. validation error across model complexity")
ax.legend(fontsize=8)

k_ticks = [N_FIT, 100, 20, val_optimal_k, 5, 1]
k_ticks = sorted(set(k for k in k_ticks if 1 <= k <= N_FIT))
ax_top = ax.secondary_xaxis("top", functions=(lambda c: 1.0 / c, lambda k: 1.0 / k))
ax_top.set_xticks(k_ticks)
ax_top.set_xlabel("k (for reference)")
plt.tight_layout()
plt.show()
""",
            "wp41-703-plot",
        ),
        md(
            "Fitting error keeps falling as complexity grows (perfect at k=1, "
            "the same resubstitution optimism from Section 4) while validation "
            "error is lowest at an intermediate complexity and rises again "
            "toward both ends -- the empirical signature of the classic "
            "bias-variance curve from Section 6.",
            "wp41-704-explanation",
        ),
    ]


def _section_8() -> list[dict]:
    return [
        md("## Section 8 — Explore model complexity", "wp41-801-header"),
        md(
            "Move the slider or type a value to refit KNN at a different `k` "
            "and watch the observed-versus-predicted plot and the error curve "
            "position change together. Three deterministic training-sample "
            "resamples are overlaid so you can see how much predictions shift "
            "at a given `k` just from which fitting participants happened to "
            "be drawn.",
            "wp41-802-intro",
        ),
        code(
            """
# This activity's own KNN fits do not depend on Section 5's import: it runs
# correctly whether or not you have completed that activity yet.
from sklearn.neighbors import KNeighborsRegressor

_rng = np.random.default_rng(41)
_resample_idx = [_rng.choice(N_FIT, size=N_FIT, replace=True) for _ in range(3)]
_resample_colors = ["#2a6f9e", "#b5622f", "#4c9a5b"]

k_slider = widgets.IntSlider(value=20, min=1, max=N_FIT, step=1, description="k:")
k_input = widgets.BoundedIntText(value=20, min=1, max=N_FIT, description="k (exact):")
k_output = widgets.Output()


def _explore_refit(k):
    with k_output:
        k_output.clear_output(wait=True)
        fig, (ax_scatter, ax_curve) = plt.subplots(1, 2, figsize=(10, 4))

        for idx, color in zip(_resample_idx, _resample_colors):
            model_r = KNeighborsRegressor(n_neighbors=k).fit(Xf[idx], y_fit[idx])
            pred_r = model_r.predict(Xv)
            ax_scatter.scatter(y_val, pred_r, s=12, alpha=0.5, color=color)
        lims = [y_val.min() - 3, y_val.max() + 3]
        ax_scatter.plot(lims, lims, "--", color="0.4", lw=1)
        ax_scatter.set_xlim(lims)
        ax_scatter.set_ylim(lims)
        ax_scatter.set_aspect("equal")
        ax_scatter.set_xlabel("observed age (years)")
        ax_scatter.set_ylabel("predicted age (years)")
        ax_scatter.set_title(f"k={k}  (three training-sample resamples)")

        ax_curve.plot(1.0 / ks, fit_mse, color="#2a6f9e", label="fitting MSE")
        ax_curve.plot(1.0 / ks, val_mse, color="#b5622f", label="validation MSE")
        ax_curve.axvline(1.0 / k, color="black", lw=1.5)
        ax_curve.set_xlabel("Model complexity")
        ax_curve.set_ylabel("mean squared error (years$^2$)")
        ax_curve.set_title("Your current k on the error curve")
        ax_curve.legend(fontsize=8)
        plt.tight_layout()
        plt.show()
        print(f"k = {k}   model complexity (1/k) = {1.0 / k:.3f}")


def _on_k_change(change):
    if change["name"] == "value":
        k_input.value = change["new"]
        k_slider.value = change["new"]
        _explore_refit(change["new"])


k_slider.observe(_on_k_change, names="value")
k_input.observe(_on_k_change, names="value")
display(widgets.VBox([k_slider, k_input, k_output]))
_explore_refit(k_slider.value)
""",
            "wp41-803-widget",
        ),
        code(
            """
display(make_single_choice_question(
    "In this activity, what happens to the three training-sample resamples' scatter as k grows very large?",
    [
        "They converge toward the same near-constant predictions.",
        "They spread further apart from each other.",
        "They become identical to the k=1 scatter.",
    ],
    correct_index=0,
    feedback_correct="Correct: at large k every resample averages over nearly the whole fitting set, so predictions converge toward the fitting-set mean regardless of which participants happened to be resampled.",
))
""",
            "wp41-804-checked",
        ),
    ]


def _bonus_section() -> list[dict]:
    return [
        md("## Bonus — Feature sets and sample size", "wp41-901-header"),
        md(
            "This section is optional and not required for the core session, "
            "and it is a teaching demonstration, not a rigorous protocol: "
            "trying many feature sets or sample sizes below is exploratory "
            "comparison, not formal feature selection -- the held-out score "
            "of the best-looking option is not an unbiased estimate of its "
            "true performance. The 10-feature set below was fixed in advance "
            "and is not chosen by ranking feature correlations the way "
            "Activity 2B did.",
            "wp41-902-intro",
        ),
        code(
            """
# A small, fixed 10-column cortical-thickness subset, unrelated to the
# 360-feature recipe used everywhere else in this notebook: the bilateral
# sensorimotor strip (primary motor cortex, BA4, plus primary somatosensory
# cortex BA 3a/3b/1/2).
SAMPLE_SIZE_ROIS = ["4", "3a", "3b", "1", "2"]
FEATURES_SS = [f"fsCT_{hemi}_{roi}_ROI" for roi in SAMPLE_SIZE_ROIS for hemi in ("L", "R")]

data_ss = data[FEATURES_SS + ["age", "group"]]
X_ss = data_ss[FEATURES_SS].to_numpy()
y_ss = data_ss["age"].to_numpy()
groups_ss = data_ss["group"].to_numpy()
X_train_ss, X_test_ss, y_train_ss, y_test_ss = train_test_split(
    X_ss, y_ss, test_size=0.25, random_state=42, stratify=groups_ss
)

sizes = [40, 60, 90, 130, 200, 300, len(y_train_ss)]
n_repeats = 15
rng = np.random.default_rng(11)
med_r2, lo_r2, hi_r2 = [], [], []

scaler_ss = StandardScaler().fit(X_train_ss)
X_train_ss_scaled = scaler_ss.transform(X_train_ss)
X_test_ss_scaled = scaler_ss.transform(X_test_ss)

for n in sizes:
    scores = []
    for _ in range(n_repeats):
        idx = rng.choice(len(y_train_ss), size=min(n, len(y_train_ss)), replace=False)
        m = LinearRegression().fit(X_train_ss_scaled[idx], y_train_ss[idx])
        scores.append(r2_score(y_test_ss, m.predict(X_test_ss_scaled)))
    scores = np.array(scores)
    med_r2.append(np.median(scores))
    lo_r2.append(np.percentile(scores, 10))
    hi_r2.append(np.percentile(scores, 90))

fig, ax = plt.subplots(figsize=(6, 4))
ax.fill_between(sizes, lo_r2, hi_r2, alpha=0.25, label="10th-90th percentile")
ax.plot(sizes, med_r2, "o-", label="median held-out R$^2$")
ax.axhline(0, color="0.5", lw=1, ls=":")
ax.set_xlabel("training-set size")
ax.set_ylabel("held-out R^2")
ax.set_title(f"Sample size vs. accuracy ({len(FEATURES_SS)}-feature sensorimotor recipe)")
ax.legend(fontsize=8)
plt.show()
""",
            "wp41-903-code",
        ),
        md(
            "Median held-out R² climbs and the 10th-90th percentile band "
            "narrows as the training set grows: repeated resampling reduces "
            "the influence of any one unusually easy or hard draw, so the "
            "typical trend is what matters. This is a property of this small, "
            "fixed 10-feature recipe -- it does not describe the whole-cortex "
            "360-feature recipe used everywhere else in this notebook.",
            "wp41-904-explanation",
        ),
    ]


def _summary() -> list[dict]:
    return [
        md(
            """
## In summary

- A performance estimate that fits on training data and scores on data the
  model has never seen avoids inflated results; scoring on the fitting rows
  themselves inflates the number, whether those rows are the training set
  (optimistic) or, worse, the test set (invalid).
- `age` has a genuinely positive held-out R² from cortical thickness alone,
  for both linear regression and KNN.
- KNN's `k` directly controls model complexity: small `k` means high
  complexity, low bias, high variance; large `k` means low complexity,
  higher bias, lower variance.
""",
            "wp41-999-summary",
        )
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1()
    section_2 = _section_2()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_2]
    section_3 = _section_3()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_3]
    cells += _section_4()
    section_5 = _section_5()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_5]
    cells += _section_6()
    cells += _section_7()
    cells += _section_8()
    cells += _bonus_section()
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
