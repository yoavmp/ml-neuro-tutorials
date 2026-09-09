// Pure correlation maths. No DOM, no Plotly, no fetch — unit tested in
// tests/correlation.test.ts. The component plots and labels exactly what this
// returns.
//
// "Missing" means anything that is not a finite number (JSON `null`, and
// defensively NaN / Infinity / non-number). A pair (row) contributes to a
// correlation only when BOTH variables are finite on that row. Group-specific
// results use the same pairwise-complete rule within each group.
//
// Neither Pearson nor Spearman here implies causation; that caveat lives in the
// teaching copy, not the maths.

export type NumCell = number | null | undefined;

export type CorrelationMethod = "pearson" | "spearman";

export const REASON_TOO_FEW =
  "Fewer than 3 participants have both variables recorded, so a correlation is not defined.";
export const REASON_NO_VARIANCE =
  "One of the variables does not vary in this subset, so a correlation is not defined.";

export interface MissingBreakdown {
  /** Rows in the full sample. */
  total: number;
  /** Rows where X is not a finite number. */
  x: number;
  /** Rows where Y is not a finite number. */
  y: number;
  /** Rows dropped because X or Y (or both) is not finite. */
  either: number;
}

export interface CorrelationOutcome {
  /** Pairwise-complete participant count this coefficient is based on. */
  n: number;
  /** The coefficient, or null when it is not defined. */
  r: number | null;
  /** Human-readable reason when `r` is null; otherwise null. */
  reason: string | null;
}

export interface GroupOutcome extends CorrelationOutcome {
  /** Stable key = `String(code)`; used for deterministic ordering / testids. */
  key: string;
  /** The group's numeric code in the grouping column. */
  code: number;
  /** Readable label from the config value mapping. */
  label: string;
}

export interface CorrelationPoints {
  x: number[];
  y: number[];
  /** Grouping code per point (aligned to x / y), or null when ungrouped. */
  group: number[] | null;
}

export interface CorrelationResult {
  method: CorrelationMethod;
  /** Overall pairwise-complete result across every retained row. */
  overall: CorrelationOutcome;
  missing: MissingBreakdown;
  /** Pairwise-complete observations, for the scatter plot. */
  points: CorrelationPoints;
  /**
   * Per-group results in the exact order of `grouping.values`, or null when no
   * grouping was requested. A configured group with no data still appears (with
   * `n: 0` and a reason).
   */
  groups: GroupOutcome[] | null;
}

export interface GroupingInput {
  /** Column name, only used in error messages. */
  field: string;
  /** Grouping code per row, aligned to the X / Y columns. */
  codes: ReadonlyArray<NumCell>;
  /** Ordered code→label mapping; also fixes the output group order. */
  values: ReadonlyArray<{ code: number; label: string }>;
}

function isFiniteNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

/** Throw unless every column is the same length as the first. */
export function assertAligned(
  columns: ReadonlyArray<{ name: string; length: number }>,
): void {
  if (columns.length === 0) return;
  const expected = columns[0]!.length;
  for (const col of columns) {
    if (col.length !== expected) {
      throw new Error(
        `Column "${col.name}" has ${col.length} values but "${columns[0]!.name}" has ${expected}.`,
      );
    }
  }
}

export interface PairwiseComplete {
  x: number[];
  y: number[];
  n: number;
  missing: MissingBreakdown;
}

/**
 * Extract the rows where both `xCol` and `yCol` are finite numbers.
 * Throws if the two columns differ in length.
 */
export function pairwiseComplete(
  xCol: ReadonlyArray<NumCell>,
  yCol: ReadonlyArray<NumCell>,
): PairwiseComplete {
  assertAligned([
    { name: "x", length: xCol.length },
    { name: "y", length: yCol.length },
  ]);
  const total = xCol.length;
  const x: number[] = [];
  const y: number[] = [];
  let missX = 0;
  let missY = 0;
  let missEither = 0;
  for (let i = 0; i < total; i += 1) {
    const xv = xCol[i];
    const yv = yCol[i];
    const xok = isFiniteNumber(xv);
    const yok = isFiniteNumber(yv);
    if (!xok) missX += 1;
    if (!yok) missY += 1;
    if (!xok || !yok) {
      missEither += 1;
      continue;
    }
    x.push(xv);
    y.push(yv);
  }
  return {
    x,
    y,
    n: x.length,
    missing: { total, x: missX, y: missY, either: missEither },
  };
}

/**
 * Pearson product-moment correlation of two equal-length numeric arrays.
 * Returns null for n < 3 or when either array has zero variance.
 */
