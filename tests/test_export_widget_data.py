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
    "DX_GROUP",
    "SEX",
    "CURRENT_MED_STATUS",
    "HANDEDNESS_CATEGORY",
]

# 4 data rows; leading/trailing spaces on headers on purpose.
FIXTURE_CSV = (
    " SUB_ID , SITE_ID , AGE_AT_SCAN , FIQ , SCQ_TOTAL \n"
    "1,ABC,10.5,100,\n"
    "2,ABC,,95,12\n"
    "3,DEF,21.0,,7\n"
    "4,DEF,8.25,110,0\n"
).encode("latin-1")

# 6 rows across 3 sites for the retention artifact. Includes a valid 0
# (CURRENT_MED_STATUS), documented integer category codes, floats, and nulls.
RETENTION_FIXTURE_CSV = (
    "SUB_ID,SITE_ID,DX_GROUP,AGE_AT_SCAN,SEX,FIQ,CURRENT_MED_STATUS\n"
    "1,SiteB,1,10.5,1,100,0\n"
    "2,SiteB,2,,1,95,1\n"
    "3,SiteA,1,21.0,2,,0\n"
    "4,SiteA,2,8.25,2,110,\n"
    "5,SiteA,1,12.0,1,105,1\n"
    "6,SiteC,2,15.0,1,,0\n"
).encode("latin-1")

RETENTION_VARS = ["DX_GROUP", "AGE_AT_SCAN", "SEX", "FIQ", "CURRENT_MED_STATUS"]


def build_fixture_frame():
    return ew.parse_csv(FIXTURE_CSV)


def build_retention_frame():
    return ew.parse_csv(RETENTION_FIXTURE_CSV)


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


class BuildRetentionArtifactTests(unittest.TestCase):
    def good(self):
        frame = build_retention_frame()
        return ew.build_retention_artifact(frame, RETENTION_VARS, ALLOWED)

    def test_happy_path_shape_and_metadata(self):
        art = self.good()
        self.assertEqual(art["activity"], "eda-retention")
        self.assertEqual(art["schemaVersion"], ew.SCHEMA_VERSION)
        self.assertEqual(art["rowCount"], 6)
        # SITE_ID is the first column key and every candidate follows.
        self.assertIn("SITE_ID", art["columns"])
        self.assertEqual(set(art["columns"]) - {"SITE_ID"}, set(RETENTION_VARS))
        # aligned lengths
        for name, values in art["columns"].items():
            self.assertEqual(len(values), 6, name)
        # per-variable available/missing counts
        meta = {m["name"]: m for m in art["variables"]}
        self.assertEqual(meta["FIQ"]["availableN"], 4)
        self.assertEqual(meta["FIQ"]["missingN"], 2)
        self.assertEqual(meta["AGE_AT_SCAN"]["availableN"], 5)
        self.assertEqual(meta["DX_GROUP"]["availableN"], 6)
        self.assertEqual(meta["CURRENT_MED_STATUS"]["availableN"], 5)  # a real 0 is present, 1 null

    def test_valid_zero_is_not_missing(self):
        art = self.good()
        self.assertEqual(art["columns"]["CURRENT_MED_STATUS"], [0, 1, 0, None, 1, 0])
        meta = {m["name"]: m for m in art["variables"]}
        self.assertEqual(meta["CURRENT_MED_STATUS"]["availableN"], 5)
        self.assertEqual(meta["CURRENT_MED_STATUS"]["missingN"], 1)

    def test_categories_preserved_as_documented_codes(self):
        art = self.good()
        self.assertEqual(art["columns"]["DX_GROUP"], [1, 2, 1, 2, 1, 2])
        self.assertEqual(art["columns"]["SEX"], [1, 1, 2, 2, 1, 1])

    def test_null_and_alignment_preserved_in_row_order(self):
        art = self.good()
        self.assertEqual(art["columns"]["FIQ"], [100, 95, None, 110, 105, None])
        self.assertEqual(art["columns"]["AGE_AT_SCAN"], [10.5, None, 21, 8.25, 12, 15])
        self.assertEqual(art["columns"]["SITE_ID"], ["SiteB", "SiteB", "SiteA", "SiteA", "SiteA", "SiteC"])

    def test_site_metadata_is_first_appearance_order(self):
        art = self.good()
        self.assertEqual(art["site"]["field"], "SITE_ID")
        self.assertEqual(art["site"]["siteCount"], 3)
        self.assertEqual(
            art["site"]["sites"],
            [
                {"label": "SiteB", "total": 2},
                {"label": "SiteA", "total": 3},
                {"label": "SiteC", "total": 1},
            ],
        )
        self.assertEqual(sum(s["total"] for s in art["site"]["sites"]), art["rowCount"])

    def test_site_id_is_the_only_allowed_identifier_shaped_field(self):
        # SITE_ID itself trips the identifier regex, but the retention builder
        # lets exactly that one name through.
        self.assertTrue(ew.looks_like_identifier("SITE_ID"))
        art = self.good()
        self.assertIn("SITE_ID", art["columns"])

    def test_rejects_sub_id_as_a_selected_variable(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["SUB_ID", "FIQ"], ALLOWED)

    def test_rejects_arbitrary_id_field(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["SCANNER_ID"], ALLOWED + ["SCANNER_ID"])

    def test_rejects_site_field_as_a_selected_variable(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["SITE_ID", "FIQ"], ALLOWED)

    def test_rejects_non_site_id_site_field(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, RETENTION_VARS, ALLOWED, site_field="SITE_NAME")

    def test_rejects_variable_missing_from_source(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["VIQ"], ALLOWED)

    def test_rejects_variable_not_in_curated_authority(self):
        frame = build_retention_frame()
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["FIQ"], ["SITE_ID"])

    def test_rejects_missing_site_label(self):
        csv = (
            "SUB_ID,SITE_ID,FIQ\n"
            "1,SiteA,100\n"
            "2,,95\n"
        ).encode("latin-1")
        frame = ew.parse_csv(csv)
        with self.assertRaises(ValueError):
            ew.build_retention_artifact(frame, ["FIQ"], ALLOWED)


