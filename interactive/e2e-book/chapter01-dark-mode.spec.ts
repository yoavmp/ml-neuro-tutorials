import { expect, test, type Frame, type Page } from "@playwright/test";

// WP22 regression guard, against the *built* Jupyter Book over real HTTP --
// not the standalone Vite dev page. Confirmed root cause: every activity used
// to read `prefers-color-scheme` on its OWN window, once, at mount time. The
// book's own light/dark toggle (pydata-sphinx-theme) never touches that media
// query -- it resolves the reader's choice onto the PARENT document's
// `data-theme`/`data-mode` instead (see `src/theme.ts`). This spec forces the
// browser's OS-level color-scheme to stay LIGHT throughout (`emulateMedia`)
// and drives the book's own toggle button, so any assertion that passes only
// because the OS preference happened to agree with the book's theme is not
// possible here -- exactly the mismatch the pre-WP22 code could not handle.
//
// A histogram (bar fill + gridlines) and the correlation scatter (marker
// fill) live on the same page, so both charts are covered without a second
// page load.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html";
const HIST_SEL = 'iframe[src*="config=../configs/eda_histogram.json"]';
const CORR_SEL = 'iframe[src*="config=../configs/eda_correlation.json"]';

// Resolved hex -> rgb() the way getComputedStyle reports it, so assertions
// read as "the dark palette color", not a magic rgb() triplet.
const LIGHT = {
  bg: "rgb(255, 255, 255)",
  histBar: "rgb(42, 111, 158)", // #2a6f9e
  gridColor: "rgb(226, 226, 226)", // #e2e2e2
  corrMarker: "rgb(51, 86, 107)", // #33566b (UNGROUPED_COLOR_LIGHT)
};
const DARK = {
  bg: "rgb(28, 26, 38)", // #1c1a26
  histBar: "rgb(90, 155, 212)", // #5a9bd4
  gridColor: "rgb(58, 58, 58)", // #3a3a3a
  corrMarker: "rgb(143, 182, 204)", // #8fb6cc (UNGROUPED_COLOR_DARK)
};

// `waitUntil: "commit"` (see the two `goto`/`reload` calls below) resolves as
// soon as the response is received -- well before the book's own inline
// script (pydata-sphinx-theme's `setTheme`/`addModeListener`) has run. In
// this environment `"load"`/`"domcontentloaded"` never resolve at all (some
// external resource this sandbox cannot reach keeps the load event pending
// indefinitely), so this polls for the concrete signal that actually matters
// instead: the theme script has resolved `data-mode` from "" to a real value
// and wired up the toggle button's click handler.
async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

// Each activity iframe is `loading="lazy"` (book/_static, WP16), so it only
// starts fetching its own document once the browser's native lazy-load
// intersection check recognizes it as near the viewport. Plain
// `.scrollIntoView()` (bypassing Playwright's actionability/"stable
// bounding box" wait) is used deliberately: `activity-resize.js` keeps
// nudging the iframe's own `height` attribute as its content settles, which
// can keep `scrollIntoViewIfNeeded()`'s stability check from ever resolving.
//
// WP31R3: a single `scrollIntoView()` call issued immediately after a
// full-page `reload()` can race the browser's own layout pass -- if layout
// has not yet stabilized at the moment of the call, the intersection check
// silently does not register and the iframe's `contentDocument` stays at
// `"about:blank"` indefinitely. Direct reproduction confirmed this exactly
// (WPs/reports/WP31R3_REPORT.md): every failure of this kind showed
// `contentDocument.URL === "about:blank"` even after 20+ seconds -- not a
// slow render, a lazy-load trigger that never fired. A real reader's
// natural scrolling fires many intersection checks over the course of
// scrolling and does not hit this; a single synthetic `scrollIntoView()`
// gets exactly one chance. Wait for the observable precondition --
// navigation away from `"about:blank"` has actually started -- re-issuing
// the scroll on every polling attempt (confirmed empirically to recover
// within 1-3 attempts, ~600-900ms) rather than calling it once and hoping.
async function waitForActivityNavigationStarted(page: Page, iframeSelector: string): Promise<void> {
  try {
    await page.waitForFunction(
      (iframeSelector: string) => {
        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
        if (!iframe) return false;
        iframe.scrollIntoView({ block: "center" });
        const url = iframe.contentDocument?.URL;
        return !!url && url !== "about:blank";
      },
      iframeSelector,
      { timeout: 10_000, polling: 250 },
    );
  } catch {
    throw new Error(
      `${iframeSelector}: navigation never started (contentDocument stayed at about:blank) within 10s -- ` +
        `the native lazy-load intersection check did not trigger despite repeated scrollIntoView() attempts`,
    );
  }
}

