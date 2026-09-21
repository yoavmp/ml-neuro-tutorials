#!/usr/bin/env python3
"""Generate the portable Colab / VS Code notebooks from the canonical notebooks.

The canonical notebooks under ``book/chapters/`` are written for Jupyter Book:
they embed the browser activities as ``<iframe>`` elements and use MyST
directives (``{admonition}``, ``{dropdown}``) that only render inside Sphinx.
Those files stay the single source of truth.

This script derives a self-contained notebook for each, under
``book/downloads/<chapter>/``, that a casual user can open in Google Colab or run
locally with only the packages that ship with a normal scientific-Python setup.
Each portable notebook:

* keeps every ordinary Markdown cell and every runnable Python analysis cell;
* replaces each ``<iframe>`` activity with a short Markdown pointer to the
  published course page;
* rewrites MyST directives as plain Markdown headings / ``<details>`` blocks;
* drops Jupyter Book presentation tags/metadata (``hide-input`` etc.) and clears
  every code cell's stored output -- with a small, per-notebook allowlist of
  cells whose deterministic saved outputs are kept (see each ``NotebookSpec``);
* loads any public data from the same pinned HTTPS URLs the canonical notebook
  uses -- no repository file is required;
* carries a banner identifying it as the portable derivative and linking back to
  the richer course page, plus an optional, commented-out ``%pip install`` cell
  for the packages that lesson imports.

Modes (exactly one required):

* ``--write``   -- (re)generate the portable notebook(s) on disk.
* ``--check``   -- regenerate in memory and fail if a committed file is stale or
                   missing. Used by CI. No network access, no writes.

``--notebook {chapter_01,chapter_02,chapter_03,chapter_04,chapter_05,chapter_06,chapter_07,chapter_08,all}``
(default ``all``) scopes both modes. Exercises 9-12 are placeholder pages
with no interactive activity and no portable notebook, so they are not
registered here. The bare ``--write`` / ``--check`` invocations keep working
and now cover every registered notebook.

Determinism: each output depends only on its committed inputs. Serialization
goes through ``nbformat.writes`` (sorted keys, fixed indent) with a single
trailing newline; cell ids are stable (passthrough cells keep their id,
generated cells use fixed literal ids). Running ``--write`` twice is a no-op.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
COLUMNS_JSON = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"

PUBLISHED_PAGE = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html"
)
PUBLISHED_PAGE_CH2 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html"
)
PUBLISHED_PAGE_CH3 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html"
)
PUBLISHED_PAGE_CH4 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html"
)
PUBLISHED_PAGE_CH5 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html"
)
PUBLISHED_PAGE_CH6 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html"
)
PUBLISHED_PAGE_CH7 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html"
)
PUBLISHED_PAGE_CH8 = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html"
)

BANNER_ID = "portable-banner"
SETUP_ID = "portable-setup"
SETUP_INSTALL_ID = "portable-setup-install"

HIDE_TAGS = {"hide-input", "hide-cell", "hide-output"}

_FENCE_RE = re.compile(r"^```\{(admonition|dropdown)\}\s*(.*)$")
_OPTION_RE = re.compile(r"^:([A-Za-z0-9_-]+):\s*(.*)$")
_IFRAME_TITLE_RE = re.compile(r'<iframe[^>]*\btitle="([^"]+)"', re.DOTALL)


# --- MyST -> plain Markdown -------------------------------------------------


def convert_myst_directives(source: str) -> str:
    """Rewrite ``{admonition}`` / ``{dropdown}`` fenced blocks as plain Markdown.

    ``{admonition} T`` becomes an ``#### T`` heading followed by its body.
    ``{dropdown} T`` becomes a ``<details><summary><strong>T</strong></summary>``
    block (rendered by Colab, VS Code and Jupyter alike). A cell may hold several
    such blocks; every block is converted and any text between/around them is
    kept verbatim.
    """
    lines = source.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        m = _FENCE_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        kind, title = m.group(1), m.group(2).strip()
        i += 1

        # consume MyST directive options (":class:", ":name:", ...)
        while i < n and _OPTION_RE.match(lines[i].strip()):
            i += 1

        body: list[str] = []
        while i < n and lines[i].strip() != "```":
            body.append(lines[i])
            i += 1
        if i < n and lines[i].strip() == "```":
            i += 1  # consume the closing fence

        while body and body[0].strip() == "":
            body.pop(0)
        while body and body[-1].strip() == "":
            body.pop()

        if out and out[-1].strip() != "":
            out.append("")

        if kind == "dropdown":
            out.append("<details>")
            out.append(f"<summary><strong>{title}</strong></summary>")
            out.append("")
            out.extend(body)
            out.append("")
            out.append("</details>")
        else:  # admonition
            out.append(f"#### {title}")
            out.append("")
            out.extend(body)
        out.append("")
        i = _skip_one_blank(lines, i)

    while out and out[-1].strip() == "":
        out.pop()
    return "\n".join(out)


def _skip_one_blank(lines: list[str], i: int) -> int:
    if i < len(lines) and lines[i].strip() == "":
        return i + 1
    return i


# --- notebook specs ------------------------------------------------------


@dataclass(frozen=True)
class NotebookSpec:
    key: str
    canonical: Path
    portable: Path
    published_page: str
    banner_source: str
    setup_source: str
    lesson_packages: str
    drop_admonition_titles: frozenset[str]
    iframe_replacements: dict[str, str]
    preserve_output_ids: frozenset[str]
    # Optional runnable Python cell inserted immediately after an iframe's
    # markdown replacement, keyed by the same iframe `title`. Used where a
    # static, non-interactive equivalent is practical and not already covered
    # by an earlier section (WP14 section 4.4).
    iframe_followup_code: dict[str, str] = field(default_factory=dict)
    iframe_followup_ids: dict[str, str] = field(default_factory=dict)
    rewrite_columns: bool = False
    require_pinned_source: str = "neurohackademy/nh2020-curriculum/"
    extra_banned: dict[str, str] = field(default_factory=dict)
    # The name Colab shows in its own tab / title bar for this notebook. When
    # set, written to `metadata.colab.name` (Colab reads this in preference to
    # the file name). None leaves the notebook metadata untouched.
    colab_title: str | None = None


_CH1_BANNER = (
    "# Exercise 1: Exploratory Data Analysis - portable notebook\n"
    "\n"
    "This is the **portable version** of the Chapter 1 EDA practice from\n"
    "**Machine Learning for Neuroscience**, generated from the canonical\n"
    "course notebook by `scripts/build_portable_notebook.py`. It is meant for\n"
    "running or editing the code in Google Colab or in a local VS Code /\n"
    "Jupyter setup.\n"
    "\n"
    "The richer version -- with the four activities embedded and running in\n"
    "the browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE + ">\n"
    "\n"
    "In this notebook the four interactive activities are replaced by links\n"
    "to that page; every Python analysis cell is kept and runnable. Questions\n"
    "marked *Think first* are followed, where one exists, by a collapsible\n"
    "*Check your reasoning* block; open questions are left without one fixed\n"
    "answer."
)

_CH1_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`seaborn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH2_BANNER = (
    "# Exercise 2: Regression and Bias-Variance Trade-Off - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 2 regression and KNN\n"
    "bias-variance practice from **Machine Learning for Neuroscience**,\n"
    "generated from the canonical course notebook by\n"
    "`scripts/build_portable_notebook.py`. It is meant for running or editing\n"
    "the code in Google Colab or in a local VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the k-exploration activity embedded and\n"
    "running in the browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH2 + ">\n"
    "\n"
    "In this notebook that interactive activity is replaced by a link to\n"
    "that page; every Python analysis cell is kept and runnable. Questions\n"
    "marked *Think first* are followed, where one exists, by a collapsible\n"
    "*Check your reasoning* block; open questions are left without one fixed\n"
    "answer."
)

_CH2_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads two\n"
    "public data files the first time it runs, so it needs internet access."
)

_CH2_IFRAME_REPLACEMENT = (
    "### Compare feature sets on the course website\n"
    "\n"
    "The interactive activity lets you configure two linear-regression models\n"
    "-- a measurement type and an anatomical ROI bundle each -- and compares\n"
    "their held-out performance on one fixed cohort and one fixed train/test\n"
    "split.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise II page:\n"
    "> <" + PUBLISHED_PAGE_CH2 + ">\n"
    "> This portable notebook links to it instead of embedding it. The\n"
    "> Python sections below still run the same kind of comparison directly."
)

_CH2_KNN_EXPLORE_IFRAME_REPLACEMENT = (
    "### Explore k yourself on the course website\n"
    "\n"
    "The interactive activity lets you drag a slider across every k from 1\n"
    "through every participant in the fitting set and watch fitting error,\n"
    "validation error, and the observed-vs-predicted scatter update from the\n"
    "actual refitted model at that k.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 2 page:\n"
    "> <" + PUBLISHED_PAGE_CH2 + ">\n"
    "> This portable notebook links to it instead of embedding it. Section 6\n"
    "> above already computes and plots the same k = 1..N_fit exploration as a\n"
    "> static Matplotlib figure, from the same fitting/validation split -- run\n"
    "> it and change `FIT_RANDOM_STATE` or the split size to explore further."
)

# Per-activity replacement for the Chapter 1 `<iframe>` cells, keyed by the
# iframe `title` attribute.
IFRAME_REPLACEMENTS = {
    "Interactive head, tail, and sample comparison for the ABIDE-II table": (
        "The interactive comparison lets you switch between `head()`, `tail()`\n"
        "and `sample()`, change the row count, and see how many acquisition sites\n"
        "and missing cells each view contains. The next cell runs the same three\n"
        "views in Python.\n"
        "\n"
        "> **Interactive version on the course website.** It is embedded in the\n"
        "> published Chapter 1 page:\n"
        "> <" + PUBLISHED_PAGE + ">\n"
        "> This portable notebook links to it instead of embedding it."
    ),
    "Interactive ABIDE-II complete-case retention explorer": (
        "### Complete-case retention explorer\n"
        "\n"
        "The interactive explorer lets you mark the variables you would treat as\n"
        "essential and shows how many participants remain when *every* marked\n"
        "variable must be recorded -- overall and for each acquisition site.\n"
        "\n"
        "> **Interactive version on the course website.** It is embedded in the\n"
        "> published Chapter 1 page:\n"
        "> <" + PUBLISHED_PAGE + ">\n"
        "> This portable notebook links to it instead of embedding it."
    ),
    "Interactive histogram of ABIDE-II variable distributions": (
        "The interactive histogram lets you pick a variable and change the number\n"
        "of bins to see how the choice of bin width changes the shape of a\n"
        "distribution without changing the data behind it. The next cell\n"
        "reproduces the same kind of plot in Python.\n"
        "\n"
        "> **Interactive version on the course website.** It is embedded in the\n"
        "> published Chapter 1 page:\n"
        "> <" + PUBLISHED_PAGE + ">\n"
        "> This portable notebook links to it instead of embedding it."
    ),
    "Interactive ABIDE-II feature correlation explorer": (
        "### Explore correlations yourself\n"
        "\n"
        "The interactive explorer lets you choose an X and a Y variable, colour\n"
        "the points by diagnostic group or sex, and read off the Pearson\n"
        "correlation coefficient, the pairwise-complete `n`, and how many\n"
        "participants were dropped for a missing value.\n"
        "\n"
        "> **Interactive version on the course website.** It is embedded in the\n"
        "> published Chapter 1 page:\n"
        "> <" + PUBLISHED_PAGE + ">\n"
        "> This portable notebook links to it instead of embedding it."
    ),
}

DROP_ADMONITION_TITLES = frozenset(
    {"Run or download this notebook", "How to use this notebook"}
)

# The Chapter 1 sampling cell keeps its three saved pandas tables (WP10 §3); the
# portable notebook has no embedded head/tail/sample activity.
PRESERVE_OUTPUT_IDS = frozenset({"7a1e5c93d204"})

LESSON_PACKAGES = "numpy pandas matplotlib seaborn"

CHAPTER_01 = NotebookSpec(
    key="chapter_01",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb",
    published_page=PUBLISHED_PAGE,
    banner_source=_CH1_BANNER,
    setup_source=_CH1_SETUP,
    lesson_packages=LESSON_PACKAGES,
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements=IFRAME_REPLACEMENTS,
    preserve_output_ids=PRESERVE_OUTPUT_IDS,
    rewrite_columns=True,
)

CHAPTER_02 = NotebookSpec(
    key="chapter_02",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH2,
    banner_source=_CH2_BANNER,
    setup_source=_CH2_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive KNN neighbour-count exploration for predicting age from brain structure": (
            _CH2_KNN_EXPLORE_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 2: Regression and Bias-Variance Trade-Off",
)

_CH3_BANNER = (
    "# Exercise 3: Classification and Metrics - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 3 classification\n"
    "practice from **Machine Learning for Neuroscience**, generated from the\n"
    "canonical course notebook by `scripts/build_portable_notebook.py`. It is\n"
    "meant for running or editing the code in Google Colab or in a local\n"
    "VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the decision-threshold and class-imbalance\n"
    "activities embedded and running in the browser -- is the published\n"
    "course page:\n"
    "<" + PUBLISHED_PAGE_CH3 + ">\n"
    "\n"
    "In this notebook the two embedded activities are replaced by links to\n"
    "that page; every Python analysis cell -- including the ordinary,\n"
    "editable equivalents of both activities -- is kept and runnable.\n"
    "Questions marked *Think first* are followed, where one exists, by a\n"
    "collapsible *Check your reasoning* block; open questions are left\n"
    "without one fixed answer."
)

_CH3_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH3_THRESHOLD_IFRAME_REPLACEMENT = (
    "### Explore the decision threshold on the course website\n"
    "\n"
    "The interactive activity lets you drag a slider across the decision\n"
    "threshold and watch the confusion matrix, accuracy, sensitivity,\n"
    "specificity, and the marked point on the ROC curve update from the\n"
    "exact same fixed test-set predicted probabilities -- the model is never\n"
    "refit.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 3 page:\n"
    "> <" + PUBLISHED_PAGE_CH3 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> cell runs the same threshold exploration directly -- edit `threshold`\n"
    "> and rerun it."
)

_CH3_IMBALANCE_IFRAME_REPLACEMENT = (
    "### Explore class imbalance on the course website\n"
    "\n"
    "The interactive activity lets you choose a class ratio and a\n"
    "predetermined split seed and compares the model's own test accuracy\n"
    "against the majority-class baseline accuracy on the same resampled cohort\n"
    "of real participants.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 3 page:\n"
    "> <" + PUBLISHED_PAGE_CH3 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> cell runs the same comparison directly -- edit `class_ratio` and\n"
    "> `random_state` and rerun it.\n"
    "\n"
    "**Think about this as you try a few ratios:** as imbalance increases, the\n"
    "model's raw accuracy rises too. Is the model actually performing better\n"
    "than at 50:50, or worse? What might you wrongly conclude if you only saw\n"
    "its accuracy, without the baseline for comparison?"
)

CHAPTER_03 = NotebookSpec(
    key="chapter_03",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH3,
    banner_source=_CH3_BANNER,
    setup_source=_CH3_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive decision-threshold exploration for classifying autism vs. control from brain structure": (
            _CH3_THRESHOLD_IFRAME_REPLACEMENT
        ),
        "Interactive class-imbalance exploration for classifying autism vs. control from brain structure": (
            _CH3_IMBALANCE_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 3: Classification and Metrics",
)

_CH4_BANNER = (
    "# Exercise 4: Validation and Cross-Validation - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 4 validation and\n"
    "cross-validation practice from **Machine Learning for Neuroscience**,\n"
    "generated from the canonical course notebook by\n"
    "`scripts/build_portable_notebook.py`. It is meant for running or editing\n"
    "the code in Google Colab or in a local VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the three embedded activities running in the\n"
    "browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH4 + ">\n"
    "\n"
    "In this notebook the three interactive activities are replaced by links\n"
    "to that page; every Python analysis cell -- including the ordinary,\n"
    "editable equivalents of every activity -- is kept and runnable. The cell\n"
    "that reveals the locked test-set result (Section 5) keeps no saved\n"
    "output here, even though every other code cell normally would: you must\n"
    "run it yourself to see the result, exactly as the browser activity asks\n"
    "you to choose a value of k before revealing its test score."
)

_CH4_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas` and `scikit-learn`. All\n"
    "three are already installed on Google Colab, and in a typical\n"
    "scientific-Python environment, so there is normally nothing to do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH4_STABILITY_IFRAME_REPLACEMENT = (
    "### Explore split and fold instability on the course website\n"
    "\n"
    "The interactive activity lets you choose a sample size, a random seed,\n"
    "and a number of cross-validation folds, and compares a single-split test\n"
    "score with cross-validation fold scores for the same fixed KNN model.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 4 page:\n"
    "> <" + PUBLISHED_PAGE_CH4 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> cell runs one such cross-validation directly."
)

_CH4_LOCK_TEST_IFRAME_REPLACEMENT = (
    "### Tune k yourself on the course website\n"
    "\n"
    "The interactive activity lets you compare training and validation\n"
    "performance across candidate values of k, choose a final value, and\n"
    "reveal the held-out test result once you lock in your choice.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 4 page:\n"
    "> <" + PUBLISHED_PAGE_CH4 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> two cells run the same tuning step, and then the same one-time reveal,\n"
    "> directly in Python."
)

_CH4_NESTED_CV_IFRAME_REPLACEMENT = (
    "### Explore nested cross-validation yourself on the course website\n"
    "\n"
    "The interactive activity lets you inspect, outer fold by outer fold, how\n"
    "the inner cross-validation compared candidate k values and how the\n"
    "resulting choice then scored on that fold's outer test data.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 4 page:\n"
    "> <" + PUBLISHED_PAGE_CH4 + ">\n"
    "> This portable notebook links to it instead of embedding it. The\n"
    "> preceding cells already compute and print the same fold-by-fold\n"
    "> results as a table."
)

CHAPTER_04 = NotebookSpec(
    key="chapter_04",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH4,
    banner_source=_CH4_BANNER,
    setup_source=_CH4_SETUP,
    lesson_packages="numpy pandas scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive single-split and cross-validation stability comparison for predicting age from brain structure": (
            _CH4_STABILITY_IFRAME_REPLACEMENT
        ),
        "Interactive KNN tuning activity: choose k before revealing the test result": (
            _CH4_LOCK_TEST_IFRAME_REPLACEMENT
        ),
        "Interactive nested cross-validation explorer for predicting age from brain structure": (
            _CH4_NESTED_CV_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 4: Validation and Cross-Validation",
)

_CH5_BANNER = (
    "# Exercise 5: Regularization and Feature Selection - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 5 regularization and\n"
    "feature-selection practice from **Machine Learning for Neuroscience**,\n"
    "generated from the canonical course notebook by\n"
    "`scripts/build_portable_notebook.py`. It is meant for running or editing\n"
    "the code in Google Colab or in a local VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the two embedded activities running in the\n"
    "browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH5 + ">\n"
    "\n"
    "In this notebook both interactive activities are replaced by links to\n"
    "that page; every Python analysis cell -- including the optional\n"
    "reproduction of the regularization activity's alpha curves -- is kept\n"
    "and runnable. Questions marked *Think first* are followed, where one\n"
    "exists, by a collapsible *Check your reasoning* block; open questions\n"
    "are left without one fixed answer."
)

_CH5_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH5_COMPARE_IFRAME_REPLACEMENT = (
    "### Compare predefined feature sets on the course website\n"
    "\n"
    "The interactive activity lets you configure two linear-regression models\n"
    "-- a measurement type and an anatomical ROI bundle each -- and compares\n"
    "their held-out performance on one fixed cohort and one fixed train/test\n"
    "split.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 5 page:\n"
    "> <" + PUBLISHED_PAGE_CH5 + ">\n"
    "> This portable notebook links to it instead of embedding it."
)

_CH5_REGULARIZATION_IFRAME_REPLACEMENT = (
    "### Shrink the coefficients on the course website\n"
    "\n"
    "The interactive activity lets you choose Linear Regression, Ridge, or\n"
    "Lasso and move alpha on a logarithmic scale, watching predictions,\n"
    "coefficients, and training/validation error update together.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 5 page:\n"
    "> <" + PUBLISHED_PAGE_CH5 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> section reproduces the same alpha curves directly in Python."
)

CHAPTER_05 = NotebookSpec(
    key="chapter_05",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_05" / "exercise_05.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_05" / "exercise_05_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH5,
    banner_source=_CH5_BANNER,
    setup_source=_CH5_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive feature-set comparison for predicting age from brain structure": (
            _CH5_COMPARE_IFRAME_REPLACEMENT
        ),
        "Interactive Ridge/Lasso regularization exploration for predicting age from brain structure": (
            _CH5_REGULARIZATION_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 5: Regularization and Feature Selection",
)

_CH6_BANNER = (
    "# Exercise 6: Decision Trees - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 6 decision-trees\n"
    "practice from **Machine Learning for Neuroscience**, generated from the\n"
    "canonical course notebook by `scripts/build_portable_notebook.py`. It is\n"
    "meant for running or editing the code in Google Colab or in a local\n"
    "VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the two embedded activities running in the\n"
    "browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH6 + ">\n"
    "\n"
    "In this notebook both interactive activities are replaced by links to\n"
    "that page; every Python analysis cell -- including the optional\n"
    "reproduction of the greedy-splitting calculation -- is kept and\n"
    "runnable. Questions marked *Think first* are left as open prompts."
)

_CH6_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH6_GREEDY_IFRAME_REPLACEMENT = (
    "### Build a tree greedily on the course website\n"
    "\n"
    "The interactive activity walks through the greedy splitting algorithm on\n"
    "a small synthetic dataset: choose a feature and threshold at each active\n"
    "node, lock your answer, then reveal the greedy optimum and compare.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 6 page:\n"
    "> <" + PUBLISHED_PAGE_CH6 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> section reproduces the same threshold/MSE calculation directly in\n"
    "> Python."
)

_CH6_ENSEMBLE_IFRAME_REPLACEMENT = (
    "### One tree or many? on the course website\n"
    "\n"
    "The interactive activity compares a single regression tree, bagging, and\n"
    "a Random Forest across five deterministic training replicates and a\n"
    "range of ensemble sizes, for predicting age from brain structure.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 6 page:\n"
    "> <" + PUBLISHED_PAGE_CH6 + ">\n"
    "> This portable notebook links to it instead of embedding it."
)

CHAPTER_06 = NotebookSpec(
    key="chapter_06",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_06" / "exercise_06.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_06" / "exercise_06_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH6,
    banner_source=_CH6_BANNER,
    setup_source=_CH6_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive greedy-splitting activity for a small synthetic regression tree": (
            _CH6_GREEDY_IFRAME_REPLACEMENT
        ),
        "Interactive comparison of a single tree, bagging, and Random Forest for predicting age from brain structure": (
            _CH6_ENSEMBLE_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 6: Decision Trees",
)

_CH7_BANNER = (
    "# Exercise 7: Boosting and Gradient Boosting - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 7 boosting and\n"
    "gradient-boosting practice from **Machine Learning for Neuroscience**,\n"
    "generated from the canonical course notebook by\n"
    "`scripts/build_portable_notebook.py`. It is meant for running or editing\n"
    "the code in Google Colab or in a local VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the two embedded activities running in the\n"
    "browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH7 + ">\n"
    "\n"
    "In this notebook both interactive activities are replaced by links to\n"
    "that page; every Python analysis cell -- including the optional\n"
    "reproduction of the stage-by-stage boosting calculation -- is kept and\n"
    "runnable."
)

_CH7_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH7_STEP_BY_STEP_IFRAME_REPLACEMENT = (
    "### Build a boosted model on the course website\n"
    "\n"
    "The interactive activity lets you choose a learning rate and step through\n"
    "squared-error gradient boosting stage by stage on a small simulated\n"
    "dataset, watching the ensemble prediction, the residuals left before each\n"
    "update, and the shallow tree fitted to them.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 7 page:\n"
    "> <" + PUBLISHED_PAGE_CH7 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> cell reproduces the same simulated dataset and its first boosting stage\n"
    "> directly in Python."
)

_CH7_PARAMETER_EXPLORER_IFRAME_REPLACEMENT = (
    "### Explore the boosting parameters on the course website\n"
    "\n"
    "The interactive activity lets you choose a learning rate, a tree depth,\n"
    "and a number of trees -- or press Play to add trees sequentially -- and\n"
    "watch training/validation MSE, a learning-rate x tree-count heatmap, and\n"
    "observed-versus-predicted validation age update together, using the\n"
    "development data only.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 7 page:\n"
    "> <" + PUBLISHED_PAGE_CH7 + ">\n"
    "> This portable notebook links to it instead of embedding it."
)

CHAPTER_07 = NotebookSpec(
    key="chapter_07",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_07" / "exercise_07.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_07" / "exercise_07_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH7,
    banner_source=_CH7_BANNER,
    setup_source=_CH7_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive stage-by-stage gradient boosting activity on a small simulated dataset": (
            _CH7_STEP_BY_STEP_IFRAME_REPLACEMENT
        ),
        "Interactive gradient-boosting parameter explorer for predicting age from brain structure": (
            _CH7_PARAMETER_EXPLORER_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 7: Boosting and Gradient Boosting",
)

_CH8_SETUP = (
    "## Setup\n"
    "\n"
    "This notebook imports only `numpy`, `pandas`, `matplotlib` and\n"
    "`scikit-learn`. All four are already installed on Google Colab, and in a\n"
    "typical scientific-Python environment, so there is normally nothing to\n"
    "do here.\n"
    "\n"
    "If one of the imports further down fails, run the next cell once (edit\n"
    "the version pins if your project needs specific ones), then restart the\n"
    "kernel and run the notebook from the top. The notebook also downloads a\n"
    "public data file the first time it runs, so it needs internet access."
)

_CH8_BANNER = (
    "# Exercise 8: Unsupervised Learning - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise 8 unsupervised-learning\n"
    "practice from **Machine Learning for Neuroscience**, generated from the\n"
    "canonical course notebook by `scripts/build_portable_notebook.py`. It is\n"
    "meant for running or editing the code in Google Colab or in a local\n"
    "VS Code / Jupyter setup.\n"
    "\n"
    "The richer version -- with the two embedded activities running in the\n"
    "browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH8 + ">\n"
    "\n"
    "In this notebook both interactive activities are replaced by links to\n"
    "that page; every Python analysis cell -- including the optional\n"
    "reproduction of the projection activity's math -- is kept and runnable."
)

_CH8_PROJECTION_IFRAME_REPLACEMENT = (
    "### Find the best projection on the course website\n"
    "\n"
    "The interactive activity lets you drag a projection-angle slider for a\n"
    "small simulated two-dimensional dataset and watch the variance captured\n"
    "and the reconstruction error left behind, before revealing the true\n"
    "first principal component.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 8 page:\n"
    "> <" + PUBLISHED_PAGE_CH8 + ">\n"
    "> This portable notebook links to it instead of embedding it. The next\n"
    "> cell reproduces the same simulated dataset and its projection math\n"
    "> directly in Python."
)

_CH8_KMEANS_IFRAME_REPLACEMENT = (
    "### Explore PCA and K-means on the course website\n"
    "\n"
    "The interactive activity lets you choose how many principal components\n"
    "to retain, a number of clusters k, and an initialization seed, then\n"
    "inspect the resulting clusters against diagnosis, sex, acquisition site,\n"
    "or age.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise 8 page:\n"
    "> <" + PUBLISHED_PAGE_CH8 + ">\n"
    "> This portable notebook links to it instead of embedding it. Section 6\n"
    "> above already reproduces a runnable, single-configuration version of\n"
    "> the same PCA-then-K-means workflow."
)

CHAPTER_08 = NotebookSpec(
    key="chapter_08",
    canonical=REPO_ROOT / "book" / "chapters" / "chapter_08" / "exercise_08.ipynb",
    portable=REPO_ROOT / "book" / "downloads" / "chapter_08" / "exercise_08_portable.ipynb",
    published_page=PUBLISHED_PAGE_CH8,
    banner_source=_CH8_BANNER,
    setup_source=_CH8_SETUP,
    lesson_packages="numpy pandas matplotlib scikit-learn",
    drop_admonition_titles=DROP_ADMONITION_TITLES,
    iframe_replacements={
        "Interactive projection-angle activity for a small simulated two-dimensional dataset": (
            _CH8_PROJECTION_IFRAME_REPLACEMENT
        ),
        "Interactive PCA and K-means explorer for ABIDE-II participants": (
            _CH8_KMEANS_IFRAME_REPLACEMENT
        ),
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
    colab_title="Exercise 8: Unsupervised Learning",
)

NOTEBOOKS = {
    CHAPTER_01.key: CHAPTER_01,
    CHAPTER_02.key: CHAPTER_02,
    CHAPTER_03.key: CHAPTER_03,
    CHAPTER_04.key: CHAPTER_04,
    CHAPTER_05.key: CHAPTER_05,
    CHAPTER_06.key: CHAPTER_06,
    CHAPTER_07.key: CHAPTER_07,
    CHAPTER_08.key: CHAPTER_08,
}

# Back-compat aliases for existing callers/tests (chapter_01 scope).
CANONICAL = CHAPTER_01.canonical
PORTABLE = CHAPTER_01.portable


# --- cell transforms ------------------------------------------------------


def _admonition_title(source: str) -> str | None:
    m = _FENCE_RE.match(source.split("\n", 1)[0])
    if m and m.group(1) == "admonition":
        return m.group(2).strip()
    return None


def _iframe_title(source: str) -> str | None:
    m = _IFRAME_TITLE_RE.search(source)
    return m.group(1) if m else None


def _rewrite_data_loading(source: str, columns: list[str]) -> str:
    """Embed the curated column list; drop the repo-relative config read.

    The Chapter 1 canonical notebook reads
    ``book/config/eda_phenotype_columns.json`` with
    ``json.loads(Path("../../config/...").read_text())``. The portable notebook
    must not depend on a repository checkout, so that read is replaced by a
    literal list and the now-unused ``json`` / ``pathlib`` imports are dropped.
    """
    col_block = "CURATED_COLUMNS = [\n" + "".join(
        f"    {json.dumps(c)},\n" for c in columns
    ) + "]"

    source = source.replace("import json\n", "", 1)
    source = source.replace("from pathlib import Path\n", "", 1)
    source = source.lstrip("\n")
    source = re.sub(
        r"# Curated column subset for this exercise\..*?"
        r"CURATED_COLUMNS = json\.loads\(\s*"
        r'Path\("\.\./\.\./config/eda_phenotype_columns\.json"\)\.read_text\(\)\s*\)',
        "# Curated column subset, embedded so this notebook needs no repository\n"
        "# files (the canonical Jupyter Book notebook reads it from book/config/).\n"
        + col_block,
        source,
        count=1,
        flags=re.DOTALL,
    )
    return source


def _sanitise_output(out: dict) -> dict:
    """Copy one saved output, dropping environment-specific execution metadata."""
    clean: dict = {"output_type": out["output_type"]}
    if "name" in out:
        clean["name"] = out["name"]
    if "text" in out:
        clean["text"] = out["text"]
    if "data" in out:
        clean["data"] = json.loads(json.dumps(out["data"]))  # deep copy, JSON-safe
    if out["output_type"] == "execute_result":
        clean["execution_count"] = None
    clean.setdefault("metadata", {})
    return nbformat.from_dict(clean)


def _preserved_outputs(src_cell) -> list:
    """The sanitised saved outputs for a preserve-output cell."""
    outputs = src_cell.get("outputs", []) or []
    if not outputs:
        raise SystemExit(
            f"cell {src_cell['id']} is marked output-preserving but the canonical "
            "notebook has no saved output for it; re-execute the canonical notebook"
        )
    return [_sanitise_output(o) for o in outputs]


def _banner_cell(nbf, spec: NotebookSpec) -> "nbformat.NotebookNode":
    cell = nbf.new_markdown_cell(spec.banner_source)
    cell["id"] = BANNER_ID
    cell["metadata"] = {}
    return cell


def _setup_cell(nbf, spec: NotebookSpec) -> "nbformat.NotebookNode":
    cell = nbf.new_markdown_cell(spec.setup_source)
    cell["id"] = SETUP_ID
    cell["metadata"] = {}
    return cell


def _setup_install_cell(nbf, spec: NotebookSpec) -> "nbformat.NotebookNode":
    cell = nbf.new_code_cell(
        "# If an import below fails, uncomment and run this line once, then\n"
        "# restart the kernel. Safe on Colab, VS Code and Jupyter.\n"
        f"# %pip install {spec.lesson_packages}"
    )
    cell["id"] = SETUP_INSTALL_ID
    cell["metadata"] = {}
    cell["outputs"] = []
    cell["execution_count"] = None
    return cell


# --- generation ---------------------------------------------------------------


def build_portable(
    canonical_nb: "nbformat.NotebookNode",
    columns: list[str],
    spec: NotebookSpec = CHAPTER_01,
):
    nbf = nbformat.v4
    out = nbf.new_notebook()
    out["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    }
    if spec.colab_title:
        # Colab shows this in its own tab / title bar in preference to the
        # file name; it does not affect nbformat validation or any other tool.
        out["metadata"]["colab"] = {"name": spec.colab_title}
    out["nbformat"] = 4
    out["nbformat_minor"] = 5

    cells = [_banner_cell(nbf, spec), _setup_cell(nbf, spec), _setup_install_cell(nbf, spec)]

    for src_cell in canonical_nb.cells:
        cell_type = src_cell["cell_type"]
        source = src_cell["source"]
        if isinstance(source, list):
            source = "".join(source)

        if cell_type == "markdown":
            if _admonition_title(source) in spec.drop_admonition_titles:
                continue
            iframe_title = _iframe_title(source)
            if iframe_title is not None:
                if iframe_title not in spec.iframe_replacements:
                    raise SystemExit(
                        f"Unknown activity iframe title: {iframe_title!r}"
                    )
                source = spec.iframe_replacements[iframe_title]
            source = convert_myst_directives(source)
            new = nbf.new_markdown_cell(source)
            new["id"] = src_cell["id"]
            new["metadata"] = {}
            cells.append(new)
            if iframe_title is not None and iframe_title in spec.iframe_followup_code:
                followup = nbf.new_code_cell(spec.iframe_followup_code[iframe_title])
                followup["id"] = spec.iframe_followup_ids[iframe_title]
                followup["metadata"] = {}
                followup["outputs"] = []
                followup["execution_count"] = None
                cells.append(followup)

        elif cell_type == "code":
            if spec.rewrite_columns and "eda_phenotype_columns.json" in source:
                source = _rewrite_data_loading(source, columns)
            new = nbf.new_code_cell(source)
            new["id"] = src_cell["id"]
            new["metadata"] = {}
            if src_cell["id"] in spec.preserve_output_ids:
                new["outputs"] = _preserved_outputs(src_cell)
            else:
                new["outputs"] = []
            new["execution_count"] = None
            cells.append(new)

        elif cell_type == "raw":
            new = nbf.new_raw_cell(source)
            new["id"] = src_cell["id"]
            new["metadata"] = {}
            cells.append(new)

        else:  # pragma: no cover - notebooks only have the three types above
            raise SystemExit(f"Unexpected cell type: {cell_type!r}")

    out["cells"] = cells
    _assert_portable(out, spec)
    return out


def _assert_portable(nb: "nbformat.NotebookNode", spec: NotebookSpec = CHAPTER_01) -> None:
    nbformat.validate(nb)

    ids = [c["id"] for c in nb.cells]
    if len(ids) != len(set(ids)):
        raise SystemExit("portable notebook has duplicate cell ids")

    banned = {
        "<iframe": "an iframe",
        "_static/": "a book/_static path",
        "../../config/": "a repo-relative config path",
        "requirements.txt": "a repository requirements.txt instruction",
        "```{": "a MyST directive fence",
        "colab.research.google.com/github": "a self-referential Colab link",
        "ipywidgets": "an ipywidgets import",
        "require(": "a Node/RequireJS call",
        **spec.extra_banned,
    }
    for cell in nb.cells:
        source = cell["source"]
        if isinstance(source, list):
            source = "".join(source)
        for needle, what in banned.items():
            if needle in source:
                raise SystemExit(
                    f"portable notebook still contains {what}: {needle!r}"
                )
        if cell["cell_type"] == "code":
            tags = cell.get("metadata", {}).get("tags", [])
            if set(tags) & HIDE_TAGS:
                raise SystemExit(f"portable code cell keeps a hide tag: {tags}")
            if cell.get("outputs") and cell["id"] not in spec.preserve_output_ids:
                raise SystemExit(
                    f"portable code cell {cell['id']} keeps stored outputs"
                )
            if cell.get("execution_count") is not None:
                raise SystemExit(
                    f"portable code cell {cell['id']} keeps an execution_count"
                )

    # Output-preserving cells must actually carry their deterministic, sanitised
    # outputs, and nothing else may.
    preserved = [c for c in nb.cells if c["id"] in spec.preserve_output_ids]
    if len(preserved) != len(spec.preserve_output_ids):
        raise SystemExit("portable notebook lost an output-preserving cell")
    for cell in preserved:
        outs = cell.get("outputs") or []
        if not outs:
            raise SystemExit(f"cell {cell['id']} lost its preserved outputs")
        if set(cell.get("metadata", {}).get("tags", [])) & HIDE_TAGS:
            raise SystemExit(f"output-preserving cell {cell['id']} has a hide tag")
        for out in outs:
            if out.get("output_type") not in {"display_data", "execute_result", "stream"}:
                raise SystemExit(f"cell {cell['id']} has an unexpected output type: {out.get('output_type')!r}")
            if "execution_count" in out and out["execution_count"] is not None:
                raise SystemExit(f"cell {cell['id']} output kept an execution_count")
            if out.get("metadata"):
                raise SystemExit(f"cell {cell['id']} output kept transient metadata")
            payload = out.get("text", "") or "".join(
                "".join(v) if isinstance(v, list) else v
                for v in out.get("data", {}).values()
            )
            if "SITE_ID" not in payload:
                raise SystemExit(f"cell {cell['id']} preserved output is not the expected pandas table")

    outputful = [
        c["id"]
        for c in nb.cells
        if c["cell_type"] == "code" and (c.get("outputs") or [])
    ]
    if set(outputful) != set(spec.preserve_output_ids):
        raise SystemExit(
            f"exactly {sorted(spec.preserve_output_ids)} may keep outputs; got {sorted(outputful)}"
        )

    joined = "\n".join(
        "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        for c in nb.cells
    )
    if spec.rewrite_columns:
        if "CURATED_COLUMNS" not in joined:
            raise SystemExit("portable notebook lost the embedded CURATED_COLUMNS list")
        if "CURATED_COLUMNS = json.loads" in joined:
            raise SystemExit("portable notebook still reads the column list from a file")
    if spec.require_pinned_source and spec.require_pinned_source not in joined:
        raise SystemExit("portable notebook lost the pinned public data URL")

    ids = [c["id"] for c in nb.cells]
    if SETUP_INSTALL_ID not in ids:
        raise SystemExit("portable notebook is missing the optional install cell")
    install = next(c for c in nb.cells if c["id"] == SETUP_INSTALL_ID)
    install_src = "".join(install["source"]) if isinstance(install["source"], list) else install["source"]
    if f"# %pip install {spec.lesson_packages}" not in install_src:
        raise SystemExit("portable install cell lost its commented %pip install line")
    for cell in nb.cells:
        src = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith(("%pip install", "!pip install", "%pip3 install", "!pip3 install")):
                raise SystemExit(f"portable notebook has an active install command: {stripped!r}")


def serialize(nb: "nbformat.NotebookNode") -> str:
    text = nbformat.writes(nb, version=4)
    if not text.endswith("\n"):
        text += "\n"
    return text


# --- CLI --------------------------------------------------------------------


def _build_for(spec: NotebookSpec):
    canonical = nbformat.read(spec.canonical, as_version=4)
    columns = json.loads(COLUMNS_JSON.read_text(encoding="utf-8")) if spec.rewrite_columns else []
    portable = build_portable(canonical, columns, spec)
    return portable, serialize(portable)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="(re)generate the portable notebook(s)")
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail if a committed portable notebook is stale or missing",
    )
    parser.add_argument(
        "--notebook",
        choices=(*NOTEBOOKS.keys(), "all"),
        default="all",
        help="which notebook --write / --check operates on (default: all)",
    )
    args = parser.parse_args(argv)

    specs = list(NOTEBOOKS.values()) if args.notebook == "all" else [NOTEBOOKS[args.notebook]]
    exit_code = 0
    for spec in specs:
        portable, rendered = _build_for(spec)
        if args.write:
            spec.portable.parent.mkdir(parents=True, exist_ok=True)
            existing = spec.portable.read_text(encoding="utf-8") if spec.portable.exists() else None
            if existing == rendered:
                print(f"portable notebook already up to date: {_rel(spec.portable)}")
                continue
            spec.portable.write_text(rendered, encoding="utf-8")
            print(f"wrote {_rel(spec.portable)} ({len(portable.cells)} cells)")
            continue

        # --check
        if not spec.portable.exists():
            print(
                f"ERROR: {_rel(spec.portable)} is missing. Run "
                "`python scripts/build_portable_notebook.py --write`.",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        if spec.portable.read_text(encoding="utf-8") != rendered:
            print(
                f"ERROR: {_rel(spec.portable)} is stale. Run "
                "`python scripts/build_portable_notebook.py --write` and commit.",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        print(f"portable notebook is up to date ({len(portable.cells)} cells): {_rel(spec.portable)}")
    return exit_code


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
