import { expect, test, type Frame, type Page } from "@playwright/test";

// Reusable content-height contract for EVERY interactive activity iframe in
// Exercises 1-10 (WP35 §17). The parent page (book/_static/activity-resize.js)
// and each widget (interactive/src/resize-report.ts) implement one shared,
// future-proof mechanism -- ResizeObserver in the child, postMessage to a
// same-origin parent that resizes only the matching iframe -- rather than a
// per-widget table of hand-calibrated pixel heights (WP16, batching and
// oscillation-tolerance added here). This spec enumerates every iframe once
// and checks the contract generically, so a future activity that reuses
// `startHeightReporting()` is covered automatically.
//
// Contract, checked per iframe after layout settles:
//   - iframe height is at least the child document's required height
//     (within IFRAME_UNDERSHOOT_TOLERANCE_PX);
//   - bottom slack (iframe height minus child required height) does not
//     exceed BOTTOM_SLACK_TOLERANCE_PX;
//   - the child document has no vertical scrollbar caused by clipping
//     (its content does not exceed the iframe's own rendered height);
//   - the gap below the activity's own last element does not exceed
//     TRAILING_GAP_TOLERANCE_PX (WP38R sec 7.1: fails on excessive blank
//     space, not just on clipping or a reporting-pipeline mismatch);
//   - a control change, AND a reset/"try again" contraction back to the
//     default state where one exists, still leave the contract holding
//     (re-verified after whichever resize each should trigger);
//   - dark mode and a 390px viewport still fit the same contract;
//   - no resize-message or cross-window runtime error is emitted throughout.
//
// WP38R sec 7: `childScrollHeight` is read from `document.body.scrollHeight`,
// not `document.documentElement.scrollHeight` -- the latter is defined by
// the CSSOM View spec as the greater of the viewport's own height and the
// content's height, so it can never report a value smaller than the
// iframe's OWN current height and would silently pass even a permanently
// stuck-too-tall iframe. See `measureContract` below and
// `interactive/src/resize-report.ts` for the fix this mirrors.

const BOTTOM_SLACK_TOLERANCE_PX = 32;
const IFRAME_UNDERSHOOT_TOLERANCE_PX = 4;
const SETTLE_TIMEOUT_MS = 15_000;

// WP38R sec 7.1: the distance between the content's own last meaningful
// element and the bottom of the content box, derived from the shared
// design's own intentional spacing rather than picked to make a known-bad
// number pass -- `.widget-root`'s own bottom padding (20px, styles.css) plus
// the largest bottom margin any trailing element can carry (`.widget-plot`'s
// 28px, when a chart -- not a `<ul class="widget-prompts">` -- happens to be
// an activity's last element) plus ~8px of headroom for cross-platform
// line-height/list-margin rounding (WP16's own 12px-clearance note already
// measured a ~6px Linux/Chromium-vs-macOS difference at this same boundary).
// Measured baselines: every activity ending on `<ul class="widget-prompts">`
// (the common case) sits at ~24px; this tolerance is deliberately still well
// under the 40-220px of dead space the pre-fix `.widget-plot { min-height:
// 320px }` produced for any activity with one or more sub-320px charts
// (leakage-lab: 2x300px plots; pca-kmeans-explorer: four sub-320px panels),
// so it still fails on that regression.
const TRAILING_GAP_TOLERANCE_PX = 60;

interface ActivityCase {
  chapterUrl: string;
  iframeSelector: string;
}

function iframeByTitle(title: string): string {
  return `iframe[title="${title}"]`;
}

