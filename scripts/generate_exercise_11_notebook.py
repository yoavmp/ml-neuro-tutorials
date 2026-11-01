#!/usr/bin/env python3
"""Generate Exercise 11's JupyterLite template, portable copy, and reference.

WP61: build Exercise 11 ("Embeddings and Representational Similarity
Analysis") from a titled placeholder stub into a real, active notebook,
following scripts/generate_exercise_09_notebook.py's exact shape (hidden
setup cell, show_question() answer-key hiding, Blank-tagged student tasks,
native ipywidgets/Matplotlib activities, generous sanity-check tolerances).

**Local-only scope (WP61):** this generator's outputs are NOT wired into
book/_toc.yml, book/_config.yml's exclude_patterns, book/config/
exercise_manifest.json, or any launch button -- Exercise 11 stays excluded
from the published Sphinx build and the release gate exactly as before
(book/config/exercise_manifest.json's own $comment, and
book/chapters/chapter_11/exercise_11.md, the titled placeholder stub, are
both left untouched). Wiring this generator's outputs into the live site is
deliberately deferred to a later, explicitly authorized release WP (the
WP51->WP52, WP57->WP57 release, WP58->WP59 pattern this repo already uses).
The JupyterLite route is still built and tested locally this WP, by placing
the template directly under book/lite/files/ and navigating to it by URL
during local verification, exactly as WP51/WP57/WP58 did before their own
release WPs.

Content: this is the first course notebook built on real fMRI data. Subject
2 of Haxby et al. (2001)'s visual-object-category dataset (nilearn's own
documented default subject) is reduced, by a separate offline, maintainer-
only script (scripts/export_haxby_rsa_data.py), to one ventral-temporal
voxel-response pattern per stimulus category per run -- 12 runs x 8
categories x 464 voxels, book/lite/files/data/haxby_rsa_patterns.csv. This
notebook teaches representational similarity analysis (RSA) on that small,
already-prepared export: a neural representational dissimilarity matrix
(RDM) from pairwise correlation distances between category patterns, a 2-D
MDS embedding of that RDM, and a comparison against two predeclared
category hypotheses (face vs. other; animate vs. inanimate, with scrambled
pictures excluded from the animacy comparison since they carry no animacy
at all). Two native ipywidgets/Matplotlib activities: (A) toggle between
correlation and Euclidean distance and see the resulting RDM/embedding
change; (B) assign the 7 non-scrambled categories into two groups and see
the resulting hypothesis RDM's descriptive match to the real neural RDM --
explicitly labeled exploration, since optimizing a grouping against the
same data it is then scored against is not an independent test.

WP61R (author review of the WP61 build) removed the split-half (odd run
vs. even run) reliability section entirely -- its code, blank, check,
question, and every dependent reference/section number -- along with the
separate condition-order checked question; a short note on matching
category order before comparing two RDMs stays in Section 2 without a quiz
attached. WP61R also fixed two latent bugs matching WP61's own "an
untouched blank shouldn't silently look complete" pattern: the Section 2
heatmap-plot cell and the Section 3 MDS cell now both guard against an
all-zero (unfilled) `neural_rdm`, not just the check cell and the
face-hypothesis example WP61 already guarded. See WP61R_REPORT.md for the
full list of author-requested wording/structure changes.

Numbers verified directly against book/lite/files/data/haxby_rsa_patterns.csv
(built by scripts/export_haxby_rsa_data.py --refresh; see its own docstring
and book/lite/files/data/haxby_rsa_patterns.manifest.json for the full
extraction method, provenance, and checksum) before writing a single
generator line -- see the WP61 report for every verification command.
Headline results (correlation-distance RDM, category patterns averaged
across all 12 runs unless noted; unchanged by WP61R, which touched wording
and structure only, never the extraction or any measured value):
  Neural RDM distances range from 0.426 (bottle-shoe, the most similar pair)
    to 1.124 (cat-scrambledpix, the least similar pair); diagonal is exactly
    0, matrix is exactly symmetric (both guaranteed by construction, not
    independently "discovered").
  Face-vs-other-categories model RDM match: r = 0.247 -- weak-positive, not
    the strongest result in this notebook; reported honestly rather than
    omitted or re-derived to look stronger.
  Animate-vs-inanimate model RDM match (scrambled excluded, 7x7 sub-RDM):
    r = 0.446 -- moderate, clearly the stronger of the two predeclared
    hypotheses here, consistent with face/cat (the two animate categories)
    having one of the lowest pairwise distances (0.440) in the whole RDM.

Outputs:
  book/lite/files/exercise_11.ipynb                    (--student, JupyterLite)
  book/lite/files/exercise_11_portable.ipynb            (--student, same file,
                                                          a portable/Colab-ready
                                                          copy, checked for a
                                                          downloaded notebook)
  scripts/reference_notebooks/exercise_11_reference.ipynb (--reference)

**Deliberately NOT written this WP:**
book/downloads/chapter_11/exercise_11_portable.ipynb. Exercise 11 is still
the one remaining exercise guarded by tests/test_placeholder_exercises.py's
test_no_active_portable_notebook_for_any_placeholder, which asserts no file
exists at exactly that path while Exercise 11's book page stays the
placeholder stub. That guard is intentional (it is what stops a "coming
later" page from quietly gaining a real download button) and this WP does
not lift it -- a future release WP both fills that path and removes
Exercise 11 from that test's PLACEHOLDER_TITLES, the same way WP52/WP57R/
WP59 did for their own exercises. The portable/Colab-ready copy this WP
does ship (book/lite/files/exercise_11_portable.ipynb) is checked by this
WP's own tests and reachable from the local JupyterLite build's file
listing; only the book-page download button is deferred.

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
DATA_SIDECAR = REPO_ROOT / "book" / "lite" / "files" / "data" / "haxby_rsa_patterns.manifest.json"

LITE_TEMPLATE_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_11.ipynb"
# book/downloads/chapter_11/exercise_11_portable.ipynb is deliberately NOT
# written this WP -- see the module docstring's "Deliberately NOT written
# this WP" note: tests/test_placeholder_exercises.py's
# test_no_active_portable_notebook_for_any_placeholder asserts that path
# does not exist while Exercise 11's book page is still the placeholder
# stub. LITE_FILES_PORTABLE_COPY_PATH below is this WP's portable, checked
# copy instead.
LITE_FILES_PORTABLE_COPY_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_11_portable.ipynb"
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_11_reference.ipynb"

TEMPLATE_VERSION = 1

KERNELSPEC = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "wp41": {"exercise": 11, "templateVersion": TEMPLATE_VERSION},
}

ANIMATE_CATEGORIES = {"face", "cat"}
SCRAMBLED_CATEGORY = "scrambledpix"
HRF_ONSET_TRS_DROPPED = 2


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


def _category_list_literal() -> str:
    sidecar = json.loads(DATA_SIDECAR.read_text())
    cats = sidecar["extraction"]["categories"]
    return "[" + ", ".join(repr(c) for c in cats) + "]"


# Duplicates (never imports) generate_exercise_09_notebook.py's setup-cell
# pattern -- each generator module is a self-contained, independently
# regenerable source of truth (WP41 maintainer guide section 4.7).
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

CATEGORIES = {categories_literal}

_HAXBY_RSA_FALLBACK_URL = (
    "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
    "book/lite/files/data/haxby_rsa_patterns.csv"
)


def load_haxby_rsa_table():
    """Return the prepared run x category x voxel table: one row per
    (run, category), one column per retained ventral-temporal (VT) voxel.

    Tries the small same-origin file this notebook ships next to first
    (JupyterLite, or a full local checkout); falls back to this course's
    own public copy of the same small derived file for a bare downloaded
    notebook or Colab, neither of which has the sibling data file. Both
    paths return identically shaped, identically ordered columns.
    """
    from pathlib import Path

    local_path = Path("data/haxby_rsa_patterns.csv")
    if local_path.exists():
        return pd.read_csv(local_path)
    return pd.read_csv(_HAXBY_RSA_FALLBACK_URL)


def category_patterns_from(frame, voxel_columns):
    """Average each category's voxel pattern across every run in `frame`,
    in CATEGORIES order. Returns an array shaped (len(CATEGORIES), n_voxels).
    """
    return np.vstack([
        frame.loc[frame["category"] == c, voxel_columns].to_numpy().mean(axis=0)
        for c in CATEGORIES
    ])


def upper_triangle(matrix):
    """The strictly-above-diagonal entries of a square matrix, as a 1-D
    array -- used whenever two RDMs (or an RDM and a model RDM) are
    compared, since the diagonal is always 0 by construction and the
    matrix is symmetric, so the lower triangle carries no new information.
    """
    import numpy as np

    n = matrix.shape[0]
    idx = np.triu_indices(n, k=1)
    return matrix[idx]


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
.widget-controls-row .widget-select-multiple { width: auto !important; }
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
# visible call like show_question("q-rdm-cell") never prints or displays a
# correct_index/correct_indices value. Every option/statement list below is
# written with its correct answer(s) first, for readability -- show_question
# shuffles the DISPLAYED order with a fixed, per-question seed --
# reproducible across runs/reruns of the same cell, but different across
# questions, so correct answers no longer land on the same position every
# time.
_QUESTIONS = {
    "q-row-voxel": dict(
        type="single",
        shuffle_seed=2,
        prompt=(
            "What does one row of the loaded table represent, and what "
            "does one voxel_#### column represent?"
        ),
        options=[
            "One row is a single category's averaged BOLD response pattern from one scanning run; each voxel_#### column is one ventral-temporal voxel's response within that pattern.",
            "One row is a single picture presentation; each voxel_#### column is a single time point (TR) during that presentation.",
            "One row is one scanning run as a whole; each voxel_#### column is a separate stimulus category.",
        ],
        correct_index=0,
        feedback_correct="Correct: this table is already category-level and run-level -- one row per (run, category), one column per retained ventral-temporal voxel.",
    ),
    "q-rdm-cell": dict(
        type="single",
        shuffle_seed=9,
        prompt=(
            "What does one cell of the neural RDM -- say, the cell for "
            "'face' and 'house' -- actually represent?"
        ),
        options=[
            "How dissimilar those two categories' averaged response patterns are, according to whichever distance measure was used -- not a statement about which brain region or mechanism drives that difference.",
            "The probability that a voxel in this ROI responds more strongly to faces than to houses.",
            "The number of voxels that respond differently to faces and houses.",
        ],
        correct_index=0,
        feedback_correct="Correct: an RDM cell is a dissimilarity between two patterns, under one chosen distance measure -- it says nothing by itself about mechanism or which voxels drive it.",
    ),
    "q-mds-distortion": dict(
        type="single",
        shuffle_seed=7,
        prompt=(
            "The 2-D MDS plot places each category at one point. What does "
            "the distance between two points on that plot represent?"
        ),
        options=[
            "An approximation of the RDM's real dissimilarity between those two categories -- 2 dimensions generally cannot preserve every pairwise distance from an 8x8 RDM exactly, and the plot's axis orientation is arbitrary.",
            "The exact dissimilarity value from the RDM, preserved without any distortion.",
            "The number of voxels that distinguish the two categories.",
        ],
        correct_index=0,
        feedback_correct="Correct: MDS finds the best available 2-D approximation to the RDM's distances -- not an exact, distortion-free embedding -- and the axes themselves carry no fixed meaning.",
    ),
    "q-face-match-implications": dict(
        type="multi",
        shuffle_seed=18,
        prompt=(
            "This notebook finds a positive correlation between the neural "
            "RDM and the face-vs-other-categories model RDM. Which "
            "statements about what that does and does not establish are true?"
        ),
        statements=[
            "It is consistent with face-related information being present somewhere in this region of interest -- it does not by itself prove the mechanism.",
            "It is a descriptive correlation between two matrices, not a significance-tested or causal claim.",
            "A similar positive correlation could in principle arise from a different underlying representational code that happens to produce a similar RDM pattern.",
            "It proves that specific individual voxels are dedicated exclusively to processing faces.",
            "It confirms the exact anatomical boundary of a 'face area' within this mask.",
            "It is only meaningful if the correlation reaches a statistically significant p-value.",
        ],
        correct_indices={0, 1, 2},
        feedback_correct="Correct: a positive RDM-model correlation is consistent with face-related structure being present, but it is descriptive and non-identifying -- it does not prove a specific mechanism, exclusive voxel tuning, or an exact anatomical boundary, and (as this notebook discusses) a naive p-value here would treat non-independent category pairs as independent observations.",
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
    source = SETUP_SOURCE_TEMPLATE.replace("{categories_literal}", _category_list_literal())
    return code(source, "wp61-000-setup", hidden=True)


def _run_first_notice() -> dict:
    return md(
        """
