// Production activity: Exercise 6's "One Tree or Many?" (WP29).
//
// Compares a single regression tree, bagging, and a Random Forest across
// five deterministic training replicates (each a fixed proportion of the
// dev-split fitting partition, drawn without replacement at a predefined
// seed -- not merely a different random_state on identical data) and a
// grid of ensemble sizes, all scored on one fixed validation set. Every
// (replicate, model, n_trees) prediction is precomputed offline
// (scripts/export_tree_ensemble_widget.py); nothing is fit in the browser.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { TreeEnsembleCompareConfig, TreeEnsembleCompareHighlight } from "../config";
import {
  parseTreeEnsembleCompareData,
  type TreeEnsembleCompareData,
  type TreeEnsembleModelPoint,
} from "../tree-ensemble-compare-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const MODEL_LABELS: Record<TreeEnsembleCompareHighlight, string> = {
  "single-tree": "Single tree",
  bagging: "Bagging",
  "random-forest": "Random Forest",
};

function sharedAxisRange(values: number[], padFrac: number): [number, number] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * padFrac || 1;
  return [min - pad, max + pad];
}

function mount(args: MountArgs<TreeEnsembleCompareConfig, TreeEnsembleCompareData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  const seeds = data.replicates.map((r) => r.seed);
  let replicateSeed = seeds.includes(config.defaultReplicateSeed) ? config.defaultReplicateSeed : seeds[0]!;
  let nTrees = data.nTreesGrid.includes(config.defaultNTrees) ? config.defaultNTrees : data.nTreesGrid[0]!;
  let highlightModel: TreeEnsembleCompareHighlight = config.defaultHighlightModel;

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

  const rfNote = document.createElement("p");
  rfNote.className = "widget-note";
  rfNote.setAttribute("data-testid", "tree-ensemble-rf-note");
  rfNote.textContent = config.randomForestNote;
  container.appendChild(rfNote);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "tree-ensemble-cohort");
  cohortLine.textContent =
    `Each training replicate draws ${Math.round(data.settings.replicateFraction * 100)}% of the ` +
    `${data.settings.replicatePoolSize}-participant fitting pool without replacement. Fixed validation set: ` +
    `${data.split.devSplit.nVal} participants, identical across every replicate and model. Feature recipe: ` +
    `${data.featureRecipe.featureCount} cortical-thickness features, the same as Exercises 2, 4, and 5.`;
  container.appendChild(cohortLine);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const replicateGroup = document.createElement("div");
  replicateGroup.className = "widget-control";
  const replicateLabel = document.createElement("label");
  replicateLabel.setAttribute("for", "tree-ensemble-replicate");
  replicateLabel.textContent = "Training replicate:";
  const replicateSelect = document.createElement("select");
  replicateSelect.id = "tree-ensemble-replicate";
  replicateSelect.setAttribute("data-testid", "tree-ensemble-replicate-select");
  seeds.forEach((s, i) => {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = `Replicate ${i + 1} (seed ${s})`;
    replicateSelect.appendChild(opt);
  });
  replicateGroup.append(replicateLabel, replicateSelect);
  controls.appendChild(replicateGroup);

  const nTreesGroup = document.createElement("div");
  nTreesGroup.className = "widget-control";
  const nTreesLabel = document.createElement("label");
  nTreesLabel.setAttribute("for", "tree-ensemble-ntrees");
  nTreesLabel.textContent = "Number of trees (bagging / Random Forest):";
  const nTreesSelect = document.createElement("select");
  nTreesSelect.id = "tree-ensemble-ntrees";
  nTreesSelect.setAttribute("data-testid", "tree-ensemble-ntrees-select");
  for (const n of data.nTreesGrid) {
    const opt = document.createElement("option");
    opt.value = String(n);
    opt.textContent = String(n);
    nTreesSelect.appendChild(opt);
  }
  nTreesGroup.append(nTreesLabel, nTreesSelect);
  controls.appendChild(nTreesGroup);

  const modelGroup = document.createElement("div");
  modelGroup.className = "widget-control";
  const modelLabel = document.createElement("label");
  modelLabel.setAttribute("for", "tree-ensemble-model");
  modelLabel.textContent = "Highlighted model (prediction panel):";
  const modelSelect = document.createElement("select");
  modelSelect.id = "tree-ensemble-model";
  modelSelect.setAttribute("data-testid", "tree-ensemble-model-select");
  (["single-tree", "bagging", "random-forest"] as const).forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = MODEL_LABELS[m];
    modelSelect.appendChild(opt);
  });
  modelGroup.append(modelLabel, modelSelect);
  controls.appendChild(modelGroup);
  container.appendChild(controls);

  // --- panel 1 ---------------------------------------------------------
  const p1Heading = document.createElement("h2");
  p1Heading.className = "widget-subhead";
  p1Heading.textContent = "Performance across training replicates";
  container.appendChild(p1Heading);

  const distPlot = document.createElement("div");
  distPlot.className = "widget-plot";
  distPlot.setAttribute("data-testid", "tree-ensemble-distribution-plot");
  distPlot.dataset.renderCount = "0";
  container.appendChild(distPlot);

  // --- panel 2 ---------------------------------------------------------
  const p2Heading = document.createElement("h2");
  p2Heading.className = "widget-subhead";
  p2Heading.textContent = "Effect of ensemble size";
  container.appendChild(p2Heading);

  const sizePlot = document.createElement("div");
  sizePlot.className = "widget-plot";
  sizePlot.setAttribute("data-testid", "tree-ensemble-size-plot");
  sizePlot.dataset.renderCount = "0";
  container.appendChild(sizePlot);

  // --- panel 3 ---------------------------------------------------------
  const p3Heading = document.createElement("h2");
  p3Heading.className = "widget-subhead";
  p3Heading.textContent = "Observed vs predicted age (selected replicate and model)";
  container.appendChild(p3Heading);

  const predictionMetrics = document.createElement("p");
  predictionMetrics.className = "widget-stats";
  predictionMetrics.setAttribute("data-testid", "tree-ensemble-prediction-metrics");
  container.appendChild(predictionMetrics);

  const predictionPlot = document.createElement("div");
  predictionPlot.className = "widget-plot";
  predictionPlot.setAttribute("data-testid", "tree-ensemble-prediction-plot");
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

  function currentReplicate() {
    return data.replicates.find((r) => r.seed === replicateSeed)!;
  }

  function pointFor(model: TreeEnsembleCompareHighlight, n: number): TreeEnsembleModelPoint {
    const r = currentReplicate();
    if (model === "single-tree") return r.singleTree;
    if (model === "bagging") return r.bagging.byNTrees[String(n)]!;
    return r.randomForest.byNTrees[String(n)]!;
  }

  // --- drawing ---------------------------------------------------------

  async function drawDistribution(): Promise<void> {
    if (destroyed) return;
    const singleValues = data.replicates.map((r) => r.singleTree.valMSE);
    const bagValues = data.replicates.map((r) => r.bagging.byNTrees[String(nTrees)]!.valMSE);
    const rfValues = data.replicates.map((r) => r.randomForest.byNTrees[String(nTrees)]!.valMSE);

    const traces = [
      { name: "Single tree", values: singleValues, color: theme.axisColor },
      { name: "Bagging", values: bagValues, color: theme.markerPrimary },
      { name: "Random Forest", values: rfValues, color: theme.diagonalLine },
    ].map((t) => ({
      type: "box" as const,
      name: t.name,
      y: t.values,
      boxpoints: "all" as const,
      jitter: 0.4,
      pointpos: 0,
      marker: { color: t.color },
      line: { color: t.color },
      hovertemplate: `${t.name}<br>validation MSE %{y:.2f}<extra></extra>`,
    }));

    const layout = buildPlotLayout(theme, {
      height: 320,
      yaxis: { title: { text: `Validation MSE across ${data.replicates.length} replicates (lower is better)` } },
    });
    await Plotly.react(distPlot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(distPlot.dataset.renderCount ?? "0") + 1;
    distPlot.dataset.renderCount = String(n);
  }

  async function drawSizeCurve(): Promise<void> {
    if (destroyed) return;
    const grid = data.nTreesGrid;
    const bagMean = grid.map((n) => data.summary.bagging[String(n)]!.meanMSE);
    const bagSd = grid.map((n) => data.summary.bagging[String(n)]!.sdMSE);
    const rfMean = grid.map((n) => data.summary.randomForest[String(n)]!.meanMSE);
    const rfSd = grid.map((n) => data.summary.randomForest[String(n)]!.sdMSE);
    const singleMean = data.summary.singleTree.meanMSE;

    const bagTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Bagging",
      x: grid,
      y: bagMean,
      error_y: { type: "data" as const, array: bagSd, visible: true },
      line: { color: theme.markerPrimary },
      marker: { color: theme.markerPrimary },
      hovertemplate: "n_trees=%{x}<br>mean MSE %{y:.2f}<extra>Bagging</extra>",
    };
    const rfTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Random Forest",
      x: grid,
      y: rfMean,
      error_y: { type: "data" as const, array: rfSd, visible: true },
      line: { color: theme.diagonalLine },
      marker: { color: theme.diagonalLine },
      hovertemplate: "n_trees=%{x}<br>mean MSE %{y:.2f}<extra>Random Forest</extra>",
    };
    const singleTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: "Single tree (reference)",
      x: [grid[0], grid[grid.length - 1]],
      y: [singleMean, singleMean],
      line: { color: theme.axisColor, dash: "dash" as const },
      hoverinfo: "skip" as const,
    };

    const layout = buildPlotLayout(theme, {
      height: 320,
      showlegend: true,
      xaxis: { title: { text: "Number of trees" }, type: "log" as const },
      yaxis: { title: { text: "Mean validation MSE across replicates (lower is better)" } },
    });
    await Plotly.react(sizePlot, [singleTrace, bagTrace, rfTrace], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(sizePlot.dataset.renderCount ?? "0") + 1;
    sizePlot.dataset.renderCount = String(n);
  }

  async function drawPrediction(): Promise<void> {
    if (destroyed) return;
    const point = pointFor(highlightModel, nTrees);
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
    const n = Number(predictionPlot.dataset.renderCount ?? "0") + 1;
    predictionPlot.dataset.renderCount = String(n);
  }

  function drawMetrics(): void {
    const point = pointFor(highlightModel, nTrees);
    const nTreesText = highlightModel === "single-tree" ? "not applicable (one tree)" : String(nTrees);
    const maxFeaturesText =
      highlightModel === "random-forest"
        ? `  ·  Random Forest feature-subset size = ${data.settings.randomForestMaxFeatures} of ${data.featureRecipe.featureCount}`
        : "";
    predictionMetrics.textContent =
      `${MODEL_LABELS[highlightModel]}  ·  trees = ${nTreesText}  ·  validation MSE = ${point.valMSE.toFixed(1)} ` +
      `(lower is better)  ·  validation R² = ${point.valR2.toFixed(3)}${maxFeaturesText}.`;
    container.dataset.highlightModel = highlightModel;
    container.dataset.valMse = point.valMSE.toFixed(4);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    nTreesSelect.disabled = highlightModel === "single-tree";
    drawMetrics();
    await Promise.all([drawDistribution(), drawSizeCurve(), drawPrediction()]);
  }

  replicateSelect.value = String(replicateSeed);
  nTreesSelect.value = String(nTrees);
  modelSelect.value = highlightModel;

  replicateSelect.addEventListener("change", () => {
    replicateSeed = Number(replicateSelect.value);
    void draw();
  });
  nTreesSelect.addEventListener("change", () => {
    nTrees = Number(nTreesSelect.value);
    void draw();
  });
  modelSelect.addEventListener("change", () => {
    highlightModel = modelSelect.value as TreeEnsembleCompareHighlight;
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
      Plotly.purge(distPlot);
      Plotly.purge(sizePlot);
      Plotly.purge(predictionPlot);
    },
  };
}

export const treeEnsembleCompareComponent: WidgetComponent<TreeEnsembleCompareConfig, TreeEnsembleCompareData> = {
  type: "tree-ensemble-compare",
  parseData: parseTreeEnsembleCompareData,
  mount,
};
