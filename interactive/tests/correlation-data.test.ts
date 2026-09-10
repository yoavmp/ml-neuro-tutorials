import { describe, expect, it } from "vitest";
import {
  parseAbideCorrelationData,
  numericColumn,
} from "../src/correlation-data";

function base() {
  return {
    schemaVersion: 1 as const,
    activity: "eda-retention" as const,
    rowCount: 4,
    columns: {
      SITE_ID: ["A", "A", "B", "B"],
      FIQ: [100, null, 110, 95],
      SRS_TOTAL_RAW: [40, 55, null, 20],
      DX_GROUP: [1, 2, 1, 2],
    },
  };
}

describe("parseAbideCorrelationData", () => {
  it("accepts the reused retention artifact shape (SITE_ID allowed, null = missing)", () => {
    const r = parseAbideCorrelationData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a column that is not aligned to rowCount", () => {
    const b = base();
    b.columns.FIQ = [1, 2];
    const r = parseAbideCorrelationData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/expected rowCount 4/);
  });

  it("rejects an identifier-shaped column other than SITE_ID", () => {
    const b = base();
    (b.columns as Record<string, unknown>).SUB_ID = [1, 2, 3, 4];
    const r = parseAbideCorrelationData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("rejects a wrong schemaVersion", () => {
    const r = parseAbideCorrelationData({ ...base(), schemaVersion: 2 });
    expect(r.ok).toBe(false);
  });

  it("numericColumn maps non-finite / non-number cells to null", () => {
    const r = parseAbideCorrelationData(base());
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(numericColumn(r.data, "FIQ")).toEqual([100, null, 110, 95]);
      expect(numericColumn(r.data, "SITE_ID")).toEqual([null, null, null, null]);
      expect(numericColumn(r.data, "NOPE")).toBeUndefined();
    }
  });

  it("validates the committed abide_retention.json for correlation use", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_retention.json",
      import.meta.url,
    );
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseAbideCorrelationData(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.rowCount).toBe(1114);
      for (const name of [
        "AGE_AT_SCAN",
        "FIQ",
        "VIQ",
        "PIQ",
        "ADOS_G_TOTAL",
        "ADI_R_SOCIAL_TOTAL_A",
        "SRS_TOTAL_RAW",
        "DX_GROUP",
        "SEX",
      ]) {
        expect(numericColumn(r.data, name)).toHaveLength(1114);
      }
    }
  });
});
