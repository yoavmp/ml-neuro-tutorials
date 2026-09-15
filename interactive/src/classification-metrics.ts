// Pure, DOM-free classification metrics shared by both Exercise 4 activities
// (WP17). No sklearn re-implementation shortcuts: confusion matrix, ROC
// curve, and AUC are all computed directly from labels + scores, the same
// definitions scikit-learn uses, so a chosen threshold recomputes a REAL
// confusion matrix every time -- never a relabelled canned result.

export interface ConfusionCounts {
  readonly tp: number;
  readonly tn: number;
  readonly fp: number;
  readonly fn: number;
}

/** Positive class = 1. `score >= threshold` predicts the positive class. */
export function predictAtThreshold(scores: readonly number[], threshold: number): number[] {
  return scores.map((s) => (s >= threshold ? 1 : 0));
}

export function confusionMatrix(labels: readonly number[], predicted: readonly number[]): ConfusionCounts {
  if (labels.length !== predicted.length) {
    throw new Error(`confusionMatrix: labels (${labels.length}) and predicted (${predicted.length}) length mismatch`);
  }
  let tp = 0;
  let tn = 0;
  let fp = 0;
  let fn = 0;
  for (let i = 0; i < labels.length; i += 1) {
    const label = labels[i]!;
    const pred = predicted[i]!;
    if (label === 1 && pred === 1) tp += 1;
    else if (label === 1 && pred === 0) fn += 1;
    else if (label === 0 && pred === 1) fp += 1;
    else tn += 1;
  }
  return { tp, tn, fp, fn };
}

export function accuracyFromCounts(c: ConfusionCounts): number {
  const total = c.tp + c.tn + c.fp + c.fn;
  return total === 0 ? NaN : (c.tp + c.tn) / total;
}

/** Sensitivity / recall: proportion of actual positives correctly identified. */
export function sensitivityFromCounts(c: ConfusionCounts): number {
  const denom = c.tp + c.fn;
  return denom === 0 ? NaN : c.tp / denom;
}

/** Specificity: proportion of actual negatives correctly identified. */
export function specificityFromCounts(c: ConfusionCounts): number {
  const denom = c.tn + c.fp;
  return denom === 0 ? NaN : c.tn / denom;
}

export interface RocPoint {
  readonly fpr: number;
  readonly tpr: number;
  /** The score threshold this point's cumulative counts stop at (informational only). */
  readonly threshold: number;
}

/**
 * Standard step ROC curve: sort by descending score, sweep the threshold
 * down through every distinct score value, accumulating true/false positive
 * counts. Tied scores are grouped so they contribute one point, not a
 * staircase artefact. Returns [] if only one class is present (ROC/AUC
 * undefined).
 */
export function rocCurve(labels: readonly number[], scores: readonly number[]): RocPoint[] {
  if (labels.length !== scores.length) {
    throw new Error(`rocCurve: labels (${labels.length}) and scores (${scores.length}) length mismatch`);
  }
  const nPos = labels.filter((l) => l === 1).length;
  const nNeg = labels.length - nPos;
  if (nPos === 0 || nNeg === 0) return [];

  const order = labels.map((_, i) => i).sort((a, b) => scores[b]! - scores[a]!);
  const points: RocPoint[] = [{ fpr: 0, tpr: 0, threshold: Number.POSITIVE_INFINITY }];
  let tp = 0;
  let fp = 0;
  let i = 0;
  while (i < order.length) {
    const currentScore = scores[order[i]!]!;
    while (i < order.length && scores[order[i]!]! === currentScore) {
      if (labels[order[i]!] === 1) tp += 1;
      else fp += 1;
      i += 1;
    }
    points.push({ fpr: fp / nNeg, tpr: tp / nPos, threshold: currentScore });
  }
  return points;
}

/** Trapezoidal area under an already-computed (ascending-fpr) ROC curve. */
export function aucTrapezoidal(points: readonly RocPoint[]): number {
  if (points.length < 2) return NaN;
  const sorted = [...points].sort((a, b) => a.fpr - b.fpr);
  let area = 0;
  for (let i = 1; i < sorted.length; i += 1) {
    const x0 = sorted[i - 1]!.fpr;
    const x1 = sorted[i]!.fpr;
    const y0 = sorted[i - 1]!.tpr;
    const y1 = sorted[i]!.tpr;
    area += ((x1 - x0) * (y0 + y1)) / 2;
  }
  return area;
}

/** The (FPR, TPR) point on the ROC curve for one chosen threshold. */
export function rocPointAtThreshold(
  labels: readonly number[],
  scores: readonly number[],
  threshold: number,
): { fpr: number; tpr: number } {
  const predicted = predictAtThreshold(scores, threshold);
  const c = confusionMatrix(labels, predicted);
  return {
    fpr: c.fp + c.tn === 0 ? NaN : c.fp / (c.fp + c.tn),
    tpr: c.tp + c.fn === 0 ? NaN : c.tp / (c.tp + c.fn),
  };
}

/** Proportion of participants (by score/threshold) predicted positive. */
export function percentPredictedPositive(scores: readonly number[], threshold: number): number {
  if (scores.length === 0) return NaN;
  const predicted = predictAtThreshold(scores, threshold);
  return (predicted.reduce((a, b) => a + b, 0) / scores.length) * 100;
}

/** Accuracy a classifier predicting only the majority class would achieve. */
export function majorityBaselineAccuracy(labels: readonly number[]): number {
  if (labels.length === 0) return NaN;
  const nPos = labels.filter((l) => l === 1).length;
  const nNeg = labels.length - nPos;
  return Math.max(nPos, nNeg) / labels.length;
}
