// Zod schema + parser for the Exercise 3 Section 3 "honest vs invalid" KNN
// interactive artifact (book/_static/widgets/data/abide_knn_abc.json,
// produced by scripts/export_knn_abc_data.py). DOM / Plotly free so it can be
// unit tested and reused independently of the rendering component.
//
// The artifact stores, for Exercise 2's own locked 753/251 outer train/test
// split: for every query participant in each of three panels (A valid, B
// resubstitution, C invalid leakage), that participant's reference-pool
// target (age) values reordered by distance (nearest first), truncated to
// the shared valid k range 1..min(n_train, n_test). The component derives
// every panel's observed-vs-predicted scatter and R2/MSE for any chosen k
// with one client-side prefix mean per query; no brain feature, distance, or
// participant identifier is ever shipped.

import { z } from "zod";
import type { DataResult } from "./components/types";

const IDENTIFIER_TOKEN = /(^|_)(id|ids|uid|sub|subject|participant|site|mrn|name|dob)($|_)/i;

export const knnAbcDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("knn-abc"),
    source: z
      .object({
        pinnedCommit: z.string().min(1),
        brainTableSha256: z.string().min(1),
        phenotypeTableSha256: z.string().min(1),
      })
      .passthrough(),
    target: z
      .object({
        name: z.string().min(1),
        label: z.string().min(1),
        unit: z.string().min(1),
      })
      .passthrough(),
    featureRecipe: z
      .object({
        bundle: z.string().min(1),
        measures: z.array(z.string().min(1)).min(1),
        featureCount: z.number().int().positive(),
      })
      .passthrough(),
    split: z
      .object({
        nTrain: z.number().int().positive(),
        nTest: z.number().int().positive(),
        kMax: z.number().int().positive(),
      })
      .passthrough(),
    selectedKFromAudit: z.number().int().positive(),
    observedTrain: z.array(z.number().finite()).min(1),
    observedTest: z.array(z.number().finite()).min(1),
    neighborTargetsA: z.array(z.array(z.number().finite())).min(1),
    neighborTargetsB: z.array(z.array(z.number().finite())).min(1),
    neighborTargetsC: z.array(z.array(z.number().finite())).min(1),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    for (const key of Object.keys(data)) {
      if (IDENTIFIER_TOKEN.test(key)) add([key], `identifier-shaped top-level key "${key}" is not allowed`);
    }

    const { nTrain, nTest, kMax } = data.split;
    if (kMax !== Math.min(nTrain, nTest)) {
      add(["split", "kMax"], `kMax must equal min(nTrain, nTest) = ${Math.min(nTrain, nTest)}`);
    }
    if (data.observedTrain.length !== nTrain) {
      add(["observedTrain"], `expected ${nTrain} values, got ${data.observedTrain.length}`);
    }
    if (data.observedTest.length !== nTest) {
      add(["observedTest"], `expected ${nTest} values, got ${data.observedTest.length}`);
    }

    const panels: [string, number[][], number][] = [
      ["neighborTargetsA", data.neighborTargetsA, nTest],
      ["neighborTargetsB", data.neighborTargetsB, nTrain],
      ["neighborTargetsC", data.neighborTargetsC, nTest],
    ];
    for (const [name, rows, expectedRows] of panels) {
      if (rows.length !== expectedRows) {
        add([name], `expected ${expectedRows} rows, got ${rows.length}`);
        continue;
      }
      for (let i = 0; i < rows.length; i += 1) {
        if (rows[i]!.length !== kMax) {
          add([name, i], `row must have kMax (${kMax}) entries, got ${rows[i]!.length}`);
          break;
        }
      }
    }

    // k=1 structural endpoint: B and C are exact resubstitution.
    if (data.neighborTargetsB.length === data.observedTrain.length) {
      for (let i = 0; i < data.observedTrain.length; i += 1) {
        if (Math.abs(data.neighborTargetsB[i]![0]! - data.observedTrain[i]!) > 1e-6) {
          add(["neighborTargetsB", i, 0], "k=1 (B) must equal observedTrain -- each training row is its own nearest neighbour");
          break;
        }
      }
    }
    if (data.neighborTargetsC.length === data.observedTest.length) {
      for (let i = 0; i < data.observedTest.length; i += 1) {
        if (Math.abs(data.neighborTargetsC[i]![0]! - data.observedTest[i]!) > 1e-6) {
          add(["neighborTargetsC", i, 0], "k=1 (C) must equal observedTest -- each test row is its own nearest neighbour");
          break;
        }
      }
    }

    if (data.selectedKFromAudit < 1 || data.selectedKFromAudit > kMax) {
      add(["selectedKFromAudit"], `selectedKFromAudit must be within [1, ${kMax}]`);
    }
  });

export type KnnAbcData = z.infer<typeof knnAbcDataSchema>;

export function parseKnnAbcData(raw: unknown): DataResult<KnnAbcData> {
  const parsed = knnAbcDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid KNN A/B/C data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
