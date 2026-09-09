import { describe, expect, it } from "vitest";
import { computeHistogram } from "../src/histogram";

const sum = (xs: number[]): number => xs.reduce((a, b) => a + b, 0);

describe("computeHistogram — ordinary data", () => {
  it("returns exactly the requested number of equal-width bins", () => {
    const r = computeHistogram([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5);
    expect(r.kind).toBe("normal");
    expect(r.counts).toHaveLength(5);
    expect(r.binEdges).toHaveLength(6);
    expect(r.binEdges[0]).toBe(0);
    expect(r.binEdges[5]).toBe(10);
    // equal width of 2
    for (let i = 0; i < 5; i += 1) {
      expect(r.binEdges[i + 1]! - r.binEdges[i]!).toBeCloseTo(2, 10);
    }
  });

  it("includes the maximum in the final bin, not a new one", () => {
    const r = computeHistogram([0, 2, 4, 6, 8, 10], 5);
    expect(r.counts).toHaveLength(5);
    expect(sum(r.counts)).toBe(6);
    // the value 10 lands in the last bin
    expect(r.counts[4]).toBeGreaterThanOrEqual(1);
  });

  it("conserves counts (sum === availableN) across bin choices", () => {
    const data = [1, 1, 2, 3, 3, 3, 4, 5, 8, 13, 21];
    for (const bins of [1, 2, 3, 7, 10, 50]) {
      const r = computeHistogram(data, bins);
      expect(sum(r.counts)).toBe(r.availableN);
      expect(r.availableN).toBe(data.length);
    }
  });

  it("reports min, max, availableN and missingN", () => {
    const r = computeHistogram([5, 10, 15, 20], 4);
    expect(r.min).toBe(5);
    expect(r.max).toBe(20);
    expect(r.availableN).toBe(4);
    expect(r.missingN).toBe(0);
  });

  it("produces centers and labels aligned to the bins", () => {
    const r = computeHistogram([0, 10], 2);
    expect(r.binCenters).toEqual([2.5, 7.5]);
    expect(r.binLabels[0]).toBe("[0, 5)");
    expect(r.binLabels[1]).toBe("[5, 10]"); // last bin closed
  });
});

describe("computeHistogram — boundaries, negatives, decimals", () => {
  it("puts interior boundary values in the higher bin", () => {
    // width 1 over [0,4]; value 2 -> floor(2/1) = index 2
    const r = computeHistogram([0, 2, 4], 4);
    expect(r.counts).toEqual([1, 0, 1, 1]);
  });

  it("handles negative and decimal values", () => {
    const r = computeHistogram([-2.5, -1, 0, 0.5, 1.75], 3);
    expect(r.kind).toBe("normal");
    expect(r.min).toBe(-2.5);
    expect(r.max).toBe(1.75);
    expect(sum(r.counts)).toBe(5);
  });
});

describe("computeHistogram — missingness", () => {
  it("counts nulls as missing and excludes them from bins", () => {
    const r = computeHistogram([1, null, 2, null, null, 3], 3);
    expect(r.availableN).toBe(3);
    expect(r.missingN).toBe(3);
    expect(sum(r.counts)).toBe(3);
  });
});

describe("computeHistogram — requested-bin validation", () => {
  it("rejects non-positive, non-integer and non-finite bin counts", () => {
    expect(() => computeHistogram([1, 2, 3], 0)).toThrow(RangeError);
    expect(() => computeHistogram([1, 2, 3], -4)).toThrow(RangeError);
    expect(() => computeHistogram([1, 2, 3], 2.5)).toThrow(RangeError);
    expect(() => computeHistogram([1, 2, 3], Number.NaN)).toThrow(RangeError);
    expect(() => computeHistogram([1, 2, 3], Number.POSITIVE_INFINITY)).toThrow(RangeError);
  });

  it("rejects a non-finite numeric observation that slips through", () => {
    expect(() => computeHistogram([1, 2, Number.NaN], 3)).toThrow(TypeError);
    expect(() => computeHistogram([1, 2, Number.POSITIVE_INFINITY], 3)).toThrow(TypeError);
  });
});

describe("computeHistogram — all-missing / empty", () => {
  it("returns a deterministic empty result with no bins", () => {
    const r = computeHistogram([null, null, null], 10);
    expect(r.kind).toBe("empty");
    expect(r.counts).toEqual([]);
    expect(r.binEdges).toEqual([]);
    expect(r.binCenters).toEqual([]);
    expect(r.availableN).toBe(0);
    expect(r.missingN).toBe(3);
    expect(r.min).toBeNull();
    expect(r.max).toBeNull();
  });

  it("treats a zero-length input as empty", () => {
    const r = computeHistogram([], 4);
    expect(r.kind).toBe("empty");
    expect(r.availableN).toBe(0);
    expect(r.missingN).toBe(0);
  });
});

describe("computeHistogram — constant variable", () => {
  it("renders one unit-wide bin with every observation and no divide-by-zero", () => {
    const r = computeHistogram([7, 7, 7, 7], 25);
    expect(r.kind).toBe("constant");
    expect(r.counts).toEqual([4]);
    expect(r.binEdges).toEqual([6.5, 7.5]);
    expect(r.binCenters).toEqual([7]);
    expect(r.binLabels).toEqual(["[7]"]);
    expect(r.min).toBe(7);
    expect(r.max).toBe(7);
    expect(sum(r.counts)).toBe(r.availableN);
  });

  it("counts missing values alongside a constant present value", () => {
    const r = computeHistogram([3, null, 3, null], 10);
    expect(r.kind).toBe("constant");
    expect(r.availableN).toBe(2);
    expect(r.missingN).toBe(2);
    expect(r.counts).toEqual([2]);
  });
});
