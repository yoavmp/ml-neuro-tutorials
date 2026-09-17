// Zod schema + parser for the "One Split or Several Folds?" activity data
// artifact (book/_static/widgets/data/wp27_validation_stability.json,
// produced by scripts/export_wp27_widget_data.py from the single committed
// audit result scripts/wp27_validation_audit_result.json). DOM / Plotly free
// so it can be unit tested and reused independently of the component.
//
// Every number here is precomputed offline for a predeclared, transparent
// grid of sample sizes and seeds (WP27 spec section 10.1 / 21) -- nothing is
// recomputed in the browser, and no seed or sample size is cherry-picked.

import { z } from "zod";
import type { DataResult } from "./components/types";

const sourceSchema = z
  .object({
    pinnedCommit: z.string().min(1),
    brainTableSha256: z.string().min(1),
    phenotypeTableSha256: z.string().min(1),
  })
  .passthrough();

const validSingleSplit = z
  .object({
    seed: z.number().int(),
    valid: z.literal(true),
    n_train: z.number().int().positive(),
    n_test: z.number().int().positive(),
    test_mse: z.number().finite().nonnegative(),
    test_r2: z.number().finite(),
  })
  .strict();

const invalidSingleSplit = z
  .object({
    seed: z.number().int(),
    valid: z.literal(false),
    reason: z.string().min(1),
  })
  .strict();

const singleSplitEntry = z.union([validSingleSplit, invalidSingleSplit]);

const validCvEntry = z
  .object({
    seed: z.number().int(),
    valid: z.literal(true),
    fold_test_sizes: z.array(z.number().int().positive()).min(1),
    fold_train_sizes: z.array(z.number().int().positive()).min(1),
    fold_mse: z.array(z.number().finite().nonnegative()).min(1),
    fold_r2: z.array(z.number().finite()).min(1),
    mean_mse: z.number().finite().nonnegative(),
    std_mse: z.number().finite().nonnegative(),
    mean_r2: z.number().finite(),
    std_r2: z.number().finite().nonnegative(),
  })
  .strict();

const invalidCvEntry = z
  .object({
    seed: z.number().int(),
    valid: z.literal(false),
    reason: z.string().min(1),
  })
  .strict();

const cvEntry = z.union([validCvEntry, invalidCvEntry]);

const sizeEntry = z
  .object({
    sizeKey: z.string().min(1),
    label: z.string().min(1),
    nActual: z.number().int().positive(),
    singleSplit: z.array(singleSplitEntry).min(1),
    cvByFolds: z.record(z.array(cvEntry).min(1)),
    instabilityMeaningful: z.boolean(),
    anyNegativeSingleSplitR2: z.boolean(),
    anyNegativeCv5MeanR2: z.boolean(),
  })
  .strict();

export const validationStabilityDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("validation-stability"),
    source: sourceSchema,
    fixedK: z.number().int().positive(),
    singleSplitTestSize: z.number().positive().lt(1),
    splitSeeds: z.array(z.number().int()).min(1),
    foldOptions: z.array(z.number().int().positive()).min(1),
    sizes: z.array(sizeEntry).min(1),
    sizesWithMeaningfulInstability: z.array(z.string()),
    instabilityRequiresSmallN: z.boolean(),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const keys = data.sizes.map((s) => s.sizeKey);
    const dup = keys.filter((k, i) => keys.indexOf(k) !== i);
    if (dup.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["sizes"],
        message: `duplicate sizeKey(s): ${[...new Set(dup)].join(", ")}`,
      });
    }
    for (const size of data.sizes) {
      const seeds = size.singleSplit.map((s) => s.seed);
      if (seeds.length !== data.splitSeeds.length || !data.splitSeeds.every((s) => seeds.includes(s))) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["sizes", size.sizeKey, "singleSplit"],
          message: `singleSplit seeds ${JSON.stringify(seeds)} do not match splitSeeds ${JSON.stringify(data.splitSeeds)}`,
        });
      }
      for (const foldsKey of Object.keys(size.cvByFolds)) {
        if (!data.foldOptions.some((f) => String(f) === foldsKey)) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["sizes", size.sizeKey, "cvByFolds", foldsKey],
            message: `fold option "${foldsKey}" is not one of foldOptions ${JSON.stringify(data.foldOptions)}`,
          });
        }
      }
    }
    for (const key of data.sizesWithMeaningfulInstability) {
      if (!keys.includes(key)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["sizesWithMeaningfulInstability"],
          message: `"${key}" is not one of sizes[].sizeKey`,
        });
      }
    }
  });

export type ValidationStabilityData = z.infer<typeof validationStabilityDataSchema>;
export type SizeEntry = z.infer<typeof sizeEntry>;
export type SingleSplitEntry = z.infer<typeof singleSplitEntry>;
export type CvEntry = z.infer<typeof cvEntry>;

export function parseValidationStabilityData(raw: unknown): DataResult<ValidationStabilityData> {
  const parsed = validationStabilityDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid validation-stability data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
