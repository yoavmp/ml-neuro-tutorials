"""Reusable strict recursive semantic comparison for JSON-like data (WP31R).

Byte-for-byte JSON comparison is not portable: numpy/libm produce
scientifically-equivalent floating-point results that can differ in their
final decimal digit across platforms (observed: macOS vs. Linux CI on the
Exercise 6 greedy-tree artifact, WP31 run 35437984824). This comparator
stays strict everywhere except floating-point leaves, which may differ only
within a small absolute tolerance:

* dictionary keys must match exactly (no missing/extra keys);
* list lengths and ordering must match exactly;
* strings, Booleans, ``None``, and integers must match exactly;
* float leaves may differ by at most ``abs_tol``, compared with
  ``rel_tol=0`` so large values do not get a proportionally larger
  allowance;
* NaN and infinity are never accepted, even if both sides agree.

Used by ``tests/test_export_tree_greedy_widget_data.py`` and by
``scripts/export_tree_greedy_widget.py``'s ``--check`` path.
"""

from __future__ import annotations

import math
from typing import Any

# Chosen from the observed CI discrepancy (exactly 1e-6 on two adjacent
# `reduction` leaves): about double the observed magnitude, well under the
# 5e-6 ceiling, so a genuine cross-platform float-noise difference passes
# while anything larger than trivial last-digit noise still fails.
DEFAULT_ABS_TOL = 2e-6


class SemanticMismatch(Exception):
    """A single failing JSON path, with both values, from `semantic_diff`."""

    def __init__(self, path: str, a: Any, b: Any, reason: str):
        self.path = path
        self.a = a
        self.b = b
        self.reason = reason
        super().__init__(f"at {path}: {reason}: {a!r} != {b!r}")


def semantic_diff(a: Any, b: Any, *, abs_tol: float = DEFAULT_ABS_TOL, path: str = "$") -> SemanticMismatch | None:
    """Return the first semantic mismatch between `a` and `b`, or None."""
    if isinstance(a, dict) and isinstance(b, dict):
        keys_a, keys_b = set(a), set(b)
        if keys_a != keys_b:
            missing = sorted(keys_a - keys_b)
            extra = sorted(keys_b - keys_a)
            return SemanticMismatch(path, sorted(keys_a), sorted(keys_b), f"key mismatch (missing={missing}, extra={extra})")
        for key in sorted(keys_a):
            mismatch = semantic_diff(a[key], b[key], abs_tol=abs_tol, path=f"{path}.{key}")
            if mismatch is not None:
                return mismatch
        return None

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return SemanticMismatch(path, len(a), len(b), "list length mismatch")
        for i, (av, bv) in enumerate(zip(a, b)):
            mismatch = semantic_diff(av, bv, abs_tol=abs_tol, path=f"{path}[{i}]")
            if mismatch is not None:
                return mismatch
        return None

    if isinstance(a, bool) or isinstance(b, bool):
        if type(a) is not type(b) or a != b:
            return SemanticMismatch(path, a, b, "boolean mismatch")
        return None

    if isinstance(a, float) or isinstance(b, float):
        fa, fb = float(a), float(b)
        if not math.isfinite(fa) or not math.isfinite(fb):
            return SemanticMismatch(path, a, b, "non-finite numeric value is never accepted")
        if not math.isclose(fa, fb, rel_tol=0.0, abs_tol=abs_tol):
            return SemanticMismatch(path, a, b, f"float difference {abs(fa - fb):.3g} exceeds tolerance {abs_tol:.3g}")
        return None

    if isinstance(a, int) and isinstance(b, int):
        if a != b:
            return SemanticMismatch(path, a, b, "integer mismatch")
        return None

    if a != b:
        return SemanticMismatch(path, a, b, "value mismatch")
    return None


def assert_semantically_equal(a: Any, b: Any, *, abs_tol: float = DEFAULT_ABS_TOL) -> None:
    """Raise AssertionError (with the failing path and both values) unless
    `a` and `b` are semantically equal under `semantic_diff`."""
    mismatch = semantic_diff(a, b, abs_tol=abs_tol)
    if mismatch is not None:
        raise AssertionError(str(mismatch))
