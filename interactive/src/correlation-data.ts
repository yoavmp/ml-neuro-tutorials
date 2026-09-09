// Zod schema + parser for the data artifact the `eda-correlation` activity
// loads. It deliberately REUSES book/_static/widgets/data/abide_retention.json
// (WP05 §5 "Reuse data where possible"): that file already carries aligned,
// identifier-free numeric columns for age, IQ, ADOS, SRS and SCQ plus the
// DX_GROUP / SEX category codes this activity groups by.
//
// This schema is intentionally looser than retention-data.ts — it does not
// require the `site` metadata block or per-variable metadata, only that the
// artifact is schemaVersion 1, that every column is aligned to `rowCount`, and
// that no identifier-shaped column is present (SITE_ID is the sole allowed
// exception, matching the retention exporter). Kept DOM / Plotly free so it can
// be unit tested.

import { z } from "zod";
import type { DataResult } from "./components/types";

export const SITE_FIELD = "SITE_ID" as const;

// Same token set as scripts/export_widget_data.py and retention-data.ts.
const IDENTIFIER_TOKEN =
  /(^|_)(ID|IDS|UID|GUID|MRN|SUB|SUBJECT|PARTICIPANT|NAME|EMAIL|DOB)($|_)/i;

const cellValue = z.union([z.number(), z.string(), z.boolean(), z.null()]);

export const abideCorrelationDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    rowCount: z.number().int().positive(),
    columns: z.record(z.array(cellValue)),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    const addIssue = (path: (string | number)[], message: string): void => {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path, message });
    };

    for (const [name, values] of Object.entries(data.columns)) {
      if (values.length !== data.rowCount) {
        addIssue(
          ["columns", name],
          `column "${name}" has ${values.length} values, expected rowCount ${data.rowCount}`,
        );
      }
      if (name !== SITE_FIELD && IDENTIFIER_TOKEN.test(name)) {
        addIssue(["columns", name], `identifier-shaped column "${name}" is not allowed`);
      }
    }
  });

export type AbideCorrelationData = z.infer<typeof abideCorrelationDataSchema>;

export function parseAbideCorrelationData(raw: unknown): DataResult<AbideCorrelationData> {
  const parsed = abideCorrelationDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid ABIDE correlation data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}

/** Read one column as `(number | null)[]`, mapping every non-finite cell to null. */
export function numericColumn(
  data: AbideCorrelationData,
  name: string,
): (number | null)[] | undefined {
  const raw = data.columns[name];
  if (!raw) return undefined;
  return raw.map((v) => (typeof v === "number" && Number.isFinite(v) ? v : null));
}
