import { describe, expect, it } from "vitest";
import { parseImbalanceThresholdData } from "../src/imbalance-threshold-data";

const N_MAJORITY = 9;
const N_MINORITY = 1;
const N_TEST = N_MAJORITY + N_MINORITY;

function testLabels(): number[] {
  return [...Array(N_MAJORITY).fill(0), ...Array(N_MINORITY).fill(1)];
}

function modelResult(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    model: "Pipeline(StandardScaler(), LogisticRegression(C=1.0))",
    predictedProbaPositive: Array.from({ length: N_TEST }, (_, i) =>
      i === N_TEST - 1 ? 0.8 : 0.1,
    ) as number[],
    rocAuc: 0.63,
    prAuc: 0.14,
    ...overrides,
  };
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "imbalance-threshold",
    source: { pinnedCommit: "abc123", brainTableSha256: "d".repeat(64) },
    cohort: { n: 400, nMajority: 360, nMinority: 40 },
    majorityClass: "control",
    minorityClass: "autism",
    ratioKey: "90:10",
    splitSeed: 0,
    nTestMajority: N_MAJORITY,
    nTestMinority: N_MINORITY,
    positivePrevalence: 0.1,
    majorityBaselineAccuracy: 0.9,
    modelC: 1.0,
    testLabels: testLabels(),
    models: {
      ordinary: modelResult(),
      classWeighted: modelResult({ model: 'Pipeline(StandardScaler(), LogisticRegression(class_weight="balanced"))' }),
    },
  };
}

describe("parseImbalanceThresholdData", () => {
  it("accepts a well-formed payload", () => {
    const result = parseImbalanceThresholdData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("rejects testLabels whose length does not match nTestMajority + nTestMinority", () => {
    const bad = validPayload();
    bad.testLabels = bad.testLabels.slice(0, N_TEST - 1);
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("rejects predictedProbaPositive whose length does not match the test set size", () => {
    const bad = validPayload();
    bad.models.ordinary.predictedProbaPositive = bad.models.ordinary.predictedProbaPositive.slice(0, 3);
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("rejects a positive-label count that does not match nTestMinority", () => {
    const bad = validPayload();
    bad.testLabels[0] = 1;
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("rejects a probability outside [0, 1]", () => {
    const bad = validPayload();
    bad.models.ordinary.predictedProbaPositive[0] = 1.5;
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("rejects an rocAuc outside [0, 1]", () => {
    const bad = validPayload();
    bad.models.classWeighted.rocAuc = 1.2;
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("rejects a missing model key (strict object)", () => {
    const bad = validPayload() as { models: Record<string, unknown> };
    delete bad.models.classWeighted;
    expect(parseImbalanceThresholdData(bad).ok).toBe(false);
  });

  it("accepts the shipped data/abide_imbalance_threshold.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_imbalance_threshold.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseImbalanceThresholdData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
