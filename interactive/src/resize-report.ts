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
// WP35 §17.5: a ResizeObserver can fire many times within the same frame
// (e.g. Plotly re-drawing several stacked plots during one relayout) and
// sub-pixel/scrollbar rounding can oscillate a reported height by a pixel or
// two indefinitely. Both are handled here: callbacks are coalesced with
// requestAnimationFrame so at most one message is posted per rendered frame,
// and a height change of less than IGNORE_DELTA_PX is treated as noise, not
// a real content-size change -- preventing a resize message/parent
// iframe.height write loop.
const IGNORE_DELTA_PX = 2;

export function startHeightReporting(): void {
  if (typeof window === "undefined" || window.parent === window) return;
  if (typeof ResizeObserver === "undefined") return;

  let lastReportedHeight = 0;
  let rafHandle: number | undefined;

  function postHeight(): void {
    rafHandle = undefined;
    const height = document.documentElement.scrollHeight;
    if (Math.abs(height - lastReportedHeight) < IGNORE_DELTA_PX) return;
    lastReportedHeight = height;
    window.parent.postMessage({ type: "ml-activity-resize", height }, window.location.origin);
  }

  function scheduleReport(): void {
    if (rafHandle !== undefined) return; // already coalescing this frame
    rafHandle = window.requestAnimationFrame(postHeight);
  }

  new ResizeObserver(scheduleReport).observe(document.documentElement);
  scheduleReport();
}
