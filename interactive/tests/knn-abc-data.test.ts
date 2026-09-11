import { describe, expect, it } from "vitest";
import { parseKnnAbcData } from "../src/knn-abc-data";

function base() {
  // n_train = 3, n_test = 2, kMax = min(3, 2) = 2. Deliberately small.
  return {
    schemaVersion: 1 as const,
    activity: "knn-abc" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: { nTrain: 3, nTest: 2, kMax: 2 },
    selectedKFromAudit: 1,
    observedTrain: [10, 20, 30],
    observedTest: [12, 25],
    neighborTargetsA: [
      [10, 20],
      [30, 20],
    ],
    neighborTargetsB: [
      [10, 20],
      [20, 10],
      [30, 20],
    ],
    neighborTargetsC: [
      [12, 25],
      [25, 12],
    ],
  };
}

describe("parseKnnAbcData", () => {
  it("accepts a well-formed artifact", () => {
    const r = parseKnnAbcData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseKnnAbcData({ ...base(), activity: "knn-explore" }).ok).toBe(false);
  });

  it("rejects kMax not equal to min(nTrain, nTest)", () => {
    const b = base();
    b.split.kMax = 3;
    expect(parseKnnAbcData(b).ok).toBe(false);
  });

  it("rejects neighborTargetsB with the wrong row count", () => {
    const b = base();
    b.neighborTargetsB.pop();
    const r = parseKnnAbcData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborTargetsB/);
  });

  it("rejects a row of the wrong (non-kMax) length", () => {
    const b = base();
    b.neighborTargetsA[0] = [10, 20, 30];
    const r = parseKnnAbcData(b);
    expect(r.ok).toBe(false);
  });

  it("rejects k=1 (B) not matching observedTrain", () => {
    const b = base();
    b.neighborTargetsB[0]![0] = 999;
    const r = parseKnnAbcData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborTargetsB/);
  });

  it("rejects k=1 (C) not matching observedTest", () => {
    const b = base();
    b.neighborTargetsC[0]![0] = 999;
    const r = parseKnnAbcData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/neighborTargetsC/);
  });

  it("rejects selectedKFromAudit out of range", () => {
    const b = base();
    b.selectedKFromAudit = 99;
    expect(parseKnnAbcData(b).ok).toBe(false);
  });

  it("rejects an identifier-shaped top-level key", () => {
    const b = base() as Record<string, unknown>;
    b.SUB_ID = [1, 2, 3];
    const r = parseKnnAbcData(b);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/identifier-shaped/);
  });

  it("validates the committed abide_knn_abc.json artifact", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL("../../book/_static/widgets/data/abide_knn_abc.json", import.meta.url);
    const raw = JSON.parse(await fs.readFile(url, "utf-8")) as unknown;
    const r = parseKnnAbcData(raw);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
    if (r.ok) {
      expect(r.data.target.name).toBe("age");
      expect(r.data.featureRecipe.featureCount).toBe(360);
      expect(r.data.split.nTrain).toBe(753);
      expect(r.data.split.nTest).toBe(251);
      expect(r.data.split.kMax).toBe(251);
      expect(r.data.observedTrain).toHaveLength(753);
      expect(r.data.observedTest).toHaveLength(251);
      expect(r.data.neighborTargetsA).toHaveLength(251);
      expect(r.data.neighborTargetsB).toHaveLength(753);
      expect(r.data.neighborTargetsC).toHaveLength(251);
      expect(r.data.neighborTargetsA[0]).toHaveLength(251);
      // k=1 endpoints
      const bFirst = r.data.neighborTargetsB.map((row) => row[0]);
      expect(bFirst).toEqual(r.data.observedTrain);
      const cFirst = r.data.neighborTargetsC.map((row) => row[0]);
      expect(cFirst).toEqual(r.data.observedTest);
      expect(r.data.selectedKFromAudit).toBe(15);
    }
  });
});
