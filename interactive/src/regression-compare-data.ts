// Zod schema + parser for the Exercise II model-comparison catalog artifact
// (book/_static/widgets/data/abide_regression_models.json, produced by
// scripts/export_regression_catalog.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// The catalog is a finite set of pre-computed model results. Every enabled
// entry shares one eligible cohort and one deterministic 5-fold split: the
// observed target vector and the per-row fold assignment are stored once at the
// top level, and each model carries only its out-of-fold predictions. This
// schema enforces that structure so a config can never silently compare models
// fitted on different cohorts or folds, and it recomputes each model's R2 / MSE
// from the stored arrays.

import { z } from "zod";
import type { DataResult } from "./components/types";
import { r2Score, meanSquaredError } from "./regression-compare";

const R2_TOLERANCE = 1e-3;
const MSE_TOLERANCE = 1e-1;
const IDENTIFIER_TOKEN = /(^|_)(id|ids|uid|sub|subject|participant|site|mrn|name|dob)($|_)/i;

const modelEntry = z
  .object({
    key: z.string().min(1),
    bundle: z.string().min(1),
    measures: z.array(z.string().min(1)).min(1),
    featureCount: z.number().int().positive(),
    disabled: z.boolean(),
    reason: z.string().min(1).optional(),
    predicted: z.array(z.number().finite()).optional(),
    cvR2: z.number().finite().optional(),
    cvMSE: z.number().finite().nonnegative().optional(),
  })
  .passthrough();

export const regressionCatalogSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("regression-compare"),
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
    cohort: z
      .object({
        n: z.number().int().positive(),
        requirement: z.string().min(1),
        diagnosisNote: z.string().min(1),
      })
      .passthrough(),
    crossValidation: z
      .object({
        kind: z.literal("KFold"),
        nSplits: z.number().int().min(2),
        shuffle: z.boolean(),
        randomState: z.number().int(),
        foldTrainN: z.number().int().positive(),
      })
      .passthrough(),
    preprocessing: z.string().min(1),
    observed: z.array(z.number().finite()).min(1),
    foldOf: z.array(z.number().int().nonnegative()).min(1),
    bundles: z.record(
      z
        .object({ label: z.string().min(1), rois: z.array(z.string().min(1)).min(1) })
        .passthrough(),
    ),
    measures: z.record(
      z.object({ label: z.string().min(1), unit: z.string().min(1) }).passthrough(),
    ),
    measurementSubsets: z.array(z.array(z.string().min(1)).min(1)).min(1),
    models: z.array(modelEntry).min(1),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    for (const key of Object.keys(data)) {
      if (IDENTIFIER_TOKEN.test(key)) add([key], `identifier-shaped top-level key "${key}" is not allowed`);
    }

    if (data.observed.length !== data.cohort.n) {
      add(["observed"], `observed has ${data.observed.length} values, expected cohort.n ${data.cohort.n}`);
    }
    // observed need not be integer: age (years) is fractional, FIQ is an
    // integer standard score. z.number().finite() on the array element already
    // rejects NaN / Infinity / non-numbers.
    if (data.foldOf.length !== data.observed.length) {
      add(["foldOf"], "foldOf must align with observed");
    }
    const foldsUsed = [...new Set(data.foldOf)].sort((a, b) => a - b);
    const expectedFolds = Array.from({ length: data.crossValidation.nSplits }, (_, i) => i);
    if (foldsUsed.join(",") !== expectedFolds.join(",")) {
      add(["foldOf"], `foldOf must use every fold index 0..${data.crossValidation.nSplits - 1}`);
    }

    for (const subset of data.measurementSubsets) {
      for (const m of subset) {
        if (!data.measures[m]) add(["measurementSubsets"], `subset references unknown measure "${m}"`);
      }
    }

    const seenKeys = new Set<string>();
    let enabled = 0;
    for (let i = 0; i < data.models.length; i += 1) {
      const m = data.models[i]!;
      if (seenKeys.has(m.key)) add(["models", i, "key"], `duplicate model key "${m.key}"`);
      seenKeys.add(m.key);
      if (!data.bundles[m.bundle]) add(["models", i, "bundle"], `unknown bundle "${m.bundle}"`);
      for (const meas of m.measures) {
        if (!data.measures[meas]) add(["models", i, "measures"], `unknown measure "${meas}"`);
      }
      if (m.disabled) {
        if (!m.reason) add(["models", i, "reason"], `disabled model "${m.key}" needs a reason`);
        if (m.predicted) add(["models", i, "predicted"], `disabled model "${m.key}" must not carry predictions`);
        continue;
      }
      enabled += 1;
      if (!m.predicted || m.predicted.length !== data.observed.length) {
        add(["models", i, "predicted"], `model "${m.key}" predictions must align with observed`);
        continue;
      }
      if (typeof m.cvR2 !== "number" || typeof m.cvMSE !== "number") {
        add(["models", i], `model "${m.key}" is missing cvR2 / cvMSE`);
        continue;
      }
      const r2 = r2Score(data.observed, m.predicted);
      const mse = meanSquaredError(data.observed, m.predicted);
      if (Math.abs(r2 - m.cvR2) > R2_TOLERANCE) {
        add(["models", i, "cvR2"], `stored cvR2 ${m.cvR2} disagrees with recomputed ${r2.toFixed(6)}`);
      }
      if (Math.abs(mse - m.cvMSE) > MSE_TOLERANCE) {
        add(["models", i, "cvMSE"], `stored cvMSE ${m.cvMSE} disagrees with recomputed ${mse.toFixed(4)}`);
      }
    }
    if (enabled === 0) add(["models"], "the catalog has no enabled models");
  });

export type RegressionCatalog = z.infer<typeof regressionCatalogSchema>;
export type RegressionModelEntry = z.infer<typeof modelEntry>;

export function parseRegressionCatalog(raw: unknown): DataResult<RegressionCatalog> {
  const parsed = regressionCatalogSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid regression catalog data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
