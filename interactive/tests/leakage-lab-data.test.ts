import { describe, expect, it } from "vitest";
import {
  entriesForScenarioSize,
  findLeakageLabEntry,
  parseLeakageLabData,
} from "../src/leakage-lab-data";

const SAMPLE_SIZES = [60, 100];
const SEEDS = [0, 1];
const SCENARIOS = ["scaling", "feature_selection", "pca"] as const;

function scenarioMeta(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    bundle: "sensorimotor_core",
    featureCount: 10,
    measures: ["CT"],
    model: "Pipeline(StandardScaler(), LinearRegression())",
    correctWorkflow: "split first; fit on training rows only.",
    leakyWorkflow: "fit on all sampled rows, then split.",
    ...overrides,
  };
}

function makeEntries() {
  const entries: Record<string, unknown>[] = [];
  for (const scenario of SCENARIOS) {
    for (const sampleSize of SAMPLE_SIZES) {
      for (const seed of SEEDS) {
        const same = scenario === "scaling";
        entries.push({
          scenario,
          sampleSize,
          seed,
          nTrain: Math.round(sampleSize * 0.75),
          nTest: Math.round(sampleSize * 0.25),
          correct: { mse: 50, r2: 0.3 },
          leaky: { mse: same ? 50 : 45, r2: same ? 0.3 : 0.35 },
        });
      }
    }
  }
  return entries;
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "leakage-lab",
    target: "age",
    source: { pinnedCommit: "abc123", brainTableSha256: "d".repeat(64) },
    sampleSizes: SAMPLE_SIZES,
    seeds: SEEDS,
    scenarios: {
      scaling: scenarioMeta(),
      feature_selection: scenarioMeta({ selectedFeatureCount: 20 }),
      pca: scenarioMeta({ componentCount: 10 }),
    },
    entries: makeEntries(),
  };
}

describe("parseLeakageLabData", () => {
  it("accepts a well-formed payload with full scenario x size x seed coverage", () => {
    const result = parseLeakageLabData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("preserves a zero (identical) correct/leaky gap for the scaling scenario", () => {
    const result = parseLeakageLabData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const entry = findLeakageLabEntry(result.data, "scaling", 60, 0);
      expect(entry.correct.mse).toBe(entry.leaky.mse);
      expect(entry.correct.r2).toBe(entry.leaky.r2);
    }
  });

  it("rejects missing scenario/size/seed coverage", () => {
    const bad = validPayload();
    bad.entries = bad.entries.slice(0, bad.entries.length - 1);
    expect(parseLeakageLabData(bad).ok).toBe(false);
  });

  it("rejects a duplicate entry masking a missing one", () => {
    const bad = validPayload();
    bad.entries[bad.entries.length - 1] = { ...bad.entries[0]! };
    expect(parseLeakageLabData(bad).ok).toBe(false);
  });

  it("rejects an unknown scenario key", () => {
    const bad = validPayload();
    bad.entries[0] = { ...bad.entries[0]!, scenario: "normalization" };
    expect(parseLeakageLabData(bad).ok).toBe(false);
  });

  it("rejects an r2 that is not finite", () => {
    const bad = validPayload();
    (bad.entries[0] as { correct: { r2: number } }).correct.r2 = Number.NaN;
    expect(parseLeakageLabData(bad).ok).toBe(false);
  });

  it("entriesForScenarioSize returns entries sorted by seed", () => {
    const result = parseLeakageLabData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const entries = entriesForScenarioSize(result.data, "pca", 100);
      expect(entries.map((e) => e.seed)).toEqual([0, 1]);
    }
  });

  it("findLeakageLabEntry throws for an unknown combination", () => {
    const result = parseLeakageLabData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(() => findLeakageLabEntry(result.data, "pca", 9999, 0)).toThrow();
    }
  });

  it("accepts the shipped data/abide_leakage_lab.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL("../../book/_static/widgets/data/abide_leakage_lab.json", import.meta.url);
    const text = await fs.readFile(url, "utf-8");
    const r = parseLeakageLabData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
