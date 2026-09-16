import { describe, expect, it } from "vitest";
import { getPlotlyTheme, buildPlotLayout } from "../src/components/plotly-policy";

// WP22: every Plotly-bearing component must get a genuinely distinct, fully
// explicit palette for each theme -- not a shared/blank one that happens to
// look plausible in a snapshot. These assert the actual values differ and
// that the essential surfaces (backgrounds, gridlines, legend, axis text)
// are never left unset.

describe("getPlotlyTheme — explicit light/dark palettes", () => {
  it("returns two genuinely different palettes, not the same colors twice", () => {
    const light = getPlotlyTheme("light");
    const dark = getPlotlyTheme("dark");
    expect(light.dark).toBe(false);
    expect(dark.dark).toBe(true);
    expect(light.axisColor).not.toBe(dark.axisColor);
    expect(light.gridColor).not.toBe(dark.gridColor);
    expect(light.legendBg).not.toBe(dark.legendBg);
    expect(light.legendText).not.toBe(dark.legendText);
    expect(light.markerPrimary).not.toBe(dark.markerPrimary);
    expect(light.diagonalLine).not.toBe(dark.diagonalLine);
  });

  it("every color field is a non-empty explicit string in both themes", () => {
    for (const theme of [getPlotlyTheme("light"), getPlotlyTheme("dark")]) {
      for (const [key, value] of Object.entries(theme)) {
        if (key === "dark") continue;
        expect(typeof value, `${key} should be a string`).toBe("string");
        expect((value as string).length, `${key} should not be empty`).toBeGreaterThan(0);
      }
    }
  });
});

describe("buildPlotLayout — theme wiring into the shared layout helper", () => {
  it("carries the resolved axis/grid/legend colors from the theme into the layout, not a default", () => {
    const dark = getPlotlyTheme("dark");
    const layout = buildPlotLayout(dark) as unknown as {
      font: { color: string };
      xaxis: { gridcolor: string; linecolor: string; tickcolor: string };
      yaxis: { gridcolor: string; linecolor: string; tickcolor: string };
      legend: { bgcolor: string; font: { color: string } };
    };
    expect(layout.font.color).toBe(dark.axisColor);
    expect(layout.xaxis.gridcolor).toBe(dark.gridColor);
    expect(layout.xaxis.linecolor).toBe(dark.axisColor);
    expect(layout.xaxis.tickcolor).toBe(dark.axisColor);
    expect(layout.yaxis.gridcolor).toBe(dark.gridColor);
    expect(layout.legend.bgcolor).toBe(dark.legendBg);
    expect(layout.legend.font.color).toBe(dark.legendText);
  });

  it("keeps the transparent paper/plot background policy in both themes (the widget card supplies the real surface)", () => {
    for (const theme of [getPlotlyTheme("light"), getPlotlyTheme("dark")]) {
      const layout = buildPlotLayout(theme) as unknown as { paper_bgcolor: string; plot_bgcolor: string };
      expect(layout.paper_bgcolor).toBe("rgba(0,0,0,0)");
      expect(layout.plot_bgcolor).toBe("rgba(0,0,0,0)");
    }
  });

  it("keeps the WP16 interaction lock regardless of theme", () => {
    const layout = buildPlotLayout(getPlotlyTheme("dark")) as unknown as {
      dragmode: unknown;
      xaxis: { fixedrange: unknown };
      yaxis: { fixedrange: unknown };
    };
    expect(layout.dragmode).toBe(false);
    expect(layout.xaxis.fixedrange).toBe(true);
    expect(layout.yaxis.fixedrange).toBe(true);
  });

  it("still lets a component override a nested axis key without losing the shared theme defaults alongside it", () => {
    const dark = getPlotlyTheme("dark");
    const layout = buildPlotLayout(dark, { xaxis: { range: [0, 1] } }) as unknown as {
      xaxis: { range: number[]; gridcolor: string; fixedrange: unknown; automargin: unknown };
    };
    expect(layout.xaxis.range).toEqual([0, 1]);
    expect(layout.xaxis.gridcolor).toBe(dark.gridColor);
    expect(layout.xaxis.fixedrange).toBe(true);
    expect(layout.xaxis.automargin).toBe(true);
  });
});
