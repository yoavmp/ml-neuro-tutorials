// Loader for the Exercise 10 class-balance comparison artifact
// (book/_static/widgets/data/abide_class_balance_compare.json, produced by
// scripts/export_class_balance_compare_data.py). DOM / Plotly free so it can
// be unit tested independently of the rendering component.
//
// WP38R sec 5: replaces the removed imbalance-threshold activity. Compares
// ordinary vs class_weight="balanced" logistic regression across five
// progressively more imbalanced control:autism cohorts (50:50 through
// 90:10) at a FIXED decision threshold of 0.5 -- every metric here is
// precomputed offline from real fitted models' `.predict()` output; there is
// no predicted-probability array and no threshold field anywhere in this
// artifact (contrast with the removed schema).

import { z } from "zod";
import type { DataResult } from "./components/types";

const EXPECTED_RATIO_KEYS = ["50:50", "60:40", "70:30", "80:20", "90:10"] as const;

const confusionSchema = z
  .object({
    tn: z.number().int().nonnegative(),
    fp: z.number().int().nonnegative(),
    fn: z.number().int().nonnegative(),
    tp: z.number().int().nonnegative(),
  })
  .strict();

// precision/f1/balancedAccuracy can be genuinely undefined (e.g. a model that
// never predicts the positive class has tp+fp==0, so precision is undefined)
// -- the exporter ships an explicit JSON null rather than crashing or
// fabricating a number.
const modelResultSchema = z
  .object({
    confusionMatrix: confusionSchema,
    accuracy: z.number().min(0).max(1),
    majorityBaselineAccuracy: z.number().min(0).max(1),
    balancedAccuracy: z.number().min(0).max(1).nullable(),
    recall: z.number().min(0).max(1).nullable(),
    precision: z.number().min(0).max(1).nullable(),
    f1: z.number().min(0).max(1).nullable(),
    rocAuc: z.number().min(0).max(1),
    prAuc: z.number().min(0).max(1),
    prAucBaseline: z.number().min(0).max(1),
  })
  .strict();

const entrySchema = z
  .object({
    ratioKey: z.string().min(1),
    cohort: z
      .object({
        n: z.number().int().positive(),
        nMajority: z.number().int().positive(),
        nMinority: z.number().int().positive(),
      })
      .strict(),
    nTrainMajority: z.number().int().nonnegative(),
    nTrainMinority: z.number().int().nonnegative(),
    nTestMajority: z.number().int().nonnegative(),
    nTestMinority: z.number().int().nonnegative(),
    models: z
      .object({
        ordinary: modelResultSchema,
        classWeighted: modelResultSchema,
      })
      .strict(),
  })
  .strict();

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
    activity: z.literal("class-balance-compare"),
    source: z
      .object({ pinnedCommit: z.string().min(1), brainTableSha256: z.string().min(1) })
      .passthrough(),
    majorityClass: z.string().min(1),
    minorityClass: z.string().min(1),
    cohortSize: z.number().int().positive(),
    splitSeed: z.number().int(),
    modelC: z.number().positive(),
    ratios: z.array(ratioSchema).length(5),
    modelOrdinary: z.string().min(1),
    modelClassWeighted: z.string().min(1),
    entries: z.array(entrySchema).length(5),
  })
  .passthrough();

export type ClassBalanceCompareData = z.infer<typeof schema>;
export type ClassBalanceCompareEntry = z.infer<typeof entrySchema>;
export type ClassBalanceCompareModelResult = z.infer<typeof modelResultSchema>;
export type ClassBalanceCompareModelKey = "ordinary" | "classWeighted";

export function parseClassBalanceCompareData(raw: unknown): DataResult<ClassBalanceCompareData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid class-balance-compare data: ${msg}` };
  }
  const data = parsed.data;

  const ratioKeys = data.ratios.map((r) => r.key);
  if (ratioKeys.join(",") !== EXPECTED_RATIO_KEYS.join(",")) {
    return {
      ok: false,
      error:
        `Invalid class-balance-compare data: ratios must be exactly ` +
        `${EXPECTED_RATIO_KEYS.join(", ")} in order, got ${ratioKeys.join(", ")}`,
    };
  }
  if (ratioKeys.includes("95:5")) {
    return {
      ok: false,
      error: "Invalid class-balance-compare data: ratios must not include 95:5 (exactly five balance levels)",
    };
  }

  const entryKeys = new Set(data.entries.map((e) => e.ratioKey));
  if (entryKeys.size !== EXPECTED_RATIO_KEYS.length || ![...EXPECTED_RATIO_KEYS].every((k) => entryKeys.has(k))) {
    return {
      ok: false,
      error: "Invalid class-balance-compare data: entries do not cover exactly the five expected ratio keys",
    };
  }

  for (const entry of data.entries) {
    if (entry.cohort.nMajority + entry.cohort.nMinority !== entry.cohort.n) {
      return {
        ok: false,
        error: `Invalid class-balance-compare data: entry ${entry.ratioKey} cohort majority+minority does not sum to n`,
      };
    }
    if (entry.nTrainMajority + entry.nTestMajority !== entry.cohort.nMajority) {
      return {
        ok: false,
        error: `Invalid class-balance-compare data: entry ${entry.ratioKey} nTrainMajority+nTestMajority does not equal cohort.nMajority`,
      };
    }
    if (entry.nTrainMinority + entry.nTestMinority !== entry.cohort.nMinority) {
      return {
        ok: false,
        error: `Invalid class-balance-compare data: entry ${entry.ratioKey} nTrainMinority+nTestMinority does not equal cohort.nMinority`,
      };
    }
    const nTest = entry.nTestMajority + entry.nTestMinority;
    for (const key of ["ordinary", "classWeighted"] as const) {
      const cm = entry.models[key].confusionMatrix;
      const cmTotal = cm.tn + cm.fp + cm.fn + cm.tp;
      if (cmTotal !== nTest) {
        return {
          ok: false,
          error:
            `Invalid class-balance-compare data: entry ${entry.ratioKey}/${key} confusion matrix total ` +
            `(${cmTotal}) disagrees with nTestMajority+nTestMinority (${nTest})`,
        };
      }
    }
    const o = entry.models.ordinary;
    const w = entry.models.classWeighted;
    if (o.majorityBaselineAccuracy !== w.majorityBaselineAccuracy) {
      return {
        ok: false,
        error: `Invalid class-balance-compare data: entry ${entry.ratioKey} majorityBaselineAccuracy differs between models`,
      };
    }
    if (o.prAucBaseline !== w.prAucBaseline) {
      return {
        ok: false,
        error: `Invalid class-balance-compare data: entry ${entry.ratioKey} prAucBaseline differs between models`,
      };
    }
  }

  return { ok: true, data };
}

export function findEntry(data: ClassBalanceCompareData, ratioKey: string): ClassBalanceCompareEntry {
  const entry = data.entries.find((e) => e.ratioKey === ratioKey);
  if (!entry) {
    throw new Error(`No entry for ratio "${ratioKey}"`);
  }
  return entry;
}
