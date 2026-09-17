"""Offline assertions for book/chapters/chapter_03/exercise_03.ipynb (Exercise 3).

WP25 moved this content wholesale from the old Exercise 4 (chapter_04) to
become the new syllabus-aligned Exercise 3; the old KNN/bias-variance Exercise
3 was merged into Exercise 2 and the old Exercise 4's route is now a
placeholder for a future Cross-Validation exercise. This file replaces the
pre-WP25 `test_exercise_03_notebook.py`, which tested the discarded KNN
notebook now preserved only on archive/pre-syllabus-notebook-structure.

Standard-library ``unittest``; no network. Checks structure, the leakage
guard and locked/stratified split, that the confusion matrix / accuracy /
AUC in the notebook's committed outputs match the committed audit result,
and that both interactive activities are embedded correctly under their new
Exercise 3 numbering.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_03_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb"
AUDIT_RESULT = json.loads((REPO_ROOT / "scripts" / "classification_model_audit_result.json").read_text())


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
        self.assertTrue(all(i.startswith(("wp17-", "wp18-", "wp19-")) for i in ids), ids)

    def test_h1_title_is_exact(self):
        self.assertEqual(
            _src(self.cells[0]).splitlines()[0],
            "# Exercise 3: Classification and Metrics",
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
        for other in ("chapter_01", "chapter_02", "chapter_04"):
            self.assertNotIn(other, card)

    def test_opening_has_scope_and_prerequisites_no_time_budget(self):
        opening = "\n".join(_src(c) for c in self.cells[:3])
        self.assertIn("What this notebook covers", opening)
        self.assertIn("Prerequisites", opening)
        low = " ".join(opening.lower().split())
        self.assertIn("classifier", low)
        self.assertIn("confusion matrix", low)
        self.assertNotIn("minutes", low)
        self.assertNotRegex(opening, r"\d+\s*[-–]\s*\d+\s*min")

    def test_covers_section_names_the_classification_pipeline(self):
        # Task requirement: the concise "what this notebook covers" wording
        # names logistic regression and classification metrics explicitly.
        opening = _src(self.cells[2])
        low = opening.lower()
        self.assertIn("classification pipeline", low)
        self.assertIn("logistic regression", low)
        self.assertIn("classification metrics", low)

    def test_cell_count_is_short_relative_to_exercise_one(self):
        n = len(self.cells)
        self.assertGreaterEqual(n, 20)
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
            "## 1. The ABIDE classification data",
            "## 2. From a linear score to a probability",
            "## 3. One logistic-regression model",
            "## 4. Classification outcomes and metrics",
            "## 5. Interactive activity: choosing a decision threshold",
            "## 6. Interactive activity: class imbalance and misleading accuracy",
        )
        for head in headings:
            self.assertIn(head, self.md)
        positions = [self.md.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))

    # -- data / leakage guard -------------------------------------------------

    def test_diagnosis_column_and_coding_are_explicit(self):
        self.assertIn('(model_df["group"] == 1)', self.code)
        self.assertIn("1 = autism, 0 = control", self.code)
        self.assertIn("463 autism (group=1), 541 control (group=2)", self.all_output)
        self.assertIn("missing diagnosis: 0 of 1004 participants", self.all_output)
        self.assertIn("duplicate participant ids: 0", self.all_output)

    def test_only_the_360_approved_roi_features_are_predictors(self):
        cell = self.by_id["wp17-031"]
        src = _src(cell)
        self.assertIn('FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]', src)
        self.assertIn('assert all(c.startswith("fsCT_") for c in FEATURES)', src)
        self.assertIn('assert "group" not in FEATURES', src)
        self.assertIn("360 features", self.all_output)
        # same FEATURES derivation line as Exercise 2's Section 2 recipe cell
        ex2 = nbformat.read(REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb", as_version=4)
        ex2_cell = next(c for c in ex2.cells if c["id"] == "wp11-021")
        self.assertIn('FEATURES = [c for c in BRAIN_COLS if c.startswith("fsCT_")]', _src(ex2_cell))

    def test_forbidden_columns_are_not_predictors(self):
        xy_cell = self.by_id["wp17-032"]
        src = _src(xy_cell)
        self.assertIn("X = model_df[FEATURES].to_numpy(float)", src)
        for forbidden in ("subject", "site", "age", "sex", "\"group\"]"):
            self.assertNotIn(f"model_df[[{forbidden}", src)
        self.assertNotIn("model_df[\"group\"].to_numpy(float)] +", src)

    def test_split_is_stratified_by_y_with_project_standard_seed(self):
        self.assertIn("test_size=0.25, random_state=42, stratify=y", self.code)
        self.assertIn("n_train = 753   n_test = 251   n_features = 360", self.all_output)

    def test_c_is_fixed_by_course_design_not_a_search(self):
        # WP19 §5.1/§5.2: C = 1.0 is predeclared, not selected by
        # cross-validation or any other search over candidate values.
        self.assertIn("C_EXAMPLE = 1.0", self.code)
        self.assertIn("LogisticRegression(C=C_EXAMPLE, max_iter=5000)", self.code)
        self.assertNotIn("GridSearchCV", self.code)
        self.assertNotIn("StratifiedKFold", self.code)
        self.assertNotIn("CANDIDATE_CS", self.code)
        self.assertNotIn("C_SELECTED", self.code)
        low_md = self.md.lower()
        for needle in ("cross-validation", "cross validation", "gridsearchcv"):
            self.assertNotIn(needle, low_md)
        self.assertIn("accuracy    = 0.546", self.all_output)
        self.assertIn("AUC         = 0.569", self.all_output)

    def test_scaler_fit_only_on_training_rows(self):
        self.assertIn("scaler.fit_transform(X_train)", self.code)
        self.assertIn("scaler.transform(X_test)", self.code)
        self.assertNotIn("scaler.fit_transform(X_test)", self.code)
        self.assertNotIn("scaler.fit(X_test)", self.code)

    def test_explicit_and_pipeline_versions_agree(self):
        self.assertIn("assert np.array_equal(y_pred, explicit_model.predict(X_test_scaled))", self.code)

    def test_explicit_scaling_cell_ends_with_semicolon_and_has_no_rich_estimator_output(self):
        # WP18 sec 2.3: the bare-estimator repr (scikit-learn's gray expandable
        # HTML diagram) must not appear after the explicit-scaling cell.
        cell = self.by_id["wp17-033"]
        src = _src(cell)
        self.assertIn("LogisticRegression(C=C_EXAMPLE, max_iter=5000)", src)
        self.assertTrue(src.rstrip().endswith(";"), src[-60:])
        self.assertEqual(cell.get("outputs", []), [])

    def test_no_estimator_html_repr_anywhere_in_the_notebook(self):
        for cell in self.cells:
            for out in cell.get("outputs", []):
                html = out.get("data", {}).get("text/html", "")
                html = "".join(html) if isinstance(html, list) else html
                self.assertNotIn("sk-top-container", html)
                self.assertNotIn("sk-estimator", html)

    def test_only_one_brief_reminder_about_held_out_metrics(self):
        # WP17 §3.4: one brief reminder, not a repeat of the earlier
        # train/resubstitution/invalid demonstration. The prerequisites line
        # may name "resubstitution" once, forward-referencing Exercise 2's
        # demonstration to say it will not be repeated -- that is not itself
        # a repeat of the demonstration's code/plots.
        self.assertIn("none of them were used to fit the model", self.md + self.code)
        self.assertEqual(self.md.lower().count("resubstitution"), 1)
        self.assertNotIn("invalid_test_fitted_model", self.code)

    # -- metrics ----------------------------------------------------------

    def test_confusion_matrix_orientation_stated(self):
        self.assertIn("Rows are the **actual** diagnosis", self.md)
        self.assertIn("columns are the **predicted** diagnosis", self.md)

    def test_honest_metrics_match_the_committed_audit(self):
        ev = AUDIT_RESULT["locked_test_eval"]
        self.assertIn(f"accuracy    = {ev['accuracy']:.3f}", self.all_output)
        self.assertIn(f"AUC         = {ev['auc']:.3f}", self.all_output)
        self.assertIn(f"sensitivity = {ev['sensitivity']:.3f}", self.all_output)
        self.assertIn(f"specificity = {ev['specificity']:.3f}", self.all_output)

    def test_confusion_matrix_cells_are_labelled_with_their_abbreviation(self):
        # WP18 sec 3: TN/FP/FN/TP must appear directly beside their values.
        cm = AUDIT_RESULT["locked_test_eval"]["confusion_matrix"]
        for label, key in (("TN", "tn"), ("FP", "fp"), ("FN", "fn"), ("TP", "tp")):
            self.assertIn(f"{label} = {cm[key]}", self.all_output)
        cell = self.by_id["wp17-041"]
        src = _src(cell)
        self.assertIn('f"TN = {tn}"', src)
        self.assertIn('f"FP = {fp}"', src)
        self.assertIn('f"FN = {fn}"', src)
        self.assertIn('f"TP = {tp}"', src)

    def test_predict_proba_think_first_present(self):
        self.assertIn("predict_proba()", self.md)
        self.assertIn(":class: think-first", self.md)

    # -- activities ---------------------------------------------------------

    def test_threshold_activity_iframe_present(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        matching = [c for c in iframe_cells if "configs/classification_threshold.json" in _src(c)]
        self.assertEqual(len(matching), 1)
        self.assertIn(
            'title="Interactive decision-threshold exploration for classifying autism vs. control from brain structure"',
            _src(matching[0]),
        )

    def test_threshold_activity_never_refits_the_model(self):
        self.assertIn("never refit", self.md.lower())

    def test_threshold_portable_code_cell_has_editable_threshold_line(self):
        cell = self.by_id["wp17-053"]
        src = _src(cell)
        self.assertIn("threshold = 0.50", src)
        self.assertNotIn("ipywidgets", src)
        self.assertNotIn("<iframe", src)

    def test_imbalance_activity_iframe_present(self):
        iframe_cells = [c for c in self.cells if "<iframe" in _src(c)]
        matching = [c for c in iframe_cells if "configs/classification_imbalance.json" in _src(c)]
        self.assertEqual(len(matching), 1)
        self.assertIn(
            'title="Interactive class-imbalance exploration for classifying autism vs. control from brain structure"',
            _src(matching[0]),
        )

    def test_imbalance_portable_code_cell_has_editable_ratio_and_seed(self):
        cell = self.by_id["wp17-063"]
        src = _src(cell)
        self.assertIn('class_ratio = "90:10"', src)
        self.assertIn("random_state = 42", src)
        self.assertIn("LogisticRegression(C=C_EXAMPLE, max_iter=5000)", src)
        self.assertNotIn("ipywidgets", src)
        self.assertNotIn("<iframe", src)

    def test_imbalance_cohort_size_and_output_present(self):
        self.assertIn("cohort: 400 participants (360 control, 40 autism)", self.all_output)

    def test_no_stratified_vs_unstratified_comparison_remains(self):
        # WP18 sec 4: the stratified-vs-unstratified comparison, paired split
        # panels, split-kind language, and "what does stratification solve"
        # framing are all removed. One concise implementation-detail sentence
        # about the internal stratified split is explicitly still allowed.
        low = self.md.lower()
        self.assertNotIn("unstratified", low)
        self.assertNotIn("stratified split (", low)
        self.assertNotIn("stratified model", low)
        self.assertNotIn("what does stratification solve", low)
        self.assertNotIn("what problem does stratification solve", low)
        self.assertIn("stratified train/test split internally", low)

    def test_95_5_baseline_think_first_present(self):
        self.assertIn("95%", self.md)
        low = self.md.lower()
        self.assertIn("predicting", low)
        self.assertIn("control", low)

    # -- closing --------------------------------------------------------------

    def test_takeaways_and_exactly_three_review_questions_with_answers(self):
        self.assertIn("## In summary", self.md)
        self.assertIn("### Questions to take away", self.md)
        closing = self.md[self.md.index("### Questions to take away"):]
        self.assertEqual(closing.count("```{dropdown} Answer"), 3)
        self.assertNotRegex(self.md, r"\d+\s*[-–]\s*\d+\s*min")

    def test_no_wp_script_or_report_references_in_student_text(self):
        low_md = self.md.lower()
        low_code = self.code.lower()
        for needle in ("scripts/", "wp16", "wp17", "audit script", "audit_result"):
            self.assertNotIn(needle, low_md)
            self.assertNotIn(needle, low_code)

    def test_excluded_topics_absent(self):
        low = self.md.lower() + self.code.lower()
        for needle in (
            "smote",
            "precision-recall",
            "precision_recall",
            "coefficient map",
            "leave-one-site-out",
            "multiclass",
        ):
            self.assertNotIn(needle, low)

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

    def test_no_stale_old_exercise_numbering(self):
        # WP25: this content used to be Exercise 4, cross-referencing
        # "Exercises 2-3". Both must be gone now that it is Exercise 3
        # cross-referencing the single merged Exercise 2.
        self.assertNotIn("Exercise 4", self.md)
        self.assertNotIn("Exercises 2-3", self.md)
        self.assertNotIn("chapter_04", self.md + self.code)


if __name__ == "__main__":
    unittest.main()
