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
