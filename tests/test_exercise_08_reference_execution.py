"""Executes the completed Exercise 8 reference notebook and checks its
numbers against approved results -- verified directly against
book/lite/files/data/abide_age_brain.csv and the new
book/lite/files/data/abide_age_brain_demographics.csv sidecar (see the
generator's module docstring and the WP47 report for the full reasoning: PCA
and K-means are invariant to column order, so Sections 1-4 reproduce
scripts/pca_kmeans_audit_result.json's network-sourced numbers almost
exactly; Section 5's PCA+KNN selection differs slightly at a near-tied CV
margin, honestly re-verified here, not copied from that audit), modeled on
tests/test_exercise_07_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/WP44/WP45/WP46 documented: this notebook's native widget
uses an ipywidgets ``Output()`` widget as a context manager, which hangs
nbclient's real ZMQ kernel with no frontend attached to acknowledge the
widget comm handshake.

Network: none (reads the committed same-origin CSVs via the notebook's own
loaders, exactly as JupyterLite would).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_08_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_08_reference.ipynb"
STUDENT_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_08.ipynb"

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
        self.assertEqual(len(self.ns["demographics"]), 1004)

    def test_demographics_never_feed_pca_or_kmeans(self):
        pca_cell = next(
            c for c in nbformat.read(REFERENCE_PATH, as_version=4).cells if c.get("id") == "wp47-204-pca-blank"
        )
        self.assertNotIn("demographics", pca_cell["source"])
        self.assertNotIn("sex", pca_cell["source"])
        self.assertNotIn("site", pca_cell["source"])

    def test_pca_matches_the_audit_almost_exactly(self):
        # Order-invariant (see the generator's module docstring): matches
        # scripts/pca_kmeans_audit_result.json (computed from the network
        # source) to 4 decimal places.
        pca_explore = self.ns["pca_explore"]
        evr = pca_explore.explained_variance_ratio_
        cum = evr.cumsum()
        self.assertAlmostEqual(evr[0], 0.361414, places=4)
        self.assertAlmostEqual(cum[1], 0.420024, places=3)
        self.assertAlmostEqual(cum[9], 0.543078, places=3)
        self.assertAlmostEqual(cum[49], 0.701822, places=3)

    def test_pca_shapes(self):
        self.assertEqual(self.ns["Xs"].shape, (1004, 360))
        self.assertEqual(self.ns["X_pca"].shape, (1004, 50))

    def test_kmeans_inertia_decreases_and_silhouette_matches_the_audit(self):
        results = {r["k"]: r for r in self.ns["kmeans_results"]}
        self.assertEqual(set(results), set(self.ns["K_CANDIDATES"]))
        inertias = [results[k]["inertia"] for k in sorted(results)]
        self.assertTrue(all(a >= b - 1e-6 for a, b in zip(inertias, inertias[1:])))
        self.assertIsNone(results[1]["silhouette"])
        # k=3's silhouette is an exact match to the legacy audit's demo
        # k=3 silhouette (0.265) -- order-invariant, verified directly.
        self.assertAlmostEqual(results[3]["silhouette"], 0.265, places=2)

    def test_activity_uses_the_students_own_x_pca_when_available(self):
        self.assertIn("your own completed PCA", "".join(self.ns.get("_activity_source_note", "")))

    def test_pipeline_selects_a_genuine_configuration_and_differs_honestly_from_the_legacy_audit(self):
        # This notebook's own data source selects (n_components=20, k=5),
        # not the legacy audit's (n_components=20, k=10) -- see the
        # generator's module docstring for the documented, honestly-computed
        # divergence at a near-tied cross-validation margin.
        self.assertEqual(self.ns["selected_n"], 20)
        self.assertEqual(self.ns["selected_k"], 5)
        self.assertAlmostEqual(self.ns["pca_knn_test_mse"], 19.1311, places=1)
        self.assertAlmostEqual(self.ns["pca_knn_test_r2"], 0.795060, places=2)

    def test_raw_feature_knn_baseline_matches_the_legacy_audit_exactly(self):
        # Order-invariant: Euclidean distance over all 360 features does not
        # depend on column order, unlike a tree's greedy split search.
        self.assertEqual(self.ns["selected_raw_k"], 5)
        self.assertAlmostEqual(self.ns["raw_knn_test_mse"], 32.0452, places=3)
        self.assertAlmostEqual(self.ns["raw_knn_test_r2"], 0.656718, places=5)

    def test_pca_knn_beats_raw_knn_on_this_split(self):
        self.assertLess(self.ns["pca_knn_test_mse"], self.ns["raw_knn_test_mse"])

    def test_pipeline_never_lets_section_2s_full_data_pca_touch_the_held_out_test(self):
        cell = next(
            c for c in nbformat.read(REFERENCE_PATH, as_version=4).cells if c.get("id") == "wp47-506-pipeline"
        )
        source = cell["source"]
        self.assertNotIn("pca_explore", source)
        self.assertIn('PCA(n_components=n, random_state=0)', source)


class StudentTemplateNoCascade(unittest.TestCase):
    """The untouched template must execute cleanly end to end: every blank's
    own check cell degrades to its own guidance, with zero exceptions."""

    @classmethod
    def setUpClass(cls):
        cls.ns, cls.errors = _execute(STUDENT_PATH)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_every_blank_check_cell_shows_not_complete_yet(self):
        import io
        from contextlib import redirect_stdout

        nb = nbformat.read(STUDENT_PATH, as_version=4)
        for check_id in (
            "wp47-205-pca-check",
            "wp47-208-variance-check",
            "wp47-211-scatter-check",
            "wp47-216-loadings-check",
            "wp47-306-kmeans-check",
        ):
            cell = next(c for c in nb.cells if c.get("id") == check_id)
            out = io.StringIO()
            with redirect_stdout(out):
                exec(compile(cell["source"], check_id, "exec"), dict(self.ns))
            self.assertIn("Not complete yet", out.getvalue(), check_id)

    def test_section_4_and_5_still_run_independently_of_the_students_blanks(self):
        self.assertIn("independently computed PCA", "".join(self.ns.get("_activity_source_note", "")))
        self.assertEqual(len(self.ns["y_train"]), 753)
        self.assertEqual(len(self.ns["y_test"]), 251)
        self.assertIn("selected_n", self.ns)


if __name__ == "__main__":
    unittest.main()
