// One shared Plotly presentation policy for every activity chart (WP16, WP22).
//
// Every component used to redefine its own `prefersDark`/axis-color logic and
// hand-roll a `layout` object, which is how the project-wide bugs this module
// fixes crept in independently in several files: a fixed `height` + fixed
// bottom margin with no `automargin` (long axis titles painted outside the
// plot's own box and overlapped whatever came next in the DOM), free-standing
// axis drag/zoom (the lesson's controls are the sliders/selects, not the
// chart), and a plot card background that didn't match the page.
//
// WP22: `getPlotlyTheme` used to call `matchMedia("(prefers-color-scheme:
// dark)")` itself, once, at mount time -- the OS/browser preference only,
// read exactly once. The published Jupyter Book's own light/dark toggle
// (pydata-sphinx-theme) never touches that media query; it resolves the
// reader's choice onto `document.documentElement.dataset.theme` on the PARENT
// document instead. `../theme.ts` is now the one place that resolves "what
// theme is active" (parent attribute, own attribute, then media query) and
// notifies subscribers when it changes; this module only turns that resolved
// `Theme` into concrete Plotly colors.
//
// `buildPlotLayout` is a deep-enough merge for the nested keys a component
// legitimately needs to override (`margin`, `xaxis`, `yaxis`, `legend`,
// `font`) so that overriding e.g. `xaxis.range` cannot silently drop the
// shared `fixedrange`/`automargin`/`gridcolor` defaults alongside it -- a
// naive `{ ...base, ...overrides }` would do exactly that.
import type { Config, Layout } from "plotly.js-cartesian-dist-min";
import type { Theme } from "../theme";

export interface PlotlyTheme {
  readonly dark: boolean;
  readonly axisColor: string;
  readonly gridColor: string;
  /** Legend chip background -- WP22: previously left as Plotly's default
   *  (an opaque near-white), unreadable once the surrounding page went dark. */
  readonly legendBg: string;
  readonly legendText: string;
  /** Default annotation text color; components may still override per-call
   *  (e.g. a reference-line label that needs to match its line's own hue). */
  readonly annotationText: string;
  /** The recurring "observed vs predicted" scatter marker color, identical
   *  across regression-compare / knn-abc / knn-explore before WP22 -- three
   *  independent copies of the same ternary. */
  readonly markerPrimary: string;
  /** The recurring dashed "perfect prediction" reference-line color, same
   *  three components. */
  readonly diagonalLine: string;
}

/** Turn the resolved app-wide `Theme` into concrete Plotly colors. */
export function getPlotlyTheme(theme: Theme): PlotlyTheme {
  const dark = theme === "dark";
  return {
    dark,
    axisColor: dark ? "#c9c9c9" : "#333333",
    gridColor: dark ? "#3a3a3a" : "#e2e2e2",
    legendBg: dark ? "rgba(36,34,47,0.82)" : "rgba(255,255,255,0.82)",
    legendText: dark ? "#ece9f5" : "#1b1826",
    annotationText: dark ? "#ece9f5" : "#1b1826",
    markerPrimary: dark ? "rgba(120,170,210,0.55)" : "rgba(42,111,158,0.5)",
    diagonalLine: dark ? "#d98b5f" : "#b5622f",
  };
}

/**
 * Runtime config shared by every ordinary lesson chart: no modebar, no
 * scroll-zoom, no double-click axis reset. Combined with the `dragmode:
 * false` + `fixedrange: true` axis defaults in `buildPlotLayout`, students can
 * no longer accidentally drag/zoom/pan a chart -- the lesson's own controls
 * (sliders, selects, tabs) remain the only way to change what is plotted.
 * Hover tooltips are unaffected by any of this.
 */
export const PLOT_CONFIG: Partial<Config> = {
  displayModeBar: false,
  responsive: true,
  scrollZoom: false,
  doubleClick: false,
};

type AxisOverrides = Record<string, unknown>;

export interface LayoutOverrides {
  margin?: Partial<{ t: number; r: number; b: number; l: number }>;
  height?: number;
  showlegend?: boolean;
  legend?: Record<string, unknown>;
  xaxis?: AxisOverrides;
  yaxis?: AxisOverrides;
  font?: Record<string, unknown>;
  [key: string]: unknown;
}

// Generous enough for every current activity's short titles at the real
// deployed content width; components only need to override what genuinely
// differs (e.g. a taller bottom margin for rotated site-name tick labels).
const DEFAULT_MARGIN = { t: 12, r: 12, b: 48, l: 56 };

// WP27R: the "Choose k Before Revealing the Test Set" activity grew a third
// stacked subplot (train / validation / test), each with its own Plotly axis
// object (`xaxis`/`xaxis2`/`xaxis3`, `yaxis`/`yaxis2`/`yaxis3`) sharing the
// same axis policy below. Rather than hand-rolling that policy again per
// extra axis, any override key matching this pattern gets the same
// `axisDefaults` merge that `xaxis`/`yaxis` already receive.
const EXTRA_AXIS_KEY_RE = /^[xy]axis\d+$/;

export function buildPlotLayout(theme: PlotlyTheme, overrides: LayoutOverrides = {}): Layout {
  const { margin, xaxis, yaxis, legend, font, ...rest } = overrides;

  // `automargin` is the actual fix for the title/next-element overlap: with a
  // fixed figure `height`, it lets Plotly grow an axis's margin to fit its
  // title and tick labels while *shrinking the plot area to compensate*,
  // instead of painting the title outside the figure's own box. `fixedrange`
  // + the config's `dragmode: false` above is the interaction lock.
  const axisDefaults = {
    fixedrange: true,
    automargin: true,
    gridcolor: theme.gridColor,
    linecolor: theme.axisColor,
    tickcolor: theme.axisColor,
    zeroline: false,
  };

  const defaultLegend = {
    orientation: "h",
    y: 1.12,
    bgcolor: theme.legendBg,
    font: { color: theme.legendText },
  };

  const extraAxes: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(rest)) {
    if (EXTRA_AXIS_KEY_RE.test(key)) {
      extraAxes[key] = { ...axisDefaults, ...(value as AxisOverrides) };
      delete rest[key];
    }
  }

  return {
    autosize: true,
    dragmode: false,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
    ...rest,
    margin: { ...DEFAULT_MARGIN, ...margin },
    font: { color: theme.axisColor, ...font },
    legend: { ...defaultLegend, ...legend },
    xaxis: { ...axisDefaults, ...xaxis },
    yaxis: { ...axisDefaults, ...yaxis },
    ...extraAxes,
  } as Layout;
}
