#!/usr/bin/env python3
"""Generate Exercise 1's JupyterLite template, portable copy, and reference.

WP42 Gate 2: migrates Exercise 1 (Exploratory Data Analysis) onto the same
JupyterLite-native platform WP41 built for Exercise 2. Mirrors
scripts/generate_exercise_02_notebook.py's shape exactly: one authoritative
structured source; every "YOUR CODE HERE" activity is a (starter, solution)
``Blank`` pair; ``--student`` renders the starter side, ``--reference`` the
solved side used only by tests.

Preserves the established curated ABIDE-II teaching table (13 columns, see
book/config/eda_phenotype_columns.json), its approved numbers, and Pearson-
only scope. Seaborn is not used anywhere (no prebuilt Pyodide wheel; the
maintainer guide's portable-package convention is numpy/pandas/scikit-learn/
matplotlib/ipywidgets only) -- every plot the old notebook built with
seaborn is rebuilt here in plain Matplotlib instead, which is also what
keeps this notebook running unmodified in JupyterLite, a downloaded local
Jupyter, and Colab (no environment-conditional plotting import needed).

Outputs:
  book/lite/files/exercise_01.ipynb                    (--student, JupyterLite)
  book/downloads/chapter_01/exercise_01_portable.ipynb (--student, Colab/local)
  book/lite/files/exercise_01_portable.ipynb           (--student, same file,
                                                          served copy)
  scripts/reference_notebooks/exercise_01_reference.ipynb (--reference)

Modes:
  --write   regenerate the selected output(s) on disk.
  --check   regenerate in memory and fail if a committed file is stale.
  --student / --reference / --all (default --all with --write or --check)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO_ROOT = Path(__file__).resolve().parents[1]
CURATED_COLUMNS_PATH = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
DATA_SIDECAR = REPO_ROOT / "book" / "lite" / "files" / "data" / "abide_phenotypes.manifest.json"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_01.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb"
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_01_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_01_reference.ipynb"

TEMPLATE_VERSION = 2

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 1, "templateVersion": TEMPLATE_VERSION},
}


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


def _curated_columns_literal() -> str:
    cols = json.loads(CURATED_COLUMNS_PATH.read_text())
    lines = ["_CURATED_COLUMNS = ["]
    for i in range(0, len(cols), 4):
        chunk = ", ".join(repr(c) for c in cols[i : i + 4])
        lines.append(f"    {chunk},")
    lines.append("]")
    return "\n".join(lines)


SETUP_SOURCE_TEMPLATE = '''
import sys
import warnings

# This pinned browser kernel's matplotlib/backend combination emits a
# benign MatplotlibDeprecationWarning about float pixel coordinates on
# every figure it draws, independent of anything this notebook's own code
# does (root-caused by live bisection for this course's other exercises).
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
from IPython.display import display

{curated_columns_literal}


def load_abide_phenotypes():
    """Return the curated 13-column ABIDE-II phenotype table (see
    book/config/eda_phenotype_columns.json), before any dtype conversion.

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout); falls back to the same pinned
    public source this course already used before this notebook's
    migration (a bare downloaded .ipynb, or Colab, neither of which has the
    sibling data file). Both paths return identically shaped, identically
    ordered columns.
    """
    from pathlib import Path

    local_path = Path("data/abide_phenotypes.csv")
    if local_path.exists():
        table = pd.read_csv(local_path)
    else:
        url = (
            "https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/"
            "e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/"
            "tu-machine-learning-yarkoni/data/abide2_phenotypic.csv"
        )
        table = pd.read_csv(url, encoding="latin-1", low_memory=False)
        table.columns = table.columns.str.strip()
    return table[_CURATED_COLUMNS].copy()


# Keeps every checked question's and every checkbox-group activity's option
# text wrapping within the notebook's own width, at any viewport, instead of
# being cut off with an ellipsis (ipywidgets' own stylesheet gives
# ".widget-checkbox"/".widget-label-basic" a fixed 300px width with
# "white-space: nowrap" + "text-overflow: ellipsis" -- confirmed live in a
# real JupyterLite browser at 390px).
_WRAP_CSS = """
<style>
.wrap-labels .widget-checkbox { width: 100% !important; height: auto !important; }
.wrap-labels .widget-label-basic {
    width: 100% !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    height: auto !important;
}
.wrap-labels .widget-radio-box { width: 100% !important; }
.wrap-labels .widget-radio-box label {
    width: 100% !important;
    max-width: 100% !important;
    white-space: normal !important;
    box-sizing: border-box;
}
</style>
"""


def _wrap_style_widget():
    return widgets.HTML(_WRAP_CSS, layout=widgets.Layout(height="0px", margin="0px", padding="0px"))


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
        [_wrap_style_widget(), widgets.HTML(f"<b>{prompt}</b>"), radio, button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("wrap-labels")
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
        [_wrap_style_widget(), widgets.HTML(f"<b>{prompt}</b>")] + boxes + [button, feedback],
        layout=widgets.Layout(width="100%"),
    )
    box.add_class("wrap-labels")
    return box


# Question content lives here, not in the visible cell that displays it: a
# visible call like show_question("q-histogram-bins") never prints or
# displays a correct_index/correct_indices value (WP48's "Multiple-choice
# answer visibility" requirement -- see scripts/generate_exercise_08_notebook.py
# for the pattern this mirrors). This is visual concealment, not secure
# assessment: the hidden cell is fully expandable, and a downloaded, fully
# offline, editable notebook must contain enough information to check an
# answer locally, so a technically curious student can always recover it
# from source or the running kernel.
_QUESTIONS = {
    "q-categorical-columns": dict(
        kind="multi",
        prompt="Which of these columns should be treated as categorical, even though some are stored as numbers?",
        options=[
            "DX_GROUP (diagnosis code)",
            "AGE_AT_SCAN (age in years)",
            "SEX (coded 1/2)",
            "FIQ (full-scale IQ score)",
            "HANDEDNESS_CATEGORY (coded 1/2/3)",
        ],
        correct_indices={0, 2, 4},
    ),
    "q-histogram-bins": dict(
        kind="single",
        prompt="Using very few histogram bins mainly risks:",
        options=[
            "Hiding real structure in the distribution (e.g. two separate peaks).",
            "Turning random noise into apparent structure.",
            "Changing the underlying data values.",
        ],
        correct_index=0,
    ),
    "q-fiq-correlation": dict(
        kind="multi",
        prompt="FIQ correlates strongly with VIQ and PIQ (r ~ 0.83). What does that tell you?",
        options=[
            "Full-scale IQ is computed from the verbal and performance scores, so a strong correlation is expected by construction.",
            "It is strong evidence of a specific brain mechanism linking the three scores.",
            "VIQ and PIQ are two separate sub-scores, so their own correlation with each other can still be moderate.",
            "A correlation this strong proves FIQ causes changes in VIQ.",
        ],
        correct_indices={0, 2},
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
    source = SETUP_SOURCE_TEMPLATE.replace("{curated_columns_literal}", _curated_columns_literal())
    return code(source, "wp42-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp42-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 1: Exploratory Data Analysis", "wp42-001-title"),
        md(
            """
