import { describe, expect, it } from "vitest";
import { parsePcaProjectionData, projectAtAngle, type PcaProjectionData } from "../src/pca-projection-data";

function validData(): PcaProjectionData {
  // A simple, exactly-known square-ish cloud: 4 points at the corners of an
  // axis-aligned rectangle, already mean-centered, so the math below can be
  // checked by hand.
  return {
    schemaVersion: 1,
    activity: "pca-projection",
    syntheticDataNote: "note",
    generatingProcess: {
      distribution: "mean-zero correlated Gaussian",
      sigmaX: 3,
      sigmaY: 2,
      rho: 0.5,
      nObservations: 4,
      seed: 11,
      seedNote: "note",
      centeringNote: "note",
    },
    featureX: { name: "x", label: "Feature 1" },
    featureY: { name: "y", label: "Feature 2" },
    observations: [
      { id: 0, x: 2, y: 0 },
      { id: 1, x: -2, y: 0 },
      { id: 2, x: 0, y: 1 },
      { id: 3, x: 0, y: -1 },
    ],
    totalVariance: 2.5, // mean(x^2) + mean(y^2) = (4+4+0+0)/4 + (0+0+1+1)/4 = 2 + 0.5
    truePc1: { angleDeg: 0, explainedVarianceRatio: 0.8 },
    angleSliderDeg: { min: 0, max: 180, step: 1 },
  };
}

describe("parsePcaProjectionData", () => {
  it("accepts valid data", () => {
    const result = parsePcaProjectionData(validData());
    expect(result.ok).toBe(true);
  });

  it("rejects a mismatched observation count", () => {
    const bad = validData();
    bad.generatingProcess.nObservations = 40;
    const result = parsePcaProjectionData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects an invalid angle slider range", () => {
    const bad = validData();
    bad.angleSliderDeg = { min: 90, max: 10, step: 1 };
    const result = parsePcaProjectionData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects malformed input with a readable error", () => {
    const result = parsePcaProjectionData({ nope: true });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain("Invalid pca-projection data");
    }
  });
});

describe("projectAtAngle", () => {
  it("captures all x-axis variance at angle 0", () => {
    const data = validData();
    const result = projectAtAngle(data, 0);
    expect(result.varianceCaptured).toBeCloseTo(2, 6);
    expect(result.reconstructionMSE).toBeCloseTo(0.5, 6);
    expect(result.proportionVarianceCaptured).toBeCloseTo(0.8, 6);
  });

  it("captures all y-axis variance at angle 90", () => {
    const data = validData();
    const result = projectAtAngle(data, 90);
    expect(result.varianceCaptured).toBeCloseTo(0.5, 6);
    expect(result.reconstructionMSE).toBeCloseTo(2, 6);
  });

  it("variance captured plus reconstruction MSE always equals total variance", () => {
    const data = validData();
    for (const angle of [0, 17, 45, 63, 90, 128, 180]) {
      const result = projectAtAngle(data, angle);
      expect(result.varianceCaptured + result.reconstructionMSE).toBeCloseTo(data.totalVariance, 6);
    }
  });

  it("is periodic-symmetric: angle and angle+180 capture the same variance", () => {
    const data = validData();
    const a = projectAtAngle(data, 40);
    const b = projectAtAngle(data, 220);
    expect(a.varianceCaptured).toBeCloseTo(b.varianceCaptured, 6);
  });
});
