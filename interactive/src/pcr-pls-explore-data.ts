// Zod schema + parser for Exercise 9's "PCR or PLS?" activity data
// (book/_static/widgets/data/pcr_pls_explore.json, produced by
// scripts/export_pcr_pls_widget.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// A fixed, deterministic synthetic 2-D predictor cloud with a fixed 40/20
// train/validation split. Only the target values (and therefore the
// precomputed PCR/PLS fits) change across the three presets; the predictor
// cloud and the split never do.

import { z } from "zod";
import type { DataResult } from "./components/types";

const point = z.object({ id: z.number().int().nonnegative(), x: z.number().finite(), y: z.number().finite() }).strict();

const methodName = z.enum(["pcr", "pls"]);
const presetName = z.enum(["weak", "moderate", "strong"]);

const catalogEntry = z
  .object({
    method: methodName,
    nComponents: z.number().int().positive(),
    preset: presetName,
    firstComponentDirection: z.tuple([z.number().finite(), z.number().finite()]),
    trainMse: z.number().finite().nonnegative(),
    trainR2: z.number().finite(),
    valMse: z.number().finite().nonnegative(),
    valR2: z.number().finite(),
    valPredictions: z.array(z.number().finite()).min(1),
    constructionNote: z.string().min(1),
  })
  .strict();

export const pcrPlsExploreDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("pcr-pls-explore"),
    syntheticDataNote: z.string().min(1),
    fixedSignalNoiseNote: z.string().min(1),
    generatingProcess: z
      .object({
        nObservations: z.number().int().positive(),
        nTrain: z.number().int().positive(),
        nVal: z.number().int().positive(),
        rho: z.number().min(-1).max(1),
        signalSd: z.number().positive(),
        noiseSd: z.number().positive(),
        seed: z.number().int(),
        seedNote: z.string().min(1),
        pc1ExplainedVarianceRatio: z.number().min(0).max(1),
        pc2ExplainedVarianceRatio: z.number().min(0).max(1),
      })
      .passthrough(),
    featureX: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    featureY: z.object({ name: z.string().min(1), label: z.string().min(1) }).strict(),
    points: z.array(point).min(1),
    trainIds: z.array(z.number().int().nonnegative()).min(1),
    valIds: z.array(z.number().int().nonnegative()).min(1),
    presets: z.record(presetName, z.object({ label: z.string().min(1), weightPc1: z.number(), weightPc2: z.number() }).strict()),
    targets: z.record(presetName, z.array(z.number().finite())),
    methods: z.array(methodName).min(1),
    componentGrid: z.array(z.number().int().positive()).min(1),
    catalog: z.record(z.string(), catalogEntry),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    const n = data.points.length;
    if (data.trainIds.length + data.valIds.length !== n) {
      add(["trainIds"], "trainIds + valIds must partition every point exactly once");
    }
    for (const preset of Object.keys(data.presets) as (keyof typeof data.presets)[]) {
      if ((data.targets[preset]?.length ?? 0) !== n) {
        add(["targets", preset], "must have exactly one target value per point");
      }
      for (const method of data.methods) {
        for (const nComponents of data.componentGrid) {
          const key = catalogKeyRaw(method, nComponents, preset);
          if (!data.catalog[key]) {
            add(["catalog", key], "missing catalogue entry for a declared (method, nComponents, preset) combination");
          }
        }
      }
    }
  });

export type PcrPlsExploreData = z.infer<typeof pcrPlsExploreDataSchema>;
export type PcrPlsCatalogEntry = z.infer<typeof catalogEntry>;
export type PcrPlsMethod = z.infer<typeof methodName>;
export type PcrPlsPreset = z.infer<typeof presetName>;

function catalogKeyRaw(method: string, nComponents: number, preset: string): string {
  return `${method}|${nComponents}|${preset}`;
}

export function catalogKey(method: PcrPlsMethod, nComponents: number, preset: PcrPlsPreset): string {
  return catalogKeyRaw(method, nComponents, preset);
}

export function catalogEntryFor(
  data: PcrPlsExploreData,
  method: PcrPlsMethod,
  nComponents: number,
  preset: PcrPlsPreset,
): PcrPlsCatalogEntry {
  const entry = data.catalog[catalogKey(method, nComponents, preset)];
  if (!entry) {
    throw new Error(`pcr-pls-explore: no catalogue entry for method=${method} nComponents=${nComponents} preset=${preset}`);
  }
  return entry;
}

export function targetsFor(data: PcrPlsExploreData, preset: PcrPlsPreset): number[] {
  const values = data.targets[preset];
  if (!values) throw new Error(`pcr-pls-explore: no targets for preset=${preset}`);
  return values;
}

/** Two-point line segment through the origin along `direction`, spanning
 * [-halfLength, +halfLength] -- pure geometry, no fitting. */
export function directionLinePoints(direction: readonly [number, number], halfLength: number): { x: number[]; y: number[] } {
  const [dx, dy] = direction;
  return { x: [-dx * halfLength, dx * halfLength], y: [-dy * halfLength, dy * halfLength] };
}

export function parsePcrPlsExploreData(raw: unknown): DataResult<PcrPlsExploreData> {
  const parsed = pcrPlsExploreDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid pcr-pls-explore data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