## What this notebook covers

You will apply exploratory data analysis (EDA) to real ABIDE-II phenotypic
data: inspecting rows, summarizing variables, quantifying and handling
missing values, and looking at distributions and correlations. Some cells
are supplied and ready to run; others ask you to write a few lines
yourself, answer a question in writing, or answer a checked question with
immediate feedback.

Written-answer cells (like the bold question below) are ordinary Markdown:
double-click to edit, type your answer, then press Shift+Enter to render it
back. Your answer is saved with the rest of this notebook, including in
**Download my notebook**.
""",
            "wp42-002-overview",
        ),
    ]


def _section_1() -> list[dict]:
    return [
        md("## Section 1 -- Load the data", "wp42-101-header"),
        md(
            "The [ABIDE-II](https://fcon_1000.projects.nitrc.org/indi/abide/abide_II.html) "
            "phenotypic table combines data from 19 research sites. This notebook uses a "
            "curated 13-column subset covering site, diagnosis, demographics, IQ, and a "
            "few behavioral scores.",
            "wp42-102-intro",
        ),
        code(
            """
# Load the curated ABIDE-II phenotype table (13 columns).
try:
    data = load_abide_phenotypes()
except NameError as exc:
    raise RuntimeError(
        "load_abide_phenotypes is not defined yet. Run this notebook's "
        "first code cell (collapsed, at the very top, under 'Run the cell "
        "below first') before this one, then run this cell again."
    ) from exc
