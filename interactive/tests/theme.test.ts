import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// WP22 regression guard for the actual confirmed root cause: the app used to
// read `prefers-color-scheme` once, at mount time, on its own window -- never
// the parent Jupyter Book's `data-theme`/`data-mode`, and never again after
// that first read. These tests exercise `src/theme.ts` against small, exact
// fakes of the DOM surface it touches (no jsdom dependency in this project),
// so a real regression on any of the four documented behaviors fails here,
// not just visually in a browser.

class FakeMutationObserver {
  static instances: FakeMutationObserver[] = [];
  callback: MutationCallback;
  disconnected = false;
  observeCalls: Array<{ target: unknown; options: unknown }> = [];
  constructor(callback: MutationCallback) {
    this.callback = callback;
    FakeMutationObserver.instances.push(this);
  }
  observe(target: unknown, options: unknown): void {
    this.observeCalls.push({ target, options });
  }
  disconnect(): void {
    this.disconnected = true;
  }
  trigger(): void {
    this.callback([], this as unknown as MutationObserver);
  }
}

function makeElement(attrs: Record<string, string> = {}) {
  return {
    getAttribute(name: string): string | null {
      return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name]! : null;
    },
    setAttribute(name: string, value: string): void {
      attrs[name] = value;
    },
  };
}

function makeMedia(initialMatches: boolean) {
  const listeners: Array<(ev: { matches: boolean }) => void> = [];
  return {
    matches: initialMatches,
    addEventListener(_type: string, cb: (ev: { matches: boolean }) => void): void {
      listeners.push(cb);
    },
    removeEventListener(_type: string, cb: (ev: { matches: boolean }) => void): void {
      const i = listeners.indexOf(cb);
      if (i >= 0) listeners.splice(i, 1);
    },
    listenerCount(): number {
      return listeners.length;
    },
    fire(matches: boolean): void {
      this.matches = matches;
      for (const cb of [...listeners]) cb({ matches });
    },
  };
}

let ownElement: ReturnType<typeof makeElement>;
let media: ReturnType<typeof makeMedia>;

beforeEach(() => {
  FakeMutationObserver.instances = [];
  ownElement = makeElement();
  media = makeMedia(false);
  vi.stubGlobal("MutationObserver", FakeMutationObserver);
  vi.stubGlobal("document", { documentElement: ownElement });
  vi.stubGlobal("window", {
    matchMedia: () => media,
    // top-level by default: parent === window itself.
    get parent() {
      return globalThis.window;
    },
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("getActiveTheme", () => {
  it("reads an already-active parent dark theme when embedded", async () => {
    const parentElement = makeElement({ "data-theme": "dark" });
    vi.stubGlobal("window", {
      matchMedia: () => media,
      parent: { document: { documentElement: parentElement } },
    });
    const { getActiveTheme } = await import("../src/theme");
    expect(getActiveTheme()).toBe("dark");
  });

  it("falls back to prefers-color-scheme when no parent theme is available (standalone/direct open)", async () => {
    media.matches = true; // OS/browser prefers dark
    const { getActiveTheme } = await import("../src/theme");
    expect(getActiveTheme()).toBe("dark");
  });

  it("falls back to light when nothing indicates dark", async () => {
    media.matches = false;
    const { getActiveTheme } = await import("../src/theme");
    expect(getActiveTheme()).toBe("light");
  });

  it("does not throw when the parent is cross-origin (accessing .document throws)", async () => {
    vi.stubGlobal("window", {
      matchMedia: () => media,
      get parent() {
        return {
          get document(): never {
            throw new DOMException("Blocked a frame with origin from accessing a cross-origin frame.");
          },
        };
      },
    });
    const { getActiveTheme } = await import("../src/theme");
    expect(() => getActiveTheme()).not.toThrow();
    expect(getActiveTheme()).toBe("light");
  });
});

describe("subscribeToThemeChanges", () => {
  it("calls back with the new theme when the parent's data-theme attribute changes", async () => {
    const parentElement = makeElement({ "data-theme": "light" });
    vi.stubGlobal("window", {
      matchMedia: () => media,
      parent: { document: { documentElement: parentElement } },
    });
    const { subscribeToThemeChanges } = await import("../src/theme");

    const seen: string[] = [];
    const unsubscribe = subscribeToThemeChanges((theme) => seen.push(theme));

    // Simulate the book's toggle: it mutates its own root element, then a
    // MutationObserver callback fires.
    parentElement.setAttribute("data-theme", "dark");
    const parentObserver = FakeMutationObserver.instances.find((o) =>
      o.observeCalls.some((c) => c.target === parentElement),
    );
    expect(parentObserver, "a MutationObserver was attached to the parent element").toBeTruthy();
    parentObserver!.trigger();

    expect(seen).toEqual(["dark"]);
    unsubscribe();
  });

  it("falls back to the browser preference changing when no parent theme is available", async () => {
    const { subscribeToThemeChanges } = await import("../src/theme");
    const seen: string[] = [];
    const unsubscribe = subscribeToThemeChanges((theme) => seen.push(theme));

    media.fire(true); // OS switches to dark mid-session

    expect(seen).toEqual(["dark"]);
    unsubscribe();
  });

  it("cleans up every observer and the media-query listener on unsubscribe", async () => {
    const parentElement = makeElement({ "data-theme": "light" });
    vi.stubGlobal("window", {
      matchMedia: () => media,
      parent: { document: { documentElement: parentElement } },
    });
    const { subscribeToThemeChanges } = await import("../src/theme");

    expect(media.listenerCount()).toBe(0);
    const unsubscribe = subscribeToThemeChanges(() => {});
    expect(media.listenerCount()).toBe(1);
    expect(FakeMutationObserver.instances.length).toBeGreaterThan(0);
    expect(FakeMutationObserver.instances.every((o) => !o.disconnected)).toBe(true);

    unsubscribe();

    expect(media.listenerCount()).toBe(0);
    expect(FakeMutationObserver.instances.every((o) => o.disconnected)).toBe(true);

    // Safe to call twice.
    expect(() => unsubscribe()).not.toThrow();
  });
});
