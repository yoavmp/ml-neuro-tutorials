import { describe, expect, it } from "vitest";
import { parseRegularizationExploreData } from "../src/regularization-explore-data";

function metrics(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    trainMSE: 10,
    valMSE: 20,
    trainR2: 0.8,
    valR2: 0.5,
    nonzeroCount: 3,
    coefNorm: 1.2,
    predictedValidation: [10, 11, 12],
    coefficients: [0.5, -0.3, 0.1],
    ...overrides,
  };
}

function alphaEntry(bestIndex = 1) {
  return {
    alphaGrid: [0.1, 1, 10],
    bestAlphaIndex: bestIndex,
    perAlpha: [metrics(), metrics({ valMSE: 15 }), metrics({ valMSE: 25 })],
  };
}

function base() {
  return {
    schemaVersion: 1 as const,
    activity: "regularization-explore" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan (years)", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: {
      outerHoldout: { testSize: 0.25, randomState: 42, stratify: "group", nTrain: 753, nTest: 251 },
      devSplit: { testSize: 0.25, randomState: 7, stratify: "group", nFit: 564, nVal: 3 },
    },
    observedFitting: new Array(564).fill(15),
    observedValidation: [10, 11, 12],
    trackedFeatures: ["fsCT_L_46_ROI", "fsCT_R_46_ROI", "fsCT_L_V1_ROI"],
    models: {
      linear: metrics(),
      ridge: alphaEntry(1),
      lasso: alphaEntry(0),
    },
  };
}

describe("parseRegularizationExploreData", () => {
  it("accepts a well-formed artifact", () => {
    const r = parseRegularizationExploreData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseRegularizationExploreData({ ...base(), activity: "regression-compare" }).ok).toBe(false);
  });

  it("rejects observedValidation length mismatched with split.devSplit.nVal", () => {
    const b = base();
    b.split.devSplit.nVal = 999;
    expect(parseRegularizationExploreData(b).ok).toBe(false);
  });

  it("rejects a model whose coefficients length disagrees with trackedFeatures", () => {
    const b = base();
    b.models.linear.coefficients = [0.1, 0.2];
    expect(parseRegularizationExploreData(b).ok).toBe(false);
  });

  it("rejects a ridge/lasso entry with mismatched alphaGrid/perAlpha lengths", () => {
    const b = base();
    b.models.ridge.perAlpha = b.models.ridge.perAlpha.slice(0, 2);
    expect(parseRegularizationExploreData(b).ok).toBe(false);
  });

  it("rejects a predictedValidation array misaligned with observedValidation", () => {
    const b = base();
    b.models.linear.predictedValidation = [1, 2];
    expect(parseRegularizationExploreData(b).ok).toBe(false);
  });

  it("rejects an out-of-range bestAlphaIndex", () => {
    const b = base();
    b.models.lasso.bestAlphaIndex = 99;
    expect(parseRegularizationExploreData(b).ok).toBe(false);
  });
});