print(f"Data table shape: {data.shape}")
data.head()
""",
            "wp42-103-load",
        ),
    ]


def _section_2() -> list[dict]:
    cells: list[dict] = [
        md("## Section 2 -- Inspect rows", "wp42-201-header"),
        md(
            "`head()`, `tail()`, and `sample()` all pull out rows, but they answer "
            "different questions. `head()` shows the first rows:",
            "wp42-202-intro",
        ),
        code(
            """
# data.head() shows five rows by default; data.head(n=8) shows eight participants.
data.head()
""",
            "wp42-203-head",
        ),
        md(
            """
Now write code that:
- shows the **last** rows with `tail()`;
- draws a **random** sample of rows with `sample()` (pass `random_state=0` so
  it is reproducible);
- uses the same number of rows (e.g. 8) for both, and shows all 13 columns.
""",
            "wp42-204-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n",
            """
display(data.tail(8))
display(data.sample(8, random_state=0))
""",
            "wp42-205-blank",
            tags=["wp42-activity-tail-sample"],
        ),
        md(
            "> **`head()` and `tail()` are deterministic; `sample()` is not. Looking "
            "at the `SITE_ID` column across the three views, what does that tell you "
            "about how the table is ordered, and why might that matter if you only "
            "ever used `head()` to check a dataset?**",
            "wp42-206-answer",
        ),
    ]
    return cells


def _section_3() -> list[dict]:
    return [
        md("## Section 3 -- Statistical inspection", "wp42-301-header"),
        md(
            "`info()` reports the shape, data types, and non-missing counts of every "
            "column in one call.",
            "wp42-302-intro",
        ),
        code("data.info()", "wp42-303-info"),
        md(
            """
A column's **storage type** is not always its **statistical type**. Here
`SITE_ID` is text; `DX_GROUP`, `SEX`, `HANDEDNESS_CATEGORY`, and
`CURRENT_MED_STATUS` are stored as numbers but are really categories
(diagnosis, sex, handedness, medication status) -- pandas does not know that
unless told:
""",
            "wp42-304-categorical-intro",
        ),
        code(
            """
categorical_columns = ["SITE_ID", "DX_GROUP", "SEX", "HANDEDNESS_CATEGORY", "CURRENT_MED_STATUS"]
data[categorical_columns] = data[categorical_columns].astype("category")
data["SUB_ID"] = data["SUB_ID"].astype("string")  # a label, not a measurement
""",
            "wp42-305-categorical-cast",
        ),
        code(
            """
show_question("q-categorical-columns")
""",
            "wp42-306-checked",
        ),
        md(
            "`describe()` summarizes every numerical column: count, mean, standard "
            "deviation, min/max, and quartiles.",
            "wp42-307-describe-intro",
        ),
        code("data.describe().T", "wp42-308-describe"),
    ]


def _section_4() -> list[dict]:
    cells: list[dict] = [
        md("## Section 4 -- Quantify missingness", "wp42-401-header"),
        md(
            """
Write code that builds a table with one row per column and two columns of
its own: `n_missing` and `percent_missing` (0-100, one decimal place), sorted
with the most-missing column first. *Hint:* `data.isna().sum()` counts
missing values per column; `data.isna().mean() * 100` gives the percentage.
""",
            "wp42-402-instructions",
        ),
        blank(
            """
# YOUR CODE HERE
# missing_summary = pd.DataFrame({
#     "n_missing": ...,
#     "percent_missing": ...,
# })
""",
            """
missing_summary = pd.DataFrame(
    {
        "n_missing": data.isna().sum(),
        "percent_missing": (data.isna().mean() * 100).round(1),
    }
).sort_values("n_missing", ascending=False)
display(missing_summary.query("n_missing > 0"))
""",
            "wp42-403-blank",
            tags=["wp42-activity-missing-summary"],
        ),
        code(
            """
# A student-facing check: verifies your missingness table without breaking
# later, independent sections if something above is still incomplete.
if "missing_summary" in globals():
    assert {"n_missing", "percent_missing"} <= set(missing_summary.columns), (
        "missing_summary should have n_missing and percent_missing columns"
    )
    assert missing_summary["n_missing"].max() <= len(data), "n_missing cannot exceed the number of rows"
    top = missing_summary["n_missing"].idxmax()
    print(f"Looks good: most-missing column is {top!r} with {int(missing_summary.loc[top, 'n_missing'])} missing.")
