"""Offline tests for scripts/semantic_json_compare.py (WP31R): the strict
recursive semantic comparator used to verify the Exercise 6 greedy-tree
artifact against a fresh recomputation without relying on cross-platform-
invalid byte-for-byte float equality.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_semantic_json_compare.py'
"""

from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from semantic_json_compare import (  # noqa: E402
    DEFAULT_ABS_TOL,
    SemanticMismatch,
    assert_semantically_equal,
    semantic_diff,
)


def nested(reduction: float) -> dict:
    return {
        "rounds": [
            {
                "id": "root",
                "optimal": {"feature": "x1", "threshold": 3.25, "reduction": reduction},
                "candidates": {"x1": {"reduction": [0.1, reduction, 6.20928]}},
            }
        ],
        "generatingProcess": {"selectedSeed": 17},
    }


class SemanticDiffTests(unittest.TestCase):
    def test_accepts_float_difference_smaller_than_tolerance(self):
        a = nested(15.975361)
        b = nested(15.975361 + DEFAULT_ABS_TOL / 2)
        self.assertIsNone(semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL))
        assert_semantically_equal(a, b, abs_tol=DEFAULT_ABS_TOL)  # does not raise

    def test_rejects_float_difference_larger_than_tolerance(self):
        a = nested(15.975361)
        b = nested(15.975361 + DEFAULT_ABS_TOL * 10)
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertIsInstance(mismatch, SemanticMismatch)
        with self.assertRaises(AssertionError):
            assert_semantically_equal(a, b, abs_tol=DEFAULT_ABS_TOL)

    def test_rejects_changed_selected_seed(self):
        a = nested(1.0)
        b = nested(1.0)
        b["generatingProcess"]["selectedSeed"] = 18
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.generatingProcess.selectedSeed")

    def test_rejects_changed_optimal_feature_or_threshold_beyond_tolerance(self):
        a = nested(1.0)
        b_feature = nested(1.0)
        b_feature["rounds"][0]["optimal"]["feature"] = "x2"
        mismatch = semantic_diff(a, b_feature, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.rounds[0].optimal.feature")

        b_threshold = nested(1.0)
        b_threshold["rounds"][0]["optimal"]["threshold"] = 3.25 + 1.0
        mismatch = semantic_diff(a, b_threshold, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.rounds[0].optimal.threshold")

    def test_rejects_missing_dictionary_key(self):
        a = {"x": 1, "y": 2}
        b = {"x": 1}
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertIn("key mismatch", mismatch.reason)
        self.assertIn("missing", mismatch.reason)

    def test_rejects_extra_dictionary_key(self):
        a = {"x": 1}
        b = {"x": 1, "y": 2}
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertIn("key mismatch", mismatch.reason)
        self.assertIn("extra", mismatch.reason)

    def test_rejects_changed_list_order(self):
        a = {"xs": [1, 2, 3]}
        b = {"xs": [1, 3, 2]}
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.xs[1]")

    def test_rejects_changed_list_length(self):
        a = {"xs": [1, 2, 3]}
        b = {"xs": [1, 2, 3, 4]}
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.xs")
        self.assertIn("length", mismatch.reason)

    def test_reports_the_relevant_nested_json_path(self):
        a = nested(1.0)
        b = nested(1.0)
        b["rounds"][0]["candidates"]["x1"]["reduction"][2] = 999.0
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.rounds[0].candidates.x1.reduction[2]")

    def test_rejects_non_finite_numeric_values(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(bad=bad):
                a = nested(1.0)
                b = nested(bad)
                mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
                self.assertIsNotNone(mismatch)
                self.assertIn("non-finite", mismatch.reason)

    def test_rejects_non_finite_even_when_both_sides_agree(self):
        # NaN/inf must never be silently accepted, even if committed and
        # recomputed both happen to carry the same non-finite value.
        a = nested(float("nan"))
        b = nested(float("nan"))
        mismatch = semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL)
        self.assertIsNotNone(mismatch)
        self.assertIn("non-finite", mismatch.reason)

    def test_rejects_changed_boolean(self):
        mismatch = semantic_diff({"ok": True}, {"ok": False}, abs_tol=DEFAULT_ABS_TOL)
        self.assertEqual(mismatch.path, "$.ok")

    def test_rejects_integer_masquerading_as_bool_or_vice_versa(self):
        mismatch = semantic_diff({"ok": True}, {"ok": 1}, abs_tol=DEFAULT_ABS_TOL)
        self.assertIsNotNone(mismatch)

    def test_identical_structures_match(self):
        a = nested(1.0)
        b = nested(1.0)
        self.assertIsNone(semantic_diff(a, b, abs_tol=DEFAULT_ABS_TOL))


if __name__ == "__main__":
    unittest.main()
