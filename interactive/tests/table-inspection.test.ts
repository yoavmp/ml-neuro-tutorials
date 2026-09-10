import { describe, expect, it } from "vitest";
import {
  INSPECTION_METHODS,
  formatCell,
  mulberry32,
  sampleRowIndices,
  selectRowIndices,
  summariseView,
} from "../src/table-inspection";
import type { CellValue } from "../src/retention";

describe("mulberry32", () => {
  it("is deterministic for a given seed", () => {
    const a = mulberry32(7);
    const b = mulberry32(7);
    const seqA = [a(), a(), a(), a()];
    const seqB = [b(), b(), b(), b()];
    expect(seqA).toEqual(seqB);
  });

  it("returns floats in [0, 1)", () => {
    const r = mulberry32(123);
    for (let i = 0; i < 1000; i += 1) {
      const v = r();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("different seeds give different streams", () => {
    expect(mulberry32(1)()).not.toBe(mulberry32(2)());
  });
});

describe("selectRowIndices", () => {
  it("head returns the first n indices in order", () => {
    expect(selectRowIndices("head", 100, 5, 0)).toEqual([0, 1, 2, 3, 4]);
  });

  it("tail returns the last n indices in order", () => {
    expect(selectRowIndices("tail", 100, 5, 0)).toEqual([95, 96, 97, 98, 99]);
  });

  it("head/tail clamp n to the table size", () => {
    expect(selectRowIndices("head", 3, 10, 0)).toEqual([0, 1, 2]);
    expect(selectRowIndices("tail", 3, 10, 0)).toEqual([0, 1, 2]);
  });

  it("sample is deterministic for a fixed seed and sorted ascending", () => {
    const a = selectRowIndices("sample", 1114, 8, 7);
    const b = selectRowIndices("sample", 1114, 8, 7);
    expect(a).toEqual(b);
    expect([...a].sort((x, y) => x - y)).toEqual(a);
    expect(new Set(a).size).toBe(a.length);
  });

  it("sample matches the independently computed pandas-free draw (seed 7, n 8, N 1114)", () => {
    // Cross-checked with a Python re-implementation of mulberry32 + Fisher–Yates
    // over the real 1114-row ABIDE-II table.
    expect(selectRowIndices("sample", 1114, 8, 7)).toEqual([
      12, 482, 585, 680, 773, 858, 976, 1098,
    ]);
  });

  it("a different seed gives a different sample", () => {
    expect(selectRowIndices("sample", 1114, 8, 7)).not.toEqual(
      selectRowIndices("sample", 1114, 8, 8),
    );
  });

  it("throws on an unknown method", () => {
    // @ts-expect-error deliberately invalid
    expect(() => selectRowIndices("middle", 10, 3, 0)).toThrow(/Unknown inspection method/);
  });

  it("exposes exactly head/tail/sample", () => {
    expect([...INSPECTION_METHODS]).toEqual(["head", "tail", "sample"]);
  });
});

describe("sampleRowIndices", () => {
  it("returns every index when k >= totalRows", () => {
    expect(sampleRowIndices(5, 5, 42)).toEqual([0, 1, 2, 3, 4]);
    expect(sampleRowIndices(5, 99, 42)).toEqual([0, 1, 2, 3, 4]);
  });

  it("returns [] for k = 0", () => {
    expect(sampleRowIndices(10, 0, 1)).toEqual([]);
  });

  it("throws on a negative table size", () => {
    expect(() => sampleRowIndices(-1, 2, 0)).toThrow(/non-negative integer/);
  });
});

describe("summariseView", () => {
  const columns: Record<string, CellValue[]> = {
    SITE_ID: ["A", "A", "B", "B", "C"],
    AGE: [10, null, 21, 8, null],
    FIQ: [100, 95, null, 110, 105],
  };
  const sites = columns.SITE_ID as string[];

  it("counts distinct sites in first-appearance order and missing cells", () => {
    const v = summariseView(columns, sites, ["SITE_ID", "AGE", "FIQ"], [0, 1, 2]);
    expect(v.rowCount).toBe(3);
    expect(v.sites).toEqual(["A", "B"]);
    expect(v.siteCount).toBe(2);
    expect(v.missingCells).toBe(2); // AGE[1], FIQ[2]
    expect(v.totalCells).toBe(9);
  });

  it("head vs tail of the fixture concentrate on different sites", () => {
    const head = summariseView(columns, sites, ["SITE_ID"], selectRowIndices("head", 5, 2, 0));
    const tail = summariseView(columns, sites, ["SITE_ID"], selectRowIndices("tail", 5, 2, 0));
    expect(head.sites).toEqual(["A"]);
    expect(tail.sites).toEqual(["B", "C"]);
  });

  it("throws when a display column is absent", () => {
    expect(() => summariseView(columns, sites, ["NOPE"], [0])).toThrow(/not present/);
  });

  it("throws on an out-of-range row index", () => {
    expect(() => summariseView(columns, sites, ["AGE"], [99])).toThrow(/out of range/);
  });
});

describe("formatCell", () => {
  it("renders an em dash for missing", () => {
    expect(formatCell(null)).toBe("—");
    expect(formatCell(undefined)).toBe("—");
  });

  it("keeps integers integer and rounds floats to 2dp", () => {
    expect(formatCell(42)).toBe("42");
    expect(formatCell(6.685832)).toBe("6.69");
  });

  it("passes strings through", () => {
    expect(formatCell("ABIDEII-BNI_1")).toBe("ABIDEII-BNI_1");
  });
});

describe("table-inspection against the committed abide_retention.json", () => {
  async function loadArtifact() {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_retention.json",
      import.meta.url,
    );
    return JSON.parse(await fs.readFile(url, "utf-8")) as {
      rowCount: number;
      columns: Record<string, CellValue[]>;
    };
  }

  const DISPLAY = [
    "SITE_ID",
    "DX_GROUP",
    "AGE_AT_SCAN",
    "SEX",
    "HANDEDNESS_CATEGORY",
    "FIQ",
    "SRS_TOTAL_RAW",
    "ADOS_G_TOTAL",
  ];

  it("head(8) is one site with no missing display cells; tail(8) is one site with missing cells", async () => {
    const art = await loadArtifact();
    const sites = art.columns.SITE_ID as string[];
    const head = summariseView(art.columns, sites, DISPLAY, selectRowIndices("head", art.rowCount, 8, 7));
    const tail = summariseView(art.columns, sites, DISPLAY, selectRowIndices("tail", art.rowCount, 8, 7));
    expect(head.siteCount).toBe(1);
    expect(head.sites).toEqual(["ABIDEII-BNI_1"]);
    expect(head.missingCells).toBe(0);
    expect(tail.siteCount).toBe(1);
    expect(tail.sites).toEqual(["ABIDEII-USM_1"]);
    expect(tail.missingCells).toBe(19);
  });

  it("sample(8, seed 7) spans 8 sites with far fewer missing cells than tail", async () => {
    const art = await loadArtifact();
    const sites = art.columns.SITE_ID as string[];
    const idx = selectRowIndices("sample", art.rowCount, 8, 7);
    expect(idx).toEqual([12, 482, 585, 680, 773, 858, 976, 1098]);
    const v = summariseView(art.columns, sites, DISPLAY, idx);
    expect(v.siteCount).toBe(8);
    expect(v.missingCells).toBe(7);
  });
});
