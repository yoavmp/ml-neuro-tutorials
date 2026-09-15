// Loader for the Exercise 4 class-imbalance / stratified-split interactive
// artifact (book/_static/widgets/data/abide_classification_imbalance.json,
// produced by scripts/export_classification_imbalance_data.py). Ships only
// aggregated counts and metrics per (ratio, seed, split-kind) -- no brain
// features, no participant identifiers, no raw probabilities. DOM / Plotly
// free so it can be unit tested independently of the rendering component.

import { z } from "zod";
import type { DataResult } from "./components/types";

const confusionSchema = z
  .object({
    tn: z.number().int().nonnegative(),
    fp: z.number().int().nonnegative(),
    fn: z.number().int().nonnegative(),
    tp: z.number().int().nonnegative(),
  })
  .strict();

const sideSchema = z
  .object({
    nTrainMajority: z.number().int().nonnegative(),
    nTrainMinority: z.number().int().nonnegative(),
    nTestMajority: z.number().int().nonnegative(),
    nTestMinority: z.number().int().nonnegative(),
    confusionMatrix: confusionSchema,
    accuracy: z.number().min(0).max(1),
    auc: z.number().min(0).max(1).nullable(),
    majorityBaselineAccuracy: z.number().min(0).max(1),
  })
  .passthrough();

const entrySchema = z
  .object({
    ratioKey: z.string().min(1),
    seed: z.number().int(),
    cohort: z
      .object({
        n: z.number().int().positive(),
        nMajority: z.number().int().positive(),
        nMinority: z.number().int().positive(),
      })
      .passthrough(),
    stratified: sideSchema,
    unstratified: sideSchema,
  })
  .passthrough();

const ratioSchema = z
  .object({
    key: z.string().min(1),
    majorityPct: z.number().min(0).max(1),
    minorityPct: z.number().min(0).max(1),
  })
  .passthrough();

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("classification-imbalance"),
    source: z
      .object({ pinnedCommit: z.string().min(1), brainTableSha256: z.string().min(1) })
      .passthrough(),
    majorityClass: z.string().min(1),
    minorityClass: z.string().min(1),
    cohortSize: z.number().int().positive(),
    ratios: z.array(ratioSchema).min(1),
    splitSeeds: z.array(z.number().int()).min(1),
    model: z.string().min(1),
    entries: z.array(entrySchema).min(1),
  })
  .passthrough();

export type ClassificationImbalanceData = z.infer<typeof schema>;
export type ClassificationImbalanceEntry = z.infer<typeof entrySchema>;
export type ClassificationImbalanceSide = z.infer<typeof sideSchema>;

export function parseClassificationImbalanceData(raw: unknown): DataResult<ClassificationImbalanceData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    return {
      ok: false,
      error: `Invalid classification imbalance data: ${parsed.error.issues.map((i) => i.message).join("; ")}`,
    };
  }
  const data = parsed.data;
  const expectedPairs = new Set(data.ratios.flatMap((r) => data.splitSeeds.map((s) => `${r.key}::${s}`)));
  const seenPairs = new Set(data.entries.map((e) => `${e.ratioKey}::${e.seed}`));
  const missingOrExtra =
    expectedPairs.size !== seenPairs.size || [...expectedPairs].some((p) => !seenPairs.has(p));
  if (missingOrExtra) {
    return {
      ok: false,
      error: "Invalid classification imbalance data: entries do not cover every (ratio, seed) combination exactly once",
    };
  }
  return { ok: true, data };
}

export function findEntry(
  data: ClassificationImbalanceData,
  ratioKey: string,
  seed: number,
): ClassificationImbalanceEntry {
  const entry = data.entries.find((e) => e.ratioKey === ratioKey && e.seed === seed);
  if (!entry) {
    throw new Error(`No entry for ratio "${ratioKey}" seed ${seed}`);
  }
  return entry;
}
