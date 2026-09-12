import { describe, expect, it } from "vitest";
import {
  computeRetention,
  NO_SELECTION_MESSAGE,
  type CellValue,
} from "../src/retention";

// Tiny aligned fixture: 6 rows, 3 sites in first-appearance order B, A, C.
const columns: Record<string, CellValue[]> = {
  //          r0     r1     r2     r3     r4     r5
  DX_GROUP: [1, 2, 1, 2, 1, 2],
  AGE: [10.5, null, 21, 8.25, 12, 15],
  FIQ: [100, 95, null, 110, 105, null],
  MED0: [0, 0, 0, 0, 0, 0], // all valid zeros — never "missing"
  HAND: ["R", "L", "R", null, "A", "R"],
  ALLNULL: [null, null, null, null, null, null],
};
const siteLabels = ["SiteB", "SiteB", "SiteA", "SiteA", "SiteA", "SiteC"];

describe("computeRetention", () => {
  it("no selection retains every row and flags that no criterion is applied", () => {
    const r = computeRetention(columns, siteLabels, []);
    expect(r.noSelection).toBe(true);
    expect(r.message).toBe(NO_SELECTION_MESSAGE);
    expect(r.retained).toBe(6);
    expect(r.excluded).toBe(0);
    expect(r.retainedPct).toBe(100);
    expect(r.sites.map((s) => [s.site, s.retained, s.total])).toEqual([
      ["SiteB", 2, 2],
      ["SiteA", 3, 3],
      ["SiteC", 1, 1],
    ]);
  });

  it("one variable: retains rows where that variable is non-null", () => {
    const r = computeRetention(columns, siteLabels, ["FIQ"]);
    expect(r.noSelection).toBe(false);
    expect(r.message).toBeNull();
    expect(r.retained).toBe(4); // r0,r1,r3,r4
    expect(r.excluded).toBe(2);
    expect(r.selected).toEqual(["FIQ"]);
  });

  it("multiple variables: a row needs every selected field non-null", () => {
    const r = computeRetention(columns, siteLabels, ["AGE", "FIQ"]);
    // AGE non-null: r0,r2,r3,r4,r5 ; FIQ non-null: r0,r1,r3,r4 ; both: r0,r3,r4
    expect(r.retained).toBe(3);
  });

  it("treats valid 0 as present, not missing", () => {
    const r = computeRetention(columns, siteLabels, ["MED0"]);
    expect(r.retained).toBe(6);
    expect(r.retainedPct).toBe(100);
  });

  it("treats documented category strings as present; only null is missing", () => {
    const r = computeRetention(columns, siteLabels, ["HAND"]);
    expect(r.retained).toBe(5); // only r3 (null) drops
  });

  it("no missingness in the selected set retains everyone", () => {
    const r = computeRetention(columns, siteLabels, ["DX_GROUP"]);
    expect(r.retained).toBe(6);
    expect(r.excluded).toBe(0);
  });

  it("a fully-missing variable excludes everyone", () => {
    const r = computeRetention(columns, siteLabels, ["ALLNULL"]);
    expect(r.retained).toBe(0);
    expect(r.excluded).toBe(6);
    expect(r.retainedPct).toBe(0);
    for (const s of r.sites) expect(s.retained).toBe(0);
  });

  it("reports site-specific missingness with a deterministic first-appearance order", () => {
    const r = computeRetention(columns, siteLabels, ["FIQ"]);
    expect(r.sites.map((s) => s.site)).toEqual(["SiteB", "SiteA", "SiteC"]);
    // FIQ retained: r0(SiteB), r1(SiteB), r3(SiteA), r4(SiteA); SiteC row r5 null
    expect(r.sites).toEqual([
      { site: "SiteB", total: 2, retained: 2, excluded: 0, retainedPct: 100 },
      { site: "SiteA", total: 3, retained: 2, excluded: 1, retainedPct: (2 / 3) * 100 },
      { site: "SiteC", total: 1, retained: 0, excluded: 1, retainedPct: 0 },
    ]);
  });

  it("conserves counts overall and per site (retained + excluded = total)", () => {
    for (const sel of [[], ["FIQ"], ["AGE", "FIQ"], ["ALLNULL"], ["DX_GROUP", "HAND"]]) {
      const r = computeRetention(columns, siteLabels, sel);
      expect(r.retained + r.excluded).toBe(r.total);
      let sumTotal = 0;
      let sumRetained = 0;
      for (const s of r.sites) {
        expect(s.retained + s.excluded).toBe(s.total);
        sumTotal += s.total;
        sumRetained += s.retained;
      }
      expect(sumTotal).toBe(r.total);
      expect(sumRetained).toBe(r.retained);
    }
  });

  it("rejects a duplicate selected variable", () => {
    expect(() => computeRetention(columns, siteLabels, ["FIQ", "FIQ"])).toThrow(/Duplicate/);
  });

  it("rejects a selected variable not present in the data", () => {
    expect(() => computeRetention(columns, siteLabels, ["NOPE"])).toThrow(/not present/);
  });

  it("rejects a column whose length disagrees with the site labels", () => {
    const bad = { ...columns, FIQ: [1, 2, 3] };
    expect(() => computeRetention(bad, siteLabels, ["DX_GROUP"])).toThrow(/values but there are 6/);
  });

  it("rejects a missing site label", () => {
    const labels = ["SiteB", "", "SiteA", "SiteA", "SiteA", "SiteC"];
    expect(() => computeRetention(columns, labels, ["DX_GROUP"])).toThrow(/Missing site label/);
  });
});

