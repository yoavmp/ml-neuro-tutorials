// Zod schema + parser for Exercise 9's "Explore an SVM Boundary" activity
// data (book/_static/widgets/data/svm_explorer.json, produced by
// scripts/export_svm_explorer_widget.py). DOM / Plotly free so it can be
// unit tested independently of the rendering component.
//
// Two fixed, deterministic synthetic 2-D classification datasets, each with
// its own fixed train/validation split and a precomputed catalogue covering
// every (kernel, C, gamma) combination the student can select (gamma is
// ignored for the linear kernel). decisionGrid rows are compact digit
// strings ("0"/"1" per cell), not nested number arrays -- see the export
// script for why.

import { z } from "zod";
import type { DataResult } from "./components/types";

const point = z
  .object({ id: z.number().int().nonnegative(), x: z.number().finite(), y: z.number().finite(), label: z.union([z.literal(0), z.literal(1)]) })
  .strict();

const datasetName = z.enum(["linear", "nonlinear"]);
const kernelName = z.enum(["linear", "poly", "rbf"]);

const decisionGridRow = z.string().regex(/^[01]+$/, "decisionGrid row must contain only '0'/'1' characters");

const catalogEntry = z
  .object({
    dataset: datasetName,
    kernel: kernelName,
    c: z.number().positive(),
    gamma: z.number().positive().nullable(),
    trainAccuracy: z.number().min(0).max(1),
    valAccuracy: z.number().min(0).max(1),
    nSupportVectors: z.number().int().nonnegative(),
    supportVectorIds: z.array(z.number().int().nonnegative()),
    decisionGrid: z.array(decisionGridRow).min(1),
  })
  .strict()
  .refine((e) => e.nSupportVectors === e.supportVectorIds.length, {
    message: "nSupportVectors must equal supportVectorIds.length",
  });

const datasetEntry = z
  .object({
    points: z.array(point).min(1),
    trainIds: z.array(z.number().int().nonnegative()).min(1),
    valIds: z.array(z.number().int().nonnegative()).min(1),
    gridX: z.array(z.number().finite()).min(1),
    gridY: z.array(z.number().finite()).min(1),
    catalog: z.record(z.string(), catalogEntry),
  })
  .strict();

export const svmExplorerDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("svm-explorer"),
    syntheticDataNote: z.string().min(1),
    kernelOptions: z.array(kernelName).min(1),
    polyDegree: z.number().int().positive(),
    cGrid: z.array(z.number().positive()).min(1),
    gammaGrid: z.array(z.number().positive()).min(1),
    datasets: z.record(datasetName, datasetEntry),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const add = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };
    for (const [name, d] of Object.entries(data.datasets)) {
      const n = d.points.length;
      if (d.trainIds.length + d.valIds.length !== n) {
        add(["datasets", name], "trainIds + valIds must partition every point exactly once");
      }
      if (d.gridX.length !== d.gridY.length) {
        add(["datasets", name], "gridX and gridY must have the same length");
      }
      const trainSet = new Set(d.trainIds);
      for (const [key, entry] of Object.entries(d.catalog)) {
        if (entry.decisionGrid.length !== d.gridY.length || entry.decisionGrid.some((row) => row.length !== d.gridX.length)) {
          add(["datasets", name, "catalog", key], "decisionGrid dimensions must match gridX/gridY");
        }
        if (!entry.supportVectorIds.every((id) => trainSet.has(id))) {
          add(["datasets", name, "catalog", key], "support vectors must come only from training rows");
        }
      }
    }
  });

export type SvmExplorerData = z.infer<typeof svmExplorerDataSchema>;
export type SvmExplorerCatalogEntry = z.infer<typeof catalogEntry>;
export type SvmExplorerDatasetName = z.infer<typeof datasetName>;
export type SvmExplorerKernelName = z.infer<typeof kernelName>;

function catalogKeyRaw(dataset: string, kernel: string, c: number, gamma: number | null): string {
  const gammaPart = kernel === "linear" ? "na" : String(gamma);
  return `${dataset}|${kernel}|${c}|${gammaPart}`;
}

export function catalogKey(dataset: SvmExplorerDatasetName, kernel: SvmExplorerKernelName, c: number, gamma: number | null): string {
  return catalogKeyRaw(dataset, kernel, c, kernel === "linear" ? null : gamma);
}

export function catalogEntryFor(
  data: SvmExplorerData,
  dataset: SvmExplorerDatasetName,
  kernel: SvmExplorerKernelName,
  c: number,
  gamma: number | null,
): SvmExplorerCatalogEntry {
  const d = data.datasets[dataset];
  if (!d) {
    throw new Error(`svm-explorer: no dataset entry for dataset=${dataset}`);
  }
  const entry = d.catalog[catalogKey(dataset, kernel, c, gamma)];
  if (!entry) {
    throw new Error(`svm-explorer: no catalogue entry for dataset=${dataset} kernel=${kernel} C=${c} gamma=${gamma}`);
  }
  return entry;
}

/** Decode one decisionGrid digit-string row into an array of 0/1 numbers. */
export function decodeDecisionGridRow(row: string): number[] {
  return row.split("").map((ch) => Number(ch));
}

/** Decode the full decisionGrid into a 2-D number array (gridY.length rows x
 * gridX.length columns), for Plotly's contour `z`. */
export function decodeDecisionGrid(grid: readonly string[]): number[][] {
  return grid.map(decodeDecisionGridRow);
}

export function parseSvmExplorerData(raw: unknown): DataResult<SvmExplorerData> {
  const parsed = svmExplorerDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid svm-explorer data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
