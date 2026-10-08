#!/usr/bin/env python3
"""Run the checks `scripts/classify_release_change.py` selects (WP50).

One script, called from both `.github/workflows/deploy.yml` and locally, so
the "selected checks" CI actually runs and the checks a maintainer runs by
hand are guaranteed to be the same set -- never two independently-maintained
lists that can drift apart.

Recomputes the classification itself (deterministic, cheap, no shared state
mutated) rather than taking it as an argument, so there is exactly one
source of truth for "what does this change require."

Gate `full` is intentionally out of scope here: it keeps running the
existing, unchanged steps directly in `.github/workflows/deploy.yml` (the
broad offline Python suite, the full `npm run test:e2e:book`, etc.) -- this
script only ever narrows the fast paths (`prose`, `exercise`), never
widens or replaces the full gate. Gate `skip` has nothing to run.

Two phases, because the exercise-tier's browser spec and both tiers' route
smoke-check need the site already built, while the generator/unit-test
checks do not and should fail fast *before* paying for that build:

    --phase pretest    generator --check + structural (+ reference, for the
                        "exercise" gate only) unittest files for every
                        touched exercise. No site build required.
    --phase postbuild  scripts/smoke_release_routes.py for every touched
                        exercise, plus (gate "exercise" only) the touched
                        exercises' own Playwright specs
                        (exercise-0N-lite.spec.ts + chapterNN.spec.ts).
                        Requires book/_build/html (and, for "exercise", the
                        JupyterLite build under it) to already exist.

Usage:
    .venv/bin/python scripts/run_selected_checks.py --phase pretest
    .venv/bin/python scripts/run_selected_checks.py --phase postbuild
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify_release_change import (  # noqa: E402
    GATE_EXERCISE,
    GATE_PROSE,
    GATE_SKIP,
    classify_release,
    human_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_logged(cmd: list[str], *, cwd: Path = REPO_ROOT) -> bool:
    print(f"+ {' '.join(cmd)}  (cwd={cwd.relative_to(REPO_ROOT) if cwd != REPO_ROOT else '.'})", flush=True)
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd)
    elapsed = time.monotonic() - start
    status = "OK" if proc.returncode == 0 else f"FAILED (exit {proc.returncode})"
    print(f"  -- {status} in {elapsed:.1f}s", flush=True)
    return proc.returncode == 0


def pretest_commands(exercises: list[int], gate: str) -> list[list[str]]:
    cmds: list[list[str]] = []
    for n in exercises:
        nn = f"{n:02d}"
        cmds.append([sys.executable, f"scripts/generate_exercise_{nn}_notebook.py", "--check"])
        cmds.append([sys.executable, f"scripts/generate_exercise_{nn}_transition_page.py", "--check"])
        cmds.append(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", f"test_exercise_{nn}_lite_notebook.py"]
        )
        cmds.append(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", f"test_exercise_{nn}_transition_page.py"]
        )
        if gate == GATE_EXERCISE:
            cmds.append(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    f"test_exercise_{nn}_reference_execution.py",
                ]
            )
    return cmds


def postbuild_commands(exercises: list[int], gate: str, build_dir: str) -> list[tuple[list[str], Path]]:
    cmds: list[tuple[list[str], Path]] = []
    exercise_csv = ",".join(str(n) for n in exercises)
    cmds.append(
        (
            [sys.executable, "scripts/smoke_release_routes.py", "--build-dir", build_dir, "--exercises", exercise_csv],
            REPO_ROOT,
        )
    )
    if gate == GATE_EXERCISE:
        spec_args: list[str] = []
        for n in exercises:
            nn = f"{n:02d}"
            spec_args += [f"exercise-{nn}-lite", f"chapter{nn}"]
        cmds.append(
            (
                ["npx", "playwright", "test", "--config", "playwright.book.config.ts", *spec_args],
                REPO_ROOT / "interactive",
            )
        )
    return cmds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase", choices=("pretest", "postbuild"), required=True)
    parser.add_argument("--build-dir", default="book/_build/html")
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--head-ref", default="HEAD")
    args = parser.parse_args()

    c = classify_release(REPO_ROOT, head_ref=args.head_ref, explicit_base=args.base_ref)
    print(human_report(c))
    print()

    if c.gate == GATE_SKIP:
        print("gate=skip -- nothing to run")
        return
    if c.gate not in (GATE_PROSE, GATE_EXERCISE):
        print(f"gate={c.gate} -- out of scope for this script (handled directly by the full-gate workflow steps)")
        return

    if args.phase == "pretest":
        commands = [(cmd, REPO_ROOT) for cmd in pretest_commands(c.exercises, c.gate)]
    else:
        commands = postbuild_commands(c.exercises, c.gate, args.build_dir)

    overall_start = time.monotonic()
    failures: list[str] = []
    for cmd, cwd in commands:
        if not _run_logged(cmd, cwd=cwd):
            failures.append(" ".join(cmd))
    overall_elapsed = time.monotonic() - overall_start

    print(f"\n{args.phase} phase: {len(commands) - len(failures)}/{len(commands)} checks passed in {overall_elapsed:.1f}s")
    if failures:
        print("FAILED checks:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
