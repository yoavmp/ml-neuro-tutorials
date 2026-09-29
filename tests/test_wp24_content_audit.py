"""Focused regression tests for WP24 (notebook concision and content
refinement): the decision-block move in Exercise 1, the "impute" ->
plain-language rewording, the removal of Spearman correlation from every
Exercise 1 surface, the single-occurrence fixes in Exercises 2 and 4, the
new Exercise 4 comparison question, and the dark-mode syntax-color fix.

Standard-library ``unittest``; no network, no build.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_wp24_content_audit.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EX1 = REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb"
EX1_PORTABLE = REPO_ROOT / "book" / "downloads" / "chapter_01" / "exercise_01_portable.ipynb"
EX2 = REPO_ROOT / "book" / "chapters" / "chapter_02" / "exercise_02.ipynb"
EX2_PORTABLE = REPO_ROOT / "book" / "downloads" / "chapter_02" / "exercise_02_portable.ipynb"
# WP28 moved "Compare Two Feature Sets" (and its exploratory-comparison
# warning) from Exercise 2's Bonus section to Exercise 5.
EX5 = REPO_ROOT / "book" / "chapters" / "chapter_05" / "exercise_05.ipynb"
# WP25 moved this content wholesale from chapter_04 to chapter_03 (the
# classification lesson is now Exercise 3; chapter_04 is a placeholder).
# WP44 migrated Exercise 3 to a JupyterLite notebook: EX4 now points at the
# real lesson (book/lite/files/exercise_03.ipynb), not the canonical page
# (now a 2-cell transition page with none of this content -- see
# tests/test_exercise_03_transition_page.py), mirroring how EX2_LITE already
# repoints Exercise 2's own checks below.
EX4 = REPO_ROOT / "book" / "lite" / "files" / "exercise_03.ipynb"
EX4_PORTABLE = REPO_ROOT / "book" / "downloads" / "chapter_03" / "exercise_03_portable.ipynb"

EDA_CORRELATION_JSON = REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "eda_correlation.json"
REGRESSION_COMPARE_JSON = REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "regression_compare.json"
CLASSIFICATION_IMBALANCE_JSON = (
    REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "classification_imbalance.json"
)
ABIDE_RETENTION_JSON = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_retention.json"

CORRELATION_TS = REPO_ROOT / "interactive" / "src" / "correlation.ts"
CORRELATION_COMPONENT_TS = REPO_ROOT / "interactive" / "src" / "components" / "correlation.ts"

CUSTOM_CSS = REPO_ROOT / "book" / "_static" / "custom.css"


def _load_cells(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def _cell_text(cell: dict) -> str:
    src = cell.get("source", "")
    text = "".join(src) if isinstance(src, list) else src
    parts = [text]
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream":
            t = out.get("text", "")
            parts.append("".join(t) if isinstance(t, list) else t)
        elif "data" in out:
            plain = out["data"].get("text/plain", "")
            parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


def _notebook_text(path: Path) -> str:
    return "\n".join(_cell_text(c) for c in _load_cells(path))


def _notebook_markdown_text(path: Path) -> str:
    return "\n".join(
        _cell_text(c) for c in _load_cells(path) if c.get("cell_type") == "markdown"
    )


# WP24's Exercise1DecisionBlockOrder is retired: WP42 migrated Exercise 1 to
# a JupyterLite notebook (EX1 is now a short transition page; the real
# lesson is EX1_PORTABLE) and dropped the separate "Our approach in this
# exercise" decision block entirely as part of its concision pass -- the
# retention explorer section (still present, notebook-native, see
# tests/test_exercise_01_lite_notebook.py's
# test_retention_explorer_is_notebook_native) no longer has a preceding
# block whose order could be checked here.


class Exercise1NoImputeJargon(unittest.TestCase):
    """WP24 §2.2: no case-insensitive 'imput' anywhere student-facing in Ex1.
    WP42 moved the real lesson text from EX1 (now a transition page) to
    EX1_PORTABLE (the migrated JupyterLite notebook)."""

    def test_canonical_notebook_has_no_imput_text(self):
        text = _notebook_text(EX1)
        self.assertNotIn("imput", text.lower())

    def test_portable_notebook_has_no_imput_text(self):
        text = _notebook_text(EX1_PORTABLE)
        self.assertNotIn("imput", text.lower())

    def test_plain_language_present(self):
        text = _notebook_text(EX1_PORTABLE)
        self.assertIn("fill in", text.lower())
        self.assertIn("filled in", text.lower())


class Exercise1NoSpearman(unittest.TestCase):
    """WP24 §2.3: Spearman is fully removed from every Exercise 1 surface."""

    def test_canonical_notebook_has_no_spearman(self):
        self.assertNotIn("spearman", _notebook_text(EX1).lower())

    def test_portable_notebook_has_no_spearman(self):
        self.assertNotIn("spearman", _notebook_text(EX1_PORTABLE).lower())

    def test_correlation_widget_config_has_no_spearman_or_default_method(self):
        raw = EDA_CORRELATION_JSON.read_text(encoding="utf-8")
        self.assertNotIn("spearman", raw.lower())
        config = json.loads(raw)
        self.assertNotIn("defaultMethod", config)

    def test_exported_correlation_data_has_no_spearman(self):
        self.assertNotIn("spearman", ABIDE_RETENTION_JSON.read_text(encoding="utf-8").lower())

    def test_correlation_maths_module_has_no_spearman(self):
        self.assertNotIn("spearman", CORRELATION_TS.read_text(encoding="utf-8").lower())

    def test_correlation_component_has_no_spearman(self):
        self.assertNotIn("spearman", CORRELATION_COMPONENT_TS.read_text(encoding="utf-8").lower())


class Exercise1CorrelationWidgetPearsonOnly(unittest.TestCase):
    """WP24 §2.3: no method selector; Pearson is labelled clearly."""

    def test_no_method_selector_testid(self):
        source = CORRELATION_COMPONENT_TS.read_text(encoding="utf-8")
        self.assertNotIn("correlation-method", source)

    def test_labels_pearson_clearly(self):
        source = CORRELATION_COMPONENT_TS.read_text(encoding="utf-8")
        self.assertIn("Pearson correlation", source)

    def test_variable_and_grouping_selects_retained(self):
        source = CORRELATION_COMPONENT_TS.read_text(encoding="utf-8")
        self.assertIn("correlation-x", source)
        self.assertIn("correlation-y", source)
        self.assertIn("correlation-group", source)


def _norm_ws(text: str) -> str:
    return " ".join(text.split())


class Exercise5SingleExploratoryWarning(unittest.TestCase):
    """WP24 §3.1 (moved to Exercise 5 by WP28): the exploratory-comparison
    warning appears once, in the notebook, and the widget's duplicate note
    is gone. Exercise 2 no longer carries this activity or warning at all."""

    NEEDLE = "exploratory comparison"

    def test_notebook_contains_warning_exactly_once(self):
        text = _norm_ws(_notebook_markdown_text(EX5))
        self.assertEqual(text.count(self.NEEDLE), 1)

    def test_widget_config_has_no_selection_bias_note(self):
        raw = REGRESSION_COMPARE_JSON.read_text(encoding="utf-8")
        self.assertNotIn("selectionBiasNote", raw)
        self.assertNotIn(self.NEEDLE, raw.lower())

    def test_warning_follows_the_interactive_activity(self):
        text = _norm_ws(_notebook_text(EX5))
        iframe_idx = text.index("regression_compare.json")
        warning_idx = text.index(self.NEEDLE)
        self.assertGreater(warning_idx, iframe_idx)

    def test_no_exploratory_comparison_warning_left_in_exercise_2(self):
        text = _norm_ws(_notebook_markdown_text(EX2))
        self.assertNotIn(self.NEEDLE, text)


EX2_LITE = REPO_ROOT / "book" / "lite" / "files" / "exercise_02.ipynb"


class Exercise2SampleSizeSectionAccurate(unittest.TestCase):
    """WP24 §3.2: the Bonus section is concise and accurately describes the
    predeclared, non-ranked feature-bundle selection; the fixed feature set
    is unchanged. WP41 moved Exercise 2's canonical page to
    book/lite/files/exercise_02.ipynb (book/chapters/chapter_02/exercise_02.ipynb
    is now a transition page, see tests/test_exercise_02_transition_page.py)."""

    def test_bonus_intro_is_concise(self):
        text = _notebook_markdown_text(EX2_LITE)
        start = text.index("## Bonus")
        end = text.index("```", start) if "```" in text[start:] else start + 400
        section = text[start:end]
        self.assertLess(len(section.split()), 220, "Bonus lead-in should be concise")

    def test_selection_described_as_not_ranked_by_correlation(self):
        text = _notebook_markdown_text(EX2_LITE)
        self.assertIn("not chosen by ranking", text)

    def test_teaching_demonstration_caution_present(self):
        text = _notebook_markdown_text(EX2_LITE)
        self.assertIn("teaching demonstration", text.lower())

    def test_fixed_feature_set_and_sizes_unchanged(self):
        text = _notebook_text(EX2_LITE)
        self.assertIn('SAMPLE_SIZE_ROIS = ["4", "3a", "3b", "1", "2"]', text)
        self.assertIn("sizes = [40, 60, 90, 130, 200, 300, len(y_train_ss)]", text)


class Exercise4SingleMajorityBaselineParagraph(unittest.TestCase):
    """WP24 §4.1: the majority-baseline paragraph appears once, in the
    notebook, and the widget's duplicate note is gone."""

    NEEDLE = "As class imbalance increases, predicting only the majority"

    def test_notebook_contains_paragraph_exactly_once(self):
        text = _notebook_markdown_text(EX4)
        self.assertEqual(text.count(self.NEEDLE), 1)

    def test_widget_config_has_no_imbalance_note(self):
        raw = CLASSIFICATION_IMBALANCE_JSON.read_text(encoding="utf-8")
        self.assertNotIn("imbalanceNote", raw)
        self.assertNotIn(self.NEEDLE, raw)


