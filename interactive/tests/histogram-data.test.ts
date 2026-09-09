import { describe, expect, it } from "vitest";
import { parseAbideHistogramData } from "../src/histogram-data";

const base = {
  schemaVersion: 1 as const,
  rowCount: 3,
  source: { url: "https://example/abide.csv", sha256: "deadbeef" },
  variables: [{ name: "FIQ", availableN: 2, missingN: 1 }],
  columns: { FIQ: [100, null, 110] },
};

describe("parseAbideHistogramData", () => {
  it("accepts a well-formed artifact", () => {
    const r = parseAbideHistogramData(base);
    expect(r.ok).toBe(true);
  });

  it("rejects a column whose length disagrees with rowCount", () => {
    const r = parseAbideHistogramData({ ...base, columns: { FIQ: [100, null] } });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/expected rowCount 3/);
  });

  it("rejects availableN metadata that disagrees with the data", () => {
    const r = parseAbideHistogramData({
      ...base,
      variables: [{ name: "FIQ", availableN: 3, missingN: 0 }],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/availableN/);
  });

  it("rejects a NaN value in a column", () => {
    const r = parseAbideHistogramData({ ...base, columns: { FIQ: [100, Number.NaN, 110] } });
    expect(r.ok).toBe(false);
  });

  it("rejects a wrong schemaVersion", () => {
    const r = parseAbideHistogramData({ ...base, schemaVersion: 2 });
    expect(r.ok).toBe(false);
  });

  it("rejects variable metadata with no matching column", () => {
    const r = parseAbideHistogramData({
      ...base,
      variables: [{ name: "VIQ", availableN: 0, missingN: 3 }],
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/no matching column/);
  });

  it("validates the committed abide_histogram.json artifact", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/abide_histogram.json",
      import.meta.url,
    );
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseAbideHistogramData(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.rowCount).toBe(1114);
      expect(Object.keys(r.data.columns).sort()).toEqual(
        [
          "ADOS_2_TOTAL",
          "ADOS_G_TOTAL",
          "AGE_AT_SCAN",
          "FIQ",
          "PIQ",
          "SCQ_TOTAL",
          "SRS_TOTAL_RAW",
          "VIQ",
        ],
      );
    }
  });
});
