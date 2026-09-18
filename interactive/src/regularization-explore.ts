// Pure, unit-tested helpers for the Exercise 5 "Shrink the Coefficients"
// activity. No DOM, no Plotly. Every (model, alpha) configuration's numbers
// are precomputed by scripts/export_regularization_widget.py; these helpers
// only pick out the right precomputed entry and format it for display.

/** Inclusive [min, max] over the given values, padded by `padFrac` of the
 *  range, for a shared observed-vs-predicted diagonal. */
export function sharedAxisRange(values: readonly number[], padFrac = 0.05): [number, number] {
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

/** Compact display string for a regularization strength, e.g. `0.215` or
 *  `3.16e+2`. Values in [0.01, 10000) print as fixed-precision decimals; more
 *  extreme values switch to exponential notation so the label never grows
 *  unreadably long at either end of a log-scale grid. */
export function formatAlpha(alpha: number): string {
  if (!Number.isFinite(alpha) || alpha <= 0) return String(alpha);
  if (alpha >= 0.01 && alpha < 10000) {
    const fixed = alpha.toPrecision(3);
    return fixed.includes(".") ? fixed.replace(/0+$/, "").replace(/\.$/, "") : fixed;
  }
  return alpha.toExponential(2);
}

/** Clamp a slider/select index into `[0, length - 1]`. */
export function clampAlphaIndex(index: number, length: number): number {
  if (!Number.isFinite(index)) return 0;
  return Math.min(length - 1, Math.max(0, Math.round(index)));
}
