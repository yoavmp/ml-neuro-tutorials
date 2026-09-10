"""WP09 content assertions for the canonical Chapter 1 EDA notebook.

Reads ``book/chapters/chapter_01/exercise_01.ipynb`` with ``nbformat`` and checks
the specific streamlining WP09 asked for (course pages, the 13-column curated
table, the trimmed statistical / missing-data / correlation sections, and the
new head/tail/sample activity). Offline, no build required.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_notebook_corrections.py'
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NB_PATH = REPO_ROOT / "book" / "chapters" / "chapter_01" / "exercise_01.ipynb"
COLUMNS_JSON = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"

# The 13-column curated teaching table (WP09 §7).
CURATED_COLUMNS = [
    "SITE_ID",
    "SUB_ID",
    "DX_GROUP",
    "AGE_AT_SCAN",
    "SEX",
    "HANDEDNESS_CATEGORY",
    "FIQ",
    "VIQ",
    "PIQ",
    "CURRENT_MED_STATUS",
    "SRS_TOTAL_RAW",
    "ADOS_G_TOTAL",
    "ADI_R_SOCIAL_TOTAL_A",
]

# Phenotype columns that appeared in the old 39-column table and must not be
# referenced by any executable code / active-table prose / assertion any more.
REMOVED_PHENOTYPES = [
    "PDD_DSM_IV_TR",
    "ASD_DSM_5",
    "HANDEDNESS_SCORES",
    "FIQ_TEST_TYPE",
    "VIQ_TEST_TYPE",
    "PIQ_TEST_TYPE",
    "EYE_STATUS_AT_SCAN",
    "ADI_R_VERBAL_TOTAL_BV",
    "ADI_R_RRB_TOTAL_C",
    "ADI_R_NONVERBAL_TOTAL_BV",
    "ADOS_MODULE",
    "ADOS_2_TOTAL",
    "ADOS_2_SEVERITY_TOTAL",
    "SRS_VERSION",
    "SRS_INFORMANT",
    "SRS_TOTAL_T",
    "SRS_COMMUNICATION_RAW",
    "SRS_AWARENESS_RAW",
    "SRS_COGNITION_RAW",
    "SRS_MOTIVATION_RAW",
    "SRS_MANNERISMS_RAW",
    "SCQ_TOTAL",
    "SCQ_VERSION",
    "RBSR_6SUBSCALE_TOTAL",
    "MASC_TOTAL_T",
    "BRIEF_BRI_T",
    "BRIEF_MI_T",
    "BRIEF_GEC_T",
    "CBCL_6-18_INTERNAL_T",
    "CBCL_6-18_EXTERNAL_T",
    "CBCL_6-18_TOTAL_PROBLEM_T",
]


class NotebookStreamlining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = nbformat.read(NB_PATH, as_version=4)
        cls.by_id = {c["id"]: c for c in cls.nb.cells}
        cls.md = "\n\n".join(
            c["source"] for c in cls.nb.cells if c["cell_type"] == "markdown"
        )
        cls.code = [c for c in cls.nb.cells if c["cell_type"] == "code"]
        cls.code_src = "\n\n".join(c["source"] for c in cls.code)

    # --- §5: course-introduction duplicates removed ------------------------
    def test_about_how_to_learning_objectives_removed(self):
        for cid in (
            "a1b2c30d4e5f",  # About this exercise
            "b2c3d40e5f6a",  # How to use this notebook
            "6d0ba51b-5219-4743-8c9a-e37126224d86",  # Learning objectives
        ):
            self.assertNotIn(cid, self.by_id)
        for needle in ("## About this exercise", "## Learning objectives",
                       "How to use this notebook"):
            self.assertNotIn(needle, self.md)

    def test_retains_h1_and_compact_run_or_download_control(self):
        self.assertTrue(self.nb.cells[0]["source"].startswith("# Exercise 1"))
        card = self.by_id["c4d5e6f7a8b9"]["source"]
        self.assertIn("Run or download this notebook", card)
        self.assertIn(
            "https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/"
            "blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb",
            card,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/"
            "book/downloads/chapter_01/exercise_01_portable.ipynb",
            card,
        )

    def test_what_this_notebook_covers_kept_and_numpy_not_a_prerequisite(self):
        covers = self.by_id["373d8862-c5df-49a8-9295-a3e4fc073d0f"]["source"]
        self.assertIn("What this notebook covers", covers)
        self.assertIn("Prerequisites:", covers)
        prereq_line = next(
            line for line in covers.splitlines() if "Prerequisites:" in line
        )
        self.assertNotIn("NumPy", prereq_line)
        self.assertNotIn("`NumPy`", covers)
        self.assertNotIn("numpy", covers.lower())

    # --- §7: the 13-column curated table ---------------------------------
    def test_curated_column_config_is_the_13_column_table(self):
        cols = json.loads(COLUMNS_JSON.read_text(encoding="utf-8"))
        self.assertEqual(cols, CURATED_COLUMNS)
        self.assertTrue(10 <= len(cols) <= 15)

    def test_notebook_reads_the_column_config_from_one_place(self):
        load = self.by_id["bd37a40a-40a1-4ab3-9398-f539a2b61fca"]["source"]
        self.assertIn("eda_phenotype_columns.json", load)
        self.assertIn("CURATED_COLUMNS", load)
        self.assertIn('print(f"Data table shape: {rows,cols}")', load)

    def test_data_table_shape_output_is_1114_by_13(self):
        load = self.by_id["bd37a40a-40a1-4ab3-9398-f539a2b61fca"]
        text = _output_text(load)
        self.assertIn("Data table shape: (1114, 13)", text)

    def test_no_stale_removed_phenotype_in_code_or_active_prose(self):
        # Executable code must not mention a removed phenotype.
        for name in REMOVED_PHENOTYPES:
            self.assertNotIn(
                name, self.code_src, f"removed phenotype {name} still in code"
            )
        # Prose that *describes the active table* must not either. The only
        # allowed mention anywhere is a link to the full official legend.
        for name in REMOVED_PHENOTYPES:
            for cell in self.nb.cells:
                if cell["cell_type"] != "markdown":
                    continue
                if name in cell["source"]:
                    self.fail(f"removed phenotype {name} still in markdown cell {cell['id']}")

    def test_categorical_conversion_uses_only_curated_categoricals(self):
        cell = self.by_id["64a0bf6b-8141-4ef6-b604-bfd7b2df6d7b"]["source"]
        self.assertIn('"SITE_ID"', cell)
        self.assertIn('"HANDEDNESS_CATEGORY"', cell)
        self.assertIn('"CURRENT_MED_STATUS"', cell)
        self.assertIn('phenotypes["SUB_ID"] = phenotypes["SUB_ID"].astype("string")', cell)
        cat_list = re.search(r"categorical_columns = \[(.*?)\]", cell, re.S).group(1)
        names = re.findall(r'"([^"]+)"', cat_list)
        self.assertEqual(names, ["SITE_ID", "DX_GROUP", "SEX", "HANDEDNESS_CATEGORY", "CURRENT_MED_STATUS"])

    # --- §8: info()/describe() interpretation sections removed -----------
    def test_interpreting_info_and_describe_sections_absent(self):
        for cid in ("3ad75c70-7fdf-406c-be12-7f2329dd0cb5",
                    "5284a2b7-51c1-420e-b7e9-385b64dd70ec"):
            self.assertNotIn(cid, self.by_id)
        self.assertNotIn("#### Interpreting `info()`", self.md)
        self.assertNotIn("#### Interpreting `describe()`", self.md)

    def test_essential_info_describe_caveats_folded_in_earlier(self):
        info_sec = self.by_id["4116a60a-89bb-4d4b-a6d2-132591668e11"]["source"]
        self.assertIn("shape", info_sec)
        self.assertIn("distribution", info_sec)
        desc_sec = self.by_id["0adaedf8-225f-4f29-9a93-7c4d300b1e86"]["source"]
        self.assertIn("hide", desc_sec.lower())
        self.assertIn("missing", desc_sec.lower())

    # --- §9: missing-data approaches table trimmed to <= 3 rows ----------
    def test_missing_data_table_has_at_most_three_body_rows(self):
        cell = self.by_id["a6028127-7a60-403d-9516-0472f4df8084"]["source"]
        rows = [
            ln for ln in cell.splitlines()
            if ln.strip().startswith("|") and "---" not in ln
        ]
        # header row + <= 3 body rows
        self.assertLessEqual(len(rows), 4)
        self.assertGreaterEqual(len(rows), 2)
        self.assertIn("no one strategy is always best", cell.lower())

    def test_complete_case_prose_and_code_say_13_not_39(self):
        prose = self.by_id["1b016f0b-ec2f-4f6e-831f-5198bb148471"]["source"]
        self.assertIn("13 variables", prose)
        self.assertNotIn("39", prose)
        code = self.by_id["33d94597-727c-4b58-a365-9ac1ecb4f365"]["source"]
        self.assertIn("Complete for all 13 variables", code)
        self.assertNotIn("39", code)

    # --- §10: correlation section trimmed -------------------------------
    def test_correlation_detours_removed(self):
        for cid in (
            "c4dc9fe3ee9e",  # "Participants behind each correlation" graph
            "e15470791c85",  # "When a correlation matrix is the wrong tool"
            "2c5625b060d7",  # SEX x DX_GROUP crosstab
            "458219f7acdb",  # Cramer's V sidebar
            "1e00b5ffc77d",  # "Choosing an association measure" Think first
        ):
            self.assertNotIn(cid, self.by_id)
        self.assertNotIn("When a correlation matrix is the wrong tool", self.md)
        self.assertNotIn("Participants behind each correlation", self.code_src)
        self.assertNotIn("cramers_v", self.code_src)
        self.assertNotIn("pairwise_n", self.code_src)

    def test_correlation_matrix_uses_the_curated_numeric_variables(self):
        cell = self.by_id["9b478759eff3"]["source"]
        block = re.search(r"correlation_variables = \[(.*?)\]", cell, re.S).group(1)
        names = re.findall(r'"([^"]+)"', block)
        self.assertEqual(
            names,
            ["AGE_AT_SCAN", "FIQ", "VIQ", "PIQ", "SRS_TOTAL_RAW",
             "ADOS_G_TOTAL", "ADI_R_SOCIAL_TOTAL_A"],
        )

    def test_correlation_section_ends_with_a_short_takeaway(self):
        obs = self.by_id["188d49e2ebf5"]["source"]
        self.assertIn("Practical takeaway", obs)
        self.assertIn("0.83", obs)  # FIQ ~ VIQ/PIQ definitional
        self.assertIn("0.52", obs)  # VIQ ~ PIQ

    # --- §11: head()/tail()/sample() activity --------------------------
    def test_table_inspection_activity_present_at_start_of_section_2(self):
        ids = [c["id"] for c in self.nb.cells]
        section2 = ids.index("3e4d2fad-c625-4989-a9a5-443fafa004e1")
        # next four cells are the new activity block
        self.assertEqual(
            ids[section2 + 1: section2 + 5],
            ["7a1e5c93d201", "7a1e5c93d202", "7a1e5c93d203", "7a1e5c93d204"],
        )
        iframe = self.by_id["7a1e5c93d201"]["source"]
        self.assertIn(
            'src="../../_static/widgets/app/index.html?config=../configs/table_inspection.json"',
            iframe,
        )
        self.assertIn(
            'title="Interactive head, tail, and sample comparison for the ABIDE-II table"',
            iframe,
        )

    def test_no_advance_claim_that_head_tail_are_inferior(self):
        section2 = self.by_id["3e4d2fad-c625-4989-a9a5-443fafa004e1"]["source"]
        self.assertNotIn("broader first impression", section2)
        self.assertNotIn("may not represent the entire dataset", section2)
        # the deleted single-random-sample cell and its heading are gone
        self.assertNotIn("c80dce59-8978-4314-a20b-ec0947c1f175", self.by_id)
        self.assertNotIn("7af020ab-570e-43ce-a88a-eb51b34aa8b6", self.by_id)
        self.assertNotIn("random_state=42", self.code_src)

    def test_think_first_then_explanation_then_collapsed_python_equivalent(self):
        self.assertIn("```{admonition} Think first", self.by_id["7a1e5c93d202"]["source"])
        expl = self.by_id["7a1e5c93d203"]["source"]
        self.assertIn("deterministic", expl)
        self.assertIn("random_state", expl)
        pyeq = self.by_id["7a1e5c93d204"]
        self.assertEqual(pyeq["cell_type"], "code")
        self.assertIn("hide-input", pyeq["metadata"].get("tags", []))
        self.assertIn("phenotypes.head(8)", pyeq["source"])
        self.assertIn("phenotypes.tail(8)", pyeq["source"])
        self.assertIn("phenotypes.sample(8, random_state=0)", pyeq["source"])

    # --- §12: cell / visibility counts --------------------------------
    def test_cell_and_visibility_counts(self):
        self.assertEqual(len(self.nb.cells), 76)
        self.assertEqual(len(self.code), 20)
        vis = {"visible": 0, "hide-input": 0, "hide-cell": 0, "hide-output": 0}
        for c in self.code:
            tags = set(c["metadata"].get("tags", []))
            key = next(
                (k for k in ("hide-cell", "hide-input", "hide-output") if k in tags),
                "visible",
            )
            vis[key] += 1
        self.assertEqual(vis, {"visible": 10, "hide-input": 8, "hide-cell": 2, "hide-output": 0})

    def test_valid_and_unique_ids_only_hide_tags(self):
        nbformat.validate(self.nb)
        ids = [c["id"] for c in self.nb.cells]
        self.assertEqual(len(ids), len(set(ids)))
        for c in self.nb.cells:
            for t in c["metadata"].get("tags", []):
                self.assertIn(t, {"hide-input", "hide-cell", "hide-output"})

    # --- retained essentials ------------------------------------------
    def test_seeded_stripplot_preserved(self):
        cell = self.by_id["80632a35b296"]["source"]
        self.assertIn("np.random.seed(0)", cell)
        self.assertIn("np.random.get_state()", cell)
        self.assertIn("np.random.set_state(", cell)

    def test_histogram_example_cell_preserved(self):
        hist = self.by_id["e6f7a8b9c0d1"]
        self.assertIn("hide-input", hist["metadata"].get("tags", []))
        self.assertIn('x="AGE_AT_SCAN"', hist["source"])
        self.assertIn("bins=25", hist["source"])

    def test_iqr_range_check_still_flags_56(self):
        text = _output_text(self.by_id["7bf82a8cd5a9"])
        self.assertIn("56 of 1114 participants flagged", text)


def _output_text(cell) -> str:
    parts: list[str] = []
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream":
            parts.append(out.get("text", ""))
        elif "data" in out:
            plain = out["data"].get("text/plain", "")
            parts.append("".join(plain) if isinstance(plain, list) else plain)
    return "\n".join(parts)


if __name__ == "__main__":
    unittest.main()
