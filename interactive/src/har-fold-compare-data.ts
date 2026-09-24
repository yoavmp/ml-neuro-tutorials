// Loader for the Exercise 10 HAR fold-comparison artifact
// (book/_static/widgets/data/uci_har_fold_comparison.json). DOM / Plotly free
// so it can be unit tested independently of the rendering component.
//
// Every k's per-fold accuracy/macro-F1/confusion matrix, for both ordinary
// (random-window) and participant-grouped 5-fold cross-validation, is
// precomputed offline; nothing is refit in the browser. `participantFolds`
// records, per participant, every ordinary fold their windows land in
// (`ordinaryFolds`, often more than one) and their single grouped fold
// (`groupedFold`) -- the component uses these to draw the participant/fold
// assignment diagram and to count participants split across the selected
// fold under ordinary splitting.

import { z } from "zod";
import type { DataResult } from "./components/types";

const NUM_ACTIVITIES = 6;

const foldMetricsSchema = z
  .object({
    accPerFold: z.array(z.number().min(0).max(1)).min(1),
    f1PerFold: z.array(z.number().min(0).max(1)).min(1),
    confusionPerFold: z
      .array(z.array(z.array(z.number().int().nonnegative())).min(1))
      .min(1),
    accMean: z.number().min(0).max(1),
    f1Mean: z.number().min(0).max(1),
  })
  .strict();

const kResultSchema = z
  .object({
    k: z.number().int().positive(),
    ordinary: foldMetricsSchema,
    grouped: foldMetricsSchema,
    accGap: z.number(),
    f1Gap: z.number(),
  })
  .strict();

const participantFoldSchema = z
  .object({
    participantId: z.number().int().positive(),
    ordinaryFolds: z.array(z.number().int().nonnegative()).min(1),
    groupedFold: z.number().int().nonnegative(),
    nObservations: z.number().int().positive(),
  })
  .strict();

const observationsPerParticipantSchema = z
  .object({
    min: z.number().int().nonnegative(),
    max: z.number().int().nonnegative(),
    mean: z.number().nonnegative(),
    median: z.number().nonnegative(),
  })
  .strict();

const sourceSchema = z
  .object({
    sourceUrl: z.string().min(1),
    doi: z.string().min(1),
    license: z.string().min(1),
  })
  .passthrough();

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("har-fold-compare"),
    activityLabels: z.record(z.string().min(1)),
    kValues: z.array(z.number().int().positive()).min(1),
    nSplits: z.number().int().positive(),
    nRows: z.number().int().positive(),
    nParticipants: z.number().int().positive(),
    observationsPerParticipant: observationsPerParticipantSchema,
    kResults: z.array(kResultSchema).min(1),
    participantFolds: z.array(participantFoldSchema).min(1),
    source: sourceSchema,
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const activityIds = Object.keys(data.activityLabels)
      .map(Number)
      .sort((a, b) => a - b);
    if (activityIds.length !== NUM_ACTIVITIES) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["activityLabels"],
        message: `activityLabels must declare exactly ${NUM_ACTIVITIES} activities, found ${activityIds.length}`,
      });
    }

    const kSet = data.kValues;
    const resultKs = data.kResults.map((r) => r.k);
    const dupKs = resultKs.filter((k, i) => resultKs.indexOf(k) !== i);
    if (dupKs.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["kResults"],
        message: `duplicate k value(s) in kResults: ${[...new Set(dupKs)].join(", ")}`,
      });
    }
    if (resultKs.length !== kSet.length || !kSet.every((k) => resultKs.includes(k))) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["kResults"],
        message: `kResults k values ${JSON.stringify(resultKs)} do not match kValues ${JSON.stringify(kSet)}`,
      });
    }

    for (const [i, result] of data.kResults.entries()) {
      for (const side of ["ordinary", "grouped"] as const) {
        const metrics = result[side];
        if (metrics.accPerFold.length !== data.nSplits) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["kResults", i, side, "accPerFold"],
            message: `expected ${data.nSplits} folds, got ${metrics.accPerFold.length}`,
          });
        }
        if (metrics.f1PerFold.length !== data.nSplits) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["kResults", i, side, "f1PerFold"],
            message: `expected ${data.nSplits} folds, got ${metrics.f1PerFold.length}`,
          });
        }
        if (metrics.confusionPerFold.length !== data.nSplits) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["kResults", i, side, "confusionPerFold"],
            message: `expected ${data.nSplits} confusion matrices, got ${metrics.confusionPerFold.length}`,
          });
        }
        for (const [f, matrix] of metrics.confusionPerFold.entries()) {
          if (matrix.length !== NUM_ACTIVITIES || matrix.some((row) => row.length !== NUM_ACTIVITIES)) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              path: ["kResults", i, side, "confusionPerFold", f],
              message: `confusion matrix must be ${NUM_ACTIVITIES}x${NUM_ACTIVITIES}`,
            });
          }
        }
      }
    }

    if (data.participantFolds.length !== data.nParticipants) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["participantFolds"],
        message: `expected ${data.nParticipants} participants, got ${data.participantFolds.length}`,
      });
    }
    for (const [i, p] of data.participantFolds.entries()) {
      if (p.groupedFold >= data.nSplits) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["participantFolds", i, "groupedFold"],
          message: `groupedFold ${p.groupedFold} is out of range for ${data.nSplits} splits`,
        });
      }
      if (p.ordinaryFolds.some((f) => f >= data.nSplits)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["participantFolds", i, "ordinaryFolds"],
          message: `ordinaryFolds contains an out-of-range fold for ${data.nSplits} splits`,
        });
      }
    }
  });

export type HarFoldCompareData = z.infer<typeof schema>;
export type HarKResult = z.infer<typeof kResultSchema>;
export type HarFoldMetrics = z.infer<typeof foldMetricsSchema>;
export type HarParticipantFold = z.infer<typeof participantFoldSchema>;
export type HarSplitMethod = "ordinary" | "grouped";

export function parseHarFoldCompareData(raw: unknown): DataResult<HarFoldCompareData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid HAR fold comparison data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}

export function findKResult(data: HarFoldCompareData, k: number): HarKResult {
  const result = data.kResults.find((r) => r.k === k);
  if (!result) throw new Error(`No kResults entry for k=${k}`);
  return result;
}

export function sortedActivityIds(data: HarFoldCompareData): number[] {
  return Object.keys(data.activityLabels)
    .map(Number)
    .sort((a, b) => a - b);
}

/** Participants whose selected-fold membership makes them "split" under the
 * given method: for ordinary, in the selected fold AND appearing in more than
 * one fold overall; for grouped, always none (each participant has exactly
 * one fold). */
export function participantsSplitAcrossFold(
  data: HarFoldCompareData,
  method: HarSplitMethod,
  fold: number,
): number {
  if (method === "grouped") return 0;
  return data.participantFolds.filter(
    (p) => p.ordinaryFolds.includes(fold) && p.ordinaryFolds.length > 1,
  ).length;
}
