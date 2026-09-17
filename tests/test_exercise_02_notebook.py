"""Offline assertions for book/chapters/chapter_02/exercise_02.ipynb (Exercise 2).

WP25 merged the old Exercise 3's bias-variance/KNN material (its Sections 4-6;
Sections 1-3 -- the standalone KNN workflow and the honest-vs-invalid A/B/C
widget -- are discarded, preserved only on
archive/pre-syllabus-notebook-structure) into this notebook, renamed it
"Exercise 2: Regression and Bias-Variance Trade-Off", and moved the old
Sections 4-5 (feature-set comparison, sample size) to a trailing "## Bonus"
section. This file supersedes the pre-WP25 version of the same tests.

Standard-library ``unittest``; no network. Checks structure, the leakage guard
in the notebook code, that the age feature recipe matches the reviewed
manifest, that the executed outputs are present, that the transferred KNN
material appears exactly once and in the right place, and that no discarded
old-Exercise-3 material or FIQ/regularisation content was (re)introduced.

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
        cls.by_id = {c["id"]: c for c in cls.cells}
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    def test_valid_and_ids_are_stable_and_unique(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith(("wp11-", "wp13-", "wp14-", "wp25-")) for i in ids), ids)

    def test_h1_title(self):
        self.assertEqual(
            _src(self.cells[0]).splitlines()[0],
            "# Exercise 2: Regression and Bias-Variance Trade-Off",
        )

    def test_no_stale_exercise_ii_wording(self):
        self.assertNotIn("Exercise II", self.md)
        self.assertNotIn("Exercise II", self.code)

    def test_no_linear_regression_half_sentence_or_asaf_comparison(self):
        low = self.md.lower()
        self.assertNotIn("linear-regression half", low)
        self.assertNotIn("short on theory", low)
        self.assertNotIn("asaf", low)

    def test_opening_has_scope_prerequisites_and_in_class_at_home_framing(self):
        opening = "\n".join(_src(c) for c in self.cells[:3])
        self.assertIn("What this notebook covers", opening)
        self.assertIn("Prerequisites", opening)
        low = opening.lower()
        self.assertIn("bias-variance", low)
        self.assertIn("k-nearest neighbours", low)
        self.assertNotIn("minutes", low)
        self.assertNotRegex(opening, r"\d+\s*[-–]\s*\d+\s*min")
        self.assertNotIn("at your own pace", low)
        self.assertNotIn("moodle", low)
        self.assertIn("autism", low)
        self.assertIn("regression", low)
        self.assertNotIn("this notebook answers", low)
        # task-required in-class/at-home distinction (WP25 §8.2)
        self.assertIn("in class", low)
        self.assertIn("at home", low)

    def test_opening_appears_exactly_once(self):
        # WP25 §4: one main title, one "What this notebook covers" section --
        # never two notebooks concatenated.
        self.assertEqual(self.md.count("# Exercise 2:"), 1)
        self.assertEqual(self.md.count("What this notebook covers"), 1)
        self.assertEqual(self.md.count("Run or download this notebook"), 1)
        self.assertEqual(self.md.count("**Prerequisites:**"), 1)

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
        self.assertNotIn("chapter_01", card)

    def test_single_data_loading_sequence(self):
        # WP25 §4.1: one imports/data-loading sequence, not one per merged notebook.
        self.assertEqual(self.code.count('pd.read_csv(f"{BASE}/abide2.tsv"'), 1)
        self.assertEqual(self.md.count("## 1. Our data table"), 1)

    def test_cell_count_is_short_relative_to_exercise_one(self):
        n = len(self.cells)
        ex1 = nbformat.read(
            REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4
        )
        self.assertLess(n, len(ex1.cells))

    def test_only_hide_input_and_hide_cell_tags_are_used(self):
        seen = set()
        for c in self.cells:
            seen |= set(c.get("metadata", {}).get("tags", []))
        self.assertTrue(seen <= {"hide-input", "hide-cell"}, seen)

    def test_seven_numbered_sections_present_in_order(self):
        headings = (
            "## 1. Our data table",
            "## 2. Building one linear-regression workflow",
            "## 3. Three ways to score the same model",
            "## 4. Introducing KNN regression",
            "## 5. The classic bias–variance tradeoff",
            "## 6. How performance changes across every k",
            "## 7. Explore k yourself",
        )
        for head in headings:
            self.assertIn(head, self.md)
        positions = [self.md.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))
        # each numbered heading appears exactly once (no duplicate/pasted section)
        for head in headings:
            self.assertEqual(self.md.count(head), 1, head)
        self.assertNotIn("## 8.", self.md)

    def test_bonus_appears_after_the_knn_material_and_before_summary(self):
        knn_pos = self.md.index("## 7. Explore k yourself")
        bonus_pos = self.md.index("## Bonus")
        summary_pos = self.md.index("## In summary")
        self.assertLess(knn_pos, bonus_pos)
        self.assertLess(bonus_pos, summary_pos)
        self.assertEqual(self.md.count("## Bonus"), 1)

    def test_bonus_contains_feature_set_and_sample_size_as_subsections(self):
        bonus_pos = self.md.index("## Bonus")
        bonus_text = self.md[bonus_pos:]
        self.assertIn("### Comparing feature sets", bonus_text)
        self.assertIn("### What does sample size change?", bonus_text)
        # not top-level numbered sections anymore
        self.assertNotIn("## 4. Comparing feature sets", self.md)
        self.assertNotIn("## 5. What does sample size change?", self.md)
        # one short student-facing sentence marking them optional
        low_bonus = bonus_text.lower()
        self.assertTrue(
            "not required for the core session" in low_bonus or "optional" in low_bonus,
            bonus_text[:400],
        )

    def test_no_cross_validation_or_best_k_selection_introduced(self):
        low = (self.md + self.code).lower()
        for needle in (
            "gridsearchcv",
            "cross_val_score",
            "cross_val_predict",
            "cross-validation",
            "cross validation",
            "best k",
            "selected k",
            "optimal k",
        ):
            self.assertNotIn(needle, low)

    # -- transferred KNN material appears once, and old Ex3 §1-3 do not -----

    def test_knn_material_appears_exactly_once(self):
        for marker in (
            "K_EXAMPLE = 20",
            "knn_model = make_pipeline(StandardScaler(), KNeighborsRegressor",
            "def sorted_neighbor_targets",
            "def r2_mse_curve",
        ):
            self.assertEqual(self.code.count(marker), 1, marker)

    def test_old_exercise_3_sections_1_to_3_are_not_present(self):
        # The discarded standalone KNN workflow and the honest-vs-invalid A/B/C
        # widget (old Exercise 3 Sections 1-3) must not appear in Exercise 2.
        self.assertNotIn("One standard KNN regression workflow", self.md)
        self.assertNotIn("Correct and misleading ways to evaluate a model", self.md)
        self.assertNotIn("configs/knn_abc.json", self.md + self.code)
        self.assertNotIn("knn-abc", self.md + self.code)
        self.assertNotIn("ols_compare", self.code)

    def test_two_iframes_regression_compare_and_knn_explore_each_once(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        self.assertEqual(len(iframe_cells), 2)
        srcs = [_src(c) for c in iframe_cells]
        self.assertEqual(sum("configs/regression_compare.json" in s for s in srcs), 1)
        self.assertEqual(sum("configs/knn_explore.json" in s for s in srcs), 1)

    def test_activity_iframe_points_at_the_regression_compare_config(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        matching = [c for c in iframe_cells if "configs/regression_compare.json" in _src(c)]
        self.assertEqual(len(matching), 1)
        self.assertIn(
            'title="Interactive feature-set comparison for predicting age from brain structure"',
            _src(matching[0]),
        )

    def test_activity_iframe_points_at_the_knn_explore_config(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        matching = [c for c in iframe_cells if "configs/knn_explore.json" in _src(c)]
        self.assertEqual(len(matching), 1)
        self.assertIn(
            'title="Interactive KNN neighbour-count exploration for predicting age from brain structure"',
            _src(matching[0]),
        )

    def test_dependency_adaptation_groups_train_is_available_for_section_6(self):
        # WP25 §1: Exercise 2's own split was extended to also unpack
        # groups_train/groups_test (needed by the transferred Section 6 for
        # its internal fitting/validation stratification) without changing
        # X_train/X_test/y_train/y_test at all.
        self.assertIn(
            "X_train, X_test, y_train, y_test, groups_train, groups_test = train_test_split(",
            self.code,
        )
        self.assertIn("stratify=groups_train", self.code)

    def test_no_fiq_or_regularisation_content(self):
        # WP14 §3.1: FIQ must not be loaded or mentioned anywhere in Exercise 2.
        self.assertNotIn("FIQ", self.md)
        self.assertNotIn("FIQ", self.code)
        self.assertNotIn("FIQ", self.all_output)
        self.assertNotIn("RidgeCV", self.code)
        self.assertNotIn("LassoCV", self.code)
        self.assertNotIn("ridge", self.md.lower())
        self.assertNotIn("lasso", self.md.lower())
        self.assertNotIn("Regularisation preview", self.md)

    def test_main_target_is_age_per_manifest(self):
        self.assertEqual(MANIFEST["targets"]["age"]["role"], "main")
        self.assertIn('y = model_df.loc[has_age, "age"]', self.code)

    def test_canonical_feature_recipe_matches_the_manifest_all_eligible_bundle_360(self):
        cell = self.by_id["wp11-021"]
        src = _src(cell)
        self.assertIn("360 features", self.all_output)
        self.assertIn(
            'FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]', src
        )
        self.assertNotIn("5L", src)
        self.assertNotIn("5R", src)
        self.assertNotIn("ASYMMETRIC", src)

        import sys

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import abide_modeling_data as amd  # noqa: E402

        expected = set(amd.bundle_columns("all-eligible", ["CT"]))
        self.assertEqual(len(expected), 360)
        notebook_equivalent = {
            f"fsCT_{hemi}_{amd.raw_label_for(roi, hemi)}_ROI"
            for roi in amd.ROI_INVENTORY
            for hemi in ("L", "R")
        }
        self.assertEqual(notebook_equivalent, expected)

    def test_notebook_code_has_the_leakage_guard(self):
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', self.code)
        self.assertIn('"age" not in FEATURES', self.code)

    def test_fixed_stratified_split_and_pipeline(self):
        self.assertIn("random_state=42", self.code)
        self.assertIn("stratify=groups", self.code)
        self.assertIn("make_pipeline(StandardScaler(), LinearRegression())", self.code)
        self.assertNotIn("without turning this into a splitting lecture", self.code)
        self.assertNotIn("without turning this into a splitting lecture", self.md)

    def test_explicit_scaling_precedes_the_pipeline_shortcut(self):
        explicit_cell = self.by_id["wp14-101"]
        pipeline_cell = self.by_id["wp11-023"]
        ids = [c["id"] for c in self.cells]
        self.assertLess(ids.index("wp14-101"), ids.index("wp11-023"))
        explicit_src = _src(explicit_cell)
        self.assertIn("scaler = StandardScaler()", explicit_src)
        self.assertIn("scaler.fit_transform(X_train)", explicit_src)
        self.assertIn("scaler.transform(X_test)", explicit_src)
        self.assertNotIn("make_pipeline", explicit_src)
        pipeline_src = _src(pipeline_cell)
        self.assertIn("make_pipeline(StandardScaler(), LinearRegression())", pipeline_src)
        self.assertIn("np.allclose(y_pred, explicit_pred)", pipeline_src)
        explain = _src(self.by_id["wp14-102"])
        self.assertIn("fit_transform", explain)
        self.assertIn("transform", explain)
        self.assertIn("never be fitted on the test set", explain.replace("must never", "never"))

    def test_b_resubstitution_comment_is_on_its_own_line(self):
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
        after = self.code.split("invalid_test_fitted_model", 2)
        self.assertEqual(len(after), 3)  # defined + used once in section 3 only

    def test_age_literature_citations_present(self):
        self.assertIn("10.1038/s41586-022-04554-y", self.md)  # Bethlehem et al. 2022
        self.assertIn("10.1523/JNEUROSCI.0391-14.2014", self.md)  # Storsve et al. 2014

    def test_no_iq_literature_without_fiq_analysis(self):
        self.assertNotIn("10.1017/S0140525X07001185", self.md)  # Jung & Haier P-FIT
        self.assertNotIn("10.1093/cercor/bhl125", self.md)  # Narr et al.

    def test_sample_size_section_uses_a_small_predeclared_subset_not_the_360_recipe(self):
        self.assertIn("sizes = [40, 60, 90, 130, 200, 300, len(y_train_ss)]", self.code)
        self.assertIn("n/p", self.code)
        self.assertNotIn("clip(", self.code)
        self.assertIn('SAMPLE_SIZE_ROIS = ["4", "3a", "3b", "1", "2"]', self.code)
        self.assertIn("n_features (p) = 10", self.all_output)
        self.assertIn("360 features", self.all_output)
        self.assertIn("n_features = 360", self.all_output)

        import sys

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import abide_modeling_data as amd  # noqa: E402

        expected = {
            f"fsCT_{hemi}_{amd.raw_label_for(roi, hemi)}_ROI"
            for roi in ["4", "3a", "3b", "1", "2"]
            for hemi in ("L", "R")
        }
        self.assertEqual(len(expected), 10)
        amd.assert_brain_only(sorted(expected))

    def test_sample_size_subset_reuses_the_same_participant_split_as_section_2(self):
        self.assertIn(
            "assert np.array_equal(y_train_ss, y_train) and np.array_equal(y_test_ss, y_test)",
            self.code,
        )

    def test_no_stale_double_descent_or_underdetermined_claims(self):
        self.assertNotIn("sizes = [50, 100, 200, 300, 400, 550, len(y_train)]", self.code)
        self.assertNotIn("UNDERDETERMINED", self.all_output)
        self.assertNotIn("double descent", self.md.lower())
        self.assertNotIn("interpolation threshold", self.md.lower())

    def test_sample_size_curve_shows_a_clear_upward_trend_with_narrowing_spread(self):
        cell = self.by_id["wp11-058"]
        out = "\n".join(
            "".join(o.get("text", "")) for o in cell.get("outputs", []) if o.get("output_type") == "stream"
        )
        import re

        rows = re.findall(r"n_train\s*=\s*(\d+).*?median\s+([+-]\d+\.\d+).*?pct \[\s*([+-]\d+\.\d+),\s*([+-]\d+\.\d+)\]", out)
        self.assertGreaterEqual(len(rows), 7)
        medians = [float(r[1]) for r in rows]
        spreads = [float(r[3]) - float(r[2]) for r in rows]
        self.assertLess(medians[0], medians[-1])
        self.assertLess(spreads[-1], spreads[0])
        self.assertGreater(medians[-1], 0.15)

    def test_no_wp_script_or_report_references_in_student_text(self):
        low_md = self.md.lower()
        low_code = self.code.lower()
        for needle in ("scripts/", "wp11", "wp12", "wp13", "wp14", "wp25", ".py\n", "audit script"):
            self.assertNotIn(needle, low_md)
        self.assertNotIn("scripts/", low_code)

    def test_executed_outputs_are_present_and_teach_the_point(self):
        out = self.all_output
        self.assertIn("age available for 1004 of 1004", out)
        self.assertIn("held-out R^2 = 0.469", out)  # linear regression
        self.assertIn("held-out R^2 = 0.664", out)  # KNN, k=20
        self.assertIn("n_train = 753", out)
        self.assertIn("n_features = 360", out)
        self.assertIn("A. correct", out)
        self.assertIn("B. training score", out)
        self.assertIn("C. invalid", out)
        self.assertIn("n_features (p) = 10", out)
        self.assertIn("fitting participants (N_fit) = 564", out)
        self.assertIn("validation participants (N_val) = 189", out)
        self.assertIn("every validation prediction equals the fitting-set mean", out)

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
                self.assertNotIn(":class: note\nBefore", src)


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
