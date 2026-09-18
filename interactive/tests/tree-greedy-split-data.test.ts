import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseTreeGreedySplitData } from "../src/tree-greedy-split-data";

const REAL_ARTIFACT = JSON.parse(
  readFileSync(
    fileURLToPath(new URL("../../book/_static/widgets/data/tree_greedy_split.json", import.meta.url)),
    "utf-8",
  ),
);

function candidates(n = 3) {
  return {
    thresholds: Array.from({ length: n }, (_, i) => i + 0.5),
    splitMSE: Array.from({ length: n }, () => 10),
    reduction: Array.from({ length: n }, () => 5),
    nLeft: Array.from({ length: n }, () => 2),
    nRight: Array.from({ length: n }, () => 2),
  };
}

function round(id: string, label: string, activeObservationIds: number[]) {
  return {
    id,
    label,
    activeObservationIds,
    parentMSE: 20,
    candidates: { x1: candidates(), x2: candidates() },
    optimal: {
      feature: "x1" as const,
      thresholdIndex: 1,
      threshold: 1.5,
      splitMSE: 10,
      reduction: 10,
      nLeft: activeObservationIds.length / 2,
      nRight: activeObservationIds.length / 2,
      leftMean: 5,
      rightMean: 15,
    },
  };
}

function base() {
  const observations = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    x1: i % 4,
    x2: Math.floor(i / 4),
    y: i < 6 ? 5 + i : 15 + i,
  }));
  const allIds = observations.map((o) => o.id);
  return {
    schemaVersion: 1 as const,
    activity: "tree-greedy-split" as const,
    syntheticDataNote: "This dataset is synthetic.",
    features: { x1: { name: "x1", label: "X1" }, x2: { name: "x2", label: "X2" } },
    observations,
    rounds: [
      round("root", "Root node", allIds),
      round("left-child", "Left child", allIds.slice(0, 6)),
      round("right-child", "Right child", allIds.slice(6)),
    ],
  };
}

describe("parseTreeGreedySplitData", () => {
  it("accepts the real committed artifact", () => {
    const r = parseTreeGreedySplitData(REAL_ARTIFACT);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("accepts a well-formed minimal artifact", () => {
    const r = parseTreeGreedySplitData(base());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a wrong activity tag", () => {
    expect(parseTreeGreedySplitData({ ...base(), activity: "tree-ensemble-compare" }).ok).toBe(false);
  });

  it("rejects fewer than 3 rounds", () => {
    const b = base();
    b.rounds = [b.rounds[0]!];
    expect(parseTreeGreedySplitData(b).ok).toBe(false);
  });

  it("rejects candidate arrays of mismatched length", () => {
    const b = base();
    b.rounds[0]!.candidates.x1.splitMSE = [1, 2];
    expect(parseTreeGreedySplitData(b).ok).toBe(false);
  });

  it("rejects an optimal threshold that disagrees with its own thresholdIndex", () => {
    const b = base();
    b.rounds[0]!.optimal.threshold = 999;
    expect(parseTreeGreedySplitData(b).ok).toBe(false);
  });

  it("rejects an activeObservationIds entry that names an unknown observation", () => {
    const b = base();
    b.rounds[0]!.activeObservationIds = [0, 1, 2, 999];
    expect(parseTreeGreedySplitData(b).ok).toBe(false);
  });

  it("rejects fewer than 12 or more than 20 observations", () => {
    const b = base();
    b.observations = b.observations.slice(0, 2);
    expect(parseTreeGreedySplitData(b).ok).toBe(false);
  });
});
