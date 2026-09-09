// Pure complete-case retention maths. No DOM, no Plotly, no fetch — unit tested
// in tests/retention.test.ts. The component renders exactly what this returns.
//
// "Missing" means JSON `null` only. A valid `0`, a documented category code, or
// a documented category string is NOT missing. A participant (row) is retained
// only when every selected variable is non-null on that row. With no variable
// selected, every row is retained and `noSelection` is set so the UI can say
// that no completeness criterion is being applied.

export type CellValue = number | string | boolean | null;

export interface SiteRetention {
  /** Site-grouping label, e.g. an acquisition-site code. */
  site: string;
  /** Participants from this site in the full sample. */
  total: number;
  /** Participants from this site kept by the complete-case rule. */
  retained: number;
  /** `total - retained`. */
  excluded: number;
  /** `retained / total * 100`, or `0` when the site has no participants. */
  retainedPct: number;
}

export interface RetentionResult {
  /** Rows in the full sample. */
  total: number;
  /** Rows kept by the complete-case rule (all selected variables non-null). */
  retained: number;
  /** `total - retained`. */
  excluded: number;
  /** `retained / total * 100`, or `0` when `total` is `0`. */
  retainedPct: number;
  /** Per-site breakdown, in first-appearance order of `siteLabels`. */
  sites: SiteRetention[];
  /** The requested variable names, unchanged. */
  selected: string[];
  /** True when `selected` is empty: no completeness criterion is applied. */
  noSelection: boolean;
  /** Human-readable note when `noSelection` is true; otherwise `null`. */
  message: string | null;
}

export const NO_SELECTION_MESSAGE =
  "All participants are retained because no completeness criterion is currently applied.";

function isMissing(value: CellValue | undefined): boolean {
  return value === null || value === undefined;
}

/**
 * Compute overall and per-site complete-case retention.
 *
 * @param columns aligned columnar values, keyed by variable name.
 * @param siteLabels site-grouping label for each row (same length as columns).
 * @param selected variable names that must all be non-null for a row to be kept.
 *
 * Throws on: a duplicate name in `selected`; a selected name that is not a key
 * of `columns`; any column whose length differs from `siteLabels.length`; a
 * `siteLabels` entry that is not a non-empty string.
 */
export function computeRetention(
  columns: Readonly<Record<string, ReadonlyArray<CellValue>>>,
  siteLabels: ReadonlyArray<string>,
  selected: ReadonlyArray<string>,
): RetentionResult {
  const total = siteLabels.length;

  const seen = new Set<string>();
  for (const name of selected) {
    if (seen.has(name)) {
      throw new Error(`Duplicate selected variable: "${name}".`);
    }
    seen.add(name);
    if (!Object.prototype.hasOwnProperty.call(columns, name)) {
      throw new Error(`Selected variable "${name}" is not present in the data.`);
    }
  }

  for (const [name, values] of Object.entries(columns)) {
    if (values.length !== total) {
      throw new Error(
        `Column "${name}" has ${values.length} values but there are ${total} site labels.`,
      );
    }
  }

  for (let i = 0; i < total; i += 1) {
    const label = siteLabels[i];
    if (typeof label !== "string" || label.trim() === "") {
      throw new Error(`Missing site label at row ${i}.`);
    }
  }

  // Per-site tallies, insertion-ordered by first appearance.
  const siteTotals = new Map<string, number>();
  const siteRetained = new Map<string, number>();
  for (const label of siteLabels) {
    siteTotals.set(label, (siteTotals.get(label) ?? 0) + 1);
    if (!siteRetained.has(label)) siteRetained.set(label, 0);
  }

  const noSelection = selected.length === 0;
  const selectedColumns = selected.map((name) => columns[name] as ReadonlyArray<CellValue>);

  let retained = 0;
  for (let i = 0; i < total; i += 1) {
    let keep = true;
    if (!noSelection) {
      for (const column of selectedColumns) {
        if (isMissing(column[i])) {
          keep = false;
          break;
        }
      }
    }
    if (keep) {
      retained += 1;
      const label = siteLabels[i] as string;
      siteRetained.set(label, (siteRetained.get(label) ?? 0) + 1);
    }
  }

  const pct = (part: number, whole: number): number => (whole === 0 ? 0 : (part / whole) * 100);

  const sites: SiteRetention[] = [];
  for (const [site, siteTotal] of siteTotals) {
    const siteKept = siteRetained.get(site) ?? 0;
    sites.push({
      site,
      total: siteTotal,
      retained: siteKept,
      excluded: siteTotal - siteKept,
      retainedPct: pct(siteKept, siteTotal),
    });
  }

  return {
    total,
    retained,
    excluded: total - retained,
    retainedPct: pct(retained, total),
    sites,
    selected: [...selected],
    noSelection,
    message: noSelection ? NO_SELECTION_MESSAGE : null,
  };
}
