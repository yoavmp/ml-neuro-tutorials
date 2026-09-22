import { describe, expect, it } from "vitest";
import {
  parseSvmExplorerData,
  catalogEntryFor,
  catalogKey,
  decodeDecisionGrid,
  decodeDecisionGridRow,
  type SvmExplorerData,
  type SvmExplorerCatalogEntry,
} from "../src/svm-explorer-data";

function validData(): SvmExplorerData {
  const points = [
    { id: 0, x: -1, y: -1, label: 0 as const },
    { id: 1, x: -1, y: -0.5, label: 0 as const },
    { id: 2, x: 1, y: 1, label: 1 as const },
    { id: 3, x: 1, y: 0.5, label: 1 as const },
  ];
  function catalogFor(dataset: "linear" | "nonlinear") {
    const catalog: Record<string, SvmExplorerCatalogEntry> = {};
    catalog[`${dataset}|linear|1|na`] = {
      dataset,
      kernel: "linear",
      c: 1,
      gamma: null,
      trainAccuracy: 1,
      valAccuracy: 1,
      nSupportVectors: 2,
      supportVectorIds: [0, 2],
      decisionGrid: ["00", "11"],
    };
    catalog[`${dataset}|rbf|1|1`] = {
      dataset,
      kernel: "rbf",
      c: 1,
      gamma: 1,
      trainAccuracy: 1,
      valAccuracy: 0.9,
      nSupportVectors: 2,
      supportVectorIds: [0, 2],
      decisionGrid: ["01", "10"],
    };
    return catalog;
  }
  return {
    schemaVersion: 1,
    activity: "svm-explorer",
    syntheticDataNote: "note",
    kernelOptions: ["linear", "poly", "rbf"],
    polyDegree: 3,
    cGrid: [0.1, 1, 10, 100],
    gammaGrid: [0.1, 1, 10],
    datasets: {
      linear: { points, trainIds: [0, 2], valIds: [1, 3], gridX: [-1, 1], gridY: [-1, 1], catalog: catalogFor("linear") },
      nonlinear: { points, trainIds: [0, 2], valIds: [1, 3], gridX: [-1, 1], gridY: [-1, 1], catalog: catalogFor("nonlinear") },
    },
  };
}

describe("parseSvmExplorerData", () => {
  it("accepts valid data", () => {
    const result = parseSvmExplorerData(validData());
    expect(result.ok).toBe(true);
  });

  it("rejects a decisionGrid with a bad character", () => {
    const bad = validData();
    bad.datasets.linear!.catalog["linear|linear|1|na"]!.decisionGrid = ["0x", "11"];
    const result = parseSvmExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a decisionGrid whose dimensions don't match gridX/gridY", () => {
    const bad = validData();
    bad.datasets.linear!.catalog["linear|linear|1|na"]!.decisionGrid = ["000", "111"];
    const result = parseSvmExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a support vector id that is not a training row", () => {
    const bad = validData();
    bad.datasets.linear!.catalog["linear|linear|1|na"]!.supportVectorIds = [1];
    const result = parseSvmExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects trainIds/valIds that do not partition every point", () => {
    const bad = validData();
    bad.datasets.linear!.trainIds = [0];
    const result = parseSvmExplorerData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects malformed input with a readable error", () => {
    const result = parseSvmExplorerData({ nope: true });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain("Invalid svm-explorer data");
    }
  });
});

describe("catalogKey / catalogEntryFor", () => {
  it("builds 'na' for the linear kernel's gamma slot", () => {
    expect(catalogKey("linear", "linear", 1, null)).toBe("linear|linear|1|na");
  });

  it("builds the numeric gamma slot for rbf", () => {
    expect(catalogKey("linear", "rbf", 1, 1)).toBe("linear|rbf|1|1");
  });

  it("looks up the matching catalogue entry", () => {
    const data = validData();
    const entry = catalogEntryFor(data, "nonlinear", "rbf", 1, 1);
    expect(entry.kernel).toBe("rbf");
    expect(entry.dataset).toBe("nonlinear");
  });

  it("throws a readable error for a missing combination", () => {
    const data = validData();
    expect(() => catalogEntryFor(data, "linear", "poly", 100, 10)).toThrow(/no catalogue entry/);
  });
});

describe("decodeDecisionGridRow / decodeDecisionGrid", () => {
  it("decodes a digit string into numbers", () => {
    expect(decodeDecisionGridRow("0110")).toEqual([0, 1, 1, 0]);
  });

  it("decodes every row of a grid", () => {
    expect(decodeDecisionGrid(["00", "11"])).toEqual([
      [0, 0],
      [1, 1],
    ]);
  });
});
