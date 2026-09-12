// Shared, reusable loader for the compact binary interactive-data format
// (WP15 §3). Replaces large numeric-array JSON payloads with a small
// versioned JSON manifest (validated like any other activity data, via zod)
// plus one deterministic binary file, fetched with `fetch(...).arrayBuffer()`
// and decoded into typed arrays -- never eval, never innerHTML.
//
// Python encoder: scripts/binary_asset.py (keep both in sync: dtypes,
// 4-byte alignment, little-endian). Activity-specific reconstruction (e.g.
// expanding a neighbour-index matrix back into a logical target-value
// matrix) lives in each activity's own *-data.ts, on top of this module.

import { z } from "zod";
import { resolveDataUrl } from "./urls";

const IDENTIFIER_TOKEN = /(^|_)(id|ids|uid|sub|subject|participant|site|mrn|name|dob)($|_)/i;

export const BINARY_DTYPES = ["float32", "uint16"] as const;
export type BinaryDtype = (typeof BINARY_DTYPES)[number];

const ELEMENT_SIZE: Record<BinaryDtype, number> = { float32: 4, uint16: 2 };

export const binarySectionSchema = z
  .object({
    dtype: z.enum(BINARY_DTYPES),
    shape: z.array(z.number().int().nonnegative()).min(1),
    byteOffset: z.number().int().nonnegative(),
    byteLength: z.number().int().nonnegative(),
  })
  .strict();

export type BinarySection = z.infer<typeof binarySectionSchema>;

export const binaryManifestBaseSchema = z
  .object({
    schemaVersion: z.number().int().positive(),
    activity: z.string().min(1),
    binary: z
      .object({
        path: z.string().min(1),
        byteLength: z.number().int().nonnegative(),
        sha256: z.string().regex(/^[0-9a-f]{64}$/i, "sha256 must be a 64-character hex digest"),
      })
      .passthrough(),
    sections: z.record(binarySectionSchema),
  })
  .passthrough();

export type BinaryManifestBase = z.infer<typeof binaryManifestBaseSchema>;
export type DecodedSection = Float32Array | Uint16Array;

// Avoid duplicate network fetches of the same binary file on one page (e.g.
// a re-render, or two activities that -- in principle -- shared a payload).
const bufferCache = new Map<string, Promise<ArrayBuffer>>();

async function fetchArrayBuffer(url: URL): Promise<ArrayBuffer> {
  const key = url.href;
  let pending = bufferCache.get(key);
  if (!pending) {
    pending = (async () => {
      const res = await fetch(url.href, { credentials: "omit", mode: "same-origin" });
      if (!res.ok) throw new Error(`HTTP ${res.status} for ${url.href}`);
      return res.arrayBuffer();
    })();
    bufferCache.set(key, pending);
  }
  return pending;
}

/** Exposed for tests only -- do not call from application code. */
export function _clearBufferCacheForTests(): void {
  bufferCache.clear();
}

