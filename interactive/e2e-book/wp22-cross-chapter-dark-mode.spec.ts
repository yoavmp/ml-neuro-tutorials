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

  test("Exercise 2 — regression feature-set comparison and KNN exploration: initial dark load", async ({ page }) => {
    await gotoDark(page, "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html");
    const frame = await activityFrame(page, 'iframe[src*="config=../configs/regression_compare.json"]');

    for (const testId of ["regression-A-plot", "regression-B-plot"]) {
      const snap = await snapshotPlot(frame, testId);
      assertDarkFigure(snap, `regression-compare ${testId}`);
      expect(snap.markerColors, `regression-compare ${testId}: scatter marker uses the dark palette`).toContain(
        MARKER_PRIMARY_DARK,
      );
      expect(snap.markerColors, `regression-compare ${testId}: diagonal reference line uses the dark palette`).toContain(
        DIAGONAL_LINE_DARK,
      );
    }

    // --- KNN exploration: one plot (cheap addition, same already-loaded page) ---
    const exploreFrame = await activityFrame(page, 'iframe[src*="config=../configs/knn_explore.json"]');
    const exploreSnap = await snapshotPlot(exploreFrame, "knn-scatter-plot");
    assertDarkFigure(exploreSnap, "knn-explore knn-scatter-plot");
    expect(exploreSnap.markerColors, "knn-explore scatter: validation points visible (dark palette)").toContain(
      MARKER_PRIMARY_DARK,
    );
    expect(exploreSnap.markerColors, "knn-explore scatter: diagonal reference line visible (dark palette)").toContain(
      DIAGONAL_LINE_DARK,
    );
  });

  test("Exercise 3 — classification threshold ROC and class-imbalance: initial dark load", async ({ page }) => {
    await gotoDark(page, "/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html");

    const rocFrame = await activityFrame(page, 'iframe[src*="config=../configs/classification_threshold.json"]');
    const rocSnap = await snapshotPlot(rocFrame, "cls-roc-plot");
    assertDarkFigure(rocSnap, "classification-threshold cls-roc-plot");
    expect(rocSnap.markerColors, "classification-threshold: ROC curve uses the dark palette").toContain("#8fb8da");
    expect(rocSnap.markerColors, "classification-threshold: chance line uses the dark palette").toContain("#b0b0b0");
    expect(rocSnap.markerColors, "classification-threshold: selected-threshold marker uses the dark palette").toContain(
      "#f0915c",
    );

    // Cheap addition, same already-loaded page.
    const imbFrame = await activityFrame(page, 'iframe[src*="config=../configs/classification_imbalance.json"]');
    const imbSnap = await snapshotPlot(imbFrame, "cls-imb-plot");
    assertDarkFigure(imbSnap, "classification-imbalance cls-imb-plot");
    expect(imbSnap.markerColors, "classification-imbalance: model-accuracy bar uses the dark palette").toContain(
      "#5a9bd4",
    );
    expect(imbSnap.markerColors, "classification-imbalance: baseline-accuracy bar uses the dark palette").toContain(
      "#d9a441",
    );
  });

  test("Exercise 4 — validation-stability, validation-lock-test, nested-cv-explorer: initial dark load", async ({
    page,
  }) => {
    await gotoDark(page, "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html");

    const stabilityFrame = await activityFrame(page, 'iframe[src*="config=../configs/validation_stability.json"]');
    for (const testId of ["validation-stability-single-plot", "validation-stability-cv-plot"]) {
      const snap = await snapshotPlot(stabilityFrame, testId);
      assertDarkFigure(snap, `validation-stability ${testId}`);
      expect(snap.markerColors, `validation-stability ${testId}: bars use the dark palette`).toContain(
        MARKER_PRIMARY_DARK,
      );
      expect(
        snap.markerColors,
        `validation-stability ${testId}: highlighted seed / mean line uses the dark palette`,
      ).toContain(DIAGONAL_LINE_DARK);
    }

    // Cheap addition, same already-loaded page.
    const lockTestFrame = await activityFrame(page, 'iframe[src*="config=../configs/validation_lock_test.json"]');
    const lockTestSnap = await snapshotPlot(lockTestFrame, "validation-lock-test-plot");
    assertDarkFigure(lockTestSnap, "validation-lock-test validation-lock-test-plot");
    expect(lockTestSnap.markerColors, "validation-lock-test: training line uses the dark palette").toContain(
      MARKER_PRIMARY_DARK,
    );
    expect(lockTestSnap.markerColors, "validation-lock-test: validation line uses the dark palette").toContain(
      DIAGONAL_LINE_DARK,
    );

    // Cheap addition, same already-loaded page.
    const nestedCvFrame = await activityFrame(page, 'iframe[src*="config=../configs/nested_cv_explorer.json"]');
    const nestedCvSnap = await snapshotPlot(nestedCvFrame, "nested-cv-inner-plot");
    assertDarkFigure(nestedCvSnap, "nested-cv-explorer nested-cv-inner-plot");
    expect(nestedCvSnap.markerColors, "nested-cv-explorer: candidate-k bars use the dark palette").toContain(
      MARKER_PRIMARY_DARK,
    );
    expect(nestedCvSnap.markerColors, "nested-cv-explorer: selected-k bar uses the dark palette").toContain(
      DIAGONAL_LINE_DARK,
    );

    // WP27R: the native nested-CV split diagram (raw HTML on the page, not
    // inside a widget iframe) must also pick up the dark palette via its
    // `--ml-ncv-*` custom properties, not just the Plotly figures.
    const diagram = page.locator(".ml-ncv-diagram");
    await expect(diagram).toBeVisible();
    const outerTrainVar = await diagram.evaluate((el) => getComputedStyle(el).getPropertyValue("--ml-ncv-outer-train"));
    expect(outerTrainVar.trim()).toBe("#4d6a94");
  });
});
