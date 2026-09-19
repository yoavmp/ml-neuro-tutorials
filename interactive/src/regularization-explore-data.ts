// Zod schema + parser for the Exercise 5 "Shrink the Coefficients" activity
// data (book/_static/widgets/data/regularization_explore.json, produced by
// scripts/export_regularization_widget.py). DOM / Plotly free so it can be
// unit tested and reused independently of the rendering component.
//
// The artifact is a finite, precomputed set of (model, alpha) configurations
// on one fixed fitting/validation split (n_fit=564, n_val=189) -- the outer
// test set never appears here at all. This schema enforces that every
// per-alpha entry's arrays align with the shared observed/tracked-feature
// arrays, so a config can never silently reference a malformed artifact.

import { z } from "zod";
import type { DataResult } from "./components/types";

const splitPart = z
  .object({
    testSize: z.number().positive().lt(1),
    randomState: z.number().int(),
    stratify: z.string().min(1),
  })
  .passthrough();

const modelMetrics = z.object({
  trainMSE: z.number().finite().nonnegative(),
  valMSE: z.number().finite().nonnegative(),
  trainR2: z.number().finite(),
  valR2: z.number().finite(),
  nonzeroCount: z.number().int().nonnegative(),
  coefNorm: z.number().finite().nonnegative(),
  predictedValidation: z.array(z.number().finite()).min(1),
  coefficients: z.array(z.number().finite()).min(1),
});

const alphaModelEntry = z.object({
  alphaGrid: z.array(z.number().positive()).min(2),
  bestAlphaIndex: z.number().int().nonnegative(),
  perAlpha: z.array(modelMetrics).min(2),
});

export const regularizationExploreDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("regularization-explore"),
    source: z
      .object({
        pinnedCommit: z.string().min(1),
        brainTableSha256: z.string().min(1),
        phenotypeTableSha256: z.string().min(1),
      })
      .passthrough(),
    target: z.object({ name: z.string().min(1), label: z.string().min(1), unit: z.string().min(1) }).passthrough(),
    featureRecipe: z
      .object({
        bundle: z.string().min(1),
        measures: z.array(z.string().min(1)).min(1),
        featureCount: z.number().int().positive(),
      })
      .passthrough(),
    split: z
      .object({
        outerHoldout: splitPart.extend({ nTrain: z.number().int().positive(), nTest: z.number().int().positive() }),
        devSplit: splitPart.extend({ nFit: z.number().int().positive(), nVal: z.number().int().positive() }),
      })
      .passthrough(),
    observedFitting: z.array(z.number().finite()).min(1),
    observedValidation: z.array(z.number().finite()).min(1),
    trackedFeatures: z.array(z.string().min(1)).min(1),
    models: z.object({
      linear: modelMetrics,
      ridge: alphaModelEntry,
      lasso: alphaModelEntry,
    }),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    if (data.observedFitting.length !== data.split.devSplit.nFit) {
      add(["observedFitting"], "observedFitting length must equal split.devSplit.nFit");
    }
    if (data.observedValidation.length !== data.split.devSplit.nVal) {
      add(["observedValidation"], "observedValidation length must equal split.devSplit.nVal");
    }

    const nTracked = data.trackedFeatures.length;
    const nVal = data.observedValidation.length;

    const checkMetrics = (path: (string | number)[], m: z.infer<typeof modelMetrics>): void => {
      if (m.coefficients.length !== nTracked) add([...path, "coefficients"], "must align with trackedFeatures");
      if (m.predictedValidation.length !== nVal) add([...path, "predictedValidation"], "must align with observedValidation");
    };

    checkMetrics(["models", "linear"], data.models.linear);

    for (const family of ["ridge", "lasso"] as const) {
      const entry = data.models[family];
      if (entry.alphaGrid.length !== entry.perAlpha.length) {
        add(["models", family], "alphaGrid and perAlpha must have the same length");
      }
      if (entry.bestAlphaIndex < 0 || entry.bestAlphaIndex >= entry.perAlpha.length) {
        add(["models", family, "bestAlphaIndex"], "out of range");
      }
      entry.perAlpha.forEach((m, i) => checkMetrics(["models", family, "perAlpha", i], m));
    }
  });

export type RegularizationExploreData = z.infer<typeof regularizationExploreDataSchema>;
export type RegularizationModelMetrics = z.infer<typeof modelMetrics>;

export function parseRegularizationExploreData(raw: unknown): DataResult<RegularizationExploreData> {
  const parsed = regularizationExploreDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid regularization-explore data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
