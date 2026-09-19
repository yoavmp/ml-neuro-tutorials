import { describe, expect, it } from "vitest";
import { parseValidationLockTestData } from "../src/validation-lock-test-data";

const source = {
  pinnedCommit: "abc",
  brainTableSha256: "x".repeat(64),
  phenotypeTableSha256: "y".repeat(64),
};

function makeValid() {
  return {
    schemaVersion: 1,
    activity: "validation-lock-test",
    source,
    nFit: 564,
    nVal: 189,
    nTest: 251,
    featureCount: 360,
    candidateKs: [1, 20, 100],
    rows: [
      { k: 1, trainMse: 0, trainR2: 1, valMse: 50, valR2: 0.3, testMseIfLocked: 60, testR2IfLocked: 0.2 },
      { k: 20, trainMse: 20, trainR2: 0.8, valMse: 30, valR2: 0.6, testMseIfLocked: 31, testR2IfLocked: 0.66 },
      { k: 100, trainMse: 40, trainR2: 0.6, valMse: 45, valR2: 0.4, testMseIfLocked: 44, testR2IfLocked: 0.5 },
    ],
    trainingSelectedK: 1,
    validationSelectedK: 20,
  };
}

describe("parseValidationLockTestData", () => {
  it("accepts a well-formed payload", () => {
    const r = parseValidationLockTestData(makeValid());
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });

  it("rejects a trainingSelectedK that disagrees with argmin(trainMse)", () => {
    const data = makeValid();
    data.trainingSelectedK = 20;
    const r = parseValidationLockTestData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a validationSelectedK that disagrees with argmin(valMse)", () => {
    const data = makeValid();
    data.validationSelectedK = 1;
    const r = parseValidationLockTestData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects rows whose k values do not match candidateKs", () => {
    const data = makeValid();
    data.candidateKs = [1, 20];
    const r = parseValidationLockTestData(data);
    expect(r.ok).toBe(false);
  });

  it("rejects a duplicate k in rows", () => {
    const data = makeValid();
    data.rows.push({ ...data.rows[0]! });
    const r = parseValidationLockTestData(data);
    expect(r.ok).toBe(false);
  });

  it("accepts the shipped wp27_validation_lock_test.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/data/wp27_validation_lock_test.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseValidationLockTestData(JSON.parse(text));
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});
