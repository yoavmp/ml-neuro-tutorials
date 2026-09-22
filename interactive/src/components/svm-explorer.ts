// Production activity: Exercise 9's "Explore an SVM Boundary" (WP34).
//
// Two fixed, deterministic synthetic 2-D classification datasets -- one
// approximately linear, one not. Every (dataset, kernel, C, gamma)
// combination in the bounded grid is precomputed with scikit-learn's SVC
// (scripts/export_svm_explorer_widget.py); nothing is fit live here. Gamma
// is irrelevant for the linear kernel, so its control is disabled (never
// silently ignored) whenever that kernel is selected. This activity is
// explicitly conceptual exploration, not a model-selection procedure.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { SvmExplorerConfig, SvmExplorerDataset, SvmExplorerKernel } from "../config";
import { parseSvmExplorerData, catalogEntryFor, decodeDecisionGrid, type SvmExplorerData } from "../svm-explorer-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const CLASS_COLORS = ["#4c72b0", "#dd8452"];

function mount(args: MountArgs<SvmExplorerConfig, SvmExplorerData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let dataset: SvmExplorerDataset = data.datasets[config.defaultDataset] ? config.defaultDataset : "linear";
  let kernel: SvmExplorerKernel = data.kernelOptions.includes(config.defaultKernel) ? config.defaultKernel : data.kernelOptions[0]!;
  let c = data.cGrid.includes(config.defaultC) ? config.defaultC : data.cGrid[0]!;
  let gamma = data.gammaGrid.includes(config.defaultGamma) ? config.defaultGamma : data.gammaGrid[0]!;

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
  syntheticNote.setAttribute("data-testid", "svm-explorer-synthetic-note");
  syntheticNote.textContent = data.syntheticDataNote;
  container.appendChild(syntheticNote);

  const conceptualNote = document.createElement("p");
  conceptualNote.className = "widget-note";
  conceptualNote.setAttribute("data-testid", "svm-explorer-conceptual-note");
  conceptualNote.textContent =
    "This is conceptual exploration to build intuition for margins, support vectors, and kernels -- not a model-selection procedure.";
  container.appendChild(conceptualNote);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  function buildSelect(id: string, testId: string, labelText: string, options: { value: string; label: string }[]): {
    group: HTMLDivElement;
    select: HTMLSelectElement;
  } {
    const group = document.createElement("div");
    group.className = "widget-control";
    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelText;
    const select = document.createElement("select");
    select.id = id;
    select.setAttribute("data-testid", testId);
    for (const opt of options) {
      const o = document.createElement("option");
      o.value = opt.value;
      o.textContent = opt.label;
      select.appendChild(o);
    }
    group.append(label, select);
    return { group, select };
  }

  const datasetControl = buildSelect("svm-dataset", "svm-explorer-dataset-select", "Dataset:", [
    { value: "linear", label: "Approximately linear" },
    { value: "nonlinear", label: "Nonlinear" },
  ]);
  const kernelControl = buildSelect(
    "svm-kernel",
    "svm-explorer-kernel-select",
    "Kernel:",
    data.kernelOptions.map((k) => ({ value: k, label: k === "rbf" ? "RBF" : k === "poly" ? `Polynomial (degree ${data.polyDegree})` : "Linear" })),
  );
  const cControl = buildSelect(
    "svm-c",
    "svm-explorer-c-select",
    "C (error/margin-violation penalty):",
    data.cGrid.map((v) => ({ value: String(v), label: String(v) })),
  );
  const gammaControl = buildSelect(
    "svm-gamma",
    "svm-explorer-gamma-select",
    "Gamma (RBF/polynomial locality):",
    data.gammaGrid.map((v) => ({ value: String(v), label: String(v) })),
  );

  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.textContent = "Reset";
  resetButton.setAttribute("data-testid", "svm-explorer-reset-button");

  controls.append(datasetControl.group, kernelControl.group, cControl.group, gammaControl.group, resetButton);
  container.appendChild(controls);

  const gammaIrrelevantNote = document.createElement("p");
  gammaIrrelevantNote.className = "widget-note";
  gammaIrrelevantNote.setAttribute("data-testid", "svm-explorer-gamma-irrelevant-note");
  gammaIrrelevantNote.textContent = "Gamma has no effect on a linear kernel, so it is disabled above.";
  container.appendChild(gammaIrrelevantNote);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "svm-explorer-stats");
  stats.setAttribute("role", "status");
  stats.setAttribute("aria-live", "polite");
  container.appendChild(stats);

  // --- plot ---------------------------------------------------------
  const plotHeading = document.createElement("h2");
  plotHeading.className = "widget-subhead";
  plotHeading.textContent = "Decision regions, training/validation points, and support vectors";
  container.appendChild(plotHeading);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "svm-explorer-plot");
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

  // --- helpers ---------------------------------------------------------

  function currentEntry() {
    return catalogEntryFor(data, dataset, kernel, c, kernel === "linear" ? null : gamma);
  }

  function updateGammaControlState(): void {
    const irrelevant = kernel === "linear";
    gammaControl.select.disabled = irrelevant;
    gammaControl.select.setAttribute("aria-disabled", String(irrelevant));
    gammaIrrelevantNote.hidden = !irrelevant;
  }

  // --- drawing ---------------------------------------------------------

  async function drawPlot(): Promise<void> {
    if (destroyed) return;
    const d = data.datasets[dataset]!;
    const entry = currentEntry();
    const trainSet = new Set(d.trainIds);
    const svSet = new Set(entry.supportVectorIds);
    const grid = decodeDecisionGrid(entry.decisionGrid);

    const regionTrace = {
      type: "contour" as const,
      x: d.gridX,
      y: d.gridY,
      z: grid,
      showscale: false,
      colorscale: [
        [0, theme.dark ? "rgba(76,114,176,0.25)" : "rgba(76,114,176,0.18)"],
        [1, theme.dark ? "rgba(221,132,82,0.25)" : "rgba(221,132,82,0.18)"],
      ],
      contours: { coloring: "fill" as const, showlines: false },
      hoverinfo: "skip" as const,
    };

    const pointTraces = [0, 1].flatMap((label) =>
      [
        { ids: d.points.filter((p) => trainSet.has(p.id) && p.label === label && !svSet.has(p.id)), isTrain: true, name: `Class ${label} (train)`, symbol: "circle" as const, size: 8 },
        { ids: d.points.filter((p) => !trainSet.has(p.id) && p.label === label), isTrain: false, name: `Class ${label} (validation)`, symbol: "diamond" as const, size: 9 },
      ].map((group) => ({
        type: "scatter" as const,
        mode: "markers" as const,
        name: group.name,
        x: group.ids.map((p) => p.x),
        y: group.ids.map((p) => p.y),
        marker: { color: CLASS_COLORS[label], size: group.size, symbol: group.symbol, line: { color: theme.axisColor, width: 0.5 } },
        hovertemplate: `x %{x:.2f}<br>y %{y:.2f}<extra>${group.name}</extra>`,
      })),
    );

    const svPoints = d.points.filter((p) => svSet.has(p.id));
    const svTrace = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Support vectors",
      x: svPoints.map((p) => p.x),
      y: svPoints.map((p) => p.y),
      marker: {
        color: svPoints.map((p) => CLASS_COLORS[p.label]),
        size: 13,
        symbol: "circle-open" as const,
        line: { color: theme.annotationText, width: 2.5 },
      },
      hovertemplate: "support vector<extra></extra>",
    };

    const layout = buildPlotLayout(theme, {
      height: 440,
      showlegend: true,
      xaxis: { title: { text: "Feature 1" } },
      yaxis: { title: { text: "Feature 2" }, scaleanchor: "x" as const, scaleratio: 1 },
    });
    await Plotly.react(plot, [regionTrace, ...pointTraces, svTrace], layout, PLOT_CONFIG);
    if (destroyed) return;
    plot.dataset.renderCount = String(Number(plot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const entry = currentEntry();
    stats.textContent =
      `Dataset = ${dataset}  ·  kernel = ${kernel}  ·  C = ${c}` +
      `${kernel === "linear" ? "" : `  ·  gamma = ${gamma}`}  ·  ` +
      `training accuracy = ${(entry.trainAccuracy * 100).toFixed(0)}%  ·  ` +
      `validation accuracy = ${(entry.valAccuracy * 100).toFixed(0)}%  ·  ` +
      `support vectors = ${entry.nSupportVectors}.`;
    container.dataset.dataset = dataset;
    container.dataset.kernel = kernel;
    container.dataset.c = String(c);
    container.dataset.gamma = kernel === "linear" ? "na" : String(gamma);
    container.dataset.trainAccuracy = entry.trainAccuracy.toFixed(4);
    container.dataset.valAccuracy = entry.valAccuracy.toFixed(4);
    container.dataset.nSupportVectors = String(entry.nSupportVectors);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    updateGammaControlState();
    drawText();
    await drawPlot();
  }

  datasetControl.select.value = dataset;
  kernelControl.select.value = kernel;
  cControl.select.value = String(c);
  gammaControl.select.value = String(gamma);

  datasetControl.select.addEventListener("change", () => {
    dataset = datasetControl.select.value as SvmExplorerDataset;
    void draw();
  });
  kernelControl.select.addEventListener("change", () => {
    kernel = kernelControl.select.value as SvmExplorerKernel;
    void draw();
  });
  cControl.select.addEventListener("change", () => {
    c = Number(cControl.select.value);
    void draw();
  });
  gammaControl.select.addEventListener("change", () => {
    gamma = Number(gammaControl.select.value);
    void draw();
  });
  resetButton.addEventListener("click", () => {
    dataset = data.datasets[config.defaultDataset] ? config.defaultDataset : "linear";
    kernel = data.kernelOptions.includes(config.defaultKernel) ? config.defaultKernel : data.kernelOptions[0]!;
    c = data.cGrid.includes(config.defaultC) ? config.defaultC : data.cGrid[0]!;
    gamma = data.gammaGrid.includes(config.defaultGamma) ? config.defaultGamma : data.gammaGrid[0]!;
    datasetControl.select.value = dataset;
    kernelControl.select.value = kernel;
    cControl.select.value = String(c);
    gammaControl.select.value = String(gamma);
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

export const svmExplorerComponent: WidgetComponent<SvmExplorerConfig, SvmExplorerData> = {
  type: "svm-explorer",
  parseData: parseSvmExplorerData,
  mount,
};
