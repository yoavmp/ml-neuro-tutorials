"""Repository-wide content audit for WP19: confirms that early-course
cross-validation / formal-parameter-selection material -- neither taught nor
implemented -- is absent from the rendered student-facing sources of
Exercises 1-3 (WP25 renumbered the active book to Exercises 1-3 plus
placeholder Exercises 4-12; the discarded old Exercise 3 sections and the
old Exercise 4 numbering live only on archive/pre-syllabus-notebook-structure).

Scope (WP19 §8.1, corrected; paths updated by WP25): the three active
canonical notebooks, their generated portable notebooks, and the four
activity-widget config JSON files whose text is rendered directly in the
book pages (knn_explore, classification_threshold, classification_imbalance,
regression_compare). Historical WP documents and completed WP reports are
records and are intentionally NOT scanned here (WP19 §2 scope rule).

WP19 correction (Exercise 2): the regression-compare feature-set-comparison
activity previously scored every catalog entry with a hidden 5-fold KFold /
cross_val_predict procedure -- invisible in the notebook's own wording, but
real analysis. This is now a fixed, reproducible train/test split, so the
prohibited-term list below includes ``kfold``, ``cross_val_predict``, and
bare ``fold`` (not just the phrase "cross-validation") to confirm the
underlying implementation changed, not merely its description.

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp19_content_audit.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Indices: 0=ch1 canonical, 1=ch2 canonical, 2=ch3 canonical,
# 3=ch1 portable, 4=ch2 portable, 5=ch3 portable.
NOTEBOOK_PATHS = [
    REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb",
    REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb",
    REPO_ROOT / "book" / "chapters" / "chapter_03" / "exercise_03.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb",
    REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb",
]

WIDGET_CONFIG_PATHS = [
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_explore.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "classification_threshold.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "classification_imbalance.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "regression_compare.json",
]

# Generated data artifacts for the Exercise 1-3 activities (checked for
# leftover implementation, not just wording, per the WP19 correction).
GENERATED_ARTIFACT_PATHS = [
    REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_regression_models.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_knn_explore_manifest.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_classification_threshold.json",
    REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_classification_imbalance.json",
]

# The Exercise 2 exporter itself: WP19 correction requires the underlying
# analysis -- not only its wording -- to drop KFold/cross_val_predict.
EXERCISE_2_EXPORTER_PATH = REPO_ROOT / "scripts" / "export_regression_catalog.py"

# Case-insensitive substrings that must not appear in rendered student-facing
# text for Exercises 1-4 (WP19 §8.1). Regex-escaped where needed.
PROHIBITED_PATTERNS = [
    r"gridsearchcv",
    r"cross_val_score",
    r"cross_val_predict",
    r"cross_validate\b",
    r"stratifiedkfold",
    r"\bkfold\b",  # any mention of KFold, not just a live call
    r"\bcross[- ]validation\b",
    r"5-fold cross-validation",
    r"\bfold(s|ing)?\b",  # bare "fold"/"folds"/"folding" -- verified absent
    # from every scanned file below before this pattern was added
    r"best\s+k\b",
    r"selected\s+k\b",
    r"optimal\s+k\b",
    r"cv-selected\s+k",
    r"best\s+c\b",
    r"selected\s+c\b",
    r"optimal\s+c\b",
    r"cv-selected\s+c",
    r"choosing k honestly",
    r"choosing c honestly",
    r"k_selected",
    r"c_selected",
]

PROHIBITED_RE = re.compile("|".join(PROHIBITED_PATTERNS), re.IGNORECASE)


def _notebook_text(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        src = cell.get("source", "")
        parts.append("".join(src) if isinstance(src, list) else src)
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                text = out.get("text", "")
                parts.append("".join(text) if isinstance(text, list) else text)
            elif "data" in out:
                plain = out["data"].get("text/plain", "")
                parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


class NotebookContentAudit(unittest.TestCase):
    def test_notebooks_exist(self):
        for path in NOTEBOOK_PATHS:
            self.assertTrue(path.exists(), path)

    def test_no_prohibited_early_cv_or_tuning_terms(self):
        for path in NOTEBOOK_PATHS:
            text = _notebook_text(path)
            matches = sorted(set(m.group(0).lower() for m in PROHIBITED_RE.finditer(text)))
            self.assertEqual(
                matches, [], f"{path.relative_to(REPO_ROOT)} contains prohibited terms: {matches}"
            )

    def test_exercise_2_uses_fixed_k20_language(self):
        for path in (NOTEBOOK_PATHS[1], NOTEBOOK_PATHS[4]):
            text = _notebook_text(path)
            self.assertIn("K_EXAMPLE = 20", text, path)

    def test_exercise_3_uses_fixed_c1_language(self):
        for path in (NOTEBOOK_PATHS[2], NOTEBOOK_PATHS[5]):
            text = _notebook_text(path)
            self.assertIn("C_EXAMPLE = 1.0", text, path)


class WidgetConfigContentAudit(unittest.TestCase):
    def test_configs_exist(self):
        for path in WIDGET_CONFIG_PATHS:
            self.assertTrue(path.exists(), path)

    def test_no_prohibited_early_cv_or_tuning_terms(self):
        for path in WIDGET_CONFIG_PATHS:
            text = path.read_text(encoding="utf-8")
            matches = sorted(set(m.group(0).lower() for m in PROHIBITED_RE.finditer(text)))
            self.assertEqual(
                matches, [], f"{path.relative_to(REPO_ROOT)} contains prohibited terms: {matches}"
            )

    def test_knn_explore_default_k_is_the_fixed_worked_example(self):
        cfg = json.loads((REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "knn_explore.json").read_text())
        self.assertEqual(cfg["defaultK"], 20)


class GeneratedArtifactContentAudit(unittest.TestCase):
    """WP19 correction: confirms the *implementation*, not only the wording,
    is free of cross-validation -- the committed data artifacts a student's
    browser actually loads must carry no KFold/fold/cross_val trace."""

    def test_artifacts_exist(self):
        for path in GENERATED_ARTIFACT_PATHS:
            self.assertTrue(path.exists(), path)

    def test_no_prohibited_early_cv_or_tuning_terms(self):
        for path in GENERATED_ARTIFACT_PATHS:
            text = path.read_text(encoding="utf-8")
            matches = sorted(set(m.group(0).lower() for m in PROHIBITED_RE.finditer(text)))
            self.assertEqual(
                matches, [], f"{path.relative_to(REPO_ROOT)} contains prohibited terms: {matches}"
            )

    def test_regression_catalog_uses_one_fixed_holdout_split(self):
        artifact = json.loads(
            (REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_regression_models.json").read_text()
        )
        self.assertIn("holdoutSplit", artifact)
        self.assertNotIn("crossValidation", artifact)
        self.assertNotIn("foldOf", artifact)
        self.assertIn("observedTest", artifact)
        self.assertNotIn("observed", artifact)
        hs = artifact["holdoutSplit"]
        self.assertEqual(hs["nTrain"] + hs["nTest"], artifact["cohort"]["n"])


class Exercise2ExporterImplementationAudit(unittest.TestCase):
    """WP19 correction: the Exercise 2 feature-set-comparison exporter must
    not run any cross-validation procedure. The module docstring may still
    describe, in prose, the WP19 correction itself (what was removed and
    why) -- so this checks for the specific executable constructs rather
    than banning every mention of the word "cross-validation"."""

    def setUp(self):
        full_source = EXERCISE_2_EXPORTER_PATH.read_text(encoding="utf-8")
        # Drop the module docstring: it explains, in prose, the WP19
        # correction itself (what was removed and why) and is allowed to
        # name "KFold"/"cross_val_predict" as history. The executable code
        # below the docstring must not.
        parts = full_source.split('"""')
        self.assertGreaterEqual(len(parts), 3, "module docstring not found")
        self.source = '"""'.join(parts[2:])

    def test_no_kfold_import_or_construction(self):
        self.assertNotIn("KFold", self.source)

    def test_no_cross_val_predict_call(self):
        self.assertNotIn("cross_val_predict", self.source)
        self.assertNotIn("cross_val_score", self.source)

    def test_uses_train_test_split_and_the_shared_holdout_protocol(self):
        self.assertIn("train_test_split", self.source)
        self.assertIn('manifest["protocol"]["holdout_split"]', self.source)

    def test_manifest_has_no_catalog_cross_validation_protocol(self):
        import sys as _sys

        _sys.path.insert(0, str((REPO_ROOT / "scripts").resolve()))
        import abide_modeling_data as amd  # noqa: E402

        self.assertNotIn("cross_validation", amd.MANIFEST["protocol"])
        _sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
