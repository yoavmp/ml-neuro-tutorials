// Pure row-selection + view-summary maths for the `table-inspection` activity.
// No DOM, no Plotly, no fetch — unit tested in tests/table-inspection.test.ts.
// The component renders exactly what this returns.
//
// The three inspection methods mirror pandas:
//   head(n)   -> the first n rows, in table order          (deterministic)
//   tail(n)   -> the last n rows, in table order           (deterministic)
//   sample(n) -> n rows drawn without replacement using a seeded PRNG, then
//                returned in ascending table order so the view is stable and
//                comparable to head()/tail(). The seed is fixed in the config,
//                so the first view a student sees is always the same; a
//                different seed (the "Reshuffle" control) gives a different
//                deterministic draw. This is NOT the same row set pandas'
//                `sample(n, random_state=...)` returns — pandas uses NumPy's
//                Mersenne Twister — only the same idea.

import type { CellValue } from "./retention";

export type InspectionMethod = "head" | "tail" | "sample";

export const INSPECTION_METHODS: readonly InspectionMethod[] = [
  "head",
  "tail",
  "sample",
] as const;

export interface ViewSummary {
  /** Rows actually shown (min(requested, totalRows)). */
  rowCount: number;
  /** Distinct site labels present in the shown rows, in first-appearance order. */
  sites: string[];
  /** `sites.length`. */
  siteCount: number;
  /** Missing (null) cells across the shown rows and the displayed columns. */
  missingCells: number;
  /** `rowCount * displayColumns.length`. */
  totalCells: number;
}

/**
 * mulberry32 — a tiny, fast, well-distributed 32-bit PRNG. Deterministic for a
 * given seed and identical across every browser (pure integer maths, no
 * `Math.random`). Returns a float in [0, 1).
 */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function next(): number {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), 1 | t);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * A seeded, without-replacement draw of `k` row indices from `[0, totalRows)`,
 * returned sorted ascending. Uses a full Fisher–Yates shuffle so the result is
 * a genuine uniform sample and does not depend on `k` beyond the final slice.
 * `k` is clamped to `[0, totalRows]`.
 */
export function sampleRowIndices(
  totalRows: number,
  k: number,
  seed: number,
): number[] {
  if (!Number.isInteger(totalRows) || totalRows < 0) {
    throw new Error(`totalRows must be a non-negative integer, got ${totalRows}`);
  }
  const want = Math.max(0, Math.min(k, totalRows));
  const order = Array.from({ length: totalRows }, (_, i) => i);
  const rand = mulberry32(seed);
  for (let i = totalRows - 1; i > 0; i -= 1) {
    const j = Math.floor(rand() * (i + 1));
    const tmp = order[i] as number;
    order[i] = order[j] as number;
    order[j] = tmp;
  }
  return order.slice(0, want).sort((x, y) => x - y);
}

/**
 * The row indices a given inspection method returns, in the order they should
 * be displayed. `requested` is clamped to `[0, totalRows]`.
 *
 * Throws on an unknown method or a non-integer / negative `totalRows`.
 */
export function selectRowIndices(
  method: InspectionMethod,
  totalRows: number,
  requested: number,
  seed: number,
): number[] {
  if (!Number.isInteger(totalRows) || totalRows < 0) {
    throw new Error(`totalRows must be a non-negative integer, got ${totalRows}`);
  }
  const k = Math.max(0, Math.min(requested, totalRows));
  if (method === "head") {
    return Array.from({ length: k }, (_, i) => i);
  }
  if (method === "tail") {
    return Array.from({ length: k }, (_, i) => totalRows - k + i);
  }
  if (method === "sample") {
    return sampleRowIndices(totalRows, k, seed);
  }
  throw new Error(`Unknown inspection method: "${method}"`);
}

/**
 * Summarise a view: which sites it touches and how many missing cells it holds
 * over the displayed columns. `siteLabels` is the site-grouping label for every
 * row of the full table; `columns` is the aligned columnar data; `displayColumns`
 * is the ordered list of column names actually shown in the table.
 *
 * Throws if a display column is absent from `columns`, or if a referenced row
 * index is out of range, or if a site label is missing.
 */
export function summariseView(
  columns: Readonly<Record<string, ReadonlyArray<CellValue>>>,
  siteLabels: ReadonlyArray<string>,
  displayColumns: ReadonlyArray<string>,
  rowIndices: ReadonlyArray<number>,
): ViewSummary {
  for (const name of displayColumns) {
    if (!Object.prototype.hasOwnProperty.call(columns, name)) {
      throw new Error(`Display column "${name}" is not present in the data.`);
    }
  }

  const sites: string[] = [];
  const seen = new Set<string>();
  let missingCells = 0;

  for (const rowIndex of rowIndices) {
    if (rowIndex < 0 || rowIndex >= siteLabels.length) {
      throw new Error(`Row index ${rowIndex} is out of range.`);
    }
    const label = siteLabels[rowIndex];
    if (typeof label !== "string" || label.trim() === "") {
      throw new Error(`Missing site label at row ${rowIndex}.`);
    }
    if (!seen.has(label)) {
      seen.add(label);
      sites.push(label);
    }
    for (const name of displayColumns) {
      const value = (columns[name] as ReadonlyArray<CellValue>)[rowIndex];
      if (value === null || value === undefined) missingCells += 1;
    }
  }

  return {
    rowCount: rowIndices.length,
    sites,
    siteCount: sites.length,
    missingCells,
    totalCells: rowIndices.length * displayColumns.length,
  };
}

/** Format one cell for display. `null`/`undefined` -> the em-dash placeholder. */
export function formatCell(value: CellValue | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : String(Math.round(value * 100) / 100);
  }
  return String(value);
}
