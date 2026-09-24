"""Offline assertions for book/chapters/chapter_10/exercise_10.ipynb (Exercise 10).

WP38 replaced the Exercise 10 placeholder with a review-and-debugging
notebook on common ML evaluation mistakes: the boundary around the training
data (with a multiple-selection quiz), a leakage laboratory comparing correct
and leaky preprocessing on ABIDE-II age regression, model selection with the
test set, related observations on the public UCI HAR dataset, class
imbalance, a bonus site-split section, and a "find the mistake" debugging
exercise.

Standard-library ``unittest``; no network.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_10_notebook.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_10" / "exercise_10.ipynb"
PORTABLE_PATH = REPO_ROOT / "book" / "downloads" / "chapter_10" / "exercise_10_portable.ipynb"

SECTION_TITLES = [
    "## 1. The Boundary Around the Training Data",
    "## 2. A Leakage Laboratory",
    "## 3. Do Not Choose the Model With the Test Set",
    "## 4. Related Observations Must Stay Together",
    "## 5. Class Imbalance Changes the Question",
    "## 6. Does the Split Match the Scientific Question? (Bonus)",
    "## 7. Find the Mistake",
]

IFRAME_TITLES = [
    "Interactive multiple-selection question on which preprocessing and modelling steps must not use the final test participants",
    "Interactive leakage-lab comparing correct and leaky preprocessing pipelines on ABIDE-II cortical thickness and age",
    "Interactive comparison of random-window and participant-grouped cross-validation on UCI HAR smartphone sensor windows",
    "Interactive comparison of ordinary and class-weighted logistic regression for imbalanced autism classification",
]

ENGINEERING_VOCAB = ("schema", "payload", "artifact", "manifest", "wp38", "fixture", "canonical recipe")


def _src(cell) -> str:
    s = cell["source"]
    return "".join(s) if isinstance(s, list) else s


class ExerciseTenNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.cells = cls.nb.cells
        cls.joined = "\n".join(_src(c) for c in cls.cells)

    def test_notebook_is_valid_nbformat(self):
        nbformat.validate(self.nb)

    def test_cell_count_within_target_range(self):
        self.assertTrue(32 <= len(self.cells) <= 38, len(self.cells))

    def test_title_cell_is_first_and_only_the_title(self):
        first = _src(self.cells[0]).strip()
        self.assertEqual(first, "# Exercise 10: Examples and Common Mistakes")

    def test_run_or_download_admonition_present(self):
        self.assertIn("```{admonition} Run or download this notebook", self.joined)
        self.assertIn("exercise_10_portable.ipynb", self.joined)

    def test_what_this_notebook_covers_has_four_numbered_items(self):
        idx = next(i for i, c in enumerate(self.cells) if "What this notebook covers" in _src(c))
        text = _src(self.cells[idx])
        for item in (
            "1. keep preprocessing and feature construction away from final test participants",
            "2. avoid choosing models or parameters with the test set",
            "3. keep related observations in the same fold",
            "4. use metrics and training choices that match an imbalanced classification problem",
        ):
            self.assertIn(item, text)

    def test_all_section_headings_present_in_order(self):
        positions = []
        for title in SECTION_TITLES:
            found = [i for i, c in enumerate(self.cells) if title in _src(c)]
            self.assertTrue(found, f"missing section heading: {title!r}")
            positions.append(found[0])
        self.assertEqual(positions, sorted(positions))

    def test_all_four_iframes_present_with_expected_titles(self):
        for title in IFRAME_TITLES:
            self.assertIn(f'title="{title}"', self.joined)
        self.assertEqual(self.joined.count("<iframe"), 4)

    def test_iframe_src_paths_point_at_expected_configs(self):
        for name in ("leakage_quiz", "leakage_lab", "har_fold_compare", "imbalance_threshold"):
            self.assertIn(f"configs/{name}.json", self.joined)

    def test_quiz_options_and_only_metric_choice_is_incorrect(self):
        quiz_data = json.loads((REPO_ROOT / "book" / "_static" / "widgets" / "data" / "leakage_quiz.json").read_text())
        options = quiz_data["options"]
        self.assertEqual(len(options), 7)
        correct = [o for o in options if o["correct"]]
        incorrect = [o for o in options if not o["correct"]]
        self.assertEqual(len(correct), 6)
        self.assertEqual(len(incorrect), 1)
        self.assertIn("metric", incorrect[0]["text"].lower())
        for distractor in ("renaming", "color"):
            self.assertNotIn(distractor, json.dumps(options).lower())

    def test_think_first_blocks_present_and_not_duplicated_verbatim(self):
        think_first_blocks = [c for c in self.cells if "```{admonition} Think first" in _src(c)]
        self.assertGreaterEqual(len(think_first_blocks), 2)
        bodies = [_src(c).split("Think first", 1)[1] for c in think_first_blocks]
        self.assertEqual(len(bodies), len(set(bodies)))

    def test_leakage_evaluation_invalid_sentence_present_once(self):
        sentence = "Leakage makes the evaluation invalid even when its score is similar"
        normalized = " ".join(self.joined.split())
        self.assertEqual(normalized.count(sentence), 1)

    def test_find_the_mistake_has_five_fragments_and_dropdown_answers(self):
        for i in range(1, 6):
            self.assertIn(f"**Fragment {i}**", self.joined)
        self.assertEqual(self.joined.count("```{dropdown} Answer"), 5)

    def test_final_checklist_present_with_nine_items(self):
        idx = next(i for i, c in enumerate(self.cells) if _src(c).strip().startswith("## Final Checklist"))
        text = _src(self.cells[idx])
        bullets = [line for line in text.splitlines() if line.strip().startswith("- ")]
        self.assertEqual(len(bullets), 9)

    def test_no_engineering_vocabulary_leaks_to_student_text(self):
        lowered = self.joined.lower()
        for term in ENGINEERING_VOCAB:
            self.assertNotIn(term, lowered, term)

    def test_data_loading_cells_are_hide_input_not_hide_cell(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            src = _src(c)
            tags = c.get("metadata", {}).get("tags", [])
            if "pd.read_csv" in src and "compact" in src:
                self.assertIn("hide-input", tags)
            if "abide2.tsv" in src:
                self.assertIn("hide-input", tags)

    def test_reproduction_cells_use_hide_cell(self):
        for c in self.cells:
            if c["cell_type"] != "code":
                continue
            src = _src(c)
            if "StratifiedGroupKFold" in src or "class_weight" in src:
                self.assertIn("hide-cell", c.get("metadata", {}).get("tags", []))

    def test_uci_har_attribution_present(self):
        self.assertIn("archive.ics.uci.edu/dataset/240", self.joined)
        self.assertIn("10.24432/C54S4K", self.joined)
        self.assertIn("CC BY 4.0", self.joined)

    def test_portable_notebook_exists_and_has_no_repository_relative_dependency(self):
        self.assertTrue(PORTABLE_PATH.exists())
        portable = nbformat.read(PORTABLE_PATH, as_version=4)
        joined_portable = "\n".join(_src(c) for c in portable.cells)
        for forbidden in ("_static/", "../../config/", "<iframe", "requirements.txt", "```{"):
            self.assertNotIn(forbidden, joined_portable)

if __name__ == "__main__":
    unittest.main()
