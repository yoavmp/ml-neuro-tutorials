// Pure, unit-tested helpers for the Exercise 3 "vary k" KNN activity. No DOM,
// no Plotly. r2Score / meanSquaredError / sharedAxisRange are the same generic
// metrics regression-compare.ts already defines; reused here rather than
// duplicated.

export { r2Score, meanSquaredError, sharedAxisRange } from "./regression-compare";

/**
 * Predicted value for one query point at neighbour count `k`: the mean of the
 * first `k` entries of `sortedTargets` (its fitting-set neighbours, nearest
 * first). O(k), not O(n_fit): callers looping over k should prefer
 * `cumulativeMeans`, which computes every k in one O(n_fit) pass.
 */
export function predictForK(sortedTargets: readonly number[], k: number): number {
  if (k < 1 || k > sortedTargets.length) {
    throw new Error(`predictForK: k=${k} out of range [1, ${sortedTargets.length}]`);
  }
  let sum = 0;
  for (let i = 0; i < k; i += 1) sum += sortedTargets[i]!;
  return sum / k;
}

/** Cumulative mean of the first 1..n entries: `result[k-1]` is the k-nearest-
 *  neighbour prediction from `sortedTargets` (nearest first). One O(n) pass. */
export function cumulativeMeans(sortedTargets: readonly number[]): number[] {
  const out = new Array<number>(sortedTargets.length);
  let sum = 0;
  for (let i = 0; i < sortedTargets.length; i += 1) {
    sum += sortedTargets[i]!;
    out[i] = sum / (i + 1);
  }
  return out;
}

/** Predicted values for every query point at a fixed `k`, from each point's
 *  neighbour-ordered target array (nearest first). */
export function predictAllForK(neighborTargetsByProximity: readonly (readonly number[])[], k: number): number[] {
  return neighborTargetsByProximity.map((row) => predictForK(row, k));
}

/**
 * WP14 §4.8: an empirical **training-sample-sensitivity** ("variance") proxy
 * -- the mean, across query points, of the standard deviation of several
 * training samples' predictions for that point. This is NOT the formal
 * population variance term of the bias-variance decomposition (that would
 * require repeated draws from the true data-generating process, which ABIDE
 * does not provide); it is one honest, observable stand-in computed from a
 * handful of deterministic alternative training-set selections.
 */
export function varianceProxy(samplePredictions: readonly (readonly number[])[]): number {
  if (samplePredictions.length < 2) {
    throw new Error("varianceProxy needs at least two training samples");
  }
  const nQuery = samplePredictions[0]!.length;
  let total = 0;
  for (let i = 0; i < nQuery; i += 1) {
    const vals = samplePredictions.map((sample) => sample[i]!);
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    const variance = vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length;
    total += Math.sqrt(variance);
  }
  return total / nQuery;
}

/**
 * WP14 §4.9: an observable **bias-like underfitting proxy** -- the ordinary
 * least-squares slope of (ensemble-mean prediction) regressed on (observed
 * value). A slope near 1 means predictions still track the observed value
 * closely; a slope near 0 means predictions have flattened toward a
 * constant, the signature of an oversmoothed (large-k) fit. This is NOT
 * formal bias-squared: ABIDE does not reveal the true population function,
 * and the observed age-level outcomes still contain irreducible variation
 * this slope cannot separate out.
 */
export function calibrationSlope(observed: readonly number[], ensemblePredicted: readonly number[]): number {
  if (observed.length !== ensemblePredicted.length || observed.length === 0) {
    throw new Error("calibrationSlope: observed and ensemblePredicted must be the same non-empty length");
  }
  const n = observed.length;
  const meanObs = observed.reduce((a, b) => a + b, 0) / n;
  const meanPred = ensemblePredicted.reduce((a, b) => a + b, 0) / n;
  let cov = 0;
  let varObs = 0;
  for (let i = 0; i < n; i += 1) {
    cov += (observed[i]! - meanObs) * (ensemblePredicted[i]! - meanPred);
    varObs += (observed[i]! - meanObs) ** 2;
  }
  return varObs > 0 ? cov / varObs : 0;
}

/** Ensemble-mean prediction (average across training samples) for every
 *  query point at a fixed `k`. */
export function ensembleMeanForK(
  samples: readonly (readonly (readonly number[])[])[],
  k: number,
): number[] {
  const perSample = samples.map((s) => predictAllForK(s, k));
  const nQuery = perSample[0]!.length;
  const out = new Array<number>(nQuery);
  for (let i = 0; i < nQuery; i += 1) {
    out[i] = perSample.reduce((sum, sample) => sum + sample[i]!, 0) / perSample.length;
  }
  return out;
}