describe("computeRetention — against the committed abide_retention.json", () => {
  async function loadArtifact() {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_retention.json",
      import.meta.url,
    );
    return JSON.parse(await fs.readFile(url, "utf-8")) as {
      rowCount: number;
      site: { sites: { label: string; total: number }[] };
      columns: Record<string, CellValue[]>;
    };
  }

  it("suggested core set {DX_GROUP, AGE_AT_SCAN, SEX, FIQ}: 1015 / 1114 retained (91.1131%)", async () => {
    const art = await loadArtifact();
    const sites = art.columns.SITE_ID as string[];
    const r = computeRetention(art.columns, sites, ["DX_GROUP", "AGE_AT_SCAN", "SEX", "FIQ"]);
    expect(r.total).toBe(1114);
    expect(r.retained).toBe(1015);
    expect(r.excluded).toBe(99);
    expect(r.retainedPct).toBeCloseTo(91.1131, 4);
    // per-site cross-checks (independently computed with pandas)
    const bySite = new Map(r.sites.map((s) => [s.site, s]));
    expect(bySite.get("ABIDEII-BNI_1")).toMatchObject({ retained: 58, total: 58 });
    expect(bySite.get("ABIDEII-EMC_1")).toMatchObject({ retained: 0, total: 54 });
    expect(bySite.get("ABIDEII-IP_1")).toMatchObject({ retained: 25, total: 56 });
    expect(bySite.get("ABIDEII-USM_1")).toMatchObject({ retained: 27, total: 33 });
    // deterministic order == artifact's first-appearance site order
    expect(r.sites.map((s) => s.site)).toEqual(art.site.sites.map((s) => s.label));
    // conservation
    expect(r.sites.reduce((a, s) => a + s.total, 0)).toBe(1114);
    expect(r.sites.reduce((a, s) => a + s.retained, 0)).toBe(1015);
  });

  it("behavioral pair {ADOS_G_TOTAL, ADI_R_SOCIAL_TOTAL_A}: 152 / 1114 retained (13.6445%)", async () => {
    const art = await loadArtifact();
    const sites = art.columns.SITE_ID as string[];
    const r = computeRetention(art.columns, sites, ["ADOS_G_TOTAL", "ADI_R_SOCIAL_TOTAL_A"]);
    expect(r.retained).toBe(152);
    expect(r.retainedPct).toBeCloseTo(13.6445, 4);
  });

  it("no selection against the real artifact keeps all 1114 and flags no criterion", async () => {
    const art = await loadArtifact();
    const sites = art.columns.SITE_ID as string[];
    const r = computeRetention(art.columns, sites, []);
    expect(r.retained).toBe(1114);
    expect(r.noSelection).toBe(true);
  });
});
