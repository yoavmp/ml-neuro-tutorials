"""Offline assertions for book/chapters/chapter_05/exercise_05.ipynb (Exercise 5).

WP28 replaced the 3-line Exercise 5 placeholder with a notebook on
regularization and feature selection, moving "Compare Two Feature Sets" (and
its regression-compare activity) here from Exercise 2's Bonus section, and
adding a new Ridge/Lasso "Shrink the Coefficients" activity. This file checks
structure, the leakage guard, that feature selection stays training-only,
that Ridge/Lasso are described correctly, that no stability/frequency
material was introduced, and that the closing section stays a single open
question rather than a second methods table.

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_05_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_05" / "exercise_05.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_05" / "exercise_05_portable.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")

SECTION_TITLES = [
    "## 1. Why Select Features?",
    "## 2. Compare Predefined Feature Sets",
    "## 3. Select Features Using the Data",
    "## 4. Ridge and Lasso Regression",
    "## 5. Explore Regularization",
    "## 6. A Complete Regularized Regression Pipeline",
    "## 7. Other Feature-Selection Methods",
    "## 8. How Do We Choose a Feature-Selection Method?",
]

STABILITY_NEEDLES = (
    "selection frequency",
    "feature-selection stability",
    "are the selected features stable",
    "folds selected",
    "stability heatmap",
    "selection-frequency heatmap",
)


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


def _norm_ws(text: str) -> str:
    return " ".join(text.split())


def _index_of_cell_starting_with(cells, prefix: str) -> int:
    for i, c in enumerate(cells):
        if c["cell_type"] == "markdown" and _src(c).lstrip().startswith(prefix):
            return i
    raise AssertionError(f"no cell starts with {prefix!r}")


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


class Notebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.by_id = {c["id"]: c for c in cls.cells}
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    # -- basic structure --------------------------------------------------

    def test_is_a_notebook_not_a_placeholder(self):
        self.assertEqual(NB_PATH.suffix, ".ipynb")
        self.assertFalse((REPO_ROOT / "book" / "chapters" / "chapter_05" / "exercise_05.md").exists())
        self.assertGreater(len(self.cells), 20)

    def test_valid_and_ids_are_unique(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.cells]
        self.assertEqual(len(ids), len(set(ids)))

    def test_h1_title(self):
        self.assertEqual(
            _src(self.cells[0]).splitlines()[0],
            "# Exercise 5: Regularization and Feature Selection",
        )

    def test_run_or_download_block_links_this_chapters_portable_notebook(self):
        opening = self.md[: self.md.index("## 1.")]
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/"
            "book/downloads/chapter_05/exercise_05_portable.ipynb",
            opening,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_05/exercise_05_portable.ipynb",
            opening,
        )

    def test_launch_buttons_js_maps_chapter_5_to_its_portable_notebook(self):
        self.assertIn(
            '"chapters/chapter_05/exercise_05.html":\n'
            '      "book/downloads/chapter_05/exercise_05_portable.ipynb",',
            LAUNCH_BUTTONS_JS,
        )

    def test_portable_notebook_exists_and_banner_links_the_published_page(self):
        self.assertTrue(PORTABLE_PATH.exists())
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        banner = _src(portable.cells[0])
        self.assertIn(
            "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html",
            banner,
        )

    def test_eight_numbered_sections_present_in_order(self):
        positions = [self.md.index(title) for title in SECTION_TITLES]
        self.assertEqual(positions, sorted(positions))
        for title in SECTION_TITLES:
            self.assertEqual(self.md.count(title), 1, title)

    def test_opening_covers_list_has_eight_items_matching_sections(self):
        covers = self.md[self.md.index("## What this notebook covers") : self.md.index("## 1.")]
        for n in range(1, 9):
            self.assertIn(f"\n{n}. ", covers, f"missing covers list item {n}")
        self.assertNotIn("\n9. ", covers)

    def test_no_stability_or_frequency_material_anywhere(self):
        low = self.md.lower() + self.code.lower()
        for needle in STABILITY_NEEDLES:
            self.assertNotIn(needle, low, needle)

    def test_opening_does_not_promise_stability_or_a_dedicated_choosing_section(self):
        covers = self.md[: self.md.index("## 1.")]
        low = covers.lower()
        for needle in STABILITY_NEEDLES:
            self.assertNotIn(needle, low, needle)

    # -- leakage guard, shared recipe with Exercises 2 and 4 --------------

    def test_notebook_code_has_the_leakage_guard(self):
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', self.code)
        self.assertIn('assert "age" not in FEATURES', self.code)

    def test_canonical_feature_recipe_matches_the_manifest(self):
        recipe = MANIFEST["regularization"]["canonical_recipe"]
        self.assertEqual(recipe["bundle"], "all-eligible")
        self.assertEqual(recipe["measures"], ["CT"])
        self.assertIn("360 predictors", self.all_output)

    def test_outer_holdout_split_matches_exercises_2_and_4(self):
        self.assertIn(
            "train_test_split(\n    X, y, groups, test_size=0.25, random_state=42, stratify=groups\n)",
            self.code,
        )

    def test_dev_split_matches_exercise_4s_tuning_split(self):
        self.assertIn(
            "train_test_split(\n    X_train, y_train, test_size=0.25, random_state=7, stratify=groups_train\n)",
            self.code,
        )

    # -- Section 2: moved "Compare Predefined Feature Sets" ---------------

    def test_compare_predefined_feature_sets_heading_present_once(self):
        self.assertEqual(self.md.count("## 2. Compare Predefined Feature Sets"), 1)

    def test_regression_compare_iframe_present_exactly_once(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        srcs = [_src(c) for c in iframe_cells]
        self.assertEqual(sum("configs/regression_compare.json" in s for s in srcs), 1)

    def test_section_2_reframes_as_predefined_comparison_not_exploration_only(self):
        section2 = self.md[
            self.md.index("## 2. Compare Predefined Feature Sets") : self.md.index("## 3.")
        ]
        self.assertIn("Prior knowledge can define a feature set before model fitting", section2)
        self.assertIn("useful for prediction", section2)
        self.assertIn("exploratory comparison", _norm_ws(section2.lower()))

    # -- Section 3: leakage-safe data-driven selection ---------------------

    def test_correlation_ranking_uses_training_partition_only(self):
        section3 = self.md[self.md.index("## 3.") : self.md.index("## 4.")]
        corr_code_cells = [
            _src(c) for c in self.cells
            if c["cell_type"] == "code" and "np.corrcoef(X_train" in _src(c)
        ]
        self.assertEqual(len(corr_code_cells), 1)
        self.assertNotIn("X_test", corr_code_cells[0])
        self.assertIn("training participants only", section3)

    def test_selectkbest_is_inside_a_cross_validated_pipeline(self):
        select_cells = [_src(c) for c in self.cells if "SelectKBest" in _src(c)]
        self.assertTrue(select_cells)
        joined = "\n".join(select_cells)
        self.assertIn("Pipeline(", joined)
        self.assertIn("GridSearchCV", joined)
        self.assertIn("StandardScaler", joined)
        self.assertNotIn("X_test", joined)
        self.assertIn("[5, 10, 20, 40, 80, 160, 360]", joined)

    # -- Section 4: Ridge vs Lasso description ------------------------------

    def test_ridge_not_described_as_feature_selection(self):
        self.assertIn(
            "| Ridge             | Coefficients shrink toward zero       | Usually no          |",
            self.md,
        )
        self.assertIn("Ridge is regularization, not usually", self.md)

    def test_lasso_described_as_capable_of_exact_zero_coefficients(self):
        self.assertIn(
            "| Lasso             | Some coefficients become exactly zero | Yes                 |",
            self.md,
        )
        self.assertIn("embedded feature selection", self.md)

    def test_scaling_required_before_comparing_penalties(self):
        self.assertIn("standardized", self.md.lower())
        section4 = self.md[self.md.index("## 4.") : self.md.index("## 5.")]
        self.assertIn("predictors must be put on the same", section4)
        self.assertIn("standardized", section4)

    # -- Section 5: the regularization-explore activity ---------------------

    def test_regularization_explore_iframe_present_exactly_once(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        srcs = [_src(c) for c in iframe_cells]
        self.assertEqual(sum("configs/regularization_explore.json" in s for s in srcs), 1)

    def test_exactly_two_iframes_total(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        self.assertEqual(len(iframe_cells), 2)

    def test_test_set_never_referenced_between_section_4_and_section_6(self):
        # Sections 4-5 (the tuning playground) must not READ the outer test
        # set -- a comment merely naming it (to say it is untouched) is fine.
        start = _index_of_cell_starting_with(self.cells, "## 4. Ridge and Lasso Regression")
        end = _index_of_cell_starting_with(self.cells, "## 6. A Complete Regularized Regression Pipeline")
        playground_code = "\n\n".join(
            _src(c) for c in self.cells[start:end] if c["cell_type"] == "code"
        )
        code_lines = [ln for ln in playground_code.splitlines() if not ln.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        for needle in ("X_test)", "X_test,", "X_test.", "= X_test", "(X_test"):
            self.assertNotIn(needle, code_only, needle)
        for needle in ("y_test)", "y_test,", "y_test.", "= y_test"):
            self.assertNotIn(needle, code_only, needle)

    # -- Section 6: nested CV pipeline --------------------------------------

    def test_section_6_uses_standard_scaler_inside_each_pipeline(self):
        section6_code = [
            _src(c)
            for c in self.cells
            if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c)
        ]
        self.assertEqual(len(section6_code), 1)
        code = section6_code[0]
        self.assertIn("StandardScaler()", code)
        self.assertIn('Pipeline([("scaler", StandardScaler())', code)

    def test_alpha_tuning_happens_in_the_inner_loop_only(self):
        section6_code = [
            _src(c)
            for c in self.cells
            if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c)
        ][0]
        self.assertIn("GridSearchCV", section6_code)
        self.assertIn("search.fit(X_tr, y_tr)", section6_code)
        self.assertNotIn("search.fit(X_te", section6_code)

    def test_outer_scores_used_for_evaluation(self):
        section6_code = [
            _src(c)
            for c in self.cells
            if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c)
        ][0]
        self.assertIn("best_model.predict(X_te)", section6_code)
        self.assertIn("outer_test_mse", section6_code)
        self.assertIn("outer_test_r2", section6_code)

    def test_section_6_notes_inner_score_is_not_the_final_estimate(self):
        section6 = self.md[
            self.md.index("## 6. A Complete Regularized Regression Pipeline") : self.md.index("## 7.")
        ]
        self.assertIn("inner score chooses alpha", section6)
        self.assertIn("not the final performance estimate", section6)
        self.assertIn(
            "do not establish that the corresponding brain regions cause",
            _norm_ws(section6),
        )

    def test_results_table_is_concise_not_a_fold_by_fold_dump(self):
        summary_cells = [
            _src(c)
            for c in self.cells
            if c["cell_type"] == "code" and "pipeline_results.groupby" in _src(c)
        ]
        self.assertEqual(len(summary_cells), 1)

    # -- Section 7: other feature-selection methods -------------------------

    def test_other_methods_table_has_exactly_three_rows(self):
        expected_rows = [
            "| Univariate filtering",
            "| Sequential selection",
            "| PCA",
        ]
        for row in expected_rows:
            self.assertEqual(self.md.count(row), 1, row)
        section7 = self.md[
            self.md.index("## 7. Other Feature-Selection Methods") : self.md.index("## 8.")
        ]
        forbidden_rows = [
            "| Forward selection",
            "| Backward selection",
            "| Recursive feature elimination",
            "| Mutual information",
            "| Tree importance",
            "| Lasso",
        ]
        for row in forbidden_rows:
            self.assertNotIn(row, section7, row)

    def test_pca_identified_as_future_feature_extraction(self):
        self.assertIn(
            "| PCA                   | Replace features with components              | "
            "Feature extraction, not feature selection; covered later          |",
            self.md,
        )

    def test_sequential_feature_selector_is_introduced(self):
        self.assertIn("SequentialFeatureSelector", self.code)
        self.assertIn("direction=\"forward\"", self.code)

    def test_stepwise_runs_on_a_small_predefined_bundle_not_all_360(self):
        self.assertIn("FEATURES_FRONTAL", self.code)
        self.assertIn("42 predictors", self.all_output)
        sfs_cells = [_src(c) for c in self.cells if "SequentialFeatureSelector(" in _src(c)]
        self.assertEqual(len(sfs_cells), 1)
        self.assertIn("X_frontal_train", sfs_cells[0])
        self.assertNotIn("X_train)", sfs_cells[0])

    def test_no_third_major_widget_for_stepwise(self):
        # Only two <iframe activities exist in this notebook (checked above);
        # the stepwise demonstration uses code + a static matplotlib figure.
        section7 = self.md[
            self.md.index("## 7. Other Feature-Selection Methods") : self.md.index("## 8.")
        ]
        self.assertNotIn("<iframe", section7)

    # -- Section 8: open question, not a second table -----------------------

    def test_section_8_is_a_single_open_question_with_a_brief_answer(self):
        section8 = self.md[
            self.md.index("## 8. How Do We Choose a Feature-Selection Method?") :
            self.md.index("## In summary")
        ]
        self.assertIn("How do we choose a feature-selection method?", section8)
        self.assertIn("There is no universally best method", section8)
        # at most four brief bullet considerations
        bullet_count = section8.count("\n- ")
        self.assertLessEqual(bullet_count, 4, section8)

    def test_no_duplicate_methods_table_in_section_8(self):
        section8 = self.md[
            self.md.index("## 8. How Do We Choose a Feature-Selection Method?") :
            self.md.index("## In summary")
        ]
        self.assertNotIn("| Univariate filtering", section8)
        self.assertNotIn("Main idea", section8)

    # -- scope guards: no forbidden content ---------------------------------

    def test_no_classification_or_tree_model_content(self):
        low = (self.md + self.code).lower()
        for needle in (
            "logisticregression",
            "randomforest",
            "gradientboosting",
            "confusion_matrix",
            "recursivefeatureelimination",
            "mutual_info_regression",
        ):
            self.assertNotIn(needle, low, needle)

    def test_pca_is_mentioned_but_not_implemented(self):
        self.assertNotIn("PCA(", self.code)
        self.assertNotIn("from sklearn.decomposition", self.code)

    def test_no_wp_script_or_report_references_in_student_text(self):
        for needle in ("WP28", "WP27", "regularization_model_audit", "export_regularization_widget"):
            self.assertNotIn(needle, self.md)


if __name__ == "__main__":
    unittest.main()
