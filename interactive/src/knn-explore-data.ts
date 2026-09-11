// Zod schema + parser for the Exercise 3 "vary k" activity artifact
// (book/_static/widgets/data/abide_knn_explore.json, produced by
// scripts/export_knn_explore_data.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// The artifact stores, for a fixed fitting/validation split of the ABIDE-II
// age-prediction training partition: the per-k fitting/validation R2 and MSE
// curve for every integer k from 1 through n_fit, and -- for every validation
// participant -- the fitting-set target values reordered by distance (nearest
// first). The component derives the observed-vs-predicted scatter for any
// chosen k from that reordered array with one client-side prefix mean; no
// brain feature, distance, or participant identifier is ever shipped.

import { z } from "zod";
import type { DataResult } from "./components/types";

const IDENTIFIER_TOKEN = /(^|_)(id|ids|uid|sub|subject|participant|site|mrn|name|dob)($|_)/i;

const curveSchema = z
  .object({
    k: z.array(z.number().int().positive()).min(1),
    fitR2: z.array(z.number().finite()).min(1),
    fitMSE: z.array(z.number().finite().nonnegative()).min(1),
    valR2: z.array(z.number().finite()).min(1),
    valMSE: z.array(z.number().finite().nonnegative()).min(1),
  })
  .passthrough();

const trainingSampleSchema = z
  .object({
    fitTargetMean: z.number().finite(),
    neighborTargetsByProximity: z.array(z.array(z.number().finite())).min(1),
  })
  .passthrough();

export const knnExploreDataSchema = z
  .object({
    schemaVersion: z.literal(2),
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
    validationOptimalK: z.number().int().positive(),
    selectedKFromAudit: z.number().int().positive(),
    observedValidation: z.array(z.number().finite()).min(1),
    observedFitting: z.array(z.number().finite()).min(1),
    neighborTargetsByProximity: z.array(z.array(z.number().finite())).min(1),
    trainingSamples: z
      .object({ A: trainingSampleSchema, B: trainingSampleSchema, C: trainingSampleSchema })
      .strict(),
    curve: curveSchema,
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    for (const key of Object.keys(data)) {
      if (IDENTIFIER_TOKEN.test(key)) add([key], `identifier-shaped top-level key "${key}" is not allowed`);
    }

    const { nFit, nValidation } = data.split;
    if (data.observedValidation.length !== nValidation) {
      add(["observedValidation"], `expected ${nValidation} values, got ${data.observedValidation.length}`);
    }
    if (data.observedFitting.length !== nFit) {
      add(["observedFitting"], `expected ${nFit} values, got ${data.observedFitting.length}`);
    }
    if (data.neighborTargetsByProximity.length !== nValidation) {
      add(
        ["neighborTargetsByProximity"],
        `expected ${nValidation} rows (one per validation participant), got ` +
          `${data.neighborTargetsByProximity.length}`,
      );
    }
    for (let i = 0; i < data.neighborTargetsByProximity.length; i += 1) {
      const row = data.neighborTargetsByProximity[i]!;
      if (row.length !== nFit) {
        add(["neighborTargetsByProximity", i], `row must have ${nFit} entries, got ${row.length}`);
        break;
      }
    }

    for (const label of ["A", "B", "C"] as const) {
      const sample = data.trainingSamples[label];
      if (sample.neighborTargetsByProximity.length !== nValidation) {
        add(
          ["trainingSamples", label, "neighborTargetsByProximity"],
          `expected ${nValidation} rows, got ${sample.neighborTargetsByProximity.length}`,
        );
      }
      for (let i = 0; i < sample.neighborTargetsByProximity.length; i += 1) {
        const row = sample.neighborTargetsByProximity[i]!;
        if (row.length !== nFit) {
          add(["trainingSamples", label, "neighborTargetsByProximity", i], `row must have ${nFit} entries, got ${row.length}`);
          break;
        }
      }
    }
    if (
      JSON.stringify(data.trainingSamples.A.neighborTargetsByProximity) !==
      JSON.stringify(data.neighborTargetsByProximity)
    ) {
      add(["trainingSamples", "A"], "trainingSamples.A must equal the top-level neighborTargetsByProximity");
    }

    const { k, fitR2, fitMSE, valR2, valMSE } = data.curve;
    const expectedK = Array.from({ length: nFit }, (_, i) => i + 1);
    if (k.length !== nFit || k.some((v, i) => v !== expectedK[i])) {
      add(["curve", "k"], `curve.k must be exactly [1, 2, ..., ${nFit}]`);
    }
    for (const [name, arr] of [
      ["fitR2", fitR2],
      ["fitMSE", fitMSE],
      ["valR2", valR2],
      ["valMSE", valMSE],
    ] as const) {
      if (arr.length !== nFit) add(["curve", name], `must have ${nFit} entries, got ${arr.length}`);
    }

    if (fitR2.length > 0 && Math.abs(fitR2[0]! - 1) > 1e-6) {
      add(["curve", "fitR2", 0], "fitR2 at k=1 must be (numerically) 1.0 -- perfect resubstitution");
    }
    if (fitR2.length > 0 && Math.abs(fitR2[fitR2.length - 1]!) > 1e-3) {
      add(["curve", "fitR2"], "fitR2 at k=n_fit must be (numerically) ~0.0 -- the constant-mean predictor");
    }

    if (
      data.validationOptimalK < 1 ||
      data.validationOptimalK > nFit ||
      data.selectedKFromAudit < 1 ||
      data.selectedKFromAudit > nFit
    ) {
      add(["validationOptimalK"], "validationOptimalK and selectedKFromAudit must be within [1, n_fit]");
    }
  });

export type KnnExploreData = z.infer<typeof knnExploreDataSchema>;

export function parseKnnExploreData(raw: unknown): DataResult<KnnExploreData> {
  const parsed = knnExploreDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid KNN explore data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
