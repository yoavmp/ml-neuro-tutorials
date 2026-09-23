// Zod schema + parser for Exercise 7's "Explore the Boosting Parameters"
// activity data (book/_static/widgets/data/boosting_parameter_explorer.json,
// produced by scripts/export_boosting_parameter_widget.py). DOM / Plotly
// free so it can be unit tested and reused independently of the rendering
// component.
//
// A precomputed grid of (learning_rate, max_depth, n_trees) combinations on
// the fixed 564/189 development fit/validation split -- every metric and
// validation prediction is precomputed offline via staged_predict; nothing
// is fit live in the browser, and the locked outer test set never appears
// here (enforced structurally: this schema has no field for it).

import { z } from "zod";
import type { DataResult } from "./components/types";

const splitPart = z
  .object({
    test_size: z.number().positive().lt(1),
    random_state: z.number().int(),
    stratify: z.string().min(1),
  })
  .passthrough();

const gridPoint = z
  .object({
    trainMSE: z.number().finite().nonnegative(),
    valMSE: z.number().finite().nonnegative(),
    valR2: z.number().finite(),
    predictedValidation: z.array(z.number().finite()).min(1),
  })
  .strict();

const gridEntry = z
  .object({
    learningRate: z.number().positive(),
    maxDepth: z.number().int().positive(),
    byNTrees: z.record(z.string(), gridPoint),
  })
  .strict();

export const boostingParameterExplorerDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("boosting-parameter-explorer"),
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
        outerHoldout: splitPart,
        devSplit: splitPart.extend({ nFit: z.number().int().positive(), nVal: z.number().int().positive() }),
      })
      .passthrough(),
    lockedTestExcluded: z.literal(true),
    learningRateGrid: z.array(z.number().positive()).min(1),
    depthGrid: z.array(z.number().int().positive()).min(1),
    nTreesGrid: z.array(z.number().int().positive()).min(2),
    defaults: z
      .object({
        learningRate: z.number().positive(),
        depth: z.number().int().positive(),
        nTrees: z.number().int().positive(),
      })
      .strict(),
    observedValidation: z.array(z.number().finite()).min(1),
    grid: z.record(z.string(), gridEntry),
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
    for (const lr of data.learningRateGrid) {
      for (const depth of data.depthGrid) {
        const key = `${lr}|${depth}`;
        const entry = data.grid[key];
        if (!entry) {
          add(["grid", key], "missing entry for a declared (learningRate, depth) combination");
          continue;
        }
        for (const n of data.nTreesGrid) {
          const point = entry.byNTrees[String(n)];
          if (!point || point.predictedValidation.length !== nVal) {
            add(["grid", key, "byNTrees", String(n)], "missing or misaligned prediction array");
          }
        }
      }
    }
    if (!data.learningRateGrid.includes(data.defaults.learningRate)) {
      add(["defaults", "learningRate"], "must be one of learningRateGrid");
    }
    if (!data.depthGrid.includes(data.defaults.depth)) {
      add(["defaults", "depth"], "must be one of depthGrid");
    }
    if (!data.nTreesGrid.includes(data.defaults.nTrees)) {
      add(["defaults", "nTrees"], "must be one of nTreesGrid");
    }
  });

export type BoostingParameterExplorerData = z.infer<typeof boostingParameterExplorerDataSchema>;
export type BoostingParameterGridPoint = z.infer<typeof gridPoint>;
export type BoostingParameterGridEntry = z.infer<typeof gridEntry>;

export function parseBoostingParameterExplorerData(raw: unknown): DataResult<BoostingParameterExplorerData> {
  const parsed = boostingParameterExplorerDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid boosting-parameter-explorer data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
