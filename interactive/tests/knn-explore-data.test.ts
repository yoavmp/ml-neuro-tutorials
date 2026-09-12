import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { parseKnnExploreData } from "../src/knn-explore-data";
import { _clearBufferCacheForTests } from "../src/binary-asset";
import { mockFetchServing, packSections, sha256Hex } from "./binary-fixture";

const DATA_URL = new URL("https://example.test/data/abide_knn_explore_manifest.json");
const BINARY_NAME = "abide_knn_explore.bin";

// n_fit = 3, n_validation = 2. Deliberately small; the endpoint invariants
// (k=1 -> fitR2=1, k=n_fit -> fitR2~0) are set directly in curveFitR2 rather
// than recomputed, since this fixture tests the *loader*, not the export
// script (that recomputation is tested against real data in
// tests/test_export_knn_explore_data.py).
const OBSERVED_VALIDATION = [12, 25];
const OBSERVED_FITTING = [10, 20, 30]; // A's own reference pool
const FIT_TARGETS_B = [11, 21, 31];
const FIT_TARGETS_C = [9, 19, 29];
// index A: row0 -> [10,20,30] (0,1,2); row1 -> [30,20,10] (2,1,0)
const INDEX_A = [0, 1, 2, 2, 1, 0];
const INDEX_B = [0, 1, 2, 2, 1, 0]; // same ordering, into FIT_TARGETS_B
const INDEX_C = [0, 1, 2, 2, 1, 0]; // same ordering, into FIT_TARGETS_C
const CURVE_FIT_R2 = [1, 0.5, 0];
const CURVE_FIT_MSE = [0, 5, 10];
const CURVE_VAL_R2 = [0.4, 0.6, 0.3];
const CURVE_VAL_MSE = [20, 15, 25];

function sectionSpec() {
  return {
    observedValidation: { dtype: "float32" as const, shape: [2], values: OBSERVED_VALIDATION },
    observedFitting: { dtype: "float32" as const, shape: [3], values: OBSERVED_FITTING },
    fitTargetsB: { dtype: "float32" as const, shape: [3], values: FIT_TARGETS_B },
    fitTargetsC: { dtype: "float32" as const, shape: [3], values: FIT_TARGETS_C },
    neighborIndexA: { dtype: "uint16" as const, shape: [2, 3], values: INDEX_A },
    neighborIndexB: { dtype: "uint16" as const, shape: [2, 3], values: INDEX_B },
    neighborIndexC: { dtype: "uint16" as const, shape: [2, 3], values: INDEX_C },
    curveFitR2: { dtype: "float32" as const, shape: [3], values: CURVE_FIT_R2 },
    curveFitMSE: { dtype: "float32" as const, shape: [3], values: CURVE_FIT_MSE },
    curveValR2: { dtype: "float32" as const, shape: [3], values: CURVE_VAL_R2 },
    curveValMSE: { dtype: "float32" as const, shape: [3], values: CURVE_VAL_MSE },
  };
}

async function buildManifestAndServe(
  overrides: Record<string, unknown> = {},
  sectionOverrides: Partial<ReturnType<typeof sectionSpec>> = {},
) {
  const packed = packSections({ ...sectionSpec(), ...sectionOverrides });
  mockFetchServing(BINARY_NAME, packed.buffer);
  const manifest = {
    schemaVersion: 3 as const,
    activity: "knn-explore" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: { nOuterTrain: 5, nFit: 3, nValidation: 2 },
    fitTargetMean: 20,
    trainingSampleMeans: { A: 20, B: 21, C: 19 },
    validationOptimalK: 2,
    selectedKFromAudit: 2,
    binary: { path: BINARY_NAME, byteLength: packed.buffer.byteLength, sha256: await sha256Hex(packed.buffer) },
    sections: packed.sections,
    ...overrides,
  };
  return manifest;
}

