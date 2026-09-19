import { describe, expect, it } from "vitest";
import { parseValidationStabilityData } from "../src/validation-stability-data";

const source = {
  pinnedCommit: "abc",
  brainTableSha256: "x".repeat(64),
  phenotypeTableSha256: "y".repeat(64),
};

function makeSize(sizeKey: string, seeds: number[], instabilityMeaningful = false) {
  return {
    sizeKey,
    label: sizeKey,
    nActual: 30,
    singleSplit: seeds.map((seed) => ({
      seed,
      valid: true,
      n_train: 22,
      n_test: 8,
      test_mse: 10,
      test_r2: 0.5,
    })),
    cvByFolds: {
      "5": seeds.map((seed) => ({
        seed,
        valid: true,
        fold_test_sizes: [6, 6, 6, 6, 6],
        fold_train_sizes: [24, 24, 24, 24, 24],
        fold_mse: [10, 11, 9, 10, 12],
        fold_r2: [0.5, 0.4, 0.6, 0.5, 0.3],
        mean_mse: 10.4,
        std_mse: 1.0,
        mean_r2: 0.46,
        std_r2: 0.1,
      })),
    },
    instabilityMeaningful,
    anyNegativeSingleSplitR2: instabilityMeaningful,
    anyNegativeCv5MeanR2: false,
  };
}

function makeValid() {
  return {
    schemaVersion: 1,
    activity: "validation-stability",
    source,
    fixedK: 20,
    singleSplitTestSize: 0.25,
    splitSeeds: [0, 1],
    foldOptions: [5],
    sizes: [makeSize("30", [0, 1], true)],
    sizesWithMeaningfulInstability: ["30"],
    instabilityRequiresSmallN: true,
  };
}

describe("parseValidationStabilityData", () => {
  it("accepts a well-formed payload", () => {
    const r = parseValidationStabilityData(makeValid());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a duplicate sizeKey", () => {
    const data = makeValid();
    data.sizes.push(makeSize("30", [0, 1]));
    const r = parseValidationStabilityData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a size whose singleSplit seeds do not match splitSeeds", () => {
    const data = makeValid();
    data.sizes[0]!.singleSplit = [data.sizes[0]!.singleSplit[0]!];
    const r = parseValidationStabilityData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects an invalid single-split entry missing a reason", () => {
    const data = makeValid() as any;
    data.sizes[0].singleSplit[0] = { seed: 0, valid: false };
    const r = parseValidationStabilityData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects sizesWithMeaningfulInstability referencing an unknown size", () => {
    const data = makeValid();
    data.sizesWithMeaningfulInstability = ["999"];
    const r = parseValidationStabilityData(data);
    expect(r.ok).toBe(false);
  });

  it("accepts the shipped wp27_validation_stability.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/wp27_validation_stability.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseValidationStabilityData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
