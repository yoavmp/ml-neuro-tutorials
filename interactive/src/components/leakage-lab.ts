// Production activity: Exercise 10's "What happens when the test set leaks
// in?" (WP38). Compares a correct pipeline (preprocessing fit on training
// rows only) against a leaky variant (the same step fit on training+test
// rows together) for scaling, feature selection, and PCA, on real ABIDE-II
// participants predicting age from cortical thickness. The estimator is
// KNeighborsRegressor(n_neighbors=15) in every scenario (WP38R sec 4). Every
// (scenario, sample size, seed) combination's test MSE/R2 is precomputed
// offline; the component only selects, compares, and aggregates -- it never
// refits.
//
// Honesty note (do not "fix" this): unlike ordinary least squares, KNN's
// predictions depend on feature scale, so the scaling scenario's correct and
// leaky numbers are NOT identical in the recomputed artifact -- every entry
// shows a real gap, though it is often small (roughly +/-0.07 R2 across the
// predeclared splits) and its sign is not consistent from split to split.
// The paired and aggregate views below render whatever gap (zero, small, or
// larger) the artifact actually contains exactly like any other value; do
// not assume a particular sign or force one to appear.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { LeakageLabConfig } from "../config";
import {
  entriesForScenarioSize,
  findLeakageLabEntry,
  LEAKAGE_LAB_SCENARIOS,
  parseLeakageLabData,
  type LeakageLabData,
  type LeakageLabScenario,
} from "../leakage-lab-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const SCENARIO_LABELS: Record<LeakageLabScenario, string> = {
  scaling: "Scaling (standardization)",
  feature_selection: "Feature selection",
  pca: "PCA",
};

const DEFAULT_SCENARIO: LeakageLabScenario = "feature_selection";

function sizeLabel(size: number, maxSize: number): string {
  return size === maxSize ? `All eligible participants (n = ${size})` : String(size);
}

