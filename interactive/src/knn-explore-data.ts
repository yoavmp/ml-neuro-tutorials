// Loader for the Exercise 3 "vary k" activity artifact
// (book/_static/widgets/data/abide_knn_explore_manifest.json +
// abide_knn_explore.bin, produced by scripts/export_knn_explore_data.py).
// DOM / Plotly free so it can be unit tested and reused independently of the
// rendering component.
//
// WP15 §3: the artifact is now a small JSON manifest plus one compact
// binary payload (scripts/binary_asset.py / binary-asset.ts), not one large
// JSON file of nested number arrays. For every validation participant, the
// binary stores a fitting-set neighbour row INDEX (nearest first, uint16)
// rather than the reordered target VALUES directly, once per training
// sample (A/B/C); this module reconstructs each sample's reordered
// target-value matrix (`number[][]`, unchanged shape and semantics from
// schema v2) by indexing into that sample's own small target array
// (float32) once, in memory -- the component below is unaffected by the
// wire-format change. Sample A's index matrix also stands in for the old
// top-level "baseline" matrix (they were always identical; schema v3 never
// stores that duplicate in the first place). No brain feature, distance, or
// participant identifier is ever shipped.

import { z } from "zod";
import type { DataResult } from "./components/types";
import { binaryManifestBaseSchema, loadBinaryAsset } from "./binary-asset";

const knnExploreManifestSchema = binaryManifestBaseSchema.extend({
  schemaVersion: z.literal(3),
  activity: z.literal("knn-explore"),
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
      nOuterTrain: z.number().int().positive(),
      nFit: z.number().int().positive(),
      nValidation: z.number().int().positive(),
    })
    .passthrough(),
  fitTargetMean: z.number().finite(),
  trainingSampleMeans: z
    .object({ A: z.number().finite(), B: z.number().finite(), C: z.number().finite() })
    .strict(),
  validationOptimalK: z.number().int().positive(),
  selectedKFromAudit: z.number().int().positive(),
});

export interface KnnExploreTrainingSample {
  fitTargetMean: number;
  neighborTargetsByProximity: number[][];
}

