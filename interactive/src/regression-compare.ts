// Pure, unit-tested helpers for the Exercise II model-comparison activity.
// No DOM, no Plotly. The component (components/regression-compare.ts) turns the
// selected catalog entry into a scatter of observed vs out-of-fold predicted
// values; these functions do the arithmetic and the lookups.

export interface ScatterPoint {
  observed: number;
  predicted: number;
  fold: number;
}

/** Coefficient of determination R^2 = 1 - SS_res / SS_tot. Not clamped:
 *  a value below 0 is legitimate and means "worse than predicting the mean". */
export function r2Score(observed: readonly number[], predicted: readonly number[]): number {
  if (observed.length !== predicted.length || observed.length === 0) {
    throw new Error("r2Score: observed and predicted must be non-empty and equal length");
  }
  const mean = observed.reduce((a, b) => a + b, 0) / observed.length;
  let ssRes = 0;
  let ssTot = 0;
  for (let i = 0; i < observed.length; i += 1) {
    const o = observed[i]!;
    ssRes += (o - predicted[i]!) ** 2;
    ssTot += (o - mean) ** 2;
  }
  if (ssTot === 0) throw new Error("r2Score: target has zero variance");
  return 1 - ssRes / ssTot;
}

export function meanSquaredError(observed: readonly number[], predicted: readonly number[]): number {
  if (observed.length !== predicted.length || observed.length === 0) {
    throw new Error("meanSquaredError: observed and predicted must be non-empty and equal length");
  }
  let sum = 0;
  for (let i = 0; i < observed.length; i += 1) sum += (observed[i]! - predicted[i]!) ** 2;
  return sum / observed.length;
}

/** Zip observed / predicted / fold into scatter points, in cohort row order. */
export function scatterPoints(
  observed: readonly number[],
  predicted: readonly number[],
  foldOf: readonly number[],
): ScatterPoint[] {
  if (observed.length !== predicted.length || observed.length !== foldOf.length) {
    throw new Error("scatterPoints: all three arrays must be the same length");
  }
  return observed.map((o, i) => ({ observed: o, predicted: predicted[i]!, fold: foldOf[i]! }));
}

/** Inclusive [min, max] over both arrays, padded by `padFrac` of the range, so
 *  Model A and Model B panels can share identical axis limits. */
export function sharedAxisRange(
  values: readonly number[],
  padFrac = 0.05,
): [number, number] {
  if (values.length === 0) throw new Error("sharedAxisRange: no values");
  let lo = values[0]!;
  let hi = values[0]!;
  for (const v of values) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const pad = (hi - lo || 1) * padFrac;
  return [lo - pad, hi + pad];
}

export interface CatalogKeyParts {
  bundle: string;
  measures: string[];
}

/** Deterministic catalog key: `<bundle>__<measure>+<measure>`. */
export function catalogKey(parts: CatalogKeyParts): string {
  return `${parts.bundle}__${parts.measures.join("+")}`;
}
