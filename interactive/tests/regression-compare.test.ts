import { describe, expect, it } from "vitest";
import {
  catalogKey,
  meanSquaredError,
  r2Score,
  scatterPoints,
  sharedAxisRange,
} from "../src/regression-compare";

describe("r2Score", () => {
  it("is 1.0 for perfect predictions", () => {
    expect(r2Score([1, 2, 3, 4], [1, 2, 3, 4])).toBeCloseTo(1, 12);
  });

  it("is 0.0 when the prediction is the mean", () => {
    expect(r2Score([1, 2, 3, 4], [2.5, 2.5, 2.5, 2.5])).toBeCloseTo(0, 12);
  });

  it("is negative when the model is worse than the mean", () => {
    expect(r2Score([1, 2, 3, 4], [4, 3, 2, 1])).toBeLessThan(0);
  });

  it("matches the textbook formula on a worked example", () => {
    // y = [10, 12, 14], yhat = [11, 11, 15]; mean 12; SS_tot = 8; SS_res = 1+1+1 = 3
    expect(r2Score([10, 12, 14], [11, 11, 15])).toBeCloseTo(1 - 3 / 8, 12);
  });

  it("throws on length mismatch and on zero-variance targets", () => {
    expect(() => r2Score([1, 2], [1])).toThrow();
    expect(() => r2Score([5, 5, 5], [1, 2, 3])).toThrow(/zero variance/);
  });
});

describe("meanSquaredError", () => {
  it("computes the mean of squared residuals", () => {
    expect(meanSquaredError([1, 2, 3], [1, 2, 3])).toBe(0);
    expect(meanSquaredError([0, 0, 0], [1, 2, 2])).toBeCloseTo((1 + 4 + 4) / 3, 12);
  });

  it("throws on length mismatch", () => {
    expect(() => meanSquaredError([1, 2, 3], [1, 2])).toThrow();
  });
});

describe("scatterPoints", () => {
  it("zips the three arrays in row order", () => {
    const pts = scatterPoints([1, 2], [1.1, 1.9], [0, 3]);
    expect(pts).toEqual([
      { observed: 1, predicted: 1.1, fold: 0 },
      { observed: 2, predicted: 1.9, fold: 3 },
    ]);
  });

  it("throws when the arrays disagree in length", () => {
    expect(() => scatterPoints([1, 2], [1], [0, 1])).toThrow();
  });
});

describe("sharedAxisRange", () => {
  it("spans the min and max of all values with padding", () => {
    const [lo, hi] = sharedAxisRange([10, 50, 30], 0.1);
    expect(lo).toBeCloseTo(10 - 4, 12);
    expect(hi).toBeCloseTo(50 + 4, 12);
  });

  it("does not collapse when every value is equal", () => {
    const [lo, hi] = sharedAxisRange([7, 7, 7], 0.1);
    expect(hi).toBeGreaterThan(lo);
  });
});

describe("catalogKey", () => {
  it("joins bundle and measures deterministically", () => {
    expect(catalogKey({ bundle: "frontoparietal", measures: ["CT"] })).toBe("frontoparietal__CT");
    expect(catalogKey({ bundle: "occipital", measures: ["CT", "Area"] })).toBe("occipital__CT+Area");
  });
});
