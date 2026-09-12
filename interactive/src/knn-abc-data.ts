// Loader for the Exercise 3 Section 3 "honest vs invalid" KNN interactive
// artifact (book/_static/widgets/data/abide_knn_abc_manifest.json +
// abide_knn_abc.bin, produced by scripts/export_knn_abc_data.py). DOM /
// Plotly free so it can be unit tested and reused independently of the
// rendering component.
//
// WP15 §3: the artifact is now a small JSON manifest plus one compact
// binary payload (scripts/binary_asset.py / binary-asset.ts), not one large
// JSON file of nested number arrays. For every query participant in each of
// three panels (A valid, B resubstitution, C invalid leakage), the binary
// stores a reference-pool row INDEX (nearest first, uint16), truncated to
// the shared valid k range 1..min(n_train, n_test); this module reconstructs
// each panel's reordered target-VALUE matrix (`number[][]`, unchanged shape
// and semantics from schema v1) by indexing into the small reference target
// arrays (`observedTrain`/`observedTest`, float32) once, in memory -- the
// component below is unaffected by the wire-format change. No brain
// feature, distance, or participant identifier is ever shipped.

import { z } from "zod";
import type { DataResult } from "./components/types";
import { binaryManifestBaseSchema, loadBinaryAsset } from "./binary-asset";

const knnAbcManifestSchema = binaryManifestBaseSchema.extend({
  schemaVersion: z.literal(2),
  activity: z.literal("knn-abc"),
  source: z
    .object({
      pinnedCommit: z.string().min(1),
      brainTableSha256: z.string().min(1),
      phenotypeTableSha256: z.string().min(1),
    })
    .passthrough(),
  target: z
    .object({
      name: z.string().min(1),
      label: z.string().min(1),
      unit: z.string().min(1),
    })
    .passthrough(),
  featureRecipe: z
    .object({
      bundle: z.string().min(1),
      measures: z.array(z.string().min(1)).min(1),
      featureCount: z.number().int().positive(),
    })
    .passthrough(),
  split: z
    .object({
      nTrain: z.number().int().positive(),
      nTest: z.number().int().positive(),
      kMax: z.number().int().positive(),
    })
    .passthrough(),
  selectedKFromAudit: z.number().int().positive(),
});

export interface KnnAbcData {
  schemaVersion: number;
  activity: "knn-abc";
  source: { pinnedCommit: string; brainTableSha256: string; phenotypeTableSha256: string };
  target: { name: string; label: string; unit: string };
  featureRecipe: { bundle: string; measures: string[]; featureCount: number };
  split: { nTrain: number; nTest: number; kMax: number };
  selectedKFromAudit: number;
  observedTrain: number[];
  observedTest: number[];
  neighborTargetsA: number[][];
  neighborTargetsB: number[][];
  neighborTargetsC: number[][];
}

function toRows(refTargets: Float32Array, index: Uint16Array, nRows: number, nCols: number, name: string): number[][] {
  const rows: number[][] = new Array(nRows);
  for (let i = 0; i < nRows; i += 1) {
    const row = new Array<number>(nCols);
    const base = i * nCols;
    for (let j = 0; j < nCols; j += 1) {
      const refIndex = index[base + j]!;
      if (refIndex < 0 || refIndex >= refTargets.length) {
        throw new Error(`${name}[${i}][${j}]: index ${refIndex} is out of bounds for a ${refTargets.length}-element reference array`);
      }
      row[j] = refTargets[refIndex]!;
    }
    rows[i] = row;
  }
  return rows;
}

function validateReconstructed(data: KnnAbcData): string | null {
  const { nTrain, nTest, kMax } = data.split;
  if (kMax !== Math.min(nTrain, nTest)) {
    return `split.kMax must equal min(nTrain, nTest) = ${Math.min(nTrain, nTest)}`;
  }
  if (data.observedTrain.length !== nTrain) return `observedTrain: expected ${nTrain} values, got ${data.observedTrain.length}`;
  if (data.observedTest.length !== nTest) return `observedTest: expected ${nTest} values, got ${data.observedTest.length}`;

  const panels: [string, number[][], number][] = [
    ["neighborTargetsA", data.neighborTargetsA, nTest],
    ["neighborTargetsB", data.neighborTargetsB, nTrain],
    ["neighborTargetsC", data.neighborTargetsC, nTest],
  ];
  for (const [name, rows, expectedRows] of panels) {
    if (rows.length !== expectedRows) return `${name}: expected ${expectedRows} rows, got ${rows.length}`;
    for (let i = 0; i < rows.length; i += 1) {
      if (rows[i]!.length !== kMax) return `${name}[${i}]: row must have kMax (${kMax}) entries, got ${rows[i]!.length}`;
    }
  }

  // k=1 structural endpoint: B and C are exact resubstitution.
  for (let i = 0; i < data.observedTrain.length; i += 1) {
    if (Math.abs(data.neighborTargetsB[i]![0]! - data.observedTrain[i]!) > 1e-3) {
      return `neighborTargetsB[${i}][0] (k=1) must equal observedTrain -- each training row is its own nearest neighbour`;
    }
  }
  for (let i = 0; i < data.observedTest.length; i += 1) {
    if (Math.abs(data.neighborTargetsC[i]![0]! - data.observedTest[i]!) > 1e-3) {
      return `neighborTargetsC[${i}][0] (k=1) must equal observedTest -- each test row is its own nearest neighbour`;
    }
  }

  if (data.selectedKFromAudit < 1 || data.selectedKFromAudit > kMax) {
    return `selectedKFromAudit must be within [1, ${kMax}]`;
  }
  return null;
}

export async function parseKnnAbcData(raw: unknown, dataUrl: URL): Promise<DataResult<KnnAbcData>> {
  const loaded = await loadBinaryAsset(raw, knnAbcManifestSchema, dataUrl);
  if (!loaded.ok) return { ok: false, error: `Invalid KNN A/B/C data: ${loaded.error}` };
  const { manifest, sections } = loaded.value;

  const required = ["observedTrain", "observedTest", "neighborIndexA", "neighborIndexB", "neighborIndexC"];
  for (const name of required) {
    if (!(name in sections)) return { ok: false, error: `Invalid KNN A/B/C data: missing binary section "${name}"` };
  }
  const observedTrainArr = sections.observedTrain as Float32Array;
  const observedTestArr = sections.observedTest as Float32Array;
  const { nTrain, nTest, kMax } = manifest.split;

  let data: KnnAbcData;
  try {
    data = {
      schemaVersion: manifest.schemaVersion,
      activity: "knn-abc",
      source: manifest.source,
      target: manifest.target,
      featureRecipe: manifest.featureRecipe,
      split: manifest.split,
      selectedKFromAudit: manifest.selectedKFromAudit,
      observedTrain: Array.from(observedTrainArr),
      observedTest: Array.from(observedTestArr),
      neighborTargetsA: toRows(observedTrainArr, sections.neighborIndexA as Uint16Array, nTest, kMax, "neighborTargetsA"),
      neighborTargetsB: toRows(observedTrainArr, sections.neighborIndexB as Uint16Array, nTrain, kMax, "neighborTargetsB"),
      neighborTargetsC: toRows(observedTestArr, sections.neighborIndexC as Uint16Array, nTest, kMax, "neighborTargetsC"),
    };
  } catch (e) {
    return { ok: false, error: `Invalid KNN A/B/C data: ${(e as Error).message}` };
  }

  const error = validateReconstructed(data);
  if (error) return { ok: false, error: `Invalid KNN A/B/C data: ${error}` };
  return { ok: true, data };
}
