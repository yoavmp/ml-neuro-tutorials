# WP31R3 Exact Changelog

Diff scope, `WP31R2_RELEASE_SHA` (`f12967beaed9a4e16b4930e2881e28435478d388`)
to `WP31R3_RELEASE_SHA` (`4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`):

```
 WPs/WP31R3_CHAPTER01_DARK_MODE_STABILITY_AND_REDEPLOY.md | 324 +++++++++++++
 WPs/reports/WP31R2_EXACT_CHANGELOG.md                    |  75 +++
 WPs/reports/WP31R2_REPORT.md                             | 368 ++++++++++++++
 interactive/e2e-book/chapter01-dark-mode.spec.ts         | 231 ++++++++--
 4 files changed, 957 insertions(+), 41 deletions(-)
```

`WPs/reports/WP31R2_EXACT_CHANGELOG.md` and `WPs/reports/WP31R2_REPORT.md`
were already-committed local-only content from WP31R2 (its documentation
commit, `8e2a827`, one commit ahead of `origin/main` at the start of this
WP); they were merged unchanged. `WPs/WP31R3_CHAPTER01_DARK_MODE_STABILITY_AND_REDEPLOY.md`
is this WP's own specification, committed as its first checkpoint
(`2d38421`) before any implementation change.

## The narrow correction itself

One file changed: `interactive/e2e-book/chapter01-dark-mode.spec.ts`
(+231/-41).

### Summary of the change

* Replaced `activityFrame()` + `waitForRendered()` (a single `expect(locator).toHaveAttribute("data-render-count", /[1-9]/)` gated by the default 5s timeout) with:
  * `waitForActivityNavigationStarted(page, iframeSelector)` — polls (250ms interval, 10s timeout) for `iframe.contentDocument.URL !== "about:blank"`, re-issuing `scrollIntoView()` on every attempt.
  * `waitForActivityRendered(page, iframeSelector, testId)` — polls (every animation frame, 20s timeout) `iframe.contentDocument` directly for the plot element, populated Plotly `_fullData`/`_fullLayout`, a valid `data-render-count`, and a non-zero bounding box; on failure, reports exactly which condition(s) are unmet.
  * `activityFrame()` retained, now called only after both waits confirm readiness, to obtain the Playwright `Frame` used for the final style-snapshot `evaluate()` calls.
* `snapshotHistogram`/`snapshotCorrelation` now take `page: Page` directly (calling both waits + `activityFrame` internally) instead of a pre-fetched `Frame` — every call site collapsed from an `activityFrame(...)` + `snapshotX(frame)` pair into one `snapshotX(page)` call. No assertion at any call site was added, removed, or changed.

### Full diff

