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

``--notebook {chapter_01,chapter_02,all}`` (default ``all``) scopes both modes.
The bare ``--write`` / ``--check`` invocations keep working and now cover every
registered notebook.

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
    rewrite_columns: bool = False
    require_pinned_source: str = "neurohackademy/nh2020-curriculum/"
    extra_banned: dict[str, str] = field(default_factory=dict)


_CH1_BANNER = (
    "# Exercise 1 - Exploratory data analysis (EDA) - portable notebook\n"
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
    "# Exercise II: Regression - portable notebook\n"
    "\n"
    "This is the **portable version** of the Exercise II regression practice\n"
    "from **Machine Learning for Neuroscience**, generated from the canonical\n"
    "course notebook by `scripts/build_portable_notebook.py`. It is meant for\n"
    "running or editing the code in Google Colab or in a local VS Code /\n"
    "Jupyter setup.\n"
    "\n"
    "The richer version -- with the feature-set comparison activity embedded\n"
    "and running in the browser -- is the published course page:\n"
    "<" + PUBLISHED_PAGE_CH2 + ">\n"
    "\n"
    "In this notebook the interactive activity is replaced by a link to that\n"
    "page; every Python analysis cell is kept and runnable. Questions marked\n"
    "*Think first* are followed, where one exists, by a collapsible *Check\n"
    "your reasoning* block; open questions are left without one fixed answer."
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
    "their cross-validated performance on one fixed cohort and one fixed set\n"
    "of folds.\n"
    "\n"
    "> **Interactive version on the course website.** It is embedded in the\n"
    "> published Exercise II page:\n"
    "> <" + PUBLISHED_PAGE_CH2 + ">\n"
    "> This portable notebook links to it instead of embedding it. The\n"
    "> Python sections below still run the same kind of comparison directly."
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
        "The interactive explorer lets you choose an X and a Y variable, switch\n"
        "between Pearson and Spearman, colour the points by diagnostic group or\n"
        "sex, and read off the coefficient, the pairwise-complete `n`, and how\n"
        "many participants were dropped for a missing value.\n"
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
        "Interactive feature-set comparison for predicting IQ from brain structure": (
            _CH2_IFRAME_REPLACEMENT
        )
    },
    preserve_output_ids=frozenset(),
    rewrite_columns=False,
)

NOTEBOOKS = {CHAPTER_01.key: CHAPTER_01, CHAPTER_02.key: CHAPTER_02}

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
