"""Offline tests for scripts/export_svm_explorer_widget.py and its
committed data artifact (WP34, Exercise 9 "Explore an SVM Boundary").

Standard-library ``unittest``; no network -- both datasets are entirely
synthetic. Recomputes structural invariants independently, and re-validates
the full artifact against a fresh recomputation (the export script itself
takes tens of seconds, so this suite reuses the committed artifact rather
than recomputing it per test).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_export_svm_explorer_widget_data.py'
"""

from __future__ import annotations

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import export_svm_explorer_widget as sew  # noqa: E402


class CommittedArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(sew.OUT_PATH.read_text(encoding="utf-8"))

    def test_check_mode_passes(self):
        problems = sew.validate(self.data)
        self.assertEqual(problems, [], problems)

    def test_explicitly_marked_synthetic(self):
        note = self.data["syntheticDataNote"].lower()
        self.assertTrue("synthetic" in note or "simulated" in note)
        self.assertIn("not abide", note)

    def test_both_datasets_present_with_the_declared_observation_count(self):
        for dataset in sew.DATASETS:
            d = self.data["datasets"][dataset]
            self.assertEqual(len(d["points"]), sew.N_OBSERVATIONS)

    def test_train_and_val_ids_partition_every_point_exactly_once(self):
        for dataset in sew.DATASETS:
            d = self.data["datasets"][dataset]
            train_ids = set(d["trainIds"])
            val_ids = set(d["valIds"])
            self.assertEqual(len(train_ids), sew.N_TRAIN)
            self.assertEqual(train_ids & val_ids, set())
            self.assertEqual(train_ids | val_ids, set(range(sew.N_OBSERVATIONS)))

    def test_every_declared_grid_combination_present(self):
        for dataset in sew.DATASETS:
            catalog = self.data["datasets"][dataset]["catalog"]
            for kernel in sew.KERNELS:
                gammas = [None] if kernel == "linear" else sew.GAMMA_GRID
                for c in sew.C_GRID:
                    for gamma in gammas:
                        self.assertIn(sew._combo_key(dataset, kernel, c, gamma), catalog)

    def test_support_vectors_are_always_training_rows(self):
        for dataset in sew.DATASETS:
            d = self.data["datasets"][dataset]
            train_ids = set(d["trainIds"])
            for key, entry in d["catalog"].items():
                with self.subTest(dataset=dataset, key=key):
                    self.assertTrue(set(entry["supportVectorIds"]).issubset(train_ids))
                    self.assertEqual(entry["nSupportVectors"], len(entry["supportVectorIds"]))

    def test_decision_grid_rows_are_binary_digit_strings_of_the_declared_resolution(self):
        for dataset in sew.DATASETS:
            d = self.data["datasets"][dataset]
            for key, entry in d["catalog"].items():
                grid = entry["decisionGrid"]
                self.assertEqual(len(grid), sew.GRID_RES, key)
                for row in grid:
                    self.assertEqual(len(row), sew.GRID_RES, key)
                    self.assertTrue(set(row).issubset({"0", "1"}), key)

    def test_linear_kernel_separates_the_linear_dataset_far_better_than_the_nonlinear_one(self):
        linear_cat = self.data["datasets"]["linear"]["catalog"]
        nonlinear_cat = self.data["datasets"]["nonlinear"]["catalog"]
        linear_acc = max(e["valAccuracy"] for e in linear_cat.values() if e["kernel"] == "linear")
        nonlinear_acc = max(e["valAccuracy"] for e in nonlinear_cat.values() if e["kernel"] == "linear")
        self.assertGreater(linear_acc, nonlinear_acc)
        self.assertGreaterEqual(linear_acc, 0.9)

    def test_gamma_is_null_only_for_the_linear_kernel(self):
        for dataset in sew.DATASETS:
            for entry in self.data["datasets"][dataset]["catalog"].values():
                if entry["kernel"] == "linear":
                    self.assertIsNone(entry["gamma"])
                else:
                    self.assertIsNotNone(entry["gamma"])

    def test_accuracies_are_valid_proportions(self):
        for dataset in sew.DATASETS:
            for entry in self.data["datasets"][dataset]["catalog"].values():
                self.assertGreaterEqual(entry["trainAccuracy"], 0.0)
                self.assertLessEqual(entry["trainAccuracy"], 1.0)
                self.assertGreaterEqual(entry["valAccuracy"], 0.0)
                self.assertLessEqual(entry["valAccuracy"], 1.0)

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
