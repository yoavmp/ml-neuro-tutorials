// Production activity: Exercise 7's "Explore the Boosting Parameters"
// (WP32).
//
// Learning rate, tree depth, and number of trees on the real ABIDE
// development data (dev-split fitting/validation partitions only, n_fit=564
// / n_val=189 -- the locked outer test set is never present in the data
// artifact this component reads). Every (learning_rate, depth, n_trees)
// combination's metrics and validation predictions are precomputed offline
// via sklearn's `staged_predict` (scripts/export_boosting_parameter_widget.py);
// nothing is fit live in the browser. Play advances through the committed
// tree-count grid at the current learning rate/depth; Pause and Reset stop
// it, and the interval timer is always cleared on unmount.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { BoostingParameterExplorerConfig } from "../config";
import {
  parseBoostingParameterExplorerData,
  type BoostingParameterExplorerData,
} from "../boosting-parameter-explorer-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function sharedAxisRange(values: number[], padFrac: number): [number, number] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * padFrac || 1;
  return [min - pad, max + pad];
}

function prefersReducedMotion(): boolean {
  try {
    return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

function mount(
  args: MountArgs<BoostingParameterExplorerConfig, BoostingParameterExplorerData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  const lrGrid = data.learningRateGrid;
  const depthGrid = data.depthGrid;
  const nTreesGrid = data.nTreesGrid;

  let learningRate = lrGrid.includes(config.defaultLearningRate) ? config.defaultLearningRate : lrGrid[0]!;
  let depth = depthGrid.includes(config.defaultDepth) ? config.defaultDepth : depthGrid[0]!;
  let nTreesIndex = nTreesGrid.includes(config.defaultNTrees) ? nTreesGrid.indexOf(config.defaultNTrees) : 0;
  let playing = false;
  let intervalHandle: number | undefined;

  const scatterAxisRange = sharedAxisRange(data.observedValidation, 0.05);

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const testNote = document.createElement("p");
  testNote.className = "widget-note";
  testNote.setAttribute("data-testid", "boosting-param-test-note");
  testNote.textContent = config.testSetNote;
  container.appendChild(testNote);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "boosting-param-cohort");
  cohortLine.textContent =
    `Development data only: ${data.split.devSplit.nFit}-participant fitting set, ` +
    `${data.split.devSplit.nVal}-participant validation set. Feature recipe: ` +
    `${data.featureRecipe.featureCount} cortical-thickness features, the same as Exercises 2, 4, 5, and 6.`;
  container.appendChild(cohortLine);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const lrGroup = document.createElement("div");
  lrGroup.className = "widget-control";
  const lrLabel = document.createElement("label");
  lrLabel.setAttribute("for", "boosting-param-lr");
  lrLabel.textContent = "Learning rate:";
  const lrSelect = document.createElement("select");
  lrSelect.id = "boosting-param-lr";
  lrSelect.setAttribute("data-testid", "boosting-param-lr-select");
  for (const lr of lrGrid) {
    const opt = document.createElement("option");
    opt.value = String(lr);
    opt.textContent = String(lr);
    lrSelect.appendChild(opt);
  }
  lrGroup.append(lrLabel, lrSelect);
  controls.appendChild(lrGroup);

  const depthGroup = document.createElement("div");
  depthGroup.className = "widget-control";
  const depthLabel = document.createElement("label");
  depthLabel.setAttribute("for", "boosting-param-depth");
  depthLabel.textContent = "Tree depth:";
  const depthSelect = document.createElement("select");
  depthSelect.id = "boosting-param-depth";
  depthSelect.setAttribute("data-testid", "boosting-param-depth-select");
  for (const d of depthGrid) {
    const opt = document.createElement("option");
    opt.value = String(d);
    opt.textContent = String(d);
    depthSelect.appendChild(opt);
  }
  depthGroup.append(depthLabel, depthSelect);
  controls.appendChild(depthGroup);

  const nTreesGroup = document.createElement("div");
  nTreesGroup.className = "widget-control";
  const nTreesLabel = document.createElement("label");
  nTreesLabel.setAttribute("for", "boosting-param-ntrees");
  nTreesLabel.textContent = "Number of trees:";
  const nTreesSlider = document.createElement("input");
  nTreesSlider.id = "boosting-param-ntrees";
  nTreesSlider.type = "range";
  nTreesSlider.min = "0";
  nTreesSlider.max = String(nTreesGrid.length - 1);
  nTreesSlider.step = "1";
  nTreesSlider.setAttribute("data-testid", "boosting-param-ntrees-slider");
  nTreesSlider.setAttribute(
    "aria-label",
    `Number of trees, from ${nTreesGrid[0]} to ${nTreesGrid[nTreesGrid.length - 1]}`,
  );
  const nTreesValue = document.createElement("output");
  nTreesValue.setAttribute("for", "boosting-param-ntrees");
  nTreesValue.setAttribute("data-testid", "boosting-param-ntrees-value");
  nTreesValue.className = "widget-bin-value";
  nTreesGroup.append(nTreesLabel, nTreesSlider, nTreesValue);
  controls.appendChild(nTreesGroup);
  container.appendChild(controls);

  const buttonRow = document.createElement("div");
  buttonRow.className = "widget-controls";

  const playButton = document.createElement("button");
  playButton.type = "button";
  playButton.setAttribute("data-testid", "boosting-param-play-button");

  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.textContent = "Reset";
  resetButton.setAttribute("data-testid", "boosting-param-reset-button");

  buttonRow.append(playButton, resetButton);
  container.appendChild(buttonRow);

  const metrics = document.createElement("p");
  metrics.className = "widget-stats";
  metrics.setAttribute("data-testid", "boosting-param-metrics");
  metrics.setAttribute("role", "status");
  metrics.setAttribute("aria-live", "polite");
  container.appendChild(metrics);

  // --- panels ---------------------------------------------------------
  const p1Heading = document.createElement("h2");
  p1Heading.className = "widget-subhead";
  p1Heading.textContent = "Training and validation MSE versus number of trees";
  container.appendChild(p1Heading);

  const msePlot = document.createElement("div");
  msePlot.className = "widget-plot";
  msePlot.setAttribute("data-testid", "boosting-param-mse-plot");
  msePlot.dataset.renderCount = "0";
  container.appendChild(msePlot);

  const p2Heading = document.createElement("h2");
  p2Heading.className = "widget-subhead";
  p2Heading.textContent = "Validation MSE across learning rate and number of trees";
  container.appendChild(p2Heading);

  const heatmapPlot = document.createElement("div");
  heatmapPlot.className = "widget-plot";
  heatmapPlot.setAttribute("data-testid", "boosting-param-heatmap-plot");
  heatmapPlot.dataset.renderCount = "0";
  container.appendChild(heatmapPlot);

  const p3Heading = document.createElement("h2");
  p3Heading.className = "widget-subhead";
  p3Heading.textContent = "Observed versus predicted validation age";
  container.appendChild(p3Heading);

  const predictionPlot = document.createElement("div");
  predictionPlot.className = "widget-plot";
  predictionPlot.setAttribute("data-testid", "boosting-param-prediction-plot");
  predictionPlot.dataset.renderCount = "0";
  container.appendChild(predictionPlot);

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
    return data.grid[`${learningRate}|${depth}`]!;
  }

  function currentNTrees(): number {
    return nTreesGrid[nTreesIndex]!;
  }

  function currentPoint() {
    return currentEntry().byNTrees[String(currentNTrees())]!;
  }

  // --- drawing ---------------------------------------------------------

  async function drawMsePlot(): Promise<void> {
    if (destroyed) return;
    const entry = currentEntry();
    const trainSeries = nTreesGrid.map((n) => entry.byNTrees[String(n)]!.trainMSE);
    const valSeries = nTreesGrid.map((n) => entry.byNTrees[String(n)]!.valMSE);
    const trainTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Training MSE",
      x: nTreesGrid,
      y: trainSeries,
      line: { color: theme.axisColor },
      marker: { color: theme.axisColor },
      hovertemplate: "n_trees=%{x}<br>training MSE %{y:.2f}<extra></extra>",
    };
    const valTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Validation MSE",
      x: nTreesGrid,
      y: valSeries,
      line: { color: theme.diagonalLine },
      marker: { color: theme.diagonalLine },
      hovertemplate: "n_trees=%{x}<br>validation MSE %{y:.2f}<extra></extra>",
    };
    const maxY = Math.max(...trainSeries, ...valSeries);
    const marker = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: "Selected number of trees",
      x: [currentNTrees(), currentNTrees()],
      y: [0, maxY],
      line: { color: theme.markerPrimary, width: 2, dash: "dash" as const },
      hoverinfo: "skip" as const,
      showlegend: false,
    };
    const layout = buildPlotLayout(theme, {
      height: 300,
      showlegend: true,
      xaxis: { title: { text: "Number of trees" }, type: "log" as const },
      yaxis: { title: { text: "MSE (years²)" } },
    });
    await Plotly.react(msePlot, [trainTrace, valTrace, marker], layout, PLOT_CONFIG);
    if (destroyed) return;
    msePlot.dataset.renderCount = String(Number(msePlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawHeatmap(): Promise<void> {
    if (destroyed) return;
    const xCats = nTreesGrid.map(String);
    const yCats = lrGrid.map(String);
    const z = lrGrid.map((lr) => nTreesGrid.map((n) => data.grid[`${lr}|${depth}`]!.byNTrees[String(n)]!.valMSE));
    const heatmap = {
      type: "heatmap" as const,
      x: xCats,
      y: yCats,
      z,
      colorscale: "Viridis" as const,
      reversescale: true,
      colorbar: { title: { text: "validation MSE" }, thickness: 12 },
      hovertemplate: "learning rate=%{y}<br>n_trees=%{x}<br>validation MSE %{z:.2f}<extra></extra>",
    };
    const selection = {
      type: "scatter" as const,
      mode: "markers" as const,
      x: [String(currentNTrees())],
      y: [String(learningRate)],
      marker: { symbol: "square-open" as const, size: 22, color: theme.diagonalLine, line: { width: 3 } },
      hoverinfo: "skip" as const,
      showlegend: false,
    };
    const layout = buildPlotLayout(theme, {
      height: 320,
      xaxis: { title: { text: "Number of trees" }, type: "category" as const },
      yaxis: { title: { text: "Learning rate" }, type: "category" as const },
    });
    await Plotly.react(heatmapPlot, [heatmap, selection], layout, PLOT_CONFIG);
    if (destroyed) return;
    heatmapPlot.dataset.renderCount = String(Number(heatmapPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawPrediction(): Promise<void> {
    if (destroyed) return;
    const point = currentPoint();
    const scatter = {
      type: "scattergl" as const,
      mode: "markers" as const,
      x: data.observedValidation,
      y: point.predictedValidation,
      marker: { color: theme.markerPrimary, size: 6 },
      hovertemplate: `observed ${data.target.label} %{x}<br>predicted %{y:.1f}<extra></extra>`,
      showlegend: false,
    };
    const diag = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: scatterAxisRange,
      y: scatterAxisRange,
      line: { color: theme.diagonalLine, width: 2, dash: "dash" as const },
      hoverinfo: "skip" as const,
      name: "Perfect prediction (observed = predicted)",
      showlegend: true,
    };
    const layout = buildPlotLayout(theme, {
      height: 340,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.12 },
      xaxis: { title: { text: `Observed ${data.target.label}` }, range: [...scatterAxisRange] },
      yaxis: {
        title: { text: `Predicted ${data.target.label} (validation)` },
        range: [...scatterAxisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    });
    await Plotly.react(predictionPlot, [scatter, diag], layout, PLOT_CONFIG);
    if (destroyed) return;
    predictionPlot.dataset.renderCount = String(Number(predictionPlot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const point = currentPoint();
    nTreesValue.textContent = String(currentNTrees());
    metrics.textContent =
      `learning rate = ${learningRate}  ·  depth = ${depth}  ·  trees = ${currentNTrees()}  ·  ` +
      `training MSE = ${point.trainMSE.toFixed(1)}  ·  validation MSE = ${point.valMSE.toFixed(1)} ` +
      `(lower is better)  ·  validation R² = ${point.valR2.toFixed(3)}.`;
    container.dataset.learningRate = String(learningRate);
    container.dataset.depth = String(depth);
    container.dataset.nTrees = String(currentNTrees());
    container.dataset.valMse = point.valMSE.toFixed(4);
    container.dataset.playing = String(playing);
    playButton.textContent = playing ? "Pause" : "Play";
    playButton.setAttribute("aria-pressed", String(playing));
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    nTreesSlider.value = String(nTreesIndex);
    drawText();
    await Promise.all([drawMsePlot(), drawHeatmap(), drawPrediction()]);
  }

  // --- Play/Pause lifecycle ---------------------------------------------

  function stopPlaying(): void {
    playing = false;
    if (intervalHandle !== undefined) {
      window.clearInterval(intervalHandle);
      intervalHandle = undefined;
    }
    drawText();
  }

  function startPlaying(): void {
    if (playing || destroyed) return;
    if (nTreesIndex >= nTreesGrid.length - 1) {
      nTreesIndex = 0;
    }
    playing = true;
    drawText();
    const intervalMs = prefersReducedMotion() ? config.playIntervalMs * 3 : config.playIntervalMs;
    intervalHandle = window.setInterval(() => {
      if (destroyed) return;
      if (nTreesIndex >= nTreesGrid.length - 1) {
        stopPlaying();
        return;
      }
      nTreesIndex += 1;
      void draw();
      if (nTreesIndex >= nTreesGrid.length - 1) {
        stopPlaying();
      }
    }, intervalMs);
  }

  function pauseOrStopForControlChange(): void {
    if (playing) stopPlaying();
  }

  lrSelect.value = String(learningRate);
  depthSelect.value = String(depth);
  nTreesSlider.value = String(nTreesIndex);

  lrSelect.addEventListener("change", () => {
    pauseOrStopForControlChange();
    learningRate = Number(lrSelect.value);
    void draw();
  });
  depthSelect.addEventListener("change", () => {
    pauseOrStopForControlChange();
    depth = Number(depthSelect.value);
    void draw();
  });
  nTreesSlider.addEventListener("input", () => {
    pauseOrStopForControlChange();
    nTreesIndex = Number(nTreesSlider.value);
    void draw();
  });

  playButton.addEventListener("click", () => {
    if (playing) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

  resetButton.addEventListener("click", () => {
    stopPlaying();
    learningRate = lrGrid.includes(config.defaultLearningRate) ? config.defaultLearningRate : lrGrid[0]!;
    depth = depthGrid.includes(config.defaultDepth) ? config.defaultDepth : depthGrid[0]!;
    nTreesIndex = nTreesGrid.includes(config.defaultNTrees) ? nTreesGrid.indexOf(config.defaultNTrees) : 0;
    lrSelect.value = String(learningRate);
    depthSelect.value = String(depth);
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
      stopPlaying();
      unsubscribeTheme();
      Plotly.purge(msePlot);
      Plotly.purge(heatmapPlot);
      Plotly.purge(predictionPlot);
    },
  };
}

export const boostingParameterExplorerComponent: WidgetComponent<
  BoostingParameterExplorerConfig,
  BoostingParameterExplorerData
> = {
  type: "boosting-parameter-explorer",
  parseData: parseBoostingParameterExplorerData,
  mount,
};
