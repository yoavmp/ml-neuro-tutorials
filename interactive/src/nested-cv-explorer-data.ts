// Zod schema + parser for the "Look Inside Nested Cross-Validation" activity
// data artifact (book/_static/widgets/data/wp27_nested_cv_explorer.json,
// produced by scripts/export_wp27_widget_data.py). DOM / Plotly free so it
// can be unit tested independently of the component.
//
// Every outer fold's inner-CV mean MSE per candidate k, selected k, and
// outer-test MSE/R2 is precomputed offline (scripts/wp27_validation_audit.py)
// -- nothing here runs a nested search in the browser (WP27 spec section 18).

import { z } from "zod";
import type { DataResult } from "./components/types";

const sourceSchema = z
  .object({
    pinnedCommit: z.string().min(1),
    brainTableSha256: z.string().min(1),
    phenotypeTableSha256: z.string().min(1),
  })
  .passthrough();

const foldRowSchema = z
  .object({
    outerFold: z.number().int().nonnegative(),
    nTrain: z.number().int().positive(),
    nTest: z.number().int().positive(),
    innerMseByK: z.record(z.number().finite().nonnegative()),
    selectedK: z.number().int().positive(),
    bestInnerMse: z.number().finite().nonnegative(),
    outerTestMse: z.number().finite().nonnegative(),
    outerTestR2: z.number().finite(),
  })
  .strict();

export const nestedCvExplorerDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("nested-cv-explorer"),
    source: sourceSchema,
    candidateKs: z.array(z.number().int().positive()).min(2),
    nOuter: z.number().int().positive(),
    nInner: z.number().int().positive(),
    featureCount: z.number().int().positive(),
    foldRows: z.array(foldRowSchema).min(1),
    selectedKPerFold: z.array(z.number().int().positive()).min(1),
    selectedKVariesAcrossFolds: z.boolean(),
    meanOuterTestMse: z.number().finite().nonnegative(),
    stdOuterTestMse: z.number().finite().nonnegative(),
    meanOuterTestR2: z.number().finite(),
    stdOuterTestR2: z.number().finite().nonnegative(),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    if (data.foldRows.length !== data.nOuter) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["foldRows"],
        message: `foldRows has ${data.foldRows.length} entries, expected nOuter ${data.nOuter}`,
      });
    }
    const folds = data.foldRows.map((r) => r.outerFold);
    const dup = folds.filter((f, i) => folds.indexOf(f) !== i);
    if (dup.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["foldRows"],
        message: `duplicate outerFold index(es): ${[...new Set(dup)].join(", ")}`,
      });
    }
    for (const row of data.foldRows) {
      if (!data.candidateKs.includes(row.selectedK)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["foldRows", row.outerFold, "selectedK"],
          message: `selectedK ${row.selectedK} is not one of candidateKs ${JSON.stringify(data.candidateKs)}`,
        });
      }
      const innerKeys = Object.keys(row.innerMseByK);
      const candidateKeys = data.candidateKs.map(String);
      if (innerKeys.length !== candidateKeys.length || !candidateKeys.every((k) => innerKeys.includes(k))) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["foldRows", row.outerFold, "innerMseByK"],
          message: `innerMseByK keys ${JSON.stringify(innerKeys)} do not match candidateKs ${JSON.stringify(candidateKeys)}`,
        });
      }
    }
    const recomputedSelected = data.foldRows.map((r) => r.selectedK);
    if (JSON.stringify(recomputedSelected) !== JSON.stringify(data.selectedKPerFold)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["selectedKPerFold"],
        message: `selectedKPerFold ${JSON.stringify(data.selectedKPerFold)} disagrees with foldRows' selectedK order ${JSON.stringify(recomputedSelected)}`,
      });
    }
    const variesActual = new Set(data.selectedKPerFold).size > 1;
    if (variesActual !== data.selectedKVariesAcrossFolds) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["selectedKVariesAcrossFolds"],
        message: `selectedKVariesAcrossFolds ${data.selectedKVariesAcrossFolds} disagrees with recomputed ${variesActual}`,
      });
    }
  });

export type NestedCvExplorerData = z.infer<typeof nestedCvExplorerDataSchema>;
export type NestedCvFoldRow = z.infer<typeof foldRowSchema>;

export function parseNestedCvExplorerData(raw: unknown): DataResult<NestedCvExplorerData> {
  const parsed = nestedCvExplorerDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid nested-cv-explorer data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
