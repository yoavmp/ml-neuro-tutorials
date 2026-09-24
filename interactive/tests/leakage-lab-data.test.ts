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
    model: "Pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=15))",
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
        // KNN (unlike OLS) is scale-sensitive, so every scenario -- scaling
        // included -- may show a nonzero correct/leaky gap; this fixture
        // gives every scenario a small nonzero gap so no test here assumes
        // scaling is special-cased to an identical pair.
        entries.push({
          scenario,
          sampleSize,
          seed,
          nTrain: Math.round(sampleSize * 0.75),
          nTest: Math.round(sampleSize * 0.25),
          correct: { mse: 50, r2: 0.3 },
          leaky: { mse: 45, r2: 0.35 },
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

  it("does not force the scaling scenario's correct/leaky pair to be identical", () => {
    // Historical note: under ordinary least squares, scaling correct/leaky
    // pairs were mathematically identical (OLS is scale-invariant). The
    // estimator is now KNeighborsRegressor(n_neighbors=15) (WP38R sec 4),
    // which IS scale-sensitive, so the parser/schema must not assume or
    // require equality here -- a nonzero gap is a valid, expected value.
    const result = parseLeakageLabData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      const entry = findLeakageLabEntry(result.data, "scaling", 60, 0);
      expect(entry.correct.mse).not.toBe(entry.leaky.mse);
      expect(entry.correct.r2).not.toBe(entry.leaky.r2);
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

  it("shipped scaling entries are not trivially forced identical (KNN is scale-sensitive)", async () => {
    // Smoke check against the real, recomputed KNeighborsRegressor(n_neighbors=15)
    // artifact (WP38R sec 4): with the old LinearRegression estimator, every
    // scaling entry's correct/leaky pair was mathematically identical. KNN's
    // distance-based predictions depend on feature scale, so this equality
    // no longer holds by construction; assert it stays that way rather than
    // silently regressing to a stale OLS-shaped fixture.
    const fs = await import("node:fs/promises");
    const url = new URL("../../book/_static/widgets/data/abide_leakage_lab.json", import.meta.url);
    const text = await fs.readFile(url, "utf-8");
    const r = parseLeakageLabData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      const scalingEntries = r.data.entries.filter((e) => e.scenario === "scaling");
      expect(scalingEntries.length).toBeGreaterThan(0);
      const identicalCount = scalingEntries.filter(
        (e) => e.correct.mse === e.leaky.mse && e.correct.r2 === e.leaky.r2,
      ).length;
      expect(identicalCount).toBe(0);
      for (const e of r.data.entries) {
        expect(Number.isFinite(e.correct.mse)).toBe(true);
        expect(Number.isFinite(e.leaky.mse)).toBe(true);
        expect(Number.isFinite(e.correct.r2)).toBe(true);
        expect(Number.isFinite(e.leaky.r2)).toBe(true);
        expect(e.correct.mse).toBeGreaterThanOrEqual(0);
        expect(e.leaky.mse).toBeGreaterThanOrEqual(0);
      }
    }
  });
});
