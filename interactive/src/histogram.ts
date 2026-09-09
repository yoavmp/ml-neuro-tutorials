// Pure histogram binning. No DOM, no Plotly, no fetch — unit tested in
// tests/histogram.test.ts. The component plots exactly what this returns using a
// Plotly *bar* trace, so the number of bins and the counts are precisely the
// tested values (never delegated to a Plotly histogram trace).

export type HistogramKind = "normal" | "constant" | "empty";

export interface HistogramBins {
  /** Bin edges, ascending. Length = counts.length + 1 (empty: []). */
  binEdges: number[];
  /** Bin midpoints. Length = counts.length. */
  binCenters: number[];
  /** Human-readable interval labels, e.g. "[5, 8)"; last bin is closed "[…, …]". */
  binLabels: string[];
  /** Observation count per bin. Sums to availableN. */
  counts: number[];
  /** Number of non-null, finite observations. */
  availableN: number;
  /** Number of null observations. */
  missingN: number;
  /** Minimum / maximum observed value, or null when there is no data. */
  min: number | null;
  max: number | null;
  kind: HistogramKind;
}

function formatNumber(value: number): string {
  if (Number.isInteger(value)) return String(value);
  return (Math.round(value * 100) / 100).toString();
}

/**
 * Bin `observations` (finite numbers or `null` for missing) into `requestedBins`
 * equal-width bins.
 *
 * Deterministic edge cases:
 *  - **empty / all-missing** (`availableN === 0`): `kind: "empty"`, no bins,
 *    `min`/`max` null. The caller renders an explicit "no data" message.
 *  - **constant** (`min === max`): `kind: "constant"`, exactly one unit-wide bin
 *    centred on the value holding every observation. Never divides by zero.
 *  - **normal**: exactly `requestedBins` equal-width bins spanning `[min, max]`,
 *    with the maximum included in the final bin.
 *
 * Throws `RangeError` if `requestedBins` is not a positive integer, and
 * `TypeError` if a non-null observation is not a finite number.
 */
export function computeHistogram(
  observations: ReadonlyArray<number | null>,
  requestedBins: number,
): HistogramBins {
  if (!Number.isInteger(requestedBins) || requestedBins < 1) {
    throw new RangeError(
      `requestedBins must be a positive integer, got ${JSON.stringify(requestedBins)}`,
    );
  }

  let missingN = 0;
  const present: number[] = [];
  for (const value of observations) {
    if (value === null) {
      missingN += 1;
      continue;
    }
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TypeError(
        `histogram observations must be finite numbers or null; got ${JSON.stringify(value)}`,
      );
    }
    present.push(value);
  }

  const availableN = present.length;

  if (availableN === 0) {
    return {
      binEdges: [],
      binCenters: [],
      binLabels: [],
      counts: [],
      availableN: 0,
      missingN,
      min: null,
      max: null,
      kind: "empty",
    };
  }

  let min = present[0]!;
  let max = present[0]!;
  for (const value of present) {
    if (value < min) min = value;
    if (value > max) max = value;
  }

  if (min === max) {
    const lo = min - 0.5;
    const hi = min + 0.5;
    return {
      binEdges: [lo, hi],
      binCenters: [min],
      binLabels: [`[${formatNumber(min)}]`],
      counts: [availableN],
      availableN,
      missingN,
      min,
      max,
      kind: "constant",
    };
  }

  const nbins = requestedBins;
  const width = (max - min) / nbins;

  const binEdges: number[] = new Array<number>(nbins + 1);
  for (let i = 0; i < nbins; i += 1) binEdges[i] = min + i * width;
  binEdges[nbins] = max; // exact, no floating-point drift at the top edge

  const counts: number[] = new Array<number>(nbins).fill(0);
  for (const value of present) {
    let index = Math.floor((value - min) / width);
    if (index < 0) index = 0;
    if (index >= nbins) index = nbins - 1; // maximum belongs to the final bin
    counts[index] = (counts[index] ?? 0) + 1;
  }

  const binCenters: number[] = new Array<number>(nbins);
  const binLabels: string[] = new Array<string>(nbins);
  for (let i = 0; i < nbins; i += 1) {
    const left = binEdges[i] ?? min;
    const right = binEdges[i + 1] ?? max;
    binCenters[i] = (left + right) / 2;
    const close = i === nbins - 1 ? "]" : ")";
    binLabels[i] = `[${formatNumber(left)}, ${formatNumber(right)}${close}`;
  }

  return {
    binEdges,
    binCenters,
    binLabels,
    counts,
    availableN,
    missingN,
    min,
    max,
    kind: "normal",
  };
}