```diff
diff --git a/interactive/e2e-book/chapter01-dark-mode.spec.ts b/interactive/e2e-book/chapter01-dark-mode.spec.ts
index 88673ae..d32e281 100644
--- a/interactive/e2e-book/chapter01-dark-mode.spec.ts
+++ b/interactive/e2e-book/chapter01-dark-mode.spec.ts
@@ -50,25 +50,181 @@ async function waitForBookReady(page: Page): Promise<void> {
   );
 }
 
-async function activityFrame(page: Page, selector: string): Promise<Frame> {
-  // Each activity iframe is `loading="lazy"` (book/_static, WP16), so it only
-  // starts fetching its own document once scrolled near the viewport. Plain
-  // `.scrollIntoView()` (bypassing Playwright's actionability/"stable
-  // bounding box" wait) is used deliberately: `activity-resize.js` keeps
-  // nudging the iframe's own `height` attribute as its content settles, which
-  // can keep `scrollIntoViewIfNeeded()`'s stability check from ever
-  // resolving.
-  const locator = page.locator(selector);
-  await locator.evaluate((el) => el.scrollIntoView({ block: "center" }));
-  const handle = await locator.elementHandle();
-  expect(handle, `${selector} element present`).not.toBeNull();
+// Each activity iframe is `loading="lazy"` (book/_static, WP16), so it only
+// starts fetching its own document once the browser's native lazy-load
+// intersection check recognizes it as near the viewport. Plain
+// `.scrollIntoView()` (bypassing Playwright's actionability/"stable
+// bounding box" wait) is used deliberately: `activity-resize.js` keeps
+// nudging the iframe's own `height` attribute as its content settles, which
+// can keep `scrollIntoViewIfNeeded()`'s stability check from ever resolving.
+//
+// WP31R3: a single `scrollIntoView()` call issued immediately after a
+// full-page `reload()` can race the browser's own layout pass -- if layout
+// has not yet stabilized at the moment of the call, the intersection check
+// silently does not register and the iframe's `contentDocument` stays at
+// `"about:blank"` indefinitely. Direct reproduction confirmed this exactly
+// (WPs/reports/WP31R3_REPORT.md): every failure of this kind showed
+// `contentDocument.URL === "about:blank"` even after 20+ seconds -- not a
+// slow render, a lazy-load trigger that never fired. A real reader's
+// natural scrolling fires many intersection checks over the course of
+// scrolling and does not hit this; a single synthetic `scrollIntoView()`
+// gets exactly one chance. Wait for the observable precondition --
+// navigation away from `"about:blank"` has actually started -- re-issuing
+// the scroll on every polling attempt (confirmed empirically to recover
+// within 1-3 attempts, ~600-900ms) rather than calling it once and hoping.
+async function waitForActivityNavigationStarted(page: Page, iframeSelector: string): Promise<void> {
+  try {
+    await page.waitForFunction(
+      (iframeSelector: string) => {
+        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
+        if (!iframe) return false;
+        iframe.scrollIntoView({ block: "center" });
+        const url = iframe.contentDocument?.URL;
+        return !!url && url !== "about:blank";
+      },
+      iframeSelector,
+      { timeout: 10_000, polling: 250 },
+    );
+  } catch {
+    throw new Error(
+      `${iframeSelector}: navigation never started (contentDocument stayed at about:blank) within 10s -- ` +
+        `the native lazy-load intersection check did not trigger despite repeated scrollIntoView() attempts`,
+    );
+  }
+}
+
+async function activityFrame(page: Page, iframeSelector: string): Promise<Frame> {
+  const handle = await page.locator(iframeSelector).elementHandle();
+  expect(handle, `${iframeSelector} element present`).not.toBeNull();
   const frame = await handle!.contentFrame();
-  expect(frame, `${selector} content frame present`).not.toBeNull();
+  expect(frame, `${iframeSelector} content frame present`).not.toBeNull();
   return frame!;
 }
 
-async function waitForRendered(frame: Frame, testId: string): Promise<void> {
-  await expect(frame.locator(`[data-testid="${testId}"]`)).toHaveAttribute("data-render-count", /[1-9]/);
+// WP31R3: once `waitForActivityNavigationStarted` above confirms the iframe
+// is actually loading, this waits for it to finish rendering. Plain
+// `data-render-count` bumping (Plotly's own React-resolve signal, also read
+// by chapter05-visual-policy.spec.ts and wp22-cross-chapter-dark-mode.spec.ts)
+// only means `Plotly.react()`'s promise settled, and gating on that alone
+// through the default 5s `expect` timeout is its own smaller readiness
+// race: a cold iframe's module execution + data fetch + first Plotly draw
+// can legitimately take a couple of seconds under load, on top of whatever
+// time `waitForActivityNavigationStarted` already spent recovering the
+// lazy-load trigger. Not a stuck or broken widget -- the identical code
+// renders correctly in the large majority of runs and in every other
+// render within the same test (WPs/reports/WP31R3_REPORT.md). Waiting via
+// a `Frame` object obtained through `elementHandle().contentFrame()` before
+// the iframe's own navigation has settled can itself stall for many
+// seconds waiting on that frame's execution context, so this waits from
+// the STABLE parent-page context instead, reading straight through
+// `iframe.contentDocument` (same-origin, so this is a synchronous,
+// same-process DOM read, not a separate cross-frame round trip) for the
+// complete observable render-complete state: the iframe document and plot
+// element exist, Plotly has actually populated `_fullData`/`_fullLayout`
+// (the same properties wp22-cross-chapter-dark-mode.spec.ts reads for its
+// own color assertions, not just the render-count side effect),
+// `data-render-count` is a valid non-zero marker, and the rendered box is
+// non-zero -- polled every animation frame (as
+// chapter05-visual-policy.spec.ts's `waitForStableGeometry` already does)
+// with a longer, explicit, condition-specific timeout. This is not a
+// blanket global-timeout increase: it is a local wait for a more complete,
+// more specific condition, sized to the evidence gathered during diagnosis
+// rather than picked arbitrarily. Frame-to-frame stability (as
+// `waitForStableGeometry` also does, for Plotly's `automargin` relayout
+// pass) is not needed here: the colors this spec asserts on are
+// marker/bar/grid fill values set synchronously within the same completed
+// `Plotly.react()` draw, not values `automargin` revisits afterward. Only
+// once this confirms the render is complete does `activityFrame()` obtain
+// the actual Playwright `Frame` object used for the style snapshot below,
+// by which point its execution context is already live.
+async function waitForActivityRendered(page: Page, iframeSelector: string, testId: string): Promise<void> {
+  try {
+    await page.waitForFunction(
+      ({ iframeSelector, testId }: { iframeSelector: string; testId: string }) => {
+        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
+        const doc = iframe?.contentDocument;
+        if (!doc) return false;
+        const el = doc.querySelector(`[data-testid="${testId}"]`) as
+          | (HTMLElement & { _fullData?: unknown[]; _fullLayout?: Record<string, unknown> })
+          | null;
+        if (!el) return false;
+        const renderCount = Number(el.dataset.renderCount ?? "0");
+        if (!Number.isFinite(renderCount) || renderCount < 1) return false;
+        if (!Array.isArray(el._fullData) || el._fullData.length === 0) return false;
+        if (!el._fullLayout || Object.keys(el._fullLayout).length === 0) return false;
+        const rect = el.getBoundingClientRect();
+        return rect.width > 0 && rect.height > 0;
+      },
+      { iframeSelector, testId },
+      { timeout: 20_000, polling: "raf" },
+    );
+  } catch {
+    const state = await page.evaluate(
+      ({ iframeSelector, testId }: { iframeSelector: string; testId: string }) => {
+        const iframe = document.querySelector(iframeSelector) as HTMLIFrameElement | null;
+        const doc = iframe?.contentDocument;
+        if (!doc) {
+          return {
+            iframeExists: !!iframe,
+            docAccessible: false,
+            exists: false,
+            renderCount: 0,
+            hasFullData: false,
+            hasFullLayout: false,
+            boxWidth: 0,
+            boxHeight: 0,
+          };
+        }
+        const el = doc.querySelector(`[data-testid="${testId}"]`) as
+          | (HTMLElement & { _fullData?: unknown[]; _fullLayout?: Record<string, unknown> })
+          | null;
+        if (!el) {
+          return {
+            iframeExists: true,
+            docAccessible: true,
+            exists: false,
+            renderCount: 0,
+            hasFullData: false,
+            hasFullLayout: false,
+            boxWidth: 0,
+            boxHeight: 0,
+          };
+        }
+        const rect = el.getBoundingClientRect();
+        return {
+          iframeExists: true,
+          docAccessible: true,
+          exists: true,
+          renderCount: Number(el.dataset.renderCount ?? "0"),
+          hasFullData: Array.isArray(el._fullData) && el._fullData.length > 0,
+          hasFullLayout: !!el._fullLayout && Object.keys(el._fullLayout).length > 0,
+          boxWidth: rect.width,
+          boxHeight: rect.height,
+        };
+      },
+      { iframeSelector, testId },
+    );
+    const unmet: string[] = [];
+    if (!state.iframeExists) {
+      unmet.push("iframe element does not exist");
+    } else if (!state.docAccessible) {
+      unmet.push("iframe contentDocument is not accessible");
+    } else if (!state.exists) {
+      unmet.push(`[data-testid="${testId}"] does not exist inside the iframe document`);
+    } else {
+      if (!Number.isFinite(state.renderCount) || state.renderCount < 1) {
+        unmet.push(`data-render-count is ${state.renderCount}, expected >= 1`);
+      }
+      if (!state.hasFullData) unmet.push("Plotly _fullData is not yet populated");
+      if (!state.hasFullLayout) unmet.push("Plotly _fullLayout is not yet populated");
+      if (!(state.boxWidth > 0 && state.boxHeight > 0)) {
+        unmet.push(`bounding box is ${state.boxWidth}x${state.boxHeight}, expected non-zero`);
+      }
+    }
+    throw new Error(
+      `${iframeSelector} [data-testid="${testId}"] did not reach a fully-rendered state within 20s: ${unmet.join("; ")}`,
+    );
+  }
 }
 
 interface ChartSnapshot {
@@ -79,8 +235,10 @@ interface ChartSnapshot {
   dragRectStrokes: string[];
 }
 
-async function snapshotHistogram(frame: Frame): Promise<ChartSnapshot> {
-  await waitForRendered(frame, "histogram-plot");
+async function snapshotHistogram(page: Page): Promise<ChartSnapshot> {
+  await waitForActivityNavigationStarted(page, HIST_SEL);
+  await waitForActivityRendered(page, HIST_SEL, "histogram-plot");
+  const frame = await activityFrame(page, HIST_SEL);
   return frame.evaluate(() => {
     const plot = document.querySelector('[data-testid="histogram-plot"]')!;
     const bar = plot.querySelector(".bars path");
@@ -96,8 +254,10 @@ async function snapshotHistogram(frame: Frame): Promise<ChartSnapshot> {
   });
 }
 
-async function snapshotCorrelation(frame: Frame): Promise<ChartSnapshot> {
-  await waitForRendered(frame, "correlation-plot");
+async function snapshotCorrelation(page: Page): Promise<ChartSnapshot> {
+  await waitForActivityNavigationStarted(page, CORR_SEL);
+  await waitForActivityRendered(page, CORR_SEL, "correlation-plot");
+  const frame = await activityFrame(page, CORR_SEL);
   return frame.evaluate(() => {
     const plot = document.querySelector('[data-testid="correlation-plot"]')!;
     const point = plot.querySelector("g.points path.point");
@@ -130,10 +290,8 @@ test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", ()
     await waitForBookReady(page);
 
     // --- 1. light mode (book default: "auto", resolved against light OS) ---
-    let hist = await activityFrame(page, HIST_SEL);
-    let corr = await activityFrame(page, CORR_SEL);
-    const histLight = await snapshotHistogram(hist);
-    const corrLight = await snapshotCorrelation(corr);
+    const histLight = await snapshotHistogram(page);
+    const corrLight = await snapshotCorrelation(page);
     expect(histLight.bodyBg, "histogram light: widget card background").toBe(LIGHT.bg);
     expect(histLight.barOrMarkerFill, "histogram light: bar color").toBe(LIGHT.histBar);
     expect(histLight.gridStroke, "histogram light: gridline color").toBe(LIGHT.gridColor);
@@ -144,10 +302,8 @@ test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", ()
     await page.locator("button.theme-switch-button").first().click();
     await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
 
-    hist = await activityFrame(page, HIST_SEL);
-    corr = await activityFrame(page, CORR_SEL);
-    const histDark = await snapshotHistogram(hist);
-    const corrDark = await snapshotCorrelation(corr);
+    const histDark = await snapshotHistogram(page);
+    const corrDark = await snapshotCorrelation(page);
     expect(histDark.bodyBg, "histogram dark: widget card background").toBe(DARK.bg);
     expect(histDark.barOrMarkerFill, "histogram dark: bar color").toBe(DARK.histBar);
     expect(histDark.gridStroke, "histogram dark: gridline color").toBe(DARK.gridColor);
@@ -166,10 +322,8 @@ test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", ()
     // book's own localStorage. ---
     await page.reload({ waitUntil: "commit" });
     await waitForBookReady(page);
-    hist = await activityFrame(page, HIST_SEL);
-    corr = await activityFrame(page, CORR_SEL);
-    const histReloaded = await snapshotHistogram(hist);
-    const corrReloaded = await snapshotCorrelation(corr);
+    const histReloaded = await snapshotHistogram(page);
+    const corrReloaded = await snapshotCorrelation(page);
     expect(histReloaded.bodyBg, "histogram reload-in-dark: widget card background").toBe(DARK.bg);
     expect(histReloaded.barOrMarkerFill, "histogram reload-in-dark: bar color").toBe(DARK.histBar);
     expect(corrReloaded.bodyBg, "correlation reload-in-dark: widget card background").toBe(DARK.bg);
@@ -179,10 +333,8 @@ test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", ()
     await page.locator("button.theme-switch-button").first().click();
     await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
 
-    hist = await activityFrame(page, HIST_SEL);
-    corr = await activityFrame(page, CORR_SEL);
-    const histRestored = await snapshotHistogram(hist);
-    const corrRestored = await snapshotCorrelation(corr);
+    const histRestored = await snapshotHistogram(page);
+    const corrRestored = await snapshotCorrelation(page);
     expect(histRestored.bodyBg, "histogram restored-light: widget card background").toBe(LIGHT.bg);
     expect(histRestored.barOrMarkerFill, "histogram restored-light: bar color").toBe(LIGHT.histBar);
     expect(corrRestored.bodyBg, "correlation restored-light: widget card background").toBe(LIGHT.bg);
@@ -198,20 +350,17 @@ test.describe("Chapter 1 built page — dark-mode Plotly theme sync (WP22)", ()
 
     await toggle.click(); // auto -> dark
     await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
-    let hist = await activityFrame(page, HIST_SEL);
-    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(DARK.histBar);
+    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(DARK.histBar);
 
     await toggle.click(); // dark -> light
     await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
-    hist = await activityFrame(page, HIST_SEL);
-    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(LIGHT.histBar);
+    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(LIGHT.histBar);
 
     await toggle.click(); // light -> auto (resolves to light against light OS emulation)
     await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
 
     await toggle.click(); // auto -> dark
     await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
-    hist = await activityFrame(page, HIST_SEL);
-    expect((await snapshotHistogram(hist)).barOrMarkerFill).toBe(DARK.histBar);
+    expect((await snapshotHistogram(page)).barOrMarkerFill).toBe(DARK.histBar);
   });
 });
```

## Commits, in order

| Commit | Message | Files |
|---|---|---|
| `2d38421` | WP31R3: add specification (initial checkpoint) | `WPs/WP31R3_CHAPTER01_DARK_MODE_STABILITY_AND_REDEPLOY.md` (new) |
| `3050ee6` | Stabilize Chapter 1 dark-mode rendering test | `interactive/e2e-book/chapter01-dark-mode.spec.ts` |
| `4f0dc06` | Stabilize Chapter 1 dark-mode rendering test (merge, `--no-ff`) | merges `3050ee6` into `main`; `WP31R3_RELEASE_SHA` |

Pushed to `origin/main`: `f12967b..4f0dc06`. Triggered GitHub Actions run
`35513291539` (headSha `4f0dc06`): **all steps passed**, including
"End-to-end test the built Chapter 1 page" (the step that failed twice
before) and "Publish website". `gh-pages` moved from
`9dbe3b10ac31363aa1ef9cd8418a1b9cdd56ca12` to
`803f98875090787e1108eb714e427d235f032fc4`. Full production verification
passed — see `WPs/reports/WP31R3_REPORT.md` §9–§10. **Exercises 4–6 are
live.**