const CASES: ActivityCase[] = [
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html", iframeSelector: iframeByTitle("Interactive head, tail, and sample comparison for the ABIDE-II table") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html", iframeSelector: iframeByTitle("Interactive ABIDE-II complete-case retention explorer") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html", iframeSelector: iframeByTitle("Interactive histogram of ABIDE-II variable distributions") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html", iframeSelector: iframeByTitle("Interactive ABIDE-II feature correlation explorer") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_02/exercise_02.html", iframeSelector: iframeByTitle("Interactive KNN neighbour-count exploration for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html", iframeSelector: iframeByTitle("Interactive decision-threshold exploration for classifying autism vs. control from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_03/exercise_03.html", iframeSelector: iframeByTitle("Interactive class-imbalance exploration for classifying autism vs. control from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html", iframeSelector: iframeByTitle("Interactive single-split and cross-validation stability comparison for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html", iframeSelector: iframeByTitle("Interactive KNN tuning activity: choose k before revealing the test result") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_04/exercise_04.html", iframeSelector: iframeByTitle("Interactive nested cross-validation explorer for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html", iframeSelector: iframeByTitle("Interactive feature-set comparison for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_05/exercise_05.html", iframeSelector: iframeByTitle("Interactive Ridge/Lasso regularization exploration for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html", iframeSelector: iframeByTitle("Interactive greedy-splitting activity for a small synthetic regression tree") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_06/exercise_06.html", iframeSelector: iframeByTitle("Interactive comparison of a single tree, bagging, and Random Forest for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html", iframeSelector: iframeByTitle("Interactive stage-by-stage gradient boosting activity on a small simulated dataset") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_07/exercise_07.html", iframeSelector: iframeByTitle("Interactive gradient-boosting parameter explorer for predicting age from brain structure") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html", iframeSelector: iframeByTitle("Interactive projection-angle activity for a small simulated two-dimensional dataset") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_08/exercise_08.html", iframeSelector: iframeByTitle("Interactive PCA and K-means explorer for ABIDE-II participants") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html", iframeSelector: iframeByTitle("Interactive PCR-versus-PLS activity for a small simulated two-dimensional dataset") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_09/exercise_09.html", iframeSelector: iframeByTitle("Interactive SVM decision-boundary explorer for two synthetic classification datasets") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html", iframeSelector: iframeByTitle("Interactive multiple-selection question on which preprocessing and modelling steps must not use the final test participants") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html", iframeSelector: iframeByTitle("Interactive leakage-lab comparing correct and leaky preprocessing pipelines on ABIDE-II cortical thickness and age") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html", iframeSelector: iframeByTitle("Interactive comparison of random-window and participant-grouped cross-validation on UCI HAR smartphone sensor windows") },
  { chapterUrl: "/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html", iframeSelector: iframeByTitle("Interactive comparison of ordinary and class-weighted logistic regression for imbalanced autism classification") },
];

async function waitForBookReady(page: Page): Promise<void> {
  await page.waitForFunction(
    () => document.documentElement.dataset.mode !== undefined && document.documentElement.dataset.mode !== "",
    undefined,
    { timeout: 15000 },
  );
}

async function activityFrame(page: Page, iframeSelector: string): Promise<Frame> {
  await page.locator(iframeSelector).scrollIntoViewIfNeeded();
  const handle = await page.locator(iframeSelector).elementHandle();
  expect(handle, `${iframeSelector} element present`).not.toBeNull();
  const frame = await handle!.contentFrame();
  expect(frame, `${iframeSelector} content frame present`).not.toBeNull();
  return frame!;
}

async function waitForWidgetReady(frame: Frame): Promise<void> {
  await frame.waitForFunction(
    () => document.querySelector("#app")?.getAttribute("data-widget-ready") === "true",
    undefined,
    { timeout: SETTLE_TIMEOUT_MS },
  );
}

// Polls the iframe's own rendered height AND its (same-origin) child
// document's scroll width together until BOTH stop changing across
// consecutive animation frames -- a state/layout condition, not an
// arbitrary sleep, per WP35 §20. Tracking width alongside height matters
// after a viewport/theme change: Plotly's own responsive relayout is
// asynchronous, so a snapshot taken between the resize event and that
// relayout completing can catch a real but transient horizontal overflow.
async function waitForIframeLayoutToSettle(
  page: Page,
  iframeSelector: string,
): Promise<{ height: number; childScrollWidth: number; childClientWidth: number }> {
  const handle = await page.waitForFunction(
    (sel: string) => {
      const w = window as unknown as {
        __mlSettle?: Record<
          string,
          { lastHeight: number; lastScrollW: number; lastClientW: number; stableSinceMs: number }
        >;
      };
      w.__mlSettle ??= {};
      const state = (w.__mlSettle[sel] ??= { lastHeight: -1, lastScrollW: -1, lastClientW: -1, stableSinceMs: -1 });
      const el = document.querySelector(sel) as HTMLIFrameElement | null;
      const doc = el?.contentDocument;
      if (!el || !doc) return false;
      const height = el.getBoundingClientRect().height;
      const scrollWidth = doc.documentElement.scrollWidth;
      const clientWidth = doc.documentElement.clientWidth;
      const now = performance.now();
      // All three must be stable together, for a sustained duration (not
      // merely a handful of animation frames): the outer iframe box itself
      // can still be mid-transition after a viewport/theme change because
      // the book theme's OWN sidebar/TOC-visibility JS debounces its
      // resize handling independently of this page's content -- the
      // child's own content can finish reflowing and hold still for
      // several frames at the container's still-wide, pre-collapse width,
      // which a short frame-count check would misread as "settled" before
      // the theme's debounced collapse actually finishes. Requiring
      // wall-clock stability rides out that debounce without assuming its
      // exact duration.
      const changed =
        Math.abs(height - state.lastHeight) >= 1 ||
        Math.abs(scrollWidth - state.lastScrollW) >= 1 ||
        Math.abs(clientWidth - state.lastClientW) >= 1;
      if (changed || state.stableSinceMs < 0) {
        state.stableSinceMs = now;
      }
      state.lastHeight = height;
      state.lastScrollW = scrollWidth;
      state.lastClientW = clientWidth;
      return now - state.stableSinceMs >= 400
        ? { height, childScrollWidth: scrollWidth, childClientWidth: clientWidth }
        : false;
    },
    iframeSelector,
    { timeout: SETTLE_TIMEOUT_MS, polling: "raf" },
  );
  return handle.jsonValue() as Promise<{ height: number; childScrollWidth: number; childClientWidth: number }>;
}

interface ContractSnapshot {
  iframeHeight: number;
  childScrollHeight: number;
  childClientWidthOverflow: number;
  trailingGap: number | null;
}

async function measureContract(page: Page, iframeSelector: string): Promise<ContractSnapshot> {
  const frame = await activityFrame(page, iframeSelector);
  await waitForWidgetReady(frame);
  const settled = await waitForIframeLayoutToSettle(page, iframeSelector);
  // WP38R sec 7: `document.documentElement.scrollHeight` (the `<html>`
  // element) is defined by the CSSOM View spec as the GREATER of the
  // viewport's own height and the content's rendered height -- it can never
  // report a value smaller than whatever height this iframe currently has,
  // which is exactly why an iframe that starts (or was ever) too tall could
  // never shrink back down (confirmed by direct measurement: forcing a short
  // activity's viewport taller than its content left `documentElement
  // .scrollHeight` stuck at the viewport's height even after the content was
  // shrunk further -- see WP38R_REPORT.md sec 5). `document.body.scrollHeight`
  // has no such floor and reflects the true, current content height in both
  // directions -- this is also what `resize-report.ts` itself now measures,
  // so this assertion is checking the real contract, not a tautology against
  // the same clamped number the pipeline already reported.
  const { childScrollHeight, trailingGap } = await frame.evaluate(() => {
    const height = document.body.scrollHeight;
    const app = document.getElementById("app");
    const last = app?.lastElementChild ?? null;
    const gap = last ? height - last.getBoundingClientRect().bottom : null;
    return { childScrollHeight: height, trailingGap: gap };
  });
  return {
    iframeHeight: settled.height,
    childScrollHeight,
    childClientWidthOverflow: settled.childScrollWidth - settled.childClientWidth,
    trailingGap,
  };
}

function assertContract(snapshot: ContractSnapshot, label: string): void {
  const { iframeHeight, childScrollHeight } = snapshot;
  expect(iframeHeight, `${label}: iframe height must reach the child's required height`).toBeGreaterThanOrEqual(
    childScrollHeight - IFRAME_UNDERSHOOT_TOLERANCE_PX,
  );
  expect(iframeHeight - childScrollHeight, `${label}: bottom slack within tolerance`).toBeLessThanOrEqual(
    BOTTOM_SLACK_TOLERANCE_PX,
  );
  // No internal vertical scrollbar caused by clipping: the child's own
  // content must not exceed the iframe's rendered height.
  expect(childScrollHeight, `${label}: child content not clipped by its own iframe height`).toBeLessThanOrEqual(
    iframeHeight + IFRAME_UNDERSHOOT_TOLERANCE_PX,
  );
  expect(snapshot.childClientWidthOverflow, `${label}: no horizontal scrollbar`).toBeLessThanOrEqual(1);
  // WP38R sec 7.1: the residual space below the activity's own last element
  // must be limited to the design's intentional padding, not a large dead
  // region -- this is the assertion that actually fails on excessive blank
  // space (as opposed to the checks above, which only fail on clipping or a
  // reporting-pipeline mismatch).
  if (snapshot.trailingGap !== null) {
    expect(snapshot.trailingGap, `${label}: trailing gap within intentional padding`).toBeLessThanOrEqual(
      TRAILING_GAP_TOLERANCE_PX,
    );
    expect(snapshot.trailingGap, `${label}: trailing gap is not negative (no overlap/clipping)`).toBeGreaterThanOrEqual(
      0,
    );
  }
}

test.describe("iframe height contract (every activity, Exercises 1-10)", () => {
  for (const { chapterUrl, iframeSelector } of CASES) {
    const label = `${chapterUrl} ${iframeSelector}`;

    test.describe(`iframe height contract: ${label}`, () => {
      test.describe.configure({ timeout: 60_000 });

      test("fits its content after settle, survives a control change, and fits in dark mode at 390px", async ({ page }) => {
      // Pre-existing page-chrome noise unrelated to the iframe-resize
      // contract this spec checks (a Thebe double-declaration and a
      // one-time "invalid theme mode" warning during the book's own
      // color-mode bootstrap, both independent of any activity iframe) --
      // excluded here so this spec fails only on a genuine resize/runtime
      // regression, not on unrelated pre-existing book-chrome console noise.
      const KNOWN_UNRELATED_NOISE = [/THEBE_JS_URL' has already been declared/, /Got invalid theme mode/];
      const runtimeErrors: string[] = [];
      const record = (text: string) => {
        if (KNOWN_UNRELATED_NOISE.some((re) => re.test(text))) return;
        runtimeErrors.push(text);
      };
      page.on("pageerror", (e) => record(String(e)));
      page.on("console", (msg) => {
        if (msg.type() === "error") record(msg.text());
      });

      await page.emulateMedia({ colorScheme: "light" });
      await page.setViewportSize({ width: 1350, height: 1200 });
      await page.goto(chapterUrl, { waitUntil: "commit" });
      await waitForBookReady(page);

      const initial = await measureContract(page, iframeSelector);
      assertContract(initial, `${label} (initial)`);

      // A control change should leave the contract holding after the resize
      // it may trigger -- covers "controls still fit" without assuming
      // every control changes height (many legitimately do not).
      const frame = await activityFrame(page, iframeSelector);
      const selectHandle = await frame.locator("select").first();
      if (await selectHandle.count()) {
        const options = await selectHandle.locator("option").all();
        if (options.length > 1) {
          const lastValue = await options[options.length - 1]!.getAttribute("value");
          if (lastValue !== null) {
            await selectHandle.selectOption(lastValue);
            const afterControl = await measureContract(page, iframeSelector);
            assertContract(afterControl, `${label} (after control change)`);
          }
        }
      }

      // WP38R sec 7.1: explicitly exercise a CONTRACTION, not just any
      // change -- "Reset"/"Try again" returns every one of these activities
      // to its shorter default state, which is exactly the transition the
      // pre-fix `document.documentElement.scrollHeight` (viewport-floored)
      // measurement could never report correctly once the iframe had grown
      // taller than that default.
      const resetButton = frame.locator('button[data-testid*="reset" i]').first();
      if (await resetButton.count()) {
        await resetButton.click();
        const afterReset = await measureContract(page, iframeSelector);
        assertContract(afterReset, `${label} (after reset)`);
      }

      // Dark mode + 390px narrow viewport.
      await page.locator("button.theme-switch-button").first().click();
      await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
      await page.setViewportSize({ width: 390, height: 900 });
      const darkNarrow = await measureContract(page, iframeSelector);
      assertContract(darkNarrow, `${label} (dark, 390px)`);

      expect(runtimeErrors, `${label}: no resize-message or runtime errors`).toEqual([]);
      });
    });
  }
});
