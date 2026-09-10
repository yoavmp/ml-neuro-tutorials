import { describe, expect, it } from "vitest";
import { parseRegressionCatalog } from "../src/regression-compare-data";
import { r2Score, meanSquaredError } from "../src/regression-compare";

function base() {
  // 6 participants, 2 folds. Model A predictions are exact -> R2 = 1.
  const observed = [100, 110, 90, 120, 95, 105];
  const predicted = [...observed];
  return {
    schemaVersion: 1 as const,
    activity: "regression-compare" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "FIQ", label: "Full-scale IQ", unit: "IQ points" },
    cohort: { n: 6, requirement: "FIQ present", diagnosisNote: "same sites" },
    crossValidation: { kind: "KFold" as const, nSplits: 2, shuffle: true, randomState: 0, foldTrainN: 3 },
    preprocessing: "Pipeline(StandardScaler, LinearRegression)",
    observed,
    foldOf: [0, 1, 0, 1, 0, 1],
    bundles: {
      frontoparietal: { label: "Frontoparietal", rois: ["46", "PGs"] },
      occipital: { label: "Occipital", rois: ["V1", "V2"] },
    },
    measures: { CT: { label: "cortical thickness", unit: "mm" } },
    measurementSubsets: [["CT"]],
    models: [
      {
        key: "frontoparietal__CT",
        bundle: "frontoparietal",
        measures: ["CT"],
        featureCount: 4,
        disabled: false,
        predicted,
        cvR2: r2Score(observed, predicted),
        cvMSE: meanSquaredError(observed, predicted),
      },
      {
        key: "occipital__CT",
        bundle: "occipital",
        measures: ["CT"],
        featureCount: 4,
        disabled: true,
        reason: "too many features for this fold",
      },
    ],
  };
}

describe("parseRegressionCatalog", () => {
  it("accepts a well-formed catalog", () => {
    const r = parseRegressionCatalog(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseRegressionCatalog({ ...base(), activity: "eda-histogram" }).ok).toBe(false);
  });

  it("rejects observed that disagrees with cohort.n", () => {
    const b = base();
    b.observed = b.observed.slice(0, 5);
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/observed/);
  });

  it("rejects foldOf that does not use every fold index", () => {
    const b = base();
    b.foldOf = [0, 0, 0, 0, 0, 0];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/fold index/);
  });

  it("rejects a stored cvR2 that disagrees with the predictions", () => {
    const b = base();
    b.models[0]!.cvR2 = 0.42;
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/cvR2/);
  });

  it("rejects an enabled model whose predictions are misaligned", () => {
    const b = base();
    b.models[0]!.predicted = [1, 2, 3];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/align with observed/);
  });

  it("rejects a disabled model that still carries predictions", () => {
    const b = base();
    (b.models[1] as Record<string, unknown>).predicted = [1, 2, 3, 4, 5, 6];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/must not carry predictions/);
  });

  it("rejects an identifier-shaped top-level key", () => {
    const b = base() as Record<string, unknown>;
    b.SUB_ID = [1, 2, 3, 4, 5, 6];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("rejects a model referencing an unknown bundle", () => {
    const b = base();
    b.models[0]!.bundle = "temporal";
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/unknown bundle/);
  });

  it("validates the committed abide_regression_models.json artifact", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_regression_models.json",
      import.meta.url,
    );
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseRegressionCatalog(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.cohort.n).toBe(908);
      expect(r.data.observed).toHaveLength(908);
      expect(r.data.foldOf).toHaveLength(908);
      expect(r.data.crossValidation.nSplits).toBe(5);
      expect(r.data.activity).toBe("regression-compare");
      const enabled = r.data.models.filter((m) => !m.disabled);
      expect(enabled.length).toBeGreaterThan(20);
      // Every enabled model's stored metrics recompute from its predictions.
      for (const m of enabled) {
        expect(Math.abs(r2Score(r.data.observed, m.predicted!) - m.cvR2!)).toBeLessThan(1e-3);
      }
      // The literature-motivated frontoparietal-CT bundle does NOT beat occipital-CT here.
      const fpar = enabled.find((m) => m.key === "frontoparietal__CT")!;
      const occ = enabled.find((m) => m.key === "occipital__CT")!;
      expect(fpar.cvR2!).toBeLessThan(0);
      expect(occ.cvR2!).toBeLessThan(0);
      expect(fpar.cvR2!).toBeLessThan(occ.cvR2!);
    }
  });
});
