// Pure display/derivation logic for Exercise 8's "Explore PCA and K-Means"
// activity (WP33). DOM / Plotly free so it can be unit tested independently
// of ../components/pca-kmeans-explorer.ts, which only wires these functions
// to controls and charts.

// A fixed, mid-saturation categorical palette (distinguishable in both
// light and dark themes against a transparent plot background) for up to 6
// clusters -- the largest k in kGrid. Reused across every panel so a given
// cluster id always maps to the same color.
export const CLUSTER_COLORS = ["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b2", "#937860"];

export function clusterColor(id: number): string {
  if (CLUSTER_COLORS.length === 0) throw new Error("CLUSTER_COLORS must not be empty");
  return CLUSTER_COLORS[((id % CLUSTER_COLORS.length) + CLUSTER_COLORS.length) % CLUSTER_COLORS.length]!;
}

export function sharedAxisRange(values: readonly number[], padFrac = 0.08): [number, number] {
  if (values.length === 0) throw new Error("sharedAxisRange: values must not be empty");
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * padFrac || 1;
  return [min - pad, max + pad];
}

/** Indices of participants assigned to cluster `c` under `labels`. */
export function indicesForCluster(labels: readonly number[], c: number): number[] {
  const out: number[] = [];
  labels.forEach((lbl, i) => {
    if (lbl === c) out.push(i);
  });
  return out;
}

/**
 * For each distinct category in `values` (sorted), the proportion of each
 * cluster's members that fall in that category -- rows sum to <=1 per
 * cluster column (exactly 1 once every category is included), never a
 * signed/raw count, so cluster-size differences do not distort the
 * comparison. Used for diagnosis / sex (few categories, grouped bars).
 */
export function categoryShareByCluster(labels: readonly number[], k: number, values: readonly string[]): { category: string; sharesByCluster: number[] }[] {
  const categories = Array.from(new Set(values)).sort();
  return categories.map((category) => {
    const sharesByCluster = Array.from({ length: k }, (_, c) => {
      let clusterTotal = 0;
      let matching = 0;
      labels.forEach((lbl, i) => {
        if (lbl === c) {
          clusterTotal += 1;
          if (values[i] === category) matching += 1;
        }
      });
      return clusterTotal > 0 ? matching / clusterTotal : 0;
    });
    return { category, sharesByCluster };
  });
}

/**
 * site x cluster matrix, each ROW (one acquisition site) normalized to sum
 * to 1 across clusters -- "of participants scanned at this site, what share
 * fell in each cluster", the natural reading for "does clustering reproduce
 * acquisition site" without implying site is a prediction target.
 */
export function siteShareMatrix(labels: readonly number[], k: number, values: readonly string[]): { sites: string[]; z: number[][] } {
  const sites = Array.from(new Set(values)).sort();
  const z = sites.map((site) => {
    const counts = Array.from({ length: k }, () => 0);
    labels.forEach((lbl, i) => {
      if (values[i] === site) counts[lbl] = (counts[lbl] ?? 0) + 1;
    });
    const total = counts.reduce((a, b) => a + b, 0) || 1;
    return counts.map((v) => v / total);
  });
  return { sites, z };
}

/** Per-cluster age arrays, for a box/violin summary. */
export function agesByCluster(labels: readonly number[], k: number, ages: readonly number[]): number[][] {
  return Array.from({ length: k }, (_, c) => indicesForCluster(labels, c).map((i) => ages[i]!));
}