export function pearson(x: ReadonlyArray<number>, y: ReadonlyArray<number>): number | null {
  const n = x.length;
  if (n !== y.length) {
    throw new Error(`pearson: length mismatch (${n} vs ${y.length}).`);
  }
  if (n < 3) return null;
  let sx = 0;
  let sy = 0;
  for (let i = 0; i < n; i += 1) {
    sx += x[i]!;
    sy += y[i]!;
  }
  const mx = sx / n;
  const my = sy / n;
  let cov = 0;
  let vx = 0;
  let vy = 0;
  for (let i = 0; i < n; i += 1) {
    const dx = x[i]! - mx;
    const dy = y[i]! - my;
    cov += dx * dy;
    vx += dx * dx;
    vy += dy * dy;
  }
  if (vx === 0 || vy === 0) return null;
  const r = cov / Math.sqrt(vx * vy);
  // Guard against tiny floating-point overshoot past ±1.
  if (r > 1) return 1;
  if (r < -1) return -1;
  return r;
}

/** Fractional (1-based) ranks with ties resolved to the average rank. */
export function averageRanks(values: ReadonlyArray<number>): number[] {
  const order = values.map((_, i) => i).sort((a, b) => values[a]! - values[b]!);
  const ranks = new Array<number>(values.length);
  let i = 0;
  while (i < order.length) {
    let j = i;
    while (j + 1 < order.length && values[order[j + 1]!]! === values[order[i]!]!) {
      j += 1;
    }
    const avg = (i + j) / 2 + 1; // positions i..j share this average rank
    for (let k = i; k <= j; k += 1) ranks[order[k]!] = avg;
    i = j + 1;
  }
  return ranks;
}

/**
 * Spearman rank correlation: Pearson on the average-rank transforms of each
 * array. Returns null for n < 3 or when either array is constant (no rank
 * variation).
 */
export function spearman(x: ReadonlyArray<number>, y: ReadonlyArray<number>): number | null {
  if (x.length !== y.length) {
    throw new Error(`spearman: length mismatch (${x.length} vs ${y.length}).`);
  }
  if (x.length < 3) return null;
  return pearson(averageRanks(x), averageRanks(y));
}

function coefficient(
  x: ReadonlyArray<number>,
  y: ReadonlyArray<number>,
  method: CorrelationMethod,
): CorrelationOutcome {
  const n = x.length;
  if (n < 3) return { n, r: null, reason: REASON_TOO_FEW };
  const r = method === "pearson" ? pearson(x, y) : spearman(x, y);
  if (r === null) return { n, r: null, reason: REASON_NO_VARIANCE };
  return { n, r, reason: null };
}

/**
 * Overall + optional group-specific correlation for two numeric columns.
 *
 * @param xCol / yCol aligned numeric columns (`null` / non-finite = missing).
 * @param method "pearson" or "spearman".
 * @param grouping optional; when present, its `codes` must align with the
 *   columns and its `values` fix the group order in the result.
 *
 * Throws only on a column-length mismatch (a data-integrity bug); every
 * statistical edge case is reported as a null coefficient with a reason.
 */
export function computeCorrelation(
  xCol: ReadonlyArray<NumCell>,
  yCol: ReadonlyArray<NumCell>,
  method: CorrelationMethod,
  grouping?: GroupingInput | null,
): CorrelationResult {
  const cols = [
    { name: "x", length: xCol.length },
    { name: "y", length: yCol.length },
  ];
  if (grouping) cols.push({ name: grouping.field, length: grouping.codes.length });
  assertAligned(cols);

  const total = xCol.length;
  const pw = pairwiseComplete(xCol, yCol);
  const overall = coefficient(pw.x, pw.y, method);

  // Pairwise-complete points, with their group code when grouping is active.
  const pointGroups: number[] = [];
  if (grouping) {
    for (let i = 0; i < total; i += 1) {
      if (isFiniteNumber(xCol[i]) && isFiniteNumber(yCol[i])) {
        const code = grouping.codes[i];
        pointGroups.push(isFiniteNumber(code) ? code : Number.NaN);
      }
    }
  }
  const points: CorrelationPoints = {
    x: pw.x,
    y: pw.y,
    group: grouping ? pointGroups : null,
  };

  let groups: GroupOutcome[] | null = null;
  if (grouping) {
    groups = grouping.values.map(({ code, label }) => {
      const gx: number[] = [];
      const gy: number[] = [];
      for (let i = 0; i < total; i += 1) {
        if (grouping.codes[i] !== code) continue;
        const xv = xCol[i];
        const yv = yCol[i];
        if (isFiniteNumber(xv) && isFiniteNumber(yv)) {
          gx.push(xv);
          gy.push(yv);
        }
      }
      return { key: String(code), code, label, ...coefficient(gx, gy, method) };
    });
  }

  return { method, overall, missing: pw.missing, points, groups };
}