async function activityFrame(page: Page, iframeSelector: string): Promise<Frame> {
  const handle = await page.locator(iframeSelector).elementHandle();
  expect(handle, `${iframeSelector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${iframeSelector} content frame present`).not.toBeNull();
  return frame!;
}

// WP31R3: once `waitForActivityNavigationStarted` above confirms the iframe
// is actually loading, this waits for it to finish rendering. Plain
// `data-render-count` bumping (Plotly's own React-resolve signal, also read
// by chapter05-visual-policy.spec.ts and wp22-cross-chapter-dark-mode.spec.ts)
// only means `Plotly.react()`'s promise settled, and gating on that alone
// through the default 5s `expect` timeout is its own smaller readiness
// race: a cold iframe's module execution + data fetch + first Plotly draw
// can legitimately take a couple of seconds under load, on top of whatever
// time `waitForActivityNavigationStarted` already spent recovering the
// lazy-load trigger. Not a stuck or broken widget -- the identical code
// renders correctly in the large majority of runs and in every other
// render within the same test (WPs/reports/WP31R3_REPORT.md). Waiting via
// a `Frame` object obtained through `elementHandle().contentFrame()` before
// the iframe's own navigation has settled can itself stall for many
// seconds waiting on that frame's execution context, so this waits from
// the STABLE parent-page context instead, reading straight through
// `iframe.contentDocument` (same-origin, so this is a synchronous,
// same-process DOM read, not a separate cross-frame round trip) for the
// complete observable render-complete state: the iframe document and plot
// element exist, Plotly has actually populated `_fullData`/`_fullLayout`
// (the same properties wp22-cross-chapter-dark-mode.spec.ts reads for its
// own color assertions, not just the render-count side effect),
// `data-render-count` is a valid non-zero marker, and the rendered box is
// non-zero -- polled every animation frame (as
// chapter05-visual-policy.spec.ts's `waitForStableGeometry` already does)
// with a longer, explicit, condition-specific timeout. This is not a
// blanket global-timeout increase: it is a local wait for a more complete,
// more specific condition, sized to the evidence gathered during diagnosis
// rather than picked arbitrarily. Frame-to-frame stability (as
// `waitForStableGeometry` also does, for Plotly's `automargin` relayout
// pass) is not needed here: the colors this spec asserts on are
// marker/bar/grid fill values set synchronously within the same completed
// `Plotly.react()` draw, not values `automargin` revisits afterward. Only
// once this confirms the render is complete does `activityFrame()` obtain
// the actual Playwright `Frame` object used for the style snapshot below,
// by which point its execution context is already live.
async function waitForActivityRendered(page: Page, iframeSelector: string, testId: string): Promise<void> {
  try {
    await page.waitForFunction(
      ({ iframeSelector, testId }: { iframeSelector: string; testId: string }) => {
        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
        const doc = iframe?.contentDocument;
        if (!doc) return false;
        const el = doc.querySelector(`[data-testid="${testId}"]`) as
          | (HTMLElement & { _fullData?: unknown[]; _fullLayout?: Record<string, unknown> })
          | null;
        if (!el) return false;
        const renderCount = Number(el.dataset.renderCount ?? "0");
        if (!Number.isFinite(renderCount) || renderCount < 1) return false;
        if (!Array.isArray(el._fullData) || el._fullData.length === 0) return false;
        if (!el._fullLayout || Object.keys(el._fullLayout).length === 0) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      },
      { iframeSelector, testId },
      { timeout: 20_000, polling: "raf" },
    );
  } catch {
    const state = await page.evaluate(
      ({ iframeSelector, testId }: { iframeSelector: string; testId: string }) => {
        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
        const doc = iframe?.contentDocument;
        if (!doc) {
          return {
            iframeExists: !!iframe,
            docAccessible: false,
            exists: false,
            renderCount: 0,
            hasFullData: false,
            hasFullLayout: false,
            boxWidth: 0,
            boxHeight: 0,
          };
        }
        const el = doc.querySelector(`[data-testid="${testId}"]`) as
          | (HTMLElement & { _fullData?: unknown[]; _fullLayout?: Record<string, unknown> })
          | null;
        if (!el) {
          return {
            iframeExists: true,
            docAccessible: true,
            exists: false,
            renderCount: 0,
            hasFullData: false,
            hasFullLayout: false,
            boxWidth: 0,
            boxHeight: 0,
          };
        }
        const rect = el.getBoundingClientRect();
        return {
          iframeExists: true,
          docAccessible: true,
          exists: true,
          renderCount: Number(el.dataset.renderCount ?? "0"),
          hasFullData: Array.isArray(el._fullData) && el._fullData.length > 0,
          hasFullLayout: !!el._fullLayout && Object.keys(el._fullLayout).length > 0,
          boxWidth: rect.width,
          boxHeight: rect.height,
        };
      },
      { iframeSelector, testId },
    );
    const unmet: string[] = [];
    if (!state.iframeExists) {
      unmet.push("iframe element does not exist");
    } else if (!state.docAccessible) {
      unmet.push("iframe contentDocument is not accessible");
    } else if (!state.exists) {
      unmet.push(`[data-testid="${testId}"] does not exist inside the iframe document`);
    } else {
      if (!Number.isFinite(state.renderCount) || state.renderCount < 1) {
        unmet.push(`data-render-count is ${state.renderCount}, expected >= 1`);
      }
      if (!state.hasFullData) unmet.push("Plotly _fullData is not yet populated");
      if (!state.hasFullLayout) unmet.push("Plotly _fullLayout is not yet populated");
      if (!(state.boxWidth > 0 && state.boxHeight > 0)) {
        unmet.push(`bounding box is ${state.boxWidth}x${state.boxHeight}, expected non-zero`);
      }
    }
    throw new Error(
      `${iframeSelector} [data-testid="${testId}"] did not reach a fully-rendered state within 20s: ${unmet.join("; ")}`,
    );
  }
}

