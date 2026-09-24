"""Offline assertions for book/chapters/chapter_06/exercise_06.ipynb (Exercise 6).

WP29 replaced the 2-line Exercise 6 placeholder with a notebook on decision
trees: a single shallow regression tree on two predefined predictors, the
greedy-splitting algorithm (with an interactive "Build a Tree Greedily"
activity), a tree-complexity curve, bagging and Random Forest, and an
interactive "One Tree or Many?" comparison. WP30 then: reworked the
single-tree diagram (short display aliases, "Mean age"/"Leaf"/"Predicted
age" wording, no bare "value ="), added gray partition-boundary overlays,
replaced the greedy activity's four-quadrant dataset with a noisy simulated
one, added a conditional classification-tree contrast figure (its
predeclared inclusion rule passed), removed the ensemble activity's visible
replicate selector and shortened its MSE axis titles, switched the fair-
comparison cell from hide-cell to hide-input, and removed the duplicate
post-activity "Think again" markdown blocks (each activity's widget already
has its own in-iframe "Reflect" list). This file checks structure, that
trees are not scaled, that the 2D partition uses only axis-aligned splits,
that the greedy dataset is explicitly simulated (not four clean quadrants),
that the complexity table lists only the three intended hyperparameters,
that Random Forest declares an explicit feature-subsampling size, and that
no boosting/unrelated material was introduced.

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

# WP30 sec 4: a conditional classification-tree contrast figure is now
# legitimately present (its predeclared inclusion rule passed -- see
# ClassificationComplexityContrast below), so DecisionTreeClassifier /
# "classification tree" are no longer forbidden needles. Logistic
# regression is still out of scope for Exercise 6.
CLASSIFICATION_NEEDLES = (
    "logisticregression",
    "logistic regression",
)

DT_RESULT = json.loads((REPO_ROOT / "scripts" / "decision_tree_model_audit_result.json").read_text())


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

    def test_partition_boundaries_correspond_to_the_tree_s_hierarchical_regions(self):
        # Executes the notebook's own draw_partition_boundaries() against a
        # small standalone 2-feature tree and checks that every drawn
        # segment is clipped to its own parent node's region rather than
        # spanning the full plot -- except the root split, which legitimately
        # covers the whole extent.
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.tree import DecisionTreeRegressor

        boundary_cell = None
        for c in self.cells:
            if c["cell_type"] == "code" and "def draw_partition_boundaries" in _src(c):
                boundary_cell = c
        self.assertIsNotNone(boundary_cell)
        namespace: dict = {}
        exec(_src(boundary_cell).split("\n\nx1_grid")[0], namespace)  # noqa: S102
        draw_partition_boundaries = namespace["draw_partition_boundaries"]

        X = [[0.0, 0.0], [0.0, 10.0], [10.0, 0.0], [10.0, 10.0]] * 5
        y = [1.0, 2.0, 3.0, 4.0] * 5
        tree = DecisionTreeRegressor(max_depth=2, min_samples_leaf=1, random_state=0).fit(X, y)

        fig, ax = plt.subplots()
        try:
            draw_partition_boundaries(ax, tree, (0.0, 10.0), (0.0, 10.0))
            segments = [c.get_segments()[0] for c in ax.collections]
            self.assertGreaterEqual(len(segments), 1)
            full_x_span = any(
                (seg[0][0] == seg[1][0]) and abs(seg[0][1] - 0.0) < 1e-9 and abs(seg[1][1] - 10.0) < 1e-9
                for seg in segments
            ) or any(
                (seg[0][1] == seg[1][1]) and abs(seg[0][0] - 0.0) < 1e-9 and abs(seg[1][0] - 10.0) < 1e-9
                for seg in segments
            )
            self.assertTrue(full_x_span, "the root split should span the full plot extent")
            if len(segments) > 1:
                non_root_full_span = [
                    seg
                    for seg in segments[1:]
                    if (abs(seg[0][0] - seg[1][0]) < 1e-9 and abs(seg[0][1] - 0.0) < 1e-9 and abs(seg[1][1] - 10.0) < 1e-9)
                    or (
                        abs(seg[0][1] - seg[1][1]) < 1e-9
                        and abs(seg[0][0] - 0.0) < 1e-9
                        and abs(seg[1][0] - 10.0) < 1e-9
                    )
                ]
                self.assertEqual(non_root_full_span, [], "a non-root split should not span the full plot extent")
        finally:
            plt.close(fig)

    def test_diagram_uses_display_only_aliases_while_real_columns_remain_in_code(self):
        # WP30 sec 1.1: aliases appear in the diagram-producing cell and its
        # surrounding prose, but the real ABIDE column names are still what
        # every other cell (TREE_FEATURES, FEATURES, the manifest) uses.
        self.assertIn('"fsCT_L_3a_ROI": "Left 3a thickness"', self.full_source)
        self.assertIn('"fsCT_R_2_ROI": "Right area 2 thickness"', self.full_source)
        self.assertIn('TREE_FEATURES = ["fsCT_L_3a_ROI", "fsCT_R_2_ROI"]', self.full_source)
        i = _index_of_cell_starting_with(self.cells, "### Tree diagram")
        text = _src(self.cells[i]).lower()
        self.assertIn("display-only", text)
        self.assertIn("fsct_l_3a_roi", text)

    def test_diagram_formatter_uses_mean_age_leaf_predicted_age_wording(self):
        self.assertIn("Mean age =", self.full_source)
        self.assertIn('"Leaf\\nPredicted age', self.full_source)

    def test_diagram_has_a_title_and_a_leaf_mean_annotation(self):
        self.assertIn('"Resulting Regression Tree"', self.full_source)
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "code" and "format_tree_diagram(tree" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        text = _src(self.cells[i]).lower()
        self.assertIn("mean age of the training participants who reached that leaf", text)

    def test_no_visible_tree_box_contains_the_bare_sklearn_value_label(self):
        # Executes the notebook's own formatter against a small standalone
        # tree, proving the fix functionally rather than just grepping
        # source text.
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        from sklearn.tree import DecisionTreeRegressor

        formatter_cell = None
        for c in self.cells:
            if c["cell_type"] == "code" and "def format_tree_diagram" in _src(c):
                formatter_cell = c
        self.assertIsNotNone(formatter_cell)

        namespace = {"plot_tree": __import__("sklearn.tree", fromlist=["plot_tree"]).plot_tree}
        exec(_src(formatter_cell), namespace)  # noqa: S102 (test-only, trusted local source)
        format_tree_diagram = namespace["format_tree_diagram"]

        rng = np.random.RandomState(0)
        X = rng.rand(60, 2)
        y = rng.rand(60) * 10
        tree = DecisionTreeRegressor(max_depth=2, min_samples_leaf=5, random_state=0).fit(X, y)

        fig, ax = plt.subplots()
        try:
            format_tree_diagram(tree, ["feat_a", "feat_b"], {"feat_a": "Alias A", "feat_b": "Alias B"}, ax)
            texts = [t.get_text() for t in ax.texts]
            self.assertTrue(any("Mean age" in t or "Predicted age" in t for t in texts))
            for t in texts:
                self.assertNotIn("value =", t)
        finally:
            plt.close(fig)


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
        self.assertTrue("synthetic" in text or "simulated" in text)
        self.assertIn("brain measure 1", text)
        self.assertIn("brain measure 2", text)

    def test_activity_prose_no_longer_describes_four_quadrant_points(self):
        i = _index_of_cell_starting_with(self.cells, "### Interactive activity: Build a Tree Greedily")
        text = _src(self.cells[i]).lower()
        self.assertNotIn("quadrant", text)
        self.assertNotIn("understandable split structure", text)

    def test_optional_python_reproduction_present_and_collapsed_on_the_website(self):
        found = False
        for c in self.cells:
            if c["cell_type"] == "code" and "greedy_x1" in _src(c) and "SEED = 17" in _src(c):
                found = True
                self.assertIn("hide-cell", c.get("metadata", {}).get("tags", []))
        self.assertTrue(found)

    def test_reproduction_uses_the_committed_formula_constants_and_seed(self):
        dt_scripts_dir = REPO_ROOT / "scripts"
        import sys

        sys.path.insert(0, str(dt_scripts_dir))
        import export_tree_greedy_widget as tg

        text = self.full_source
        self.assertIn(f"MU1, SD1 = {tg.MU1}, {tg.SD1}", text)
        self.assertIn(
            f"INTERCEPT, BETA1, BETA2, GAMMA, NOISE_SD = {tg.INTERCEPT}, {tg.BETA1}, {tg.BETA2}, {tg.GAMMA}, {tg.NOISE_SD}",
            text,
        )
        self.assertIn(f"SEED = {tg.SELECTED_SEED}", text)

    def test_only_one_post_activity_reflection_block_for_the_greedy_activity(self):
        # WP30 sec 3.2: the notebook's separate "Think again" markdown block
        # duplicated the widget's own in-iframe "Reflect" list almost
        # verbatim -- removed here, keeping the widget's list as the single
        # reflection mechanism for this activity.
        self.assertNotIn("Think again, after using the activity", self.full_source)


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
            if c["cell_type"] == "code" and "train_mse, val_mse, n_leaves = [], [], []" in _src(c):
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

    def test_regression_curve_is_not_mislabeled_as_a_two_feature_curve(self):
        section_start = _index_of_cell_starting_with(self.cells, "## 3. How Large Should the Tree Be?")
        section_end = _index_of_cell_starting_with(self.cells, "## 4. From One Tree to an Ensemble")
        text = "\n".join(_src(c) for c in self.cells[section_start:section_end]).lower()
        self.assertNotIn("two-feature curve", text)
        self.assertNotIn("two feature curve", text)


class ClassificationComplexityContrast(NotebookLoads):
    """WP30 sec 4: the classification-tree contrast figure is conditional on
    a predeclared inclusion rule, evaluated once and never re-tuned. These
    tests tie the notebook's actual content to that committed audit result,
    so the figure is present if and only if the rule passed."""

    def test_inclusion_rule_is_the_committed_audit_result(self):
        rule = DT_RESULT["classification_complexity_curve"]["inclusion_rule"]
        self.assertIn("include_figure", rule)

    def test_figure_present_if_and_only_if_the_rule_passed(self):
        include_figure = DT_RESULT["classification_complexity_curve"]["inclusion_rule"]["include_figure"]
        has_figure = "Classification: predicting autism diagnosis" in self.full_source
        self.assertEqual(has_figure, include_figure)
        if include_figure:
            self.assertNotIn("unsuccessful audit", self.full_source_lower)
        else:
            self.assertNotIn("Classification: predicting autism diagnosis", self.full_source)
            self.assertNotIn("DecisionTreeClassifier", self.full_source)

    def test_corrected_development_only_numbers_match_the_committed_audit(self):
        if not DT_RESULT["classification_complexity_curve"]["inclusion_rule"]["include_figure"]:
            self.skipTest("inclusion rule failed; no figure to check")
        ccc = DT_RESULT["classification_complexity_curve"]
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "markdown" and "ROC AUC is higher-is-better" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        text = _src(self.cells[i])
        self.assertIn(f"max_depth={ccc['best_depth']}", text)
        self.assertIn(f"{ccc['best_val_auc']:.3f}", text)
        self.assertIn(f"{ccc['depth2_val_auc']:.3f}", text)
        self.assertIn(f"{ccc['margin_over_depth2']:.3f}", text)
        self.assertIn("training-and-validation data", text)
        self.assertIn("753", text)
        self.assertIn("251", text)
        self.assertNotIn("full eligible cohort", text)

    def test_no_stale_claim_that_never_reading_an_index_was_sufficient(self):
        # WP30R sec 5: the earlier, misleading provenance framing must not
        # survive anywhere in student-facing text.
        self.assertNotIn("is never touched by this audit", self.full_source_lower)
        self.assertNotIn("never read a stored", self.full_source_lower)

    def test_panels_are_clearly_labeled_and_carry_the_required_caveats(self):
        if not DT_RESULT["classification_complexity_curve"]["inclusion_rule"]["include_figure"]:
            self.skipTest("inclusion rule failed; no figure to check")
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "markdown" and "ROC AUC is higher-is-better" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        text = _src(self.cells[i])
        self.assertIn("higher-is-better", text)
        self.assertIn("lower-is-better", text)
        self.assertIn("does **not** mean classification is inherently more (or less) complex", text)

    def test_classification_audit_uses_the_exercise_3_cohort_and_recipe(self):
        text = self.full_source
        self.assertIn(
            'y_eligible = (model_df.loc[has_group, "group"].to_numpy(float) == 1.0).astype(int)', text
        )
        self.assertIn("X_eligible = model_df.loc[has_group, FEATURES].to_numpy(float)", text)
        self.assertIn("StratifiedKFold(n_splits=5, shuffle=True, random_state=42)", text)

    def test_classification_audit_reconstructs_exercise_3_outer_split_and_excludes_it(self):
        # WP30R: the notebook must reconstruct Exercise 3's exact outer
        # split, prove development/outer-test disjointness by participant
        # set (not merely by omission), and restrict the CV pool (X_cls,
        # y_cls) to the development rows only.
        text = self.full_source
        self.assertIn("test_size=0.25, random_state=42, stratify=y_eligible", text)
        self.assertIn("dev_subjects.isdisjoint(test_subjects)", text)
        self.assertIn("dev_subjects | test_subjects == set(subjects_eligible)", text)
        self.assertIn("X_cls, y_cls = X_eligible[dev_pos], y_eligible[dev_pos]", text)

    def test_classification_audit_never_touches_an_outer_test_set(self):
        section_start = _index_of_cell_starting_with(self.cells, "## 3. How Large Should the Tree Be?")
        section_end = _index_of_cell_starting_with(self.cells, "## 4. From One Tree to an Ensemble")
        text = "\n".join(_src(c) for c in self.cells[section_start:section_end])
        self.assertNotIn("X_test", text)
        self.assertNotIn("y_test", text)
        # test_pos/test_subjects exist only for the disjointness assertions
        # above -- never passed to .fit(/.predict(/roc_auc_score(.
        for forbidden in (".fit(X_eligible[test_pos]", ".predict(X_eligible[test_pos]", "roc_auc_score(y_eligible[test_pos]"):
            self.assertNotIn(forbidden, text)

    def test_classification_audit_reports_eligible_development_outer_test_sizes(self):
        out = _collect_output(self.nb)
        self.assertIn("eligible = 1004", out)
        self.assertIn("development = 753", out)
        self.assertIn("outer test (excluded) = 251", out)


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

    def test_student_facing_text_calls_the_prediction_panel_a_fixed_training_sample(self):
        i = _index_of_cell_starting_with(self.cells, "## 5. One Tree or Many?")
        text = _norm_ws(_src(self.cells[i]))
        self.assertIn("fixed training sample", text)

    def test_only_one_post_activity_reflection_block_for_the_ensemble_activity(self):
        start = _index_of_cell_starting_with(self.cells, "## 5. One Tree or Many?")
        end = _index_of_cell_starting_with(self.cells, "## 6. A Fair Model Comparison")
        text = "\n".join(_src(c) for c in self.cells[start:end])
        self.assertNotIn("Think again, after using the activity", text)

    def test_ensemble_config_has_no_visible_replicate_seed_selector(self):
        config = json.loads(
            (REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "tree_ensemble_compare.json").read_text()
        )
        self.assertNotIn("defaultReplicateSeed", config)


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

    def test_comparison_cell_is_hide_input_not_hide_cell(self):
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "code" and "cv = KFold" in _src(c) and "BaggingRegressor" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        tags = self.cells[i].get("metadata", {}).get("tags", [])
        self.assertIn("hide-input", tags)
        self.assertNotIn("hide-cell", tags)

    def test_comparison_cell_has_a_recorded_table_output(self):
        i = None
        for idx, c in enumerate(self.cells):
            if c["cell_type"] == "code" and "cv = KFold" in _src(c) and "BaggingRegressor" in _src(c):
                i = idx
        self.assertIsNotNone(i)
        self.assertTrue(len(self.cells[i].get("outputs", [])) > 0)


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
        found = any(c["cell_type"] == "code" and "greedy_x1" in _src(c) for c in portable.cells)
        self.assertTrue(found)

    def test_portable_notebook_has_only_one_reflection_block_per_activity(self):
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        full = "\n".join(_src(c) for c in portable.cells)
        self.assertNotIn("Think again, after using the activity", full)

    def test_portable_notebook_fair_comparison_code_stays_visible(self):
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        found = any(
            c["cell_type"] == "code" and "cv = KFold" in _src(c) and "BaggingRegressor" in _src(c)
            for c in portable.cells
        )
        self.assertTrue(found)

    def test_exercises_11_through_12_still_have_no_portable_notebook(self):
        # Exercise 7 gained a portable notebook in WP32, Exercise 8 in WP33
        # (see test_exercise_07_notebook.py, test_exercise_08_notebook.py),
        # Exercise 9 in WP34 (see test_exercise_09_notebook.py), and
        # Exercise 10 in WP38 (see test_exercise_10_notebook.py); only
        # 11-12 remain placeholders.
        for n in range(11, 13):
            portable_path = (
                REPO_ROOT / "book" / "downloads" / f"chapter_{n:02d}" / f"exercise_{n:02d}_portable.ipynb"
            )
            self.assertFalse(portable_path.exists())


if __name__ == "__main__":
    unittest.main()
