import { describe, expect, it } from "vitest";
import {
  findKResult,
  parseHarFoldCompareData,
  participantsSplitAcrossFold,
  sortedActivityIds,
} from "../src/har-fold-compare-data";

const N_SPLITS = 2;

function confusionMatrix6x6(): number[][] {
  return Array.from({ length: 6 }, () => Array.from({ length: 6 }, () => 0));
}

function foldMetrics() {
  return {
    accPerFold: Array.from({ length: N_SPLITS }, () => 0.8),
    f1PerFold: Array.from({ length: N_SPLITS }, () => 0.75),
    confusionPerFold: Array.from({ length: N_SPLITS }, () => confusionMatrix6x6()),
    accMean: 0.8,
    f1Mean: 0.75,
  };
}

function kResult(k: number) {
  return {
    k,
    ordinary: foldMetrics(),
    grouped: foldMetrics(),
    accGap: 0.05,
    f1Gap: 0.06,
  };
}

function validPayload() {
  return {
    schemaVersion: 1,
    activity: "har-fold-compare",
    activityLabels: {
      "1": "WALKING",
      "2": "WALKING_UPSTAIRS",
      "3": "WALKING_DOWNSTAIRS",
      "4": "SITTING",
      "5": "STANDING",
      "6": "LAYING",
    },
    kValues: [1, 3],
    nSplits: N_SPLITS,
    nRows: 100,
    nParticipants: 2,
    observationsPerParticipant: { min: 40, max: 60, mean: 50, median: 50 },
    kResults: [kResult(1), kResult(3)],
    participantFolds: [
      { participantId: 1, ordinaryFolds: [0, 1], groupedFold: 0, nObservations: 50 },
      { participantId: 2, ordinaryFolds: [1], groupedFold: 1, nObservations: 50 },
    ],
    source: {
      sourceUrl: "https://archive.ics.uci.edu/dataset/240",
      doi: "https://doi.org/10.24432/C54S4K",
      license: "CC BY 4.0",
    },
  };
}

describe("parseHarFoldCompareData", () => {
  it("accepts a well-formed payload", () => {
    const result = parseHarFoldCompareData(validPayload());
    expect(result.ok).toBe(true);
  });

  it("rejects a confusion matrix that is not 6x6", () => {
    const bad = validPayload();
    bad.kResults[0]!.ordinary.confusionPerFold[0] = [[0, 0]];
    expect(parseHarFoldCompareData(bad).ok).toBe(false);
  });

  it("rejects kResults whose k values do not match kValues", () => {
    const bad = validPayload();
    bad.kResults[0]!.k = 999;
    expect(parseHarFoldCompareData(bad).ok).toBe(false);
  });

  it("rejects participantFolds whose length does not match nParticipants", () => {
    const bad = validPayload();
    bad.participantFolds = bad.participantFolds.slice(0, 1);
    expect(parseHarFoldCompareData(bad).ok).toBe(false);
  });

  it("rejects an out-of-range groupedFold", () => {
    const bad = validPayload();
    bad.participantFolds[0]!.groupedFold = 99;
    expect(parseHarFoldCompareData(bad).ok).toBe(false);
  });

  it("sortedActivityIds returns the six activity ids in ascending order", () => {
    const result = parseHarFoldCompareData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(sortedActivityIds(result.data)).toEqual([1, 2, 3, 4, 5, 6]);
    }
  });

  it("findKResult returns the matching entry and throws for an unknown k", () => {
    const result = parseHarFoldCompareData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(findKResult(result.data, 3).k).toBe(3);
      expect(() => findKResult(result.data, 999)).toThrow();
    }
  });

  it("participantsSplitAcrossFold counts only multi-fold ordinary participants, and is always 0 for grouped", () => {
    const result = parseHarFoldCompareData(validPayload());
    expect(result.ok).toBe(true);
    if (result.ok) {
      // participant 1 spans folds [0,1]; participant 2 spans only [1].
      expect(participantsSplitAcrossFold(result.data, "ordinary", 0)).toBe(1);
      expect(participantsSplitAcrossFold(result.data, "ordinary", 1)).toBe(1);
      expect(participantsSplitAcrossFold(result.data, "grouped", 0)).toBe(0);
      expect(participantsSplitAcrossFold(result.data, "grouped", 1)).toBe(0);
    }
  });

  it("accepts the shipped data/uci_har_fold_comparison.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/uci_har_fold_comparison.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseHarFoldCompareData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
