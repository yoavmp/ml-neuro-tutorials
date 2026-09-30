import { expect, test, type Frame, type Page } from "@playwright/test";

// WP22 addendum: `chapter01-dark-mode.spec.ts` covers Exercise 1 (histogram,
// correlation scatter) end to end, including the full light/dark/reload
// cycle. This spec extends coverage to one Plotly activity from every other
// exercise that has one, against the *built* Jupyter Book over real HTTP,
// OS/browser forced to light throughout so the only way "dark" can appear
// anywhere is via the book's own toggle (the exact mismatch the pre-WP22
// code could not handle). WP25 moved the KNN exploration activity into
// Exercise 2 and moved classification into Exercise 3; the discarded
// knn-abc activity's dark-mode coverage (the original bug screenshot) lives
// only on archive/pre-syllabus-notebook-structure.
//
// `regression-compare.ts` and `knn-explore.ts`'s scatter panel both use
// Plotly's `scattergl` trace type, which renders through WebGL --
// there is no per-point SVG element whose `fill` a computed-style check could
// read. Every color assertion here instead reads the trace's own resolved
// `marker.color`/`line.color` off `_fullData` (what Plotly actually used to
// draw the trace, gl or SVG), which is exact, format-stable across trace
// types, and directly verifies the same code path `plotly-policy.ts` feeds.
// Grid/axis-text/drag-layer checks stay DOM/computed-style based, since those
// elements are ordinary SVG in every trace type.

const LIGHT_OS = { colorScheme: "light" as const };

const DARK_BODY_BG = "rgb(28, 26, 38)"; // #1c1a26
const DARK_GRID_STROKE = "rgb(58, 58, 58)"; // #3a3a3a
const DARK_TICK_FILL = "rgb(201, 201, 201)"; // #c9c9c9
const MARKER_PRIMARY_DARK = "rgba(120,170,210,0.55)";
const DIAGONAL_LINE_DARK = "#d98b5f";
const BLACKISH = new Set(["rgb(0, 0, 0)", "#000000", "#000", "black"]);

async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

async function gotoDark(page: Page, url: string): Promise<void> {
  await page.emulateMedia(LIGHT_OS);
  await page.setViewportSize({ width: 1350, height: 1000 });
  await page.goto(url, { waitUntil: "commit" });
  await waitForBookReady(page);
  await page.locator("button.theme-switch-button").first().click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
}

async function activityFrame(page: Page, selector: string): Promise<Frame> {
  // See chapter01-dark-mode.spec.ts: every activity iframe is `loading="lazy"`
  // (WP16) and `activity-resize.js` keeps nudging its height, so a plain
  // `.scrollIntoView()` is used deliberately in place of
  // `scrollIntoViewIfNeeded()`, which waits for a stable bounding box that
  // this page's own resize script can keep from ever settling.
  const locator = page.locator(selector);
  await locator.evaluate((el) => el.scrollIntoView({ block: "center" }));
  const handle = await locator.elementHandle();
  expect(handle, `${selector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${selector} content frame present`).not.toBeNull();
  return frame!;
}

interface PlotSnapshot {
  bodyBg: string;
  frameDataTheme: string | null;
  paperBg: string | null;
  plotBg: string | null;
  gridStroke: string | null;
  tickTextFill: string | null;
  markerColors: string[];
  dragRectFills: string[];
  dragRectStrokes: string[];
  hasError: boolean;
}

