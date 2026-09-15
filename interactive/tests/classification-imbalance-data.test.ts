import { describe, expect, it } from "vitest";
import { findEntry, parseClassificationImbalanceData } from "../src/classification-imbalance-data";

function entry(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    ratioKey: "50:50",
    seed: 0,
    cohort: { n: 40, nMajority: 20, nMinority: 20 },
    nTrainMajority: 15,
    nTrainMinority: 15,
    nTestMajority: 5,
    nTestMinority: 5,
    confusionMatrix: { tn: 3, fp: 2, fn: 1, tp: 4 },
    accuracy: 0.7,
    majorityBaselineAccuracy: 0.5,
    auc: 0.65,
    balancedAccuracy: 0.68,
    sensitivity: 0.8,
    specificity: 0.6,
    ...overrides,
  };
}

function validPayload() {
  return {
    schemaVersion: 2,
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
    modelC: 1.0,
    model: "Pipeline(StandardScaler(), LogisticRegression(C=0.01, max_iter=5000))",
    entries: [
      entry({ ratioKey: "50:50", seed: 0 }),
      entry({ ratioKey: "50:50", seed: 1 }),
      entry({ ratioKey: "95:5", seed: 0, cohort: { n: 40, nMajority: 38, nMinority: 2 } }),
      entry({ ratioKey: "95:5", seed: 1, cohort: { n: 40, nMajority: 38, nMinority: 2 } }),
    ],
  };
}

describe("parseClassificationImbalanceData", () => {
  it("accepts a well-formed payload with full (ratio, seed) coverage", () => {
    const result = parseClassificationImbalanceData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("accepts an entry with no stratified/unstratified nesting", () => {
    const result = parseClassificationImbalanceData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const found = findEntry(result.data, "95:5", 0);
      expect(found.accuracy).toBe(0.7);
      expect(found).not.toHaveProperty("stratified");
      expect(found).not.toHaveProperty("unstratified");
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
    (bad.entries[0] as { auc: number }).auc = 1.4;
    const result = parseClassificationImbalanceData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a null auc (no undefined-AUC case in this schema)", () => {
    const bad = validPayload();
    (bad.entries[0] as { auc: unknown }).auc = null;
    const result = parseClassificationImbalanceData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects the old schemaVersion 1 payload shape", () => {
    const bad = { ...validPayload(), schemaVersion: 1 };
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
