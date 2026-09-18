"""Offline assertions for book/chapters/chapter_06/exercise_06.ipynb (Exercise 6).

WP29 replaced the 2-line Exercise 6 placeholder with a notebook on decision
trees: a single shallow regression tree on two predefined predictors, the
greedy-splitting algorithm (with an interactive "Build a Tree Greedily"
activity), a tree-complexity curve, bagging and Random Forest, and an
interactive "One Tree or Many?" comparison. This file checks structure, that
trees are not scaled, that the 2D partition uses only axis-aligned splits,
that the greedy dataset is explicitly synthetic, that the complexity table
lists only the three intended hyperparameters, that Random Forest declares
an explicit feature-subsampling size, and that no boosting/classification
material was introduced.

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_06_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_06" / "exercise_06.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_06" / "exercise_06_portable.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")

SECTION_TITLES = [
    "## 1. One Regression Tree",
    "## 2. Build a Tree Greedily",
    "## 3. How Large Should the Tree Be?",
    "## 4. From One Tree to an Ensemble",
    "## 5. One Tree or Many?",
    "## 6. A Fair Model Comparison",
    "## 7. What Should We Remember?",
]

BOOSTING_NEEDLES = (
    "adaboost",
    "gradient boosting",
    "xgboost",
    "gradientboostingregressor",
)

CLASSIFICATION_NEEDLES = (
    "decisiontreeclassifier",
    "logistic",
    "classification tree",
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


class NotebookLoads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.full_source = "\n".join(_src(c) for c in cls.cells)
        cls.full_source_lower = cls.full_source.lower()

    def test_is_an_ipynb_not_the_old_placeholder(self):
        self.assertTrue(NB_PATH.exists())
        self.assertFalse((REPO_ROOT / "book" / "chapters" / "chapter_06" / "exercise_06.md").exists())

    def test_shorter_than_exercise_1(self):
        ex1 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4)
        self.assertLess(len(self.cells), len(ex1.cells))


class OpeningStructure(NotebookLoads):
    def test_title_cell_is_exactly_the_required_title(self):
        self.assertEqual(_src(self.cells[0]).strip(), "# Exercise 6: Decision Trees")

    def test_run_or_download_admonition_present_and_points_at_this_chapters_portable_notebook(self):
        admonition = _src(self.cells[1])
        self.assertIn(":class: how-to-use", admonition)
        self.assertIn("book/downloads/chapter_06/exercise_06_portable.ipynb", admonition)

    def test_what_this_notebook_covers_heading_and_four_objectives(self):
        i = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        text = _src(self.cells[i])
        for n in (1, 2, 3, 4):
            self.assertIn(f"{n}. ", text)
        self.assertNotIn("5. ", text)

    def test_opening_objectives_are_concise_not_an_implementation_list(self):
        i = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        text = _src(self.cells[i]).lower()
        for forbidden in ("max_depth=3", "min_samples_leaf", "random_state=42", "sensorimotor_core"):
            self.assertNotIn(forbidden, text)

    def test_section_titles_appear_in_order(self):
        indices = [_index_of_cell_starting_with(self.cells, t) for t in SECTION_TITLES]
        self.assertEqual(indices, sorted(indices))


class SectionOneSingleTree(NotebookLoads):
    def test_states_trees_do_not_require_scaling(self):
        i = _index_of_cell_starting_with(self.cells, "## 1. One Regression Tree")
        text = _norm_ws(_src(self.cells[i]).lower())
        self.assertIn("do **not** require feature scaling", text)

    def test_no_standardscaler_used_for_the_tree_models(self):
        self.assertNotIn("StandardScaler", self.full_source)

    def test_uses_the_two_predeclared_sensorimotor_core_features(self):
        self.assertIn('TREE_FEATURES = ["fsCT_L_3a_ROI", "fsCT_R_2_ROI"]', self.full_source)

    def test_features_are_members_of_the_declared_bundle_in_the_manifest(self):
        dt = MANIFEST["decision_tree"]["single_tree"]
        self.assertEqual(dt["bundle"], "sensorimotor_core")
        self.assertEqual(dt["features"], ["fsCT_L_3a_ROI", "fsCT_R_2_ROI"])

    def test_tree_settings_match_the_manifest(self):
        settings = MANIFEST["decision_tree"]["single_tree"]["settings"]
        self.assertIn(f"max_depth={settings['max_depth']}", self.full_source)
        self.assertIn(f"min_samples_leaf={settings['min_samples_leaf']}", self.full_source)
        self.assertIn(f"random_state={settings['random_state']}", self.full_source)

    def test_single_tree_is_shallow_and_readable_in_recorded_output(self):
        out = _collect_output(self.nb)
        self.assertIn("leaves = 8", out)
        self.assertIn("depth = 3", out)

    def test_2d_partition_plot_present(self):
        self.assertIn("pcolormesh", self.full_source)
        self.assertIn("tree.predict(np.column_stack", self.full_source)

    def test_axis_aligned_explanation_present(self):
        i = _index_of_cell_starting_with(self.cells, "### Two-dimensional partition plot")
        text = _src(self.cells[i]).lower()
        self.assertIn("axis-aligned", text)
        self.assertIn("piecewise constant", text)
        self.assertIn("vertical", text)
        self.assertIn("horizontal", text)

    def test_node_leaf_threshold_defined(self):
        i = _index_of_cell_starting_with(self.cells, "## 1. One Regression Tree")
        text = _src(self.cells[i]).lower()
        for term in ("node", "leaf", "threshold"):
            self.assertIn(term, text)


class SectionTwoGreedySplitting(NotebookLoads):
    def test_mse_and_weighted_split_mse_formulas_present(self):
        i = _index_of_cell_starting_with(self.cells, "## 2. Build a Tree Greedily")
        text = _src(self.cells[i])
        self.assertIn(r"\operatorname{MSE}", text)
        self.assertIn(r"\operatorname{MSE}_{\mathrm{split}}", text)

    def test_greedy_is_explicitly_defined(self):
        i = _index_of_cell_starting_with(self.cells, "## 2. Build a Tree Greedily")
        text = _src(self.cells[i]).lower()
        self.assertIn("greedy", text)
        self.assertIn("does not look several", text)

    def test_iframe_embeds_the_greedy_activity(self):
        self.assertIn(
            'title="Interactive greedy-splitting activity for a small synthetic regression tree"',
            self.full_source,
        )
        self.assertIn("config=../configs/tree_greedy_split.json", self.full_source)

    def test_activity_dataset_is_explicitly_synthetic_in_the_surrounding_prose(self):
        i = _index_of_cell_starting_with(self.cells, "### Interactive activity: Build a Tree Greedily")
        text = _src(self.cells[i]).lower()
        self.assertIn("synthetic", text)

    def test_optional_python_reproduction_present_and_collapsed_on_the_website(self):
        found = False
        for c in self.cells:
            if c["cell_type"] == "code" and "greedy_points" in _src(c):
                found = True
                self.assertIn("hide-cell", c.get("metadata", {}).get("tags", []))
        self.assertTrue(found)


class SectionThreeComplexity(NotebookLoads):
    def test_complexity_table_has_exactly_the_three_hyperparameters(self):
        i = _index_of_cell_starting_with(self.cells, "## 3. How Large Should the Tree Be?")
        text = _src(self.cells[i])
        for h in ("max_depth", "min_samples_leaf", "ccp_alpha"):
            self.assertIn(h, text)
        self.assertNotIn("n_estimators", text.split("###")[0])

    def test_complexity_figure_shows_training_and_validation_mse(self):
        found = False
        for c in self.cells:
            if c["cell_type"] == "code" and "depths = list(range(1, 11))" in _src(c):
                found = True
                self.assertIn("train_mse", _src(c))
                self.assertIn("val_mse", _src(c))
                self.assertIn("hide-input", c.get("metadata", {}).get("tags", []))
        self.assertTrue(found)

    def test_no_third_major_widget_in_this_section(self):
        section_start = _index_of_cell_starting_with(self.cells, "## 3. How Large Should the Tree Be?")
        section_end = _index_of_cell_starting_with(self.cells, "## 4. From One Tree to an Ensemble")
        for c in self.cells[section_start:section_end]:
            self.assertNotIn("<iframe", _src(c))


class SectionFourEnsembleIntro(NotebookLoads):
    def test_root_split_sensitivity_uses_deterministic_subsamples_not_only_random_state(self):
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "code" and "np.random.RandomState(seed)" in _src(c) and "root_feature" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        text = _src(self.cells[i])
        self.assertIn("replace=False", text)

    def test_root_splits_differ_across_samples_in_recorded_output(self):
        out = _collect_output(self.nb)
        self.assertIn("root split on fsCT_R_V2_ROI", out)
        self.assertIn("root split on fsCT_R_3a_ROI", out)

    def test_bagging_formula_present(self):
        self.assertIn(r"\hat{y}_{\mathrm{bagging}}", self.full_source)

    def test_comparison_table_matches_the_spec_exactly(self):
        expected_rows = [
            "| Single tree | One training sample | All available features | One tree |",
            "| Bagging | Bootstrap sample per tree | All available features | Average |",
            "| Random Forest | Bootstrap sample per tree | Random feature subset | Average |",
        ]
        for row in expected_rows:
            self.assertIn(row, self.full_source)

    def test_does_not_claim_random_state_alone_demonstrates_instability(self):
        start = _index_of_cell_starting_with(self.cells, "## 4. From One Tree to an Ensemble")
        end = _index_of_cell_starting_with(self.cells, "## 5. One Tree or Many?")
        text = _norm_ws("\n".join(_src(c) for c in self.cells[start:end]))
        self.assertIn("deterministic given its training data", text)
        self.assertIn("what varies above is the training sample itself", text)


class SectionFiveEnsembleActivity(NotebookLoads):
    def test_iframe_embeds_the_ensemble_activity(self):
        self.assertIn(
            'title="Interactive comparison of a single tree, bagging, and Random Forest '
            'for predicting age from brain structure"',
            self.full_source,
        )
        self.assertIn("config=../configs/tree_ensemble_compare.json", self.full_source)

    def test_uses_the_same_fixed_predictor_recipe_as_earlier_exercises(self):
        i = _index_of_cell_starting_with(self.cells, "## 5. One Tree or Many?")
        text = _src(self.cells[i]).lower()
        self.assertIn("360-predictor", text)

    def test_no_out_of_bag_evaluation_as_a_main_topic(self):
        self.assertNotIn("oob_score", self.full_source)
        self.assertNotIn("out-of-bag", self.full_source_lower)


class SectionSixFairComparison(NotebookLoads):
    def test_uses_identical_cv_folds_for_every_model(self):
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "code" and "cv = KFold" in _src(c) and "BaggingRegressor" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        text = _src(self.cells[i])
        self.assertIn("cross_val_score(model, X, y, cv=cv", text)
        self.assertIn("Random Forest", text)

    def test_random_forest_declares_an_explicit_max_features(self):
        self.assertIn("random_forest_max_features = 19", self.full_source)

    def test_reports_results_honestly_without_claiming_random_forest_always_wins(self):
        i = _index_of_cell_starting_with(self.cells, "## 6. A Fair Model Comparison")
        following = "\n".join(_src(c) for c in self.cells[i : i + 3]).lower()
        self.assertNotIn("random forest always", following)
        self.assertNotIn("always outperforms", following)
        self.assertIn("not", following)
        self.assertIn("guaranteed", following)


class SectionSevenSummary(NotebookLoads):
    def test_mentions_boosting_is_next_without_teaching_it(self):
        # Spec §16 permits one narrative sentence plus a closing question
        # asking students to predict how boosting will differ -- both
        # mentions are expected here; what must not appear is any actual
        # boosting implementation or explanation (checked in
        # ScopeExclusions.test_no_boosting_implementation).
        i = _index_of_cell_starting_with(self.cells, "## 7. What Should We Remember?")
        text = _norm_ws(_src(self.cells[i]).replace("> ", ""))
        self.assertIn(
            "boosting will build trees sequentially, with each new tree focusing on the errors",
            text,
        )

    def test_feature_importance_causality_caveat_present(self):
        i = _index_of_cell_starting_with(self.cells, "## 7. What Should We Remember?")
        text = _src(self.cells[i]).lower()
        self.assertIn("causal", text)

    def test_questions_to_take_away_present(self):
        i = _index_of_cell_starting_with(self.cells, "## 7. What Should We Remember?")
        text = _src(self.cells[i])
        self.assertIn("### Questions to take away", text)


class ScopeExclusions(NotebookLoads):
    def test_no_boosting_implementation(self):
        for needle in BOOSTING_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower)

    def test_no_classification_or_logistic_material(self):
        for needle in CLASSIFICATION_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower)

    def test_no_feature_importance_analysis(self):
        self.assertNotIn("feature_importances_", self.full_source)

    def test_no_final_project_material(self):
        for needle in ("final project", "final-project", "capstone"):
            self.assertNotIn(needle, self.full_source_lower)

    def test_no_internal_wp_references_in_student_facing_text(self):
        import re

        wp_reference = re.compile(r"\bWP\d")
        for c in self.cells:
            if c["cell_type"] != "markdown":
                continue
            self.assertIsNone(wp_reference.search(_src(c)), _src(c))


class LaunchButtonsAndPortable(NotebookLoads):
    def test_exercise_6_registered_in_launch_buttons_js(self):
        self.assertIn('"chapters/chapter_06/exercise_06.html":', LAUNCH_BUTTONS_JS)
        self.assertIn(
            '"book/downloads/chapter_06/exercise_06_portable.ipynb"', LAUNCH_BUTTONS_JS
        )

    def test_portable_notebook_exists_and_has_no_iframes(self):
        self.assertTrue(PORTABLE_PATH.exists())
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        for c in portable.cells:
            self.assertNotIn("<iframe", _src(c))

    def test_portable_notebook_keeps_the_greedy_reproduction_code_visible(self):
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        found = any(c["cell_type"] == "code" and "greedy_points" in _src(c) for c in portable.cells)
        self.assertTrue(found)

    def test_exercises_7_through_12_still_have_no_portable_notebook(self):
        for n in range(7, 13):
            portable_path = (
                REPO_ROOT / "book" / "downloads" / f"chapter_{n:02d}" / f"exercise_{n:02d}_portable.ipynb"
            )
            self.assertFalse(portable_path.exists())


if __name__ == "__main__":
    unittest.main()
