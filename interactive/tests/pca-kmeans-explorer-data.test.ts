import { describe, expect, it } from "vitest";
import {
  parsePcaKmeansExplorerData,
  catalogEntryFor,
  externalValuesFor,
  catalogKey,
  type PcaKmeansExplorerData,
} from "../src/pca-kmeans-explorer-data";

function validData(): PcaKmeansExplorerData {
  const n = 4;
  const retainedPcGrid = [2];
  const kGrid = [2];
  const seeds = [0];
  const catalog: PcaKmeansExplorerData["catalog"] = {
    "2|2|0": {
      retainedPc: 2,
      k: 2,
      seed: 0,
      clusterLabels: [0, 1, 0, 1],
      inertia: 4.2,
      silhouette: 0.3,
      clusterSizes: [2, 2],
      centersPC1PC2: [
        [0, 0],
        [1, 1],
      ],
    },
  };
  return {
    schemaVersion: 1,
    activity: "pca-kmeans-explorer",
    cohortNote: "note",
    nParticipants: n,
    pca: { nComponentsFit: 2, note: "note" },
    participants: {
      pc1: [0.1, 0.2, 0.3, 0.4],
      pc2: [0.4, 0.3, 0.2, 0.1],
      external: {
        group: [1, 2, 1, 2],
        sex: ["M", "F", "M", "F"],
        site: ["NYU", "UCLA", "NYU", "UCLA"],
        age: [10, 20, 30, 40],
      },
    },
    externalVariableLabels: { group: "diagnosis", sex: "sex", site: "site", age: "age" },
    retainedPcGrid,
    kGrid,
    seeds,
    nInit: 10,
    catalog,
  };
}

describe("parsePcaKmeansExplorerData", () => {
  it("accepts valid data", () => {
    const result = parsePcaKmeansExplorerData(validData());
    expect(result.ok).toBe(true);
  });

  it("rejects a missing catalogue combination", () => {
    const bad = validData();
    bad.retainedPcGrid = [2, 5];
    const result = parsePcaKmeansExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects mismatched participant-array lengths", () => {
    const bad = validData();
    bad.participants.pc2 = [0.1, 0.2];
    const result = parsePcaKmeansExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a cluster-labels array of the wrong length", () => {
    const bad = validData();
    bad.catalog["2|2|0"]!.clusterLabels = [0, 1];
    const result = parsePcaKmeansExplorerData(bad);
    expect(result.ok).toBe(false);
  });
});

describe("catalogKey / catalogEntryFor", () => {
  it("builds the pipe-delimited key", () => {
    expect(catalogKey(10, 3, 1)).toBe("10|3|1");
  });

  it("looks up an existing combination", () => {
    const data = validData();
    const entry = catalogEntryFor(data, 2, 2, 0);
    expect(entry.k).toBe(2);
    expect(entry.clusterLabels).toEqual([0, 1, 0, 1]);
  });

  it("throws a readable error for a missing combination", () => {
    const data = validData();
    expect(() => catalogEntryFor(data, 50, 6, 99)).toThrow(/no catalogue entry/);
  });
});

describe("externalValuesFor", () => {
  it("returns the requested external variable's per-participant array", () => {
    const data = validData();
    expect(externalValuesFor(data, "site")).toEqual(["NYU", "UCLA", "NYU", "UCLA"]);
    expect(externalValuesFor(data, "age")).toEqual([10, 20, 30, 40]);
  });
});
