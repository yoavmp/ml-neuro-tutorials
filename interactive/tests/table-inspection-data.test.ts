import { describe, expect, it } from "vitest";
import {
  parseAbideTableInspectionData,
  IDENTIFIER_FIELDS,
} from "../src/table-inspection-data";

async function loadCommitted(): Promise<unknown> {
  const fs = await import("node:fs/promises");
  const url = new URL(
    "../../book/_static/widgets/data/abide_table_inspection.json",
    import.meta.url,
  );
  return JSON.parse(await fs.readFile(url, "utf-8"));
}

async function loadCommittedCopy(): Promise<Record<string, unknown>> {
  return structuredClone(await loadCommitted()) as Record<string, unknown>;
}

const CURATED = [
  "SITE_ID",
  "SUB_ID",
  "DX_GROUP",
  "AGE_AT_SCAN",
  "SEX",
  "HANDEDNESS_CATEGORY",
  "FIQ",
  "VIQ",
  "PIQ",
  "CURRENT_MED_STATUS",
  "SRS_TOTAL_RAW",
  "ADOS_G_TOTAL",
  "ADI_R_SOCIAL_TOTAL_A",
];

describe("parseAbideTableInspectionData", () => {
  it("exposes the two allowed identifier fields", () => {
    expect([...IDENTIFIER_FIELDS]).toEqual(["SITE_ID", "SUB_ID"]);
  });

  it("accepts the committed artifact and reports the 13 curated columns", async () => {
    const r = parseAbideTableInspectionData(await loadCommitted());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.activity).toBe("table-inspection");
      expect(r.data.columnOrder).toEqual(CURATED);
      expect(r.data.rowCount).toBe(1114);
      expect(Object.keys(r.data.columns).sort()).toEqual([...CURATED].sort());
      expect(r.data.site.siteCount).toBe(19);
    }
  });

  it("rejects an identifier-shaped column that is not SITE_ID / SUB_ID", async () => {
    const bad = await loadCommittedCopy();
    (bad.columns as Record<string, unknown[]>).SCANNER_ID = new Array(1114).fill(1);
    const r = parseAbideTableInspectionData(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped column "SCANNER_ID"/);
  });

  it("rejects a missing SUB_ID column", async () => {
    const bad = await loadCommittedCopy();
    delete (bad.columns as Record<string, unknown[]>).SUB_ID;
    const r = parseAbideTableInspectionData(bad);
    expect(r.ok).toBe(false);
  });

  it("rejects a null inside an identifier column", async () => {
    const bad = await loadCommittedCopy();
    (bad.columns as Record<string, (string | null)[]>).SUB_ID![0] = null;
    const r = parseAbideTableInspectionData(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/SUB_ID/);
  });

  it("rejects columnOrder that disagrees with the column keys", async () => {
    const bad = await loadCommittedCopy();
    (bad.columnOrder as string[]) = (bad.columnOrder as string[]).slice(0, 12);
    const r = parseAbideTableInspectionData(bad);
    expect(r.ok).toBe(false);
  });

  it("rejects the wrong activity discriminator", async () => {
    const bad = await loadCommittedCopy();
    bad.activity = "eda-retention";
    expect(parseAbideTableInspectionData(bad).ok).toBe(false);
  });

  it("rejects an unaligned column", async () => {
    const bad = await loadCommittedCopy();
    (bad.columns as Record<string, unknown[]>).FIQ!.push(1);
    const r = parseAbideTableInspectionData(bad);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/FIQ/);
  });
});
