// Zod schema + parser for Exercise 7's "Build a Boosted Model" activity data
// (book/_static/widgets/data/boosting_step_by_step.json, produced by
// scripts/export_boosting_step_widget.py). DOM / Plotly free so it can be
// unit tested and reused independently of the rendering component.
//
// A small synthetic dataset walked stage-by-stage through squared-error
// gradient boosting for several learning rates -- every stage's ensemble
// prediction, residuals-before-update, and fitted stump are precomputed;
// nothing is fit live in the browser. This schema enforces that stage 0
// carries no stump and that every later stage's arrays align with the
// observation count.

import { z } from "zod";
import type { DataResult } from "./components/types";

const observation = z
  .object({
    id: z.number().int().nonnegative(),
    x: z.number().finite(),
    y: z.number().finite(),
  })
  .strict();

const stump = z
  .object({
    threshold: z.number().finite(),
    leftValue: z.number().finite(),
    rightValue: z.number().finite(),
  })
  .strict();

const stage = z
  .object({
    stage: z.number().int().nonnegative(),
    ensemblePrediction: z.array(z.number().finite()).min(1),
    residualBeforeUpdate: z.array(z.number().finite()).min(1),
    trainMSE: z.number().finite().nonnegative(),
    stump: stump.nullable(),
    treePrediction: z.array(z.number().finite()).nullable(),
    scaledCorrection: z.array(z.number().finite()).nullable(),
  })
  .strict();

export const boostingStepByStepDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("boosting-step-by-step"),
    syntheticDataNote: z.string().min(1),
    generatingProcess: z
      .object({
        formula: z.string().min(1),
        x: z.object({ distribution: z.string().min(1), low: z.number().finite(), high: z.number().finite() }).passthrough(),
        coefficients: z.record(z.string(), z.number().finite()),
        nObservations: z.number().int().positive(),
        seed: z.number().int(),
        seedNote: z.string().min(1),
      })
      .passthrough(),
    feature: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    target: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    observations: z.array(observation).min(1),
    learningRates: z.array(z.number().positive()).min(1),
    nStages: z.number().int().positive(),
    stumpSettings: z.object({ maxDepth: z.number().int().positive() }).strict(),
    updateEquation: z.string().min(1),
    stagesByLearningRate: z.record(z.string(), z.array(stage).min(1)),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    const nObs = data.observations.length;
    const keys = Object.keys(data.stagesByLearningRate);
    for (const eta of data.learningRates) {
      // Match by numeric value, not `String(eta)`: JSON may spell a whole
      // number learning rate as "1.0" while JS's `String(1)` produces "1".
      const key = keys.find((k) => Number(k) === eta) ?? String(eta);
      const stages = data.stagesByLearningRate[key];
      if (!stages) {
        add(["stagesByLearningRate", key], "missing stages for a declared learning rate");
        continue;
      }
      if (stages.length !== data.nStages + 1) {
        add(["stagesByLearningRate", key], `expected ${data.nStages + 1} stages (0..nStages)`);
      }
      stages.forEach((s, i) => {
        if (s.ensemblePrediction.length !== nObs || s.residualBeforeUpdate.length !== nObs) {
          add(["stagesByLearningRate", key, i], "prediction/residual arrays must align with observations");
        }
        if (s.stage === 0) {
          if (s.stump !== null || s.treePrediction !== null || s.scaledCorrection !== null) {
            add(["stagesByLearningRate", key, i], "stage 0 must not carry a stump or tree prediction");
          }
        } else {
          if (s.stump === null || s.treePrediction === null || s.scaledCorrection === null) {
            add(["stagesByLearningRate", key, i], "stages after 0 must carry a stump and tree prediction");
          } else if (s.treePrediction.length !== nObs || s.scaledCorrection.length !== nObs) {
            add(["stagesByLearningRate", key, i], "treePrediction/scaledCorrection must align with observations");
          }
        }
      });
    }
  });

export type BoostingStepByStepData = z.infer<typeof boostingStepByStepDataSchema>;
export type BoostingStepByStepStage = z.infer<typeof stage>;
export type BoostingStepByStepObservation = z.infer<typeof observation>;

/**
 * Look up a learning rate's stage list by numeric value, not `String(eta)`:
 * JSON may spell a whole-number learning rate as "1.0" while JS's
 * `String(1)` produces "1" -- a mismatch this parser tolerates (see the
 * `superRefine` key-matching above) but a naive `stagesByLearningRate[String(eta)]`
 * lookup would not.
 */
export function stagesForLearningRate(data: BoostingStepByStepData, eta: number): BoostingStepByStepStage[] {
  const keys = Object.keys(data.stagesByLearningRate);
  const key = keys.find((k) => Number(k) === eta) ?? String(eta);
  return data.stagesByLearningRate[key]!;
}

export function parseBoostingStepByStepData(raw: unknown): DataResult<BoostingStepByStepData> {
  const parsed = boostingStepByStepDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid boosting-step-by-step data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
