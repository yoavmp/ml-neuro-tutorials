// Reports this page's full document height to a same-origin embedding parent
// (WP16, batching/oscillation-tolerance added by WP35 §17). The Jupyter Book
// pages embed each activity in an `<iframe>` with a single static `height`
// attribute -- but a `<details>` disclosure opening, a training-sample tab
// switching plots, a Plotly relayout, a light/dark theme change, or a
// comparison grid collapsing from side-by-side panels to a stacked column at
// a narrow iframe width all change this page's real height without a
// navigation. A single static number cannot stay correct at every viewport
// width (measured: the book theme's own sidebar/TOC visibility is not even
// monotonic in outer viewport width, so a CSS breakpoint on the outer page
// can't reliably predict it either) -- so this reports the actual height and
// `book/_static/activity-resize.js` keeps the embedding iframe in sync.
//
// No-ops when not embedded (e.g. the standalone Vite preview used by the e2e
// suite) and only ever posts to this page's own origin.
//
// WP38R sec 7: this used to observe and measure `document.documentElement`
// (the `<html>` element). That is the root cause of the "excessive blank
// space below interactive content" defect -- per the CSSOM View spec, the
// *root* element's `scrollHeight` is defined as the greater of the
// viewport's height and the content's rendered height, so it can never
// report a value smaller than whatever height the iframe is CURRENTLY set
// to. Every activity starts life exactly in that too-tall state (the
// notebook's static pre-JS `height` attribute is always an approximation of
// the real content, and is frequently taller than it), and any later
// content contraction (a control resetting to shorter text, a comparison
// grid collapsing) is invisible to `documentElement.scrollHeight` for the
// same reason -- confirmed by direct measurement: forcing a short
// activity's viewport taller than its content made `documentElement
// .scrollHeight` stick at the viewport's own height even after the content
// was shrunk further, while `document.body.scrollHeight` tracked the real,
// smaller value throughout (see WP38R_REPORT.md sec 5). `<body>` has no such
// viewport floor -- its `scrollHeight` (and its own laid-out box, which
// `ResizeObserver` watches below) reflect only its actual content, in both
// directions, which is exactly what this needs to report.
//
// WP35 §17.5: a ResizeObserver can fire many times within the same frame
// (e.g. Plotly re-drawing several stacked plots during one relayout) and
// sub-pixel/scrollbar rounding can oscillate a reported height by a pixel or
// two indefinitely. Both are handled here: callbacks are coalesced with
// requestAnimationFrame so at most one message is posted per rendered frame,
// and a height change of less than IGNORE_DELTA_PX is treated as noise, not
// a real content-size change -- preventing a resize message/parent
// iframe.height write loop.
//
// WP38R sec 7 (second finding): the height reported on each firing is the
// ResizeObserver entry's OWN `contentRect.height`, not a fresh
// `document.body.scrollHeight` read taken when the deferred rAF callback
// runs. Measured directly on a dynamically-sized chart (regularization-
// explore's coefficient plot, whose height depends on how many coefficients
// are shown): on the specific frame a shrink settles, the entry's
// `contentRect.height` already reported the correct, final, smaller value,
// while a `document.body.scrollHeight` read one (or even two) animation
// frames later still returned the previous, larger value and never
// corrected afterward -- no further resize fires because `<body>`'s own
// content box, which is what ResizeObserver watches, does not change again.
// The entry's `contentRect` is the authoritative measurement FOR the resize
// event that produced it; re-deriving the same quantity via a separately
// timed property read is exactly the gap that let a stale value slip
// through and stick.
const IGNORE_DELTA_PX = 2;

export function startHeightReporting(): void {
  if (typeof window === "undefined" || window.parent === window) return;
  if (typeof ResizeObserver === "undefined") return;

  let lastReportedHeight = 0;
  let rafHandle: number | undefined;
  let pendingHeight = document.body.scrollHeight;

  function postHeight(): void {
    rafHandle = undefined;
    const height = pendingHeight;
    if (Math.abs(height - lastReportedHeight) < IGNORE_DELTA_PX) return;
    lastReportedHeight = height;
    window.parent.postMessage({ type: "ml-activity-resize", height }, window.location.origin);
  }

  function scheduleReport(height: number): void {
    pendingHeight = height;
    if (rafHandle !== undefined) return; // already coalescing this frame
    rafHandle = window.requestAnimationFrame(postHeight);
  }

  new ResizeObserver((entries) => {
    scheduleReport(entries[entries.length - 1]!.contentRect.height);
  }).observe(document.body);
  scheduleReport(document.body.scrollHeight);
}