interface ChartSnapshot {
  bodyBg: string;
  barOrMarkerFill: string;
  gridStroke: string | null;
  dragRectFills: string[];
  dragRectStrokes: string[];
}

async function snapshotHistogram(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, HIST_SEL);
  await waitForActivityRendered(page, HIST_SEL, "histogram-plot");
  const frame = await activityFrame(page, HIST_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="histogram-plot"]')!;
    const bar = plot.querySelector(".bars path");
    const grid = plot.querySelector(".gridlayer path");
    const dragRects = Array.from(plot.querySelectorAll(".draglayer rect"));
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      barOrMarkerFill: bar ? getComputedStyle(bar).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
      dragRectFills: dragRects.map((r) => getComputedStyle(r).fill),
      dragRectStrokes: dragRects.map((r) => getComputedStyle(r).stroke),
    };
  });
}

async function snapshotCorrelation(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, CORR_SEL);
  await waitForActivityRendered(page, CORR_SEL, "correlation-plot");
  const frame = await activityFrame(page, CORR_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="correlation-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    const dragRects = Array.from(plot.querySelectorAll(".draglayer rect"));
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      barOrMarkerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
      dragRectFills: dragRects.map((r) => getComputedStyle(r).fill),
      dragRectStrokes: dragRects.map((r) => getComputedStyle(r).stroke),
    };
  });
}

