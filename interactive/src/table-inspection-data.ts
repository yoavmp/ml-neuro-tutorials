// Zod schema + parser for the exported ABIDE table-inspection data artifact
// (book/_static/widgets/data/abide_table_inspection.json, produced by
// scripts/export_widget_data.py --artifact table-inspection). Kept free of DOM /
// Plotly so it can be unit tested and reused independently of the component.
//
// This activity shows real rows of the 13-column curated teaching table so a
// student can compare what head(), tail() and sample() return, which is why it
// is the one artifact allowed to carry the two identifier-shaped string columns
// SITE_ID and SUB_ID. Every other column is a curated, non-identifier
// number / documented-code / null array. `columnOrder` is the curated column
// authority verbatim, so the config tested against it cannot drift.

import { z } from "zod";
import type { DataResult } from "./components/types";

export const IDENTIFIER_FIELDS = ["SITE_ID", "SUB_ID"] as const;

const cellValue = z.union([z.number().finite(), z.string(), z.boolean(), z.null()]);

export const abideTableInspectionDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    activity: z.literal("table-inspection"),
    rowCount: z.number().int().positive(),
    source: z
      .object({ url: z.string().min(1), sha256: z.string().min(1) })
      .passthrough(),
    columnOrder: z.array(z.string().min(1)).min(1),
    identifierFields: z.tuple([z.literal("SITE_ID"), z.literal("SUB_ID")]),
    site: z
      .object({
        field: z.literal("SITE_ID"),
        siteCount: z.number().int().positive(),
        sites: z
          .array(
            z
              .object({ label: z.string().min(1), total: z.number().int().nonnegative() })
              .passthrough(),
          )
          .min(1),
      })
      .passthrough(),
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

    const idFields = new Set<string>(data.identifierFields);

    // Column set is exactly columnOrder, and each column is aligned to rowCount.
    const columnNames = Object.keys(data.columns);
    if (
      columnNames.length !== data.columnOrder.length ||
      !data.columnOrder.every((n) => Object.prototype.hasOwnProperty.call(data.columns, n))
    ) {
      addIssue(["columns"], "columns keys must match columnOrder exactly");
    }
    for (const [name, values] of Object.entries(data.columns)) {
      if (values.length !== data.rowCount) {
        addIssue(
          ["columns", name],
          `column "${name}" has ${values.length} values, expected rowCount ${data.rowCount}`,
        );
      }
    }

    // Identifier columns exist and are non-empty strings on every row.
    for (const field of data.identifierFields) {
      const column = data.columns[field];
      if (!column) {
        addIssue(["columns", field], `required identifier column "${field}" is missing`);
        continue;
      }
      const bad = column.findIndex((v) => typeof v !== "string" || v.trim() === "");
      if (bad !== -1) {
        addIssue(
          ["columns", field, bad],
          `identifier column "${field}" must be a non-empty string on every row`,
        );
      }
    }

    // Every non-identifier column must not be identifier-shaped.
    const identifierToken = /(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|PARTICIPANT|NAME|EMAIL|DOB)($|_)/i;
    for (const name of columnNames) {
      if (!idFields.has(name) && identifierToken.test(name)) {
        addIssue(["columns", name], `identifier-shaped column "${name}" is not allowed`);
      }
    }

    // Variable metadata covers exactly the non-identifier columns and agrees
    // with the data.
    const metaNames = new Set(data.variables.map((m) => m.name));
    for (const name of columnNames) {
      if (idFields.has(name)) continue;
      if (!metaNames.has(name)) {
        addIssue(["variables"], `column "${name}" has no variables metadata entry`);
      }
    }
    for (const meta of data.variables) {
      if (idFields.has(meta.name)) {
        addIssue(["variables", meta.name], `"${meta.name}" is an identifier column, not a variable`);
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

    // site.sites is the distinct SITE_ID values in first-appearance order.
    const siteColumn = data.columns.SITE_ID;
    if (siteColumn) {
      const firstSeen = new Map<string, number>();
      for (const v of siteColumn) {
        if (typeof v === "string") firstSeen.set(v, (firstSeen.get(v) ?? 0) + 1);
      }
      if (data.site.siteCount !== firstSeen.size) {
        addIssue(["site", "siteCount"], `siteCount ${data.site.siteCount} !== distinct sites ${firstSeen.size}`);
      }
      const metaLabels = data.site.sites.map((s) => s.label);
      if (metaLabels.join("") !== [...firstSeen.keys()].join("")) {
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

export type AbideTableInspectionData = z.infer<typeof abideTableInspectionDataSchema>;

export function parseAbideTableInspectionData(
  raw: unknown,
): DataResult<AbideTableInspectionData> {
  const parsed = abideTableInspectionDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid ABIDE table-inspection data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