else:
    print("Not complete yet: define missing_summary above first.")
""",
            "wp42-404-check",
        ),
        md("Is missingness spread evenly across acquisition sites?", "wp42-405-heatmap-intro"),
        code(
            """
# Computed directly from data (not from missing_summary above): a supplied
# cell must not depend on a still-incomplete student activity, or one
# unfinished blank would cascade into every independent cell after it.
top_missing = data.isna().sum().sort_values(ascending=False).head(10).index
missing_by_site = (
    data[top_missing].isna().groupby(data["SITE_ID"], observed=True).mean() * 100
)

fig, ax = plt.subplots(figsize=(9, 6))
im = ax.imshow(missing_by_site.to_numpy(), cmap="Reds", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(top_missing)))
ax.set_xticklabels(top_missing, rotation=45, ha="right")
ax.set_yticks(range(len(missing_by_site)))
ax.set_yticklabels(missing_by_site.index, fontsize=7)
fig.colorbar(im, ax=ax, label="% missing")
ax.set_title("Missingness by acquisition site")
plt.tight_layout()
plt.show()
""",
            "wp42-406-heatmap",
        ),
        md(
            "> **Pick one column above that is missing only at a handful of sites. "
            "What does that suggest about why it is missing?**",
            "wp42-407-heatmap-answer",
        ),
        md(
            "### Complete-case retention explorer\n\nTick the variables you would "
            "require for an analysis. A participant is kept only if every ticked "
            "variable is recorded for them.",
            "wp42-408-retention-intro",
        ),
        code(_retention_widget_code(), "wp42-409-retention-widget"),
        md(
            "> **Compare a minimal selection (e.g. diagnosis, age, sex) with a "
            "richer one that adds a behavioral score such as the SRS or ADOS-G "
            "total. How much does the retained sample shrink, and which sites "
            "disappear first?**",
            "wp42-410-retention-answer",
        ),
    ]
    return cells


def _retention_widget_code() -> str:
    return """
_RETENTION_VARIABLES = [
    ("Diagnostic group", "DX_GROUP", True),
    ("Age at scan", "AGE_AT_SCAN", True),
    ("Sex", "SEX", True),
    ("Handedness category", "HANDEDNESS_CATEGORY", False),
    ("Full-scale IQ", "FIQ", True),
    ("Verbal IQ", "VIQ", False),
    ("Performance IQ", "PIQ", False),
    ("Current medication status", "CURRENT_MED_STATUS", False),
    ("SRS total (raw)", "SRS_TOTAL_RAW", False),
    ("ADOS-G total", "ADOS_G_TOTAL", False),
    ("ADI-R social total", "ADI_R_SOCIAL_TOTAL_A", False),
]
_retention_boxes = [
    widgets.Checkbox(value=default, description=label, indent=False, layout=widgets.Layout(width="100%"))
    for label, _col, default in _RETENTION_VARIABLES
]
_retention_output = widgets.Output()


def _refresh_retention(_change=None):
    with _retention_output:
        _retention_output.clear_output(wait=True)
        chosen = [col for box, (_label, col, _default) in zip(_retention_boxes, _RETENTION_VARIABLES) if box.value]
        if not chosen:
            print("Tick at least one variable.")
            return
        complete = data.dropna(subset=chosen)
        pct_overall = len(complete) / len(data) * 100
        print(f"Retained: {len(complete)} of {len(data)} participants ({pct_overall:.1f}%)")

        is_complete = data[chosen].notna().all(axis=1)
        by_site = (
            is_complete.groupby(data["SITE_ID"], observed=True).mean().mul(100).sort_values(ascending=False)
        )
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(range(len(by_site)), by_site.to_numpy(), color="#2a6f9e")
        ax.set_xticks(range(len(by_site)))
        ax.set_xticklabels(by_site.index, rotation=90, fontsize=6)
        ax.set_ylabel("% retained")
        ax.set_ylim(0, 100)
        ax.set_title("Retention by acquisition site")
        plt.tight_layout()
        plt.show()


for _box in _retention_boxes:
    _box.observe(_refresh_retention, names="value")
_retention_panel = widgets.VBox(
    [_wrap_style_widget(), widgets.HTML("<b>Required variables:</b>")] + _retention_boxes + [_retention_output],
    layout=widgets.Layout(width="100%"),
)
_retention_panel.add_class("wrap-labels")
display(_retention_panel)
_refresh_retention()
""".strip()


def _section_5() -> list[dict]:
    return [
        md("## Section 5 -- Handle missing values", "wp42-501-header"),
        md(
            """
