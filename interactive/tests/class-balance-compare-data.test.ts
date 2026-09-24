import { describe, expect, it } from "vitest";
import { findEntry, parseClassBalanceCompareData } from "../src/class-balance-compare-data";

function modelResult(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    confusionMatrix: { tn: 33, fp: 17, fn: 24, tp: 26 },
    accuracy: 0.59,
    majorityBaselineAccuracy: 0.5,
    balancedAccuracy: 0.59,
    recall: 0.52,
    precision: 0.604651,
    f1: 0.55914,
    rocAuc: 0.6176,
    prAuc: 0.602568,
    prAucBaseline: 0.5,
    ...overrides,
  };
}

function entry(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    ratioKey: "50:50",
    cohort: { n: 400, nMajority: 200, nMinority: 200 },
    nTrainMajority: 150,
    nTrainMinority: 150,
    nTestMajority: 50,
    nTestMinority: 50,
    models: { ordinary: modelResult(), classWeighted: modelResult() },
    ...overrides,
  };
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "class-balance-compare",
    source: { pinnedCommit: "abc123", brainTableSha256: "def456" },
    majorityClass: "control",
    minorityClass: "autism",
    cohortSize: 400,
    splitSeed: 0,
    modelC: 1.0,
    ratios: [
      { key: "50:50", majorityPct: 0.5, minorityPct: 0.5 },
      { key: "60:40", majorityPct: 0.6, minorityPct: 0.4 },
      { key: "70:30", majorityPct: 0.7, minorityPct: 0.3 },
      { key: "80:20", majorityPct: 0.8, minorityPct: 0.2 },
      { key: "90:10", majorityPct: 0.9, minorityPct: 0.1 },
    ],
    modelOrdinary: "Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))",
    modelClassWeighted:
      "Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight='balanced'))",
    entries: [
      entry({ ratioKey: "50:50" }),
      entry({
        ratioKey: "60:40",
        cohort: { n: 400, nMajority: 240, nMinority: 160 },
        nTrainMajority: 180,
        nTrainMinority: 120,
        nTestMajority: 60,
        nTestMinority: 40,
        models: {
          ordinary: modelResult({
            confusionMatrix: { tn: 42, fp: 18, fn: 18, tp: 22 },
            majorityBaselineAccuracy: 0.6,
            prAucBaseline: 0.4,
          }),
          classWeighted: modelResult({
            confusionMatrix: { tn: 42, fp: 18, fn: 18, tp: 22 },
            majorityBaselineAccuracy: 0.6,
            prAucBaseline: 0.4,
          }),
        },
      }),
      entry({
        ratioKey: "70:30",
        cohort: { n: 400, nMajority: 280, nMinority: 120 },
        nTrainMajority: 210,
        nTrainMinority: 90,
        nTestMajority: 70,
        nTestMinority: 30,
        models: {
          ordinary: modelResult({
            confusionMatrix: { tn: 47, fp: 23, fn: 19, tp: 11 },
            majorityBaselineAccuracy: 0.7,
            prAucBaseline: 0.3,
          }),
          classWeighted: modelResult({
            confusionMatrix: { tn: 47, fp: 23, fn: 18, tp: 12 },
            majorityBaselineAccuracy: 0.7,
            prAucBaseline: 0.3,
          }),
        },
      }),
      entry({
        ratioKey: "80:20",
        cohort: { n: 400, nMajority: 320, nMinority: 80 },
        nTrainMajority: 240,
        nTrainMinority: 60,
        nTestMajority: 80,
        nTestMinority: 20,
        models: {
          ordinary: modelResult({
            confusionMatrix: { tn: 74, fp: 6, fn: 19, tp: 1 },
            majorityBaselineAccuracy: 0.8,
            prAucBaseline: 0.2,
            precision: 0.142857,
            f1: 0.074074,
            recall: 0.05,
          }),
          classWeighted: modelResult({
            confusionMatrix: { tn: 71, fp: 9, fn: 17, tp: 3 },
            majorityBaselineAccuracy: 0.8,
            prAucBaseline: 0.2,
            precision: 0.25,
            f1: 0.1875,
            recall: 0.15,
          }),
        },
      }),
      entry({
        ratioKey: "90:10",
        cohort: { n: 400, nMajority: 360, nMinority: 40 },
        nTrainMajority: 270,
        nTrainMinority: 30,
        nTestMajority: 90,
        nTestMinority: 10,
        models: {
          ordinary: modelResult({
            confusionMatrix: { tn: 84, fp: 6, fn: 9, tp: 1 },
            accuracy: 0.85,
            majorityBaselineAccuracy: 0.9,
            prAucBaseline: 0.1,
            precision: 0.142857,
            f1: 0.117647,
            recall: 0.1,
          }),
          classWeighted: modelResult({
            confusionMatrix: { tn: 80, fp: 10, fn: 9, tp: 1 },
            accuracy: 0.81,
            majorityBaselineAccuracy: 0.9,
            prAucBaseline: 0.1,
            precision: 0.090909,
            f1: 0.095238,
            recall: 0.1,
          }),
        },
      }),
    ],
  };
}

