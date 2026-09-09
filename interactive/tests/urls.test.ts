import { describe, expect, it } from "vitest";
import { resolveConfigUrl, resolveDataUrl } from "../src/urls";

const PAGE = "https://host.example/ml-neuro-tutorials/_static/widgets/app/index.html";

describe("resolveConfigUrl", () => {
  it("resolves a same-origin relative config param against the page URL", () => {
    const r = resolveConfigUrl(`${PAGE}?config=../configs/runtime_smoke.json`);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.url.href).toBe(
        "https://host.example/ml-neuro-tutorials/_static/widgets/configs/runtime_smoke.json",
      );
    }
  });

  it("rejects a missing config param", () => {
    const r = resolveConfigUrl(PAGE);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/Missing required "config"/);
  });

  it("rejects an empty config param", () => {
    const r = resolveConfigUrl(`${PAGE}?config=`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/Missing required "config"/);
  });

  it("rejects a whitespace-only config param", () => {
    const r = resolveConfigUrl(`${PAGE}?config=%20%20`);
    expect(r.ok).toBe(false);
  });

  it("rejects a cross-origin absolute config URL", () => {
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent("https://evil.example/c.json")}`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/same-origin/);
  });

  it("rejects a protocol-relative cross-origin config URL", () => {
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent("//evil.example/c.json")}`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/same-origin/);
  });

  it("rejects credentials embedded in the config URL", () => {
    const bad = "https://user:pass@host.example/ml-neuro-tutorials/_static/widgets/configs/c.json";
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent(bad)}`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/credentials/i);
  });

  it("rejects an unsupported protocol (file:)", () => {
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent("file:///etc/passwd")}`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/http or https/);
  });

  it("rejects an unsupported protocol (data:)", () => {
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent("data:application/json,{}")}`);
    expect(r.ok).toBe(false);
  });

  it("rejects a malformed config value", () => {
    const r = resolveConfigUrl(`${PAGE}?config=${encodeURIComponent("http://")}`);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/not a resolvable URL/);
  });

  it("rejects a malformed page URL", () => {
    const r = resolveConfigUrl("not-a-url?config=x");
    expect(r.ok).toBe(false);
  });

  it("works at the site root as well as a subpath", () => {
    const r = resolveConfigUrl("http://localhost:4173/app/index.html?config=../configs/runtime_smoke.json");
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.url.href).toBe("http://localhost:4173/configs/runtime_smoke.json");
    }
  });
});

describe("resolveDataUrl", () => {
  const CONFIG = "https://host.example/ml-neuro-tutorials/_static/widgets/configs/runtime_smoke.json";

  it("resolves the data ref against the CONFIG url, not the page", () => {
    const r = resolveDataUrl(CONFIG, "../data/runtime_smoke.json");
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.url.href).toBe(
        "https://host.example/ml-neuro-tutorials/_static/widgets/data/runtime_smoke.json",
      );
    }
  });

  it("rejects a cross-origin data ref", () => {
    const r = resolveDataUrl(CONFIG, "https://cdn.evil.example/d.json");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/same-origin/);
  });

  it("rejects credentials in a data ref", () => {
    const r = resolveDataUrl(CONFIG, "https://u:p@host.example/x/d.json");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/credentials/i);
  });

  it("rejects a non-http(s) data ref", () => {
    const r = resolveDataUrl(CONFIG, "file:///tmp/d.json");
    expect(r.ok).toBe(false);
  });

  it("rejects an empty data ref", () => {
    const r = resolveDataUrl(CONFIG, "   ");
    expect(r.ok).toBe(false);
  });

  it("rejects an unresolvable data ref", () => {
    const r = resolveDataUrl(CONFIG, "http://");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toMatch(/not a resolvable URL/);
  });

  it("rejects when the config URL itself is invalid", () => {
    const r = resolveDataUrl("not-a-url", "d.json");
    expect(r.ok).toBe(false);
  });
});
