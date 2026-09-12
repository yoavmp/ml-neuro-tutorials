"""Offline tests for scripts/binary_asset.py -- the shared deterministic
binary-payload packer/decoder used by scripts/export_knn_explore_data.py and
scripts/export_knn_abc_data.py (WP15 §3).

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_binary_asset.py'
"""

from __future__ import annotations

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import binary_asset as ba  # noqa: E402


class BinaryAssetBuilder(unittest.TestCase):
    def test_round_trip_float32_and_uint16(self):
        b = ba.BinaryAssetBuilder()
        floats = np.array([1.5, -2.25, 3.0, 0.0], dtype="float64")
        ints = np.array([[0, 1, 2], [65535, 3, 4]], dtype="int64")
        b.add("f", "float32", floats)
        b.add("i", "uint16", ints)
        blob = b.build()

        decoded_f = ba.decode_section(blob, b.sections["f"])
        decoded_i = ba.decode_section(blob, b.sections["i"])
        np.testing.assert_allclose(decoded_f, floats.astype("float32"))
        np.testing.assert_array_equal(decoded_i, ints.astype("uint16"))

    def test_sections_are_4_byte_aligned(self):
        b = ba.BinaryAssetBuilder()
        # an odd-length uint16 section (2 elements = 4 bytes, fine) followed
        # by one with an odd element count (3 elements = 6 bytes, needs padding)
        b.add("a", "uint16", np.array([1, 2, 3], dtype="uint16"))  # 6 bytes -> pads to 8
        b.add("b", "float32", np.array([1.0], dtype="float32"))
        self.assertEqual(b.sections["a"]["byteOffset"] % 4, 0)
        self.assertEqual(b.sections["b"]["byteOffset"] % 4, 0)
        blob = b.build()
        self.assertEqual(len(blob) % 4, 0)
        # decoding still recovers the exact (unpadded) logical values
        np.testing.assert_array_equal(ba.decode_section(blob, b.sections["a"]), [1, 2, 3])

    def test_uint16_overflow_is_rejected(self):
        b = ba.BinaryAssetBuilder()
        with self.assertRaises(ValueError):
            b.add("bad", "uint16", np.array([0, 65536], dtype="int64"))

    def test_negative_uint16_is_rejected(self):
        b = ba.BinaryAssetBuilder()
        with self.assertRaises(ValueError):
            b.add("bad", "uint16", np.array([-1, 5], dtype="int64"))

    def test_duplicate_section_name_is_rejected(self):
        b = ba.BinaryAssetBuilder()
        b.add("x", "float32", np.array([1.0]))
        with self.assertRaises(ValueError):
            b.add("x", "float32", np.array([2.0]))

    def test_unsupported_dtype_is_rejected(self):
        b = ba.BinaryAssetBuilder()
        with self.assertRaises(ValueError):
            b.add("x", "float64", np.array([1.0]))

    def test_little_endian_regardless_of_host(self):
        b = ba.BinaryAssetBuilder()
        b.add("v", "uint16", np.array([1], dtype="uint16"))
        blob = b.build()
        # 1 as little-endian uint16 is bytes [0x01, 0x00]
        self.assertEqual(blob[:2], b"\x01\x00")

    def test_shapes_are_preserved_for_2d_arrays(self):
        b = ba.BinaryAssetBuilder()
        mat = np.arange(12, dtype="float64").reshape(3, 4)
        b.add("m", "float32", mat)
        blob = b.build()
        decoded = ba.decode_section(blob, b.sections["m"])
        self.assertEqual(decoded.shape, (3, 4))
        np.testing.assert_allclose(decoded, mat.astype("float32"))

    def test_deterministic_across_repeated_builds(self):
        def make():
            b = ba.BinaryAssetBuilder()
            b.add("a", "float32", np.array([1.0, 2.0, 3.0]))
            b.add("b", "uint16", np.array([1, 2, 3]))
            return b.build(), b.sections

        blob1, sections1 = make()
        blob2, sections2 = make()
        self.assertEqual(blob1, blob2)
        self.assertEqual(sections1, sections2)
        self.assertEqual(ba.sha256_hex(blob1), ba.sha256_hex(blob2))


if __name__ == "__main__":
    unittest.main()
