import { describe, expect, it } from "vitest";
import { sharedAxisRange, formatAlpha, clampAlphaIndex } from "../src/regularization-explore";

describe("sharedAxisRange", () => {
  it("pads the inclusive min/max by padFrac", () => {
    const [lo, hi] = sharedAxisRange([10, 20, 15], 0.1);
    expect(lo).toBeCloseTo(10 - 1, 5);
    expect(hi).toBeCloseTo(20 + 1, 5);
  });

  it("throws on an empty array", () => {
    expect(() => sharedAxisRange([])).toThrow();
  });
});

describe("formatAlpha", () => {
  it("formats a mid-range value as a trimmed decimal", () => {
    expect(formatAlpha(0.2154)).toBe("0.215");
  });

  it("formats a small value with exponential notation", () => {
    expect(formatAlpha(0.001)).toMatch(/e-?\+?/i);
  });

  it("formats a large value with exponential notation", () => {
    expect(formatAlpha(562341)).toMatch(/e\+?/i);
  });

  it("round-trips an integer-valued alpha without a trailing decimal point", () => {
    expect(formatAlpha(100)).toBe("100");
  });
});

describe("clampAlphaIndex", () => {
  it("clamps within [0, length - 1]", () => {
    expect(clampAlphaIndex(-3, 10)).toBe(0);
    expect(clampAlphaIndex(99, 10)).toBe(9);
    expect(clampAlphaIndex(4.6, 10)).toBe(5);
  });

  it("falls back to 0 for a non-finite index", () => {
    expect(clampAlphaIndex(Number.NaN, 10)).toBe(0);
  });
});