class Exercise4SinglePromptSetWithComparisonQuestion(unittest.TestCase):
    """WP24 §4.2/§4.3: Section 6 keeps exactly one prompt set (the widget's
    Reflect list), and it includes the new accuracy-vs-baseline question."""

    def test_notebook_section_6_has_no_think_first_block(self):
        # WP44 shortened this heading to "## 6. Class imbalance and
        # misleading accuracy" as part of Exercise 3's JupyterLite migration
        # (no MyST admonitions exist in a JupyterLite-native notebook at
        # all, so this assertion is now trivially true by construction --
        # kept as a real regression check, not deleted).
        cells = _load_cells(EX4)
        start = next(
            i
            for i, c in enumerate(cells)
            if "## 6. Class imbalance and misleading accuracy" in _cell_text(c)
        )
        end = next(
            (i for i, c in enumerate(cells) if i > start and _cell_text(c).startswith("## ")),
            len(cells),
        )
        section_text = "\n".join(_cell_text(cells[i]) for i in range(start, end))
        self.assertNotIn("Think first", section_text)

    def test_widget_reflection_prompts_has_exactly_three_including_comparison(self):
        config = json.loads(CLASSIFICATION_IMBALANCE_JSON.read_text(encoding="utf-8"))
        prompts = config["reflectionPrompts"]
        self.assertEqual(len(prompts), 3)
        joined = " ".join(prompts).lower()
        self.assertIn("50:50", joined)
        self.assertIn("better", joined)
        self.assertIn("baseline for comparison", joined)

    def test_portable_notebook_keeps_an_equivalent_question(self):
        text = _notebook_text(EX4_PORTABLE)
        self.assertIn("50:50", text)
        self.assertIn("baseline for comparison", text.lower())


