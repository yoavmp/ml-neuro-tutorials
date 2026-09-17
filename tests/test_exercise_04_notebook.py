"""Offline assertions for book/chapters/chapter_04/exercise_04.ipynb (Exercise 4),
its portable counterpart, and the launch-button/toc wiring WP27 changed.

WP27 replaced the Exercise 4 Markdown placeholder ("Materials for this
exercise will be added before the practice session.") with a real notebook,
"Exercise 4: Validation and Cross-Validation", covering: single-split vs.
cross-validation instability, cross-validation for a fixed KNN model,
train/validation/test roles, tuning k without looking at the test set,
nested cross-validation, and choosing a validation strategy. It reuses
Exercise 2's ABIDE age-prediction task and fixed 360-predictor KNN set
unchanged; feature selection, logistic regression, classification CV, and
final-project material are explicitly out of scope (spec section 5).

This file covers the ~30 focused checks from
WPs/WP27_EXERCISE_4_VALIDATION_AND_CROSS_VALIDATION.md section 25 items
1-30. It follows the structure/style of test_exercise_02_notebook.py and
test_exercise_03_notebook.py.

Standard-library ``unittest`` plus ``nbformat``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_04_notebook.py'
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_04" / "exercise_04_portable.ipynb"
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")
AUDIT_RESULT = json.loads(
    (REPO_ROOT / "scripts" / "wp27_validation_audit_result.json").read_text(encoding="utf-8")
)
STABILITY_DATA = json.loads(
    (REPO_ROOT / "book" / "_static" / "widgets" / "data" / "wp27_validation_stability.json").read_text(
        encoding="utf-8"
    )
)
LOCK_TEST_TS = (
    REPO_ROOT / "interactive" / "src" / "components" / "validation-lock-test.ts"
).read_text(encoding="utf-8")
LOCK_TEST_CONFIG = json.loads(
    (REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "validation_lock_test.json").read_text(
        encoding="utf-8"
    )
)
NESTED_CV_DATA = json.loads(
    (REPO_ROOT / "book" / "_static" / "widgets" / "data" / "wp27_nested_cv_explorer.json").read_text(
        encoding="utf-8"
    )
)
CUSTOM_CSS = (REPO_ROOT / "book" / "_static" / "custom.css").read_text(encoding="utf-8")

# WP27R's required hidden-test candidate values (spec section 2).
WP27R_REQUIRED_LOCK_TEST_KS = {8, 10, 15, 20, 25, 30, 50}

# WP26R's parent commit, the last commit before WP27's own spec commit
# (28d1e9b) -- see the WP27 spec section 2/29 and the hand-off's starting SHA.
WP27_BASE_COMMIT = "74c9a9a"


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


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


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


class Notebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)

    # -- 1. real notebook, not a placeholder --------------------------------

    def test_exercise_4_is_an_ipynb_not_a_placeholder_markdown_page(self):
        self.assertTrue(NB_PATH.exists())
        self.assertFalse(
            (REPO_ROOT / "book" / "chapters" / "chapter_04" / "exercise_04.md").exists()
        )
        nbformat.validate(self.nb)

    # -- 2. title and capitalization -----------------------------------------

    def test_correct_title_and_capitalization(self):
        self.assertEqual(
            _src(self.cells[0]).strip(),
            "# Exercise 4: Validation and Cross-Validation",
        )

    # -- 3. concise "What This Notebook Covers" ------------------------------

    def test_concise_what_this_notebook_covers(self):
        self.assertEqual(self.md.count("## What this notebook covers"), 1)
        section = self.md.split("## What this notebook covers", 1)[1]
        section = section.split("## 1.", 1)[0]
        # concise: well short of Exercise 1's/2's opening section length
        self.assertLess(len(section), 1800, "opening section has grown long")

    # -- 4. section order -----------------------------------------------------

    def test_correct_section_order(self):
        headings = (
            "## 1. Our Regression Data",
            "## 2. From One Split to Cross-Validation",
            "## 3. Cross-Validation for a Fixed KNN Model",
            "## 4. Train, Validation, and Test Data",
            "## 5. Tune KNN Without Looking at the Test Set",
            "## 6. Nested Cross-Validation",
            "## 7. Choosing a Validation Strategy",
        )
        for head in headings:
            self.assertIn(head, self.md)
            self.assertEqual(self.md.count(head), 1, head)
        positions = [self.md.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("## 8.", self.md)

    # -- 5. familiar loading code hidden, output retained --------------------

    def test_familiar_loading_code_is_hidden_with_output_retained(self):
        loading_cells = [
            c
            for c in self.cells
            if c["cell_type"] == "code" and "hide-input" in c.get("metadata", {}).get("tags", [])
        ]
        self.assertGreaterEqual(len(loading_cells), 1)
        for c in loading_cells:
            self.assertTrue(c.get("outputs"), "hidden loading cell has no retained output")

    # -- 6. same ABIDE task as Exercise 2 -------------------------------------

    def test_same_abide_age_prediction_task_and_fixed_predictors_as_exercise_2(self):
        ex2 = nbformat.read(
            REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb", as_version=4
        )
        ex2_code = "\n\n".join(_src(c) for c in ex2.cells if c["cell_type"] == "code")
        # same public data pin
        pin = re.search(r'PIN = "([0-9a-f]{40})"', self.code)
        ex2_pin = re.search(r'PIN = "([0-9a-f]{40})"', ex2_code)
        self.assertIsNotNone(pin)
        self.assertEqual(pin.group(1), ex2_pin.group(1))
        # same target and same fixed 360-predictor recipe
        self.assertIn('y = model_df.loc[has_age, "age"]', self.code)
        self.assertIn(
            'FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]', self.code
        )
        self.assertIn("360 predictors", self.all_output)

    # -- 7. no feature-selection lesson --------------------------------------

    def test_no_feature_selection_lesson(self):
        low = (self.md + self.code).lower()
        for needle in ("selectkbest", "feature_selection", "recursive feature elimination", "rfe("):
            self.assertNotIn(needle, low)
        # the one permitted mention is the explicit "not this lesson" pointer
        self.assertEqual(self.md.lower().count("feature selection"), 1)
        self.assertIn("Feature\nselection is Exercise 5's topic", self.md)

    # -- 8. no logistic-regression implementation ----------------------------

    def test_no_logistic_regression_implementation(self):
        self.assertNotIn("LogisticRegression", self.code)
        self.assertNotIn("logistic_regression", self.code.lower())
        # exactly the one homework-bridge mention in prose, no code/results
        self.assertEqual(self.md.lower().count("logistic"), 1)

    # -- 9. no classification/stratification section ------------------------

    def test_no_classification_or_stratified_cv_section(self):
        low_code = self.code.lower()
        self.assertNotIn("stratifiedkfold", low_code)
        self.assertNotIn("confusion matrix", self.md.lower())
        self.assertNotIn("classification_report", low_code)
        # "classification" appears exactly once: the homework-bridge sentence
        # ("...logistic-regression classification"), never as a section here.
        self.assertEqual(self.md.lower().count("classification"), 1)

    # -- 10. one homework bridge sentence only -------------------------------

    def test_one_homework_bridge_sentence_only(self):
        self.assertEqual(self.md.lower().count("homework"), 1)
        self.assertIn(
            "In the homework, you will apply the same workflow to "
            "logistic-regression\nclassification.",
            self.md,
        )

    # -- 11. combined stability/CV interaction occurs once -------------------

    def test_combined_stability_cv_interaction_occurs_once(self):
        self.assertEqual(self.md.count("configs/validation_stability.json"), 1)
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        self.assertEqual(len(iframe_cells), 3)

    # -- 12. small sample sizes present when justified by the audit ----------

    def test_small_sample_sizes_present_per_audit(self):
        part_a = AUDIT_RESULT["part_a_sample_size_stability"]
        meaningful = part_a["sizes_with_meaningful_instability"]
        self.assertTrue(meaningful, "audit found no sizes with meaningful instability")
        self.assertEqual([str(n) for n in meaningful], STABILITY_DATA["sizesWithMeaningfulInstability"])
        self.assertTrue(all(int(n) < 100 for n in meaningful))
        widget_size_keys = [s["sizeKey"] for s in STABILITY_DATA["sizes"]]
        for n in meaningful:
            self.assertIn(str(n), widget_size_keys)

    # -- 13. small-sample conclusion not attributed to full ABIDE ------------

    def test_small_sample_conclusion_not_attributed_to_full_abide(self):
        self.assertIn(
            "> The full ABIDE sample is relatively large for this demonstration. The\n"
            "> small-sample settings represent research situations in which only tens of\n"
            "> participants are available.",
            self.md,
        )
        self.assertNotIn(
            "ABIDE is generally too small", self.md
        )
        self.assertNotIn("full-sample result is unreliable", self.md)

    # -- 14. no unearned statistical-significance language -------------------

    def test_no_statistical_significance_language(self):
        self.assertNotIn("statistically significant", self.md.lower())
        self.assertNotIn("statistical significance", self.md.lower())
        self.assertNotIn("p < 0.05", self.md)
        self.assertNotIn("p-value", self.md.lower())

    # -- 15. fixed-model CV example uses pipeline scaling --------------------

    def test_fixed_model_cv_uses_scaling_inside_a_pipeline(self):
        self.assertIn(
            "make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=K_EXAMPLE))",
            self.code,
        )
        self.assertIn("cross_validate(", self.code)
        self.assertIn("KFold(n_splits=5", self.code)

    # -- 16. train/validation/test roles defined -----------------------------

    def test_train_validation_test_roles_are_defined(self):
        self.assertIn("Fit model parameters", self.md)
        self.assertIn("Compare hyperparameter values", self.md)
        self.assertIn("Evaluate the selected procedure once", self.md)
        self.assertIn(
            "A **hyperparameter** is a model\nsetting chosen before fitting",
            self.md,
        )

    # -- 17. guiding questions compare training-/validation-selected k -------

    def test_guiding_questions_compare_training_and_validation_selected_k(self):
        self.assertIn("```{admonition} Think first", self.md)
        think_first = self.md.split("```{admonition} Think first", 1)[1].split("```", 1)[0]
        self.assertIn("training-selected", think_first)
        self.assertIn("validation-selected", think_first)
        self.assertIn("Should you change `k` after seeing the test result?", think_first)
        # answers not given before the activity: the reveal cell (Section 5)
        # must come after this Think-first block
        self.assertLess(self.md.index("```{admonition} Think first"), self.md.index("## 5."))

    # -- 18/19/20. lock/reveal/reset behavior --------------------------------

    def test_test_result_initially_hidden_and_controls_lock_after_reveal(self):
        # widget: reveal panel starts hidden and only unhides once locked
        self.assertIn("let locked = false;", LOCK_TEST_TS)
        self.assertIn("reveal.hidden = !locked;", LOCK_TEST_TS)
        self.assertIn("lockBtn.disabled = locked;", LOCK_TEST_TS)
        # notebook: the reveal cell is a distinct, later cell than the tuning cell
        self.assertIn("Lock Choice and Reveal Test Result", self.md)

    def test_reset_behavior_is_explicit(self):
        self.assertIn('resetBtn.textContent = "Reset Activity";', LOCK_TEST_TS)
        self.assertIn("would not be a valid analysis", LOCK_TEST_TS)
        self.assertIn("the test set is examined once", LOCK_TEST_TS)

    # -- 21/22. nested CV uses inner+outer loops, scaling within folds -------

    def test_nested_cv_uses_inner_and_outer_loops(self):
        self.assertIn("outer_cv = KFold(n_splits=N_OUTER", self.code)
        self.assertIn("inner_cv = KFold(n_splits=N_INNER", self.code)
        self.assertIn("GridSearchCV(", self.code)
        self.assertIn("for fold_i, (train_idx, test_idx) in enumerate(outer_cv.split(X))", self.code)

    def test_scaling_occurs_within_folds(self):
        self.assertIn(
            'Pipeline([("scaler", StandardScaler()), ("knn", KNeighborsRegressor())])',
            self.code,
        )
        # the pipeline is constructed and fit fresh inside the outer loop body
        outer_loop_body = self.code.split(
            "for fold_i, (train_idx, test_idx) in enumerate(outer_cv.split(X))", 1
        )[1].split("nested = pd.DataFrame", 1)[0]
        self.assertIn('Pipeline([("scaler", StandardScaler())', outer_loop_body)
        self.assertIn("grid.fit(X_tr, y_tr)", outer_loop_body)

    # -- 23. outer metrics, not inner scores, presented as the estimate ------

    def test_outer_metrics_not_inner_score_presented_as_performance_estimate(self):
        self.assertIn(
            "The\nbest *inner* cross-validation score is not reported as a final\n"
            "performance estimate",
            self.md,
        )
        self.assertIn("mean outer-test MSE = {nested['outer_test_mse'].mean()", self.code)
        self.assertIn("mean outer-test R^2 = {nested['outer_test_r2'].mean()", self.code)
        self.assertNotIn("best_score_", self.code)

    # -- 24. independence caveat ----------------------------------------------

    def test_independence_caveat_present(self):
        self.assertIn(
            "These examples treat participants as independent observations. Repeated\n"
            "measurements from the same participant would need to remain together in the\n"
            "same fold.",
            self.md,
        )
        self.assertEqual(self.md.count("independent observations"), 1)

    # -- 30. no final-project text --------------------------------------------

    def test_no_final_project_text(self):
        low = self.md.lower()
        for needle in ("final project", "final-project", "capstone"):
            self.assertNotIn(needle, low)

    # -- misc integrity --------------------------------------------------------

    def test_no_execution_errors_or_stderr_committed(self):
        for c in self.cells:
            for o in c.get("outputs", []):
                self.assertNotEqual(o.get("output_type"), "error", _src(c)[:120])
                if o.get("output_type") == "stream":
                    self.assertNotEqual(o.get("name"), "stderr", _src(c)[:120])

    def test_no_wp_or_script_references_in_student_text(self):
        low_md = self.md.lower()
        for needle in ("scripts/", "wp27", "wp2", "audit script", "audit_result"):
            self.assertNotIn(needle, low_md)


class PortableNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(PORTABLE_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")

    # -- 25. portable notebook exists ------------------------------------------

    def test_exercise_4_portable_notebook_exists(self):
        self.assertTrue(PORTABLE_PATH.exists())
        nbformat.validate(self.nb)
        self.assertIn(
            "# Exercise 4: Validation and Cross-Validation - portable notebook",
            _src(self.cells[0]),
        )

    # -- 26. portable test-result reveal output is absent ----------------------

    def test_portable_test_result_reveal_output_absent(self):
        reveal_cells = [
            c
            for c in self.cells
            if c["cell_type"] == "code" and "STUDENT_CHOICE_K" in _src(c)
        ]
        self.assertEqual(len(reveal_cells), 1)
        self.assertEqual(reveal_cells[0].get("outputs", []), [])
        # no code cell in the portable notebook carries baked-in outputs
        # (matches the established Exercise 2/3 portable-notebook convention)
        for c in self.cells:
            if c["cell_type"] == "code":
                self.assertEqual(c.get("outputs", []), [])

    def test_portable_no_local_absolute_paths_and_install_cell_present(self):
        self.assertNotIn(str(REPO_ROOT), self.code)
        self.assertNotIn("/Users/", self.code)
        self.assertIn("pip install", self.code)

    def test_portable_activities_replaced_by_runnable_python_no_iframe(self):
        self.assertNotIn("<iframe", self.md)
        self.assertNotIn("<iframe", self.code)
        # the same three Python equivalents are still runnable
        self.assertIn("cross_validate(", self.code)
        self.assertIn("GridSearchCV(", self.code)
        self.assertIn("STUDENT_CHOICE_K", self.code)


class LaunchButtonsAndPlaceholders(unittest.TestCase):
    # -- 27. Exercise 4 launch links are correct -------------------------------

    def test_exercise_4_launch_links_are_correct(self):
        self.assertIn(
            '"chapters/chapter_04/exercise_04.html":\n'
            '      "book/downloads/chapter_04/exercise_04_portable.ipynb",',
            LAUNCH_BUTTONS_JS,
        )
        nb = nbformat.read(NB_PATH, as_version=4)
        card = _src(nb.cells[1])
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/"
            "blob/main/book/downloads/chapter_04/exercise_04_portable.ipynb",
            card,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_04/exercise_04_portable.ipynb",
            card,
        )
        portable_banner = _src(nbformat.read(PORTABLE_PATH, as_version=4).cells[0])
        self.assertIn(
            "https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html",
            portable_banner,
        )

    # -- 28. Exercises 5-12 remain placeholders without launch buttons --------

    def test_exercises_5_through_12_remain_placeholders_without_launch_buttons(self):
        for n in range(5, 13):
            page = f"chapters/chapter_{n:02d}/exercise_{n:02d}.html"
            self.assertNotIn(page, LAUNCH_BUTTONS_JS)
            md_path = REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.md"
            self.assertTrue(md_path.exists())
            ipynb_path = (
                REPO_ROOT / "book" / "chapters" / f"chapter_{n:02d}" / f"exercise_{n:02d}.ipynb"
            )
            self.assertFalse(ipynb_path.exists())
            portable_path = (
                REPO_ROOT / "book" / "downloads" / f"chapter_{n:02d}" / f"exercise_{n:02d}_portable.ipynb"
            )
            self.assertFalse(portable_path.exists())


class SyllabusUnchanged(unittest.TestCase):
    # -- 29. Syllabus source is unchanged --------------------------------------

    def test_syllabus_source_unchanged_since_wp27_base_commit(self):
        diff = _git("diff", f"{WP27_BASE_COMMIT}..HEAD", "--", "book/syllabus.md")
        self.assertEqual(diff, "", diff)


class WP27RGridsAndActivity(unittest.TestCase):
    """WP27R spec section 9: the densified grids, the revealed third panel,
    the replaced diagram, and the surrounding prose/config changes."""

    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.md = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "markdown")
        cls.code = "\n\n".join(_src(c) for c in cls.cells if c["cell_type"] == "code")
        cls.all_output = _collect_output(cls.nb)
        cls.audit = json.loads(
            (REPO_ROOT / "scripts" / "wp27_validation_audit_result.json").read_text(encoding="utf-8")
        )

    # -- hidden-test candidate grid ------------------------------------------

    def test_hidden_test_candidate_grid_includes_the_required_dense_values(self):
        b = self.audit["part_b_train_val_test_tuning"]
        self.assertTrue(WP27R_REQUIRED_LOCK_TEST_KS.issubset(set(b["candidate_ks"])))
        self.assertEqual(LOCK_TEST_CONFIG["defaultK"], b["validation_selected_k"])

    def test_no_stale_sparse_12_outside_the_nested_cv_grid(self):
        b = self.audit["part_b_train_val_test_tuning"]
        self.assertNotIn(12, b["candidate_ks"])
        # 12 remains legitimate inside the *different*, denser nested-CV grid.
        c = self.audit["part_c_nested_cv"]
        self.assertIn(12, c["candidate_ks"])

    def test_candidate_grid_consistent_across_script_notebook_and_widget_data(self):
        b = self.audit["part_b_train_val_test_tuning"]
        self.assertIn(f"CANDIDATE_KS = {b['candidate_ks']}", self.code)
        data = json.loads(
            (REPO_ROOT / "book" / "_static" / "widgets" / "data" / "wp27_validation_lock_test.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["candidateKs"], b["candidate_ks"])

    # -- three-panel reveal, hidden until locked -----------------------------

    def test_third_panel_trace_is_constructed_only_when_locked(self):
        # The test trace literally does not exist as an object until `locked`
        # is true -- no test value can reach a Plotly trace, hover template,
        # or DOM node before that.
        self.assertIn("if (locked) {", LOCK_TEST_TS)
        traces_block = LOCK_TEST_TS.split("const traces: PlotData[] = [trainTrace, valTrace];", 1)[1]
        traces_block = traces_block.split("const [yMin, yMax]", 1)[0]
        self.assertIn("if (locked) {", traces_block)
        self.assertIn("testMseIfLocked", traces_block)

    def test_selected_k_markers_drawn_on_every_panel(self):
        self.assertIn("markerShapes", LOCK_TEST_TS)
        self.assertIn("data.trainingSelectedK", LOCK_TEST_TS)
        self.assertIn("data.validationSelectedK", LOCK_TEST_TS)
        self.assertIn("chosenK", LOCK_TEST_TS)

    def test_methodology_warning_present_and_teaching_only(self):
        self.assertIn("validation-lock-test-methodology-warning", LOCK_TEST_TS)
        self.assertIn("teaching demonstration", LOCK_TEST_TS)
        self.assertIn("must not change now", LOCK_TEST_TS)

    def test_post_reveal_reflection_prompts_configured_and_distinct_from_pre_lock(self):
        pre = set(LOCK_TEST_CONFIG["reflectionPrompts"])
        post = set(LOCK_TEST_CONFIG["postRevealReflectionPrompts"])
        self.assertTrue(pre.isdisjoint(post))
        post_text = " ".join(LOCK_TEST_CONFIG["postRevealReflectionPrompts"]).lower()
        self.assertIn("resemble", post_text)
        self.assertIn("minimize test mse", post_text)
        self.assertIn("must you not switch", post_text)
        self.assertIn("meaning of the test set", post_text)

    def test_notebook_has_a_second_think_first_block_after_the_activity(self):
        self.assertEqual(self.md.count("```{admonition} Think"), 2)
        self.assertIn("Think again, after revealing", self.md)
        think_again = self.md.split("Think again, after revealing", 1)[1].split("```", 1)[0]
        self.assertIn("resemble", think_again)
        self.assertIn("not switch to it now", think_again)

    # -- optional Python reproduction, collapsed on the website --------------

    def test_optional_python_section_title_and_blurb(self):
        self.assertIn(
            "### Optional: Reproduce the Tuning Activity in Python\n"
            "\n"
            "The interactive activity above contains the main lesson. Expand this\n"
            "optional section if you want to reproduce the analysis in Python.",
            self.md,
        )

    def test_optional_reproduction_cells_are_hide_cell_on_the_website(self):
        idx = next(i for i, c in enumerate(self.cells) if "STUDENT_CHOICE_K = validation_selected_k" in _src(c))
        fit_val_idx = next(
            i for i, c in enumerate(self.cells) if "X_fit, X_val, y_fit, y_val = train_test_split" in _src(c)
        )
        for i in (fit_val_idx, idx):
            self.assertIn("hide-cell", self.cells[i]["metadata"].get("tags", []), f"cell {i} not hide-cell")

    def test_optional_section_does_not_hide_the_conceptual_explanation(self):
        # The "a few things to hold onto" interpretation is a markdown cell
        # (never collapsible by hide-cell) placed after the optional code.
        interp_idx = next(i for i, c in enumerate(self.cells) if "A few things to hold onto" in _src(c))
        self.assertEqual(self.cells[interp_idx]["cell_type"], "markdown")

    # -- nested-CV diagram ----------------------------------------------------

    def test_mermaid_flowchart_removed(self):
        self.assertNotIn("```mermaid", self.md)
        self.assertNotIn("```mermaid", self.code)

    def test_native_diagram_present_with_required_operation_labels(self):
        self.assertIn('class="ml-ncv-diagram"', self.md)
        self.assertIn("Outer cross-validation", self.md)
        self.assertIn("Inner cross-validation", self.md)
        self.assertIn("Choose <code>k</code>", self.md)
        self.assertIn("Refit the selected <code>k</code> on all outer-training data", self.md)
        self.assertIn("Evaluate the tuning procedure", self.md)
        # never a raster screenshot
        self.assertNotIn("<img", self.md)

    def test_diagram_theme_tokens_defined_for_light_and_dark(self):
        self.assertIn("--ml-ncv-outer-train", CUSTOM_CSS)
        self.assertIn("--ml-ncv-outer-test", CUSTOM_CSS)
        self.assertIn("--ml-ncv-inner-train", CUSTOM_CSS)
        self.assertIn("--ml-ncv-inner-val", CUSTOM_CSS)
        dark_block = CUSTOM_CSS.split('html[data-theme="dark"] {', 1)[1].split("\n}\n", 1)[0]
        self.assertIn("--ml-ncv-outer-train", dark_block)
        # every colored diagram element has a static fallback for contexts
        # with no stylesheet at all (portable notebook, GitHub).
        self.assertIn("var(--ml-ncv-outer-train, #", self.md)

    # -- nested-CV candidate grid ---------------------------------------------

    def test_nested_cv_grid_denser_between_10_and_30(self):
        c = self.audit["part_c_nested_cv"]
        in_range = [k for k in c["candidate_ks"] if 10 <= k <= 30]
        self.assertGreaterEqual(len(in_range), 8, c["candidate_ks"])
        self.assertIn(f"NESTED_CANDIDATE_KS = {c['candidate_ks']}", self.code)
        self.assertEqual(NESTED_CV_DATA["candidateKs"], c["candidate_ks"])

    def test_displayed_selected_k_table_matches_regenerated_audit(self):
        c = self.audit["part_c_nested_cv"]
        self.assertIn(f"selected k per outer fold: {c['selected_k_per_fold']}", self.all_output)
        mean_mse_1dp = f"{c['mean_outer_test_mse']:.1f}"
        self.assertIn(f"mean outer-test MSE = {mean_mse_1dp}", self.all_output)

    def test_prose_reports_the_real_outcome_without_falsifying_it(self):
        c = self.audit["part_c_nested_cv"]
        if c["selected_k_varies_across_folds"]:
            self.assertIn("no longer all agree", self.md)
            self.assertNotIn("all five outer folds happened to select the same", self.md)
        else:
            self.assertIn("happened to select the same", self.md)
        # the general possibility is still phrased as "can", not "will"
        self.assertIn("outer folds *can* select different", self.md)

    # -- untouched surfaces -----------------------------------------------

    def test_word_course_overview_script_untouched(self):
        diff = _git("diff", f"{WP27_BASE_COMMIT}..HEAD", "--", "scripts/build_course_overview_docx.py")
        self.assertEqual(diff, "", diff)


if __name__ == "__main__":
    unittest.main()
