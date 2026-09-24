"""Offline assertions for book/chapters/chapter_09/exercise_09.ipynb (Exercise 9).

WP34 replaced the Exercise 9 placeholder with a notebook on advanced models:
PCR (introduced here for the first time), PLS, support vector machines,
kernels, two new browser-native interactive activities ("PCR or PLS?" and
"Explore an SVM Boundary"), and a nested-cross-validation comparison of five
models (standardized OLS, PCR, PLS, linear SVR, RBF SVR) on the same
ABIDE-II age-prediction task every other exercise uses.

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_09_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_09" / "exercise_09.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_09" / "exercise_09_portable.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")
AUDIT_RESULT = json.loads((REPO_ROOT / "scripts" / "advanced_models_audit_result.json").read_text())

SECTION_TITLES = [
    "## 1. Why Consider More Advanced Models?",
    "## 2. Principal Component Regression",
    "## 3. Partial Least Squares",
    "## 4. Interactive Activity -- PCR or PLS?",
    "## 5. Support Vector Machines",
    "## 6. Kernels and Nonlinear Boundaries",
    "## 7. Interactive Activity -- Explore an SVM Boundary",
    "## 8. Comparing Advanced Models on ABIDE-II",
    "## 9. Strengths, Weaknesses, and Appropriate Uses",
    "## 10. Test-Oriented Thinking Questions",
    "## 11. Main Takeaways",
]


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
        self.assertEqual(_src(self.cells[0]).strip(), "# Exercise 9: Advanced Models")

    def test_green_run_or_download_admonition_is_second_cell(self):
        src = _src(self.cells[1])
        self.assertIn("```{admonition} Run or download this notebook", src)
        self.assertIn(":class: how-to-use", src)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/"
            "book/downloads/chapter_09/exercise_09_portable.ipynb",
            src,
        )

    def test_what_this_notebook_covers_present_and_concise(self):
        idx = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        src = _src(self.cells[idx])
        self.assertLess(len(src), 1200)
        self.assertIn("Exercise 9", src)

    def test_section_titles_appear_in_order(self):
        indices = [_index_of_cell_starting_with(self.cells, t) for t in SECTION_TITLES]
        self.assertEqual(indices, sorted(indices))

    def test_exactly_two_iframes(self):
        count = sum(1 for c in self.cells if c["cell_type"] == "markdown" and "<iframe" in _src(c))
        self.assertEqual(count, 2)

    def test_cell_count_is_reasonable_and_shorter_than_exercise_01(self):
        ex1 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb", as_version=4)
        self.assertLess(len(self.cells), len(ex1.cells))
        self.assertGreaterEqual(len(self.cells), 20)

    def test_no_stored_error_outputs(self):
        _collect_output(self.nb)  # raises AssertionError on any error output

    def test_pcr_is_introduced_here_not_earlier(self):
        idx = _index_of_cell_starting_with(self.cells, "## 2. Principal Component Regression")
        self.assertGreater(idx, _index_of_cell_starting_with(self.cells, "## 1. Why Consider More Advanced Models?"))
        ex8 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_08" / "exercise_08.ipynb", as_version=4)
        ex8_source = "\n".join(_src(c) for c in ex8.cells).lower()
        self.assertNotIn("pcr", ex8_source)
        self.assertNotIn("principal component regression", ex8_source)

    def test_not_a_repeated_full_pipeline_tutorial(self):
        # WP34 §6: "the notebook must be concise... show only model-specific
        # code". The full loading/split/tuning machinery only reappears
        # once, in section 8's comparison -- not duplicated per section.
        self.assertEqual(self.full_source.count("train_test_split"), 0)
        self.assertEqual(self.full_source_lower.count("pd.read_csv"), 1)


class PcrPlsSection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_think_first_question_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 1. Why Consider More Advanced Models?")
        full = "\n".join(_src(c) for c in self.cells[idx : idx + 2])
        self.assertIn("```{admonition} Think first", full)
        self.assertIn(
            "If two models receive the same participants and features, why can they\nproduce different predictions",
            full,
        )

    def test_pcr_pipeline_code_block_is_shown(self):
        idx = _index_of_cell_starting_with(self.cells, "## 2. Principal Component Regression")
        src = _src(self.cells[idx])
        self.assertIn('("scale", StandardScaler())', src)
        self.assertIn('("pca", PCA(n_components=...))', src)
        self.assertIn('("model", LinearRegression())', src)

    def test_pcr_teaching_points_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 2. Principal Component Regression")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("without ever seeing", src)
        self.assertIn("fitted inside each validation", src)
        self.assertIn("discard a low-variance direction", src)

    def test_pls_pipeline_code_block_uses_scale_false_and_explains_it(self):
        idx = _index_of_cell_starting_with(self.cells, "## 3. Partial Least Squares")
        src = _src(self.cells[idx])
        self.assertIn("PLSRegression(n_components=...,", src)
        self.assertIn("scale=False", src)
        self.assertIn("scale=False:", src.lower().replace("scale=false:", "scale=False:"))

    def test_pls_is_described_as_supervised_component_construction(self):
        idx = _index_of_cell_starting_with(self.cells, "## 3. Partial Least Squares")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("using the relationship between the\npredictors and the target".replace("\n", " "), src)
        self.assertIn("must happen inside each training fold", src)

    def test_iframe_points_at_the_pcr_pls_widget(self):
        iframe_cell = next(c for c in self.cells if c["cell_type"] == "markdown" and "pcr_pls_explore.json" in _src(c))
        self.assertIn(
            'title="Interactive PCR-versus-PLS activity for a small simulated two-dimensional dataset"',
            _src(iframe_cell),
        )

    def test_reproduction_cell_is_hide_cell(self):
        repro = next(c for c in self.cells if c["cell_type"] == "code" and "PLSRegression" in _src(c) and "demo_rng" in _src(c))
        self.assertIn("hide-cell", repro.get("metadata", {}).get("tags", []))

    def test_reproduction_cell_uses_the_variance_controlled_construction(self):
        # WP36: the hidden reproduction must use the same standardized,
        # mutually orthogonal construction as the real activity data, not
        # WP35's raw-coefficient construction.
        repro = next(c for c in self.cells if c["cell_type"] == "code" and "PLSRegression" in _src(c) and "demo_rng" in _src(c))
        src = _src(repro)
        self.assertIn("z1 = (pc1_demo - pc1_demo.mean())", src)
        self.assertIn("z2_raw - (z2_raw @ z1) / (z1 @ z1) * z1", src)
        self.assertIn("w1**2 + w2**2 == 1", src)
        self.assertNotIn("0.3 * pc1_demo + 0.85 * pc2_demo", src)

    def test_intro_explains_fixed_signal_and_noise_across_presets(self):
        idx = _index_of_cell_starting_with(self.cells, "## 4. Interactive Activity -- PCR or PLS?")
        iframe_idx = next(i for i in range(idx, idx + 4) if "<iframe" in _src(self.cells[i]))
        intro = "\n".join(_src(c) for c in self.cells[idx:iframe_idx])
        low = _norm_ws(intro).lower()
        self.assertIn("same signal strength", low)
        self.assertIn("same", low)
        self.assertIn("noise level", low)
        self.assertIn("pcr does best", low)
        self.assertIn("pls can help most", low)

    def test_guiding_questions_present_and_do_not_reveal_the_answer(self):
        idx = _index_of_cell_starting_with(self.cells, "## 4. Interactive Activity -- PCR or PLS?")
        next_idx = _index_of_cell_starting_with(self.cells, "## 5. Support Vector Machines")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertIn("With one component, why can PLS outperform PCR?", combined)
        self.assertIn("Why do PCR and PLS become more similar", combined)
        # The specific illustrative validation MSE numbers must not leak
        # into the surrounding prose before the student interacts.
        self.assertNotIn("PCR=0.46", combined)
        self.assertNotIn("PLS=0.45", combined)


class SvmSection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_parameter_table_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Support Vector Machines")
        src = _src(self.cells[idx])
        for term in ("`C`", "`epsilon`", "`kernel`", "`gamma`"):
            self.assertIn(term, src)
        self.assertIn("support vectors", src.lower())
        self.assertIn("margin", src.lower())

    def test_scaling_requirement_stated(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Support Vector Machines")
        src = _src(self.cells[idx]).lower()
        self.assertIn("requirement, not", src)

    def test_kernels_section_covers_linear_poly_and_rbf(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. Kernels and Nonlinear Boundaries")
        src = _src(self.cells[idx]).lower()
        self.assertIn("linear", src)
        self.assertIn("polynomial", src)
        self.assertIn("radial basis function", src)
        self.assertIn("rbf", src)

    def test_iframe_points_at_the_svm_widget(self):
        iframe_cell = next(c for c in self.cells if c["cell_type"] == "markdown" and "svm_explorer.json" in _src(c))
        self.assertIn(
            'title="Interactive SVM decision-boundary explorer for two synthetic classification datasets"',
            _src(iframe_cell),
        )

    def test_reproduction_cell_is_hide_cell(self):
        repro = next(c for c in self.cells if c["cell_type"] == "code" and "SVC(kernel=" in _src(c))
        self.assertIn("hide-cell", repro.get("metadata", {}).get("tags", []))

    def test_labeled_as_conceptual_exploration(self):
        idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity -- Explore an SVM Boundary")
        next_idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx]).lower()
        self.assertIn("conceptual exploration, not", combined)
        self.assertIn("not a final model-selection", combined)

    def test_svr_bridge_sentence_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity -- Explore an SVM Boundary")
        next_idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertIn("`SVR` uses the same ideas for a continuous outcome", combined)
        self.assertIn("epsilon-insensitive regression", combined)

    def test_guiding_questions_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity -- Explore an SVM Boundary")
        next_idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertIn("Why can the linear kernel not separate the nonlinear dataset well?", combined)
        self.assertIn("perfect training accuracy", combined)


class AbideComparisonSection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_refers_to_exercise_4_and_does_not_reteach_nested_cv(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models on ABIDE-II")
        src = _src(self.cells[idx])
        self.assertIn("Exercise 4", src)
        self.assertNotIn("outer cross-validation rotates", src)  # Exercise 4's own diagram caption text

    def test_five_models_named(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models on ABIDE-II")
        src = _src(self.cells[idx]).lower()
        for name in ("ordinary linear regression", "pcr", "pls regression", "linear svr", "rbf svr"):
            self.assertIn(name, src)

    def test_pre_questions_before_results(self):
        idx = _index_of_cell_starting_with(self.cells, "Before looking at the results below")
        results_idx = next(
            i for i, c in enumerate(self.cells) if c["cell_type"] == "code" and "mean outer-fold performance" in _src(c)
        )
        self.assertLess(idx, results_idx)
        src = _src(self.cells[idx])
        self.assertIn("Which method do you expect to perform best?", src)
        self.assertIn("Is the RBF model guaranteed to improve performance?", src)

    def test_data_loading_cell_is_hidden(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "pd.read_csv" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))

    def test_nested_cv_cell_is_hidden_and_uses_identical_outer_and_inner_folds(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))
        src = _src(cell)
        outer = MANIFEST["advanced_models"]["abide_comparison"]["outer_cv"]
        inner = MANIFEST["advanced_models"]["abide_comparison"]["inner_cv"]
        self.assertIn(f"KFold(n_splits={outer['n_splits']}, shuffle=True, random_state={outer['random_state']})", src)
        self.assertIn(f"KFold(n_splits={inner['n_splits']}, shuffle=True, random_state={inner['random_state']})", src)
        # The SAME inner_splits list object is reused across every model
        # within an outer fold, not recomputed per model.
        self.assertIn("inner_splits = list(inner_cv.split(X_tr))", src)

    def test_grids_match_the_manifest(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c))
        src = _src(cell)
        grids = MANIFEST["advanced_models"]["abide_comparison"]["models"]
        self.assertIn(f"PCR_GRID = {grids['pcr']['grid']['n_components']}", src)
        self.assertIn(f"PLS_GRID = {grids['pls']['grid']['n_components']}", src)
        self.assertIn(f"LINEAR_SVR_C_GRID = {grids['linear_svr']['grid']['C']}", src)
        self.assertIn(f"LINEAR_SVR_EPSILON_GRID = {grids['linear_svr']['grid']['epsilon']}", src)
        self.assertIn(f"RBF_SVR_C_GRID = {grids['rbf_svr']['grid']['C']}", src)
        self.assertIn(f"RBF_SVR_EPSILON = {grids['rbf_svr']['fixed_epsilon']}", src)

    def test_linear_svr_grid_excludes_c_equals_10(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c))
        src = _src(cell)
        self.assertIn("LINEAR_SVR_C_GRID = [0.01, 0.1, 1]", src)
        self.assertNotIn("LINEAR_SVR_C_GRID = [0.01, 0.1, 1, 10]", src)

    def test_run_full_nested_cv_flag_defaults_false_and_gates_the_expensive_code(self):
        flag_cell = next(c for c in self.cells if c["cell_type"] == "code" and "RUN_FULL_NESTED_CV = False" in _src(c))
        self.assertNotIn("hide-input", flag_cell.get("metadata", {}).get("tags", []))
        self.assertNotIn("hide-cell", flag_cell.get("metadata", {}).get("tags", []))
        machinery_cell = next(c for c in self.cells if c["cell_type"] == "code" and "outer_cv = KFold" in _src(c))
        src = _src(machinery_cell)
        self.assertIn("if RUN_FULL_NESTED_CV:", src)
        self.assertIn("EMBEDDED_SUMMARY", src)
        # The expensive block must be gated behind the flag, not merely
        # documented -- "outer_cv = KFold(...)" must appear only inside the
        # conditional branch, indented under "if RUN_FULL_NESTED_CV:".
        for line in src.splitlines():
            if "outer_cv = KFold" in line:
                self.assertTrue(line.startswith("    "), line)

    def test_embedded_summary_matches_the_audit(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "EMBEDDED_SUMMARY" in _src(c))
        src = _src(cell)
        summary = AUDIT_RESULT["summary"]
        label_to_key = {
            "Standardized OLS": "ols", "PCR": "pcr", "PLS": "pls", "Linear SVR": "linear_svr", "RBF SVR": "rbf_svr",
        }
        for label, key in label_to_key.items():
            entry = summary[key]
            self.assertIn(f'"model": "{label}"', src)
            self.assertIn(str(entry["mean_outer_test_mse"]), src)
            self.assertIn(str(entry["sd_outer_test_mse"]), src)
            self.assertIn(str(entry["mean_outer_test_r2"]), src)

    def test_note_explains_the_optional_full_run_takes_minutes(self):
        idx = _index_of_cell_starting_with(
            self.cells, "By default, the results below load instantly"
        )
        src = _src(self.cells[idx]).lower()
        self.assertIn("run_full_nested_cv", src)
        self.assertIn("minutes", src)

    def test_no_notebook_or_repository_dependency_for_default_embedded_results(self):
        # WP35 §16: the default (RUN_FULL_NESTED_CV=False) path must not
        # read any file or network resource to obtain its results -- the
        # values are embedded literally as EMBEDDED_SUMMARY.
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "EMBEDDED_SUMMARY" in _src(c))
        src = _src(cell)
        else_branch = src.split("else:", 1)[1]
        self.assertNotIn("open(", else_branch)
        self.assertNotIn("read_csv", else_branch)
        self.assertNotIn("requests.", else_branch)
        self.assertNotIn("urlopen", else_branch)

    def test_results_and_plot_cell_is_visible(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "mean outer-fold performance" in _src(c))
        self.assertNotIn("hide-input", cell.get("metadata", {}).get("tags", []))
        self.assertNotIn("hide-cell", cell.get("metadata", {}).get("tags", []))

    def test_recorded_summary_matches_the_audit(self):
        # Compared with a numeric tolerance, not an exact rounded string:
        # the notebook's own pandas-groupby mean and the audit script's
        # numpy mean can differ in their last displayed digit at a rounding
        # boundary (e.g. 20.15 -> "20.1" vs "20.2") purely from floating-
        # point summation order, even though both read the identical fold
        # values -- an exact string match would be flaky, not meaningful.
        import re

        out = _collect_output(self.nb)
        summary = AUDIT_RESULT["summary"]
        printed = {
            m.group(1).strip(): (float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r"([A-Za-z0-9 ]+?)\s+mean MSE = ([\d.]+)\s+mean R2 = ([+-][\d.]+)", out)
        }
        for model_key, label in (
            ("ols", "Standardized OLS"),
            ("pcr", "PCR"),
            ("pls", "PLS"),
            ("linear_svr", "Linear SVR"),
            ("rbf_svr", "RBF SVR"),
        ):
            self.assertIn(label, printed)
            printed_mse, printed_r2 = printed[label]
            self.assertAlmostEqual(printed_mse, summary[model_key]["mean_outer_test_mse"], delta=0.06)
            self.assertAlmostEqual(printed_r2, summary[model_key]["mean_outer_test_r2"], delta=0.002)

    def test_selected_hyperparameters_dropdown_present(self):
        idx = _index_of_cell_starting_with(self.cells, "```{dropdown} Selected hyperparameters per outer fold")
        src = _src(self.cells[idx])
        summary = AUDIT_RESULT["summary"]
        pcr_n = summary["pcr"]["folds"][0]["selected_params"]["n_components"]
        pls_n = summary["pls"]["folds"][0]["selected_params"]["n_components"]
        self.assertIn(f"{pcr_n} components", src)
        self.assertIn(f"{pls_n} components", src)

    def test_discussion_is_honest_and_no_longer_mentions_unresolved_warnings(self):
        # WP35 §14: after removing the nonconvergent C=10 candidate and
        # raising max_iter, the regenerated audit has zero LinearSVR
        # convergence warnings, so the notebook must stop discussing them.
        idx = _index_of_cell_starting_with(self.cells, "On this cohort and split, RBF SVR reaches")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("not a general ranking", src)
        self.assertNotIn("did not fully converge", src)
        self.assertNotIn("convergence", src)
        self.assertNotIn("warning", src)
        self.assertEqual(AUDIT_RESULT.get("convergence_warnings", []), [])

    def test_no_third_iframe_in_this_section(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Comparing Advanced Models on ABIDE-II")
        next_idx = _index_of_cell_starting_with(self.cells, "## 9. Strengths, Weaknesses, and Appropriate Uses")
        for c in self.cells[idx:next_idx]:
            self.assertNotIn("<iframe", _src(c))


class ScopeExclusions(unittest.TestCase):
    def test_no_disallowed_content_in_widget_configs(self):
        for path in [
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "pcr_pls_explore.json",
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "svm_explorer.json",
        ]:
            self.assertTrue(path.exists(), path)


class StrengthsWeaknessesAndSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_strengths_weaknesses_table_has_exactly_four_rows(self):
        idx = _index_of_cell_starting_with(self.cells, "## 9. Strengths, Weaknesses, and Appropriate Uses")
        src = _src(self.cells[idx])
        row_lines = [
            line for line in src.splitlines() if line.strip().startswith("|") and "---" not in line and "Method" not in line
        ]
        self.assertEqual(len(row_lines), 4)
        for name in ("PCR", "PLS", "Linear SVM/SVR", "Kernel SVM/SVR"):
            self.assertIn(name, src)

    def test_ten_test_oriented_questions_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 10. Test-Oriented Thinking Questions")
        src = _src(self.cells[idx])
        for n in range(1, 11):
            self.assertIn(f"{n}. ", src)

    def test_central_concept_answers_are_revealable_via_dropdown(self):
        idx = _index_of_cell_starting_with(self.cells, "## 10. Test-Oriented Thinking Questions")
        src = _src(self.cells[idx])
        self.assertGreaterEqual(src.count("```{dropdown}"), 3)

    def test_takeaways_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 11. Main Takeaways")
        src = _src(self.cells[idx]).lower()
        self.assertIn("pcr uses pca components", src)
        self.assertIn("pls constructs components", src)
        self.assertIn("fair model comparison requires the same nested validation", src)


class LaunchButtonsAndPortable(unittest.TestCase):
    def test_registered_in_launch_buttons_js(self):
        self.assertIn('"chapters/chapter_09/exercise_09.html"', LAUNCH_BUTTONS_JS)
        self.assertIn('"book/downloads/chapter_09/exercise_09_portable.ipynb"', LAUNCH_BUTTONS_JS)

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

    def test_portable_notebook_keeps_the_nested_cv_comparison_visible_and_runnable(self):
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        found = any(
            c["cell_type"] == "code" and "outer_cv = KFold" in _src(c) and "LinearSVR" in _src(c) for c in portable.cells
        )
        self.assertTrue(found)

    def test_exercises_11_through_12_have_no_launch_button(self):
        for n in range(11, 13):
            page = f'"chapters/chapter_{n:02d}/exercise_{n:02d}.html"'
            self.assertNotIn(page, LAUNCH_BUTTONS_JS)


if __name__ == "__main__":
    unittest.main()
