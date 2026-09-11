"""Offline assertions for book/chapters/chapter_02/exercise_02.ipynb (Exercise 2).

Standard-library ``unittest``; no network. Checks structure, the leakage guard
in the notebook code, that the age feature recipe matches the reviewed
manifest, that the executed outputs are present, and that no KNN /
bias-variance content was added.

WP12 retargeted the notebook's main example from `FIQ` to `age` (the modelling
audit found age has reliably positive out-of-sample R2 while FIQ does not, even
regularised) and added a regularisation-preview section; this file supersedes
the WP11 version of the same tests.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_02_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class Notebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    def test_valid_and_ids_are_stable_and_unique(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith(("wp11-", "wp12-")) for i in ids), ids)

    def test_h1_title(self):
        self.assertEqual(_src(self.cells[0]).splitlines()[0], "# Exercise 2: Regression")

    def test_no_stale_exercise_ii_wording(self):
        # WP12 §2: Arabic numbering throughout; no "Exercise II" anywhere.
        self.assertNotIn("Exercise II", self.md)
        self.assertNotIn("Exercise II", self.code)

    def test_no_linear_regression_half_sentence_or_asaf_comparison(self):
        low = self.md.lower()
        self.assertNotIn("linear-regression half", low)
        self.assertNotIn("short on theory", low)
        self.assertNotIn("asaf", low)

    def test_opening_has_scope_and_prerequisites_no_time_budget(self):
        opening = "\n".join(_src(c) for c in self.cells[:4])
        self.assertIn("What this notebook covers", opening)
        self.assertIn("Prerequisites", opening)
        self.assertIn("bias-variance", opening.lower())
        self.assertIn("k-nearest neighbours", opening.lower())
        low = opening.lower()
        self.assertNotIn("minutes", low)
        self.assertNotRegex(opening, r"\d+\s*[-–]\s*\d+\s*min")
        # does not re-teach the course-level Introduction / How-to material
        self.assertNotIn("at your own pace", low)
        self.assertNotIn("moodle", low)

    def test_run_or_download_block_matches_exercise_one_and_links_this_chapter(self):
        card = _src(self.cells[1])
        self.assertIn(":class: how-to-use", card)
        self.assertIn("Run or download this notebook", card)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/"
            "blob/main/book/downloads/chapter_02/exercise_02_portable.ipynb",
            card,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_02/exercise_02_portable.ipynb",
            card,
        )
        # never the other chapter's or the canonical notebook
        self.assertNotIn("chapter_01", card)

    def test_cell_count_is_short_relative_to_exercise_one(self):
        n = len(self.cells)
        self.assertGreaterEqual(n, 28)
        self.assertLessEqual(n, 50)
        ex1 = nbformat.read(
            REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4
        )
        self.assertLess(n, len(ex1.cells))

    def test_only_hide_input_and_hide_cell_tags_are_used(self):
        seen = set()
        for c in self.cells:
            seen |= set(c.get("metadata", {}).get("tags", []))
        self.assertTrue(seen <= {"hide-input", "hide-cell"}, seen)

    def test_no_knn_or_bias_variance_section(self):
        for c in self.cells:
            if c["cell_type"] != "markdown":
                continue
            for line in _src(c).splitlines():
                if line.startswith("#"):
                    low = line.lower()
                    self.assertNotIn("nearest neighbour", low)
                    self.assertNotIn("nearest neighbor", low)
                    self.assertNotIn("knn", low)
                    self.assertNotIn("bias-variance", low)
                    self.assertNotIn("bias–variance", low)
        # the words may appear only in the opening scope (WP12 §2 requires the
        # opening to name both) and the one forward-looking closing sentence
        self.assertLessEqual(self.md.lower().count("nearest neighbours"), 2)
        self.assertLessEqual(self.md.lower().count("bias-variance"), 3)

    def test_six_numbered_sections_present_in_order(self):
        headings = (
            "## 1. The modelling table",
            "## 2. One honest linear-regression workflow",
            "## 3. Three ways to score the same model",
            "## 4. Comparing feature sets",
            "## 5. Regularisation preview: age vs FIQ with the full brain",
            "## 6. What does sample size change?",
        )
        for head in headings:
            self.assertIn(head, self.md)
        positions = [self.md.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))

    def test_main_target_is_age_per_manifest(self):
        self.assertEqual(MANIFEST["targets"]["age"]["role"], "main")
        self.assertIn('y = model_df.loc[has_age, "age"]', self.code)

    def test_canonical_feature_recipe_matches_the_manifest_all_eligible_bundle(self):
        cell = next(c for c in self.cells if c["id"] == "wp11-021")
        src = _src(cell)
        self.assertIn("358 features", self.all_output)
        # the notebook computes "all eligible CT columns" itself (no repository
        # import); it must match scripts/abide_modeling_data.bundle_columns.
        import sys

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import abide_modeling_data as amd  # noqa: E402

        expected = set(amd.bundle_columns("all-eligible", ["CT"]))
        # simulate the notebook's own filter against the real atlas inventory
        import re

        pattern = re.compile(r"^fsCT_[LR]_.+_ROI$")
        all_ct_like = {
            f"fsCT_{hemi}_{roi}_ROI"
            for roi in amd.ROI_INVENTORY
            for hemi in ("L", "R")
        }
        notebook_equivalent = {
            c for c in all_ct_like if pattern.match(c) and not c.endswith(("_5L_ROI", "_5R_ROI"))
        }
        self.assertEqual(notebook_equivalent, expected)
        self.assertIn('not c.endswith(ASYMMETRIC_ROIS)', src)

    def test_notebook_code_has_the_leakage_guard(self):
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', self.code)
        self.assertIn('"age" not in FEATURES and "FIQ" not in FEATURES', self.code)

    def test_fixed_stratified_split_and_pipeline(self):
        self.assertIn("random_state=42", self.code)
        self.assertIn("stratify=groups", self.code)
        self.assertIn("make_pipeline(StandardScaler(), LinearRegression())", self.code)

    def test_b_resubstitution_comment_is_on_its_own_line(self):
        # WP12 §4.1: literal newline fix, not just a CSS/rendering change.
        self.assertIn("# B: resubstitution\ntrain_r2 = r2_score", self.code)

    def test_b_vs_c_sentence_matches_the_wp_wording(self):
        collapsed = " ".join(self.md.split())
        self.assertIn(
            "B evaluates the model on its training data, whereas A and C are "
            "evaluated on the test data. A is the only valid estimate of "
            "performance on unseen participants; C is invalid because the "
            "test data were used for fitting.",
            collapsed,
        )
        self.assertNotIn("B compares different rows", self.md)

    def test_invalid_leakage_model_is_a_clearly_named_object(self):
        self.assertIn("invalid_test_fitted_model", self.code)
        # it is never reused in a later section
        after = self.code.split("invalid_test_fitted_model", 2)
        self.assertEqual(len(after), 3)  # defined + used once in section 3 only

    def test_activity_iframe_points_at_the_regression_compare_config(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        self.assertEqual(len(iframe_cells), 1)
        src = _src(iframe_cells[0])
        self.assertIn("configs/regression_compare.json", src)
        self.assertIn(
            'title="Interactive feature-set comparison for predicting age from brain structure"',
            src,
        )

    def test_age_literature_citations_present(self):
        self.assertIn("10.1038/s41586-022-04554-y", self.md)  # Bethlehem et al. 2022
        self.assertIn("10.1523/JNEUROSCI.0391-14.2014", self.md)  # Storsve et al. 2014

    def test_iq_literature_retained_only_beside_fiq_analysis(self):
        # WP12 §6.2: IQ literature (P-FIT; Narr et al.) may remain, but only in
        # the section that actually analyses FIQ (Section 5).
        section5_start = self.md.index("## 5. Regularisation preview")
        section6_start = self.md.index("## 6. What does sample size change?")
        section5 = self.md[section5_start:section6_start]
        self.assertIn("10.1017/S0140525X07001185", section5)  # Jung & Haier P-FIT
        self.assertIn("10.1093/cercor/bhl125", section5)  # Narr et al.
        outside = self.md[:section5_start] + self.md[section6_start:]
        self.assertNotIn("10.1017/S0140525X07001185", outside)
        self.assertNotIn("10.1093/cercor/bhl125", outside)

    def test_regularisation_preview_uses_documented_alpha_grids_and_inner_cv(self):
        self.assertIn("RIDGE_ALPHAS = np.logspace(-1, 6, 29)", self.code)
        self.assertIn("LASSO_ALPHAS = np.logspace(-3, 2, 26)", self.code)
        self.assertIn("RidgeCV(alphas=RIDGE_ALPHAS, cv=INNER_CV)", self.code)
        self.assertIn("LassoCV(alphas=LASSO_ALPHAS, cv=INNER_CV", self.code)
        # never says regularisation "marginally reduces" the feature count
        self.assertNotIn("marginally reduce", self.md.lower())

    def test_no_stale_fiq_claims_outside_the_regularisation_preview_section(self):
        section5_start = self.md.index("## 5. Regularisation preview")
        section6_start = self.md.index("## 6. What does sample size change?")
        outside = self.md[:section5_start] + self.md[section6_start:]
        # FIQ may be *named* (e.g. as the harder target to come), but no stale
        # performance claim about it may sit outside its own section.
        self.assertNotIn("FIQ carries", outside)
        self.assertNotIn("FIQ predicts", outside)

    def test_learning_curve_on_the_same_target_and_recipe(self):
        self.assertIn("sizes = [370, 470, 570, 670, len(y_train)]", self.code)
        self.assertIn("n/p = {sizes[0]/X.shape[1]:.2f}", self.code)

    def test_executed_outputs_are_present_and_teach_the_point(self):
        out = self.all_output
        self.assertIn("age available for 1004 of 1004", out)
        self.assertIn("held-out R^2 = 0.", out)  # positive held-out R^2 for age
        self.assertIn("n_train = 753", out)
        self.assertIn("n_features (p) = 358", out)
        # the A/B/C leakage table is present with all three rows
        self.assertIn("A. correct", out)
        self.assertIn("B. training score", out)
        self.assertIn("C. invalid", out)
        # the regularisation preview ran for both targets
        self.assertIn("1432 features across 4 measures", out)
        self.assertIn("age: n_train=753", out)
        self.assertIn("FIQ: n_train=681", out)

    def test_no_execution_errors_or_stderr_committed(self):
        for c in self.cells:
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error", _src(c)[:120])
                if o.get("output_type") == "stream":
                    self.assertNotEqual(o.get("name"), "stderr", _src(c)[:120])


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
