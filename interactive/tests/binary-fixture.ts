// Shared test helper: pack typed-array sections into a binary-asset blob the
// same way scripts/binary_asset.py does (4-byte aligned, little-endian), and
// mock `fetch` to serve it -- so knn-explore-data / knn-abc-data tests can
// build small, hand-computed manifests without touching real committed data.
import { vi } from "vitest";

export interface FixtureSection {
  dtype: "float32" | "uint16";
  shape: number[];
  values: number[];
}

export interface PackedFixture {
  sections: Record<string, { dtype: string; shape: number[]; byteOffset: number; byteLength: number }>;
  buffer: ArrayBuffer;
}

export function packSections(entries: Record<string, FixtureSection>): PackedFixture {
  const chunks: Uint8Array[] = [];
  let offset = 0;
  const sections: PackedFixture["sections"] = {};
  for (const [name, { dtype, shape, values }] of Object.entries(entries)) {
    const itemSize = dtype === "float32" ? 4 : 2;
    const buf = new ArrayBuffer(values.length * itemSize);
    if (dtype === "float32") new Float32Array(buf).set(values);
    else new Uint16Array(buf).set(values);
    const bytes = new Uint8Array(buf);
    const pad = (4 - (bytes.length % 4)) % 4;
    sections[name] = { dtype, shape, byteOffset: offset, byteLength: bytes.length };
    chunks.push(bytes);
    if (pad) chunks.push(new Uint8Array(pad));
    offset += bytes.length + pad;
  }
  const total = new Uint8Array(offset);
  let pos = 0;
  for (const c of chunks) {
    total.set(c, pos);
    pos += c.length;
  }
  return { sections, buffer: total.buffer };
}

export async function sha256Hex(buffer: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Mocks the global fetch to serve `buffer` for any request whose URL ends
 * with `binaryPath`, and throw for anything else. */
export function mockFetchServing(binaryPath: string, buffer: ArrayBuffer): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL) => {
      const href = typeof input === "string" ? input : input.href;
      if (href.endsWith(binaryPath)) {
        return {
          ok: true,
          status: 200,
          arrayBuffer: async () => buffer,
        } as unknown as Response;
      }
      throw new Error(`unexpected fetch in test: ${href}`);
    }),
  );
}