**Run the cell below first.** Its code is collapsed (click the `...` to
expand it) because it is one-time setup, not part of the lesson -- but it
still has to run once, before anything else in this notebook, or later
cells will fail with `NameError`. Click it, then press Shift+Enter (or the
Run button), and continue through the notebook in order from there.
""",
        "wp61-000a-run-first",
    )


# --- section builders --------------------------------------------------


def _title_and_overview() -> list[dict]:
    return [
        md("# Exercise 11: Embeddings and Representational Similarity Analysis", "wp61-001-title"),
        md(
            """
## What this notebook covers

This is Exercise 11 of *Machine Learning for Neuroscience*. So far, "data"
in this course has meant tables of numbers -- cortical-thickness measures,
sensor readings. Here, the data is a brain response itself: a pattern of
activity across many voxels, one pattern per stimulus category. The
question this notebook asks is not "can we predict a label from this
pattern," but "how are these patterns related to each other" -- the basic
question **representational similarity analysis (RSA)** answers.

In this notebook you will:

1. load the prepared run x category x voxel response patterns and see
   what one response pattern looks like;
2. build a neural representational dissimilarity matrix (RDM) from
   pairwise correlation distances between category patterns;
3. project that RDM into a 2-D embedding and label each category;
4. compare the neural RDM against two predeclared category hypotheses;
5. interpret what these results do, and do not, establish.