test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", () => {
  // Each test drives 2 iframes through 3-4 theme states plus a full page
  // reload; the default 30s budget is tuned for lighter single-state specs.
  test.describe.configure({ timeout: 90_000 });

  test("histogram and correlation scatter: light → dark → reload-while-dark → light, every critical surface matches the intended palette", async ({
    page,
  }) => {
    // The browser's OS-level preference stays LIGHT for the entire test. If
    // any assertion below only passed because the OS preference happened to
    // agree with the book's chosen theme, this pins it so it can't.
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1000 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);

    // --- 1. light mode (book default: "auto", resolved against light OS) ---
    const histLight = await snapshotHistogram(page);
    const corrLight = await snapshotCorrelation(page);
    expect(histLight.bodyBg, "histogram light: widget card background").toBe(LIGHT.bg);
    expect(histLight.barOrMarkerFill, "histogram light: bar color").toBe(LIGHT.histBar);
    expect(histLight.gridStroke, "histogram light: gridline color").toBe(LIGHT.gridColor);
    expect(corrLight.bodyBg, "correlation light: widget card background").toBe(LIGHT.bg);
    expect(corrLight.barOrMarkerFill, "correlation light: marker color").toBe(LIGHT.corrMarker);

    // --- 2/3. switch to dark using the book's own color-mode control ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const histDark = await snapshotHistogram(page);
    const corrDark = await snapshotCorrelation(page);
    expect(histDark.bodyBg, "histogram dark: widget card background").toBe(DARK.bg);
    expect(histDark.barOrMarkerFill, "histogram dark: bar color").toBe(DARK.histBar);
    expect(histDark.gridStroke, "histogram dark: gridline color").toBe(DARK.gridColor);
    for (const fill of histDark.dragRectFills) {
      expect(["rgba(0, 0, 0, 0)", "transparent"]).toContain(fill);
    }
    for (const stroke of histDark.dragRectStrokes) {
      expect(["none", "rgba(0, 0, 0, 0)"]).toContain(stroke);
    }
    expect(corrDark.bodyBg, "correlation dark: widget card background").toBe(DARK.bg);
    expect(corrDark.barOrMarkerFill, "correlation dark: marker color").toBe(DARK.corrMarker);

    // --- 4. reload while dark is already selected (the exact WP22 defect:
    // theme used to be read once at mount, so a *cold* dark-mode load with a
    // light OS preference rendered the light palette). Mode persists via the
    // book's own localStorage. ---
    await page.reload({ waitUntil: "commit" });
    await waitForBookReady(page);
    const histReloaded = await snapshotHistogram(page);
    const corrReloaded = await snapshotCorrelation(page);
    expect(histReloaded.bodyBg, "histogram reload-in-dark: widget card background").toBe(DARK.bg);
    expect(histReloaded.barOrMarkerFill, "histogram reload-in-dark: bar color").toBe(DARK.histBar);
    expect(corrReloaded.bodyBg, "correlation reload-in-dark: widget card background").toBe(DARK.bg);
    expect(corrReloaded.barOrMarkerFill, "correlation reload-in-dark: marker color").toBe(DARK.corrMarker);

    // --- 5. switch back to light and verify restoration ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    const histRestored = await snapshotHistogram(page);
    const corrRestored = await snapshotCorrelation(page);
    expect(histRestored.bodyBg, "histogram restored-light: widget card background").toBe(LIGHT.bg);
    expect(histRestored.barOrMarkerFill, "histogram restored-light: bar color").toBe(LIGHT.histBar);
    expect(corrRestored.bodyBg, "correlation restored-light: widget card background").toBe(LIGHT.bg);
    expect(corrRestored.barOrMarkerFill, "correlation restored-light: marker color").toBe(LIGHT.corrMarker);
  });

  test("dark → light → dark again keeps redrawing correctly each time", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1000 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);
    const toggle = page.locator("button.theme-switch-button").first();

    await toggle.click(); // auto -> dark
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(DARK.histBar);

    await toggle.click(); // dark -> light
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(LIGHT.histBar);

    await toggle.click(); // light -> auto (resolves to light against light OS emulation)
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    await toggle.click(); // auto -> dark
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(DARK.histBar);
  });
});
