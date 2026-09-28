"""Offline schema/consistency tests for book/config/exercise_manifest.json.

WP41 section 4.3/12: one machine-readable manifest for Exercises 1-12, with
exactly Exercise 2 marked migrated in this WP, and unique routes/paths across
entries.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_exercise_manifest.py'
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "book" / "config" / "exercise_manifest.json"

REQUIRED_FIELDS = {
    "number",
    "title",
    "migrationState",
    "legacyStaticPagePath",
    "templateNotebookPath",
    "browserWorkingCopyName",
    "liteUrl",
    "templateVersion",
    "dataAssets",
    "extraPackages",
    "fallbackDownloadablePath",
}


class ExerciseManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text())
        cls.exercises = cls.manifest["exercises"]

    def test_schema_version(self):
        self.assertEqual(self.manifest["schemaVersion"], 1)

    def test_covers_exercises_1_through_12(self):
        numbers = [e["number"] for e in self.exercises]
        self.assertEqual(numbers, list(range(1, 13)))

    def test_every_entry_has_required_fields(self):
        for e in self.exercises:
            self.assertEqual(set(e.keys()), REQUIRED_FIELDS, e)

    def test_only_exercise_2_is_migrated(self):
        migrated = [e["number"] for e in self.exercises if e["migrationState"] == "migrated"]
        self.assertEqual(migrated, [2])
        for e in self.exercises:
            self.assertIn(e["migrationState"], {"migrated", "legacy"})

    def test_migrated_entries_have_lite_wiring_legacy_entries_do_not(self):
        for e in self.exercises:
            if e["migrationState"] == "migrated":
                self.assertIsNotNone(e["templateNotebookPath"])
                self.assertIsNotNone(e["browserWorkingCopyName"])
                self.assertIsNotNone(e["liteUrl"])
                self.assertIsNotNone(e["templateVersion"])
            else:
                self.assertIsNone(e["templateNotebookPath"])
                self.assertIsNone(e["browserWorkingCopyName"])
                self.assertIsNone(e["liteUrl"])
                self.assertIsNone(e["templateVersion"])

    def test_routes_and_paths_are_unique(self):
        for key in ("legacyStaticPagePath", "templateNotebookPath", "liteUrl", "fallbackDownloadablePath"):
            values = [e[key] for e in self.exercises if e[key] is not None]
            self.assertEqual(len(values), len(set(values)), f"duplicate {key} values: {values}")

    def test_legacy_static_page_paths_exist_on_disk(self):
        for e in self.exercises:
            path = REPO_ROOT / "book" / e["legacyStaticPagePath"]
            self.assertTrue(path.exists(), path)

    def test_exercise_2_data_assets_exist_on_disk(self):
        ex2 = next(e for e in self.exercises if e["number"] == 2)
        for rel in ex2["dataAssets"]:
            self.assertTrue((REPO_ROOT / rel).exists(), rel)

    def test_migrated_template_versions_match_notebook_metadata(self):
        # WP42 Gate 1: this manifest's own templateVersion drifted from the
        # generated notebook's `metadata.wp41.templateVersion` after WP41R
        # bumped only the notebook (see WPs/reports/WP41R_REPORT.md
        # "Deviations"). Only the generator writes notebook metadata and only
        # a human edits this manifest, so nothing previously checked they
        # agreed; this test is that check, for every migrated exercise, not
        # just Exercise 2.
        import nbformat

        for e in self.exercises:
            if e["migrationState"] != "migrated":
                continue
            nb = nbformat.read(REPO_ROOT / e["templateNotebookPath"], as_version=4)
            notebook_version = nb["metadata"]["wp41"]["templateVersion"]
            self.assertEqual(
                e["templateVersion"],
                notebook_version,
                f"exercise {e['number']}: manifest templateVersion "
                f"({e['templateVersion']}) != notebook metadata ({notebook_version})",
            )

    def test_common_packages_present(self):
        common = self.manifest["commonPackages"]
        for pkg in ("numpy", "pandas", "scikit-learn", "matplotlib", "ipywidgets"):
            self.assertIn(pkg, common)


if __name__ == "__main__":
    unittest.main()
