// Reports this page's full document height to a same-origin embedding parent
// (WP16). The Jupyter Book pages embed each activity in an `<iframe>` with a
// single static `height` attribute -- but a `<details>` disclosure opening, a
// training-sample tab switching plots, or the Exercise 2 / knn-abc
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
export function startHeightReporting(): void {
  if (typeof window === "undefined" || window.parent === window) return;
  if (typeof ResizeObserver === "undefined") return;

  let lastHeight = 0;
  function report(): void {
    const height = document.documentElement.scrollHeight;
    if (height === lastHeight) return;
    lastHeight = height;
    window.parent.postMessage({ type: "ml-activity-resize", height }, window.location.origin);
  }

  new ResizeObserver(report).observe(document.documentElement);
  report();
}