async function sha256Hex(buffer: ArrayBuffer): Promise<string | null> {
  const subtle = typeof crypto !== "undefined" ? crypto.subtle : undefined;
  if (!subtle || typeof subtle.digest !== "function") return null; // no secure-context SubtleCrypto available
  const digest = await subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// TypedArray views always use the host platform's native byte order. Every
// browser engine in practice is little-endian, but this loader is written to
// be CORRECT on a (today, essentially nonexistent) big-endian host too: it
// feature-detects platform endianness once and falls back to an explicit
// little-endian DataView decode rather than silently mis-reading bytes.
const PLATFORM_IS_LITTLE_ENDIAN = new Uint16Array(new Uint8Array([1, 0]).buffer)[0] === 1;

function decodeSection(buffer: ArrayBuffer, name: string, section: BinarySection): DecodedSection {
  const itemSize = ELEMENT_SIZE[section.dtype];
  if (section.byteOffset % itemSize !== 0) {
    throw new Error(`section "${name}": byteOffset ${section.byteOffset} is not aligned to its ${section.dtype} element size`);
  }
  if (section.byteLength % itemSize !== 0) {
    throw new Error(`section "${name}": byteLength ${section.byteLength} is not a multiple of its ${section.dtype} element size`);
  }
  if (section.byteOffset + section.byteLength > buffer.byteLength) {
    throw new Error(`section "${name}": extends past the end of the binary file`);
  }
  const count = section.byteLength / itemSize;
  const expectedCount = section.shape.reduce((a, b) => a * b, 1);
  if (count !== expectedCount) {
    throw new Error(
      `section "${name}": byteLength implies ${count} element(s) but shape [${section.shape.join(",")}] implies ${expectedCount}`,
    );
  }

  if (PLATFORM_IS_LITTLE_ENDIAN) {
    return section.dtype === "float32"
      ? new Float32Array(buffer, section.byteOffset, count)
      : new Uint16Array(buffer, section.byteOffset, count);
  }
  const view = new DataView(buffer, section.byteOffset, section.byteLength);
  if (section.dtype === "float32") {
    const out = new Float32Array(count);
    for (let i = 0; i < count; i += 1) out[i] = view.getFloat32(i * 4, true);
    return out;
  }
  const out = new Uint16Array(count);
  for (let i = 0; i < count; i += 1) out[i] = view.getUint16(i * 2, true);
  return out;
}

export interface LoadedBinaryAsset<M extends BinaryManifestBase> {
  manifest: M;
  sections: Record<string, DecodedSection>;
}

export type LoadResult<M extends BinaryManifestBase> =
  | { ok: true; value: LoadedBinaryAsset<M> }
  | { ok: false; error: string };

function formatZodError(prefix: string, error: z.ZodError): string {
  const msg = error.issues
    .map((i) => {
      const p = i.path.join(".");
      return p ? `${p}: ${i.message}` : i.message;
    })
    .join("; ");
  return `${prefix}: ${msg}`;
}

/**
 * Validate a manifest against `manifestSchema`, fetch + validate its sibling
 * binary payload (byte length, and a SHA-256 digest when SubtleCrypto is
 * available), and decode every declared section into a typed array. Returns
 * a clear, student-friendly error string on any failure -- never throws.
 */
export async function loadBinaryAsset<M extends BinaryManifestBase>(
  manifestJson: unknown,
  manifestSchema: z.ZodType<M>,
  manifestUrl: URL,
): Promise<LoadResult<M>> {
  const parsed = manifestSchema.safeParse(manifestJson);
  if (!parsed.success) {
    return { ok: false, error: formatZodError("Invalid activity manifest", parsed.error) };
  }
  const manifest = parsed.data;

  for (const key of Object.keys(manifest)) {
    if (IDENTIFIER_TOKEN.test(key)) {
      return { ok: false, error: `identifier-shaped top-level key "${key}" is not allowed` };
    }
  }
  for (const key of Object.keys(manifest.sections)) {
    if (IDENTIFIER_TOKEN.test(key)) {
      return { ok: false, error: `identifier-shaped section name "${key}" is not allowed` };
    }
  }

  const binaryUrlResult = resolveDataUrl(manifestUrl.href, manifest.binary.path);
  if (!binaryUrlResult.ok) {
    return { ok: false, error: `Activity data file path is not safe to load: ${binaryUrlResult.error}` };
  }

  let buffer: ArrayBuffer;
  try {
    buffer = await fetchArrayBuffer(binaryUrlResult.url);
  } catch (e) {
    return { ok: false, error: `Could not load this activity's data file: ${(e as Error).message}` };
  }

  if (buffer.byteLength !== manifest.binary.byteLength) {
    return {
      ok: false,
      error:
        `This activity's data file looks incomplete or out of date ` +
        `(expected ${manifest.binary.byteLength} bytes, got ${buffer.byteLength}). Try reloading the page.`,
    };
  }

  const digest = await sha256Hex(buffer);
  if (digest !== null && digest.toLowerCase() !== manifest.binary.sha256.toLowerCase()) {
    return {
      ok: false,
      error: "This activity's data file failed an integrity check. Try reloading the page.",
    };
  }

  const sections: Record<string, DecodedSection> = {};
  try {
    for (const [name, section] of Object.entries(manifest.sections)) {
      sections[name] = decodeSection(buffer, name, section);
    }
  } catch (e) {
    return { ok: false, error: `This activity's data file is malformed: ${(e as Error).message}` };
  }

  return { ok: true, value: { manifest, sections } };
}
