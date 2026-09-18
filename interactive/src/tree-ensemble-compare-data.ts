// Zod schema + parser for the Exercise 6 "One Tree or Many?" activity data
// (book/_static/widgets/data/tree_ensemble_compare.json, produced by
// scripts/export_tree_ensemble_widget.py). DOM / Plotly free so it can be
// unit tested and reused independently of the rendering component.
//
// Five deterministic training replicates, each scored on one fixed
// validation set, for a single tree, bagging, and a Random Forest across a
// grid of ensemble sizes -- every prediction is precomputed offline. This
// schema enforces that every replicate's arrays align with the shared
// validation array and the declared n_trees grid.

import { z } from "zod";
import type { DataResult } from "./components/types";

const splitPart = z
  .object({
    test_size: z.number().positive().lt(1),
    random_state: z.number().int(),
    stratify: z.string().min(1),
  })
  .passthrough();

const modelPoint = z
  .object({
    valMSE: z.number().finite().nonnegative(),
    valR2: z.number().finite(),
    predictedValidation: z.array(z.number().finite()).min(1),
  })
  .strict();

const byNTrees = z.record(z.string(), modelPoint);

const replicate = z
  .object({
    seed: z.number().int().nonnegative(),
    nTrain: z.number().int().positive(),
    rootSplit: z.object({ feature: z.string().min(1), threshold: z.number().finite() }).strict(),
    singleTree: modelPoint,
    bagging: z.object({ byNTrees }).strict(),
    randomForest: z.object({ byNTrees }).strict(),
  })
  .strict();

const summaryPoint = z
  .object({
    meanMSE: z.number().finite().nonnegative(),
    sdMSE: z.number().finite().nonnegative(),
    values: z.array(z.number().finite()).min(1),
  })
  .strict();

export const treeEnsembleCompareDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("tree-ensemble-compare"),
    source: z
      .object({
        pinnedCommit: z.string().min(1),
        brainTableSha256: z.string().min(1),
        phenotypeTableSha256: z.string().min(1),
      })
      .passthrough(),
    target: z.object({ name: z.string().min(1), label: z.string().min(1), unit: z.string().min(1) }).passthrough(),
    featureRecipe: z
      .object({ bundle: z.string().min(1), measures: z.array(z.string().min(1)).min(1), featureCount: z.number().int().positive() })
      .passthrough(),
    split: z
      .object({
        outerHoldout: splitPart.extend({ nTrain: z.number().int().positive(), nTest: z.number().int().positive() }),
        devSplit: splitPart.extend({ nFit: z.number().int().positive(), nVal: z.number().int().positive() }),
      })
      .passthrough(),
    settings: z
      .object({
        replicateFraction: z.number().positive().lte(1),
        replicatePoolSize: z.number().int().positive(),
        treeSettings: z.record(z.string(), z.number()),
        randomForestMaxFeatures: z.number().int().positive(),
      })
      .passthrough(),
    nTreesGrid: z.array(z.number().int().positive()).min(2),
    observedValidation: z.array(z.number().finite()).min(1),
    replicates: z.array(replicate).min(2),
    summary: z
      .object({
        singleTree: summaryPoint,
        bagging: z.record(z.string(), summaryPoint),
        randomForest: z.record(z.string(), summaryPoint),
      })
      .strict(),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    const nVal = data.observedValidation.length;
    if (nVal !== data.split.devSplit.nVal) {
      add(["observedValidation"], "length must equal split.devSplit.nVal");
    }
    data.replicates.forEach((r, i) => {
      if (r.singleTree.predictedValidation.length !== nVal) {
        add(["replicates", i, "singleTree", "predictedValidation"], "must align with observedValidation");
      }
      for (const n of data.nTreesGrid) {
        const bag = r.bagging.byNTrees[String(n)];
        const rf = r.randomForest.byNTrees[String(n)];
        if (!bag || bag.predictedValidation.length !== nVal) {
          add(["replicates", i, "bagging", "byNTrees", String(n)], "missing or misaligned prediction array");
        }
        if (!rf || rf.predictedValidation.length !== nVal) {
          add(["replicates", i, "randomForest", "byNTrees", String(n)], "missing or misaligned prediction array");
        }
      }
    });
    for (const n of data.nTreesGrid) {
      if (!data.summary.bagging[String(n)]) add(["summary", "bagging", String(n)], "missing summary for this n_trees");
      if (!data.summary.randomForest[String(n)]) add(["summary", "randomForest", String(n)], "missing summary for this n_trees");
    }
  });

export type TreeEnsembleCompareData = z.infer<typeof treeEnsembleCompareDataSchema>;
export type TreeEnsembleReplicate = z.infer<typeof replicate>;
export type TreeEnsembleModelPoint = z.infer<typeof modelPoint>;

export function parseTreeEnsembleCompareData(raw: unknown): DataResult<TreeEnsembleCompareData> {
  const parsed = treeEnsembleCompareDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid tree-ensemble-compare data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
