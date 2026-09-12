import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { _clearBufferCacheForTests, binaryManifestBaseSchema, loadBinaryAsset } from "../src/binary-asset";
import { mockFetchServing, packSections, sha256Hex } from "./binary-fixture";

const DATA_URL = new URL("https://example.test/data/manifest.json");
const testManifestSchema = binaryManifestBaseSchema.extend({ activity: z.literal("test-activity") });

async function baseManifest(values = [1, 2, 3, 4]) {
  const packed = packSections({ v: { dtype: "float32", shape: [4], values } });
  return {
    manifest: {
      schemaVersion: 1,
      activity: "test-activity" as const,
      binary: { path: "payload.bin", byteLength: packed.buffer.byteLength, sha256: await sha256Hex(packed.buffer) },
      sections: packed.sections,
    },
    buffer: packed.buffer,
  };
}

describe("loadBinaryAsset", () => {
  beforeEach(() => {
    _clearBufferCacheForTests();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads and decodes a well-formed manifest + binary", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const result = await loadBinaryAsset(manifest, testManifestSchema, DATA_URL);
    expect(result.ok, result.ok ? "" : result.error).toBe(true);
    if (result.ok) {
      expect(Array.from(result.value.sections.v as Float32Array)).toEqual([1, 2, 3, 4]);
    }
  });

  it("rejects an invalid manifest (schema failure)", async () => {
    const result = await loadBinaryAsset({ activity: "test-activity" }, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/Invalid activity manifest/);
  });

  it("rejects a wrong activity discriminator", async () => {
    const { manifest } = await baseManifest();
    const result = await loadBinaryAsset({ ...manifest, activity: "other" }, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
  });

  it("rejects an identifier-shaped top-level manifest key", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const result = await loadBinaryAsset({ ...manifest, subject_id: "x" }, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/identifier-shaped/);
  });

  it("rejects an identifier-shaped section name", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, sections: { ...manifest.sections, participant_id: manifest.sections.v } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/identifier-shaped/);
  });

  it("rejects a cross-origin binary path", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, binary: { ...manifest.binary, path: "https://evil.example/payload.bin" } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/not safe to load|same-origin/);
  });

  it("rejects a byte-length mismatch", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, binary: { ...manifest.binary, byteLength: manifest.binary.byteLength + 4 } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.toLowerCase()).toMatch(/incomplete|byte/);
  });

  it("rejects a SHA-256 digest mismatch", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, binary: { ...manifest.binary, sha256: "0".repeat(64) } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.toLowerCase()).toMatch(/integrity/);
  });

  it("rejects a section that extends past the end of the file", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, sections: { v: { ...manifest.sections.v, byteLength: manifest.sections.v!.byteLength + 100 } } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/malformed|extends past/);
  });

  it("rejects a misaligned section offset", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, sections: { v: { ...manifest.sections.v, byteOffset: 1 } } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/not aligned/);
  });

  it("rejects a shape/byteLength mismatch", async () => {
    const { manifest, buffer } = await baseManifest();
    mockFetchServing("payload.bin", buffer);
    const bad = { ...manifest, sections: { v: { ...manifest.sections.v, shape: [999] } } };
    const result = await loadBinaryAsset(bad, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/implies/);
  });

  it("decodes uint16 sections correctly", async () => {
    const packed = packSections({ idx: { dtype: "uint16", shape: [3], values: [0, 65535, 42] } });
    const manifest = {
      schemaVersion: 1,
      activity: "test-activity" as const,
      binary: { path: "payload.bin", byteLength: packed.buffer.byteLength, sha256: await sha256Hex(packed.buffer) },
      sections: packed.sections,
    };
    mockFetchServing("payload.bin", packed.buffer);
    const result = await loadBinaryAsset(manifest, testManifestSchema, DATA_URL);
    expect(result.ok, result.ok ? "" : result.error).toBe(true);
    if (result.ok) {
      expect(Array.from(result.value.sections.idx as Uint16Array)).toEqual([0, 65535, 42]);
    }
  });

  it("does not re-fetch the same binary URL twice on one page", async () => {
    const { manifest, buffer } = await baseManifest();
    const fetchSpy = vi.fn(async () => ({ ok: true, status: 200, arrayBuffer: async () => buffer }) as unknown as Response);
    vi.stubGlobal("fetch", fetchSpy);

    const [a, b] = await Promise.all([
      loadBinaryAsset(manifest, testManifestSchema, DATA_URL),
      loadBinaryAsset(manifest, testManifestSchema, DATA_URL),
    ]);
    expect(a.ok).toBe(true);
    expect(b.ok).toBe(true);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("produces a clear error, not a throw, when fetch itself fails", async () => {
    const { manifest } = await baseManifest();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network down");
      }),
    );
    const result = await loadBinaryAsset(manifest, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/Could not load/);
  });

  it("produces a clear error on a non-OK HTTP response", async () => {
    const { manifest } = await baseManifest();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 404, arrayBuffer: async () => new ArrayBuffer(0) }) as unknown as Response),
    );
    const result = await loadBinaryAsset(manifest, testManifestSchema, DATA_URL);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(/Could not load|404/);
  });
});
