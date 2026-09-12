// One shared Plotly presentation policy for every activity chart (WP16).
//
// Every component used to redefine its own `prefersDark`/axis-color logic and
// hand-roll a `layout` object, which is how the project-wide bugs this module
// fixes crept in independently in several files: a fixed `height` + fixed
// bottom margin with no `automargin` (long axis titles painted outside the
// plot's own box and overlapped whatever came next in the DOM), free-standing
// axis drag/zoom (the lesson's controls are the sliders/selects, not the
// chart), and a plot card background that didn't match the page.
//
// `buildPlotLayout` is a deep-enough merge for the nested keys a component
// legitimately needs to override (`margin`, `xaxis`, `yaxis`, `legend`,
// `font`) so that overriding e.g. `xaxis.range` cannot silently drop the
// shared `fixedrange`/`automargin`/`gridcolor` defaults alongside it -- a
// naive `{ ...base, ...overrides }` would do exactly that.
import type { Config, Layout } from "plotly.js-cartesian-dist-min";

export interface PlotlyTheme {
  readonly dark: boolean;
  readonly axisColor: string;
  readonly gridColor: string;
}

export function getPlotlyTheme(): PlotlyTheme {
  const dark =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  return {
    dark,
    axisColor: dark ? "#c9c9c9" : "#333333",
    gridColor: dark ? "#3a3a3a" : "#e2e2e2",
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

const DEFAULT_LEGEND = { orientation: "h", y: 1.12 };

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
    zeroline: false,
  };

  return {
    autosize: true,
    dragmode: false,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    showlegend: false,
    ...rest,
    margin: { ...DEFAULT_MARGIN, ...margin },
    font: { color: theme.axisColor, ...font },
    legend: { ...DEFAULT_LEGEND, ...legend },
    xaxis: { ...axisDefaults, ...xaxis },
    yaxis: { ...axisDefaults, ...yaxis },
  } as Layout;
}
