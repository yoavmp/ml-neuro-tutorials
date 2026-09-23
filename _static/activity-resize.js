/*
 * WP16 -- dynamic height sync for embedded activity iframes.
 *
 * Root cause: each activity iframe's HTML `height` attribute is a single
 * static number chosen for one viewport width. The activity's own content
 * reflows at other widths -- comparison grids (e.g. Exercise 2's feature-set
 * comparison) collapse from side-by-side panels to a stacked single column below
 * about 620px of iframe width, `<details>` disclosures open, controls wrap to
 * more rows -- so a single static number either clips content at some widths
 * or leaves a large blank region at others. The book theme's own responsive
 * layout (sidebar / in-page TOC visibility) is not even monotonic in the
 * outer page's viewport width, so no fixed CSS breakpoint on the outer page
 * can reliably predict when an iframe's *own* rendered width will trigger its
 * internal layout to reflow.
 *
 * Fix: each activity iframe (interactive/src/resize-report.ts) observes its
 * own document height and posts it to this same-origin parent whenever it
 * changes; this script keeps that one iframe's `height` in sync. Each
 * notebook's HTML `height` attribute remains as the pre-JS fallback -- a sane
 * initial size before the first message arrives, and the size used if
 * JavaScript is unavailable.
 */
(function () {
  "use strict";

  var MIN_HEIGHT = 200;
  var MAX_HEIGHT = 8000;
  // WP35 §17.5: skip a write that would change the on-screen height by less
  // than this -- the child already coalesces/filters (resize-report.ts), but
  // guarding here too means a stray duplicate or near-duplicate message can
  // never itself become a source of layout jitter on the parent page.
  var IGNORE_DELTA_PX = 2;

  function onMessage(event) {
    if (event.origin !== window.location.origin) return;
    var data = event.data;
    if (!data || data.type !== "ml-activity-resize" || typeof data.height !== "number") return;

    var iframes = document.querySelectorAll('iframe[src*="/widgets/app/"]');
    for (var i = 0; i < iframes.length; i += 1) {
      if (iframes[i].contentWindow === event.source) {
        var height = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, Math.round(data.height)));
        var current = parseInt(iframes[i].style.height, 10);
        if (!isNaN(current) && Math.abs(height - current) < IGNORE_DELTA_PX) break;
        iframes[i].style.height = height + "px";
        break;
      }
    }
  }

  window.addEventListener("message", onMessage);
})();
