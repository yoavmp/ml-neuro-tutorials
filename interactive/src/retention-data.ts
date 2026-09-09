// Zod schema + parser for the exported ABIDE retention data artifact
// (book/_static/widgets/data/abide_retention.json, produced by
// scripts/export_widget_data.py --artifact retention). Kept free of DOM / Plotly
// so it can be unit tested and reused independently of the rendering component.
//
// This is the component-owned schema (WP04 §5.1). It enforces the narrow
// SITE_ID exception on the client too: SITE_ID is the one identifier-shaped
// column allowed, it carries a non-empty string on every row, and every other
// column is an aligned array of numbers / documented codes / strings / null.

import { z } from "zod";
import type { DataResult } from "./components/types";

export const SITE_FIELD = "SITE_ID" as const;

const cellValue = z.union([z.number().finite(), z.string(), z.boolean(), z.null()]);

const siteMeta = z
  .object({
    field: z.literal(SITE_FIELD),
    siteCount: z.number().int().positive(),
    sites: z
      .array(
        z
          .object({
            label: z.string().min(1),
            total: z.number().int().nonnegative(),
          })
          .passthrough(),
      )
      .min(1),
  })
  .passthrough();

export const abideRetentionDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("eda-retention"),
    rowCount: z.number().int().positive(),
    source: z
      .object({
        url: z.string().min(1),
        sha256: z.string().min(1),
      })
      .passthrough(),
    site: siteMeta,
    variables: z
      .array(
        z
          .object({
            name: z.string().min(1),
            availableN: z.number().int().nonnegative(),
            missingN: z.number().int().nonnegative(),
          })
          .passthrough(),
      )
      .min(1),
    columns: z.record(z.array(cellValue)),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const addIssue = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    // Every column is aligned to rowCount.
    for (const [name, values] of Object.entries(data.columns)) {
      if (values.length !== data.rowCount) {
        addIssue(
          ["columns", name],
          `column "${name}" has ${values.length} values, expected rowCount ${data.rowCount}`,
        );
      }
    }

    // The site column exists and is a non-empty string on every row.
    const siteColumn = data.columns[SITE_FIELD];
    if (!siteColumn) {
      addIssue(["columns", SITE_FIELD], `required site column "${SITE_FIELD}" is missing`);
    } else {
      const bad = siteColumn.findIndex((v) => typeof v !== "string" || v.trim() === "");
      if (bad !== -1) {
        addIssue(
          ["columns", SITE_FIELD, bad],
          `site column "${SITE_FIELD}" must be a non-empty string on every row`,
        );
      }
    }

    // Non-site columns must not be identifier-shaped (SITE_ID is the sole
    // deliberate exception).
    const identifierToken = /(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|PARTICIPANT|NAME|EMAIL|DOB)($|_)/i;
    for (const name of Object.keys(data.columns)) {
      if (name !== SITE_FIELD && identifierToken.test(name)) {
        addIssue(["columns", name], `identifier-shaped column "${name}" is not allowed`);
      }
    }

    // Variable metadata agrees with the data. Variables never include the site
    // field.
    for (const meta of data.variables) {
      if (meta.name === SITE_FIELD) {
        addIssue(["variables", meta.name], `"${SITE_FIELD}" is the site label, not a variable`);
        continue;
      }
      const column = data.columns[meta.name];
      if (!column) {
        addIssue(["variables", meta.name], `variable "${meta.name}" has no matching column`);
        continue;
      }
      const available = column.filter((v) => v !== null).length;
      if (available !== meta.availableN) {
        addIssue(
          ["variables", meta.name, "availableN"],
          `availableN ${meta.availableN} disagrees with the data (${available})`,
        );
      }
      if (meta.availableN + meta.missingN !== data.rowCount) {
        addIssue(
          ["variables", meta.name, "missingN"],
          `availableN + missingN (${meta.availableN + meta.missingN}) !== rowCount ${data.rowCount}`,
        );
      }
    }

    // site.sites is the distinct SITE_ID values in first-appearance order, with
    // correct per-site totals.
    if (siteColumn) {
      const firstSeen = new Map<string, number>();
      for (const v of siteColumn) {
        if (typeof v === "string") firstSeen.set(v, (firstSeen.get(v) ?? 0) + 1);
      }
      if (data.site.siteCount !== firstSeen.size) {
        addIssue(["site", "siteCount"], `siteCount ${data.site.siteCount} !== distinct sites ${firstSeen.size}`);
      }
      const metaLabels = data.site.sites.map((s) => s.label);
      if (metaLabels.join("\u0001") !== [...firstSeen.keys()].join("\u0001")) {
        addIssue(["site", "sites"], "site.sites is not the SITE_ID values in first-appearance order");
      }
      let sum = 0;
      for (const s of data.site.sites) {
        sum += s.total;
        if (firstSeen.get(s.label) !== s.total) {
          addIssue(["site", "sites"], `site "${s.label}" total ${s.total} disagrees with the data`);
        }
      }
      if (sum !== data.rowCount) {
        addIssue(["site", "sites"], `site totals sum to ${sum}, expected rowCount ${data.rowCount}`);
      }
    }
  });

export type AbideRetentionData = z.infer<typeof abideRetentionDataSchema>;

export function parseAbideRetentionData(raw: unknown): DataResult<AbideRetentionData> {
  const parsed = abideRetentionDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid ABIDE retention data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
