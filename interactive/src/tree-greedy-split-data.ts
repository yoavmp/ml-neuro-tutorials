// Zod schema + parser for the Exercise 6 "Build a Tree Greedily" activity
// data (book/_static/widgets/data/tree_greedy_split.json, produced by
// scripts/export_tree_greedy_widget.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// The dataset is entirely synthetic and every round's candidate thresholds,
// weighted split MSE, and greedy optimum are precomputed -- nothing is
// recomputed in the browser. This schema enforces that every round's
// candidate arrays line up and that the optimal entry is actually present
// among its own feature's candidates, so a malformed artifact can never
// silently reach the component.

import { z } from "zod";
import type { DataResult } from "./components/types";

const observation = z
  .object({
    id: z.number().int().nonnegative(),
    x1: z.number().finite(),
    x2: z.number().finite(),
    y: z.number().finite(),
  })
  .strict();

const featureCandidates = z
  .object({
    thresholds: z.array(z.number().finite()).min(1),
    splitMSE: z.array(z.number().finite().nonnegative()).min(1),
    reduction: z.array(z.number().finite()).min(1),
    nLeft: z.array(z.number().int().nonnegative()).min(1),
    nRight: z.array(z.number().int().nonnegative()).min(1),
  })
  .strict();

const optimalSplit = z
  .object({
    feature: z.enum(["x1", "x2"]),
    thresholdIndex: z.number().int().nonnegative(),
    threshold: z.number().finite(),
    splitMSE: z.number().finite().nonnegative(),
    reduction: z.number().finite(),
    nLeft: z.number().int().nonnegative(),
    nRight: z.number().int().nonnegative(),
    leftMean: z.number().finite(),
    rightMean: z.number().finite(),
  })
  .strict();

const round = z
  .object({
    id: z.string().min(1),
    label: z.string().min(1),
    activeObservationIds: z.array(z.number().int().nonnegative()).min(2),
    parentMSE: z.number().finite().nonnegative(),
    candidates: z.object({ x1: featureCandidates, x2: featureCandidates }).strict(),
    optimal: optimalSplit,
  })
  .strict();

const generatingProcess = z
  .object({
    formula: z.string().min(1),
    x1: z.object({ distribution: z.string().min(1), mean: z.number(), sd: z.number().positive() }).strict(),
    x2: z.object({ distribution: z.string().min(1), mean: z.number(), sd: z.number().positive() }).strict(),
    intercept: z.number(),
    beta1: z.number(),
    beta2: z.number(),
    gamma: z.number(),
    noiseSD: z.number().positive(),
    nObservations: z.number().int().positive(),
    seedSearchRange: z.tuple([z.number().int(), z.number().int()]),
    selectedSeed: z.number().int().nonnegative(),
    selectionNote: z.string().min(1),
  })
  .strict();

export const treeGreedySplitDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("tree-greedy-split"),
    syntheticDataNote: z.string().min(1),
    generatingProcess,
    features: z
      .object({
        x1: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
        x2: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
      })
      .strict(),
    observations: z.array(observation).min(12).max(20),
    rounds: z.array(round).length(3),
  })
  .strict()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    const obsById = new Map(data.observations.map((o) => [o.id, o]));

    data.rounds.forEach((r, i) => {
      for (const feature of ["x1", "x2"] as const) {
        const c = r.candidates[feature];
        const lengths = new Set([
          c.thresholds.length,
          c.splitMSE.length,
          c.reduction.length,
          c.nLeft.length,
          c.nRight.length,
        ]);
        if (lengths.size !== 1) {
          add(["rounds", i, "candidates", feature], "candidate arrays must have equal length");
        }
      }
      const optCandidates = r.candidates[r.optimal.feature];
      if (r.optimal.thresholdIndex >= optCandidates.thresholds.length) {
        add(["rounds", i, "optimal", "thresholdIndex"], "out of range for its own feature's candidates");
      } else if (optCandidates.thresholds[r.optimal.thresholdIndex] !== r.optimal.threshold) {
        add(["rounds", i, "optimal", "threshold"], "does not match its own thresholdIndex");
      }
      for (const id of r.activeObservationIds) {
        if (!obsById.has(id)) add(["rounds", i, "activeObservationIds"], `unknown observation id ${id}`);
      }
    });
  });

export type TreeGreedySplitData = z.infer<typeof treeGreedySplitDataSchema>;
export type TreeGreedySplitRound = z.infer<typeof round>;
export type TreeGreedySplitObservation = z.infer<typeof observation>;

export function parseTreeGreedySplitData(raw: unknown): DataResult<TreeGreedySplitData> {
  const parsed = treeGreedySplitDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid tree-greedy-split data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
