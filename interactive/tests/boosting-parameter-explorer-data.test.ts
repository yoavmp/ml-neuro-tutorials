import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseBoostingParameterExplorerData } from "../src/boosting-parameter-explorer-data";

const REAL_ARTIFACT = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../book/_static/widgets/data/boosting_parameter_explorer.json", import.meta.url)),
    "utf-8",
  ),
);

function gridPoint(nVal = 3) {
  return {
    trainMSE: 5,
    valMSE: 6,
    valR2: 0.5,
    predictedValidation: Array.from({ length: nVal }, () => 10),
  };
}

function base() {
  const nVal = 3;
  const learningRateGrid = [0.1, 0.2];
  const depthGrid = [1, 2];
  const nTreesGrid = [1, 5, 10];
  const grid: Record<string, unknown> = {};
  for (const lr of learningRateGrid) {
    for (const depth of depthGrid) {
      const byNTrees: Record<string, unknown> = {};
      for (const n of nTreesGrid) byNTrees[String(n)] = gridPoint(nVal);
      grid[`${lr}|${depth}`] = { learningRate: lr, maxDepth: depth, byNTrees };
    }
  }
  return {
    schemaVersion: 1 as const,
    activity: "boosting-parameter-explorer" as const,
    source: { pinnedCommit: "abc", brainTableSha256: "x".repeat(64), phenotypeTableSha256: "y".repeat(64) },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: {
      outerHoldout: { test_size: 0.25, random_state: 42, stratify: "group" },
      devSplit: { test_size: 0.25, random_state: 7, stratify: "group", nFit: 564, nVal },
    },
    lockedTestExcluded: true as const,
    learningRateGrid,
    depthGrid,
    nTreesGrid,
    defaults: { learningRate: 0.1, depth: 2, nTrees: 5 },
    observedValidation: Array.from({ length: nVal }, () => 12),
    grid,
  };
}

describe("parseBoostingParameterExplorerData", () => {
  it("accepts the real committed artifact", () => {
    const r = parseBoostingParameterExplorerData(REAL_ARTIFACT);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("accepts a well-formed minimal artifact", () => {
    const r = parseBoostingParameterExplorerData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseBoostingParameterExplorerData({ ...base(), activity: "boosting-step-by-step" }).ok).toBe(false);
  });

  it("rejects lockedTestExcluded=false", () => {
    const b = base() as Record<string, unknown>;
    b.lockedTestExcluded = false;
    expect(parseBoostingParameterExplorerData(b).ok).toBe(false);
  });

  it("rejects a missing (learningRate, depth) grid entry", () => {
    const b = base();
    delete (b.grid as Record<string, unknown>)["0.2|2"];
    expect(parseBoostingParameterExplorerData(b).ok).toBe(false);
  });

  it("rejects a prediction array misaligned with observedValidation", () => {
    const b = base();
    (b.grid["0.1|1"] as { byNTrees: Record<string, { predictedValidation: number[] }> }).byNTrees["1"]!.predictedValidation = [1, 2];
    expect(parseBoostingParameterExplorerData(b).ok).toBe(false);
  });

  it("rejects a default not present in its own grid", () => {
    const b = base();
    b.defaults.nTrees = 999;
    expect(parseBoostingParameterExplorerData(b).ok).toBe(false);
  });

  it("rejects observedValidation length mismatched with devSplit.nVal", () => {
    const b = base();
    b.split.devSplit.nVal = 999;
    expect(parseBoostingParameterExplorerData(b).ok).toBe(false);
  });
});