export interface KnnExploreData {
  schemaVersion: number;
  activity: "knn-explore";
  source: { pinnedCommit: string; brainTableSha256: string; phenotypeTableSha256: string };
  target: { name: string; label: string; unit: string };
  featureRecipe: { bundle: string; measures: string[]; featureCount: number };
  split: { nOuterTrain: number; nFit: number; nValidation: number };
  fitTargetMean: number;
  validationOptimalK: number;
  selectedKFromAudit: number;
  observedValidation: number[];
  observedFitting: number[];
  neighborTargetsByProximity: number[][];
  trainingSamples: { A: KnnExploreTrainingSample; B: KnnExploreTrainingSample; C: KnnExploreTrainingSample };
  curve: { k: number[]; fitR2: number[]; fitMSE: number[]; valR2: number[]; valMSE: number[] };
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

function validateReconstructed(data: KnnExploreData): string | null {
  const { nFit, nValidation } = data.split;
  if (data.observedValidation.length !== nValidation) {
    return `observedValidation: expected ${nValidation} values, got ${data.observedValidation.length}`;
  }
  if (data.observedFitting.length !== nFit) {
    return `observedFitting: expected ${nFit} values, got ${data.observedFitting.length}`;
  }
  if (data.neighborTargetsByProximity.length !== nValidation) {
    return `neighborTargetsByProximity: expected ${nValidation} rows, got ${data.neighborTargetsByProximity.length}`;
  }

  for (const label of ["A", "B", "C"] as const) {
    const sample = data.trainingSamples[label];
    if (sample.neighborTargetsByProximity.length !== nValidation) {
      return `trainingSamples.${label}: expected ${nValidation} rows, got ${sample.neighborTargetsByProximity.length}`;
    }
    for (let i = 0; i < sample.neighborTargetsByProximity.length; i += 1) {
      if (sample.neighborTargetsByProximity[i]!.length !== nFit) {
        return `trainingSamples.${label}[${i}]: row must have ${nFit} entries`;
      }
    }
  }
  if (JSON.stringify(data.trainingSamples.A.neighborTargetsByProximity) !== JSON.stringify(data.neighborTargetsByProximity)) {
    return "trainingSamples.A must equal the top-level neighborTargetsByProximity";
  }

  const { k, fitR2, fitMSE, valR2, valMSE } = data.curve;
  for (const [name, arr] of [
    ["k", k],
    ["fitR2", fitR2],
    ["fitMSE", fitMSE],
    ["valR2", valR2],
    ["valMSE", valMSE],
  ] as const) {
    if (arr.length !== nFit) return `curve.${name}: must have ${nFit} entries, got ${arr.length}`;
  }
  if (fitR2.length > 0 && Math.abs(fitR2[0]! - 1) > 1e-2) {
    return "curve.fitR2 at k=1 must be (numerically) 1.0 -- perfect resubstitution";
  }
  if (fitR2.length > 0 && Math.abs(fitR2[fitR2.length - 1]!) > 1e-2) {
    return "curve.fitR2 at k=n_fit must be (numerically) ~0.0 -- the constant-mean predictor";
  }

  if (
    data.validationOptimalK < 1 ||
    data.validationOptimalK > nFit ||
    data.selectedKFromAudit < 1 ||
    data.selectedKFromAudit > nFit
  ) {
    return "validationOptimalK and selectedKFromAudit must be within [1, n_fit]";
  }
  return null;
}

export async function parseKnnExploreData(raw: unknown, dataUrl: URL): Promise<DataResult<KnnExploreData>> {
  const loaded = await loadBinaryAsset(raw, knnExploreManifestSchema, dataUrl);
  if (!loaded.ok) return { ok: false, error: `Invalid KNN explore data: ${loaded.error}` };
  const { manifest, sections } = loaded.value;

  const required = [
    "observedValidation", "observedFitting", "fitTargetsB", "fitTargetsC",
    "neighborIndexA", "neighborIndexB", "neighborIndexC",
    "curveFitR2", "curveFitMSE", "curveValR2", "curveValMSE",
  ];
  for (const name of required) {
    if (!(name in sections)) return { ok: false, error: `Invalid KNN explore data: missing binary section "${name}"` };
  }

  const observedFittingArr = sections.observedFitting as Float32Array;
  const fitTargetsB = sections.fitTargetsB as Float32Array;
  const fitTargetsC = sections.fitTargetsC as Float32Array;
  const { nFit, nValidation } = manifest.split;

  let data: KnnExploreData;
  try {
    const neighborTargetsByProximity = toRows(
      observedFittingArr,
      sections.neighborIndexA as Uint16Array,
      nValidation,
      nFit,
      "neighborTargetsByProximity",
    );
    data = {
      schemaVersion: manifest.schemaVersion,
      activity: "knn-explore",
      source: manifest.source,
      target: manifest.target,
      featureRecipe: manifest.featureRecipe,
      split: manifest.split,
      fitTargetMean: manifest.fitTargetMean,
      validationOptimalK: manifest.validationOptimalK,
      selectedKFromAudit: manifest.selectedKFromAudit,
      observedValidation: Array.from(sections.observedValidation as Float32Array),
      observedFitting: Array.from(observedFittingArr),
      neighborTargetsByProximity,
      trainingSamples: {
        A: { fitTargetMean: manifest.trainingSampleMeans.A, neighborTargetsByProximity },
        B: {
          fitTargetMean: manifest.trainingSampleMeans.B,
          neighborTargetsByProximity: toRows(fitTargetsB, sections.neighborIndexB as Uint16Array, nValidation, nFit, "trainingSamples.B"),
        },
        C: {
          fitTargetMean: manifest.trainingSampleMeans.C,
          neighborTargetsByProximity: toRows(fitTargetsC, sections.neighborIndexC as Uint16Array, nValidation, nFit, "trainingSamples.C"),
        },
      },
      curve: {
        k: Array.from({ length: nFit }, (_, i) => i + 1),
        fitR2: Array.from(sections.curveFitR2 as Float32Array),
        fitMSE: Array.from(sections.curveFitMSE as Float32Array),
        valR2: Array.from(sections.curveValR2 as Float32Array),
        valMSE: Array.from(sections.curveValMSE as Float32Array),
      },
    };
  } catch (e) {
    return { ok: false, error: `Invalid KNN explore data: ${(e as Error).message}` };
  }

  const error = validateReconstructed(data);
  if (error) return { ok: false, error: `Invalid KNN explore data: ${error}` };
  return { ok: true, data };
}
