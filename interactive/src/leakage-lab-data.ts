// Loader for the Exercise 10 leakage lab artifact
// (book/_static/widgets/data/abide_leakage_lab.json). DOM / Plotly free so it
// can be unit tested independently of the rendering component.
//
// Every (scenario, sample size, seed) combination's correct-pipeline and
// leaky-pipeline test MSE/R2 is precomputed offline; nothing is refit in the
// browser. The estimator is KNeighborsRegressor(n_neighbors=15) in all three
// scenarios (WP38R sec 4). Unlike ordinary least squares, KNN's predictions
// depend on feature scale, so the scaling scenario's correct/leaky pair is
// NOT identical in the recomputed artifact -- every entry now shows a real,
// if often small, gap (up to about +/-0.07 R2 across the predeclared splits,
// sign not consistent from split to split). This parser must not assume a
// zero gap for scaling, nor "fix" a non-zero one; whatever the artifact
// contains is a valid value like any other.

import { z } from "zod";
import type { DataResult } from "./components/types";

export const LEAKAGE_LAB_SCENARIOS = ["scaling", "feature_selection", "pca"] as const;
export type LeakageLabScenario = (typeof LEAKAGE_LAB_SCENARIOS)[number];

const metricPair = z
  .object({
    mse: z.number().finite().nonnegative(),
    r2: z.number().finite(),
  })
  .strict();

const entrySchema = z
  .object({
    scenario: z.enum(LEAKAGE_LAB_SCENARIOS),
    sampleSize: z.number().int().positive(),
    seed: z.number().int(),
    nTrain: z.number().int().positive(),
    nTest: z.number().int().positive(),
    correct: metricPair,
    leaky: metricPair,
  })
  .strict();

const scenarioMetaSchema = z
  .object({
    bundle: z.string().min(1),
    featureCount: z.number().int().positive(),
    measures: z.array(z.string().min(1)).min(1),
    model: z.string().min(1),
    correctWorkflow: z.string().min(1),
    leakyWorkflow: z.string().min(1),
  })
  .passthrough();

const sourceSchema = z
  .object({
    pinnedCommit: z.string().min(1),
    brainTableSha256: z.string().min(1),
  })
  .passthrough();

const schema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("leakage-lab"),
    target: z.string().min(1),
    source: sourceSchema,
    sampleSizes: z.array(z.number().int().positive()).min(1),
    seeds: z.array(z.number().int()).min(1),
    scenarios: z
      .object({
        scaling: scenarioMetaSchema,
        feature_selection: scenarioMetaSchema,
        pca: scenarioMetaSchema,
      })
      .strict(),
    entries: z.array(entrySchema).min(1),
  })
  .passthrough();

export type LeakageLabScenarioMeta = z.infer<typeof scenarioMetaSchema>;
export type LeakageLabEntry = z.infer<typeof entrySchema>;
export type LeakageLabData = z.infer<typeof schema>;

function entryKey(scenario: string, sampleSize: number, seed: number): string {
  return `${scenario}|${sampleSize}|${seed}`;
}

export function parseLeakageLabData(raw: unknown): DataResult<LeakageLabData> {
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid leakage lab data: ${msg}` };
  }
  const data = parsed.data;

  const expectedKeys = new Set<string>();
  for (const scenario of LEAKAGE_LAB_SCENARIOS) {
    for (const sampleSize of data.sampleSizes) {
      for (const seed of data.seeds) {
        expectedKeys.add(entryKey(scenario, sampleSize, seed));
      }
    }
  }

  const seenKeys = new Set<string>();
  for (const entry of data.entries) {
    const key = entryKey(entry.scenario, entry.sampleSize, entry.seed);
    if (seenKeys.has(key)) {
      return {
        ok: false,
        error: `Invalid leakage lab data: duplicate entry for scenario=${entry.scenario}, sampleSize=${entry.sampleSize}, seed=${entry.seed}`,
      };
    }
    seenKeys.add(key);
    if (!expectedKeys.has(key)) {
      return {
        ok: false,
        error: `Invalid leakage lab data: entry for scenario=${entry.scenario}, sampleSize=${entry.sampleSize}, seed=${entry.seed} is not one of the declared scenarios/sampleSizes/seeds`,
      };
    }
  }
  const missing = [...expectedKeys].filter((k) => !seenKeys.has(k));
  if (missing.length > 0) {
    return {
      ok: false,
      error: `Invalid leakage lab data: missing ${missing.length} entr${missing.length === 1 ? "y" : "ies"} (e.g. ${missing[0]})`,
    };
  }

  return { ok: true, data };
}

/** All 5 predeclared-seed entries for one (scenario, sampleSize), sorted by seed. */
export function entriesForScenarioSize(
  data: LeakageLabData,
  scenario: LeakageLabScenario,
  sampleSize: number,
): LeakageLabEntry[] {
  return data.entries
    .filter((e) => e.scenario === scenario && e.sampleSize === sampleSize)
    .sort((a, b) => a.seed - b.seed);
}

export function findLeakageLabEntry(
  data: LeakageLabData,
  scenario: LeakageLabScenario,
  sampleSize: number,
  seed: number,
): LeakageLabEntry {
  const entry = data.entries.find(
    (e) => e.scenario === scenario && e.sampleSize === sampleSize && e.seed === seed,
  );
  if (!entry) {
    throw new Error(`No leakage-lab entry for scenario=${scenario}, sampleSize=${sampleSize}, seed=${seed}`);
  }
  return entry;
}
