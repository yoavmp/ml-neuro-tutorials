import { describe, expect, it } from "vitest";
import {
  assertAligned,
  averageRanks,
  computeCorrelation,
  pairwiseComplete,
  pearson,
  spearman,
  REASON_TOO_FEW,
  REASON_NO_VARIANCE,
  type NumCell,
} from "../src/correlation";

describe("pairwiseComplete", () => {
  it("keeps rows where both are finite and counts every missing kind", () => {
    const x: NumCell[] = [1, 2, null, 4, Number.NaN, 6];
    const y: NumCell[] = [10, null, 30, 40, 50, 60];
    const pw = pairwiseComplete(x, y);
    expect(pw.x).toEqual([1, 4, 6]);
    expect(pw.y).toEqual([10, 40, 60]);
    expect(pw.n).toBe(3);
    expect(pw.missing).toEqual({ total: 6, x: 2, y: 1, either: 3 });
  });

  it("throws on a length mismatch", () => {
    expect(() => pairwiseComplete([1, 2, 3], [1, 2])).toThrow(/values but/);
  });

  it("treats Infinity and non-numbers as missing, not as data", () => {
    const pw = pairwiseComplete(
      [1, 2, Infinity, "x" as unknown as number, 5],
      [1, 2, 3, 4, 5],
    );
    expect(pw.x).toEqual([1, 2, 5]);
    expect(pw.missing.x).toBe(2);
  });
});

describe("pearson", () => {
  it("matches numpy on a known vector (r = 0.9393939…)", () => {
    const x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const y = [2, 1, 4, 3, 6, 5, 8, 7, 10, 9];
    expect(pearson(x, y)).toBeCloseTo(0.9393939393939393, 12);
  });

  it("is exactly 1 / -1 for perfect linear relations", () => {
    expect(pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])).toBeCloseTo(1, 12);
    expect(pearson([1, 2, 3, 4, 5], [10, 8, 6, 4, 2])).toBeCloseTo(-1, 12);
  });

  it("returns null for n < 3 and for a constant array (zero variance)", () => {
    expect(pearson([1, 2], [3, 4])).toBeNull();
    expect(pearson([5, 5, 5, 5], [1, 2, 3, 4])).toBeNull();
  });

  it("throws on a length mismatch", () => {
    expect(() => pearson([1, 2, 3], [1, 2])).toThrow(/length mismatch/);
  });
});

describe("averageRanks", () => {
  it("assigns the average rank to ties (matches scipy rankdata)", () => {
    expect(averageRanks([1, 1, 2, 2, 3, 3, 4, 5])).toEqual([
      1.5, 1.5, 3.5, 3.5, 5.5, 5.5, 7, 8,
    ]);
    expect(averageRanks([10, 9, 8, 8, 7, 6, 3, 1])).toEqual([
      8, 7, 5.5, 5.5, 4, 3, 2, 1,
    ]);
  });
});

describe("spearman", () => {
  it("is 1 for any strictly increasing (monotonic) relation, even non-linear", () => {
    expect(spearman([1, 2, 3, 4, 5], [1, 4, 9, 16, 25])).toBeCloseTo(1, 12);
  });

  it("matches scipy with ties (rho = -0.98787834…)", () => {
    const a = [1, 1, 2, 2, 3, 3, 4, 5];
    const b = [10, 9, 8, 8, 7, 6, 3, 1];
    expect(spearman(a, b)).toBeCloseTo(-0.9878783399072131, 12);
  });

  it("differs from Pearson on a curved monotone relation", () => {
    const x = [1, 2, 3, 4, 5];
    const y = [1, 4, 9, 16, 25];
    expect(pearson(x, y)).toBeCloseTo(0.981104910251593, 9);
    expect(spearman(x, y)).toBeCloseTo(1, 9);
  });

  it("returns null for a constant array", () => {
    expect(spearman([2, 2, 2, 2], [1, 2, 3, 4])).toBeNull();
  });
});

describe("assertAligned", () => {
  it("passes for equal lengths and throws for a mismatch", () => {
    expect(() =>
      assertAligned([
        { name: "a", length: 3 },
        { name: "b", length: 3 },
      ]),
    ).not.toThrow();
    expect(() =>
      assertAligned([
        { name: "a", length: 3 },
        { name: "b", length: 2 },
      ]),
    ).toThrow(/Column "b" has 2 values but "a" has 3/);
  });
});

