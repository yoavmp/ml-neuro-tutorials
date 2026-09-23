// Zod schema + parser for Exercise 8's "Explore PCA and K-Means" activity
// data (book/_static/widgets/data/pca_kmeans_explorer.json, produced by
// scripts/export_pca_kmeans_widget.py). DOM / Plotly free so it can be unit
// tested and reused independently of the rendering component.
//
// PCA is fit once on the real ABIDE cohort (n=1004); PC1/PC2 participant
// scores are stored once and are identical for every retained-PC count
// (PCA components are nested). A precomputed K-means catalogue covers every
// (retainedPc, k, seed) combination in the declared grids; nothing is
// fit live in the browser.

import { z } from "zod";
import type { DataResult } from "./components/types";

const externalVariableName = z.enum(["group", "sex", "site", "age"]);

const catalogEntry = z
  .object({
    retainedPc: z.number().int().positive(),
    k: z.number().int().min(2),
    seed: z.number().int(),
    clusterLabels: z.array(z.number().int().nonnegative()).min(1),
    inertia: z.number().finite().nonnegative(),
    silhouette: z.number().min(-1).max(1).nullable(),
    clusterSizes: z.array(z.number().int().nonnegative()).min(2),
    centersPC1PC2: z.array(z.tuple([z.number().finite(), z.number().finite()])).min(2),
  })
  .strict();

export const pcaKmeansExplorerDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("pca-kmeans-explorer"),
    cohortNote: z.string().min(1),
    nParticipants: z.number().int().positive(),
    pca: z.object({ nComponentsFit: z.number().int().positive(), note: z.string().min(1) }).passthrough(),
    participants: z
      .object({
        pc1: z.array(z.number().finite()).min(1),
        pc2: z.array(z.number().finite()).min(1),
        external: z
          .object({
            group: z.array(z.number().int()).min(1),
            sex: z.array(z.string()).min(1),
            site: z.array(z.string()).min(1),
            age: z.array(z.number().finite()).min(1),
          })
          .strict(),
      })
      .strict(),
    externalVariableLabels: z.record(externalVariableName, z.string().min(1)),
    retainedPcGrid: z.array(z.number().int().positive()).min(1),
    kGrid: z.array(z.number().int().min(2)).min(1),
    seeds: z.array(z.number().int()).min(1),
    nInit: z.number().int().positive(),
    catalog: z.record(z.string(), catalogEntry),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    const n = data.nParticipants;
    if (data.participants.pc1.length !== n || data.participants.pc2.length !== n) {
      add(["participants"], "pc1/pc2 must have exactly nParticipants entries");
    }
    for (const key of ["group", "sex", "site", "age"] as const) {
      if (data.participants.external[key].length !== n) {
        add(["participants", "external", key], "must have exactly nParticipants entries");
      }
    }
    for (const retainedPc of data.retainedPcGrid) {
      for (const k of data.kGrid) {
        for (const seed of data.seeds) {
          const key = `${retainedPc}|${k}|${seed}`;
          const entry = data.catalog[key];
          if (!entry) {
            add(["catalog", key], "missing catalogue entry for a declared (retainedPc, k, seed) combination");
            continue;
          }
          if (entry.clusterLabels.length !== n) {
            add(["catalog", key, "clusterLabels"], "must have exactly nParticipants entries");
          }
          if (entry.clusterSizes.length !== k || entry.clusterSizes.reduce((a, b) => a + b, 0) !== n) {
            add(["catalog", key, "clusterSizes"], `must have ${k} entries summing to nParticipants`);
          }
          if (entry.centersPC1PC2.length !== k) {
            add(["catalog", key, "centersPC1PC2"], `must have exactly ${k} entries`);
          }
        }
      }
    }
  });

export type PcaKmeansExplorerData = z.infer<typeof pcaKmeansExplorerDataSchema>;
export type PcaKmeansCatalogEntry = z.infer<typeof catalogEntry>;
export type PcaKmeansExternalVariableName = z.infer<typeof externalVariableName>;

export function catalogKey(retainedPc: number, k: number, seed: number): string {
  return `${retainedPc}|${k}|${seed}`;
}

export function catalogEntryFor(
  data: PcaKmeansExplorerData,
  retainedPc: number,
  k: number,
  seed: number,
): PcaKmeansCatalogEntry {
  const entry = data.catalog[catalogKey(retainedPc, k, seed)];
  if (!entry) {
    throw new Error(`pca-kmeans-explorer: no catalogue entry for retainedPc=${retainedPc} k=${k} seed=${seed}`);
  }
  return entry;
}

export function externalValuesFor(data: PcaKmeansExplorerData, variable: PcaKmeansExternalVariableName): (string | number)[] {
  return data.participants.external[variable];
}

export function parsePcaKmeansExplorerData(raw: unknown): DataResult<PcaKmeansExplorerData> {
  const parsed = pcaKmeansExplorerDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid pca-kmeans-explorer data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
