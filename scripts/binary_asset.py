#!/usr/bin/env python3
"""Shared deterministic binary-payload packer/decoder for browser interactive
assets (WP15 §3).

Replaces large numeric-array JSON payloads with a small versioned JSON
manifest plus one deterministic binary file, read in the browser with
``fetch(...).arrayBuffer()`` and typed arrays (``interactive/src/binary-asset.ts``
is the matching TypeScript decoder -- keep both in sync: dtypes, alignment,
and endianness must match exactly).

Format:

* every section is a flat, C-contiguous array of one dtype (``float32`` or
  ``uint16``), always written little-endian regardless of the host machine;
* sections are concatenated back-to-back, each padded with zero bytes so the
  NEXT section starts at a 4-byte-aligned offset (so a ``Float32Array`` view
  can be constructed directly on the underlying ``ArrayBuffer`` without a
  copy, on every browser);
* the JSON manifest records, per section: ``dtype``, ``shape``, ``byteOffset``,
  ``byteLength`` -- everything the browser loader needs to slice + validate
  the buffer, plus the whole binary file's own ``byteLength`` and SHA-256
  digest for integrity verification.

``uint16`` is used for nearest-neighbour row indices; every caller must prove
(assert) the maximum index is below 65,536 before adding such a section --
:meth:`BinaryAssetBuilder.add` raises if it is not.
"""

from __future__ import annotations

import hashlib
from typing import Any

ALIGNMENT = 4
NUMPY_DTYPE = {"float32": "<f4", "uint16": "<u2"}
ELEMENT_SIZE = {"float32": 4, "uint16": 2}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BinaryAssetBuilder:
    """Accumulates named sections into one deterministic, 4-byte-aligned,
    little-endian binary blob, and the matching manifest ``sections`` dict."""

    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._offset = 0
        self.sections: dict[str, dict[str, Any]] = {}

    def add(self, name: str, dtype: str, array: Any) -> None:
        import numpy as np

        if name in self.sections:
            raise ValueError(f"duplicate section name {name!r}")
        if dtype not in NUMPY_DTYPE:
            raise ValueError(f"section {name!r}: unsupported dtype {dtype!r}; known: {sorted(NUMPY_DTYPE)}")
        arr = np.asarray(array)
        if dtype == "uint16":
            if arr.size and (int(arr.min()) < 0 or int(arr.max()) > 65535):
                raise ValueError(
                    f"section {name!r}: value(s) outside the uint16 range [0, 65535] "
                    f"(min={arr.min() if arr.size else None}, max={arr.max() if arr.size else None}); "
                    "this data no longer fits the 16-bit index format and needs a wider dtype."
                )
        cast = arr.astype(NUMPY_DTYPE[dtype])
        raw = cast.tobytes(order="C")
        pad = (-len(raw)) % ALIGNMENT
        byte_offset = self._offset
        self._chunks.append(raw + b"\x00" * pad)
        self._offset += len(raw) + pad
        self.sections[name] = {
            "dtype": dtype,
            "shape": list(cast.shape),
            "byteOffset": byte_offset,
            "byteLength": len(raw),
        }

    def build(self) -> bytes:
        return b"".join(self._chunks)


def decode_section(blob: bytes, section: dict[str, Any]) -> Any:
    """Reconstruct one section's numpy array from a built blob + its manifest
    entry -- the Python-side mirror of the TypeScript loader, used to
    validate a built/committed artifact by reconstructing the SAME logical
    arrays the old JSON format stored directly."""
    import numpy as np

    dtype = NUMPY_DTYPE[section["dtype"]]
    offset = section["byteOffset"]
    length = section["byteLength"]
    itemsize = ELEMENT_SIZE[section["dtype"]]
    if length % itemsize != 0:
        raise ValueError(f"section byteLength {length} is not a multiple of its dtype's element size {itemsize}")
    count = length // itemsize
    arr = np.frombuffer(blob, dtype=dtype, count=count, offset=offset)
    return arr.reshape(tuple(section["shape"]))
