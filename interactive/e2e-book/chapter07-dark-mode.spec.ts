import { expect, test, type Frame, type Page } from "@playwright/test";

// Dedicated dark-mode regression guard for Exercise 7's two activities
// ("Build a Boosted Model", "Explore the Boosting Parameters"), over the
// *built* Jupyter Book, mirroring chapter08-dark-mode.spec.ts (itself modeled
// on chapter01-dark-mode.spec.ts, the WP22 template this project uses for
// per-chapter dark-mode coverage). WP32's own report flagged the lack of an
// equivalent spec for Exercise 7 as a deviation; this closes that gap
// (WP35 §6.1).
//
// Root cause this guards against (WP22): every activity used to read
// `prefers-color-scheme` on its OWN window, once, at mount time. The book's
// own light/dark toggle (pydata-sphinx-theme) never touches that media query
// -- it resolves the reader's choice onto the PARENT document's
// `data-theme`/`data-mode` instead (see `src/theme.ts`). This spec forces the
// browser's OS-level color-scheme to stay LIGHT throughout (`emulateMedia`)
// and drives the book's own toggle button, so a chart that only happens to
// look right because the OS preference matches the book's theme cannot pass
// by accident.

const CHAPTER_URL = "/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html";
const STEP_SEL = 'iframe[title="Interactive stage-by-stage gradient boosting activity on a small simulated dataset"]';
const PARAM_SEL =
  'iframe[title="Interactive gradient-boosting parameter explorer for predicting age from brain structure"]';

// Global Plotly theme (interactive/src/components/plotly-policy.ts) -- shared
// across every activity in the book, not recomputed per widget.
const LIGHT = {
  bg: "rgb(255, 255, 255)",
  marker: "rgb(42, 111, 158)",
  gridColor: "rgb(226, 226, 226)",
};
const DARK = {
  bg: "rgb(28, 26, 38)",
  marker: "rgb(120, 170, 210)",
  gridColor: "rgb(58, 58, 58)",
};

// boosting-param-mse-plot's first ("g.points path.point") trace is its
// "Training MSE" line, colored with the theme's axisColor (a neutral
// gray), not markerPrimary -- unlike boosting-step-observation-plot's first
// trace ("Observed"), which does use markerPrimary. Both are still the
// same shared plotly-policy.ts theme; only which color token this
// particular first trace draws from differs.
const PARAM_LIGHT_MARKER = "rgb(51, 51, 51)"; // axisColor, light: #333333
const PARAM_DARK_MARKER = "rgb(201, 201, 201)"; // axisColor, dark: #c9c9c9

async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

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
    throw new Error(`${iframeSelector}: navigation never started (contentDocument stayed at about:blank) within 10s`);
  }
}

async function waitForActivityRendered(page: Page, iframeSelector: string, testId: string): Promise<void> {
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
}

async function activityFrame(page: Page, iframeSelector: string): Promise<Frame> {
  const handle = await page.locator(iframeSelector).elementHandle();
  expect(handle, `${iframeSelector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${iframeSelector} content frame present`).not.toBeNull();
  return frame!;
}

interface ChartSnapshot {
  bodyBg: string;
  markerFill: string;
  gridStroke: string | null;
}

async function snapshotStep(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, STEP_SEL);
  await waitForActivityRendered(page, STEP_SEL, "boosting-step-observation-plot");
  const frame = await activityFrame(page, STEP_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="boosting-step-observation-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      markerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

async function snapshotParam(page: Page): Promise<ChartSnapshot> {
  await waitForActivityNavigationStarted(page, PARAM_SEL);
  await waitForActivityRendered(page, PARAM_SEL, "boosting-param-mse-plot");
  const frame = await activityFrame(page, PARAM_SEL);
  return frame.evaluate(() => {
    const plot = document.querySelector('[data-testid="boosting-param-mse-plot"]')!;
    const point = plot.querySelector("g.points path.point");
    const grid = plot.querySelector(".gridlayer path");
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      markerFill: point ? getComputedStyle(point).fill : "",
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
    };
  });
}

