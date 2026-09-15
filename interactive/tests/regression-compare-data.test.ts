import { describe, expect, it } from "vitest";
import { parseRegressionCatalog } from "../src/regression-compare-data";
import { r2Score, meanSquaredError } from "../src/regression-compare";

function base() {
  // 6 participants: 4 training, 2 held-out test (WP19: one fixed split, no folds).
  const observedTest = [90, 120, 95, 105];
  const predicted = [...observedTest];
  return {
    schemaVersion: 2 as const,
    activity: "regression-compare" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "FIQ", label: "Full-scale IQ", unit: "IQ points" },
    cohort: { n: 6, requirement: "FIQ present", diagnosisNote: "same sites" },
    holdoutSplit: { testSize: 0.25, randomState: 42, stratify: "group", nTrain: 2, nTest: 4 },
    preprocessing: "Pipeline(StandardScaler, LinearRegression) fit on the training participants only",
    observedTest,
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
        testR2: r2Score(observedTest, predicted),
        testMSE: meanSquaredError(observedTest, predicted),
      },
      {
        key: "occipital__CT",
        bundle: "occipital",
        measures: ["CT"],
        featureCount: 4,
        disabled: true,
        reason: "too many features for this split",
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

  it("rejects observedTest that disagrees with holdoutSplit.nTest", () => {
    const b = base();
    b.observedTest = b.observedTest.slice(0, 3);
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/observedTest/);
  });

  it("rejects a holdoutSplit whose nTrain + nTest disagrees with cohort.n", () => {
    const b = base();
    b.holdoutSplit.nTrain = 1;
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/holdoutSplit/);
  });

  it("rejects a stored testR2 that disagrees with the predictions", () => {
    const b = base();
    b.models[0]!.testR2 = 0.42;
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/testR2/);
  });

  it("rejects an enabled model whose predictions are misaligned", () => {
    const b = base();
    b.models[0]!.predicted = [1, 2, 3];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/align with observedTest/);
  });

  it("rejects a disabled model that still carries predictions", () => {
    const b = base();
    (b.models[1] as Record<string, unknown>).predicted = [1, 2, 3, 4];
    const r = parseRegressionCatalog(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/must not carry predictions/);
  });

  it("rejects an identifier-shaped top-level key", () => {
    const b = base() as Record<string, unknown>;
    b.SUB_ID = [1, 2, 3, 4];
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
      // WP12: the activity's target is `age` (native brain-table column, N =
      // 1004, no join / no missingness) -- not `FIQ` (N = 908) any more.
      expect(r.data.target.name).toBe("age");
      expect(r.data.cohort.n).toBe(1004);
      // WP19: one fixed, reproducible 75/25 train/test split -- no cross-validation.
      expect(r.data.holdoutSplit.nTrain).toBe(753);
      expect(r.data.holdoutSplit.nTest).toBe(251);
      expect(r.data.observedTest).toHaveLength(251);
      expect(r.data.activity).toBe("regression-compare");
      const enabled = r.data.models.filter((m) => !m.disabled);
      expect(enabled.length).toBeGreaterThan(20);
      // Every enabled model's stored metrics recompute from its predictions.
      for (const m of enabled) {
        expect(Math.abs(r2Score(r.data.observedTest, m.predicted!) - m.testR2!)).toBeLessThan(1e-3);
      }
      // Unlike FIQ (WP11), age is genuinely predictable from cortical structure:
      // almost every enabled configuration scores above zero on the fixed
      // held-out split (a couple of the smallest, weakest combinations can
      // legitimately land at/near zero under a single split's higher variance).
      const nPositive = enabled.filter((m) => m.testR2! > 0).length;
      expect(nPositive).toBeGreaterThanOrEqual(Math.round(0.9 * enabled.length));
      // The default panels (frontoparietal vs occipital, both cortical
      // thickness) still differ, just both positive.
      const fpar = enabled.find((m) => m.key === "frontoparietal__CT")!;
      const occ = enabled.find((m) => m.key === "occipital__CT")!;
      expect(fpar.testR2!).toBeGreaterThan(0);
      expect(occ.testR2!).toBeGreaterThan(0);
      expect(fpar.testR2!).toBeLessThan(occ.testR2!);
    }
  });
});
