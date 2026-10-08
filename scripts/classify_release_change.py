#!/usr/bin/env python3
"""Deterministic change classifier for the course release gate (WP50).

WP49 (section H) established the intended policy for future single-notebook
work: a full offline-suite-plus-full-browser-suite run is the exception, not
the default, for a change scoped to one notebook. This script is that policy,
implemented once, used identically by CI (`.github/workflows/deploy.yml`) and
locally (`scripts/run_selected_checks.py`, or run this script directly).

What it computes, in order:

1. The **comparison base**: the source commit of the *last successfully
   published* site, not simply the previous push to `main` (several pushes
   can fail before a later fix). `peaceiris/actions-gh-pages` already writes
   this, deterministically, as the `gh-pages` branch's own HEAD commit
   message (`deploy: <40-hex-sha>`) -- and only when the "Publish website"
   step actually runs, i.e. only on a successful job, so a failed or
   cancelled run never becomes the new base by construction. This script
   reads that marker rather than inventing a new one. A missing, corrupt, or
   unreachable marker, or a marker SHA that is not an ancestor of HEAD
   (force-push/history rewrite), is treated as **untrustworthy** and forces
   the full gate.
2. The **changed paths** between that base and HEAD (`git diff --name-status
   -M`), with renames contributing both their old and new path.
3. Each path's **classification**: WP docs (`WPs/**`), one exercise's own
   scoped surface (1-8 only -- 9-12 stay unpublished, see
   `book/config/exercise_manifest.json`), a shared/global surface, or an
   unrecognized ("unknown") path. No changed path is ever silently dropped.
4. For a change confined to one or more exercises' own scoped paths (no
   shared/unknown path touched), whether each touched exercise's actual
   *generated* notebooks (the JupyterLite template, its portable copies, and
   its transition page -- not the generator source, and not a commit
   message) differ **only** in markdown-cell wording: identical cell
   order/type, identical code-cell sources, identical cell and notebook
   metadata, identical outputs. Any other difference (including a changed
   string inside a code cell, e.g. a multiple-choice label) escalates that
   exercise.
5. The final **gate**: `skip` (WP docs only), `prose` (every touched
   exercise verified prose-only), `exercise` (one or more touched exercises
   have a real content/code/metadata change, but nothing shared), or `full`
   (a shared/unknown path changed, or the base itself is untrustworthy).

Usage:
    .venv/bin/python scripts/classify_release_change.py
    .venv/bin/python scripts/classify_release_change.py --format json
    .venv/bin/python scripts/classify_release_change.py --base-ref <sha> --head-ref <sha>
    .venv/bin/python scripts/classify_release_change.py --github-output "$GITHUB_OUTPUT"

`--base-ref` overrides automatic gh-pages-marker resolution (for local
testing/simulation, or CI re-runs where you want to pin a base explicitly).
It is still validated (must be a reachable ancestor of `--head-ref`) unless
`--force-base` is also given, which exists only so this script's own test
suite and local fixtures can exercise the "untrustworthy base" path on
purpose.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]

PUBLISHED_EXERCISE_NUMBERS = range(1, 9)  # Exercises 1-8 only; 9-12 stay legacy/unpublished.

GATE_SKIP = "skip"
GATE_PROSE = "prose"
GATE_EXERCISE = "exercise"
GATE_FULL = "full"


# --------------------------------------------------------------------------
# git plumbing
# --------------------------------------------------------------------------


def _run(args: list[str], repo_root: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------
# comparison base resolution
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseResolution:
    sha: str | None
    trustworthy: bool
    reason: str


def resolve_base(
    *,
    head_ref: str,
    gh_pages_ref: str,
    explicit_base: str | None,
    repo_root: Path,
    force_base: bool = False,
) -> BaseResolution:
    if explicit_base:
        candidate, source = explicit_base, "explicit --base-ref"
    else:
        rc, out, err = _run(["log", "-1", "--format=%s", gh_pages_ref], repo_root)
        if rc != 0:
            return BaseResolution(
                None, False, f"could not read {gh_pages_ref}: {(err or out).strip() or 'ref not found'}"
            )
        message = out.strip()
        match = re.fullmatch(r"deploy:\s*([0-9a-fA-F]{40})", message)
        if not match:
            return BaseResolution(
                None, False, f"unrecognized publish marker on {gh_pages_ref}'s HEAD commit message: {message!r}"
            )
        candidate, source = match.group(1).lower(), f"{gh_pages_ref} marker commit message"

    if force_base:
        return BaseResolution(candidate, True, f"resolved from {source} (ancestor check bypassed by --force-base)")

    rc, _, _ = _run(["cat-file", "-e", f"{candidate}^{{commit}}"], repo_root)
    if rc != 0:
        return BaseResolution(
            candidate,
            False,
            f"{source} names {candidate}, which is not a reachable commit object in this checkout "
            "(missing/corrupt/shallow)",
        )

    rc, _, _ = _run(["merge-base", "--is-ancestor", candidate, head_ref], repo_root)
    if rc != 0:
        return BaseResolution(
            candidate,
            False,
            f"{source} names {candidate}, which is not an ancestor of {head_ref} "
            "(possible force-push/history rewrite) -- treating conservatively",
        )

    return BaseResolution(candidate, True, f"resolved from {source}")


# --------------------------------------------------------------------------
# changed paths
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ChangedPath:
    status: str
    path: str
    old_path: str | None = None


def changed_paths(base_sha: str, head_ref: str, repo_root: Path) -> list[ChangedPath]:
    rc, out, err = _run(["diff", "--name-status", "-M", base_sha, head_ref], repo_root)
    if rc != 0:
        raise RuntimeError(f"git diff --name-status -M {base_sha} {head_ref} failed: {err.strip()}")
    entries: list[ChangedPath] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            entries.append(ChangedPath(status, parts[2], parts[1]))
        else:
            entries.append(ChangedPath(status, parts[1]))
    return entries


# --------------------------------------------------------------------------
# per-path classification
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PathClass:
    path: str
    kind: str  # "wp_docs" | "exercise" | "shared" | "unknown"
    exercise: int | None
    reason: str


# (pattern, human reason) -- order matters, first match wins. These are the
# surfaces the gate table (WP50 spec) calls "shared helper/CSS, data export,
# package dependency, manifest, book/JupyterLite config, workflow,
# Playwright shared fixture, deployment mechanism" -- any one of them forces
# the full gate regardless of how many (or how few) exercises also changed.
_SHARED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\.github/workflows/"), "CI workflow"),
    (re.compile(r"^book/_config\.yml$"), "Sphinx/book config"),
    (re.compile(r"^book/_toc\.yml$"), "book table of contents"),
    (re.compile(r"^book/lite/jupyter_lite_config\.json$"), "JupyterLite config"),
    (re.compile(r"^book/lite/overrides\.json$"), "JupyterLite shared overrides"),
    (re.compile(r"^book/lite/extensions/"), "JupyterLite course-toolbar extension (shared by every exercise)"),
    (re.compile(r"^book/config/"), "shared manifest/config (e.g. exercise_manifest.json)"),
    (re.compile(r"^book/lite/files/data/"), "shared exported data asset"),
    (re.compile(r"^book/_static/widgets/"), "shared widget-data export"),
    (re.compile(r"^scripts/export_"), "shared data-export script"),
    (
        re.compile(
            r"^scripts/(build_portable_notebook|smoke_portable_notebook|semantic_json_compare|binary_asset)\.py$"
        ),
        "shared notebook/asset tooling",
    ),
    (
        re.compile(r"^scripts/(classify_release_change|run_selected_checks|smoke_release_routes)\.py$"),
        "the release classifier/runner itself",
    ),
    (re.compile(r"^scripts/"), "shared script (not a per-exercise generator)"),
    (re.compile(r"^requirements(-lite)?\.txt$"), "Python package dependency pin"),
    (
        re.compile(r"^interactive/(package(-lock)?\.json|tsconfig\.json|vite\.config\.ts|index\.html)$"),
        "frontend package/build config",
    ),
    (re.compile(r"^interactive/playwright(\.book)?\.config\.ts$"), "Playwright shared fixture/config"),
    (re.compile(r"^interactive/src/"), "shared widget-app source"),
    (re.compile(r"^interactive/e2e/"), "shared widget-app browser tests"),
    (re.compile(r"^interactive/tests/"), "shared widget-app unit tests"),
    (re.compile(r"^interactive/e2e-book/"), "shared book browser-test fixture/spec"),
    (re.compile(r"^tests/"), "shared Python test (not one exercise's own test file)"),
    (re.compile(r"^book/chapters/"), "book chapter content outside the published Exercises 1-8 transition pages"),
    (re.compile(r"^book/downloads/"), "portable-notebook download outside Exercises 1-8"),
    (re.compile(r"^book/(intro|syllabus|contents)\.md$"), "book hub page"),
    (re.compile(r"^Homework_Materials/"), "Homework_Materials (separate nested repository)"),
]


def classify_path(path: str) -> PathClass:
    if path == "WPs" or path.startswith("WPs/"):
        return PathClass(path, "wp_docs", None, "WP report/spec documentation (never read at runtime)")

    match = re.fullmatch(r"scripts/generate_exercise_(0[1-8])_(notebook|transition_page)\.py", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise generator script")

    match = re.fullmatch(r"scripts/reference_notebooks/exercise_(0[1-8])_reference\.ipynb", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise reference notebook")

    match = re.fullmatch(r"book/chapters/chapter_(0[1-8])/exercise_(0[1-8])\.ipynb", path)
    if match and match.group(1) == match.group(2):
        return PathClass(path, "exercise", int(match.group(1)), "exercise transition page")

    match = re.fullmatch(r"book/lite/files/exercise_(0[1-8])(?:_portable)?\.ipynb", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise JupyterLite template/portable copy")

    match = re.fullmatch(r"book/downloads/chapter_(0[1-8])/exercise_(0[1-8])_portable\.ipynb", path)
    if match and match.group(1) == match.group(2):
        return PathClass(path, "exercise", int(match.group(1)), "exercise portable download")

    match = re.fullmatch(r"tests/test_exercise_(0[1-8])_(lite_notebook|reference_execution|transition_page)\.py", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise's own test file")

    match = re.fullmatch(r"interactive/e2e-book/exercise-(0[1-8])-lite\.spec\.ts", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise's own JupyterLite browser spec")

    match = re.fullmatch(r"interactive/e2e-book/chapter(0[1-8])\.spec\.ts", path)
    if match:
        return PathClass(path, "exercise", int(match.group(1)), "exercise's own transition-page browser spec")

    for pattern, reason in _SHARED_PATTERNS:
        if pattern.search(path):
            return PathClass(path, "shared", None, reason)

    return PathClass(path, "unknown", None, "no recognized classification rule matches this path")


# --------------------------------------------------------------------------
# prose-only verification (compares *generated* notebooks, not source diffs)
# --------------------------------------------------------------------------


def _generated_notebook_paths(n: int) -> list[str]:
    nn = f"{n:02d}"
    return [
        f"book/lite/files/exercise_{nn}.ipynb",
        f"book/lite/files/exercise_{nn}_portable.ipynb",
        f"book/downloads/chapter_{nn}/exercise_{nn}_portable.ipynb",
        f"book/chapters/chapter_{nn}/exercise_{nn}.ipynb",
        f"scripts/reference_notebooks/exercise_{nn}_reference.ipynb",
    ]


def _notebook_json_at(ref: str, path: str, repo_root: Path) -> dict | None:
    rc, out, _err = _run(["show", f"{ref}:{path}"], repo_root)
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None  # corrupt/unparseable -> caller treats as "differs"


def notebooks_differ_beyond_prose(old: dict, new: dict) -> str | None:
    """Return a human reason if `old` -> `new` is more than a wording change, else None."""
    if old.get("metadata") != new.get("metadata"):
        return "notebook-level metadata changed"
    old_cells, new_cells = old.get("cells", []), new.get("cells", [])
    if len(old_cells) != len(new_cells):
        return f"cell count changed ({len(old_cells)} -> {len(new_cells)})"
    for index, (a, b) in enumerate(zip(old_cells, new_cells)):
        if a.get("cell_type") != b.get("cell_type"):
            return f"cell {index} changed type ({a.get('cell_type')} -> {b.get('cell_type')})"
        if a.get("id") != b.get("id"):
            return f"cell {index} changed id"
        if a.get("metadata") != b.get("metadata"):
            return f"cell {index} metadata changed"
        if a.get("cell_type") == "code":
            if a.get("source") != b.get("source"):
                return f"cell {index} code-cell source changed"
            if a.get("outputs", []) != b.get("outputs", []):
                return f"cell {index} code-cell outputs changed"
            if a.get("execution_count") != b.get("execution_count"):
                return f"cell {index} execution_count changed"
        elif a.get("source") != b.get("source"):
            continue  # markdown/raw wording changes are exactly what "prose-only" allows
    return None


def exercise_is_prose_only(n: int, base_sha: str, head_ref: str, repo_root: Path) -> tuple[bool, str]:
    for relpath in _generated_notebook_paths(n):
        old = _notebook_json_at(base_sha, relpath, repo_root)
        new = _notebook_json_at(head_ref, relpath, repo_root)
        if old is None or new is None:
            return False, f"{relpath} missing or unparseable at base or head -- escalating conservatively"
        reason = notebooks_differ_beyond_prose(old, new)
        if reason is not None:
            return False, f"{relpath}: {reason}"
    return True, "every generated notebook for this exercise differs only in markdown-cell wording"


ProseChecker = Callable[[int, str, str, Path], tuple[bool, str]]


# --------------------------------------------------------------------------
# overall classification
# --------------------------------------------------------------------------


@dataclass
class Classification:
    base: BaseResolution
    head_ref: str
    path_classes: list[PathClass] = field(default_factory=list)
    gate: str = GATE_FULL
    exercises: list[int] = field(default_factory=list)
    prose_detail: dict[int, tuple[bool, str]] = field(default_factory=dict)
    reason: str = ""


def classify(
    *,
    base: BaseResolution,
    head_ref: str,
    raw_changed: list[ChangedPath],
    repo_root: Path,
    prose_checker: ProseChecker = exercise_is_prose_only,
) -> Classification:
    path_classes: list[PathClass] = []
    for entry in raw_changed:
        path_classes.append(classify_path(entry.path))
        if entry.old_path is not None and entry.old_path != entry.path:
            path_classes.append(classify_path(entry.old_path))

    if not base.trustworthy:
        return Classification(
            base,
            head_ref,
            path_classes,
            GATE_FULL,
            sorted({c.exercise for c in path_classes if c.exercise is not None}),
            {},
            f"untrustworthy comparison base: {base.reason}",
        )

    non_doc = [c for c in path_classes if c.kind != "wp_docs"]
    if not non_doc:
        return Classification(base, head_ref, path_classes, GATE_SKIP, [], {}, "only WPs/** paths changed since the base")

    blockers = [c for c in non_doc if c.kind in ("shared", "unknown")]
    if blockers:
        unique = []
        seen = set()
        for c in blockers:
            if c.path not in seen:
                seen.add(c.path)
                unique.append(c)
        detail = "; ".join(f"{c.path} ({c.kind}: {c.reason})" for c in unique[:10])
        more = "" if len(unique) <= 10 else f" (+{len(unique) - 10} more)"
        return Classification(
            base,
            head_ref,
            path_classes,
            GATE_FULL,
            sorted({c.exercise for c in non_doc if c.exercise is not None}),
            {},
            f"shared/unknown path(s) changed: {detail}{more}",
        )

    exercises = sorted({c.exercise for c in non_doc if c.exercise is not None})
    prose_detail: dict[int, tuple[bool, str]] = {}
    for n in exercises:
        prose_detail[n] = prose_checker(n, base.sha, head_ref, repo_root)

    if all(ok for ok, _ in prose_detail.values()):
        gate = GATE_PROSE
        reason = "every touched exercise's generated notebooks differ only in markdown wording"
    else:
        gate = GATE_EXERCISE
        escalated = ", ".join(str(n) for n, (ok, _) in prose_detail.items() if not ok)
        reason = f"exercise(s) {escalated} have a non-prose change (code, metadata, outputs, or structure)"

    return Classification(base, head_ref, path_classes, gate, exercises, prose_detail, reason)


def classify_release(
    repo_root: Path,
    *,
    head_ref: str = "HEAD",
    explicit_base: str | None = None,
    gh_pages_ref: str = "origin/gh-pages",
    force_base: bool = False,
    prose_checker: ProseChecker = exercise_is_prose_only,
) -> Classification:
    base = resolve_base(
        head_ref=head_ref,
        gh_pages_ref=gh_pages_ref,
        explicit_base=explicit_base,
        repo_root=repo_root,
        force_base=force_base,
    )
    if not base.trustworthy:
        return classify(base=base, head_ref=head_ref, raw_changed=[], repo_root=repo_root, prose_checker=prose_checker)
    raw = changed_paths(base.sha, head_ref, repo_root)
    return classify(base=base, head_ref=head_ref, raw_changed=raw, repo_root=repo_root, prose_checker=prose_checker)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def to_machine_dict(c: Classification) -> dict:
    return {
        "gate": c.gate,
        "exercises": c.exercises,
        "reason": c.reason,
        "base": {"sha": c.base.sha, "trustworthy": c.base.trustworthy, "reason": c.base.reason},
        "head_ref": c.head_ref,
        "changed_paths": [
            {"path": p.path, "kind": p.kind, "exercise": p.exercise, "reason": p.reason} for p in c.path_classes
        ],
        "prose_detail": {str(n): {"prose_only": ok, "reason": why} for n, (ok, why) in c.prose_detail.items()},
    }


def human_report(c: Classification) -> str:
    lines = [
        f"comparison base: {c.base.sha or '(none)'}  [{'trustworthy' if c.base.trustworthy else 'UNTRUSTWORTHY'}] -- {c.base.reason}",
        f"head: {c.head_ref}",
        f"changed paths ({len(c.path_classes)}):",
    ]
    for p in c.path_classes:
        tag = f"ex{p.exercise}" if p.exercise is not None else p.kind
        lines.append(f"  [{tag:>6}] {p.path}  ({p.reason})")
    if c.prose_detail:
        lines.append("prose-only verification:")
        for n, (ok, why) in sorted(c.prose_detail.items()):
            lines.append(f"  exercise {n}: {'PROSE-ONLY' if ok else 'ESCALATED'} -- {why}")
    lines.append(f"affected exercise IDs: {c.exercises or '(none)'}")
    lines.append(f"GATE: {c.gate}")
    lines.append(f"reason: {c.reason}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-ref", default=None, help="override automatic gh-pages-marker base resolution")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--gh-pages-ref", default="origin/gh-pages")
    parser.add_argument(
        "--force-base",
        action="store_true",
        help="skip the ancestor/reachability check on --base-ref (testing only)",
    )
    parser.add_argument("--format", choices=("human", "json", "both"), default="human")
    parser.add_argument("--github-output", default=None, help="path to append gate=/exercises=/reason= to (GITHUB_OUTPUT)")
    args = parser.parse_args()

    c = classify_release(
        REPO_ROOT,
        head_ref=args.head_ref,
        explicit_base=args.base_ref,
        gh_pages_ref=args.gh_pages_ref,
        force_base=args.force_base,
    )

    if args.format in ("human", "both"):
        print(human_report(c))
    if args.format in ("json", "both"):
        print(json.dumps(to_machine_dict(c), indent=2))

    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.write(f"gate={c.gate}\n")
            fh.write(f"exercises={json.dumps(c.exercises)}\n")
            fh.write(f"reason={c.reason}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
