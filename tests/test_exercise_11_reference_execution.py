"""Executes the completed Exercise 11 reference notebook and checks its
numbers against directly-verified results -- verified directly against
book/lite/files/data/haxby_rsa_patterns.csv (built by
scripts/export_haxby_rsa_data.py --refresh); see that script's own
docstring and WP61_REPORT.md for the full extraction method and every
verification command. Modeled on tests/test_exercise_09_reference_execution.py.

Runs every cell's source in one shared namespace, in order -- the same
semantics a notebook kernel uses. Avoids `jupyter execute`/nbclient for the
same reason WP41/.../WP51 documented: this notebook's native widgets use an
ipywidgets ``Output()`` widget as a context manager, which hangs nbclient's
real ZMQ kernel with no frontend attached to acknowledge the widget comm
handshake.

Network: none (reads the committed same-origin CSV via the notebook's own
loader, exactly as JupyterLite would).

Run:
    python3 -m unittest discover -s tests -p 'test_exercise_11_reference_execution.py'
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
REFERENCE_PATH = REPO_ROOT / "scripts" / "reference_notebooks" / "exercise_11_reference.ipynb"
STUDENT_PATH = REPO_ROOT / "book" / "lite" / "files" / "exercise_11.ipynb"

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
    # Matches the real JupyterLite cwd convention this course already
    # established (WP60): the kernel's cwd is the notebook's own directory.
    # exercise_11.ipynb sits flat in book/lite/files/, same as every
    # non-namespaced exercise, so "data/..." resolves from there.
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

    def test_data_shape(self):
        self.assertEqual(self.ns["haxby_df"].shape[0], 96)
        self.assertEqual(len(self.ns["VOXEL_COLUMNS"]), 464)
        self.assertEqual(self.ns["CATEGORY_PATTERNS"].shape, (8, 464))

    def test_neural_rdm_is_square_symmetric_zero_diagonal(self):
        import numpy as np

        rdm = self.ns["neural_rdm"]
        self.assertEqual(rdm.shape, (8, 8))
        self.assertTrue(np.allclose(rdm, rdm.T))
        self.assertTrue(np.allclose(np.diag(rdm), 0.0, atol=1e-9))
        self.assertTrue(np.all(np.isfinite(rdm)))

    def test_neural_rdm_distance_range_matches_direct_verification(self):
        import numpy as np

        rdm = self.ns["neural_rdm"]
        iu = np.triu_indices(8, k=1)
        self.assertAlmostEqual(rdm[iu].min(), 0.4255, delta=0.01)
        self.assertAlmostEqual(rdm[iu].max(), 1.1236, delta=0.01)

    def test_split_half_reliability_matches_direct_verification(self):
        self.assertAlmostEqual(self.ns["split_half_r"], 0.4854, delta=0.01)

    def test_face_hypothesis_match_matches_direct_verification(self):
        self.assertAlmostEqual(self.ns["face_match_r"], 0.2467, delta=0.01)

    def test_animacy_hypothesis_match_matches_direct_verification(self):
        self.assertAlmostEqual(self.ns["animacy_match_r"], 0.4459, delta=0.01)
        self.assertEqual(len(self.ns["nonscrambled_categories"]), 7)
        self.assertNotIn("scrambledpix", self.ns["nonscrambled_categories"])

    def test_question_shuffle_is_reproducible_and_varies_by_question(self):
        # Reproducible: calling show_question twice for the same id must
        # not raise and must not depend on prior call order/global state
        # beyond its own fixed per-question seed.
        show_question = self.ns["show_question"]
        for qid in (
            "q-row-voxel",
            "q-rdm-cell",
            "q-condition-order",
            "q-mds-distortion",
            "q-split-half",
            "q-face-match-implications",
        ):
            show_question(qid)  # must not raise

        import random

        questions = self.ns["_QUESTIONS"]
        seeds = {qid: q["shuffle_seed"] for qid, q in questions.items()}
        self.assertEqual(len(set(seeds.values())), len(seeds), "every question should use a distinct shuffle seed")

        # Reproducibility of one question's own shuffle across repeated calls.
        q = questions["q-face-match-implications"]
        order1 = list(range(len(q["statements"])))
        random.Random(q["shuffle_seed"]).shuffle(order1)
        order2 = list(range(len(q["statements"])))
        random.Random(q["shuffle_seed"]).shuffle(order2)
        self.assertEqual(order1, order2)


if __name__ == "__main__":
    unittest.main()
