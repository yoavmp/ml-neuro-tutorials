import { describe, expect, it } from "vitest";
import {
  predictForK,
  cumulativeMeans,
  predictAllForK,
  varianceProxy,
  calibrationSlope,
  ensembleMeanForK,
} from "../src/knn-explore";

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

describe("varianceProxy", () => {
  it("is zero when every sample predicts identically", () => {
    const a = [10, 20, 30];
    expect(varianceProxy([a, a, a])).toBeCloseTo(0, 12);
  });

  it("is the mean per-point SD across samples", () => {
    // point 0: values 0, 0, 0 -> SD 0; point 1: values 0, 3, 6 -> mean 3, SD = sqrt(6)
    const samples = [
      [0, 0],
      [0, 3],
      [0, 6],
    ];
    const expectedSdPoint1 = Math.sqrt(((0 - 3) ** 2 + (3 - 3) ** 2 + (6 - 3) ** 2) / 3);
    expect(varianceProxy(samples)).toBeCloseTo((0 + expectedSdPoint1) / 2, 10);
  });

  it("throws with fewer than two samples", () => {
    expect(() => varianceProxy([[1, 2, 3]])).toThrow();
  });
});

describe("calibrationSlope", () => {
  it("is 1 when predictions equal observed exactly (up to a shift)", () => {
    const observed = [1, 2, 3, 4, 5];
    const predicted = observed.map((v) => v + 2); // pure shift, slope still 1
    expect(calibrationSlope(observed, predicted)).toBeCloseTo(1, 10);
  });

  it("is 0 when predictions are a constant (fully flattened)", () => {
    const observed = [1, 2, 3, 4, 5];
    const predicted = observed.map(() => 3);
    expect(calibrationSlope(observed, predicted)).toBeCloseTo(0, 10);
  });

  it("throws on mismatched or empty lengths", () => {
    expect(() => calibrationSlope([1, 2], [1])).toThrow();
    expect(() => calibrationSlope([], [])).toThrow();
  });
});

describe("ensembleMeanForK", () => {
  it("averages predictions across samples at a fixed k", () => {
    const samples = [
      [[10, 20]], // one query point
      [[30, 40]],
      [[50, 60]],
    ];
    // k=1: predictions are 10, 30, 50 -> mean 30
    expect(ensembleMeanForK(samples, 1)).toEqual([30]);
    // k=2: predictions are 15, 35, 55 -> mean 35
    expect(ensembleMeanForK(samples, 2)).toEqual([35]);
  });
});