class RedundantReproductionCellsCollapsed(unittest.TestCase):
    """WP24 §7: website-only redundant reproduction cells are hide-cell;
    the corresponding portable cells stay fully visible.

    Exercise 1's own case (a seaborn histplot reproduction cell) no longer
    applies: WP42 migrated Exercise 1 to a JupyterLite notebook, which uses
    no seaborn at all (no prebuilt Pyodide wheel) and no hide-cell concept
    (that is a Jupyter Book/Sphinx-only rendering tag). Exercise 3's own
    case (an iframe-widget-plus-portable-reproduction pair, each previously
    carrying a matching threshold/ratio default) no longer applies for the
    same reason: WP44 migrated Exercise 3 to a JupyterLite notebook, whose
    threshold/imbalance activities are native ipywidgets controls with no
    separate iframe or hide-cell reproduction at all -- checked instead,
    directly, in tests/test_exercise_03_lite_notebook.py's
    test_threshold_widget_is_notebook_native and
    test_imbalance_widget_is_notebook_native."""

    def test_portable_notebooks_have_no_hide_tags_and_keep_the_code(self):
        for path, needle in (
            (EX4_PORTABLE, "threshold = 0.50"),
            (EX4_PORTABLE, 'class_ratio = "90:10"'),
        ):
            cells = _load_cells(path)
            cell = next(c for c in cells if needle in _cell_text(c))
            self.assertEqual(cell.get("metadata", {}).get("tags", []), [])


class SyntaxHighlightContrast(unittest.TestCase):
    """WP24 §5: the muted dark-mode syntax color meets WCAG 4.5:1 against
    the dark code-block background."""

    DARK_CODE_BG = "#201e2b"
    NEW_DARK_COLOR = "#c7a86b"

    @staticmethod
    def _contrast_ratio(hex_a: str, hex_b: str) -> float:
        def lin(c: float) -> float:
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        def luminance(hexcolor: str) -> float:
            hexcolor = hexcolor.lstrip("#")
            r, g, b = (int(hexcolor[i : i + 2], 16) for i in (0, 2, 4))
            return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

        l1, l2 = luminance(hex_a), luminance(hex_b)
        l1, l2 = max(l1, l2), min(l1, l2)
        return (l1 + 0.05) / (l2 + 0.05)

    def test_new_color_meets_minimum_contrast(self):
        ratio = self._contrast_ratio(self.NEW_DARK_COLOR, self.DARK_CODE_BG)
        self.assertGreaterEqual(ratio, 4.5)

    def test_new_color_is_less_bright_than_the_old_one(self):
        old_ratio = self._contrast_ratio("#FFD900", self.DARK_CODE_BG)
        new_ratio = self._contrast_ratio(self.NEW_DARK_COLOR, self.DARK_CODE_BG)
        self.assertLess(new_ratio, old_ratio)

    def test_custom_css_overrides_the_three_dark_mode_token_classes(self):
        css = CUSTOM_CSS.read_text(encoding="utf-8")
        dark_block = css[css.index('html[data-theme="dark"]') :]
        for selector in (".highlight .c1", ".highlight .nb", ".highlight .mi"):
            self.assertIn(selector, dark_block)
        self.assertIn(self.NEW_DARK_COLOR, dark_block)


if __name__ == "__main__":
    unittest.main()
