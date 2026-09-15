// Loader for the Exercise 4 decision-threshold interactive artifact
// (book/_static/widgets/data/abide_classification_threshold.json, produced
// by scripts/export_classification_threshold_data.py). DOM / Plotly free so
// it can be unit tested independently of the rendering component. Small
// plain JSON (251 labels + 251 probabilities) -- no binary-asset format
// needed, unlike the KNN activities' larger per-k neighbour tables.

import { z } from "zod";
import type { DataResult } from "./components/types";

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("classification-threshold"),
    source: z
      .object({ pinnedCommit: z.string().min(1), brainTableSha256: z.string().min(1) })
      .passthrough(),
    positiveClass: z.string().min(1),
    negativeClass: z.string().min(1),
    featureRecipe: z
      .object({
        bundle: z.string().min(1),
        measures: z.array(z.string().min(1)).min(1),
        featureCount: z.number().int().positive(),
      })
      .passthrough(),
    split: z
      .object({
        testSize: z.number().positive(),
        randomState: z.number().int(),
        nTrain: z.number().int().positive(),
        nTest: z.number().int().positive(),
      })
      .passthrough(),
    model: z.string().min(1),
    aucFromAudit: z.number().min(0).max(1),
    accuracyAtHalfFromAudit: z.number().min(0).max(1),
    labels: z.array(z.union([z.literal(0), z.literal(1)])),
    probabilities: z.array(z.number().min(0).max(1)),
  })
  .passthrough();

export type ClassificationThresholdData = z.infer<typeof schema>;

export function parseClassificationThresholdData(raw: unknown): DataResult<ClassificationThresholdData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    return {
      ok: false,
      error: `Invalid classification threshold data: ${parsed.error.issues.map((i) => i.message).join("; ")}`,
    };
  }
  const data = parsed.data;
  if (data.labels.length !== data.split.nTest) {
    return {
      ok: false,
      error: `Invalid classification threshold data: labels has ${data.labels.length} entries, expected split.nTest (${data.split.nTest})`,
    };
  }
  if (data.probabilities.length !== data.split.nTest) {
    return {
      ok: false,
      error: `Invalid classification threshold data: probabilities has ${data.probabilities.length} entries, expected split.nTest (${data.split.nTest})`,
    };
  }
  const hasPositive = data.labels.some((l) => l === 1);
  const hasNegative = data.labels.some((l) => l === 0);
  if (!hasPositive || !hasNegative) {
    return { ok: false, error: "Invalid classification threshold data: labels must contain both classes" };
  }
  return { ok: true, data };
}
