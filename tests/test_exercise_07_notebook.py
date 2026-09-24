"""Offline assertions for book/chapters/chapter_07/exercise_07.ipynb (Exercise 7).

WP32 replaced the Exercise 7 placeholder with a notebook on boosting and
gradient boosting: bagging-versus-boosting, a stage-by-stage squared-error
gradient-boosting activity on a small simulated dataset, a short
scikit-learn `GradientBoostingRegressor` illustration, a real-ABIDE
learning-rate/tree-count/depth explorer with Play/Pause, a static
early-stopping curve, a CV-tuned pipeline evaluated once on the locked test
set, and a single-tree/Random-Forest/gradient-boosting comparison. AdaBoost,
classification boosting, and executable XGBoost code are explicitly out of
scope.

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_07_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_07" / "exercise_07.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_07" / "exercise_07_portable.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")
GB_RESULT = json.loads((REPO_ROOT / "scripts" / "gradient_boosting_model_audit_result.json").read_text())

SECTION_TITLES = [
    "## 1. From Bagging to Boosting",
    "## 2. Building a Model One Tree at a Time",
    "## 3. Gradient Boosting with Scikit-Learn",
    "## 4. Learning Rate and Number of Trees",
    "## 5. Choosing When to Stop",
    "## 6. A Complete Gradient-Boosting Pipeline",
    "## 7. Comparing Tree-Based Models",
    "## 8. What Should We Remember?",
]

ADABOOST_NEEDLES = ("adaboost",)
CLASSIFICATION_BOOSTING_NEEDLES = (
    "gradientboostingclassifier",
    "classification boosting",
)
EXECUTABLE_XGBOOST_NEEDLES = ("import xgboost",)


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


def _index_of_cell_starting_with(cells, prefix: str) -> int:
    for i, c in enumerate(cells):
        if c["cell_type"] == "markdown" and _src(c).lstrip().startswith(prefix):
            return i
    raise AssertionError(f"no cell starts with {prefix!r}")


def _norm_ws(text: str) -> str:
    return " ".join(text.replace("**", "").split())


def _collect_output(nb) -> str:
    parts = []
    for c in nb.cells:
        if c["cell_type"] != "code":
            continue
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                parts.append(o.get("text", ""))
            elif o.get("output_type") == "error":
                raise AssertionError(f"notebook has a stored error output: {o.get('ename')}: {o.get('evalue')}")
    return "\n".join(parts)


class OpeningStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.full_source = "\n".join(_src(c) for c in cls.cells)
        cls.full_source_lower = cls.full_source.lower()

    def test_title_is_exact(self):
        self.assertEqual(_src(self.cells[0]).strip(), "# Exercise 7: Boosting and Gradient Boosting")

    def test_green_run_or_download_admonition_is_second_cell(self):
        src = _src(self.cells[1])
        self.assertIn("```{admonition} Run or download this notebook", src)
        self.assertIn(":class: how-to-use", src)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/"
            "book/downloads/chapter_07/exercise_07_portable.ipynb",
            src,
        )

    def test_what_this_notebook_covers_present_and_concise(self):
        idx = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        src = _src(self.cells[idx])
        self.assertLess(len(src), 1200)
        self.assertIn("boosting", src.lower())

    def test_does_not_promise_gradient_boosting_beats_random_forest(self):
        idx = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        src = _src(self.cells[idx]).lower()
        self.assertNotIn("will outperform", src)
        self.assertNotIn("always outperform", src)

    def test_section_titles_appear_in_order(self):
        indices = [_index_of_cell_starting_with(self.cells, t) for t in SECTION_TITLES]
        self.assertEqual(indices, sorted(indices))

    def test_exactly_two_iframes(self):
        count = sum(1 for c in self.cells if c["cell_type"] == "markdown" and "<iframe" in _src(c))
        self.assertEqual(count, 2)

    def test_cell_count_is_reasonable_and_shorter_than_exercise_01(self):
        ex1 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4)
        self.assertLess(len(self.cells), len(ex1.cells))
        self.assertGreaterEqual(len(self.cells), 25)

    def test_no_adaboost_anywhere(self):
        for needle in ADABOOST_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower)

    def test_no_classification_boosting_anywhere(self):
        for needle in CLASSIFICATION_BOOSTING_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower)

    def test_no_executable_xgboost_import_or_dependency(self):
        for needle in EXECUTABLE_XGBOOST_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower)
        # A Markdown-only illustrative example is fine; it must never be a
        # real, executed code cell.
        for c in self.cells:
            if c["cell_type"] == "code":
                self.assertNotIn("xgboost", _src(c).lower())

    def test_no_stored_error_outputs(self):
        _collect_output(self.nb)  # raises AssertionError on any error output


class DataLoadingAndSplits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_data_loading_cells_are_hidden_on_the_website(self):
        loading_cells = [c for c in self.cells if c["cell_type"] == "code" and "pd.read_csv" in _src(c)]
        self.assertGreaterEqual(len(loading_cells), 1)
        for c in loading_cells:
            self.assertIn("hide-input", c.get("metadata", {}).get("tags", []))

    def test_dev_split_matches_the_manifest_exactly(self):
        split_cell = next(c for c in self.cells if c["cell_type"] == "code" and "X_fit, X_val" in _src(c))
        src = _src(split_cell)
        dev_split = MANIFEST["gradient_boosting"]["dev_split"]
        holdout = MANIFEST["protocol"]["holdout_split"]
        self.assertIn(f'test_size=0.25, random_state={holdout["random_state"]}', src)
        self.assertIn(f'test_size=0.25, random_state={dev_split["random_state"]}', src)

    def test_recorded_cohort_and_split_sizes(self):
        out = _collect_output(self.nb)
        self.assertIn("n_fit = 564", out)
        self.assertIn("n_val = 189", out)
        self.assertIn("n_test = 251", out)
        self.assertIn("360 predictors", out)

    def test_no_scaling_of_tree_based_models(self):
        full_source = "\n".join(_src(c) for c in self.cells)
        self.assertNotIn("StandardScaler", full_source)


class BuildABoostedModelActivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_iframe_points_at_the_step_by_step_widget(self):
        iframe_cell = next(c for c in self.cells if c["cell_type"] == "markdown" and "boosting_step_by_step.json" in _src(c))
        self.assertIn(
            'title="Interactive stage-by-stage gradient boosting activity on a small simulated dataset"',
            _src(iframe_cell),
        )

    def test_reproduction_cell_is_hide_cell_and_matches_the_manifest(self):
        repro = next(c for c in self.cells if c["cell_type"] == "code" and "STEP_SEED" in _src(c))
        self.assertIn("hide-cell", repro.get("metadata", {}).get("tags", []))
        step = MANIFEST["gradient_boosting"]["step_by_step"]
        src = _src(repro)
        self.assertIn(f"STEP_SEED = {step['seed']}", src)
        self.assertIn(f"STEP_N = {step['n_observations']}", src)

    def test_no_duplicated_reflection_block_after_the_activity(self):
        full = "\n".join(_src(c) for c in self.cells)
        self.assertNotIn("Think again, after using the activity", full)


class GradientBoostingWithSklearn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_short_example_uses_the_declared_settings(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "gb_model = GradientBoostingRegressor" in _src(c))
        src = _src(cell)
        self.assertIn("n_estimators=100", src)
        self.assertIn("learning_rate=0.05", src)
        self.assertIn("max_depth=2", src)
        self.assertIn("random_state=42", src)
        # Concise per WP32 §9: the illustrative cell itself stays short.
        self.assertLess(len(src.splitlines()), 12)

    def test_parameter_table_lists_the_four_intended_hyperparameters(self):
        idx = _index_of_cell_starting_with(
            self.cells, "| Parameter | Meaning | Effect of increasing it |"
        )
        src = _src(self.cells[idx])
        for param in ("n_estimators", "learning_rate", "max_depth", "subsample"):
            self.assertIn(f"`{param}`", src)

    def test_states_no_scaling_required(self):
        idx = _index_of_cell_starting_with(
            self.cells, "| Parameter | Meaning | Effect of increasing it |"
        )
        self.assertIn("not** require feature scaling", _src(self.cells[idx]))


class ExploreBoostingParametersActivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_iframe_points_at_the_parameter_explorer_widget(self):
        iframe_cell = next(
            c for c in self.cells if c["cell_type"] == "markdown" and "boosting_parameter_explorer.json" in _src(c)
        )
        self.assertIn(
            'title="Interactive gradient-boosting parameter explorer for predicting age from brain structure"',
            _src(iframe_cell),
        )

    def test_activity_description_states_development_only_and_test_hidden(self):
        idx = _index_of_cell_starting_with(self.cells, "## 4. Learning Rate and Number of Trees")
        combined = _src(self.cells[idx]) + _src(self.cells[idx + 1])
        self.assertIn("564-participant", combined)
        self.assertIn("189-participant", combined)
        self.assertIn("locked outer test set is never part of this activity", _norm_ws(combined))


class ChoosingWhenToStop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_no_new_interactive_control_or_third_iframe(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Choosing When to Stop")
        next_idx = _index_of_cell_starting_with(self.cells, "## 6. A Complete Gradient-Boosting Pipeline")
        for c in self.cells[idx:next_idx]:
            self.assertNotIn("<iframe", _src(c))

    def test_takeaway_question_is_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Choosing When to Stop")
        next_idx = _index_of_cell_starting_with(self.cells, "## 6. A Complete Gradient-Boosting Pipeline")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertIn("300 trees", combined)
        self.assertIn("120 trees", combined)

    def test_stop_curve_cell_is_hide_input(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "stop_model = GradientBoostingRegressor" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))


class CvPipelineAndComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_intended_27_candidate_grid_is_shown_and_reduction_explained(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. A Complete Gradient-Boosting Pipeline")
        combined = "\n".join(_src(c) for c in self.cells[idx : idx + 3])
        self.assertIn('"learning_rate": [0.03, 0.05, 0.1]', combined)
        self.assertIn('"n_estimators": [50, 100, 200]', combined)
        self.assertIn('"max_depth": [1, 2, 3]', combined)
        self.assertIn("27-candidate", combined)
        self.assertIn("12-candidate", combined)

    def test_no_author_facing_grid_selection_paragraph_remains(self):
        # WP35 §4: no "predeclared rule", target-machine, WP, or internal
        # audit-report language in the student-facing grid-size explanation.
        idx = _index_of_cell_starting_with(self.cells, "## 6. A Complete Gradient-Boosting Pipeline")
        combined = "\n".join(_src(c) for c in self.cells[idx : idx + 3]).lower()
        for phrase in ("predeclared", "audited on the target machine", "target machine", "wp report", "audit"):
            self.assertNotIn(phrase, combined)

    def test_cv_fitting_cell_is_hide_input(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "candidate_grid = [" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))

    def test_cv_uses_5_folds_and_development_partition_only(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "candidate_grid = [" in _src(c))
        src = _src(cell)
        self.assertIn("KFold(n_splits=5", src)
        self.assertIn("cv.split(X_train)", src)

    def test_selected_settings_are_visible_and_raw_table_is_collapsed(self):
        # WP35 §5: the bar graph + selected-settings print stay visible; the
        # full numeric table is available but collapsed, not a second
        # duplicate visible table on the website.
        bar_cell = next(c for c in self.cells if c["cell_type"] == "code" and "selected settings:" in _src(c))
        self.assertNotIn("hide-input", bar_cell.get("metadata", {}).get("tags", []))
        self.assertNotIn("hide-cell", bar_cell.get("metadata", {}).get("tags", []))
        table_cell = next(c for c in self.cells if c["cell_type"] == "code" and "cv_results_df.round(2)" in _src(c))
        self.assertIn("hide-cell", table_cell.get("metadata", {}).get("tags", []))

    def test_bar_graph_encodes_depth_learning_rate_trees_and_mse(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "selected settings:" in _src(c))
        src = _src(cell)
        self.assertIn("max_depth", src)
        self.assertIn("learning_rate", src)
        self.assertIn("n_est", src)
        self.assertIn("mean_cv_mse", src)
        self.assertIn('legend(title="Learning rate"', src)
        self.assertIn("set_ylim(0", src)
        self.assertIn("lower is better", src.lower())
        self.assertIn("selected", src.lower())
        # Exactly one plotting call in this cell -- a single bar graph, not a
        # second duplicate chart plus a visible table.
        self.assertEqual(src.count("plt.show()"), 1)

    def test_recorded_selected_settings_and_test_metrics_match_the_audit(self):
        out = _collect_output(self.nb)
        cv = GB_RESULT["cv_pipeline"]
        self.assertIn(f"mean CV MSE = {cv['selected_mean_cv_mse']:.1f}", out)
        self.assertIn(f"locked-test MSE = {cv['test_mse']:.1f}", out)
        self.assertIn(f"locked-test R2 = {cv['test_r2']:.3f}", out)

    def test_comparison_uses_identical_split_and_carried_forward_settings(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "fair_tree_settings" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))
        src = _src(cell)
        fair = MANIFEST["decision_tree"]["fair_comparison"]
        self.assertIn(f"max_depth={fair['tree_settings']['max_depth']}", src)
        self.assertIn(f"min_samples_leaf={fair['tree_settings']['min_samples_leaf']}", src)
        self.assertIn(".fit(X_train, y_train)", src)

    def test_does_not_force_gradient_boosting_to_win_in_prose(self):
        idx = _index_of_cell_starting_with(self.cells, "## 7. Comparing Tree-Based Models")
        # Find the interpretation cell after the comparison table.
        interp = next(
            c
            for c in self.cells[idx:]
            if c["cell_type"] == "markdown" and "consistent held-out comparison" in _src(c)
        )
        src = _src(interp).lower()
        self.assertIn("not proof that gradient boosting universally wins", src)

    def test_xgboost_dropdown_is_markdown_only(self):
        cell = next(c for c in self.cells if c["cell_type"] == "markdown" and "Where does XGBoost fit?" in _src(c))
        src = _src(cell)
        self.assertIn("```{dropdown}", src)
        self.assertIn("XGBRegressor", src)
        self.assertIn("does not install, import, or execute `xgboost`", _norm_ws(src))


class ScopeExclusions(unittest.TestCase):
    def test_no_adaboost_in_manifest_or_configs(self):
        for path in [
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "boosting_step_by_step.json",
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "boosting_parameter_explorer.json",
        ]:
            self.assertNotIn("adaboost", path.read_text(encoding="utf-8").lower())


class Summary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_takeaway_questions_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. What Should We Remember?")
        src = _src(self.cells[idx])
        self.assertIn("### Questions to take away", src)
        for n in range(1, 7):
            self.assertIn(f"{n}. ", src)


class LaunchButtonsAndPortable(unittest.TestCase):
    def test_registered_in_launch_buttons_js(self):
        self.assertIn('"chapters/chapter_07/exercise_07.html"', LAUNCH_BUTTONS_JS)
        self.assertIn('"book/downloads/chapter_07/exercise_07_portable.ipynb"', LAUNCH_BUTTONS_JS)

    def test_portable_notebook_exists_and_has_no_iframe_or_static_reference(self):
        self.assertTrue(PORTABLE_PATH.exists())
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        full = "\n".join(_src(c) for c in portable.cells)
        self.assertNotIn("<iframe", full)
        self.assertNotIn("_static/", full)
        self.assertNotIn("```{", full)

    def test_portable_notebook_has_no_stored_execution_counts(self):
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        for c in portable.cells:
            if c["cell_type"] == "code":
                self.assertIsNone(c.get("execution_count"))

    def test_exercises_11_through_12_have_no_launch_button(self):
        # Exercise 8 gained a portable notebook and launch button in WP33,
        # Exercise 9 in WP34, Exercise 10 in WP38 (see test_exercise_08_notebook.py,
        # test_exercise_09_notebook.py, test_exercise_10_notebook.py); only
        # 11-12 remain placeholders.
        for n in range(11, 13):
            page = f'"chapters/chapter_{n:02d}/exercise_{n:02d}.html"'
            self.assertNotIn(page, LAUNCH_BUTTONS_JS)


if __name__ == "__main__":
    unittest.main()
