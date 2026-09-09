"""Offline unit tests for scripts/export_widget_data.py.

Standard-library ``unittest`` only. Uses tiny in-memory CSV fixtures; never
touches the network or the committed artifact.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_widget_data as ew  # noqa: E402


ALLOWED = [
    "AGE_AT_SCAN",
    "FIQ",
    "VIQ",
    "PIQ",
    "ADOS_G_TOTAL",
    "ADOS_2_TOTAL",
    "SRS_TOTAL_RAW",
    "SCQ_TOTAL",
    "SUB_ID",
    "SITE_ID",
]

# 4 data rows; leading/trailing spaces on headers on purpose.
FIXTURE_CSV = (
    " SUB_ID , SITE_ID , AGE_AT_SCAN , FIQ , SCQ_TOTAL \n"
    "1,ABC,10.5,100,\n"
    "2,ABC,,95,12\n"
    "3,DEF,21.0,,7\n"
    "4,DEF,8.25,110,0\n"
).encode("latin-1")


def build_fixture_frame():
    return ew.parse_csv(FIXTURE_CSV)


class HelperTests(unittest.TestCase):
    def test_sha256_hex_is_deterministic(self):
        self.assertEqual(ew.sha256_hex(b"abc"), ew.sha256_hex(b"abc"))
        self.assertEqual(
            ew.sha256_hex(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_looks_like_identifier(self):
        for name in ("SUB_ID", "SITE_ID", "sub_id", "PARTICIPANT_NAME", "GUID"):
            self.assertTrue(ew.looks_like_identifier(name), name)
        for name in ("AGE_AT_SCAN", "FIQ", "SCQ_TOTAL", "ADOS_G_TOTAL", "SRS_TOTAL_RAW"):
            self.assertFalse(ew.looks_like_identifier(name), name)

    def test_parse_csv_strips_headers(self):
        frame = build_fixture_frame()
        self.assertIn("AGE_AT_SCAN", frame.columns)
        self.assertIn("SUB_ID", frame.columns)
        self.assertEqual(len(frame), 4)

    def test_observation_mapping(self):
        self.assertIsNone(ew._observation(None))
        self.assertIsNone(ew._observation(float("nan")))
        self.assertEqual(ew._observation(21.0), 3 * 7)  # int, not 21.0
        self.assertIsInstance(ew._observation(21.0), int)
        self.assertEqual(ew._observation(10.5), 10.5)
        self.assertIsInstance(ew._observation(10.5), float)

    def test_observation_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            ew._observation(float("inf"))

    def test_column_to_json_values_row_order_and_nulls(self):
        frame = build_fixture_frame()
        self.assertEqual(ew.column_to_json_values(frame["AGE_AT_SCAN"]), [10.5, None, 21, 8.25])
        self.assertEqual(ew.column_to_json_values(frame["SCQ_TOTAL"]), [None, 12, 7, 0])


class BuildArtifactTests(unittest.TestCase):
    def test_happy_path(self):
        frame = build_fixture_frame()
        artifact = ew.build_artifact(frame, ["AGE_AT_SCAN", "FIQ", "SCQ_TOTAL"], ALLOWED)
        self.assertEqual(artifact["schemaVersion"], ew.SCHEMA_VERSION)
        self.assertEqual(artifact["rowCount"], 4)
        self.assertEqual(set(artifact["columns"]), {"AGE_AT_SCAN", "FIQ", "SCQ_TOTAL"})
        self.assertEqual(len(artifact["columns"]["FIQ"]), 4)
        meta = {m["name"]: m for m in artifact["variables"]}
        self.assertEqual(meta["FIQ"]["availableN"], 3)
        self.assertEqual(meta["FIQ"]["missingN"], 1)
        self.assertEqual(meta["AGE_AT_SCAN"]["availableN"], 3)
        self.assertNotIn("SUB_ID", artifact["columns"])

    def test_rejects_column_not_in_allowed_authority(self):
        frame = build_fixture_frame()
        with self.assertRaises(ValueError):
            ew.build_artifact(frame, ["AGE_AT_SCAN"], ["FIQ"])  # AGE_AT_SCAN not allowed

    def test_rejects_identifier_like_variable(self):
        frame = build_fixture_frame()
        with self.assertRaises(ValueError):
            ew.build_artifact(frame, ["SUB_ID"], ALLOWED)

    def test_rejects_missing_source_column(self):
        frame = build_fixture_frame()
        with self.assertRaises(ValueError):
            ew.build_artifact(frame, ["VIQ"], ALLOWED)  # not in fixture CSV


class ValidateArtifactTests(unittest.TestCase):
    def good_artifact(self):
        frame = build_fixture_frame()
        return ew.build_artifact(frame, ["AGE_AT_SCAN", "FIQ", "SCQ_TOTAL"], ALLOWED)

    def test_good_artifact_passes(self):
        self.assertEqual(ew.validate_artifact(self.good_artifact(), ALLOWED), [])

    def test_catches_wrong_row_count_array(self):
        art = self.good_artifact()
        art["columns"]["FIQ"].append(1)
        problems = ew.validate_artifact(art, ALLOWED)
        self.assertTrue(any("FIQ" in p and "values" in p for p in problems), problems)

    def test_catches_non_number_value(self):
        art = self.good_artifact()
        art["columns"]["FIQ"][0] = "oops"
        self.assertTrue(any("number-or-null" in p for p in ew.validate_artifact(art, ALLOWED)))

    def test_catches_identifier_key(self):
        art = self.good_artifact()
        art["columns"]["SUB_ID"] = [None, None, None, None]
        self.assertTrue(any("identifier-like" in p for p in ew.validate_artifact(art, ALLOWED)))

    def test_catches_bad_available_n(self):
        art = self.good_artifact()
        art["variables"][0]["availableN"] += 1
        self.assertTrue(any("availableN" in p for p in ew.validate_artifact(art, ALLOWED)))

    def test_catches_wrong_schema_version(self):
        art = self.good_artifact()
        art["schemaVersion"] = 999
        self.assertTrue(any("schemaVersion" in p for p in ew.validate_artifact(art, ALLOWED)))


class SerializeTests(unittest.TestCase):
    def test_deterministic_sorted_and_trailing_newline(self):
        frame = build_fixture_frame()
        art = ew.build_artifact(frame, ["FIQ", "AGE_AT_SCAN"], ALLOWED)
        text = ew.serialize(art)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(text, ew.serialize(json.loads(text)))
        # keys are sorted: "activity" before "columns" before "schemaVersion"
        self.assertLess(text.index('"activity"'), text.index('"columns"'))
        self.assertLess(text.index('"columns"'), text.index('"schemaVersion"'))

    def test_round_trip_build_serialize_validate(self):
        frame = build_fixture_frame()
        art = ew.build_artifact(frame, ["AGE_AT_SCAN", "FIQ", "SCQ_TOTAL"], ALLOWED)
        reloaded = json.loads(ew.serialize(art))
        self.assertEqual(ew.validate_artifact(reloaded, ALLOWED), [])

    def test_rejects_nan_on_serialize(self):
        with self.assertRaises(ValueError):
            ew.serialize({"x": math.nan})


if __name__ == "__main__":
    unittest.main()