describe("computeCorrelation", () => {
  const x: NumCell[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  const y: NumCell[] = [2, 1, 4, 3, 6, 5, 8, 7, 10, 9];
  const grp: NumCell[] = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2];

  it("returns the overall coefficient, missing breakdown and points when ungrouped", () => {
    const r = computeCorrelation(x, y, "pearson");
    expect(r.method).toBe("pearson");
    expect(r.overall.r).toBeCloseTo(0.93939, 4);
    expect(r.overall.n).toBe(10);
    expect(r.groups).toBeNull();
    expect(r.points.x).toHaveLength(10);
    expect(r.points.group).toBeNull();
    expect(r.missing).toEqual({ total: 10, x: 0, y: 0, either: 0 });
  });

  it("computes deterministic group results in the config value order", () => {
    const r = computeCorrelation(x, y, "pearson", {
      field: "GRP",
      codes: grp,
      values: [
        { code: 2, label: "Two" },
        { code: 1, label: "One" },
      ],
    });
    expect(r.groups?.map((g) => g.label)).toEqual(["Two", "One"]);
    expect(r.groups?.map((g) => g.n)).toEqual([5, 5]);
    expect(r.groups?.[0]?.key).toBe("2");
    // point group codes align with the retained points
    expect(r.points.group).toEqual([1, 1, 1, 1, 1, 2, 2, 2, 2, 2]);
  });

  it("reports a reason instead of throwing for a too-small group", () => {
    const codes: NumCell[] = [1, 1, 2, 2, 2, 2, 2, 2, 2, 2];
    const r = computeCorrelation(x, y, "pearson", {
      field: "GRP",
      codes,
      values: [
        { code: 1, label: "One" },
        { code: 2, label: "Two" },
      ],
    });
    expect(r.groups?.[0]).toMatchObject({ n: 2, r: null, reason: REASON_TOO_FEW });
    expect(r.groups?.[1]?.r).not.toBeNull();
  });

  it("reports a zero-variance reason for a constant column", () => {
    const flat: NumCell[] = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3];
    const r = computeCorrelation(flat, y, "pearson");
    expect(r.overall).toMatchObject({ r: null, reason: REASON_NO_VARIANCE });
  });

  it("excludes non-finite rows from n and from the plotted points", () => {
    const xn: NumCell[] = [1, 2, null, 4, 5, 6, 7, 8, 9, 10];
    const r = computeCorrelation(xn, y, "spearman");
    expect(r.overall.n).toBe(9);
    expect(r.points.x).toHaveLength(9);
    expect(r.missing.either).toBe(1);
  });

  it("throws when the grouping column is misaligned", () => {
    expect(() =>
      computeCorrelation(x, y, "pearson", {
        field: "GRP",
        codes: [1, 2, 3],
        values: [{ code: 1, label: "One" }],
      }),
    ).toThrow(/GRP/);
  });
});

describe("computeCorrelation — against the committed abide_retention.json", () => {
  async function loadColumns() {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_retention.json",
      import.meta.url,
    );
    const art = JSON.parse(await fs.readFile(url, "utf-8")) as {
      columns: Record<string, (number | string | null)[]>;
    };
    const num = (name: string): NumCell[] =>
      art.columns[name]!.map((v) =>
        typeof v === "number" && Number.isFinite(v) ? v : null,
      );
    return { art, num };
  }

  it("FIQ ~ SRS_TOTAL_RAW: Pearson -0.2404, Spearman -0.2358, n = 778 (cross-checked with pandas)", async () => {
    const { num } = await loadColumns();
    const p = computeCorrelation(num("FIQ"), num("SRS_TOTAL_RAW"), "pearson");
    const s = computeCorrelation(num("FIQ"), num("SRS_TOTAL_RAW"), "spearman");
    expect(p.overall.n).toBe(778);
    expect(p.overall.r).toBeCloseTo(-0.240447, 5);
    expect(s.overall.r).toBeCloseTo(-0.235794, 5);
    expect(p.missing).toMatchObject({ total: 1114, x: 99, y: 329, either: 336 });
  });

  it("FIQ ~ VIQ (a part–whole composite): Pearson 0.8330, n = 796", async () => {
    const { num } = await loadColumns();
    const r = computeCorrelation(num("FIQ"), num("VIQ"), "pearson");
    expect(r.overall.n).toBe(796);
    expect(r.overall.r).toBeCloseTo(0.832969, 5);
  });

  it("ADOS-G ~ ADOS-2 total: high Pearson 0.8815 but only n = 81 of 1114", async () => {
    const { num } = await loadColumns();
    const r = computeCorrelation(num("ADOS_G_TOTAL"), num("ADOS_2_TOTAL"), "pearson");
    expect(r.overall.n).toBe(81);
    expect(r.overall.r).toBeCloseTo(0.881504, 5);
  });

  it("AGE_AT_SCAN ~ FIQ: essentially no association (Pearson 0.0084) on n = 1015", async () => {
    const { num } = await loadColumns();
    const r = computeCorrelation(num("AGE_AT_SCAN"), num("FIQ"), "pearson");
    expect(r.overall.n).toBe(1015);
    expect(r.overall.r).toBeCloseTo(0.008374, 5);
  });

  it("FIQ ~ SRS_TOTAL_RAW grouped by diagnosis: ~0 within each group (overall -0.24 was mostly between-group)", async () => {
    const { num } = await loadColumns();
    const r = computeCorrelation(num("FIQ"), num("SRS_TOTAL_RAW"), "pearson", {
      field: "DX_GROUP",
      codes: num("DX_GROUP"),
      values: [
        { code: 1, label: "Autism" },
        { code: 2, label: "Control" },
      ],
    });
    expect(r.groups?.map((g) => g.n)).toEqual([372, 406]);
    expect(r.groups?.[0]?.r).toBeCloseTo(-0.026065, 4);
    expect(r.groups?.[1]?.r).toBeCloseTo(-0.055744, 4);
  });

  it("SRS_TOTAL_RAW ~ SCQ_TOTAL grouped by diagnosis: overall 0.84, within-group ~0.5 / ~0.4", async () => {
    const { num } = await loadColumns();
    const r = computeCorrelation(num("SRS_TOTAL_RAW"), num("SCQ_TOTAL"), "pearson", {
      field: "DX_GROUP",
      codes: num("DX_GROUP"),
      values: [
        { code: 1, label: "Autism" },
        { code: 2, label: "Control" },
      ],
    });
    expect(r.overall.r).toBeCloseTo(0.842054, 5);
    expect(r.groups?.[0]).toMatchObject({ n: 151 });
    expect(r.groups?.[0]?.r).toBeCloseTo(0.542738, 4);
    expect(r.groups?.[1]?.r).toBeCloseTo(0.412674, 4);
  });
});
