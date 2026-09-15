import { describe, expect, it } from "vitest";
import {
  accuracyFromCounts,
  aucTrapezoidal,
  confusionMatrix,
  majorityBaselineAccuracy,
  percentPredictedPositive,
  predictAtThreshold,
  rocCurve,
  rocPointAtThreshold,
  sensitivityFromCounts,
  specificityFromCounts,
} from "../src/classification-metrics";

describe("predictAtThreshold", () => {
  it("predicts positive when score >= threshold", () => {
    expect(predictAtThreshold([0.9, 0.5, 0.49, 0.1], 0.5)).toEqual([1, 1, 0, 0]);
  });

  it("a higher threshold never increases the count of positive predictions", () => {
    const scores = [0.9, 0.2, 0.6, 0.1, 0.55, 0.75];
    const lowCount = predictAtThreshold(scores, 0.2).reduce((a, b) => a + b, 0);
    const highCount = predictAtThreshold(scores, 0.8).reduce((a, b) => a + b, 0);
    expect(highCount).toBeLessThanOrEqual(lowCount);
  });
});

describe("confusionMatrix + derived metrics (hand-worked example)", () => {
  // labels: autism, autism, control, control; predicted at threshold 0.5
  const labels = [1, 1, 0, 0];
  const predicted = [1, 0, 1, 0]; // TP, FN, FP, TN

  it("counts TP/TN/FP/FN correctly", () => {
    expect(confusionMatrix(labels, predicted)).toEqual({ tp: 1, tn: 1, fp: 1, fn: 1 });
  });

  it("accuracy = (TP+TN)/total", () => {
    expect(accuracyFromCounts({ tp: 1, tn: 1, fp: 1, fn: 1 })).toBeCloseTo(0.5, 10);
  });

  it("sensitivity = TP/(TP+FN)", () => {
    expect(sensitivityFromCounts({ tp: 3, tn: 1, fp: 1, fn: 1 })).toBeCloseTo(0.75, 10);
  });

  it("specificity = TN/(TN+FP)", () => {
    expect(specificityFromCounts({ tp: 1, tn: 3, fp: 1, fn: 1 })).toBeCloseTo(0.75, 10);
  });

  it("throws on length mismatch", () => {
    expect(() => confusionMatrix([1, 0], [1])).toThrow();
  });
});

describe("rocCurve + aucTrapezoidal", () => {
  it("returns [] when only one class is present (undefined ROC/AUC)", () => {
    expect(rocCurve([1, 1, 1], [0.9, 0.5, 0.1])).toEqual([]);
    expect(rocCurve([0, 0, 0], [0.9, 0.5, 0.1])).toEqual([]);
  });

  it("a perfect separator scores AUC = 1", () => {
    const labels = [1, 1, 1, 0, 0, 0];
    const scores = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1];
    const auc = aucTrapezoidal(rocCurve(labels, scores));
    expect(auc).toBeCloseTo(1.0, 10);
  });

  it("a perfectly-reversed separator scores AUC = 0", () => {
    const labels = [1, 1, 1, 0, 0, 0];
    const scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9];
    const auc = aucTrapezoidal(rocCurve(labels, scores));
    expect(auc).toBeCloseTo(0.0, 10);
  });

  it("random-looking chance-level scores land near 0.5 on a larger balanced set", () => {
    // deterministic pseudo-random interleave, not actually random -- scores
    // alternate independent of label, so ranking carries no information.
    const labels = Array.from({ length: 40 }, (_, i) => i % 2);
    const scores = Array.from({ length: 40 }, (_, i) => ((i * 37) % 40) / 40);
    const auc = aucTrapezoidal(rocCurve(labels, scores));
    expect(auc).toBeGreaterThan(0.3);
    expect(auc).toBeLessThan(0.7);
  });

  it("AUC does not depend on any particular threshold (stays fixed as scores/labels are fixed)", () => {
    const labels = [1, 0, 1, 0, 1, 0, 1, 0];
    const scores = [0.9, 0.1, 0.8, 0.4, 0.6, 0.2, 0.7, 0.3];
    const points = rocCurve(labels, scores);
    const aucA = aucTrapezoidal(points);
    const aucB = aucTrapezoidal(points);
    expect(aucA).toBe(aucB);
    // Sanity: point-at-threshold changes but AUC (computed once) never does.
    const p1 = rocPointAtThreshold(labels, scores, 0.2);
    const p2 = rocPointAtThreshold(labels, scores, 0.85);
    expect(p1).not.toEqual(p2);
    expect(aucTrapezoidal(points)).toBe(aucA);
  });
});

describe("percentPredictedPositive", () => {
  it("computes the percentage predicted positive at a threshold", () => {
    expect(percentPredictedPositive([0.9, 0.1, 0.6, 0.4], 0.5)).toBeCloseTo(50, 10);
  });
});

describe("majorityBaselineAccuracy", () => {
  it("matches the classic 95:5 example", () => {
    const labels = [...Array(5).fill(1), ...Array(95).fill(0)];
    expect(majorityBaselineAccuracy(labels)).toBeCloseTo(0.95, 10);
  });
});
