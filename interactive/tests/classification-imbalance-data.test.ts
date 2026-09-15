import { describe, expect, it } from "vitest";
import { findEntry, parseClassificationImbalanceData } from "../src/classification-imbalance-data";

function side(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    nTrainMajority: 15,
    nTrainMinority: 15,
    nTestMajority: 5,
    nTestMinority: 5,
    confusionMatrix: { tn: 3, fp: 2, fn: 1, tp: 4 },
    accuracy: 0.7,
    auc: 0.65,
    majorityBaselineAccuracy: 0.5,
    ...overrides,
  };
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "classification-imbalance",
    source: { pinnedCommit: "abc123", brainTableSha256: "def456" },
    majorityClass: "control",
    minorityClass: "autism",
    cohortSize: 40,
    ratios: [
      { key: "50:50", majorityPct: 0.5, minorityPct: 0.5 },
      { key: "95:5", majorityPct: 0.95, minorityPct: 0.05 },
    ],
    splitSeeds: [0, 1],
    model: "Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))",
    entries: [
      { ratioKey: "50:50", seed: 0, cohort: { n: 40, nMajority: 20, nMinority: 20 }, stratified: side(), unstratified: side() },
      { ratioKey: "50:50", seed: 1, cohort: { n: 40, nMajority: 20, nMinority: 20 }, stratified: side(), unstratified: side() },
      { ratioKey: "95:5", seed: 0, cohort: { n: 40, nMajority: 38, nMinority: 2 }, stratified: side(), unstratified: side({ auc: null, nTestMinority: 0 }) },
      { ratioKey: "95:5", seed: 1, cohort: { n: 40, nMajority: 38, nMinority: 2 }, stratified: side(), unstratified: side() },
    ],
  };
}

describe("parseClassificationImbalanceData", () => {
  it("accepts a well-formed payload with full (ratio, seed) coverage", () => {
    const result = parseClassificationImbalanceData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("accepts a null auc (undefined case)", () => {
    const result = parseClassificationImbalanceData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const entry = findEntry(result.data, "95:5", 0);
      expect(entry.unstratified.auc).toBeNull();
    }
  });

  it("rejects missing (ratio, seed) coverage", () => {
    const bad = validPayload();
    bad.entries = bad.entries.slice(0, 3);
    const result = parseClassificationImbalanceData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a duplicate (ratio, seed) entry masking a missing one", () => {
    const bad = validPayload();
    bad.entries[3] = { ...bad.entries[0]! };
    const result = parseClassificationImbalanceData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects an out-of-range auc", () => {
    const bad = validPayload();
    (bad.entries[0] as { stratified: { auc: number } }).stratified.auc = 1.4;
    const result = parseClassificationImbalanceData(bad);
    expect(result.ok).toBe(false);
  });

  it("findEntry throws for an unknown (ratio, seed) pair", () => {
    const result = parseClassificationImbalanceData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(() => findEntry(result.data, "60:40", 0)).toThrow();
    }
  });
});