function mount(args: MountArgs<LeakageLabConfig, LeakageLabData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const maxSize = Math.max(...data.sampleSizes);
  const sortedSeeds = [...data.seeds].sort((a, b) => a - b);
  const seedSplitLabel = new Map(sortedSeeds.map((s, i) => [s, `Split ${i + 1}`]));

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let scenario: LeakageLabScenario = DEFAULT_SCENARIO;
  let sampleSize = maxSize;
  let seed = sortedSeeds[0]!;

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const scenarioGroup = document.createElement("div");
  scenarioGroup.className = "widget-control";
  const scenarioLabelEl = document.createElement("label");
  scenarioLabelEl.setAttribute("for", "leak-operation");
  scenarioLabelEl.textContent = "Preprocessing operation:";
  const scenarioSelect = document.createElement("select");
  scenarioSelect.id = "leak-operation";
  scenarioSelect.setAttribute("data-testid", "leak-operation-select");
  for (const s of LEAKAGE_LAB_SCENARIOS) {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = SCENARIO_LABELS[s];
    scenarioSelect.appendChild(opt);
  }
  scenarioGroup.append(scenarioLabelEl, scenarioSelect);
  controls.appendChild(scenarioGroup);

  const sizeGroup = document.createElement("div");
  sizeGroup.className = "widget-control";
  const sizeLabelEl = document.createElement("label");
  sizeLabelEl.setAttribute("for", "leak-samplesize");
  sizeLabelEl.textContent = "Sample size:";
  const sizeSelect = document.createElement("select");
  sizeSelect.id = "leak-samplesize";
  sizeSelect.setAttribute("data-testid", "leak-samplesize-select");
  for (const s of [...data.sampleSizes].sort((a, b) => a - b)) {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = sizeLabel(s, maxSize);
    sizeSelect.appendChild(opt);
  }
  sizeGroup.append(sizeLabelEl, sizeSelect);
  controls.appendChild(sizeGroup);

  const seedGroup = document.createElement("div");
  seedGroup.className = "widget-control";
  const seedLabelEl = document.createElement("label");
  seedLabelEl.setAttribute("for", "leak-seed");
  seedLabelEl.textContent = "Predetermined split:";
  const seedSelect = document.createElement("select");
  seedSelect.id = "leak-seed";
  seedSelect.setAttribute("data-testid", "leak-seed-select");
  for (const s of sortedSeeds) {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = seedSplitLabel.get(s)!;
    seedSelect.appendChild(opt);
  }
  seedGroup.append(seedLabelEl, seedSelect);
  controls.appendChild(seedGroup);

  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset";
  resetBtn.setAttribute("data-testid", "leak-reset-button");
  controls.appendChild(resetBtn);

  container.appendChild(controls);

  // --- workflow explanation panels ---------------------------------------
  const workflowGrid = document.createElement("div");
  workflowGrid.className = "widget-workflow-grid";
  const correctPanel = document.createElement("div");
  correctPanel.className = "widget-workflow-panel";
  const correctHeading = document.createElement("h3");
  correctHeading.textContent = "Correct pipeline";
  const correctText = document.createElement("p");
  correctText.setAttribute("data-testid", "leak-workflow-correct");
  correctPanel.append(correctHeading, correctText);

  const leakyPanel = document.createElement("div");
  leakyPanel.className = "widget-workflow-panel";
  const leakyHeading = document.createElement("h3");
  leakyHeading.textContent = "Leaky pipeline";
  const leakyText = document.createElement("p");
  leakyText.setAttribute("data-testid", "leak-workflow-leaky");
  leakyPanel.append(leakyHeading, leakyText);

  workflowGrid.append(correctPanel, leakyPanel);
  container.appendChild(workflowGrid);

  const splitStats = document.createElement("p");
  splitStats.className = "widget-stats";
  splitStats.setAttribute("data-testid", "leak-split-stats");
  container.appendChild(splitStats);

  const resultsRow = document.createElement("div");
  resultsRow.className = "widget-metric-row";
  const correctTile = document.createElement("div");
  correctTile.className = "widget-metric-tile";
  const correctTileLabel = document.createElement("p");
  correctTileLabel.className = "widget-metric-label";
  correctTileLabel.textContent = "Correct pipeline (test set)";
  const correctMetrics = document.createElement("p");
  correctMetrics.className = "widget-metric-secondary";
  correctMetrics.setAttribute("data-testid", "leak-correct-metrics");
  correctTile.append(correctTileLabel, correctMetrics);

  const leakyTile = document.createElement("div");
  leakyTile.className = "widget-metric-tile";
  const leakyTileLabel = document.createElement("p");
  leakyTileLabel.className = "widget-metric-label";
  leakyTileLabel.textContent = "Leaky pipeline (test set)";
  const leakyMetrics = document.createElement("p");
  leakyMetrics.className = "widget-metric-secondary";
  leakyMetrics.setAttribute("data-testid", "leak-leaky-metrics");
  leakyTile.append(leakyTileLabel, leakyMetrics);

  resultsRow.append(correctTile, leakyTile);
  container.appendChild(resultsRow);

  const diffStats = document.createElement("p");
  diffStats.className = "widget-stats";
  diffStats.setAttribute("data-testid", "leak-r2-diff");
  container.appendChild(diffStats);

  const mseDiffStats = document.createElement("p");
  mseDiffStats.className = "widget-stats";
  mseDiffStats.setAttribute("data-testid", "leak-mse-diff");
  container.appendChild(mseDiffStats);

  // --- paired comparison plot for the current selection -------------------
  const pairHeading = document.createElement("h2");
  pairHeading.className = "widget-subhead";
  pairHeading.textContent = "This split: correct vs leaky test R²";
  container.appendChild(pairHeading);

  const pairPlot = document.createElement("div");
  pairPlot.className = "widget-plot";
  pairPlot.setAttribute("data-testid", "leak-pair-plot");
  pairPlot.dataset.renderCount = "0";
  container.appendChild(pairPlot);

  // --- aggregate across all predeclared seeds -----------------------------
  const aggHeading = document.createElement("h2");
  aggHeading.className = "widget-subhead";
  aggHeading.textContent = "Across all 5 predetermined splits";
  container.appendChild(aggHeading);

  const aggCaption = document.createElement("p");
  aggCaption.className = "widget-note";
  aggCaption.setAttribute("data-testid", "leak-aggregate-caption");
  aggCaption.textContent =
    "A leaky evaluation is invalid on every split, whether its score comes out higher, lower, or nearly the same.";
  container.appendChild(aggCaption);

  const aggPlot = document.createElement("div");
  aggPlot.className = "widget-plot";
  aggPlot.setAttribute("data-testid", "leak-aggregate-plot");
  aggPlot.dataset.renderCount = "0";
  container.appendChild(aggPlot);

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

  async function drawPairPlot(): Promise<void> {
    if (destroyed) return;
    const entry = findLeakageLabEntry(data, scenario, sampleSize, seed);
    const correctColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const leakyColor = theme.dark ? "#d98b5f" : "#b5622f";
    const trace = {
      type: "bar" as const,
      x: ["Correct pipeline", "Leaky pipeline"],
      y: [entry.correct.r2, entry.leaky.r2],
      marker: { color: [correctColor, leakyColor] },
      customdata: [entry.correct.mse, entry.leaky.mse],
      hovertemplate: "%{x}<br>R² %{y:.3f}<br>MSE %{customdata:.1f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 300,
      yaxis: { title: { text: "Test R²" } },
    });
    await Plotly.react(pairPlot, [trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    pairPlot.dataset.renderCount = String(Number(pairPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawAggregatePlot(): Promise<void> {
    if (destroyed) return;
    const entries = entriesForScenarioSize(data, scenario, sampleSize);
    const positiveColor = theme.dark ? "#d98b5f" : "#b5622f";
    const negativeColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const diffs = entries.map((e) => e.leaky.r2 - e.correct.r2);
    const trace = {
      type: "bar" as const,
      x: entries.map((e) => seedSplitLabel.get(e.seed) ?? String(e.seed)),
      y: diffs,
      marker: {
        color: diffs.map((d) => (d >= 0 ? positiveColor : negativeColor)),
        line: {
          color: entries.map((e) => (e.seed === seed ? theme.annotationText : "rgba(0,0,0,0)")),
          width: entries.map((e) => (e.seed === seed ? 3 : 0)),
        },
      },
      hovertemplate: "%{x}<br>leaky R² − correct R² = %{y:.3f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 300,
      shapes: [
        {
          type: "line" as const,
          xref: "paper" as const,
          x0: 0,
          x1: 1,
          yref: "y" as const,
          y0: 0,
          y1: 0,
          line: { color: theme.axisColor, width: 1 },
        },
      ],
      yaxis: { title: { text: "Leaky R² − correct R² (0 = no difference)" } },
    });
    await Plotly.react(aggPlot, [trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    aggPlot.dataset.renderCount = String(Number(aggPlot.dataset.renderCount ?? "0") + 1);
  }

  function draw(): void {
    scenarioSelect.value = scenario;
    sizeSelect.value = String(sampleSize);
    seedSelect.value = String(seed);
    container.dataset.currentScenario = scenario;
    container.dataset.currentSampleSize = String(sampleSize);
    container.dataset.currentSeed = String(seed);

    const meta = data.scenarios[scenario];
    correctText.textContent = meta.correctWorkflow;
    leakyText.textContent = meta.leakyWorkflow;

    const entry = findLeakageLabEntry(data, scenario, sampleSize, seed);
    splitStats.textContent =
      `${seedSplitLabel.get(seed)}: n_train = ${entry.nTrain}, n_test = ${entry.nTest}. ` +
      "Both pipelines use the exact same participants and the exact same training/test split.";

    correctMetrics.textContent = `Test MSE = ${entry.correct.mse.toFixed(2)}  ·  Test R² = ${entry.correct.r2.toFixed(3)}`;
    leakyMetrics.textContent = `Test MSE = ${entry.leaky.mse.toFixed(2)}  ·  Test R² = ${entry.leaky.r2.toFixed(3)}`;

    const r2Diff = entry.leaky.r2 - entry.correct.r2;
    const mseDiff = entry.leaky.mse - entry.correct.mse;
    diffStats.textContent = `ΔR² (leaky − correct) = ${r2Diff >= 0 ? "+" : ""}${r2Diff.toFixed(3)}`;
    mseDiffStats.textContent = `ΔMSE (leaky − correct) = ${mseDiff >= 0 ? "+" : ""}${mseDiff.toFixed(2)}`;

    void drawPairPlot();
    void drawAggregatePlot();
  }

  scenarioSelect.addEventListener("change", () => {
    scenario = scenarioSelect.value as LeakageLabScenario;
    draw();
  });
  sizeSelect.addEventListener("change", () => {
    sampleSize = Number(sizeSelect.value);
    draw();
  });
  seedSelect.addEventListener("change", () => {
    seed = Number(seedSelect.value);
    draw();
  });
  resetBtn.addEventListener("click", () => {
    scenario = DEFAULT_SCENARIO;
    sampleSize = maxSize;
    seed = sortedSeeds[0]!;
    draw();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void drawPairPlot();
    void drawAggregatePlot();
  });

  draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(pairPlot);
      Plotly.purge(aggPlot);
    },
  };
}

export const leakageLabComponent: WidgetComponent<LeakageLabConfig, LeakageLabData> = {
  type: "leakage-lab",
  parseData: (raw) => parseLeakageLabData(raw),
  mount,
};
