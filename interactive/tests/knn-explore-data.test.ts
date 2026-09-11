import { describe, expect, it } from "vitest";
import { parseKnnExploreData } from "../src/knn-explore-data";

function base() {
  // n_fit = 3, n_validation = 2. Deliberately small; the endpoint invariants
  // (k=1 -> fitR2=1, k=n_fit -> fitR2~0) are set directly rather than
  // recomputed, since this fixture tests the *schema*, not the export script
  // (that recomputation is tested against real data in
  // tests/test_export_knn_explore_data.py).
  const neighborTargetsByProximity = [
    [10, 20, 30],
    [30, 20, 10],
  ];
  return {
    schemaVersion: 2 as const,
    activity: "knn-explore" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: { nOuterTrain: 5, nFit: 3, nValidation: 2 },
    fitTargetMean: 20,
    validationOptimalK: 2,
    selectedKFromAudit: 2,
    observedValidation: [12, 25],
    observedFitting: [10, 20, 30],
    neighborTargetsByProximity,
    trainingSamples: {
      A: { fitTargetMean: 20, neighborTargetsByProximity },
      B: { fitTargetMean: 21, neighborTargetsByProximity: [[11, 21, 31], [31, 21, 11]] },
      C: { fitTargetMean: 19, neighborTargetsByProximity: [[9, 19, 29], [29, 19, 9]] },
    },
    curve: {
      k: [1, 2, 3],
      fitR2: [1, 0.5, 0],
      fitMSE: [0, 5, 10],
      valR2: [0.4, 0.6, 0.3],
      valMSE: [20, 15, 25],
    },
  };
}

describe("parseKnnExploreData", () => {
  it("accepts a well-formed artifact", () => {
    const r = parseKnnExploreData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseKnnExploreData({ ...base(), activity: "regression-compare" }).ok).toBe(false);
  });

  it("rejects observedValidation misaligned with split.nValidation", () => {
    const b = base();
    b.observedValidation = [12];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/observedValidation/);
  });

  it("rejects a neighborTargetsByProximity row of the wrong length", () => {
    const b = base();
    b.neighborTargetsByProximity[0] = [10, 20];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborTargetsByProximity/);
  });

  it("rejects curve.k that is not exactly [1..n_fit]", () => {
    const b = base();
    b.curve.k = [1, 2, 4];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/curve\.k/);
  });

  it("rejects fitR2 at k=1 that is not (numerically) 1.0", () => {
    const b = base();
    b.curve.fitR2 = [0.9, 0.5, 0];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/perfect resubstitution/);
  });

  it("rejects fitR2 at k=n_fit that is not (numerically) ~0.0", () => {
    const b = base();
    b.curve.fitR2 = [1, 0.5, 0.4];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/constant-mean predictor/);
  });

  it("rejects an identifier-shaped top-level key", () => {
    const b = base() as Record<string, unknown>;
    b.SUB_ID = [1, 2, 3];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("rejects a missing training sample", () => {
    const b = base() as Record<string, unknown>;
    delete (b.trainingSamples as Record<string, unknown>).C;
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
  });

  it("rejects a training sample whose neighborTargetsByProximity row has the wrong length", () => {
    const b = base();
    b.trainingSamples.B.neighborTargetsByProximity[0] = [1, 2];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/trainingSamples/);
  });

  it("rejects trainingSamples.A that does not equal the top-level baseline", () => {
    const b = base();
    b.trainingSamples.A.neighborTargetsByProximity = [
      [1, 2, 3],
      [3, 2, 1],
    ];
    const r = parseKnnExploreData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/trainingSamples.*A/);
  });

  it("validates the committed abide_knn_explore.json artifact", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL("../../book/_static/widgets/data/abide_knn_explore.json", import.meta.url);
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseKnnExploreData(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.target.name).toBe("age");
      expect(r.data.featureRecipe.featureCount).toBe(360);
      expect(r.data.split.nOuterTrain).toBe(753);
      expect(r.data.split.nFit).toBe(564);
      expect(r.data.split.nValidation).toBe(189);
      expect(r.data.observedValidation).toHaveLength(189);
      expect(r.data.observedFitting).toHaveLength(564);
      expect(r.data.neighborTargetsByProximity).toHaveLength(189);
      expect(r.data.neighborTargetsByProximity[0]).toHaveLength(564);
      expect(Object.keys(r.data.trainingSamples).sort()).toEqual(["A", "B", "C"]);
      expect(r.data.trainingSamples.A.neighborTargetsByProximity).toEqual(r.data.neighborTargetsByProximity);
      expect(r.data.trainingSamples.B.neighborTargetsByProximity).toHaveLength(189);
      expect(r.data.trainingSamples.B.neighborTargetsByProximity[0]).toHaveLength(564);
      expect(r.data.trainingSamples.B.neighborTargetsByProximity).not.toEqual(r.data.neighborTargetsByProximity);
      expect(r.data.curve.k).toHaveLength(564);
      expect(r.data.curve.k[0]).toBe(1);
      expect(r.data.curve.k[563]).toBe(564);
      // k=1 is a perfect (trivial) resubstitution fit
      expect(r.data.curve.fitR2[0]).toBeCloseTo(1, 6);
      // k=n_fit predicts the constant fitting-set mean everywhere
      expect(r.data.curve.fitR2[563]).toBeCloseTo(0, 3);
      expect(r.data.validationOptimalK).toBeGreaterThanOrEqual(1);
      expect(r.data.validationOptimalK).toBeLessThanOrEqual(564);
      // the CV-selected k from the audit is a genuinely usable model
      const selected = r.data.selectedKFromAudit;
      expect(r.data.curve.valR2[selected - 1]).toBeGreaterThan(0);
    }
  });
});