| Approach | When it is useful | Main caution |
| --- | --- | --- |
| **Remove** incomplete rows or a variable | The missing fraction is small, or the variable is not needed | Can discard many participants at once |
| **Fill in** with a summary statistic (e.g. the median) | You need every row for a later step | Understates the true variability |
| **Explicit "missing" category** (categorical variables only) | The absence of a value may itself be meaningful | Can leak site/cohort identity |
""",
            "wp42-502-table",
        ),
        md(
            """
Write code that:
1. drops every incomplete row into a **new** dataframe called `data_complete`
   (`data` itself must stay unchanged);
2. prints the original and the retained number of rows.
""",
            "wp42-503-drop-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# data_complete = ...\n",
            """
data_complete = data.dropna()
print(f"original rows: {len(data)}   retained rows: {len(data_complete)}")
""",
            "wp42-504-drop-blank",
            tags=["wp42-activity-drop-incomplete"],
        ),
        code(
            """
# Run this to check your work.
if "data_complete" in globals():
    assert data_complete is not data, "data_complete should be a new dataframe, not the original"
    assert len(data) == 1114, "the original data must stay unchanged"
    assert data_complete.isna().sum().sum() == 0, "data_complete should have no missing values left"
    print(f"Looks good: data_complete retains {len(data_complete)} of {len(data)} participants.")
else:
    print("Not complete yet: define data_complete above first.")
""",
            "wp42-505-drop-check",
        ),
        md(
            """
Now write code that:
1. makes a **copy** of `data` called `data_filled`;
2. fills `data_filled`'s `FIQ` column's missing values with **that column's own
   median** (`data` itself must stay unchanged);
3. displays `describe()` for the original `FIQ` and FIQ with missing values
   filled in, side by side.
""",
            "wp42-506-fill-instructions",
        ),
        blank(
            "# YOUR CODE HERE\n# data_filled = ...\n",
            """
data_filled = data.copy()
fiq_median = data_filled["FIQ"].median()
data_filled["FIQ"] = data_filled["FIQ"].fillna(fiq_median)
display(pd.DataFrame({"original FIQ": data["FIQ"].describe(), "filled-in FIQ": data_filled["FIQ"].describe()}))
""",
            "wp42-507-fill-blank",
            tags=["wp42-activity-fill-median"],
        ),
        code(
            """
# Run this to check your work.
if "data_filled" in globals():
    assert data_filled is not data, "data_filled should be a copy, not the original"
    assert data["FIQ"].isna().any(), "the original data['FIQ'] must still have missing values"
    assert not data_filled["FIQ"].isna().any(), "data_filled['FIQ'] should have no missing values left"
    print("Looks good: data_filled['FIQ'] has no missing values, and the original data is unchanged.")
else:
    print("Not complete yet: define data_filled above first.")
""",
            "wp42-508-fill-check",
        ),
        md(
            "For a categorical variable, an explicit missing category can be more "
            "honest than filling in a guess:",
            "wp42-509-category-intro",
        ),
        code(
            """
med_status_filled = (
    data["CURRENT_MED_STATUS"].astype("object").fillna("Not recorded").astype("category")
)
med_status_filled.value_counts(dropna=False)
""",
            "wp42-510-category-code",
        ),
    ]


def _section_6() -> list[dict]:
    return [
        md("## Section 6 -- Distributions and correlation", "wp42-601-header"),
        code(
            """
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(data["AGE_AT_SCAN"].dropna(), bins=25, color="#2a6f9e", edgecolor="white")
ax.set_xlabel("age at scan (years)")
ax.set_ylabel("number of participants")
ax.set_title("Distribution of age at scan")
plt.show()
""",
            "wp42-602-histogram",
        ),
        md("Explore other variables and bin counts yourself:", "wp42-603-explore-intro"),
        code(_histogram_widget_code(), "wp42-604-histogram-widget"),
        code(
            """
show_question("q-histogram-bins")
""",
            "wp42-605-checked",
        ),
        md("Does `FIQ` differ between the two diagnostic groups?", "wp42-606-group-intro"),
        code(
            """
