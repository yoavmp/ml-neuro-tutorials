import { describe, expect, it } from "vitest";
import { parseClassificationThresholdData } from "../src/classification-threshold-data";

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "classification-threshold",
    source: { pinnedCommit: "abc123", brainTableSha256: "def456" },
    positiveClass: "autism",
    negativeClass: "control",
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: { testSize: 0.25, randomState: 42, nTrain: 3, nTest: 4 },
    model: "Pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))",
    aucFromAudit: 0.569,
    accuracyAtHalfFromAudit: 0.546,
    labels: [1, 0, 1, 0],
    probabilities: [0.6, 0.3, 0.55, 0.1],
  };
}

describe("parseClassificationThresholdData", () => {
  it("accepts a well-formed payload", () => {
    const result = parseClassificationThresholdData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("rejects a schemaVersion mismatch", () => {
    const bad = { ...validPayload(), schemaVersion: 2 };
    const result = parseClassificationThresholdData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects labels/probabilities length mismatch with split.nTest", () => {
    const bad = { ...validPayload(), labels: [1, 0, 1] };
    const result = parseClassificationThresholdData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects labels containing only one class", () => {
    const bad = { ...validPayload(), labels: [1, 1, 1, 1] };
    const result = parseClassificationThresholdData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a probability outside [0, 1]", () => {
    const bad = { ...validPayload(), probabilities: [1.4, 0.3, 0.55, 0.1] };
    const result = parseClassificationThresholdData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a non-object payload", () => {
    expect(parseClassificationThresholdData(null).ok).toBe(false);
    expect(parseClassificationThresholdData("nope").ok).toBe(false);
  });
});