Written-answer cells (bold questions in a blockquote) are ordinary Markdown:
double-click one to edit it, type your answer, then press Shift+Enter to
render it back. Your answer is saved with the rest of this notebook,
including in **Download my notebook**.

**Prerequisites:** Exercise 1 (correlation) and Exercise 8 (PCA and other
dimensionality-reduction methods).
""",
            "wp61-002-overview",
        ),
    ]


def _section_1_load() -> list[dict]:
    return [
        md("## 1. Load the Response Patterns", "wp61-101-header"),
        md(
            """
This notebook uses real functional MRI data from Haxby et al. (2001): while
a participant viewed photographs from 8 categories (faces, cats, houses,
chairs, bottles, scissors, shoes, and scrambled control images), activity
was recorded across the brain. This notebook uses only a **ventral-temporal
(VT) cortex** mask -- a region broadly involved in visual object
recognition.

We load a small, already-prepared part of the dataset: for each of 12
scanning runs and each of 8 categories, one **response pattern** across the
retained VT voxels -- that category's recorded activity, averaged across
its retained time points within the run. Preprocessing details, exclusions,
and source information are documented in
[haxby_rsa_patterns.manifest.json](data/haxby_rsa_patterns.manifest.json).

Each loaded row is one (run, category) pattern; each `voxel_####` column is
one VT voxel. These are **category-level** patterns -- the original
picture-by-picture presentation order, and any response to an individual
image, is not recoverable from this export.
""",
            "wp61-102-intro",
        ),
        code(
            """