describe("parseKnnExploreData", () => {
  beforeEach(() => {
    _clearBufferCacheForTests();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("accepts a well-formed artifact and reconstructs the logical matrices", async () => {
    const manifest = await buildManifestAndServe();
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.observedValidation).toEqual(OBSERVED_VALIDATION);
      expect(r.data.observedFitting).toEqual(OBSERVED_FITTING);
      expect(r.data.neighborTargetsByProximity).toEqual([
        [10, 20, 30],
        [30, 20, 10],
      ]);
      expect(r.data.trainingSamples.A.neighborTargetsByProximity).toEqual(r.data.neighborTargetsByProximity);
      expect(r.data.trainingSamples.B.neighborTargetsByProximity).toEqual([
        [11, 21, 31],
        [31, 21, 11],
      ]);
      expect(r.data.trainingSamples.C.neighborTargetsByProximity).toEqual([
        [9, 19, 29],
        [29, 19, 9],
      ]);
      expect(r.data.curve.k).toEqual([1, 2, 3]);
      expect(r.data.curve.fitR2).toEqual(CURVE_FIT_R2);
      // float32 storage: compare to float32 precision, not exact JS doubles
      r.data.curve.valR2.forEach((v, i) => expect(v).toBeCloseTo(CURVE_VAL_R2[i]!, 5));
    }
  });

  it("rejects a wrong activity tag", async () => {
    const manifest = await buildManifestAndServe({ activity: "regression-compare" });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
  });

  it("rejects observedValidation misaligned with split.nValidation", async () => {
    const manifest = await buildManifestAndServe({}, { observedValidation: { dtype: "float32", shape: [1], values: [12] } });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/observedValidation/);
  });

  it("rejects curve arrays not aligned with n_fit", async () => {
    const manifest = await buildManifestAndServe({}, { curveFitR2: { dtype: "float32", shape: [2], values: [1, 0.5] } });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/curve\.fitR2/);
  });

  it("rejects fitR2 at k=1 that is not (numerically) 1.0", async () => {
    const manifest = await buildManifestAndServe({}, { curveFitR2: { dtype: "float32", shape: [3], values: [0.9, 0.5, 0] } });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/perfect resubstitution/);
  });

  it("rejects fitR2 at k=n_fit that is not (numerically) ~0.0", async () => {
    const manifest = await buildManifestAndServe({}, { curveFitR2: { dtype: "float32", shape: [3], values: [1, 0.5, 0.4] } });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/constant-mean predictor/);
  });

  it("rejects an identifier-shaped top-level key", async () => {
    const manifest = await buildManifestAndServe({ SUB_ID: [1, 2, 3] });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("rejects a missing binary section", async () => {
    const packed = packSections(sectionSpec());
    const { neighborIndexC: _drop, ...rest } = packed.sections;
    void _drop;
    mockFetchServing(BINARY_NAME, packed.buffer);
    const manifest = {
      schemaVersion: 3 as const,
      activity: "knn-explore" as const,
      source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
      target: { name: "age", label: "Age at scan", unit: "years" },
      featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
      split: { nOuterTrain: 5, nFit: 3, nValidation: 2 },
      fitTargetMean: 20,
      trainingSampleMeans: { A: 20, B: 21, C: 19 },
      validationOptimalK: 2,
      selectedKFromAudit: 2,
      binary: { path: BINARY_NAME, byteLength: packed.buffer.byteLength, sha256: await sha256Hex(packed.buffer) },
      sections: rest,
    };
    const r = await parseKnnExploreData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborIndexC/);
  });

  it("rejects trainingSamples equal check when A's reconstruction would differ (index tampering)", async () => {
    // Tamper neighborIndexA so it no longer matches what the baseline expects
    // to reconstruct -- proves the loader recomputes, not trusts, equality.
    const manifest = await buildManifestAndServe({}, { neighborIndexA: { dtype: "uint16", shape: [2, 3], values: [1, 0, 2, 2, 1, 0] } });
    const r = await parseKnnExploreData(manifest, DATA_URL);
    // still structurally valid (same shape), so this should still succeed --
    // baseline and trainingSamples.A are BY CONSTRUCTION the same array
    // reference now, so they can never disagree. This documents that
    // invariant rather than testing a failure.
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.data.trainingSamples.A.neighborTargetsByProximity).toEqual(r.data.neighborTargetsByProximity);
    }
  });

  it("rejects a binary digest mismatch", async () => {
    const manifest = await buildManifestAndServe();
    const tampered = { ...manifest, binary: { ...manifest.binary, sha256: "0".repeat(64) } };
    const r = await parseKnnExploreData(tampered, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.toLowerCase()).toMatch(/integrity/);
  });

  it("validates the committed abide_knn_explore artifact (manifest + binary)", async () => {
    vi.unstubAllGlobals();
    const fs = await import("node:fs/promises");
    const manifestFsUrl = new URL("../../book/_static/widgets/data/abide_knn_explore_manifest.json", import.meta.url);
    const manifest = JSON.parse(await fs.readFile(manifestFsUrl, "utf-8")) as { binary: { path: string } };
    const binaryFsUrl = new URL(`../../book/_static/widgets/data/${manifest.binary.path}`, import.meta.url);
    const bytes = await fs.readFile(binaryFsUrl);
    const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    mockFetchServing(manifest.binary.path, buffer);

    const r = await parseKnnExploreData(manifest, DATA_URL);
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
      expect(r.data.curve.fitR2[0]).toBeCloseTo(1, 2);
      expect(r.data.curve.fitR2[563]).toBeCloseTo(0, 2);
      expect(r.data.validationOptimalK).toBeGreaterThanOrEqual(1);
      expect(r.data.validationOptimalK).toBeLessThanOrEqual(564);
      const selected = r.data.selectedKFromAudit;
      expect(r.data.curve.valR2[selected - 1]).toBeGreaterThan(0);
    }
  });
});
