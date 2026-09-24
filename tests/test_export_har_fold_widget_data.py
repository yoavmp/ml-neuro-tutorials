"""Offline tests for scripts/export_har_fold_widget_data.py and its committed
artifact (WP38 sec 8.3). Reuses uci_har_data.compute_fold_comparison
unchanged, so these numbers cannot drift from the mandatory preflight audit.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_har_fold_widget_data.py'
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_har_fold_widget_data as ehfwd  # noqa: E402
import har_group_leakage_audit as hgla  # noqa: E402
from uci_har_data import load_compact_table  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = json.loads(ehfwd.ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = ehfwd.validate_artifact(self.artifact)
        self.assertEqual(problems, [], problems)

    def test_canonical_serialization(self):
        on_disk = ehfwd.ARTIFACT_PATH.read_text(encoding="utf-8")
        self.assertEqual(ehfwd.serialize(self.artifact), on_disk)

    def test_matches_the_audited_preflight_numbers(self):
        preflight = json.loads(hgla.RESULT_PATH.read_text(encoding="utf-8"))
        for widget_k, audit_k in zip(self.artifact["kResults"], preflight["comparison"]["kResults"]):
            self.assertEqual(widget_k["k"], audit_k["k"])
            self.assertEqual(widget_k["ordinary"]["accMean"], audit_k["ordinary"]["accMean"])
            self.assertEqual(widget_k["grouped"]["accMean"], audit_k["grouped"]["accMean"])

    def test_thirty_participants_with_fold_assignments(self):
        self.assertEqual(len(self.artifact["participantFolds"]), 30)
        for p in self.artifact["participantFolds"]:
            self.assertIn("participantId", p)
            self.assertIn("ordinaryFolds", p)
            self.assertIn("groupedFold", p)

    def test_no_participant_identifier_shaped_keys_at_top_level(self):
        for key in self.artifact:
            self.assertNotIn(key.lower(), ("sub", "subject", "site"))


class BuildFromScratch(unittest.TestCase):
    def test_build_artifact_is_deterministic(self):
        frame = load_compact_table()
        a = ehfwd.build_artifact(frame)
        b = ehfwd.build_artifact(frame)
        self.assertEqual(ehfwd.serialize(a), ehfwd.serialize(b))


if __name__ == "__main__":
    unittest.main()