try:
    haxby_df = load_haxby_rsa_table()
except NameError as exc:
    raise RuntimeError(
        "load_haxby_rsa_table is not defined yet. Run this "
        "notebook's first code cell (collapsed, at the very top, under "
        "'Run the cell below first') before this one, then run this cell again."
    ) from exc

VOXEL_COLUMNS = [c for c in haxby_df.columns if c.startswith("voxel_")]
print(f"table: {haxby_df.shape[0]} rows (12 runs x 8 categories), {len(VOXEL_COLUMNS)} ventral-temporal voxels")
print(f"categories: {CATEGORIES}")
haxby_df.head()
""",
            "wp61-103-load",
        ),
        md(
            """
### What does one response pattern look like?

Here we can see a heatmap of all 8 categories' patterns from a single run
(run 0), one row per category, one column per voxel. No obvious structure
is visible by eye -- the rest of this notebook finds it systematically
instead.
""",
            "wp61-104-heatmap-intro",
        ),
        code(
            """
run0 = haxby_df[haxby_df["run"] == 0].set_index("category").loc[CATEGORIES, VOXEL_COLUMNS]

fig, ax = plt.subplots(figsize=(8, 3.2))
im = ax.imshow(run0.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
for i in range(1, len(CATEGORIES)):
    ax.axhline(i - 0.5, color="black", linewidth=0.6)
ax.set_yticks(range(len(CATEGORIES)))
ax.set_yticklabels(CATEGORIES)
ax.set_xlabel(f"ventral-temporal voxel (1 of {len(VOXEL_COLUMNS)})")
ax.set_title("Run 0: one response pattern per category")
plt.colorbar(im, ax=ax, label="z-scored response", fraction=0.03, pad=0.02)
plt.tight_layout()
plt.show()
""",
            "wp61-105-heatmap",
        ),
        code(
            """
show_question("q-row-voxel")
""",
            "wp61-106-q-row-voxel",
        ),
    ]


def _section_2_rdm() -> list[dict]:
    return [
        md("## 2. Build the Neural RDM", "wp61-201-header"),
        md(
            """
A **representational dissimilarity matrix (RDM)** summarizes how different
every pair of categories' patterns is, under one chosen distance measure.
This section uses **correlation distance**: `1 - r`, where `r` is the
Pearson correlation between two categories' voxel patterns. Two categories
with highly correlated patterns get a distance near 0; two categories with
unrelated (or oppositely patterned) activity get a distance near 1 (or
above).

First, average each category's pattern across all 12 runs (one row per
category, in `CATEGORIES` order) -- this is given code, since it reuses
only what Section 1 already loaded:
""",
            "wp61-202-intro",
        ),
        code(
            """
CATEGORY_PATTERNS = category_patterns_from(haxby_df, VOXEL_COLUMNS)
print(f"CATEGORY_PATTERNS shape: {CATEGORY_PATTERNS.shape}  (categories x voxels)")
""",
            "wp61-203-category-patterns",
        ),
        md(
            """
### Your task: build the neural RDM

Build an 8x8 array `neural_rdm` where `neural_rdm[i, j]` is the correlation
distance (`1 - r`) between `CATEGORY_PATTERNS[i]` and `CATEGORY_PATTERNS[j]`,
for every pair `i, j` in `CATEGORIES` order (including `i == j`, which
should come out essentially 0).
""",
            "wp61-204-instructions",
        ),
        blank(
            """
import numpy as np

n = len(CATEGORIES)
neural_rdm = np.zeros((n, n))

# YOUR CODE HERE
# Hint: loop over every pair (i, j) of row indices into CATEGORY_PATTERNS;
# np.corrcoef(a, b) returns a 2x2 matrix whose off-diagonal entry [0, 1] is
# the Pearson correlation between vectors a and b.
# Example format (not a real result):
# neural_rdm[0, 1] = 0.0
""",
            """
import numpy as np

n = len(CATEGORIES)
neural_rdm = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        r = np.corrcoef(CATEGORY_PATTERNS[i], CATEGORY_PATTERNS[j])[0, 1]
        neural_rdm[i, j] = 1 - r
""",
            "wp61-205-rdm-blank",
            tags=["wp61-activity-rdm"],
        ),
        code(
            """
