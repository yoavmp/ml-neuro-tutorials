// Production activity: ABIDE-II variable distributions.
//
// A labelled variable selector and an exact bin-count slider drive a Plotly
// *bar* trace built from the pure, unit-tested `computeHistogram` (src/histogram.ts).
// Bin count and counts are therefore exactly the tested values. No Python
// kernel, no CDN, no participant-level detail — hover shows a bin range and a
// count only.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { EdaHistogramConfig } from "../config";
import { computeHistogram } from "../histogram";
import {
  parseAbideHistogramData,
  type AbideHistogramData,
} from "../histogram-data";

function prefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function mount(args: MountArgs<EdaHistogramConfig, AbideHistogramData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const missingVariables = config.variables
    .map((v) => v.name)
    .filter((name) => !Object.prototype.hasOwnProperty.call(data.columns, name));
  if (missingVariables.length > 0) {
    throw new Error(
      `The data file is missing column(s) required by this activity: ${missingVariables.join(", ")}.`,
    );
  }

  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const controls = document.createElement("div");
  controls.className = "widget-controls";

  // --- variable selector ---
  const varLabel = document.createElement("label");
  varLabel.setAttribute("for", "histogram-variable");
  varLabel.textContent = "Variable:";
  const varSelect = document.createElement("select");
  varSelect.id = "histogram-variable";
  varSelect.setAttribute("data-testid", "histogram-variable");
  for (const variable of config.variables) {
    const opt = document.createElement("option");
    opt.value = variable.name;
    opt.textContent = variable.label;
    varSelect.appendChild(opt);
  }
  varSelect.value = config.defaultVariable;

  // --- bin-count slider ---
  const binLabel = document.createElement("label");
  binLabel.setAttribute("for", "histogram-bins");
  binLabel.textContent = "Number of bins:";
  const binInput = document.createElement("input");
  binInput.id = "histogram-bins";
  binInput.type = "range";
  binInput.min = String(config.bins.min);
  binInput.max = String(config.bins.max);
  binInput.step = String(config.bins.step);
  binInput.value = String(config.bins.default);
  binInput.setAttribute("data-testid", "histogram-bins");
  const binValue = document.createElement("output");
  binValue.setAttribute("for", "histogram-bins");
  binValue.setAttribute("data-testid", "histogram-bins-value");
  binValue.className = "widget-bin-value";
  binValue.textContent = String(config.bins.default);

  const varGroup = document.createElement("div");
  varGroup.className = "widget-control";
  varGroup.append(varLabel, varSelect);
  const binGroup = document.createElement("div");
  binGroup.className = "widget-control";
  binGroup.append(binLabel, binInput, binValue);
  controls.append(varGroup, binGroup);
  container.appendChild(controls);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "histogram-stats");
  container.appendChild(stats);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "histogram-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  const message = document.createElement("p");
  message.className = "widget-empty";
  message.setAttribute("data-testid", "histogram-message");
  message.hidden = true;
  container.appendChild(message);

  if (config.reflectionPrompts.length > 0) {
    const promptsHeading = document.createElement("h2");
    promptsHeading.className = "widget-subhead";
    promptsHeading.textContent = "Reflect";
    const list = document.createElement("ul");
    list.className = "widget-prompts";
    for (const prompt of config.reflectionPrompts) {
      const li = document.createElement("li");
      li.textContent = prompt;
      list.appendChild(li);
    }
    container.append(promptsHeading, list);
  }

  const dark = prefersDark();
  const axisColor = dark ? "#c9c9c9" : "#333333";
  const gridColor = dark ? "#3a3a3a" : "#e2e2e2";
  const barColor = dark ? "#5a9bd4" : "#2a6f9e";

  const plotConfig = { displayModeBar: false, responsive: true };

  let destroyed = false;

  function labelFor(name: string): string {
    return config.variables.find((v) => v.name === name)?.label ?? name;
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    const variableName = varSelect.value;
    const requestedBins = Number(binInput.value);
    binValue.textContent = String(requestedBins);

    const observations = data.columns[variableName] ?? [];
    const result = computeHistogram(observations, requestedBins);

    stats.textContent =
      `Available N: ${result.availableN.toLocaleString()} · ` +
      `Missing N: ${result.missingN.toLocaleString()}`;

    plot.dataset.activeVariable = variableName;
    plot.dataset.activeBins = String(requestedBins);
    plot.dataset.kind = result.kind;

    if (result.kind === "empty") {
      Plotly.purge(plot);
      plot.dataset.barCount = "0";
      message.hidden = false;
      message.textContent = `No observations are available for ${labelFor(variableName)}.`;
      const nextEmpty = Number(plot.dataset.renderCount ?? "0") + 1;
      plot.dataset.renderCount = String(nextEmpty);
      return;
    }
    message.hidden = true;

    const widths = result.binEdges
      .slice(1)
      .map((right, i) => right - result.binEdges[i]!);

    const trace = {
      type: "bar" as const,
      x: result.binCenters,
      y: result.counts,
      width: widths,
      customdata: result.binLabels,
      marker: { color: barColor, line: { color: dark ? "#1b1b1b" : "#ffffff", width: 1 } },
      hovertemplate: "Bin %{customdata}<br>Count %{y}<extra></extra>",
    };

    const layout = {
      margin: { t: 12, r: 12, b: 48, l: 56 },
      height: 360,
      autosize: true,
      bargap: 0,
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor },
      xaxis: {
        title: { text: config.xAxisLabel ?? labelFor(variableName) },
        gridcolor: gridColor,
        zeroline: false,
      },
      yaxis: {
        title: { text: config.yAxisLabel ?? "Number of participants" },
        gridcolor: gridColor,
        zeroline: false,
        rangemode: "tozero" as const,
      },
    };

    await Plotly.react(plot, [trace], layout, plotConfig);
    if (destroyed) return;

    plot.dataset.barCount = String(result.counts.length);
    const next = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(next);
  }

  varSelect.addEventListener("change", () => void draw());
  binInput.addEventListener("change", () => void draw());
  binInput.addEventListener("input", () => {
    binValue.textContent = binInput.value;
  });

  void draw();

  return {
    destroy() {
      destroyed = true;
      Plotly.purge(plot);
    },
  };
}

export const histogramComponent: WidgetComponent<EdaHistogramConfig, AbideHistogramData> = {
  type: "eda-histogram",
  parseData: parseAbideHistogramData,
  mount,
};
