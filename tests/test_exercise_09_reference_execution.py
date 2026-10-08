"""Executes the completed Exercise 9 reference notebook and checks its
numbers against directly-verified results -- verified directly against
book/lite/files/data/abide_age_brain.csv using the same train_test_split
convention every other exercise uses (test_size=0.25, random_state=42,
stratify=group); see the generator's module docstring and the WP51 report
for the full reasoning and every verification command. Modeled on
tests/test_exercise_08_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45/WP46/WP47 documented: this notebook's native
widgets use an ipywidgets ``Output()`` widget as a context manager, which
hangs nbclient's real ZMQ kernel with no frontend attached to acknowledge
the widget comm handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_reference_execution.py'
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import os
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_09_reference.ipynb"
STUDENT_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_09.ipynb"

_TOP_LEVEL_AWAIT = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT


async def _run_cell(source: str, ns: dict, name: str) -> None:
    code = compile(source, name, "exec", flags=_TOP_LEVEL_AWAIT)
    result = eval(code, ns)
    if inspect.iscoroutine(result):
        await result


async def _execute_notebook(nb) -> tuple[dict, list[tuple[int, str, str]]]:
    ns: dict = {}
    errors: list[tuple[int, str, str]] = []
    for i, cell in enumerate(nb.cells):
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        try:
            await _run_cell(source, ns, f"cell_{i}")
        except Exception as exc:  # noqa: BLE001 -- collected, not swallowed
            errors.append((i, cell.get("id"), f"{type(exc).__name__}: {exc}"))
    return ns, errors


def _execute(path: Path) -> tuple[dict, list[tuple[int, str, str]]]:
    import matplotlib

    matplotlib.use("Agg")  # headless: no display, no GUI event loop
    old_cwd = os.getcwd()
    os.chdir(REPO_ROOT / "book" / "lite" / "files")
    try:
        nb = nbformat.read(path, as_version=4)
        return asyncio.run(_execute_notebook(nb))
    finally:
        os.chdir(old_cwd)


class ReferenceExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns, cls.errors = _execute(REFERENCE_PATH)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_participant_and_predictor_counts(self):
        self.assertEqual(len(self.ns["df"]), 1004)
        self.assertEqual(len(self.ns["FEATURES"]), 360)
        self.assertEqual(self.ns["X_train"].shape, (753, 360))
        self.assertEqual(self.ns["X_val"].shape, (251, 360))

    def test_pcr_results_match_directly_verified_numbers(self):
        by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pcr_results"]}
        expected = {2: 51.138, 5: 44.488, 10: 34.808, 20: 31.943, 50: 29.610}
        for n, exp in expected.items():
            self.assertAlmostEqual(by_n[n], exp, delta=0.05)
        # monotonically improving across this grid, as directly verified
        ordered = [by_n[n] for n in sorted(by_n)]
        self.assertTrue(all(a >= b - 1e-6 for a, b in zip(ordered, ordered[1:])))

    def test_pls_results_match_directly_verified_numbers_and_peak_at_5(self):
        by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pls_results"]}
        expected = {2: 39.935, 5: 29.658, 10: 38.797, 20: 48.906, 50: 49.555}
        for n, exp in expected.items():
            self.assertAlmostEqual(by_n[n], exp, delta=0.05)
        self.assertEqual(min(by_n, key=by_n.get), 5)

    def test_pls_beats_pcr_at_low_component_counts_but_not_at_pcrs_own_best(self):
        pcr_by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pcr_results"]}
        pls_by_n = {r["n_components"]: r["val_mse"] for r in self.ns["pls_results"]}
        self.assertLess(pls_by_n[5], pcr_by_n[5])
        self.assertGreater(min(pls_by_n.values()), min(pcr_by_n.values()) - 0.2)

    def test_svr_subset_results_match_directly_verified_numbers(self):
        results = {(r["kernel"], r["C"]): r["val_mse"] for r in self.ns["svr_results"]}
        self.assertAlmostEqual(results[("linear", 1)], 94.996, delta=0.1)
        self.assertAlmostEqual(results[("rbf", 1)], 60.886, delta=0.1)
        self.assertAlmostEqual(results[("rbf", 100)], 29.535, delta=0.1)
        self.assertEqual(len(self.ns["X_train_svr_subset"]), 300)

    def test_svr_subset_is_a_strict_subset_of_the_training_partition(self):
        self.assertLess(len(self.ns["X_train_svr_subset"]), len(self.ns["X_train"]))

    def test_ridge_and_kernel_ridge_match_directly_verified_numbers(self):
        self.assertAlmostEqual(self.ns["ridge_result"]["val_mse"], 31.813, delta=0.01)
        self.assertAlmostEqual(self.ns["kernel_ridge_result"]["val_mse"], 21.924, delta=0.01)

    def test_kernel_ridge_beats_plain_ridge_on_this_split(self):
        self.assertLess(self.ns["kernel_ridge_result"]["val_mse"], self.ns["ridge_result"]["val_mse"])

    def test_optional_lasso_challenge_runs_and_shows_sparsity_moves_to_transformed_features(self):
        self.assertEqual(self.ns["plain_lasso_nnz"], 163)
        self.assertEqual(self.ns["rbf_lasso_nnz"], 15)
        self.assertLessEqual(self.ns["rbf_lasso_nnz"], 200)

    def test_svc_boundary_demo_matches_directly_verified_numbers(self):
        self.assertAlmostEqual(self.ns["_demo_pipe"].score(self.ns["_demo_X"][self.ns["_demo_train"]], self.ns["_demo_y"][self.ns["_demo_train"]]), 0.949, delta=0.01)
        self.assertAlmostEqual(self.ns["_demo_pipe"].score(self.ns["_demo_X"][self.ns["_demo_val"]], self.ns["_demo_y"][self.ns["_demo_val"]]), 0.952, delta=0.01)

    def test_rbf_sampler_logistic_beats_plain_logistic_on_the_nonlinear_synthetic_set(self):
        self.assertAlmostEqual(self.ns["plain_logistic_val_acc"], 0.476, delta=0.01)
        self.assertAlmostEqual(self.ns["rbf_logistic_val_acc"], 0.952, delta=0.01)

    def test_single_split_never_reused_as_a_second_locked_test_set(self):
        # WP51 "Load and split": exactly one split, reused throughout --
        # never recombined into a second held-out layer.
        self.assertNotIn("X_test", self.ns)
        self.assertNotIn("y_test", self.ns)


class StudentTemplateNoCascade(unittest.TestCase):
    """The untouched template must execute cleanly end to end: every blank's
    own check cell degrades to its own guidance, with zero exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.ns, cls.errors = _execute(STUDENT_PATH)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_every_required_blank_check_cell_shows_not_complete_yet(self):
        import io
        from contextlib import redirect_stdout

        nb = nbformat.read(STUDENT_PATH, as_version=4)
        for check_id in (
            "wp51-205-pcr-check",
            "wp51-305-pls-check",
            "wp51-412-svr-check",
            "wp51-506-kernelridge-check",
        ):
            cell = next(c for c in nb.cells if c.get("id") == check_id)
            out = io.StringIO()
            with redirect_stdout(out):
                exec(compile(cell["source"], check_id, "exec"), dict(self.ns))
            self.assertIn("Not complete yet", out.getvalue(), check_id)

    def test_optional_challenge_check_cell_never_blocks_on_being_skipped(self):
        import io
        from contextlib import redirect_stdout

        nb = nbformat.read(STUDENT_PATH, as_version=4)
        cell = next(c for c in nb.cells if c.get("id") == "wp51-512-lasso-check")
        out = io.StringIO()
        with redirect_stdout(out):
            exec(compile(cell["source"], "wp51-512-lasso-check", "exec"), dict(self.ns))
        self.assertIn("Optional", out.getvalue())

    def test_supplied_activities_and_demos_run_independently_of_every_blank(self):
        # The native widgets, the compact SVC demo, and the RBFSampler
        # demos are all supplied (not blanks) and must work even though
        # every blank above them was left untouched.
        self.assertIn("_demo_pipe", self.ns)
        self.assertIn("plain_logistic_val_acc", self.ns)
        self.assertIn("rbf_logistic_val_acc", self.ns)
        self.assertEqual(len(self.ns["X_train"]), 753)
        self.assertEqual(len(self.ns["X_val"]), 251)

    def test_comparison_table_reports_missing_results_without_raising(self):
        self.assertNotIn("pcr_results", self.ns)
        self.assertNotIn("ridge_result", self.ns)
        self.assertIn("_missing", self.ns)
        self.assertGreaterEqual(len(self.ns["_missing"]), 4)


if __name__ == "__main__":
    unittest.main()
