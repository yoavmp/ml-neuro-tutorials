"""Offline tests for scripts/classify_release_change.py (WP50).

Covers the fixture scenarios the WP50 spec names explicitly: a
markdown-only edit; a code-cell edit in one exercise; a changed
multiple-choice label inside a code cell; two exercises changing together
(both prose, and a prose+code mix); a shared helper/config change; an
unknown path; a missing published-base marker; and a prior failed push
followed by a fix (proving the union of changes since the last *successful*
deployment is what gets classified, not just the fix commit's own diff).

Two layers:

* `ClassifyPure*` exercises `classify()` directly with synthetic
  `ChangedPath` lists and a stubbed prose-checker -- no git, no filesystem,
  covers the path-classification/gate-decision logic in isolation.
* `ClassifyEndToEnd*` and `BaseResolution*` build a real, disposable git
  repository under a temp directory and drive the actual
  `classify_release()`/`resolve_base()`/`changed_paths()` entry points
  against real commits -- covers the git plumbing and the real notebook-JSON
  prose-diffing together, including the base-resolution edge cases.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_classify_release_change.py'
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from classify_release_change import (  # noqa: E402
    GATE_EXERCISE,
    GATE_FULL,
    GATE_PROSE,
    GATE_SKIP,
    BaseResolution,
    ChangedPath,
    classify,
    classify_path,
    classify_release,
    notebooks_differ_beyond_prose,
    resolve_base,
)

TRUSTWORTHY_BASE = BaseResolution("0" * 40, True, "test fixture")


def _stub_prose_checker(verdicts: dict[int, bool]):
    def _checker(n, base_sha, head_ref, repo_root):
        ok = verdicts.get(n, False)
        return ok, "stub" if ok else "stub: escalated"

    return _checker


class PathClassification(unittest.TestCase):
    def test_wp_docs(self):
        self.assertEqual(classify_path("WPs/reports/WP50_REPORT.md").kind, "wp_docs")

    def test_exercise_generator_script(self):
        c = classify_path("scripts/generate_exercise_03_notebook.py")
        self.assertEqual((c.kind, c.exercise), ("exercise", 3))

    def test_exercise_lite_template_and_portable_copy(self):
        self.assertEqual(classify_path("book/lite/files/exercise_05.ipynb").exercise, 5)
        self.assertEqual(classify_path("book/lite/files/exercise_05_portable.ipynb").exercise, 5)

    def test_exercise_download_requires_matching_chapter_and_exercise_number(self):
        self.assertEqual(classify_path("book/downloads/chapter_02/exercise_02_portable.ipynb").exercise, 2)
        # Mismatched chapter/exercise numbers should not be silently accepted as exercise-scoped
        # -- it falls through to the shared "book/downloads/" catch-all instead (full gate either way).
        mismatched = classify_path("book/downloads/chapter_02/exercise_03_portable.ipynb")
        self.assertNotEqual(mismatched.kind, "exercise")

    def test_exercise_browser_specs(self):
        self.assertEqual(classify_path("interactive/e2e-book/exercise-07-lite.spec.ts").exercise, 7)
        self.assertEqual(classify_path("interactive/e2e-book/chapter07.spec.ts").exercise, 7)

    def test_shared_manifest_and_workflow_and_data_export(self):
        self.assertEqual(classify_path("book/config/exercise_manifest.json").kind, "shared")
        self.assertEqual(classify_path(".github/workflows/deploy.yml").kind, "shared")
        self.assertEqual(classify_path("scripts/export_abide_lite_data.py").kind, "shared")
        self.assertEqual(classify_path("book/lite/files/data/abide_age_brain.csv").kind, "shared")
        self.assertEqual(classify_path("requirements.txt").kind, "shared")
        self.assertEqual(classify_path("interactive/playwright.book.config.ts").kind, "shared")

    def test_unrelated_shared_browser_spec_is_shared_not_exercise(self):
        # wp22's cross-chapter dark-mode spec touches every exercise at once -- never exercise-scoped.
        self.assertEqual(classify_path("interactive/e2e-book/wp22-cross-chapter-dark-mode.spec.ts").kind, "shared")

    def test_legacy_exercise_paths_are_not_fast_pathed(self):
        # Exercises 9-12 stay legacy/unpublished -- WP50 does not optimize their gate.
        c = classify_path("book/chapters/chapter_09/exercise_09.ipynb")
        self.assertIn(c.kind, ("shared",))

    def test_truly_unknown_path(self):
        self.assertEqual(classify_path("some/brand/new/surface.txt").kind, "unknown")


class NotebookProseDiff(unittest.TestCase):
    @staticmethod
    def _nb(cells, metadata=None):
        return {"cells": cells, "metadata": metadata or {"kernelspec": {}}, "nbformat": 4, "nbformat_minor": 5}

    @staticmethod
    def _md(text, cell_id="md1"):
        return {"cell_type": "markdown", "id": cell_id, "metadata": {}, "source": text}

    @staticmethod
    def _code(text, cell_id="code1"):
        return {"cell_type": "code", "id": cell_id, "metadata": {}, "outputs": [], "execution_count": None, "source": text}

    def test_markdown_only_wording_change_is_prose_only(self):
        old = self._nb([self._md("Hello"), self._code("x = 1")])
        new = self._nb([self._md("Hello, world"), self._code("x = 1")])
        self.assertIsNone(notebooks_differ_beyond_prose(old, new))

    def test_code_cell_source_change_escalates(self):
        old = self._nb([self._md("Hello"), self._code("x = 1")])
        new = self._nb([self._md("Hello"), self._code("x = 2")])
        self.assertIsNotNone(notebooks_differ_beyond_prose(old, new))

    def test_mc_label_change_inside_code_cell_escalates(self):
        old = self._nb([self._code('options = ["Option A: bias", "Option B: variance"]')])
        new = self._nb([self._code('options = ["Option A: bias", "Option C: noise"]')])
        self.assertIsNotNone(notebooks_differ_beyond_prose(old, new))

    def test_cell_count_change_escalates(self):
        old = self._nb([self._md("Hello")])
        new = self._nb([self._md("Hello"), self._md("New cell")])
        self.assertIsNotNone(notebooks_differ_beyond_prose(old, new))

    def test_notebook_metadata_change_escalates(self):
        old = self._nb([self._md("Hello")], metadata={"wp41": {"templateVersion": 1}})
        new = self._nb([self._md("Hello")], metadata={"wp41": {"templateVersion": 2}})
        self.assertIsNotNone(notebooks_differ_beyond_prose(old, new))

    def test_code_cell_output_change_escalates(self):
        old = self._nb([self._code("x = 1")])
        new_cells = [{**self._code("x = 1"), "outputs": [{"output_type": "stream", "text": "1\n"}]}]
        new = self._nb(new_cells)
        self.assertIsNotNone(notebooks_differ_beyond_prose(old, new))


class ClassifyPureGateDecisions(unittest.TestCase):
    def test_wp_docs_only_skips(self):
        changed = [ChangedPath("M", "WPs/reports/WP50_REPORT.md")]
        result = classify(base=TRUSTWORTHY_BASE, head_ref="HEAD", raw_changed=changed, repo_root=Path("."))
        self.assertEqual(result.gate, GATE_SKIP)

    def test_prose_only_single_exercise(self):
        changed = [ChangedPath("M", "book/lite/files/exercise_03.ipynb")]
        result = classify(
            base=TRUSTWORTHY_BASE,
            head_ref="HEAD",
            raw_changed=changed,
            repo_root=Path("."),
            prose_checker=_stub_prose_checker({3: True}),
        )
        self.assertEqual(result.gate, GATE_PROSE)
        self.assertEqual(result.exercises, [3])

    def test_code_level_change_single_exercise(self):
        changed = [ChangedPath("M", "book/lite/files/exercise_03.ipynb")]
        result = classify(
            base=TRUSTWORTHY_BASE,
            head_ref="HEAD",
            raw_changed=changed,
            repo_root=Path("."),
            prose_checker=_stub_prose_checker({3: False}),
        )
        self.assertEqual(result.gate, GATE_EXERCISE)
        self.assertEqual(result.exercises, [3])

    def test_two_exercises_both_prose_take_the_union_and_stay_prose(self):
        changed = [
            ChangedPath("M", "book/lite/files/exercise_01.ipynb"),
            ChangedPath("M", "book/lite/files/exercise_04.ipynb"),
        ]
        result = classify(
            base=TRUSTWORTHY_BASE,
            head_ref="HEAD",
            raw_changed=changed,
            repo_root=Path("."),
            prose_checker=_stub_prose_checker({1: True, 4: True}),
        )
        self.assertEqual(result.gate, GATE_PROSE)
        self.assertEqual(result.exercises, [1, 4])

    def test_two_exercises_mixed_prose_and_code_escalate_to_exercise_gate(self):
        changed = [
            ChangedPath("M", "book/lite/files/exercise_01.ipynb"),
            ChangedPath("M", "book/lite/files/exercise_04.ipynb"),
        ]
        result = classify(
            base=TRUSTWORTHY_BASE,
            head_ref="HEAD",
            raw_changed=changed,
            repo_root=Path("."),
            prose_checker=_stub_prose_checker({1: True, 4: False}),
        )
        self.assertEqual(result.gate, GATE_EXERCISE)
        self.assertEqual(result.exercises, [1, 4])

    def test_shared_config_change_forces_full_gate_even_alongside_exercise_change(self):
        changed = [
            ChangedPath("M", "book/lite/files/exercise_01.ipynb"),
            ChangedPath("M", "book/config/exercise_manifest.json"),
        ]
        result = classify(
            base=TRUSTWORTHY_BASE,
            head_ref="HEAD",
            raw_changed=changed,
            repo_root=Path("."),
            prose_checker=_stub_prose_checker({1: True}),
        )
        self.assertEqual(result.gate, GATE_FULL)

    def test_unknown_path_forces_full_gate(self):
        changed = [ChangedPath("A", "some/brand/new/surface.txt")]
        result = classify(base=TRUSTWORTHY_BASE, head_ref="HEAD", raw_changed=changed, repo_root=Path("."))
        self.assertEqual(result.gate, GATE_FULL)

    def test_untrustworthy_base_forces_full_gate_regardless_of_changed_paths(self):
        changed = [ChangedPath("M", "book/lite/files/exercise_01.ipynb")]
        bad_base = BaseResolution(None, False, "missing marker")
        result = classify(base=bad_base, head_ref="HEAD", raw_changed=changed, repo_root=Path("."))
        self.assertEqual(result.gate, GATE_FULL)

    def test_rename_contributes_both_old_and_new_path(self):
        changed = [ChangedPath("R100", "scripts/generate_exercise_02_notebook_renamed.py", "scripts/generate_exercise_02_notebook.py")]
        result = classify(base=TRUSTWORTHY_BASE, head_ref="HEAD", raw_changed=changed, repo_root=Path("."))
        # The new path doesn't match the known generator-script pattern -> unknown -> full gate,
        # even though the old path alone would have been exercise-scoped. No path is dropped.
        self.assertEqual(result.gate, GATE_FULL)


class _TempGitRepo:
    """A minimal, disposable git repository for end-to-end classifier tests."""

    def __init__(self, tmp: Path):
        self.root = tmp
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")

    def _git(self, *args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
        return proc.stdout

    def write(self, relpath: str, content: str) -> None:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit_all(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD").strip()

    def branch(self, name: str, at: str) -> None:
        self._git("branch", name, at)

    def set_branch_message(self, branch: str, message: str) -> None:
        # Make an empty commit on `branch` with the given message, used to simulate
        # peaceiris/actions-gh-pages's own "deploy: <sha>" marker commit.
        self._git("checkout", "-q", branch)
        self._git("commit", "-q", "--allow-empty", "-m", message)
        self._git("checkout", "-q", "main")


def _minimal_notebook_set(repo: _TempGitRepo, n: int, *, md_text: str, code_text: str) -> None:
    nn = f"{n:02d}"
    nb_text = json.dumps(
        {
            "cells": [
                {"cell_type": "markdown", "id": "md1", "metadata": {}, "source": md_text},
                {"cell_type": "code", "id": "code1", "metadata": {}, "outputs": [], "execution_count": None, "source": code_text},
            ],
            "metadata": {"wp41": {"exercise": n, "templateVersion": 1}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )
    for relpath in (
        f"book/lite/files/exercise_{nn}.ipynb",
        f"book/lite/files/exercise_{nn}_portable.ipynb",
        f"book/downloads/chapter_{nn}/exercise_{nn}_portable.ipynb",
        f"book/chapters/chapter_{nn}/exercise_{nn}.ipynb",
        f"scripts/reference_notebooks/exercise_{nn}_reference.ipynb",
    ):
        repo.write(relpath, nb_text)


class ClassifyEndToEndRealGit(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo = _TempGitRepo(Path(self._tmpdir.name))

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_markdown_only_edit_end_to_end_is_prose_gate(self):
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 1")
        base_sha = self.repo.commit_all("base")
        _minimal_notebook_set(self.repo, 1, md_text="Hello, world", code_text="x = 1")
        head_sha = self.repo.commit_all("wording tweak")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_PROSE)
        self.assertEqual(result.exercises, [1])

    def test_code_cell_edit_end_to_end_is_exercise_gate(self):
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 1")
        base_sha = self.repo.commit_all("base")
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 2")
        head_sha = self.repo.commit_all("code change")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_EXERCISE)
        self.assertEqual(result.exercises, [1])

    def test_mc_label_change_inside_code_cell_end_to_end_is_exercise_gate(self):
        _minimal_notebook_set(self.repo, 2, md_text="Question", code_text='label = "Option A: bias"')
        base_sha = self.repo.commit_all("base")
        _minimal_notebook_set(self.repo, 2, md_text="Question", code_text='label = "Option B: variance"')
        head_sha = self.repo.commit_all("relabel the MC option")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_EXERCISE)

    def test_two_exercises_one_prose_one_code_end_to_end_unions_and_escalates(self):
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 1")
        _minimal_notebook_set(self.repo, 4, md_text="Hello", code_text="y = 1")
        base_sha = self.repo.commit_all("base")
        _minimal_notebook_set(self.repo, 1, md_text="Hello, world", code_text="x = 1")  # prose
        _minimal_notebook_set(self.repo, 4, md_text="Hello", code_text="y = 2")  # code
        head_sha = self.repo.commit_all("mixed change")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_EXERCISE)
        self.assertEqual(result.exercises, [1, 4])
        self.assertTrue(result.prose_detail[1][0])
        self.assertFalse(result.prose_detail[4][0])

    def test_shared_path_change_end_to_end_is_full_gate(self):
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 1")
        self.repo.write("book/config/exercise_manifest.json", "{}")
        base_sha = self.repo.commit_all("base")
        self.repo.write("book/config/exercise_manifest.json", '{"schemaVersion": 1}')
        head_sha = self.repo.commit_all("manifest tweak")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_FULL)

    def test_unknown_path_end_to_end_is_full_gate(self):
        self.repo.write("README.md", "hello")
        base_sha = self.repo.commit_all("base")
        self.repo.write("README.md", "hello again")
        head_sha = self.repo.commit_all("readme tweak")

        result = classify_release(self.repo.root, head_ref=head_sha, explicit_base=base_sha)
        self.assertEqual(result.gate, GATE_FULL)


class BaseResolutionRealGit(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo = _TempGitRepo(Path(self._tmpdir.name))

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_missing_gh_pages_marker_is_untrustworthy(self):
        self.repo.write("a.txt", "1")
        self.repo.commit_all("base")
        result = resolve_base(
            head_ref="HEAD", gh_pages_ref="refs/heads/gh-pages", explicit_base=None, repo_root=self.repo.root
        )
        self.assertFalse(result.trustworthy)
        self.assertIn("could not read", result.reason)

    def test_corrupt_gh_pages_marker_is_untrustworthy(self):
        self.repo.write("a.txt", "1")
        self.repo.commit_all("base")
        self.repo.branch("gh-pages", "HEAD")
        self.repo.set_branch_message("gh-pages", "not a deploy marker at all")
        result = resolve_base(
            head_ref="main", gh_pages_ref="gh-pages", explicit_base=None, repo_root=self.repo.root
        )
        self.assertFalse(result.trustworthy)
        self.assertIn("unrecognized publish marker", result.reason)

    def test_non_ancestor_marker_from_a_force_push_is_untrustworthy(self):
        self.repo.write("a.txt", "1")
        self.repo.commit_all("base")
        # An orphan commit, unrelated to main's history -- simulates a force-push/rewrite
        # where the previously-published SHA no longer descends into current history.
        self.repo._git("checkout", "-q", "--orphan", "orphaned")
        self.repo.write("a.txt", "orphaned content")
        orphan_sha = self.repo.commit_all("orphaned commit, not an ancestor of main")
        self.repo._git("checkout", "-q", "main")
        self.repo.branch("gh-pages", "HEAD")
        self.repo.set_branch_message("gh-pages", f"deploy: {orphan_sha}")

        result = resolve_base(head_ref="main", gh_pages_ref="gh-pages", explicit_base=None, repo_root=self.repo.root)
        self.assertFalse(result.trustworthy)
        self.assertIn("not an ancestor", result.reason)

    def test_valid_marker_is_trustworthy_and_is_an_ancestor(self):
        self.repo.write("a.txt", "1")
        base_sha = self.repo.commit_all("base")
        self.repo.branch("gh-pages", "HEAD")
        self.repo.set_branch_message("gh-pages", f"deploy: {base_sha}")
        self.repo.write("a.txt", "2")
        self.repo.commit_all("later commit")

        result = resolve_base(head_ref="main", gh_pages_ref="gh-pages", explicit_base=None, repo_root=self.repo.root)
        self.assertTrue(result.trustworthy)
        self.assertEqual(result.sha, base_sha)

    def test_prior_failed_push_then_a_fix_unions_both_changes_since_last_success(self):
        """A prior push's CI run failed (so gh-pages never advanced past the last success)
        but still added a shared-path file that was never published or reverted; a later
        push fixes the actual exercise content. The comparison base must stay the last
        *successful* publish, so the classifier still sees -- and escalates on -- the
        shared-path addition from the failed push, even though it is untouched by the fix
        commit itself. Comparing against the merely-previous push instead (the wrong base)
        would miss it entirely and wrongly fast-path the release."""
        _minimal_notebook_set(self.repo, 1, md_text="Hello", code_text="x = 1")
        success_sha = self.repo.commit_all("last successful publish source")
        self.repo.branch("gh-pages", "HEAD")
        self.repo.set_branch_message("gh-pages", f"deploy: {success_sha}")

        # This push's CI run is imagined to have failed -- gh-pages is never touched for it --
        # but it already added a shared-path file that is still sitting there, unpublished.
        self.repo.write("book/config/exercise_manifest.json", "{}")
        failed_sha = self.repo.commit_all("failed push: adds a shared-path file")

        # The fix only touches exercise 1's own wording; it never reverts the shared addition.
        _minimal_notebook_set(self.repo, 1, md_text="Hello, world", code_text="x = 1")
        fix_sha = self.repo.commit_all("fix: wording tweak")

        correct = classify_release(self.repo.root, head_ref=fix_sha, gh_pages_ref="gh-pages")
        self.assertEqual(correct.base.sha, success_sha)
        self.assertTrue(correct.base.trustworthy)
        changed = {p.path for p in correct.path_classes}
        self.assertIn("book/lite/files/exercise_01.ipynb", changed)
        self.assertIn("book/config/exercise_manifest.json", changed)
        self.assertEqual(
            correct.gate,
            GATE_FULL,
            "comparing against the last SUCCESSFUL publish must still catch the failed "
            "push's never-reverted shared-path change",
        )

        # Contrast: comparing against the merely-previous push (the wrong base) misses the
        # shared-path addition entirely, because it was already present and unchanged
        # between `failed_sha` and `fix_sha` -- it would wrongly fast-path as prose-only.
        wrong = classify_release(self.repo.root, head_ref=fix_sha, explicit_base=failed_sha)
        self.assertEqual(wrong.gate, GATE_PROSE)


if __name__ == "__main__":
    unittest.main()
