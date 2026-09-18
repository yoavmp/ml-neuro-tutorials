// Zod schema + parser for the Exercise 5 predefined-feature-set-comparison
// catalog artifact (WP28; previously Exercise II / Exercise 2's Bonus)
// (book/_static/widgets/data/abide_regression_models.json, produced by
// scripts/export_regression_catalog.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// The catalog is a finite set of pre-computed model results. Every enabled
// entry shares one eligible cohort and one fixed, reproducible train/test
// split (WP19: no cross-validation): the held-out test target vector is
// stored once at the top level, and each model carries only its held-out
// test-set predictions. This schema enforces that structure so a config can
// never silently compare models fitted on different cohorts or splits, and
// it recomputes each model's R2 / MSE from the stored arrays.

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
    testR2: z.number().finite().optional(),
    testMSE: z.number().finite().nonnegative().optional(),
  })
  .passthrough();

export const regressionCatalogSchema = z
  .object({
    schemaVersion: z.literal(2),
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
    holdoutSplit: z
      .object({
        testSize: z.number().positive().lt(1),
        randomState: z.number().int(),
        stratify: z.string().min(1),
        nTrain: z.number().int().positive(),
        nTest: z.number().int().positive(),
      })
      .passthrough(),
    preprocessing: z.string().min(1),
    observedTest: z.array(z.number().finite()).min(1),
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

    if (data.observedTest.length !== data.holdoutSplit.nTest) {
      add(
        ["observedTest"],
        `observedTest has ${data.observedTest.length} values, expected holdoutSplit.nTest ${data.holdoutSplit.nTest}`,
      );
    }
    if (data.holdoutSplit.nTrain + data.holdoutSplit.nTest !== data.cohort.n) {
      add(["holdoutSplit"], "holdoutSplit.nTrain + nTest must equal cohort.n");
    }
    // observedTest need not be integer: age (years) is fractional. z.number().finite()
    // on the array element already rejects NaN / Infinity / non-numbers.

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
      if (!m.predicted || m.predicted.length !== data.observedTest.length) {
        add(["models", i, "predicted"], `model "${m.key}" predictions must align with observedTest`);
        continue;
      }
      if (typeof m.testR2 !== "number" || typeof m.testMSE !== "number") {
        add(["models", i], `model "${m.key}" is missing testR2 / testMSE`);
        continue;
      }
      const r2 = r2Score(data.observedTest, m.predicted);
      const mse = meanSquaredError(data.observedTest, m.predicted);
      if (Math.abs(r2 - m.testR2) > R2_TOLERANCE) {
        add(["models", i, "testR2"], `stored testR2 ${m.testR2} disagrees with recomputed ${r2.toFixed(6)}`);
      }
      if (Math.abs(mse - m.testMSE) > MSE_TOLERANCE) {
        add(["models", i, "testMSE"], `stored testMSE ${m.testMSE} disagrees with recomputed ${mse.toFixed(4)}`);
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
