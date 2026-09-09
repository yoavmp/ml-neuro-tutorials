import { describe, expect, it } from "vitest";
import { parseAbideRetentionData } from "../src/retention-data";

function base() {
  return {
    schemaVersion: 1 as const,
    activity: "eda-retention" as const,
    rowCount: 4,
    source: { url: "https://example/abide.csv", sha256: "deadbeef" },
    site: {
      field: "SITE_ID",
      siteCount: 2,
      sites: [
        { label: "SiteB", total: 2 },
        { label: "SiteA", total: 2 },
      ],
    },
    variables: [
      { name: "FIQ", availableN: 3, missingN: 1 },
      { name: "MED", availableN: 4, missingN: 0 },
    ],
    columns: {
      SITE_ID: ["SiteB", "SiteB", "SiteA", "SiteA"],
      FIQ: [100, null, 110, 95],
      MED: [0, 1, 0, 0],
    },
  };
}

describe("parseAbideRetentionData", () => {
  it("accepts a well-formed artifact (valid 0 kept, null is the only missing)", () => {
    const r = parseAbideRetentionData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    const r = parseAbideRetentionData({ ...base(), activity: "eda-histogram" });
    expect(r.ok).toBe(false);
  });

  it("rejects a missing SITE_ID column", () => {
    const b = base();
    const { SITE_ID: _omit, ...columns } = b.columns;
    void _omit;
    const r = parseAbideRetentionData({ ...b, columns });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/SITE_ID/);
  });

  it("rejects a null in the SITE_ID column", () => {
    const b = base();
    b.columns.SITE_ID = ["SiteB", null as unknown as string, "SiteA", "SiteA"];
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
  });

  it("rejects an identifier-shaped column other than SITE_ID", () => {
    const b = base();
    (b.columns as Record<string, unknown>).SUB_ID = [1, 2, 3, 4];
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("rejects a column whose length disagrees with rowCount", () => {
    const b = base();
    b.columns.FIQ = [100, null];
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/expected rowCount 4/);
  });

  it("rejects availableN that disagrees with the data", () => {
    const b = base();
    b.variables[0]!.availableN = 4;
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/availableN/);
  });

  it("rejects site.sites that are not in first-appearance order", () => {
    const b = base();
    b.site.sites = [
      { label: "SiteA", total: 2 },
      { label: "SiteB", total: 2 },
    ];
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/first-appearance/);
  });

  it("rejects a site total that disagrees with the data", () => {
    const b = base();
    b.site.sites[0]!.total = 3;
    const r = parseAbideRetentionData(b);
    expect(r.ok).toBe(false);
  });

  it("validates the committed abide_retention.json artifact", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_retention.json",
      import.meta.url,
    );
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseAbideRetentionData(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.rowCount).toBe(1114);
      expect(r.data.site.siteCount).toBe(19);
      expect(r.data.columns.SITE_ID).toHaveLength(1114);
      expect(Object.keys(r.data.columns).sort()).toEqual(
        [
          "ADOS_2_TOTAL",
          "ADOS_G_TOTAL",
          "AGE_AT_SCAN",
          "CURRENT_MED_STATUS",
          "DX_GROUP",
          "EYE_STATUS_AT_SCAN",
          "FIQ",
          "HANDEDNESS_CATEGORY",
          "PIQ",
          "SCQ_TOTAL",
          "SEX",
          "SITE_ID",
          "SRS_TOTAL_RAW",
          "VIQ",
        ],
      );
    }
  });
});
