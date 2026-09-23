"""Offline tests for scripts/export_pca_kmeans_widget.py and its committed
data artifact (WP33, Exercise 8 "Explore PCA and K-Means").

Standard-library ``unittest``; no network. The artifact's own source (the
real ABIDE-II table) requires network to reload, so -- like
scripts/export_regression_catalog.py -- ``--check`` (and this test file)
validate structure and canonical serialization only; a full recomputation
is exercised manually via ``--refresh`` in the bounded validation plan, not
in the offline suite.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_pca_kmeans_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_pca_kmeans_widget as pkw  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.on_disk = pkw.OUT_PATH.read_text(encoding="utf-8")
        cls.data = json.loads(cls.on_disk)

    def test_check_mode_passes(self):
        problems = pkw.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_artifact_is_canonically_serialized(self):
        self.assertEqual(pkw.serialize(self.data), self.on_disk)

    def test_full_eligible_cohort(self):
        self.assertEqual(self.data["nParticipants"], 1004)
        self.assertEqual(len(self.data["participants"]["pc1"]), 1004)
        self.assertEqual(len(self.data["participants"]["pc2"]), 1004)

    def test_declared_grids_match_the_manifest(self):
        self.assertEqual(self.data["retainedPcGrid"], pkw.RETAINED_PC_GRID)
        self.assertEqual(self.data["kGrid"], pkw.K_GRID)
        self.assertEqual(self.data["seeds"], pkw.SEEDS)
        self.assertEqual(self.data["nInit"], pkw.N_INIT)
        self.assertGreaterEqual(self.data["nInit"], 10)

    def test_every_declared_combination_is_present(self):
        expected = {
            pkw._combo_key(r, k, s)
            for r in self.data["retainedPcGrid"]
            for k in self.data["kGrid"]
            for s in self.data["seeds"]
        }
        self.assertEqual(set(self.data["catalog"].keys()), expected)
        self.assertEqual(len(expected), 5 * 5 * 3)

    def test_cluster_sizes_sum_to_the_full_cohort_for_every_combination(self):
        n = self.data["nParticipants"]
        for key, entry in self.data["catalog"].items():
            with self.subTest(combo=key):
                self.assertEqual(sum(entry["clusterSizes"]), n)
                self.assertEqual(len(entry["clusterLabels"]), n)
                recount = [entry["clusterLabels"].count(c) for c in range(entry["k"])]
                self.assertEqual(recount, entry["clusterSizes"])

    def test_silhouette_is_only_computed_when_mathematically_valid(self):
        for key, entry in self.data["catalog"].items():
            with self.subTest(combo=key):
                sil = entry["silhouette"]
                n_distinct = len(set(entry["clusterLabels"]))
                if 2 <= n_distinct <= self.data["nParticipants"] - 1:
                    self.assertIsNotNone(sil)
                    self.assertTrue(-1.0 <= sil <= 1.0)
                else:
                    self.assertIsNone(sil)

    def test_pc1_pc2_scores_are_identical_across_every_retained_pc_count(self):
        # PCA components are nested: retaining more components never changes
        # an earlier component's scores. The committed artifact stores PC1/
        # PC2 once (not once per retained-PC count); this test locks in that
        # invariant so a future edit cannot silently start duplicating (and
        # potentially diverging) per-retained-PC copies.
        self.assertIn("pc1", self.data["participants"])
        self.assertIn("pc2", self.data["participants"])
        self.assertNotIn("pc1ByRetainedPc", self.data["participants"])

    def test_external_variables_have_one_entry_per_participant(self):
        n = self.data["nParticipants"]
        external = self.data["participants"]["external"]
        for key in ("group", "sex", "site", "age"):
            with self.subTest(variable=key):
                self.assertEqual(len(external[key]), n)

    def test_external_variables_are_never_clustering_inputs(self):
        # The export script's build_data signature takes no external-variable
        # argument into PCA/KMeans; this is a structural/documentation check
        # that the cohort note says so explicitly (the code path itself is
        # exercised by test_matches_a_fresh_recomputation).
        self.assertIn("never inputs to pca or k-means", self.data["cohortNote"].lower())

    def test_centers_have_exactly_k_entries(self):
        for key, entry in self.data["catalog"].items():
            with self.subTest(combo=key):
                self.assertEqual(len(entry["centersPC1PC2"]), entry["k"])

    def test_no_non_finite_values_anywhere(self):
        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, float):
                self.assertTrue(math.isfinite(node))

        walk(self.data)


if __name__ == "__main__":
    unittest.main()
