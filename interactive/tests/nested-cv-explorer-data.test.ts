import { describe, expect, it } from "vitest";
import { parseNestedCvExplorerData } from "../src/nested-cv-explorer-data";

const source = {
  pinnedCommit: "abc",
  brainTableSha256: "x".repeat(64),
  phenotypeTableSha256: "y".repeat(64),
};

function foldRow(outerFold: number, selectedK: number) {
  return {
    outerFold,
    nTrain: 803,
    nTest: 201,
    innerMseByK: { "5": 40, "15": 32, "30": 34, "50": 37, "75": 40 },
    selectedK,
    bestInnerMse: 32,
    outerTestMse: 36,
    outerTestR2: 0.67,
  };
}

function makeValid() {
  return {
    schemaVersion: 1,
    activity: "nested-cv-explorer",
    source,
    candidateKs: [5, 15, 30, 50, 75],
    nOuter: 2,
    nInner: 5,
    featureCount: 360,
    foldRows: [foldRow(0, 15), foldRow(1, 15)],
    selectedKPerFold: [15, 15],
    selectedKVariesAcrossFolds: false,
    meanOuterTestMse: 36,
    stdOuterTestMse: 1,
    meanOuterTestR2: 0.67,
    stdOuterTestR2: 0.01,
  };
}

describe("parseNestedCvExplorerData", () => {
  it("accepts a well-formed payload", () => {
    const r = parseNestedCvExplorerData(makeValid());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects foldRows.length disagreeing with nOuter", () => {
    const data = makeValid();
    data.nOuter = 5;
    const r = parseNestedCvExplorerData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a selectedKVariesAcrossFolds that disagrees with the fold data", () => {
    const data = makeValid();
    data.selectedKVariesAcrossFolds = true;
    const r = parseNestedCvExplorerData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a selectedK not present in candidateKs", () => {
    const data = makeValid();
    data.foldRows[0]!.selectedK = 999;
    const r = parseNestedCvExplorerData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a selectedKPerFold order that disagrees with foldRows", () => {
    const data = makeValid();
    data.selectedKPerFold = [30, 15];
    const r = parseNestedCvExplorerData(data);
    expect(r.ok).toBe(false);
  });

  it("accepts the shipped wp27_nested_cv_explorer.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/wp27_nested_cv_explorer.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseNestedCvExplorerData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
