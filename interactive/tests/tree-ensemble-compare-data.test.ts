import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseTreeEnsembleCompareData } from "../src/tree-ensemble-compare-data";

const REAL_ARTIFACT = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../book/_static/widgets/data/tree_ensemble_compare.json", import.meta.url)),
    "utf-8",
  ),
);

const N_TREES_GRID = [1, 5];
const N_VAL = 3;

function modelPoint(valMSE = 20) {
  return { valMSE, valR2: 0.5, predictedValidation: [10, 11, 12] };
}

function byNTrees() {
  const out: Record<string, ReturnType<typeof modelPoint>> = {};
  for (const n of N_TREES_GRID) out[String(n)] = modelPoint();
  return out;
}

function replicate(seed: number) {
  return {
    seed,
    nTrain: 100,
    rootSplit: { feature: "fsCT_L_3a_ROI", threshold: 1.9 },
    singleTree: modelPoint(),
    bagging: { byNTrees: byNTrees() },
    randomForest: { byNTrees: byNTrees() },
  };
}

function summaryPoint() {
  return { meanMSE: 20, sdMSE: 2, values: [18, 22] };
}

function base() {
  const summaryByNTrees: Record<string, ReturnType<typeof summaryPoint>> = {};
  for (const n of N_TREES_GRID) summaryByNTrees[String(n)] = summaryPoint();
  return {
    schemaVersion: 1 as const,
    activity: "tree-ensemble-compare" as const,
    source: { pinnedCommit: "abc123", brainTableSha256: "aa", phenotypeTableSha256: "bb" },
    target: { name: "age", label: "Age at scan", unit: "years" },
    featureRecipe: { bundle: "all-eligible", measures: ["CT"], featureCount: 360 },
    split: {
      outerHoldout: { test_size: 0.25, random_state: 42, stratify: "group", nTrain: 753, nTest: 251 },
      devSplit: { test_size: 0.25, random_state: 7, stratify: "group", nFit: 564, nVal: N_VAL },
    },
    settings: {
      replicateFraction: 0.7,
      replicatePoolSize: 564,
      treeSettings: { max_depth: 6, min_samples_leaf: 5, random_state: 42 },
      randomForestMaxFeatures: 19,
    },
    nTreesGrid: N_TREES_GRID,
    observedValidation: [10, 11, 12],
    replicates: [replicate(0), replicate(1)],
    summary: {
      singleTree: summaryPoint(),
      bagging: summaryByNTrees,
      randomForest: summaryByNTrees,
    },
  };
}

describe("parseTreeEnsembleCompareData", () => {
  it("accepts the real committed artifact", () => {
    const r = parseTreeEnsembleCompareData(REAL_ARTIFACT);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("accepts a well-formed minimal artifact", () => {
    const r = parseTreeEnsembleCompareData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseTreeEnsembleCompareData({ ...base(), activity: "tree-greedy-split" }).ok).toBe(false);
  });

  it("rejects observedValidation length mismatched with split.devSplit.nVal", () => {
    const b = base();
    b.split.devSplit.nVal = 999;
    expect(parseTreeEnsembleCompareData(b).ok).toBe(false);
  });

  it("rejects a replicate whose singleTree prediction length disagrees with nVal", () => {
    const b = base();
    b.replicates[0]!.singleTree.predictedValidation = [1, 2];
    expect(parseTreeEnsembleCompareData(b).ok).toBe(false);
  });

  it("rejects a replicate missing a bagging entry for a declared n_trees", () => {
    const b = base();
    delete b.replicates[0]!.bagging.byNTrees[String(N_TREES_GRID[0])];
    expect(parseTreeEnsembleCompareData(b).ok).toBe(false);
  });

  it("rejects a summary missing an entry for a declared n_trees", () => {
    const b = base();
    delete (b.summary.randomForest as Record<string, unknown>)[String(N_TREES_GRID[1])];
    expect(parseTreeEnsembleCompareData(b).ok).toBe(false);
  });

  it("rejects fewer than 2 replicates", () => {
    const b = base();
    b.replicates = [replicate(0)];
    expect(parseTreeEnsembleCompareData(b).ok).toBe(false);
  });
});