diagnosis_labels = data["DX_GROUP"].astype("int64").map({1: "Autism", 2: "Control"})
groups = ["Autism", "Control"]
values_by_group = [data.loc[diagnosis_labels == g, "FIQ"].dropna().to_numpy() for g in groups]

fig, ax = plt.subplots(figsize=(5, 4))
ax.boxplot(values_by_group, showfliers=False)
ax.set_xticks([1, 2])
ax.set_xticklabels(groups)
rng = np.random.default_rng(0)
for i, vals in enumerate(values_by_group, start=1):
    jitter = rng.uniform(-0.08, 0.08, size=len(vals))
    ax.scatter(np.full(len(vals), i) + jitter, vals, s=8, alpha=0.3, color="#2a6f9e")
ax.set_ylabel("FIQ")
ax.set_title("FIQ by diagnostic group")
plt.show()
""",
            "wp42-607-group-plot",
        ),
        md(
            "> **The two `FIQ` distributions above overlap heavily. Name one other "
            "variable that could differ between sites *and* be related to `FIQ`, "
            "which would make a raw group comparison misleading.**",
            "wp42-608-group-answer",
        ),
        md(
            "**Pearson `r`** measures the strength of a *linear* relationship "
            "between two numeric variables, from -1 to +1. It is sensitive to "
            "outliers and never establishes causation.",
            "wp42-609-correlation-intro",
        ),
        code(
            """
correlation_variables = ["AGE_AT_SCAN", "FIQ", "VIQ", "PIQ", "SRS_TOTAL_RAW", "ADOS_G_TOTAL", "ADI_R_SOCIAL_TOTAL_A"]
pearson_matrix = data[correlation_variables].corr(method="pearson")

# figsize is widened and the title is a suptitle (figure-level, not axes-level)
# so the colorbar on the right has room without clipping the title text.
fig, ax = plt.subplots(figsize=(8, 6.5))
im = ax.imshow(pearson_matrix.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(correlation_variables)))
ax.set_xticklabels(correlation_variables, rotation=90)
ax.set_yticks(range(len(correlation_variables)))
ax.set_yticklabels(correlation_variables)
for i in range(len(correlation_variables)):
    for j in range(len(correlation_variables)):
        v = pearson_matrix.to_numpy()[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color="white" if abs(v) > 0.5 else "black")
fig.colorbar(im, ax=ax, shrink=0.8, pad=0.03, label="Pearson r")
fig.suptitle("Pearson correlation between numerical variables", x=0.46)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()
""",
            "wp42-610-correlation-plot",
        ),
        code(
            """
show_question("q-fiq-correlation")
""",
            "wp42-611-checked",
        ),
    ]


def _histogram_widget_code() -> str:
    return """
_HIST_VARIABLES = [
    ("Age at scan (years)", "AGE_AT_SCAN"),
    ("Full-scale IQ", "FIQ"),
    ("Verbal IQ", "VIQ"),
    ("Performance IQ", "PIQ"),
    ("SRS total (raw)", "SRS_TOTAL_RAW"),
    ("ADOS-G total", "ADOS_G_TOTAL"),
    ("ADI-R social total", "ADI_R_SOCIAL_TOTAL_A"),
]
hist_variable = widgets.Dropdown(options=_HIST_VARIABLES, value="AGE_AT_SCAN", description="Variable:")
hist_bins = widgets.BoundedIntText(value=25, min=5, max=80, description="Bins:")
hist_output = widgets.Output()


def _refresh_histogram(_change=None):
    with hist_output:
        hist_output.clear_output(wait=True)
        col = hist_variable.value
        values = data[col].dropna()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(values, bins=hist_bins.value, color="#2a6f9e", edgecolor="white")
        ax.set_xlabel(col)
        ax.set_ylabel("number of participants")
        ax.set_title(f"Distribution of {col}  (n={len(values)}, missing={int(data[col].isna().sum())})")
        plt.show()


hist_variable.observe(_refresh_histogram, names="value")
hist_bins.observe(_refresh_histogram, names="value")
display(widgets.VBox([hist_variable, hist_bins, hist_output]))
_refresh_histogram()
""".strip()


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1()
    section_2 = _section_2()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_2]
    cells += _section_3()
    section_4 = _section_4()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_4]
    section_5 = _section_5()
    cells += [c.render(mode) if isinstance(c, Blank) else c for c in section_5]
    cells += _section_6()
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
