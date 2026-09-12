"""WP10 §2: the table-inspection activity shows all 13 curated columns, in the
exact order of book/config/eda_phenotype_columns.json, and its committed data
artifact carries every one of them (SUB_ID included).

Offline; standard-library unittest only.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = REPO_ROOT / "book" / "config" / "eda_phenotype_columns.json"
CONFIG = REPO_ROOT / "book" / "_static" / "widgets" / "configs" / "table_inspection.json"
ARTIFACT = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "abide_table_inspection.json"


class TableInspectionColumns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_authority_is_the_13_column_list(self):
        self.assertEqual(len(self.authority), 13)
        self.assertEqual(self.authority[0], "SITE_ID")
        self.assertIn("SUB_ID", self.authority)

    def test_config_columns_match_the_authority_in_order(self):
        names = [c["name"] for c in self.config["columns"]]
        self.assertEqual(names, self.authority)
        # every displayed column has a human label
        self.assertTrue(all(c.get("label") for c in self.config["columns"]))
        self.assertEqual(self.config["data"], "../data/abide_table_inspection.json")
        self.assertEqual(self.config["siteField"], "SITE_ID")

    def test_artifact_carries_every_curated_column_in_order(self):
        self.assertEqual(self.artifact["activity"], "table-inspection")
        self.assertEqual(self.artifact["columnOrder"], self.authority)
        self.assertEqual(sorted(self.artifact["columns"]), sorted(self.authority))
        self.assertEqual(self.artifact["identifierFields"], ["SITE_ID", "SUB_ID"])
        self.assertEqual(self.artifact["rowCount"], 1114)
        # the two identifier columns are complete strings
        for field in ("SITE_ID", "SUB_ID"):
            col = self.artifact["columns"][field]
            self.assertEqual(len(col), 1114)
            self.assertTrue(all(isinstance(v, str) and v for v in col))


if __name__ == "__main__":
    unittest.main()