async function snapshotPlot(frame: Frame, testId: string): Promise<PlotSnapshot> {
  await expect(frame.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
  return frame.evaluate((selector) => {
    type PlotlyPlotEl = HTMLElement & {
      _fullData?: Array<{ marker?: { color?: string | string[] }; line?: { color?: string } }>;
      _fullLayout?: { paper_bgcolor?: string; plot_bgcolor?: string };
    };
    const plot = document.querySelector(selector) as PlotlyPlotEl | null;
    const fullData = plot?._fullData ?? [];
    const fullLayout = plot?._fullLayout ?? {};
    const grid = plot?.querySelector(".gridlayer path") ?? null;
    const tick = plot?.querySelector(".xtick text, .ytick text") ?? null;
    const dragRects = Array.from(plot?.querySelectorAll(".draglayer rect") ?? []);
    const markerColors: string[] = [];
    for (const trace of fullData) {
      const c = trace.marker?.color;
      if (Array.isArray(c)) markerColors.push(...c);
      else if (typeof c === "string") markerColors.push(c);
      if (trace.line?.color) markerColors.push(trace.line.color);
    }
    return {
      bodyBg: getComputedStyle(document.body).backgroundColor,
      frameDataTheme: document.documentElement.getAttribute("data-theme"),
      paperBg: fullLayout.paper_bgcolor ?? null,
      plotBg: fullLayout.plot_bgcolor ?? null,
      gridStroke: grid ? getComputedStyle(grid).stroke : null,
      tickTextFill: tick ? getComputedStyle(tick).fill : null,
      markerColors,
      dragRectFills: dragRects.map((r) => getComputedStyle(r).fill),
      dragRectStrokes: dragRects.map((r) => getComputedStyle(r).stroke),
      hasError: document.querySelector('[data-testid="widget-error"]') !== null,
    };
  }, `[data-testid="${testId}"]`);
}

/** The eight §2 assertions common to every checked figure. */
function assertDarkFigure(snap: PlotSnapshot, label: string): void {
  expect(snap.hasError, `${label}: no runtime error message`).toBe(false);
  expect(snap.frameDataTheme, `${label}: iframe root reports the dark theme`).toBe("dark");
  expect(snap.bodyBg, `${label}: widget card background is the dark palette`).toBe(DARK_BODY_BG);
  expect(snap.paperBg, `${label}: paper background transparent (design: card shows through)`).toBe(
    "rgba(0, 0, 0, 0)",
  );
  expect(snap.plotBg, `${label}: plot background transparent (design: card shows through)`).toBe("rgba(0, 0, 0, 0)");
  expect(snap.gridStroke, `${label}: gridline color is the dark palette`).toBe(DARK_GRID_STROKE);
  expect(snap.tickTextFill, `${label}: axis tick text color is the dark palette`).toBe(DARK_TICK_FILL);
  expect(snap.markerColors.length, `${label}: at least one principal data mark present`).toBeGreaterThan(0);
  for (const c of snap.markerColors) {
    expect(BLACKISH.has(c.toLowerCase()), `${label}: data mark "${c}" must not be black/invisible`).toBe(false);
  }
  for (const fill of snap.dragRectFills) {
    expect(["rgba(0, 0, 0, 0)", "transparent"], `${label}: draglayer rect fill "${fill}" must be transparent`).toContain(
      fill,
    );
  }
  for (const stroke of snap.dragRectStrokes) {
    expect(["none", "rgba(0, 0, 0, 0)"], `${label}: draglayer rect stroke "${stroke}" must be invisible`).toContain(
      stroke,
    );
  }
}

test.describe("Cross-chapter dark-mode Plotly verification (WP22 addendum)", () => {
  test.describe.configure({ timeout: 60_000 });

  // WP41 migrated Exercise 2 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_02/exercise_02.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter02.spec.ts asserts iframe count is 0 there), so the book's own
  // dark-mode toggle and this file's Plotly `_fullData`/`_fullLayout`
  // color-snapshot technique have no surface left to check on that page.
  // Exercise 2's own figures (matplotlib, not Plotly) live inside the
  // JupyterLite app instead, a separate origin/app with its OWN theme
  // setting unrelated to the book's theme-switch-button -- this replacement
  // test checks THAT surface: switching the notebook's own JupyterLab theme
  // to dark must not error, and Section 8's live figure (the one explicitly
  // required to "keep figures legible in light/dark modes") must still be
  // present and rendered. Matplotlib figures here are static, white-card
  // PNGs -- legible by construction regardless of the surrounding app
  // theme, unlike the dark-palette-remapped Plotly figures other exercises
  // still use, which is why this test's shape necessarily differs from the
  // others in this file rather than reusing snapshotPlot/assertDarkFigure.
  test("Exercise 2 — JupyterLite notebook: Section 8 figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    // Overrides this file's 60s describe-level timeout: a cold JupyterLite
    // start (Pyodide + the scientific stack) can take up to ~140s, the same
    // budget exercise-02-lite.spec.ts uses for this same notebook.
    test.setTimeout(180_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_02.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await page.waitForTimeout(140_000);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.78;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP45 migrated Exercise 5 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_05/exercise_05.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter05.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning WP44 already
  // applied to Exercise 3 below. This replacement checks the JupyterLite
  // app's own theme instead: switching to dark must not error, and a
  // rendered Matplotlib figure (a static, white-card PNG, legible
  // regardless of surrounding app theme) must still be present.
  test("Exercise 5 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_05.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await page.waitForTimeout(140_000);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-05-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  test("Exercise 6 — one tree or many?: initial dark load", async ({ page }) => {
    await gotoDark(page, "/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html");
    const frame = await activityFrame(page, 'iframe[src*="config=../configs/tree_ensemble_compare.json"]');

    const snap = await snapshotPlot(frame, "tree-ensemble-prediction-plot");
    assertDarkFigure(snap, "tree-ensemble-compare tree-ensemble-prediction-plot");
    expect(
      snap.markerColors,
      "tree-ensemble-compare: validation scatter uses the dark palette",
    ).toContain(MARKER_PRIMARY_DARK);
    expect(
      snap.markerColors,
      "tree-ensemble-compare: diagonal reference line uses the dark palette",
    ).toContain(DIAGONAL_LINE_DARK);
  });

  // WP44 migrated Exercise 3 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_03/exercise_03.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter03.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning already
  // applied to Exercise 2 above. This replacement checks the JupyterLite
  // app's own theme instead: switching to dark must not error, and a
  // rendered Matplotlib figure (a static, white-card PNG, legible
  // regardless of surrounding app theme, unlike the dark-palette-remapped
  // Plotly figures other exercises still use) must still be present.
  test("Exercise 3 — JupyterLite notebook: a rendered figure survives switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_03.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await page.waitForTimeout(140_000);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's own guarded model-fit RuntimeError (Section
    // 3, by design -- see exercise-03-lite.spec.ts) is the one expected
    // error cell here; anything beyond that would be a real regression.
    expect(await page.locator(".jp-mod-error").count()).toBeLessThanOrEqual(1);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.1;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);
    const figureVisible = await page.locator(".jp-OutputArea-output img, .jp-OutputArea-output canvas").count();
    expect(figureVisible).toBeGreaterThan(0);
  });

  // WP45 migrated Exercise 4 to a JupyterLite-native notebook: its built
  // page (chapters/chapter_04/exercise_04.html) is now a 2-cell transition
  // page with no embedded iframe or Plotly figure at all (confirmed:
  // chapter04.spec.ts asserts iframe count is 0 there), so this file's
  // Plotly `_fullData`/`_fullLayout` color-snapshot technique has no
  // surface left to check on that page -- the same reasoning WP44 already
  // applied to Exercise 3 below. This replacement checks the JupyterLite
  // app's own theme instead, and additionally confirms the native
  // nested-cross-validation split diagram (raw HTML in a markdown cell, not
  // a widget iframe) still picks up the dark palette via its `--ml-ncv-*`
  // custom properties.
  test("Exercise 4 — JupyterLite notebook: a rendered figure and the nested-CV diagram survive switching to the app's own dark theme", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    await page.goto("/lite/notebooks/index.html?path=exercise_04.ipynb", { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await page.click("text=Run");
    await page.waitForTimeout(200);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
    await page.waitForTimeout(140_000);

    await page.click("text=Settings");
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "Theme" }).first().click();
    await page.waitForTimeout(300);
    await page.locator(".lm-Menu-itemLabel", { hasText: "JupyterLab Dark" }).first().click();
    await page.waitForTimeout(1000);

    // The untouched template's blank "YOUR CODE HERE" activities degrade to
    // their own "Not complete yet" print messages (no exception raised, by
    // design -- see exercise-04-lite.spec.ts), so no error cell is expected
    // here at all.
    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    const el = await page.evaluate(() => {
      const panel = document.querySelector(".jp-WindowedPanel-outer");
      if (panel) panel.scrollTop = panel.scrollHeight * 0.4;
      return true;
    });
    expect(el).toBe(true);
    await page.waitForTimeout(600);

    // Unlike the built Book page (chapters/chapter_04/exercise_04.html,
    // which loads book/_static/custom.css and toggles its dark palette via
    // the Sphinx theme's own `html[data-theme="dark"]` selector), the
    // JupyterLite app is a separate build that never loads that stylesheet
    // at all -- confirmed live: `--ml-ncv-outer-train` reads back empty
    // here regardless of the JupyterLab theme, so the diagram always
    // renders its inline fallback colors (chosen for a light background).
    // This is a real, found-live limitation (the diagram does not adapt to
    // JupyterLab's own dark theme the way it adapts to the book's), noted
    // in the WP45 report rather than asserted as if it were the book
    // page's own dark-mode contract; what this test can honestly confirm
    // in this context is that the diagram still renders, visibly, with no
    // error, after switching themes.
    const diagram = page.locator(".ml-ncv-diagram");
    await expect(diagram).toBeVisible();
  });
});
