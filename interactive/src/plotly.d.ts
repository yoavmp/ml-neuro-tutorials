// Minimal ambient types for the locally bundled Plotly distribution.
// `plotly.js-cartesian-dist-min` ships no .d.ts. We only use newPlot / react /
// purge, so declare just those rather than pulling in the full @types/plotly.js.
declare module "plotly.js-cartesian-dist-min" {
  type PlotData = Record<string, unknown>;
  type Layout = Record<string, unknown>;
  interface Config {
    displayModeBar?: boolean;
    staticPlot?: boolean;
    responsive?: boolean;
    [key: string]: unknown;
  }

  interface PlotlyStatic {
    newPlot(
      root: HTMLElement,
      data: PlotData[],
      layout?: Partial<Layout>,
      config?: Partial<Config>,
    ): Promise<HTMLElement>;
    react(
      root: HTMLElement,
      data: PlotData[],
      layout?: Partial<Layout>,
      config?: Partial<Config>,
    ): Promise<HTMLElement>;
    purge(root: HTMLElement): void;
  }

  const Plotly: PlotlyStatic;
  export default Plotly;
}
