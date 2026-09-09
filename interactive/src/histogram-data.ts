// Zod schema + parser for the exported ABIDE histogram data artifact
// (book/_static/widgets/data/abide_histogram.json, produced by
// scripts/export_widget_data.py). Kept free of DOM / Plotly so it can be unit
// tested and reused independently of the rendering component.

import { z } from "zod";
import type { DataResult } from "./components/types";

const numberOrNull = z.union([z.number().finite(), z.null()]);

export const abideHistogramDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    rowCount: z.number().int().positive(),
    source: z
      .object({
        url: z.string().min(1),
        sha256: z.string().min(1),
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
    columns: z.record(z.array(numberOrNull)),
  })
  .passthrough()
  .superRefine((data, ctx) => {
    for (const [name, values] of Object.entries(data.columns)) {
      if (values.length !== data.rowCount) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["columns", name],
          message: `column "${name}" has ${values.length} values, expected rowCount ${data.rowCount}`,
        });
      }
    }
    for (const meta of data.variables) {
      const column = data.columns[meta.name];
      if (!column) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["variables", meta.name],
          message: `variable "${meta.name}" has no matching column`,
        });
        continue;
      }
      const available = column.filter((v) => v !== null).length;
      if (available !== meta.availableN) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["variables", meta.name, "availableN"],
          message: `availableN ${meta.availableN} disagrees with the data (${available})`,
        });
      }
    }
  });

export type AbideHistogramData = z.infer<typeof abideHistogramDataSchema>;

export function parseAbideHistogramData(raw: unknown): DataResult<AbideHistogramData> {
  const parsed = abideHistogramDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid ABIDE histogram data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}