class ValidateRetentionArtifactTests(unittest.TestCase):
    def good(self):
        frame = build_retention_frame()
        return ew.build_retention_artifact(frame, RETENTION_VARS, ALLOWED)

    def test_good_artifact_passes(self):
        self.assertEqual(ew.validate_retention_artifact(self.good(), ALLOWED), [])

    def test_catches_missing_site_column(self):
        art = self.good()
        del art["columns"]["SITE_ID"]
        problems = ew.validate_retention_artifact(art, ALLOWED)
        self.assertTrue(any("SITE_ID" in p for p in problems), problems)

    def test_catches_null_in_site_column(self):
        art = self.good()
        art["columns"]["SITE_ID"][0] = None
        self.assertTrue(
            any("site column" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_identifier_column_other_than_site(self):
        art = self.good()
        art["columns"]["SUB_ID"] = [None] * art["rowCount"]
        self.assertTrue(
            any("identifier-like" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_wrong_activity(self):
        art = self.good()
        art["activity"] = "eda-histogram"
        self.assertTrue(
            any("activity" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_unaligned_column(self):
        art = self.good()
        art["columns"]["FIQ"].append(1)
        self.assertTrue(
            any("FIQ" in p and "values" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_site_total_mismatch(self):
        art = self.good()
        art["site"]["sites"][0]["total"] = 999
        self.assertTrue(
            any("total" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_site_order_not_first_appearance(self):
        art = self.good()
        art["site"]["sites"] = list(reversed(art["site"]["sites"]))
        self.assertTrue(
            any("first-appearance" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )

    def test_catches_bad_available_n(self):
        art = self.good()
        art["variables"][0]["availableN"] += 1
        self.assertTrue(
            any("availableN" in p for p in ew.validate_retention_artifact(art, ALLOWED))
        )


class RetentionSerializationTests(unittest.TestCase):
    def test_deterministic_round_trip(self):
        frame = build_retention_frame()
        art = ew.build_retention_artifact(frame, RETENTION_VARS, ALLOWED)
        text = ew.serialize(art)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(text, ew.serialize(json.loads(text)))
        reloaded = json.loads(text)
        self.assertEqual(ew.validate_retention_artifact(reloaded, ALLOWED), [])


class ArtifactRegistryTests(unittest.TestCase):
    def test_both_modes_are_registered_and_distinct(self):
        self.assertEqual(set(ew.ARTIFACTS), {"histogram", "retention"})
        self.assertNotEqual(
            ew.ARTIFACTS["histogram"].path, ew.ARTIFACTS["retention"].path
        )
        self.assertEqual(ew.ARTIFACTS["histogram"].path.name, "abide_histogram.json")
        self.assertEqual(ew.ARTIFACTS["retention"].path.name, "abide_retention.json")

    def test_selector_scopes_to_one_artifact(self):
        self.assertEqual([s.key for s in ew._selected_specs("histogram")], ["histogram"])
        self.assertEqual([s.key for s in ew._selected_specs("retention")], ["retention"])
        self.assertEqual(
            sorted(s.key for s in ew._selected_specs("all")), ["histogram", "retention"]
        )

    def test_committed_artifacts_pass_their_own_validators(self):
        # Offline: the real committed files validate under the real authority.
        allowed = ew.read_allowed_columns(ew.ALLOWED_COLUMNS_PATH)
        for spec in ew.ARTIFACTS.values():
            data = json.loads(spec.path.read_text(encoding="utf-8"))
            self.assertEqual(spec.validate(data, allowed), [], spec.key)


if __name__ == "__main__":
    unittest.main()