# Run this to check your neural RDM.
if "neural_rdm" in globals() and not np.allclose(neural_rdm, 0.0):
    problems = []
    if neural_rdm.shape != (len(CATEGORIES), len(CATEGORIES)):
        problems.append(f"shape is {neural_rdm.shape}, expected {(len(CATEGORIES), len(CATEGORIES))}")
    elif not np.all(np.isfinite(neural_rdm)):
        problems.append("neural_rdm contains a non-finite value (NaN or inf)")
    else:
        max_diag = np.abs(np.diag(neural_rdm)).max()
        max_asym = np.abs(neural_rdm - neural_rdm.T).max()
        if max_diag > 1e-6:
            problems.append(f"diagonal should be ~0 (same category vs. itself); largest diagonal value is {max_diag:.4f}")
        if max_asym > 1e-6:
            problems.append(f"matrix should be symmetric; largest |A - A.T]| value is {max_asym:.4f}")
    if problems:
        print("Not quite yet:")
        for p in problems:
            print(f"  - {p}")
    else:
        print("Looks good: neural_rdm is square, finite, symmetric, with a ~0 diagonal.")
        print(f"  distance range: {upper_triangle(neural_rdm).min():.3f} to {upper_triangle(neural_rdm).max():.3f}")
else:
    print("Not complete yet: define neural_rdm above first.")
""",
            "wp61-206-rdm-check",
        ),
        md(
            """
### Visualize the neural RDM

Supplied: a heatmap of `neural_rdm`, with both axes labeled by category, in
the same fixed order every time -- a graceful fallback message appears if
the check above has not passed yet.
""",
            "wp61-207-plot-intro",
        ),
        code(
            """
