import { describe, expect, it } from "vitest";
import {
  CONFIG_SCHEMA_VERSION,
  parseActivityConfig,
  parseActivityConfigJson,
} from "../src/config";

const valid = {
  schemaVersion: CONFIG_SCHEMA_VERSION,
  type: "runtime-smoke",
  title: "Runtime smoke test (developer fixture)",
  description: "dev only",
  data: "../data/runtime_smoke.json",
};

describe("parseActivityConfig", () => {
  it("accepts a well-formed runtime-smoke config", () => {
    const r = parseActivityConfig(valid);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.config.type).toBe("runtime-smoke");
      expect(r.config.data).toBe("../data/runtime_smoke.json");
    }
  });

  it("accepts a config without the optional description", () => {
    const { description: _omit, ...rest } = valid;
    void _omit;
    expect(parseActivityConfig(rest).ok).toBe(true);
  });

  it("rejects a non-object", () => {
    expect(parseActivityConfig("nope").ok).toBe(false);
    expect(parseActivityConfig(null).ok).toBe(false);
    expect(parseActivityConfig(42).ok).toBe(false);
  });

  it("rejects a wrong schemaVersion", () => {
    const r = parseActivityConfig({ ...valid, schemaVersion: 2 });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/Unsupported config schemaVersion 2/);
  });

  it("rejects a missing schemaVersion", () => {
    const { schemaVersion: _omit, ...rest } = valid;
    void _omit;
    const r = parseActivityConfig(rest);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/schemaVersion/);
  });

  it("rejects an unknown activity type", () => {
    const r = parseActivityConfig({ ...valid, type: "totally-unknown" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/Invalid config/);
  });

  it("rejects a missing title", () => {
    const { title: _omit, ...rest } = valid;
    void _omit;
    const r = parseActivityConfig(rest);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/title/);
  });

  it("rejects an empty title", () => {
    const r = parseActivityConfig({ ...valid, title: "" });
    expect(r.ok).toBe(false);
  });

  it("rejects a missing data field", () => {
    const { data: _omit, ...rest } = valid;
    void _omit;
    const r = parseActivityConfig(rest);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/data/);
  });

  it("rejects unknown extra keys (strict schema)", () => {
    const r = parseActivityConfig({ ...valid, evil: "payload" });
    expect(r.ok).toBe(false);
  });
});

const validHistogram = {
  schemaVersion: CONFIG_SCHEMA_VERSION,
  type: "eda-histogram",
  title: "ABIDE-II variable distributions",
  instructions: "Pick a variable and change the number of bins.",
  data: "../data/abide_histogram.json",
  variables: [
    { name: "AGE_AT_SCAN", label: "Age at scan (years)" },
    { name: "FIQ", label: "Full-scale IQ" },
  ],
  defaultVariable: "AGE_AT_SCAN",
  bins: { min: 5, max: 60, step: 1, default: 25 },
  xAxisLabel: "Value",
  yAxisLabel: "Number of participants",
  reflectionPrompts: ["Predict first.", "Then compare variables."],
};

describe("parseActivityConfig — eda-histogram", () => {
  it("accepts a well-formed histogram config", () => {
    const r = parseActivityConfig(validHistogram);
    expect(r.ok).toBe(true);
    if (r.ok && r.config.type === "eda-histogram") {
      expect(r.config.defaultVariable).toBe("AGE_AT_SCAN");
      expect(r.config.bins.default).toBe(25);
      expect(r.config.variables).toHaveLength(2);
    }
  });

  it("rejects a defaultVariable that is not in variables", () => {
    const r = parseActivityConfig({ ...validHistogram, defaultVariable: "NOT_THERE" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/defaultVariable/);
  });

  it("rejects a default bin count outside [min, max]", () => {
    const r = parseActivityConfig({
      ...validHistogram,
      bins: { min: 5, max: 60, step: 1, default: 99 },
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/bins\.default/);
  });

  it("rejects bins.min greater than bins.max", () => {
    const r = parseActivityConfig({
      ...validHistogram,
      bins: { min: 60, max: 5, step: 1, default: 30 },
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/bins\.min/);
  });

  it("rejects a default not reachable from min by step", () => {
    const r = parseActivityConfig({
      ...validHistogram,
      bins: { min: 5, max: 60, step: 10, default: 26 },
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/steps of/);
  });

  it("rejects duplicate variable names", () => {
    const r = parseActivityConfig({
      ...validHistogram,
      variables: [
        { name: "FIQ", label: "Full-scale IQ" },
        { name: "FIQ", label: "duplicate" },
      ],
      defaultVariable: "FIQ",
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/duplicate/);
  });

  it("rejects an empty variables list", () => {
    const r = parseActivityConfig({ ...validHistogram, variables: [] });
    expect(r.ok).toBe(false);
  });

  it("rejects missing instructions", () => {
    const { instructions: _omit, ...rest } = validHistogram;
    void _omit;
    const r = parseActivityConfig(rest);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/instructions/);
  });

  it("rejects missing reflectionPrompts", () => {
    const { reflectionPrompts: _omit, ...rest } = validHistogram;
    void _omit;
    expect(parseActivityConfig(rest).ok).toBe(false);
  });

  it("rejects unknown extra keys (strict schema)", () => {
    const r = parseActivityConfig({ ...validHistogram, extra: 1 });
    expect(r.ok).toBe(false);
  });

  it("accepts the shipped configs/eda_histogram.json", async () => {
    const fs = await import("node:fs/promises");
    const url = new URL(
      "../../book/_static/widgets/configs/eda_histogram.json",
      import.meta.url,
    );
    const text = await fs.readFile(url, "utf-8");
    const r = parseActivityConfigJson(text);
    expect(r.ok, r.ok ? "" : r.error).toBe(true);
  });
});

describe("parseActivityConfigJson", () => {
  it("parses and validates a JSON string", () => {
    const r = parseActivityConfigJson(JSON.stringify(valid));
    expect(r.ok).toBe(true);
  });

  it("rejects invalid JSON text", () => {
    const r = parseActivityConfigJson("{ not json ]");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/not valid JSON/);
  });

  it("rejects valid JSON that is not a valid config", () => {
    const r = parseActivityConfigJson('{"schemaVersion":1}');
    expect(r.ok).toBe(false);
  });
});
