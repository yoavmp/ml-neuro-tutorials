// Loader for the Exercise 10 imbalance-threshold artifact
// (book/_static/widgets/data/abide_imbalance_threshold.json). DOM / Plotly
// free so it can be unit tested independently of the rendering component.
//
// A fixed 90:10 control:autism test cohort with FIXED predicted probabilities
// from two already-fit models (ordinary logistic regression and
// class_weight="balanced" logistic regression). The component recomputes the
// confusion matrix and every threshold-dependent metric client-side by
// thresholding these probabilities against `testLabels` -- it never refits
// a model. ROC-AUC and PR-AUC are threshold-independent and read directly
// from the artifact.

import { z } from "zod";
import type { DataResult } from "./components/types";

const modelResultSchema = z
  .object({
    model: z.string().min(1),
    predictedProbaPositive: z.array(z.number().min(0).max(1)).min(1),
    rocAuc: z.number().min(0).max(1),
    prAuc: z.number().min(0).max(1),
  })
  .strict();

const cohortSchema = z
  .object({
    n: z.number().int().positive(),
    nMajority: z.number().int().positive(),
    nMinority: z.number().int().positive(),
  })
  .strict();

const sourceSchema = z
  .object({
    pinnedCommit: z.string().min(1),
    brainTableSha256: z.string().min(1),
  })
  .passthrough();

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("imbalance-threshold"),
    source: sourceSchema,
    cohort: cohortSchema,
    majorityClass: z.string().min(1),
    minorityClass: z.string().min(1),
    ratioKey: z.string().min(1),
    splitSeed: z.number().int(),
    nTestMajority: z.number().int().positive(),
    nTestMinority: z.number().int().positive(),
    positivePrevalence: z.number().min(0).max(1),
    majorityBaselineAccuracy: z.number().min(0).max(1),
    modelC: z.number().positive(),
    testLabels: z.array(z.union([z.literal(0), z.literal(1)])).min(1),
    models: z
      .object({
        ordinary: modelResultSchema,
        classWeighted: modelResultSchema,
      })
      .strict(),
  })
  .passthrough();

export type ImbalanceThresholdData = z.infer<typeof schema>;
export type ImbalanceThresholdModelKey = "ordinary" | "classWeighted";
export type ImbalanceThresholdModelResult = z.infer<typeof modelResultSchema>;

export function parseImbalanceThresholdData(raw: unknown): DataResult<ImbalanceThresholdData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid imbalance-threshold data: ${msg}` };
  }
  const data = parsed.data;

  const nTest = data.nTestMajority + data.nTestMinority;
  if (data.testLabels.length !== nTest) {
    return {
      ok: false,
      error: `Invalid imbalance-threshold data: testLabels has ${data.testLabels.length} entries, expected nTestMajority + nTestMinority (${nTest})`,
    };
  }
  for (const key of ["ordinary", "classWeighted"] as const) {
    const arr = data.models[key].predictedProbaPositive;
    if (arr.length !== nTest) {
      return {
        ok: false,
        error: `Invalid imbalance-threshold data: models.${key}.predictedProbaPositive has ${arr.length} entries, expected ${nTest}`,
      };
    }
  }
  const nPositiveLabels = data.testLabels.filter((l) => l === 1).length;
  if (nPositiveLabels !== data.nTestMinority) {
    return {
      ok: false,
      error: `Invalid imbalance-threshold data: testLabels has ${nPositiveLabels} positive (minority) labels, expected nTestMinority (${data.nTestMinority})`,
    };
  }

  return { ok: true, data };
}