if "neural_rdm" in globals() and not np.allclose(neural_rdm, 0.0) and neural_rdm.shape == (len(CATEGORIES), len(CATEGORIES)) and np.all(np.isfinite(neural_rdm)):
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(neural_rdm, cmap="viridis")
    ax.set_xticks(range(len(CATEGORIES)))
    ax.set_yticks(range(len(CATEGORIES)))
    ax.set_xticklabels(CATEGORIES, rotation=45, ha="right")
    ax.set_yticklabels(CATEGORIES)
    ax.set_title("Neural RDM (correlation distance)")
    plt.colorbar(im, ax=ax, label="1 - correlation", fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: finish the neural_rdm task above first.")
""",
            "wp61-208-plot",
        ),
        code(
            """
show_question("q-rdm-cell")
""",
            "wp61-209-q-rdm-cell",
        ),
        md(
            """
Notice the check cell above verifies `neural_rdm`'s category order against
`CATEGORIES` implicitly, by construction (it is built in that order and
never reordered). That matters for every later comparison in this
notebook: two RDMs can only be compared cell-by-cell if both list
categories in the same order.
""",
            "wp61-210-order-note",
        ),
    ]


def _section_3_mds() -> list[dict]:
    return [
        md("## 3. A 2-D Embedding of the RDM", "wp61-301-header"),
        md(
            """
An 8x8 RDM is hard to read as a table. **Multidimensional scaling (MDS)**
finds a low-dimensional layout of points -- here, 2-D -- whose pairwise
distances match the RDM's distances as closely as possible. This is a
*best available approximation*, not an exact reconstruction: an 8x8 RDM
generally cannot be represented exactly in only 2 dimensions, and nothing
about the plot's orientation or axis directions is meaningful -- only the
relative distances between points are.

Given, ready-to-run:
""",
            "wp61-302-intro",
        ),
        code(
            """
from sklearn.manifold import MDS

if "neural_rdm" in globals() and not np.allclose(neural_rdm, 0.0) and neural_rdm.shape == (len(CATEGORIES), len(CATEGORIES)) and np.all(np.isfinite(neural_rdm)):
    mds = MDS(n_components=2, metric="precomputed", random_state=0, n_init=4, init="random")
    coords = mds.fit_transform(neural_rdm)

    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(coords[:, 0], coords[:, 1], s=60)
    for (x, y), label in zip(coords, CATEGORIES):
        ax.annotate(label, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=10)
    ax.set_xlabel("MDS dimension 1 (arbitrary units)")
    ax.set_ylabel("MDS dimension 2 (arbitrary units)")
    ax.set_title("2-D MDS embedding of the neural RDM")
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.show()
else:
    print("Not complete yet: finish Section 2's neural_rdm task first.")
""",
            "wp61-303-mds",
        ),
        md(
            """
Look at which categories land near each other, and which land far apart.
Does anything about the layout match your intuition about these
categories -- and does anything surprise you?

> **In one or two sentences, describe one thing about this layout you find
> intuitive and one thing you find surprising.**
""",
            "wp61-304-reflection",
        ),
        code(
            """
show_question("q-mds-distortion")
""",
            "wp61-305-q-mds",
        ),
    ]


def _section_4_model_comparison() -> list[dict]:
    return [
        md("## 4. Comparing the Neural RDM with Category Hypotheses", "wp61-401-header"),
        md(
            """
A **model RDM** encodes one hypothesis about category structure as 0s and
1s: 0 where the hypothesis treats two categories as the same, 1 where it
treats them as different. Comparing it to the neural RDM (again, upper
triangle to upper triangle) gives a **descriptive correlation** -- how well
that hypothesis matches the measured structure, nothing more.

### Given example: faces vs. every other category

This model RDM says: `face` differs from every other category (distance 1),
and every non-`face` pair is treated as the same (distance 0) under this
hypothesis.
""",
            "wp61-402-face-example-intro",
        ),
        code(
            """
if "neural_rdm" in globals() and not np.allclose(neural_rdm, 0.0):
    face_hypothesis_rdm = np.array([
        [0 if (ci == "face") == (cj == "face") else 1 for cj in CATEGORIES]
        for ci in CATEGORIES
    ])
    face_match_r = np.corrcoef(upper_triangle(neural_rdm), upper_triangle(face_hypothesis_rdm))[0, 1]

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    axes[0].imshow(face_hypothesis_rdm, cmap="Greys")
    axes[0].set_xticks(range(len(CATEGORIES))); axes[0].set_yticks(range(len(CATEGORIES)))
    axes[0].set_xticklabels(CATEGORIES, rotation=45, ha="right"); axes[0].set_yticklabels(CATEGORIES)
    axes[0].set_title("Face-vs-other model RDM")
    axes[1].bar(["Face vs. other\\nmodel match"], [face_match_r], color="tab:blue")
    axes[1].set_ylim(-1, 1)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_ylabel("correlation with neural RDM")
    plt.tight_layout()
    plt.show()
    print(f"face_match_r = {face_match_r:.3f}")
else:
    print("Not complete yet: finish Section 2's neural_rdm task first.")
""",
            "wp61-403-face-example",
        ),
        md(
            """
### Your task: animate vs. inanimate

Build the same kind of model RDM for an **animacy** hypothesis: `face` and
`cat` are animate; `house`, `chair`, `bottle`, `scissors`, and `shoe` are
inanimate. **Exclude `scrambledpix`** from this comparison entirely --
scrambled control images have no object identity and therefore no
animacy at all, so including them would force an arbitrary animate/
inanimate label onto a category the hypothesis was never meant to describe.

Required outputs:
- `nonscrambled_categories`: `CATEGORIES` with `"scrambledpix"` removed
  (same relative order).
- `animacy_hypothesis_rdm`: a model RDM over `nonscrambled_categories` only
  (0 if both categories are animate or both are inanimate, 1 otherwise).
- `animacy_match_r`: the Pearson correlation between
  `upper_triangle(animacy_hypothesis_rdm)` and the upper triangle of the
  **matching sub-matrix** of `neural_rdm` (the rows/columns for
  `nonscrambled_categories` only, in the same order).
""",
            "wp61-404-instructions",
        ),
        blank(
            """
ANIMATE = {"face", "cat"}

# YOUR CODE HERE
# Hint: build nonscrambled_categories first, then find each of its
# categories' position in CATEGORIES to slice the matching rows/columns out
# of neural_rdm (neural_rdm[np.ix_(positions, positions)] selects exactly
# those rows and columns). Build animacy_hypothesis_rdm the same way the
# face example built face_hypothesis_rdm, just with the ANIMATE set instead.
# Example format (not a real result):
# animacy_match_r = 0.0
""",
            """
ANIMATE = {"face", "cat"}

nonscrambled_categories = [c for c in CATEGORIES if c != "scrambledpix"]
positions = [CATEGORIES.index(c) for c in nonscrambled_categories]
neural_rdm_nonscrambled = neural_rdm[np.ix_(positions, positions)]

animacy_hypothesis_rdm = np.array([
    [0 if (ci in ANIMATE) == (cj in ANIMATE) else 1 for cj in nonscrambled_categories]
    for ci in nonscrambled_categories
])
animacy_match_r = np.corrcoef(
    upper_triangle(neural_rdm_nonscrambled), upper_triangle(animacy_hypothesis_rdm)
)[0, 1]
""",
            "wp61-405-animacy-blank",
            tags=["wp61-activity-animacy"],
        ),
        code(
            """
# Run this to check your animacy comparison.
if all(name in globals() for name in ("nonscrambled_categories", "animacy_hypothesis_rdm", "animacy_match_r")):
    problems = []
    if "scrambledpix" in nonscrambled_categories:
        problems.append("nonscrambled_categories must not include 'scrambledpix'")
    if len(nonscrambled_categories) != len(CATEGORIES) - 1:
        problems.append(f"nonscrambled_categories should have {len(CATEGORIES) - 1} entries, has {len(nonscrambled_categories)}")
    expected_shape = (len(nonscrambled_categories), len(nonscrambled_categories))
    if animacy_hypothesis_rdm.shape != expected_shape:
        problems.append(f"animacy_hypothesis_rdm has shape {animacy_hypothesis_rdm.shape}, expected {expected_shape}")
    elif not set(np.unique(animacy_hypothesis_rdm)) <= {0, 1}:
        problems.append("animacy_hypothesis_rdm should contain only 0s and 1s")
    if not np.isfinite(animacy_match_r) or not (-1.0 <= animacy_match_r <= 1.0):
        problems.append(f"animacy_match_r should be a correlation in [-1, 1]; got {animacy_match_r!r}")
    if problems:
        print("Not quite yet:")
        for p in problems:
            print(f"  - {p}")
    else:
        print(f"Looks good: animacy_match_r = {animacy_match_r:.3f} over {len(nonscrambled_categories)} categories.")
else:
    print("Not complete yet: define nonscrambled_categories, animacy_hypothesis_rdm, and animacy_match_r above first.")
""",
            "wp61-406-animacy-check",
        ),
        md(
            """
### Interactive activity -- try your own grouping

Below, assign each of the 7 non-scrambled categories to Group A or Group B
(everything not placed in Group A is Group B) and see the resulting
hypothesis RDM and its descriptive correlation with the neural RDM, updated
live as you change the selection.

**This activity is exploration, not an independent test.** Trying different
groupings against the same neural RDM this notebook already computed, and
reporting whichever grouping happens to score highest, would be searching
for a match rather than testing a hypothesis decided in advance -- exactly
the distinction Section 4's two predeclared hypotheses (face-vs-other,
animate-vs-inanimate) were built to avoid.
""",
            "wp61-407-widget-intro",
        ),
        code(
            """
