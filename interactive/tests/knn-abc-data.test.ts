import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { parseKnnAbcData } from "../src/knn-abc-data";
import { _clearBufferCacheForTests } from "../src/binary-asset";
import { mockFetchServing, packSections, sha256Hex } from "./binary-fixture";

const DATA_URL = new URL("https://example.test/data/abide_knn_abc_manifest.json");
const BINARY_NAME = "abide_knn_abc.bin";

// n_train = 3, n_test = 2, kMax = min(3, 2) = 2. Deliberately small.
const OBSERVED_TRAIN = [10, 20, 30];
const OBSERVED_TEST = [12, 25];
// neighborTargetsA (query=test, ref=train): row0 -> [10,20] (idx 0,1); row1 -> [30,20] (idx 2,1)
const INDEX_A = [0, 1, 2, 1];
// neighborTargetsB (query=train, ref=train, self-inclusive): [10,20],[20,10],[30,20]
const INDEX_B = [0, 1, 1, 0, 2, 1];
// neighborTargetsC (query=test, ref=test, self-inclusive): [12,25],[25,12]
const INDEX_C = [0, 1, 1, 0];

function sectionSpec() {
  return {
    observedTrain: { dtype: "float32" as const, shape: [3], values: OBSERVED_TRAIN },
    observedTest: { dtype: "float32" as const, shape: [2], values: OBSERVED_TEST },
    neighborIndexA: { dtype: "uint16" as const, shape: [2, 2], values: INDEX_A },
    neighborIndexB: { dtype: "uint16" as const, shape: [3, 2], values: INDEX_B },
    neighborIndexC: { dtype: "uint16" as const, shape: [2, 2], values: INDEX_C },
  };
}

async function buildManifestAndServe(
  overrides: Record<string, unknown> = {},
  sectionOverrides: Partial<ReturnType<typeof sectionSpec>> = {},
) {
  const packed = packSections({ ...sectionSpec(), ...sectionOverrides });
  mockFetchServing(BINARY_NAME, packed.buffer);
  const manifest = {
    schemaVersion: 2 as const,
    activity: "knn-abc" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: { nTrain: 3, nTest: 2, kMax: 2 },
    selectedKFromAudit: 1,
    binary: { path: BINARY_NAME, byteLength: packed.buffer.byteLength, sha256: await sha256Hex(packed.buffer) },
    sections: packed.sections,
    ...overrides,
  };
  return manifest;
}

describe("parseKnnAbcData", () => {
  beforeEach(() => {
    _clearBufferCacheForTests();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("accepts a well-formed artifact and reconstructs the logical matrices", async () => {
    const manifest = await buildManifestAndServe();
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.observedTrain).toEqual(OBSERVED_TRAIN);
      expect(r.data.observedTest).toEqual(OBSERVED_TEST);
      expect(r.data.neighborTargetsA).toEqual([
        [10, 20],
        [30, 20],
      ]);
      expect(r.data.neighborTargetsB).toEqual([
        [10, 20],
        [20, 10],
        [30, 20],
      ]);
      expect(r.data.neighborTargetsC).toEqual([
        [12, 25],
        [25, 12],
      ]);
    }
  });

  it("rejects a wrong activity tag", async () => {
    const manifest = await buildManifestAndServe({ activity: "knn-explore" });
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
  });

  it("rejects kMax not equal to min(nTrain, nTest)", async () => {
    const manifest = await buildManifestAndServe({ split: { nTrain: 3, nTest: 2, kMax: 3 } });
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
  });

  it("rejects a binary file whose byte length does not match the manifest", async () => {
    const manifest = await buildManifestAndServe();
    const bad = { ...manifest, binary: { ...manifest.binary, byteLength: manifest.binary.byteLength + 4 } };
    const r = await parseKnnAbcData(bad, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.toLowerCase()).toMatch(/incomplete|size|byte/);
  });

  it("rejects a binary file that fails its SHA-256 digest check", async () => {
    const manifest = await buildManifestAndServe();
    const tampered = { ...manifest, binary: { ...manifest.binary, sha256: "0".repeat(64) } };
    const r = await parseKnnAbcData(tampered, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error.toLowerCase()).toMatch(/integrity/);
  });

  it("rejects k=1 (B) not matching observedTrain", async () => {
    const indexB = [1, 0, 1, 0, 2, 1]; // row0 col0 now points at index 1 (value 20), not 0 (value 10)
    const manifest = await buildManifestAndServe({}, { neighborIndexB: { dtype: "uint16", shape: [3, 2], values: indexB } });
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborTargetsB/);
  });

  it("rejects an out-of-bounds neighbour index", async () => {
    const manifest = await buildManifestAndServe(
      {},
      { neighborIndexA: { dtype: "uint16", shape: [2, 2], values: [0, 1, 2, 999] } },
    );
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/out of bounds/);
  });

  it("rejects selectedKFromAudit out of range", async () => {
    const manifest = await buildManifestAndServe({ selectedKFromAudit: 99 });
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
  });

  it("rejects an identifier-shaped top-level key", async () => {
    const manifest = await buildManifestAndServe({ SUB_ID: [1, 2, 3] });
    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("validates the committed abide_knn_abc artifact (manifest + binary)", async () => {
    vi.unstubAllGlobals();
    const fs = await import("node:fs/promises");
    const manifestFsUrl = new URL("../../book/_static/widgets/data/abide_knn_abc_manifest.json", import.meta.url);
    const manifest = JSON.parse(await fs.readFile(manifestFsUrl, "utf-8")) as { binary: { path: string } };
    const binaryFsUrl = new URL(`../../book/_static/widgets/data/${manifest.binary.path}`, import.meta.url);
    const bytes = await fs.readFile(binaryFsUrl);
    const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    mockFetchServing(manifest.binary.path, buffer);

    const r = await parseKnnAbcData(manifest, DATA_URL);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.target.name).toBe("age");
      expect(r.data.featureRecipe.featureCount).toBe(360);
      expect(r.data.split.nTrain).toBe(753);
      expect(r.data.split.nTest).toBe(251);
      expect(r.data.split.kMax).toBe(251);
      expect(r.data.observedTrain).toHaveLength(753);
      expect(r.data.observedTest).toHaveLength(251);
      expect(r.data.neighborTargetsA).toHaveLength(251);
      expect(r.data.neighborTargetsB).toHaveLength(753);
      expect(r.data.neighborTargetsC).toHaveLength(251);
      expect(r.data.neighborTargetsA[0]).toHaveLength(251);
      const bFirst = r.data.neighborTargetsB.map((row) => row[0]);
      for (let i = 0; i < bFirst.length; i += 1) expect(bFirst[i]).toBeCloseTo(r.data.observedTrain[i]!, 2);
      const cFirst = r.data.neighborTargetsC.map((row) => row[0]);
      for (let i = 0; i < cFirst.length; i += 1) expect(cFirst[i]).toBeCloseTo(r.data.observedTest[i]!, 2);
      expect(r.data.selectedKFromAudit).toBe(15);
    }
  });
});