// Pre-existing page-chrome noise unrelated to this spec's own dark-mode/
// resize concern (a Thebe double-declaration -- can fire more than once
// across this test's own reload step -- and a one-time "invalid theme
// mode" warning during the book's own color-mode bootstrap, both
// independent of Exercise 7's activities) -- excluded so this check fails
// only on a genuine dark-mode/console regression in the activities
// themselves, not on unrelated pre-existing book-chrome console noise.
const KNOWN_UNRELATED_NOISE = [/THEBE_JS_URL' has already been declared/, /Got invalid theme mode/];

async function consoleErrorsOf(page: Page): Promise<string[]> {
  const errors: string[] = [];
  const record = (text: string) => {
    if (KNOWN_UNRELATED_NOISE.some((re) => re.test(text))) return;
    errors.push(text);
  };
  page.on("console", (msg) => {
    if (msg.type() === "error") record(msg.text());
  });
  page.on("pageerror", (e) => record(String(e)));
  return errors;
}

test.describe("Chapter 7 built page — dark-mode Plotly theme sync (WP22 pattern)", () => {
  test.describe.configure({ timeout: 90_000 });

  test("Build a Boosted Model and Explore the Boosting Parameters: light -> dark -> reload-while-dark -> light", async ({
    page,
  }) => {
    const errors = await consoleErrorsOf(page);

    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize({ width: 1350, height: 1200 });
    await page.goto(CHAPTER_URL, { waitUntil: "commit" });
    await waitForBookReady(page);

    // --- light mode (book default: "auto", resolved against light OS) ---
    const stepLight = await snapshotStep(page);
    const paramLight = await snapshotParam(page);
    expect(stepLight.bodyBg, "step light: widget card background").toBe(LIGHT.bg);
    expect(stepLight.markerFill, "step light: observed-point color").toBe(LIGHT.marker);
    expect(stepLight.gridStroke, "step light: gridline color").toBe(LIGHT.gridColor);
    expect(paramLight.bodyBg, "param light: widget card background").toBe(LIGHT.bg);
    expect(paramLight.markerFill, "param light: Training MSE line color").toBe(PARAM_LIGHT_MARKER);
    expect(paramLight.gridStroke, "param light: gridline color").toBe(LIGHT.gridColor);

    // --- switch to dark using the book's own color-mode control ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const stepDark = await snapshotStep(page);
    const paramDark = await snapshotParam(page);
    expect(stepDark.bodyBg, "step dark: widget card background").toBe(DARK.bg);
    expect(stepDark.markerFill, "step dark: observed-point color").toBe(DARK.marker);
    expect(stepDark.gridStroke, "step dark: gridline color").toBe(DARK.gridColor);
    expect(paramDark.bodyBg, "param dark: widget card background").toBe(DARK.bg);
    expect(paramDark.markerFill, "param dark: Training MSE line color").toBe(PARAM_DARK_MARKER);
    expect(paramDark.gridStroke, "param dark: gridline color").toBe(DARK.gridColor);

    // --- reload while dark is already selected (the exact WP22 defect) ---
    await page.reload({ waitUntil: "commit" });
    await waitForBookReady(page);
    const stepReloaded = await snapshotStep(page);
    const paramReloaded = await snapshotParam(page);
    expect(stepReloaded.bodyBg, "step reload-in-dark: widget card background").toBe(DARK.bg);
    expect(stepReloaded.markerFill, "step reload-in-dark: observed-point color").toBe(DARK.marker);
    expect(paramReloaded.bodyBg, "param reload-in-dark: widget card background").toBe(DARK.bg);
    expect(paramReloaded.markerFill, "param reload-in-dark: Training MSE line color").toBe(PARAM_DARK_MARKER);

    // --- switch back to light and verify restoration ---
    await page.locator("button.theme-switch-button").first().click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    const stepRestored = await snapshotStep(page);
    const paramRestored = await snapshotParam(page);
    expect(stepRestored.bodyBg, "step restored-light: widget card background").toBe(LIGHT.bg);
    expect(stepRestored.markerFill, "step restored-light: observed-point color").toBe(LIGHT.marker);
    expect(paramRestored.bodyBg, "param restored-light: widget card background").toBe(LIGHT.bg);
    expect(paramRestored.markerFill, "param restored-light: Training MSE line color").toBe(PARAM_LIGHT_MARKER);

    expect(errors, `unexpected console/runtime errors: ${errors.join(", ")}`).toHaveLength(0);
  });
});