# ---- "Try your own grouping" -- native interactive activity ----
# Self-contained: works even if the animacy task above was left blank.
_GROUPING_CATEGORIES = [c for c in CATEGORIES if c != "scrambledpix"]
_GROUPING_POSITIONS = [CATEGORIES.index(c) for c in _GROUPING_CATEGORIES]
_GROUPING_NEURAL_SUB_RDM = neural_rdm[np.ix_(_GROUPING_POSITIONS, _GROUPING_POSITIONS)]

_grouping_select = widgets.SelectMultiple(
    options=_GROUPING_CATEGORIES,
    value=("face", "cat"),
    description="Group A members:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="260px", height="130px"),
)
_grouping_output = widgets.Output()


def _grouping_render(_change=None):
    group_a = set(_grouping_select.value)
    group_b = set(_GROUPING_CATEGORIES) - group_a

    with _grouping_output:
        _grouping_output.clear_output(wait=True)
        if not group_a or not group_b:
            print("Choose at least one category for Group A, and leave at least one out (Group B) -- a group of zero categories has no hypothesis to test.")
            return

        hyp_rdm = np.array([
            [0 if (ci in group_a) == (cj in group_a) else 1 for cj in _GROUPING_CATEGORIES]
            for ci in _GROUPING_CATEGORIES
        ])
        match_r = np.corrcoef(
            upper_triangle(_GROUPING_NEURAL_SUB_RDM), upper_triangle(hyp_rdm)
        )[0, 1]

        fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
        axes[0].imshow(hyp_rdm, cmap="Greys")
        axes[0].set_xticks(range(len(_GROUPING_CATEGORIES))); axes[0].set_yticks(range(len(_GROUPING_CATEGORIES)))
        axes[0].set_xticklabels(_GROUPING_CATEGORIES, rotation=45, ha="right")
        axes[0].set_yticklabels(_GROUPING_CATEGORIES)
        axes[0].set_title(f"Group A: {sorted(group_a)}")
        axes[1].bar(["your grouping"], [match_r], color="tab:orange")
        axes[1].set_ylim(-1, 1)
        axes[1].axhline(0, color="black", linewidth=0.8)
        axes[1].set_ylabel("correlation with neural RDM (descriptive)")
        plt.tight_layout()
        plt.show()
        print(f"Group A = {sorted(group_a)}   Group B = {sorted(group_b)}   match r = {match_r:.3f} (exploratory, not a hypothesis test)")


_grouping_select.observe(_grouping_render, names="value")
display(widgets.VBox([controls_row(_grouping_select), _grouping_output]))
_grouping_render()
""",
            "wp61-408-widget",
        ),
    ]


def _section_5_interpret() -> list[dict]:
    return [
        md("## 5. Interpretation and Limits", "wp61-501-header"),
        md(
            """
A quick summary of what this notebook actually measured:

- The neural RDM's distances ranged from about 0.43 (the most similar pair
  of categories measured) to about 1.12 (the least similar) -- a real
  spread, not a flat, undifferentiated matrix.
- The animate-vs-inanimate hypothesis matched the neural RDM more closely
  than the face-vs-other-categories hypothesis did, in this data. Neither
  result should be read as "proven" -- both are single descriptive
  correlations from one small dataset, one subject, one region of interest.

