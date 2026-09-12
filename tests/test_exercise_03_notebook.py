"""Offline assertions for book/chapters/chapter_03/exercise_03.ipynb (Exercise 3).

Standard-library ``unittest``; no network. Checks structure, the leakage guard
and locked-split reuse in the notebook code, that the executable
cross-validation cell reproduces the committed audit's selected k, that the
invalid/demo models stay isolated, and that classification is only ever
mentioned as a forward-looking pointer.

WP14 corrected the canonical feature recipe from 358 to 360 cortical parcels,
replaced the internal-audit-script comment with executable training-only
cross-validation, and replaced the static Section 3 A/B/C table + k=1 demo
with one interactive activity. This file supersedes the WP13 version.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_03_notebook.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
AUDIT_RESULT = json.loads((REPO_ROOT / "scripts" / "knn_model_audit_result.json").read_text())


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class Notebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.by_id = {c["id"]: c for c in cls.cells}
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    def test_valid_and_ids_are_stable_and_unique(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith(("wp13-", "wp14-")) for i in ids), ids)

    def test_h1_title(self):
        self.assertEqual(
            _src(self.cells[0]).splitlines()[0],
            "# Exercise 3: KNN and the Bias–Variance Tradeoff",
        )

    def test_run_or_download_block_matches_the_pattern_and_links_this_chapter(self):
        card = _src(self.cells[1])
        self.assertIn(":class: how-to-use", card)
        self.assertIn("Run or download this notebook", card)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/"
            "blob/main/book/downloads/chapter_03/exercise_03_portable.ipynb",
            card,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_03/exercise_03_portable.ipynb",
            card,
        )
        self.assertNotIn("chapter_01", card)
        self.assertNotIn("chapter_02", card)

    def test_opening_has_scope_and_prerequisites_no_time_budget(self):
        opening = "\n".join(_src(c) for c in self.cells[:3])
        self.assertIn("What this notebook covers", opening)
        self.assertIn("Prerequisites", opening)
        low = " ".join(opening.lower().split())
        self.assertIn("k-nearest neighbours (knn)", low)
        self.assertIn("bias–variance", low)
        self.assertIn("classification", low)
        self.assertNotIn("minutes", low)
        self.assertNotRegex(opening, r"\d+\s*[-–]\s*\d+\s*min")

    def test_cell_count_is_short_relative_to_exercise_one(self):
        n = len(self.cells)
        self.assertGreaterEqual(n, 28)
        self.assertLessEqual(n, 45)
        ex1 = nbformat.read(
            REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4
        )
        self.assertLess(n, len(ex1.cells))

    def test_only_hide_input_and_hide_cell_tags_are_used(self):
        seen = set()
        for c in self.cells:
            seen |= set(c.get("metadata", {}).get("tags", []))
        self.assertTrue(seen <= {"hide-input", "hide-cell"}, seen)

    def test_six_numbered_sections_present_in_order(self):
        headings = (
            "## 1. The modelling table",
            "## 2. One standard KNN regression workflow",
            "## 3. Honest evaluation versus invalid alternatives",
            "## 4. The classic bias–variance tradeoff",
            "## 5. From k = 1 to every participant: an empirical curve",
            "## 6. Explore k yourself",
        )
        for head in headings:
            self.assertIn(head, self.md)
        positions = [self.md.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))

    def test_classification_mentioned_only_as_forward_looking(self):
        for c in self.cells:
            if c["cell_type"] != "markdown":
                continue
            for line in _src(c).splitlines():
                if line.startswith("#"):
                    self.assertNotIn("classification", line.lower())
        self.assertLessEqual(self.md.lower().count("classification"), 3)

    def test_uses_k_not_n_for_neighbour_count(self):
        self.assertIn("K_SELECTED = int(cv_results", self.code)
        self.assertIn("n_neighbors=K_SELECTED", self.code)
        low = " ".join(self.md.lower().split())
        self.assertIn("the number of neighbours", low)

    def test_canonical_feature_recipe_matches_exercise_2_and_the_manifest_360(self):
        cell = self.by_id["wp13-021"]
        src = _src(cell)
        self.assertIn("360 features", self.all_output)
        self.assertIn(
            'FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]', src
        )
        self.assertNotIn("5L", src)
        self.assertNotIn("5R", src)
        # exact same code as Exercise 2's Section 2 recipe cell (wp11-021)
        ex2 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb", as_version=4)
        ex2_cell = next(c for c in ex2.cells if c["id"] == "wp11-021")
        self.assertEqual(
            [ln for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#")],
            [ln for ln in _src(ex2_cell).splitlines() if ln.strip() and not ln.strip().startswith("#")],
        )

    def test_locked_split_matches_exercise_2(self):
        self.assertIn("test_size=0.25, random_state=42, stratify=groups", self.code)
        self.assertIn("n_train = 753", self.all_output)
        self.assertIn("n_test = 251", self.all_output)
        self.assertIn("n_features = 360", self.all_output)

    def test_notebook_code_has_the_leakage_guard(self):
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', self.code)
        self.assertIn('"age" not in FEATURES', self.code)

    def test_k_arises_from_executable_training_only_cv_not_a_hardcoded_number(self):
        # WP14 §4.3: the notebook's chosen k must come from executable code.
        cv_cell = self.by_id["wp14-211"]
        src = _src(cv_cell)
        self.assertIn("cross_val_score", src)
        self.assertIn("KFold(n_splits=5, shuffle=True, random_state=0)", src)
        self.assertIn("X_train, y_train", src)
        self.assertNotIn("X_test", src)
        self.assertNotIn("y_test", src)
        self.assertIn('idxmax()', src)
        # never a bare literal "K_SELECTED = 15" anywhere in the notebook
        self.assertNotIn("K_SELECTED = 15", self.code)
        self.assertIn("selected k = 15", self.all_output)

    def test_executable_cv_reproduces_the_committed_audit_selected_k(self):
        canonical = next(
            c
            for c in AUDIT_RESULT["candidates"]
            if c["bundle"] == "all-eligible" and c["measures"] == ["CT"]
        )
        self.assertEqual(canonical["selected_k"], 15)
        self.assertIn("selected k = 15", self.all_output)

    def test_scaling_is_fit_inside_the_pipeline_only(self):
        for line in self.code.splitlines():
            if "KNeighborsRegressor(" in line and "make_pipeline" not in line:
                self.assertNotIn("KNeighborsRegressor(n_neighbors", line, line)

    def test_no_wp_script_or_report_references_in_student_text(self):
        # WP14 §4.2: no student-facing scripts/, WP, or report reference.
        low_md = self.md.lower()
        low_code = self.code.lower()
        for needle in ("scripts/", "wp11", "wp12", "wp13", "wp14", "audit script", "audit_result"):
            self.assertNotIn(needle, low_md)
            self.assertNotIn(needle, low_code)

    def test_no_static_abc_table_or_k1_demo_remains(self):
        # WP14 §4.4: both static examples are gone.
        self.assertNotIn("invalid_test_fitted_model", self.code)
        self.assertNotIn("knn_demo_k1", self.code)
        self.assertNotIn("DELIBERATELY EXTREME", self.code)

    def test_section_3_uses_the_interactive_abc_activity(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        srcs = [_src(c) for c in iframe_cells]
        self.assertTrue(any("configs/knn_abc.json" in s for s in srcs))
        self.assertTrue(
            any('title="Interactive honest-vs-invalid KNN evaluation' in s for s in srcs)
        )

    def test_k1_endpoint_explanation_present_for_the_interactive_activity(self):
        low = self.md.lower()
        self.assertIn("k = 1, b and c are exactly perfect", low.replace("`", ""))
        self.assertIn("a at `k = 1` is not perfect", self.md.lower().replace("k=1", "k = 1") or low, )

    # -- bias-variance conceptual graph (section 4) --------------------------

    def test_conceptual_graph_is_explicitly_labelled_not_estimated(self):
        cell = self.by_id["wp13-041"]
        src = _src(cell)
        self.assertIn("CONCEPTUAL", src)
        self.assertIn("not estimated from ABIDE data", self.md + src)

    def test_bias_variance_decomposition_equation_present(self):
        self.assertIn("Bias", self.md)
        self.assertIn("Var", self.md)
        self.assertIn("sigma^2", self.md.replace("\\sigma^2", "sigma^2"))

    # -- empirical curve (section 5) -----------------------------------------

    def test_dev_split_is_independent_of_the_outer_test_set(self):
        section5 = self._section_code("wp13-050", "wp13-060")
        self.assertNotIn("X_test", section5)
        self.assertNotIn("y_test", section5)
        self.assertIn("X_train", section5)
        self.assertIn("y_train", section5)

    def test_n_fit_endpoint_is_verified_in_code(self):
        cell = self.by_id["wp13-053"]
        src = _src(cell)
        self.assertIn("assert np.allclose(pred_val_at_k_nfit, y_fit.mean())", src)
        self.assertIn(
            "k = N_fit: every validation prediction equals the fitting-set mean", self.all_output
        )

    def test_curve_never_retunes_the_locked_model(self):
        self.assertIn("never retunes", self.md.lower())
        self.assertIn("outer test", self.md.lower())

    def test_does_not_call_the_empirical_curve_a_direct_measurement(self):
        low = self.md.lower()
        self.assertIn("consistent with", low)
        self.assertNotIn("directly measures bias", low)
        self.assertNotIn("proves the bias", low)

    # -- interactive activity (section 6) ------------------------------------

    def test_activity_iframe_points_at_the_knn_explore_config(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        matching = [c for c in iframe_cells if "configs/knn_explore.json" in _src(c)]
        self.assertEqual(len(matching), 1)
        src = _src(matching[0])
        self.assertIn(
            'title="Interactive KNN neighbour-count exploration for predicting age from brain structure"',
            src,
        )

    def test_k_complexity_relationship_stated_prominently(self):
        low = self.md.lower()
        self.assertIn("lower variance but higher bias", low)
        self.assertIn("lower bias but higher variance", low)
        self.assertIn("general tendency of knn", low)

    def test_no_duplicate_reflection_prompt_block(self):
        # WP14 §4.7: only one Think-first block near Section 6 (the widget's
        # own config-driven "Reflect" list is not a second notebook block).
        section6 = self._section_code_md("wp13-060", None)
        self.assertEqual(section6.count("Think first"), 0)

    # -- outputs / cleanliness -------------------------------------------------

    def test_executed_outputs_are_present_and_teach_the_point(self):
        out = self.all_output
        self.assertIn("age available for 1004 of 1004", out)
        self.assertIn("held-out R^2 = 0.649", out)
        self.assertIn("N_fit = 564   N_val = 189", out)
        self.assertIn("validation-optimal", out)
        self.assertIn("Exercise 2 linear regression   held-out R^2 = 0.469", out)

    def test_no_execution_errors_or_stderr_committed(self):
        for c in self.cells:
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error", _src(c)[:120])
                if o.get("output_type") == "stream":
                    self.assertNotEqual(o.get("name"), "stderr", _src(c)[:120])

    def test_every_think_first_block_uses_the_shared_blue_class(self):
        for c in self.cells:
            if c["cell_type"] != "markdown":
                continue
            src = _src(c)
            if "Think first" in src:
                self.assertIn(":class: think-first", src, src[:120])

    # -- helpers ---------------------------------------------------------------

    def _section_code(self, start_id: str, end_id: str) -> str:
        ids = [c["id"] for c in self.cells]
        i, j = ids.index(start_id), ids.index(end_id)
        return "\n\n".join(_src(c) for c in self.cells[i:j] if c["cell_type"] == "code")

    def _section_code_md(self, start_id: str, end_id: str | None) -> str:
        ids = [c["id"] for c in self.cells]
        i = ids.index(start_id)
        j = ids.index(end_id) if end_id else len(self.cells)
        return "\n\n".join(_src(c) for c in self.cells[i:j] if c["cell_type"] == "markdown")


def _collect_output(nb) -> str:
    parts = []
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                parts.append(out.get("text", ""))
            elif "data" in out:
                plain = out["data"].get("text/plain", "")
                parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
