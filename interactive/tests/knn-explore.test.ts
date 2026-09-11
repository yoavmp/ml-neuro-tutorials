import { describe, expect, it } from "vitest";
import { predictForK, cumulativeMeans, predictAllForK } from "../src/knn-explore";

describe("predictForK", () => {
  it("averages the first k nearest-first entries", () => {
    expect(predictForK([10, 20, 30, 40], 1)).toBe(10);
    expect(predictForK([10, 20, 30, 40], 2)).toBe(15);
    expect(predictForK([10, 20, 30, 40], 4)).toBe(25);
  });

  it("throws for k outside [1, length]", () => {
    expect(() => predictForK([1, 2, 3], 0)).toThrow();
    expect(() => predictForK([1, 2, 3], 4)).toThrow();
  });
});

describe("cumulativeMeans", () => {
  it("matches predictForK at every k", () => {
    const sorted = [10, 20, 30, 40, 5];
    const means = cumulativeMeans(sorted);
    expect(means).toHaveLength(sorted.length);
    for (let k = 1; k <= sorted.length; k += 1) {
      expect(means[k - 1]).toBeCloseTo(predictForK(sorted, k), 12);
    }
  });

  it("the last entry is the mean of every value (k = n_fit)", () => {
    const sorted = [1, 2, 3, 4, 5, 6];
    const means = cumulativeMeans(sorted);
    expect(means[means.length - 1]).toBeCloseTo(3.5, 12);
  });
});

describe("predictAllForK", () => {
  it("predicts one value per query row", () => {
    const rows = [
      [10, 20, 30],
      [100, 200, 300],
    ];
    expect(predictAllForK(rows, 1)).toEqual([10, 100]);
    expect(predictAllForK(rows, 2)).toEqual([15, 150]);
    expect(predictAllForK(rows, 3)).toEqual([20, 200]);
  });
});
