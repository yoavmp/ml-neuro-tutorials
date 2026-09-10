#!/usr/bin/env python3
"""Generate the portable Colab / VS Code notebook from the canonical EDA notebook.

The canonical notebook ``book/chapters/chapter_01/exercise_01.ipynb`` is written
for Jupyter Book: it embeds the four browser activities as ``<iframe>`` elements
and uses MyST directives (``{admonition}``, ``{dropdown}``) that only render
inside Sphinx. That file stays the single source of truth.

This script derives a second, self-contained notebook:

    book/downloads/chapter_01/exercise_01_portable.ipynb

that a casual user can open in Google Colab or download and run in VS Code /
Jupyter with only the packages that ship with a normal scientific-Python setup
(numpy, pandas, matplotlib, seaborn -- all preinstalled on Colab). The portable
notebook:

* keeps every ordinary Markdown cell and every runnable Python analysis cell;
* replaces each ``<iframe>`` activity with a short Markdown pointer to the
  published course page;
* rewrites MyST directives as plain Markdown headings / ``<details>`` blocks;
* drops Jupyter Book presentation tags/metadata (``hide-input`` etc.) and clears
  every code cell's stored output -- with **one** deliberate, stable exception:
  the sampling-methods cell ``7a1e5c93d204`` keeps its three saved pandas table
  outputs, because the portable notebook does not embed the interactive
  head/tail/sample activity and a reader who only reads it should still see what
  the three methods return (WP10 §3). Its outputs are sanitised of
  environment-specific execution metadata but are otherwise the deterministic
  pandas HTML/plain-text tables from the canonical notebook, and re-running the
  cell in Colab / VS Code / Jupyter simply refreshes them;
* embeds the curated ABIDE-II column list so no repository file is needed
  (the canonical notebook reads it from ``book/config/``);
* loads the ABIDE-II CSV from the same pinned HTTPS URL the canonical notebook
  uses;
* carries a banner identifying it as the portable derivative and linking back to
  the richer course page, plus an optional, commented-out ``%pip install`` cell
  for the four packages the lesson imports.

Modes (exactly one required):

* ``--write``   -- (re)generate the portable notebook on disk.
* ``--check``   -- regenerate in memory and fail if the committed file is stale
                   or missing. Used by CI. No network access, no writes.

Determinism: the output depends only on the two committed inputs (the canonical
notebook and ``book/config/eda_phenotype_columns.json``). Serialization goes
through ``nbformat.writes`` (sorted keys, fixed indent) with a single trailing
newline; cell ids are stable (passthrough cells keep their id, generated cells
use fixed literal ids). Running ``--write`` twice is a no-op.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb"
COLUMNS_JSON = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
PORTABLE = REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb"

PUBLISHED_PAGE = (
    "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html"
)

# Markdown admonitions that are navigation for the Jupyter Book page only. They
# have no place in the portable notebook (the banner below replaces them).
DROP_ADMONITION_TITLES = {
    "Run or download this notebook",
    "How to use this notebook",
}

# Per-activity replacement for the three `<iframe>` cells, keyed by the iframe
# `title` attribute. Each keeps: what the activity explores, an HTTPS link to the
# published page, and a note that the embedded version lives on the course site.
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

BANNER_ID = "portable-banner"
SETUP_ID = "portable-setup"
SETUP_INSTALL_ID = "portable-setup-install"

# The single code cell whose saved outputs the portable notebook keeps. The
# portable notebook has no embedded head/tail/sample activity, so this cell's
# three pandas tables are the only place a pure reader sees what the methods
# return. Every other code cell is emitted output-free. (WP10 §3.)
PRESERVE_OUTPUT_IDS = frozenset({"7a1e5c93d204"})

# Packages the lesson actually imports that are not part of the Python standard
# library (json / pathlib / IPython are always available). Kept in sync by hand
# with the notebook's `import` lines; build/test tooling is deliberately excluded.
LESSON_PACKAGES = "numpy pandas matplotlib seaborn"

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
    such blocks (a "Think first" card plus a "Check your reasoning" dropdown);
    every block is converted and any text between/around them is kept verbatim.
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

    The canonical notebook reads ``book/config/eda_phenotype_columns.json`` with
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
    """Copy one saved output, dropping environment-specific execution metadata.

    Keeps the deterministic payload (``text/html`` / ``text/plain`` pandas
    tables, stream text) and ``output_type``; drops per-output
    ``execution_count`` and any ``metadata`` (timestamps, transient ids) so the
    result depends only on the committed canonical notebook.
    """
    clean: dict = {"output_type": out["output_type"]}
    if "name" in out:
        clean["name"] = out["name"]
    if "text" in out:
        clean["text"] = out["text"]
    if "data" in out:
        clean["data"] = json.loads(json.dumps(out["data"]))  # deep copy, JSON-safe
    # execute_result keeps a stable execution_count for nbformat validity;
    # display_data / stream have none.
    if out["output_type"] == "execute_result":
        clean["execution_count"] = None
    clean.setdefault("metadata", {})
    return nbformat.from_dict(clean)


def _preserved_outputs(src_cell) -> list:
    """The sanitised saved outputs for a PRESERVE_OUTPUT_IDS cell."""
    outputs = src_cell.get("outputs", []) or []
    if not outputs:
        raise SystemExit(
            f"cell {src_cell['id']} is marked output-preserving but the canonical "
            "notebook has no saved output for it; re-execute the canonical notebook"
        )
    return [_sanitise_output(o) for o in outputs]


def _banner_cell(nbf) -> "nbformat.NotebookNode":
    cell = nbf.new_markdown_cell(
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
    cell["id"] = BANNER_ID
    cell["metadata"] = {}
    return cell


def _setup_cell(nbf) -> "nbformat.NotebookNode":
    cell = nbf.new_markdown_cell(
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
    cell["id"] = SETUP_ID
    cell["metadata"] = {}
    return cell


def _setup_install_cell(nbf) -> "nbformat.NotebookNode":
    cell = nbf.new_code_cell(
        "# If an import below fails, uncomment and run this line once, then\n"
        "# restart the kernel. Safe on Colab, VS Code and Jupyter.\n"
        f"# %pip install {LESSON_PACKAGES}"
    )
    cell["id"] = SETUP_INSTALL_ID
    cell["metadata"] = {}
    cell["outputs"] = []
    cell["execution_count"] = None
    return cell


# --- generation ---------------------------------------------------------------


def build_portable(canonical_nb: "nbformat.NotebookNode", columns: list[str]):
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

    cells = [_banner_cell(nbf), _setup_cell(nbf), _setup_install_cell(nbf)]

    for src_cell in canonical_nb.cells:
        cell_type = src_cell["cell_type"]
        source = src_cell["source"]
        if isinstance(source, list):
            source = "".join(source)

        if cell_type == "markdown":
            if _admonition_title(source) in DROP_ADMONITION_TITLES:
                continue
            iframe_title = _iframe_title(source)
            if iframe_title is not None:
                if iframe_title not in IFRAME_REPLACEMENTS:
                    raise SystemExit(
                        f"Unknown activity iframe title: {iframe_title!r}"
                    )
                source = IFRAME_REPLACEMENTS[iframe_title]
            source = convert_myst_directives(source)
            new = nbf.new_markdown_cell(source)
            new["id"] = src_cell["id"]
            new["metadata"] = {}
            cells.append(new)

        elif cell_type == "code":
            if "eda_phenotype_columns.json" in source:
                source = _rewrite_data_loading(source, columns)
            new = nbf.new_code_cell(source)
            new["id"] = src_cell["id"]
            new["metadata"] = {}
            if src_cell["id"] in PRESERVE_OUTPUT_IDS:
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
    _assert_portable(out)
    return out


def _assert_portable(nb: "nbformat.NotebookNode") -> None:
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
            if cell.get("outputs") and cell["id"] not in PRESERVE_OUTPUT_IDS:
                raise SystemExit(
                    f"portable code cell {cell['id']} keeps stored outputs"
                )
            if cell.get("execution_count") is not None:
                raise SystemExit(
                    f"portable code cell {cell['id']} keeps an execution_count"
                )

    # The one output-preserving cell must actually carry its deterministic,
    # sanitised pandas tables, and nothing else.
    preserved = [c for c in nb.cells if c["id"] in PRESERVE_OUTPUT_IDS]
    if len(preserved) != len(PRESERVE_OUTPUT_IDS):
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
    if set(outputful) != set(PRESERVE_OUTPUT_IDS):
        raise SystemExit(
            f"exactly {sorted(PRESERVE_OUTPUT_IDS)} may keep outputs; got {sorted(outputful)}"
        )

    joined = "\n".join(
        "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        for c in nb.cells
    )
    if "CURATED_COLUMNS" not in joined:
        raise SystemExit("portable notebook lost the embedded CURATED_COLUMNS list")
    if "CURATED_COLUMNS = json.loads" in joined:
        raise SystemExit("portable notebook still reads the column list from a file")
    if "neurohackademy/nh2020-curriculum/" not in joined:
        raise SystemExit("portable notebook lost the pinned ABIDE-II CSV URL")

    ids = [c["id"] for c in nb.cells]
    if SETUP_INSTALL_ID not in ids:
        raise SystemExit("portable notebook is missing the optional install cell")
    install = next(c for c in nb.cells if c["id"] == SETUP_INSTALL_ID)
    install_src = "".join(install["source"]) if isinstance(install["source"], list) else install["source"]
    if f"# %pip install {LESSON_PACKAGES}" not in install_src:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="(re)generate the portable notebook"
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed portable notebook is stale or missing",
    )
    args = parser.parse_args(argv)

    canonical = nbformat.read(CANONICAL, as_version=4)
    columns = json.loads(COLUMNS_JSON.read_text(encoding="utf-8"))
    portable = build_portable(canonical, columns)
    rendered = serialize(portable)

    if args.write:
        PORTABLE.parent.mkdir(parents=True, exist_ok=True)
        existing = PORTABLE.read_text(encoding="utf-8") if PORTABLE.exists() else None
        if existing == rendered:
            print(f"portable notebook already up to date: {_rel(PORTABLE)}")
            return 0
        PORTABLE.write_text(rendered, encoding="utf-8")
        print(f"wrote {_rel(PORTABLE)} ({len(portable.cells)} cells)")
        return 0

    # --check
    if not PORTABLE.exists():
        print(
            f"ERROR: {_rel(PORTABLE)} is missing. Run "
            "`python scripts/build_portable_notebook.py --write`.",
            file=sys.stderr,
        )
        return 1
    if PORTABLE.read_text(encoding="utf-8") != rendered:
        print(
            f"ERROR: {_rel(PORTABLE)} is stale. Run "
            "`python scripts/build_portable_notebook.py --write` and commit.",
            file=sys.stderr,
        )
        return 1
    print(f"portable notebook is up to date ({len(portable.cells)} cells)")
    return 0


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
