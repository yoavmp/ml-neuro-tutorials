"""Offline assertions for book/chapters/chapter_08/exercise_08.ipynb (Exercise 8).

WP33 replaced the Exercise 8 placeholder with a notebook on unsupervised
learning: contrasting supervised/unsupervised learning, PCA (projection,
explained variance, loadings, reconstruction), a small simulated
projection-angle activity, PCA on the real ABIDE-II cortical-thickness
table, K-means clustering, an exploratory research example, a combined
PCA-and-K-means explorer, and PCA used before KNN regression -- a model
students already know -- in a leakage-safe supervised pipeline, compared
against KNN on the original standardized features. Hierarchical clustering,
dendrograms, t-SNE, UMAP, DBSCAN, Gaussian-mixture models, AdaBoost, and
principal component regression (PCR) are explicitly out of scope (PCR first
appears in Exercise 9).

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_08_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_08" / "exercise_08.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_08" / "exercise_08_portable.ipynb"
MANIFEST = json.loads((REPO_ROOT / "book" / "config" / "abide_modeling.json").read_text())
LAUNCH_BUTTONS_JS = (REPO_ROOT / "book" / "_static" / "launch-buttons.js").read_text(encoding="utf-8")
PCA_RESULT = json.loads((REPO_ROOT / "scripts" / "pca_kmeans_audit_result.json").read_text())

SECTION_TITLES = [
    "## 1. Learning Without a Target",
    "## 2. PCA: Representing Many Features with Fewer Dimensions",
    "## 3. Interactive Activity -- Find the Best Projection",
    "## 4. PCA with ABIDE-II Neuroimaging Data",
    "## 5. Clustering and K-Means",
    "## 6. Research Example -- Exploring Neuroanatomical Profiles",
    "## 7. Interactive Activity -- Explore PCA and K-Means",
    "## 8. Using PCA in a Supervised Pipeline",
    "## 9. What Should We Remember?",
]

OUT_OF_SCOPE_NEEDLES = (
    "hierarchical clustering",
    "dendrogram",
    "t-sne",
    "tsne",
    "umap",
    "dbscan",
    "gaussian mixture",
    "gaussianmixture",
    "adaboost",
)


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
        self.assertEqual(_src(self.cells[0]).strip(), "# Exercise 8: Unsupervised Learning")

    def test_green_run_or_download_admonition_is_second_cell(self):
        src = _src(self.cells[1])
        self.assertIn("```{admonition} Run or download this notebook", src)
        self.assertIn(":class: how-to-use", src)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/"
            "book/downloads/chapter_08/exercise_08_portable.ipynb",
            src,
        )

    def test_what_this_notebook_covers_present_and_concise(self):
        idx = _index_of_cell_starting_with(self.cells, "## What this notebook covers")
        src = _src(self.cells[idx])
        self.assertLess(len(src), 1200)
        self.assertIn("target", src.lower())

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

    def test_no_out_of_scope_methods_anywhere(self):
        for needle in OUT_OF_SCOPE_NEEDLES:
            self.assertNotIn(needle, self.full_source_lower, needle)

    def test_pcr_is_not_introduced_here(self):
        # WP34: principal component regression must first appear in
        # Exercise 9, not Exercise 8. Exercise 8's supervised section now
        # pairs PCA with KNeighborsRegressor instead.
        self.assertNotIn("pcr", self.full_source_lower)
        self.assertNotIn("principal component regression", self.full_source_lower)
        self.assertNotIn("linearregression", self.full_source_lower)
        self.assertNotIn("linear regression", self.full_source_lower)

    def test_no_stored_error_outputs(self):
        _collect_output(self.nb)  # raises AssertionError on any error output


class DataLoadingAndTerminology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.full_source_lower = "\n".join(_src(c) for c in cls.cells).lower()

    def test_data_loading_cell_is_hidden_on_the_website(self):
        loading_cells = [c for c in self.cells if c["cell_type"] == "code" and "pd.read_csv" in _src(c)]
        self.assertGreaterEqual(len(loading_cells), 1)
        for c in loading_cells:
            self.assertIn("hide-input", c.get("metadata", {}).get("tags", []))

    def test_recorded_cohort_and_feature_counts(self):
        out = _collect_output(self.nb)
        self.assertIn("1004 participants", out)
        self.assertIn("360 cortical-thickness predictors", out)

    def test_pca_is_described_as_feature_extraction_not_selection(self):
        idx = _index_of_cell_starting_with(self.cells, "## 2. PCA: Representing Many Features")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("dimensionality reduction and feature extraction", src)
        self.assertIn("not feature selection", src)

    def test_external_variables_never_described_as_clustering_inputs(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. Research Example")
        src = _src(self.cells[idx]).lower()
        self.assertIn("diagnosis, sex, site, and age never enter steps 1-4", src)


class ProjectionActivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_iframe_points_at_the_projection_widget(self):
        iframe_cell = next(c for c in self.cells if c["cell_type"] == "markdown" and "pca_projection.json" in _src(c))
        self.assertIn(
            'title="Interactive projection-angle activity for a small simulated two-dimensional dataset"',
            _src(iframe_cell),
        )

    def test_reproduction_cell_is_hide_cell_and_matches_the_manifest(self):
        repro = next(c for c in self.cells if c["cell_type"] == "code" and "PROJ_SEED" in _src(c))
        self.assertIn("hide-cell", repro.get("metadata", {}).get("tags", []))
        proj = MANIFEST["unsupervised"]["projection_activity"]
        src = _src(repro)
        self.assertIn(f"PROJ_SEED = {proj['seed']}", src)
        self.assertIn(f"PROJ_N = {proj['n_observations']}", src)

    def test_does_not_reveal_true_pc1_before_the_reveal_action(self):
        idx = _index_of_cell_starting_with(self.cells, "## 3. Interactive Activity")
        next_idx = _index_of_cell_starting_with(self.cells, "## 4. PCA with ABIDE-II")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx]).lower()
        self.assertNotIn("28.4", combined)  # the true angle is never stated in surrounding prose


class AbideePca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_standardization_explained_before_pca_fit(self):
        idx = _index_of_cell_starting_with(self.cells, "## 4. PCA with ABIDE-II")
        src = _src(self.cells[idx]).lower()
        self.assertIn("standardize", src)

    def test_pca_fit_cell_is_hidden_and_uses_standard_scaler(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "pca = PCA(n_components=50" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))
        self.assertIn("StandardScaler", _src(cell))

    def test_recorded_explained_variance_matches_the_audit(self):
        out = _collect_output(self.nb)
        pca = PCA_RESULT["pca"]
        self.assertIn(f"PC1 explained variance = {pca['explained_variance_ratio'][0]:.1%}", out)
        for k in (2, 5, 10, 20, 50):
            self.assertIn(
                f"cumulative explained variance through PC{k} = {pca['cumulative_at'][str(k)]:.1%}", out
            )

    def test_grouped_loading_matches_the_audit_and_uses_mean_absolute_value(self):
        out = _collect_output(self.nb)
        grouped = PCA_RESULT["pca"]["grouped_mean_abs_loading"]
        for group in ("frontal", "parietal", "temporal", "occipital"):
            pc1 = grouped[group]["PC1"]
            pc2 = grouped[group]["PC2"]
            self.assertIn(f"{group:10s} PC1={pc1:.4f}  PC2={pc2:.4f}", out)
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "group_mean_abs_loading" in _src(c))
        self.assertIn("np.abs(loadings", _src(cell))
        self.assertNotIn("np.sum(loadings", _src(cell))

    def test_grouped_loading_uses_the_same_anatomical_groups_as_exercise_5(self):
        ex5 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_05" / "exercise_05.ipynb", as_version=4)
        ex5_source = "\n".join(_src(c) for c in ex5.cells)
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "ANATOMICAL_ROIS" in _src(c))
        src = _src(cell)
        # Exercise 5's own frontal-bundle ROI list appears verbatim in Exercise
        # 8's grouped-loading cell -- same bundle definitions, not redefined
        # independently.
        self.assertIn('"46", "9-46d"', ex5_source)
        self.assertIn('"46", "9-46d"', src)

    def test_interpretation_questions_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 4. PCA with ABIDE-II")
        next_idx = _index_of_cell_starting_with(self.cells, "## 5. Clustering and K-Means")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertIn("global cortical-thickness pattern", combined)
        self.assertIn("scientifically useful", combined)
        self.assertIn("hidden when 360 dimensions", combined)


class ClusteringConcept(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_kmeans_steps_are_explicit(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Clustering and K-Means")
        src = _src(self.cells[idx]).lower()
        for phrase in ("initialize", "assign each participant", "update each center", "repeat"):
            self.assertIn(phrase, src)

    def test_no_single_objectively_correct_k_caveat_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 5. Clustering and K-Means")
        src = _src(self.cells[idx]).lower()
        self.assertIn("no single objectively correct", src)
        self.assertIn("does not establish a biological subtype", src)


class ResearchExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_workflow_order_is_explicit(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. Research Example")
        src = _src(self.cells[idx])
        for step in (
            "standardize the cortical-thickness features",
            "fit PCA without using diagnosis",
            "retain a chosen number of components",
            "fit K-means in that retained component space",
            "only then compare the resulting clusters",
        ):
            self.assertIn(step, src)

    def test_kmeans_uses_explicit_n_init_and_random_state(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "demo_kmeans = KMeans" in _src(c))
        src = _src(cell)
        self.assertIn("n_init=10", src)
        self.assertIn("random_state=0", src)

    def test_arbitrary_cluster_label_caution_is_visible(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. Research Example")
        next_idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx]).lower()
        self.assertIn("carry no inherent order or meaning", combined)
        self.assertNotIn("autism subtypes\n", combined.replace("does not attempt", ""))

    def test_never_calls_the_clusters_autism_subtypes(self):
        idx = _index_of_cell_starting_with(self.cells, "## 6. Research Example")
        next_idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity")
        combined = _norm_ws("\n".join(_src(c) for c in self.cells[idx:next_idx])).lower()
        # The phrase "autism subtypes" is only permitted as part of a denial
        # ("does not make them autism subtypes"), never as a flat assertion
        # that the clusters ARE autism subtypes.
        self.assertNotIn("are autism subtypes", combined)
        self.assertIn("does not make them autism subtypes", combined)


class PcaKmeansExplorerActivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_iframe_points_at_the_explorer_widget(self):
        iframe_cell = next(
            c for c in self.cells if c["cell_type"] == "markdown" and "pca_kmeans_explorer.json" in _src(c)
        )
        self.assertIn(
            'title="Interactive PCA and K-means explorer for ABIDE-II participants"',
            _src(iframe_cell),
        )

    def test_states_clustering_uses_every_retained_component(self):
        idx = _index_of_cell_starting_with(self.cells, "## 7. Interactive Activity")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("every retained component you select", src)
        self.assertIn("only pc1 and pc2", src)


class SupervisedPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_pipeline_code_block_is_shown(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        src = _src(self.cells[idx])
        self.assertIn('("scale", StandardScaler())', src)
        self.assertIn('("pca", PCA())', src)
        self.assertIn('("model", KNeighborsRegressor())', src)

    def test_teaching_points_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        src = _norm_ws(_src(self.cells[idx])).lower()
        self.assertIn("euclidean distance", src)
        self.assertIn("feature extraction, not feature selection", src)
        self.assertIn("cross-validation on the training-and-validation data only", src)
        self.assertIn("not guaranteed to help knn", src)

    def test_split_cell_matches_the_manifest_holdout_split(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "X_train, X_test, y_train, y_test, groups_train" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))
        src = _src(cell)
        holdout = MANIFEST["protocol"]["holdout_split"]
        self.assertIn(f'test_size=0.25, random_state={holdout["random_state"]}', src)

    def test_component_and_k_grids_match_the_spec(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "component_grid = [" in _src(c))
        self.assertIn("hide-input", cell.get("metadata", {}).get("tags", []))
        sup = MANIFEST["unsupervised"]["supervised_pipeline"]
        self.assertIn(f"component_grid = {sup['component_grid']}", _src(cell))
        self.assertIn(f"k_grid = {sup['k_grid']}", _src(cell))

    def test_cv_uses_5_folds_and_development_partition_only(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "component_grid = [" in _src(c))
        src = _src(cell)
        self.assertIn("KFold(n_splits=5", src)
        self.assertIn("cv.split(X_train)", src)

    def test_scaler_and_pca_are_fit_inside_the_pipeline_only(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "component_grid = [" in _src(c))
        src = _src(cell)
        # Every StandardScaler/PCA construction happens inside a Pipeline(...)
        # list, never as a free-standing fit on X_train before the loop.
        self.assertNotIn("StandardScaler().fit(X_train)", src)
        self.assertNotIn("PCA(", src.split("Pipeline([")[0])

    def test_raw_feature_knn_comparison_present_under_the_same_folds(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "component_grid = [" in _src(c))
        src = _src(cell)
        self.assertIn("raw_knn_rows", src)
        self.assertIn("fold_splits", src.split("raw_knn_rows")[1].split("results_df")[0])

    def test_results_and_selection_are_visible(self):
        cell = next(c for c in self.cells if c["cell_type"] == "code" and "results_df.round(3)" in _src(c))
        self.assertNotIn("hide-input", cell.get("metadata", {}).get("tags", []))
        self.assertNotIn("hide-cell", cell.get("metadata", {}).get("tags", []))

    def test_recorded_selected_settings_and_test_metrics_match_the_audit(self):
        out = _collect_output(self.nb)
        sup = PCA_RESULT["supervised_pipeline"]
        self.assertIn(f"selected: n_components={sup['selected_n_components']}, k={sup['selected_k']}", out)
        self.assertIn(f"raw-feature KNN selected: k={sup['selected_raw_k']}", out)

    def test_does_not_claim_pca_must_improve_prediction(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        full = _norm_ws("\n".join(_src(c) for c in self.cells[idx:]))
        self.assertIn("not a guarantee", full)
        self.assertNotIn("PCA always improves", full)
        self.assertNotIn("PCA must improve", full)

    def test_leakage_explanation_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        full = "\n".join(_src(c) for c in self.cells[idx:]).lower()
        self.assertIn("leaks information", full)
        self.assertIn("never sees the target", full)

    def test_think_first_question_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        full = "\n".join(_src(c) for c in self.cells[idx:])
        self.assertIn("```{admonition} Think first", full)
        self.assertIn(
            "Why might PCA help KNN more directly than it helps a model that does not\n"
            "calculate distances between participants?",
            full,
        )

    def test_only_one_think_first_in_this_section(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        next_idx = _index_of_cell_starting_with(self.cells, "## 9. What Should We Remember?")
        combined = "\n".join(_src(c) for c in self.cells[idx:next_idx])
        self.assertEqual(combined.count("```{admonition} Think first"), 1)

    def test_no_new_interactive_activity_in_this_section(self):
        idx = _index_of_cell_starting_with(self.cells, "## 8. Using PCA in a Supervised Pipeline")
        next_idx = _index_of_cell_starting_with(self.cells, "## 9. What Should We Remember?")
        for c in self.cells[idx:next_idx]:
            self.assertNotIn("<iframe", _src(c))


class ScopeExclusions(unittest.TestCase):
    def test_no_out_of_scope_methods_in_widget_configs(self):
        for path in [
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "pca_projection.json",
            REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "pca_kmeans_explorer.json",
        ]:
            text = path.read_text(encoding="utf-8").lower()
            for needle in OUT_OF_SCOPE_NEEDLES:
                self.assertNotIn(needle, text, (path, needle))


class Summary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells

    def test_takeaway_questions_present(self):
        idx = _index_of_cell_starting_with(self.cells, "## 9. What Should We Remember?")
        src = _src(self.cells[idx])
        self.assertIn("### Questions to take away", src)
        for n in range(1, 7):
            self.assertIn(f"{n}. ", src)


class LaunchButtonsAndPortable(unittest.TestCase):
    def test_registered_in_launch_buttons_js(self):
        self.assertIn('"chapters/chapter_08/exercise_08.html"', LAUNCH_BUTTONS_JS)
        self.assertIn('"book/downloads/chapter_08/exercise_08_portable.ipynb"', LAUNCH_BUTTONS_JS)

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
        # Exercise 9 gained a portable notebook and launch button in WP34,
        # Exercise 10 in WP38 (see test_exercise_09_notebook.py,
        # test_exercise_10_notebook.py); only 11-12 remain placeholders.
        for n in range(11, 13):
            page = f'"chapters/chapter_{n:02d}/exercise_{n:02d}.html"'
            self.assertNotIn(page, LAUNCH_BUTTONS_JS)


if __name__ == "__main__":
    unittest.main()