**Why no p-value is reported here.** A correlation between two RDMs'
upper triangles is computed from `C x (C-1) / 2` pairs built out of only
`C` underlying category patterns (8 here, or 7 once scrambled images are
excluded) -- those pairs share the same handful of underlying patterns, so
they are not independent observations in the sense a p-value calculation
assumes. This notebook reports the correlation itself, descriptively, and
leaves it there.
""",
            "wp61-502-summary",
        ),
        md(
            """
> **In a few sentences: what would you tell someone who said "this notebook
> proves this brain region has a dedicated face-detector"? What does the
> face-hypothesis result actually support, and what would it take to say
> more than that?**
""",
            "wp61-503-reflection",
        ),
        code(
            """
show_question("q-face-match-implications")
""",
            "wp61-504-q-face-implications",
        ),
        md(
            """
### Interactive activity -- correlation distance vs. Euclidean distance

Everything above used **correlation distance**. Below, toggle between
correlation distance and **Euclidean distance** (the straight-line distance
between two voxel-pattern vectors) and see how the RDM heatmap and the 2-D
embedding both change. Both variants are computed once, in advance, so
switching the control redraws instantly rather than refitting anything.
""",
            "wp61-505-widget-intro",
        ),
        code(
            """
# ---- "Correlation vs. Euclidean distance" -- native interactive activity ----
from sklearn.metrics import pairwise_distances
from sklearn.manifold import MDS as _MDS

def _corr_distance_rdm(patterns):
    k = patterns.shape[0]
    out = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            out[i, j] = 1 - np.corrcoef(patterns[i], patterns[j])[0, 1]
    return out

_DISTANCE_VARIANTS = {
    "correlation": _corr_distance_rdm(CATEGORY_PATTERNS),
    "euclidean": pairwise_distances(CATEGORY_PATTERNS, metric="euclidean"),
}
# Precomputed once up front -- the dropdown below only looks up an
# already-fitted embedding, never refits MDS on the fly.
_DISTANCE_EMBEDDINGS = {
    name: _MDS(n_components=2, metric="precomputed", random_state=0, n_init=4, init="random").fit_transform(rdm)
    for name, rdm in _DISTANCE_VARIANTS.items()
}

_distance_dd = widgets.Dropdown(
    options=[("Correlation distance (1 - r)", "correlation"), ("Euclidean distance", "euclidean")],
    value="correlation",
    description="Distance measure:",
    style={"description_width": "initial"},
)
_distance_output = widgets.Output()


def _distance_render(_change=None):
    metric = _distance_dd.value
    rdm = _DISTANCE_VARIANTS[metric]
    coords = _DISTANCE_EMBEDDINGS[metric]

    with _distance_output:
        _distance_output.clear_output(wait=True)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

        im = axes[0].imshow(rdm, cmap="viridis")
        axes[0].set_xticks(range(len(CATEGORIES))); axes[0].set_yticks(range(len(CATEGORIES)))
        axes[0].set_xticklabels(CATEGORIES, rotation=45, ha="right")
        axes[0].set_yticklabels(CATEGORIES)
        axes[0].set_title(f"RDM ({metric} distance)")
        plt.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04)

        axes[1].scatter(coords[:, 0], coords[:, 1], s=60)
        for (x, y), label in zip(coords, CATEGORIES):
            axes[1].annotate(label, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=9)
        axes[1].set_title(f"2-D MDS embedding ({metric} distance)")
        axes[1].set_xlabel("dimension 1 (arbitrary)"); axes[1].set_ylabel("dimension 2 (arbitrary)")
        axes[1].set_aspect("equal")
        plt.tight_layout()
        plt.show()


_distance_dd.observe(_distance_render, names="value")
display(widgets.VBox([controls_row(_distance_dd), _distance_output]))
_distance_render()
""",
            "wp61-506-widget",
        ),
        md(
            """
Both distance measures are built from the same underlying patterns, so a
category pair that is far apart under one measure is usually (not always)
far apart under the other too -- but the exact ordering and the embedding's
layout can shift. Correlation distance ignores each pattern's overall scale
(it only cares about the pattern's *shape* across voxels); Euclidean
distance does not.

### Closing notes

- An RDM is a summary under one chosen distance measure -- not a
  measure-free fact about the brain.
- A 2-D MDS plot approximates an RDM; it does not reproduce it exactly, and
  its axes are not independently meaningful.
- A model-RDM correlation is descriptive evidence for one predeclared
  hypothesis, not a causal or mechanistic claim, and not something a naive
  p-value should be attached to here.
""",
            "wp61-507-closing",
        ),
    ]


def _build_cells(mode: str) -> list[dict]:
    cells: list[dict] = [_run_first_notice(), _setup_cell(mode)]
    cells += _title_and_overview()
    cells += _section_1_load()

    def render_section(section_items: list) -> list[dict]:
        return [c.render(mode) if isinstance(c, Blank) else c for c in section_items]

    cells += render_section(_section_2_rdm())
    cells += _section_3_mds()
    cells += render_section(_section_4_model_comparison())
    cells += _section_5_interpret()
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
        for path in (LITE_TEMPLATE_PATH, LITE_FILES_PORTABLE_COPY_PATH):
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
