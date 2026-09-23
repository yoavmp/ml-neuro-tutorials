import { describe, expect, it } from "vitest";
import {
  parsePcrPlsExploreData,
  catalogEntryFor,
  catalogKey,
  targetsFor,
  directionLinePoints,
  type PcrPlsExploreData,
} from "../src/pcr-pls-explore-data";

function validData(): PcrPlsExploreData {
  const points = [
    { id: 0, x: 1, y: 1 },
    { id: 1, x: -1, y: -1 },
    { id: 2, x: 1, y: -1 },
    { id: 3, x: -1, y: 1 },
  ];
  const catalog: PcrPlsExploreData["catalog"] = {};
  for (const method of ["pcr", "pls"] as const) {
    for (const n of [1, 2]) {
      for (const preset of ["weak", "moderate", "strong"] as const) {
        catalog[`${method}|${n}|${preset}`] = {
          method,
          nComponents: n,
          preset,
          firstComponentDirection: [0.7071, 0.7071],
          trainMse: 0.3,
          trainR2: 0.5,
          valMse: 0.4,
          valR2: 0.4,
          valPredictions: [0.1, 0.2],
          constructionNote: "note",
        };
      }
    }
  }
  return {
    schemaVersion: 1,
    activity: "pcr-pls-explore",
    syntheticDataNote: "note",
    fixedSignalNoiseNote: "Signal strength and noise are held constant; only the target's direction changes.",
    generatingProcess: {
      nObservations: 4,
      nTrain: 2,
      nVal: 2,
      rho: 0.7,
      signalSd: 1.0,
      noiseSd: 0.3,
      seed: 21,
      seedNote: "note",
      pc1ExplainedVarianceRatio: 0.85,
      pc2ExplainedVarianceRatio: 0.15,
    },
    featureX: { name: "f1", label: "Feature 1 (standardized)" },
    featureY: { name: "f2", label: "Feature 2 (standardized)" },
    points,
    trainIds: [0, 1],
    valIds: [2, 3],
    presets: {
      weak: { label: "Weak alignment", weightPc1: 0.25, weightPc2: 0.9682458365518543 },
      moderate: { label: "Moderate alignment", weightPc1: 0.7071067811865476, weightPc2: 0.7071067811865476 },
      strong: { label: "Strong alignment", weightPc1: 0.9682458365518543, weightPc2: 0.25 },
    },
    targets: {
      weak: [0.1, 0.2, 0.3, 0.4],
      moderate: [0.2, 0.3, 0.4, 0.5],
      strong: [0.3, 0.4, 0.5, 0.6],
    },
    methods: ["pcr", "pls"],
    componentGrid: [1, 2],
    catalog,
  };
}

describe("parsePcrPlsExploreData", () => {
  it("accepts valid data", () => {
    const result = parsePcrPlsExploreData(validData());
    expect(result.ok).toBe(true);
  });

  it("rejects data where trainIds + valIds do not partition every point", () => {
    const bad = validData();
    bad.trainIds = [0];
    const result = parsePcrPlsExploreData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects data missing a catalogue combination", () => {
    const bad = validData();
    delete bad.catalog["pcr|1|weak"];
    const result = parsePcrPlsExploreData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects a target array with the wrong length", () => {
    const bad = validData();
    bad.targets.weak = [0.1, 0.2];
    const result = parsePcrPlsExploreData(bad);
    expect(result.ok).toBe(false);
  });

  it("rejects malformed input with a readable error", () => {
    const result = parsePcrPlsExploreData({ nope: true });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain("Invalid pcr-pls-explore data");
    }
  });
});

describe("catalogKey / catalogEntryFor", () => {
  it("builds the expected key format", () => {
    expect(catalogKey("pcr", 1, "weak")).toBe("pcr|1|weak");
  });

  it("looks up the matching catalogue entry", () => {
    const data = validData();
    const entry = catalogEntryFor(data, "pls", 2, "strong");
    expect(entry.method).toBe("pls");
    expect(entry.nComponents).toBe(2);
    expect(entry.preset).toBe("strong");
  });

  it("throws a readable error for a missing combination", () => {
    const data = validData();
    delete data.catalog["pcr|1|weak"];
    expect(() => catalogEntryFor(data, "pcr", 1, "weak")).toThrow(/no catalogue entry/);
  });
});

describe("targetsFor", () => {
  it("returns the targets for the requested preset", () => {
    const data = validData();
    expect(targetsFor(data, "moderate")).toEqual([0.2, 0.3, 0.4, 0.5]);
  });

  it("throws for an unknown preset", () => {
    const data = validData();
    // @ts-expect-error -- deliberately invalid at the type level too
    expect(() => targetsFor(data, "extreme")).toThrow(/no targets/);
  });
});

describe("directionLinePoints", () => {
  it("returns a symmetric two-point segment along the direction", () => {
    const { x, y } = directionLinePoints([0.6, 0.8], 5);
    expect(x[0]).toBeCloseTo(-3, 6);
    expect(x[1]).toBeCloseTo(3, 6);
    expect(y[0]).toBeCloseTo(-4, 6);
    expect(y[1]).toBeCloseTo(4, 6);
  });

  it("scales with halfLength", () => {
    const { x, y } = directionLinePoints([0.6, 0.8], 10);
    expect(x[1]).toBeCloseTo(6, 6);
    expect(y[1]).toBeCloseTo(8, 6);
  });
});
