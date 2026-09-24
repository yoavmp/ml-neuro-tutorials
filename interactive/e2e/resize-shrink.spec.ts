import { expect, test } from "@playwright/test";

// WP38R sec 7: regression test for the root cause of "excessive empty space
// below interactive content" -- `resize-report.ts` used to measure
// `document.documentElement.scrollHeight`, which the CSSOM View spec defines
// as the GREATER of the viewport's own height and the content's rendered
// height. Every activity iframe starts life at its notebook's static pre-JS
// `height` attribute (always an approximation of the real content, and
// frequently taller than it, e.g. a round number chosen for a different
// viewport width) -- so `documentElement.scrollHeight` could never correct
// back down to the true, shorter content height: it would report the
// iframe's OWN current (too-tall) height forever, a one-directional
// "reporting only growth" defect. `document.body.scrollHeight` has no such
// viewport floor.
//
// This is reproduced here with a minimal synthetic parent page (served from
// the SAME origin as the widget app, via a route so postMessage's
// same-origin targetOrigin check behaves exactly as in production) that
// starts a real activity iframe at a static height much taller than that
// activity's real content, using the exact same resize contract
// (`ml-activity-resize` message, `iframe[src*="/widgets/app/"]` selector,
// `Math.max(MIN_HEIGHT, ...)` clamp) as `book/_static/activity-resize.js`.

const PARENT_URL = "/__wp38r_resize_shrink_harness__.html";

function parentHtml(iframeSrc: string, staticHeight: number): string {
  return `<!doctype html>
<html><head><meta charset="utf-8"></head><body>
<iframe id="frame" src="${iframeSrc}" loading="eager" width="100%" height="${staticHeight}"
  class="ml-activity" style="width:100%;"></iframe>
<script>
(function () {
  "use strict";
  var MIN_HEIGHT = 200, MAX_HEIGHT = 8000, IGNORE_DELTA_PX = 2;
  window.__resizeLog = [];
  function onMessage(event) {
    if (event.origin !== window.location.origin) return;
    var data = event.data;
    if (!data || data.type !== "ml-activity-resize" || typeof data.height !== "number") return;
    var iframes = document.querySelectorAll('iframe[src*="/widgets/app/"]');
    for (var i = 0; i < iframes.length; i += 1) {
      if (iframes[i].contentWindow === event.source) {
        var height = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, Math.round(data.height)));
        var current = parseInt(iframes[i].style.height, 10);
        window.__resizeLog.push({ raw: data.height, applied: height });
        if (!isNaN(current) && Math.abs(height - current) < IGNORE_DELTA_PX) return;
        iframes[i].style.height = height + "px";
        return;
      }
    }
  }
  window.addEventListener("message", onMessage);
})();
</script>
</body></html>`;
}

test("an iframe started far taller than its real content shrinks down to that content's true height", async ({
  page,
}) => {
  // table_inspection's default config renders well under 900px; starting the
  // static fallback at 1400px reproduces the exact "generous/approximate
  // static height" starting condition every real activity iframe begins in.
  const STATIC_HEIGHT = 1400;
  const iframeSrc = "/app/index.html?config=../configs/table_inspection.json#/widgets/app/";

  await page.route(`**${PARENT_URL}`, (route) =>
    route.fulfill({ contentType: "text/html", body: parentHtml(iframeSrc, STATIC_HEIGHT) }),
  );
  await page.goto(PARENT_URL);

  const frame = page.frameLocator("#frame");
  await expect(frame.locator("#app")).toHaveAttribute("data-widget-ready", "true");

  // Give the ResizeObserver/rAF pipeline time to settle.
  await expect
    .poll(async () => Number((await page.locator("#frame").evaluate((el) => (el as HTMLIFrameElement).style.height)).replace("px", "")))
    .toBeLessThan(STATIC_HEIGHT);

  const finalHeight = Number(
    (await page.locator("#frame").evaluate((el) => (el as HTMLIFrameElement).style.height)).replace("px", ""),
  );
  const trueContentHeight = await frame.locator("body").evaluate((el) => el.scrollHeight);

  // The iframe must settle close to the TRUE content height, not stay stuck
  // near the static fallback -- the exact defect this test guards against.
  expect(finalHeight, "iframe shrank to (approximately) the real content height").toBeLessThanOrEqual(
    trueContentHeight + 20,
  );
  expect(finalHeight).toBeGreaterThanOrEqual(trueContentHeight - 20);
  expect(finalHeight, "iframe did not stay stuck at the oversized static fallback").toBeLessThan(
    STATIC_HEIGHT - 200,
  );
});
