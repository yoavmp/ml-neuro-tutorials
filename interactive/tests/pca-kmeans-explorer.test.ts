import { describe, expect, it } from "vitest";
import {
  CLUSTER_COLORS,
  clusterColor,
  sharedAxisRange,
  indicesForCluster,
  categoryShareByCluster,
  siteShareMatrix,
  agesByCluster,
} from "../src/pca-kmeans-explorer";

describe("clusterColor", () => {
  it("returns a distinct color for each of the first CLUSTER_COLORS.length ids", () => {
    const colors = Array.from({ length: CLUSTER_COLORS.length }, (_, i) => clusterColor(i));
    expect(new Set(colors).size).toBe(CLUSTER_COLORS.length);
  });

  it("wraps around for an id beyond the palette length", () => {
    expect(clusterColor(CLUSTER_COLORS.length)).toBe(clusterColor(0));
  });
});

describe("sharedAxisRange", () => {
  it("pads the inclusive min/max", () => {
    const [lo, hi] = sharedAxisRange([1, 5, 3], 0.1);
    expect(lo).toBeLessThan(1);
    expect(hi).toBeGreaterThan(5);
  });

  it("throws on an empty array", () => {
    expect(() => sharedAxisRange([])).toThrow();
  });
});

describe("indicesForCluster", () => {
  it("returns only indices assigned to the requested cluster", () => {
    const labels = [0, 1, 0, 2, 1, 0];
    expect(indicesForCluster(labels, 0)).toEqual([0, 2, 5]);
    expect(indicesForCluster(labels, 1)).toEqual([1, 4]);
    expect(indicesForCluster(labels, 2)).toEqual([3]);
  });

  it("returns an empty array for a cluster with no members", () => {
    expect(indicesForCluster([0, 0, 0], 1)).toEqual([]);
  });
});

describe("categoryShareByCluster", () => {
  it("computes within-cluster proportions that sum to 1 across categories", () => {
    const labels = [0, 0, 0, 1, 1];
    const values = ["a", "a", "b", "a", "b"];
    const shares = categoryShareByCluster(labels, 2, values);
    const byCategory = Object.fromEntries(shares.map((s) => [s.category, s.sharesByCluster]));
    expect(byCategory["a"]![0]).toBeCloseTo(2 / 3, 6);
    expect(byCategory["b"]![0]).toBeCloseTo(1 / 3, 6);
    expect(byCategory["a"]![1]).toBeCloseTo(1 / 2, 6);
    expect(byCategory["b"]![1]).toBeCloseTo(1 / 2, 6);
    const sums = [0, 1].map((c) => shares.reduce((acc, s) => acc + s.sharesByCluster[c]!, 0));
    expect(sums[0]).toBeCloseTo(1, 6);
    expect(sums[1]).toBeCloseTo(1, 6);
  });

  it("does not divide by zero for an empty cluster", () => {
    const shares = categoryShareByCluster([0, 0], 2, ["a", "a"]);
    const cluster1Share = shares.find((s) => s.category === "a")!.sharesByCluster[1];
    expect(cluster1Share).toBe(0);
  });
});

describe("siteShareMatrix", () => {
  it("normalizes each site row to sum to 1 across clusters", () => {
    const labels = [0, 0, 1, 1, 1];
    const values = ["NYU", "NYU", "NYU", "UCLA", "UCLA"];
    const { sites, z } = siteShareMatrix(labels, 2, values);
    expect(sites).toEqual(["NYU", "UCLA"]);
    const nyuRow = z[sites.indexOf("NYU")]!;
    expect(nyuRow[0]! + nyuRow[1]!).toBeCloseTo(1, 6);
    expect(nyuRow[0]).toBeCloseTo(2 / 3, 6);
    expect(nyuRow[1]).toBeCloseTo(1 / 3, 6);
    const uclaRow = z[sites.indexOf("UCLA")]!;
    expect(uclaRow[0]).toBeCloseTo(0, 6);
    expect(uclaRow[1]).toBeCloseTo(1, 6);
  });
});

describe("agesByCluster", () => {
  it("groups ages by cluster label", () => {
    const labels = [0, 1, 0, 1];
    const ages = [10, 20, 30, 40];
    const grouped = agesByCluster(labels, 2, ages);
    expect(grouped[0]).toEqual([10, 30]);
    expect(grouped[1]).toEqual([20, 40]);
  });
});
