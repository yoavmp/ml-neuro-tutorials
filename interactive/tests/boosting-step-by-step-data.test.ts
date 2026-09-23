import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseBoostingStepByStepData } from "../src/boosting-step-by-step-data";

const REAL_ARTIFACT = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../book/_static/widgets/data/boosting_step_by_step.json", import.meta.url)),
    "utf-8",
  ),
);

function stageZero(n = 4): Record<string, unknown> {
  return {
    stage: 0,
    ensemblePrediction: Array.from({ length: n }, () => 10),
    residualBeforeUpdate: Array.from({ length: n }, () => 2),
    trainMSE: 4,
    stump: null,
    treePrediction: null,
    scaledCorrection: null,
  };
}

function stageOne(n = 4): Record<string, unknown> {
  return {
    stage: 1,
    ensemblePrediction: Array.from({ length: n }, () => 11),
    residualBeforeUpdate: Array.from({ length: n }, () => 2),
    trainMSE: 2,
    stump: { threshold: 5, leftValue: -1, rightValue: 1 },
    treePrediction: Array.from({ length: n }, () => 1),
    scaledCorrection: Array.from({ length: n }, () => 0.3),
  };
}

function base() {
  const observations = Array.from({ length: 4 }, (_, i) => ({ id: i, x: i * 2.5, y: 8 + i }));
  return {
    schemaVersion: 1 as const,
    activity: "boosting-step-by-step" as const,
    syntheticDataNote: "This dataset is simulated, not ABIDE observations.",
    generatingProcess: {
      formula: "y = C + A*sin(FREQ*x) + B*x + noise",
      x: { distribution: "Uniform", low: 0, high: 10 },
      coefficients: { C: 5, A: 4, FREQ: 0.9, B: 0.6, noiseSD: 1.2 },
      nObservations: 4,
      seed: 7,
      seedNote: "Fixed before generation.",
    },
    feature: { name: "x", label: "Predictor (x)" },
    target: { name: "y", label: "Target (y)" },
    observations,
    learningRates: [0.3],
    nStages: 1,
    stumpSettings: { maxDepth: 1 },
    updateEquation: "yhat_i^(m) = yhat_i^(m-1) + eta * f_m(x_i)",
    stagesByLearningRate: { "0.3": [stageZero(), stageOne()] } as Record<string, Record<string, unknown>[]>,
  };
}

describe("parseBoostingStepByStepData", () => {
  it("accepts the real committed artifact", () => {
    const r = parseBoostingStepByStepData(REAL_ARTIFACT);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("accepts a well-formed minimal artifact", () => {
    const r = parseBoostingStepByStepData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseBoostingStepByStepData({ ...base(), activity: "boosting-parameter-explorer" }).ok).toBe(false);
  });

  it("rejects stage 0 carrying a stump", () => {
    const b = base();
    b.stagesByLearningRate["0.3"]![0] = { ...stageZero(), stump: { threshold: 1, leftValue: 0, rightValue: 0 } };
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });

  it("rejects a later stage missing its stump", () => {
    const b = base();
    b.stagesByLearningRate["0.3"]![1] = { ...stageOne(), stump: null };
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });

  it("rejects a missing stage set for a declared learning rate", () => {
    const b = base() as Record<string, unknown>;
    b.learningRates = [0.3, 0.7];
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });

  it("rejects a stage array shorter than nStages+1", () => {
    const b = base();
    b.stagesByLearningRate["0.3"] = [stageZero()];
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });

  it("rejects a prediction array misaligned with the observation count", () => {
    const b = base();
    b.stagesByLearningRate["0.3"]![1]!.ensemblePrediction = [1, 2];
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });

  it("rejects a missing generatingProcess block", () => {
    const b = base() as Record<string, unknown>;
    delete b.generatingProcess;
    expect(parseBoostingStepByStepData(b).ok).toBe(false);
  });
});
