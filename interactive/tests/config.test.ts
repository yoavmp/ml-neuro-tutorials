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
