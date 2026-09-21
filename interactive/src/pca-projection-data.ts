// Zod schema + parser for Exercise 8's "Find the Best Projection" activity
// data (book/_static/widgets/data/pca_projection.json, produced by
// scripts/export_pca_projection_widget.py). DOM / Plotly free so it can be
// unit tested and reused independently of the rendering component.
//
// A small, fixed, mean-centered synthetic two-dimensional point cloud. The
// component computes the projection onto a student-chosen angle, the
// captured variance, and the reconstruction MSE live from this data via
// plain trigonometry -- nothing here is fit or refit.

import { z } from "zod";
import type { DataResult } from "./components/types";

const observation = z
  .object({
    id: z.number().int().nonnegative(),
    x: z.number().finite(),
    y: z.number().finite(),
  })
  .strict();

export const pcaProjectionDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("pca-projection"),
    syntheticDataNote: z.string().min(1),
    generatingProcess: z
      .object({
        distribution: z.string().min(1),
        sigmaX: z.number().positive(),
        sigmaY: z.number().positive(),
        rho: z.number().min(-1).max(1),
        nObservations: z.number().int().positive(),
        seed: z.number().int(),
        seedNote: z.string().min(1),
        centeringNote: z.string().min(1),
      })
      .passthrough(),
    featureX: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    featureY: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    observations: z.array(observation).min(1),
    totalVariance: z.number().finite().nonnegative(),
    truePc1: z
      .object({
        angleDeg: z.number().min(0).max(180),
        explainedVarianceRatio: z.number().min(0).max(1),
      })
      .strict(),
    angleSliderDeg: z.object({ min: z.number(), max: z.number(), step: z.number().positive() }).strict(),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    if (data.observations.length !== data.generatingProcess.nObservations) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["observations"],
        message: `expected ${data.generatingProcess.nObservations} observations, got ${data.observations.length}`,
      });
    }
    if (data.angleSliderDeg.min < 0 || data.angleSliderDeg.max > 180 || data.angleSliderDeg.min >= data.angleSliderDeg.max) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["angleSliderDeg"],
        message: "angleSliderDeg must satisfy 0 <= min < max <= 180",
      });
    }
  });

export type PcaProjectionData = z.infer<typeof pcaProjectionDataSchema>;
export type PcaProjectionObservation = z.infer<typeof observation>;

/**
 * Projection of the (already mean-centered) point cloud onto the axis at
 * `angleDeg`: the projected ("captured") coordinate along the axis for every
 * point, the variance that axis captures, and the mean squared
 * reconstruction error left behind. Pure closed-form trigonometry -- no
 * fitting.
 *
 * Because the cloud is mean-centered, a linear projection's own mean is
 * always 0, so "variance captured" is simply the mean of the squared
 * projected coordinates, and (by the Pythagorean theorem, since the
 * projection axis is a unit vector) each point's squared reconstruction
 * error is exactly its squared distance from the origin minus its squared
 * projected coordinate -- so reconstruction MSE = totalVariance - captured
 * variance exactly, with no separate computation needed.
 */
export interface ProjectionResult {
  projected: number[];
  varianceCaptured: number;
  reconstructionMSE: number;
  proportionVarianceCaptured: number;
}

export function projectAtAngle(data: PcaProjectionData, angleDeg: number): ProjectionResult {
  const theta = (angleDeg * Math.PI) / 180;
  const ux = Math.cos(theta);
  const uy = Math.sin(theta);
  const projected = data.observations.map((o) => o.x * ux + o.y * uy);
  const varianceCaptured = projected.reduce((sum, t) => sum + t * t, 0) / projected.length;
  const reconstructionMSE = Math.max(0, data.totalVariance - varianceCaptured);
  const proportionVarianceCaptured = data.totalVariance > 0 ? varianceCaptured / data.totalVariance : 0;
  return { projected, varianceCaptured, reconstructionMSE, proportionVarianceCaptured };
}

export function parsePcaProjectionData(raw: unknown): DataResult<PcaProjectionData> {
  const parsed = pcaProjectionDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid pca-projection data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
