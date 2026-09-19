// Zod schema + parser for the "Choose k Before Revealing the Test Set"
// activity data artifact
// (book/_static/widgets/data/wp27_validation_lock_test.json, produced by
// scripts/export_wp27_widget_data.py). DOM / Plotly free so it can be unit
// tested independently of the component.
//
// Every candidate k's training MSE, validation MSE, and locked test MSE/R2
// is precomputed offline (scripts/wp27_validation_audit.py) on the exact
// Exercise 2 outer holdout split and dev split. The training-selected and
// validation-selected k are computed there too, using only train/validation
// numbers -- this schema recomputes both from the rows as a consistency
// check, so a stale or hand-edited artifact cannot silently disagree with
// its own data.

import { z } from "zod";
import type { DataResult } from "./components/types";

const sourceSchema = z
  .object({
    pinnedCommit: z.string().min(1),
    brainTableSha256: z.string().min(1),
    phenotypeTableSha256: z.string().min(1),
  })
  .passthrough();

const rowSchema = z
  .object({
    k: z.number().int().positive(),
    trainMse: z.number().finite().nonnegative(),
    trainR2: z.number().finite(),
    valMse: z.number().finite().nonnegative(),
    valR2: z.number().finite(),
    testMseIfLocked: z.number().finite().nonnegative(),
    testR2IfLocked: z.number().finite(),
  })
  .strict();

export const validationLockTestDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("validation-lock-test"),
    source: sourceSchema,
    nFit: z.number().int().positive(),
    nVal: z.number().int().positive(),
    nTest: z.number().int().positive(),
    featureCount: z.number().int().positive(),
    candidateKs: z.array(z.number().int().positive()).min(2),
    rows: z.array(rowSchema).min(2),
    trainingSelectedK: z.number().int().positive(),
    validationSelectedK: z.number().int().positive(),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const ks = data.rows.map((r) => r.k);
    const dup = ks.filter((k, i) => ks.indexOf(k) !== i);
    if (dup.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["rows"],
        message: `duplicate k value(s): ${[...new Set(dup)].join(", ")}`,
      });
    }
    if (ks.length !== data.candidateKs.length || !data.candidateKs.every((k) => ks.includes(k))) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["rows"],
        message: `row k values ${JSON.stringify(ks)} do not match candidateKs ${JSON.stringify(data.candidateKs)}`,
      });
    }
    if (data.rows.length > 0) {
      const recomputedTrainSel = data.rows.reduce((best, r) => (r.trainMse < best.trainMse ? r : best)).k;
      const recomputedValSel = data.rows.reduce((best, r) => (r.valMse < best.valMse ? r : best)).k;
      if (recomputedTrainSel !== data.trainingSelectedK) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["trainingSelectedK"],
          message: `trainingSelectedK ${data.trainingSelectedK} disagrees with recomputed argmin(trainMse) ${recomputedTrainSel}`,
        });
      }
      if (recomputedValSel !== data.validationSelectedK) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["validationSelectedK"],
          message: `validationSelectedK ${data.validationSelectedK} disagrees with recomputed argmin(valMse) ${recomputedValSel}`,
        });
      }
    }
    if (!ks.includes(data.trainingSelectedK)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["trainingSelectedK"],
        message: `trainingSelectedK ${data.trainingSelectedK} is not one of the candidate rows`,
      });
    }
    if (!ks.includes(data.validationSelectedK)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["validationSelectedK"],
        message: `validationSelectedK ${data.validationSelectedK} is not one of the candidate rows`,
      });
    }
  });

export type ValidationLockTestData = z.infer<typeof validationLockTestDataSchema>;
export type LockTestRow = z.infer<typeof rowSchema>;

export function parseValidationLockTestData(raw: unknown): DataResult<ValidationLockTestData> {
  const parsed = validationLockTestDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid validation-lock-test data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
