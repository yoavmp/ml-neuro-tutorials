// Production activity: Exercise 8's "Find the Best Projection" (WP33).
//
// A small, fixed, mean-centered synthetic two-dimensional point cloud. The
// student drags an angle slider to choose a projection axis; the plot shows
// the points, the axis, and each point's projected position with a
// perpendicular residual line back to it. The panel below reports the
// variance captured by that axis and the reconstruction MSE left behind.
// The true PC1 direction and its explained-variance ratio stay hidden until
// the student presses "Show PC1". Everything is closed-form trigonometry
// over the precomputed point cloud (../pca-projection-data.ts); nothing is
// fit live here.

import Plotly from "plotly.js-cartesian-dist-min";
import type { PlotData } from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { PcaProjectionConfig } from "../config";
import { parsePcaProjectionData, projectAtAngle, type PcaProjectionData } from "../pca-projection-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const DEFAULT_ANGLE_DEG = 90;

function symmetricRange(data: PcaProjectionData, padFrac: number): [number, number] {
  const maxAbs = Math.max(...data.observations.flatMap((o) => [Math.abs(o.x), Math.abs(o.y)]));
  const padded = maxAbs * (1 + padFrac);
  return [-padded, padded];
}

function mount(args: MountArgs<PcaProjectionConfig, PcaProjectionData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let angleDeg = DEFAULT_ANGLE_DEG;
  let revealed = false;

  const axisRange = symmetricRange(data, 0.15);

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const syntheticNote = document.createElement("p");
  syntheticNote.className = "widget-note";
  syntheticNote.setAttribute("data-testid", "pca-projection-synthetic-note");
  syntheticNote.textContent = data.syntheticDataNote;
  container.appendChild(syntheticNote);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const angleGroup = document.createElement("div");
  angleGroup.className = "widget-control";
  const angleLabel = document.createElement("label");
  angleLabel.setAttribute("for", "pca-projection-angle");
  angleLabel.textContent = "Projection angle (degrees):";
  const angleSlider = document.createElement("input");
  angleSlider.id = "pca-projection-angle";
  angleSlider.type = "range";
  angleSlider.min = String(data.angleSliderDeg.min);
  angleSlider.max = String(data.angleSliderDeg.max);
  angleSlider.step = String(data.angleSliderDeg.step);
  angleSlider.value = String(DEFAULT_ANGLE_DEG);
  angleSlider.setAttribute("data-testid", "pca-projection-angle-slider");
  angleSlider.setAttribute(
    "aria-label",
    `Projection angle in degrees, from ${data.angleSliderDeg.min} to ${data.angleSliderDeg.max}`,
  );
  const angleValue = document.createElement("output");
  angleValue.setAttribute("for", "pca-projection-angle");
  angleValue.setAttribute("data-testid", "pca-projection-angle-value");
  angleValue.className = "widget-bin-value";
  angleGroup.append(angleLabel, angleSlider, angleValue);
  controls.appendChild(angleGroup);
  container.appendChild(controls);

  const buttonRow = document.createElement("div");
  buttonRow.className = "widget-controls";

  const revealButton = document.createElement("button");
  revealButton.type = "button";
  revealButton.setAttribute("data-testid", "pca-projection-reveal-button");

  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.textContent = "Reset";
  resetButton.setAttribute("data-testid", "pca-projection-reset-button");

  buttonRow.append(revealButton, resetButton);
  container.appendChild(buttonRow);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "pca-projection-stats");
  stats.setAttribute("role", "status");
  stats.setAttribute("aria-live", "polite");
  container.appendChild(stats);

  const revealText = document.createElement("p");
  revealText.className = "widget-stats";
  revealText.setAttribute("data-testid", "pca-projection-reveal-text");
  container.appendChild(revealText);

  // --- plot ---------------------------------------------------------
  const plotHeading = document.createElement("h2");
  plotHeading.className = "widget-subhead";
  plotHeading.textContent = "Points, the current axis, and each point's projection";
  container.appendChild(plotHeading);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "pca-projection-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  if (config.reflectionPrompts && config.reflectionPrompts.length > 0) {
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = "Reflect";
    const list = document.createElement("ul");
    list.className = "widget-prompts";
    for (const p of config.reflectionPrompts) {
      const li = document.createElement("li");
      li.textContent = p;
      list.appendChild(li);
    }
    container.append(h, list);
  }

  // --- drawing ---------------------------------------------------------

  function axisLinePoints(deg: number, halfLength: number): { x: number[]; y: number[] } {
    const theta = (deg * Math.PI) / 180;
    const ux = Math.cos(theta);
    const uy = Math.sin(theta);
    return { x: [-ux * halfLength, ux * halfLength], y: [-uy * halfLength, uy * halfLength] };
  }

  async function drawPlot(): Promise<void> {
    if (destroyed) return;
    const result = projectAtAngle(data, angleDeg);
    const theta = (angleDeg * Math.PI) / 180;
    const ux = Math.cos(theta);
    const uy = Math.sin(theta);
    const halfLength = axisRange[1];

    const points = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Observed points",
      x: data.observations.map((o) => o.x),
      y: data.observations.map((o) => o.y),
      marker: { color: theme.markerPrimary, size: 9 },
      hovertemplate: `${data.featureX.label} %{x}<br>${data.featureY.label} %{y}<extra></extra>`,
    };

    const axisLine = axisLinePoints(angleDeg, halfLength);
    const axisTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: `Projection axis (${angleDeg.toFixed(0)} deg)`,
      x: axisLine.x,
      y: axisLine.y,
      line: { color: theme.diagonalLine, width: 3 },
      hoverinfo: "skip" as const,
    };

    const residualX: number[] = [];
    const residualY: number[] = [];
    const projectedX: number[] = [];
    const projectedY: number[] = [];
    data.observations.forEach((o, i) => {
      const t = result.projected[i]!;
      const px = t * ux;
      const py = t * uy;
      projectedX.push(px);
      projectedY.push(py);
      residualX.push(o.x, px, NaN);
      residualY.push(o.y, py, NaN);
    });

    const residualTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: "Residual (perpendicular to the axis)",
      x: residualX,
      y: residualY,
      line: { color: theme.axisColor, width: 1, dash: "dot" as const },
      hoverinfo: "skip" as const,
    };

    const projectedTrace = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Projected position",
      x: projectedX,
      y: projectedY,
      marker: { color: theme.diagonalLine, size: 6, symbol: "circle-open" as const },
      hoverinfo: "skip" as const,
    };

    const traces: PlotData[] = [residualTrace, points, axisTrace, projectedTrace];

    if (revealed) {
      const trueLine = axisLinePoints(data.truePc1.angleDeg, halfLength);
      traces.push({
        type: "scatter" as const,
        mode: "lines" as const,
        name: `True PC1 (${data.truePc1.angleDeg.toFixed(1)} deg)`,
        x: trueLine.x,
        y: trueLine.y,
        line: { color: theme.annotationText, width: 2, dash: "dash" as const },
        hoverinfo: "skip" as const,
      });
    }

    const layout = buildPlotLayout(theme, {
      height: 420,
      showlegend: true,
      xaxis: { title: { text: data.featureX.label }, range: [...axisRange] },
      yaxis: {
        title: { text: data.featureY.label },
        range: [...axisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    });
    await Plotly.react(plot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    plot.dataset.renderCount = String(Number(plot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const result = projectAtAngle(data, angleDeg);
    angleValue.textContent = `${angleDeg.toFixed(0)} deg`;
    stats.textContent =
      `Angle = ${angleDeg.toFixed(0)} deg  ·  variance captured = ${result.varianceCaptured.toFixed(2)} ` +
      `(${(result.proportionVarianceCaptured * 100).toFixed(0)}% of total)  ·  ` +
      `reconstruction MSE = ${result.reconstructionMSE.toFixed(2)}.`;
    revealText.textContent = revealed
      ? `True PC1 direction: ${data.truePc1.angleDeg.toFixed(1)} deg, explaining ` +
        `${(data.truePc1.explainedVarianceRatio * 100).toFixed(0)}% of the total variance.`
      : "";
    revealButton.textContent = revealed ? "Hide PC1" : "Show PC1";
    revealButton.setAttribute("aria-pressed", String(revealed));
    container.dataset.angleDeg = angleDeg.toFixed(1);
    container.dataset.revealed = String(revealed);
    container.dataset.varianceCaptured = result.varianceCaptured.toFixed(4);
    container.dataset.reconstructionMse = result.reconstructionMSE.toFixed(4);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    drawText();
    await drawPlot();
  }

  angleSlider.addEventListener("input", () => {
    angleDeg = Number(angleSlider.value);
    void draw();
  });

  revealButton.addEventListener("click", () => {
    revealed = !revealed;
    void draw();
  });

  resetButton.addEventListener("click", () => {
    angleDeg = DEFAULT_ANGLE_DEG;
    revealed = false;
    angleSlider.value = String(DEFAULT_ANGLE_DEG);
    void draw();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void draw();
  });

  void draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(plot);
    },
  };
}

export const pcaProjectionComponent: WidgetComponent<PcaProjectionConfig, PcaProjectionData> = {
  type: "pca-projection",
  parseData: parsePcaProjectionData,
  mount,
};