describe("parseClassBalanceCompareData", () => {
  it("accepts a well-formed payload with exactly five ratios", () => {
    const result = parseClassBalanceCompareData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("findEntry returns both models for a ratio", () => {
    const result = parseClassBalanceCompareData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const found = findEntry(result.data, "90:10");
      expect(found.models.ordinary.recall).toBe(0.1);
      expect(found.models.classWeighted.recall).toBe(0.1);
      expect(found.models.ordinary.accuracy).not.toBe(found.models.classWeighted.accuracy);
    }
  });

  it("accepts a null precision/f1/balancedAccuracy (undefined when tp+fp==0)", () => {
    const bad = validPayload();
    (bad.entries[4]!.models.ordinary as Record<string, unknown>).precision = null;
    (bad.entries[4]!.models.ordinary as Record<string, unknown>).f1 = null;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok, result.ok ? "" : result.error).toBe(true);
  });

  it("rejects a payload with a sixth ratio (95:5 must be absent)", () => {
    const bad = validPayload();
    bad.ratios.push({ key: "95:5", majorityPct: 0.95, minorityPct: 0.05 });
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a payload missing one of the five ratio keys", () => {
    const bad = validPayload();
    bad.entries = bad.entries.slice(0, 4);
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a confusion matrix whose total disagrees with nTestMajority+nTestMinority", () => {
    const bad = validPayload();
    bad.entries[0]!.models.ordinary.confusionMatrix.tp = 999;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects cohort counts that do not sum to n", () => {
    const bad = validPayload();
    bad.entries[0]!.cohort.nMajority = 999;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects train+test counts that disagree with the cohort composition", () => {
    const bad = validPayload();
    bad.entries[0]!.nTrainMajority = 999;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects majorityBaselineAccuracy differing between the two models at one ratio", () => {
    const bad = validPayload();
    bad.entries[0]!.models.classWeighted.majorityBaselineAccuracy = 0.42;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects an out-of-range rocAuc", () => {
    const bad = validPayload();
    bad.entries[0]!.models.ordinary.rocAuc = 1.5;
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects the old schemaVersion / activity name", () => {
    const bad = { ...validPayload(), activity: "imbalance-threshold" };
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a payload carrying a predictedProbaPositive-shaped field (no raw probabilities in this schema)", () => {
    const bad = validPayload() as Record<string, unknown>;
    (bad.entries as Array<Record<string, unknown>>)[0]!.predictedProbaPositive = [0.1, 0.2];
    // Extra unknown fields are allowed (passthrough at the top/entry level in
    // spirit of the sibling loader), but the strict entry schema itself must
    // reject this shape.
    const result = parseClassBalanceCompareData(bad);
    expect(result.ok).toBe(false);
  });

  it("findEntry throws for an unknown ratio key", () => {
    const result = parseClassBalanceCompareData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(() => findEntry(result.data, "95:5")).toThrow();
    }
  });
});
