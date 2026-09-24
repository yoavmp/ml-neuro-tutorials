// Production activity: Exercise 10's "Random windows or new participants?"
// (WP38). Compares ordinary random-window 5-fold cross-validation against
// participant-grouped 5-fold cross-validation for K-nearest-neighbours
// activity classification on the public UCI HAR dataset. Every k's per-fold
// accuracy, macro-F1, and confusion matrix -- for both splitting methods --
// is precomputed offline; the browser only selects and displays. The
// participant/fold assignment diagram is the single most important visual
// here: under ordinary splitting a participant's windows visibly spread
// across every fold color; under grouped splitting each participant shows
// exactly one fold color.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { HarFoldCompareConfig } from "../config";
import {
  findKResult,
  parseHarFoldCompareData,
  participantsSplitAcrossFold,
  sortedActivityIds,
  type HarFoldCompareData,
  type HarSplitMethod,
} from "../har-fold-compare-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const FOLD_COLORS = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#af7aa1", "#76b7b2"];

const METHOD_LABELS: Record<HarSplitMethod, string> = {
  ordinary: "Ordinary (random windows)",
  grouped: "Participant-grouped",
};

function mount(args: MountArgs<HarFoldCompareConfig, HarFoldCompareData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const activityIds = sortedActivityIds(data);
  const activityNames = activityIds.map((id) => data.activityLabels[String(id)]!);
  const foldLabels = Array.from({ length: data.nSplits }, (_, i) => `Fold ${i + 1}`);
  const defaultK = data.kValues[Math.floor(data.kValues.length / 2)]!;

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let method: HarSplitMethod = "ordinary";
  let k = defaultK;
  let fold = 0;

  // --- header -----------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const overlapCaption = document.createElement("p");
  overlapCaption.className = "widget-note";
  overlapCaption.setAttribute("data-testid", "har-overlap-caption");
  overlapCaption.textContent =
    "Each window overlaps only its immediate neighbour by 50% of its length -- not every pair of windows in the dataset overlaps this way.";
  container.appendChild(overlapCaption);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.textContent =
    `${data.nRows.toLocaleString()} sensor windows from ${data.nParticipants} participants ` +
    `(about ${Math.round(data.observationsPerParticipant.mean)} windows per participant).`;
  container.appendChild(cohortLine);

  // --- controls -----------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const methodGroup = document.createElement("div");
  methodGroup.className = "widget-control";
  const methodLabelEl = document.createElement("span");
  methodLabelEl.id = "har-method-label";
  methodLabelEl.textContent = "Splitting method:";
  const methodTabs = document.createElement("div");
  methodTabs.className = "widget-tabs";
  methodTabs.setAttribute("role", "tablist");
  methodTabs.setAttribute("aria-labelledby", "har-method-label");
  const methodButtons = new Map<HarSplitMethod, HTMLButtonElement>();
  for (const m of ["ordinary", "grouped"] as const) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = METHOD_LABELS[m];
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `har-method-${m}`);
    btn.setAttribute("aria-selected", String(m === method));
    methodTabs.appendChild(btn);
    methodButtons.set(m, btn);
  }
  methodGroup.append(methodLabelEl, methodTabs);
  controls.appendChild(methodGroup);

  const kGroup = document.createElement("div");
  kGroup.className = "widget-control";
  const kLabelEl = document.createElement("span");
  kLabelEl.id = "har-k-label";
  kLabelEl.textContent = "Number of neighbours (k):";
  const kTabs = document.createElement("div");
  kTabs.className = "widget-tabs";
  kTabs.setAttribute("role", "tablist");
  kTabs.setAttribute("aria-labelledby", "har-k-label");
  const kButtons = new Map<number, HTMLButtonElement>();
  for (const kv of data.kValues) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(kv);
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `har-k-${kv}`);
    btn.setAttribute("aria-selected", String(kv === k));
    kTabs.appendChild(btn);
    kButtons.set(kv, btn);
  }
  kGroup.append(kLabelEl, kTabs);
  controls.appendChild(kGroup);

  const foldGroup = document.createElement("div");
  foldGroup.className = "widget-control";
  const foldLabelEl = document.createElement("span");
  foldLabelEl.id = "har-fold-label";
  foldLabelEl.textContent = "Fold:";
  const foldTabs = document.createElement("div");
  foldTabs.className = "widget-tabs";
  foldTabs.setAttribute("role", "tablist");
  foldTabs.setAttribute("aria-labelledby", "har-fold-label");
  const foldButtons = new Map<number, HTMLButtonElement>();
  for (let f = 0; f < data.nSplits; f += 1) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = foldLabels[f]!;
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `har-fold-${f}`);
    btn.setAttribute("aria-selected", String(f === fold));
    foldTabs.appendChild(btn);
    foldButtons.set(f, btn);
  }
  foldGroup.append(foldLabelEl, foldTabs);
  controls.appendChild(foldGroup);

  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset";
  resetBtn.setAttribute("data-testid", "har-reset-button");
  controls.appendChild(resetBtn);

  container.appendChild(controls);

  // --- participant / fold assignment diagram ------------------------------
  const diagramHeading = document.createElement("h2");
  diagramHeading.className = "widget-subhead";
  diagramHeading.textContent = "Which fold does each participant land in?";
  container.appendChild(diagramHeading);

  const legend = document.createElement("p");
  legend.className = "widget-fold-legend";
  for (let f = 0; f < data.nSplits; f += 1) {
    const item = document.createElement("span");
    const swatch = document.createElement("span");
    swatch.className = "widget-fold-legend-swatch";
    swatch.style.background = FOLD_COLORS[f % FOLD_COLORS.length]!;
    item.append(swatch, document.createTextNode(foldLabels[f]!));
    legend.appendChild(item);
  }
  container.appendChild(legend);

  const participantGrid = document.createElement("div");
  participantGrid.className = "widget-participant-grid";
  participantGrid.setAttribute("data-testid", "har-participant-grid");
  container.appendChild(participantGrid);

  const splitStat = document.createElement("p");
  splitStat.className = "widget-stats";
  splitStat.setAttribute("data-testid", "har-split-stat");
  container.appendChild(splitStat);

  // --- selected-fold metrics ----------------------------------------------
  const foldMetricsLine = document.createElement("p");
  foldMetricsLine.className = "widget-stats";
  foldMetricsLine.setAttribute("data-testid", "har-fold-metrics");
  container.appendChild(foldMetricsLine);

  const cmHeading = document.createElement("h2");
  cmHeading.className = "widget-subhead";
  cmHeading.textContent = "Confusion matrix for the selected fold";
  container.appendChild(cmHeading);

  const confusionPlot = document.createElement("div");
  confusionPlot.className = "widget-plot";
  confusionPlot.setAttribute("data-testid", "har-confusion-plot");
  confusionPlot.dataset.renderCount = "0";
  container.appendChild(confusionPlot);

  const summaryHeading = document.createElement("h2");
  summaryHeading.className = "widget-subhead";
  summaryHeading.textContent = "Accuracy and macro-F1 across all folds";
  container.appendChild(summaryHeading);

  const summaryPlot = document.createElement("div");
  summaryPlot.className = "widget-plot";
  summaryPlot.setAttribute("data-testid", "har-summary-plot");
  summaryPlot.dataset.renderCount = "0";
  container.appendChild(summaryPlot);

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

  function drawParticipantGrid(): void {
    participantGrid.replaceChildren();
    for (const p of data.participantFolds) {
      const tile = document.createElement("div");
      tile.className = "widget-participant-tile";
      tile.setAttribute("data-testid", `har-participant-${p.participantId}`);

      const folds = method === "ordinary" ? [...p.ordinaryFolds].sort((a, b) => a - b) : [p.groupedFold];
      const inSelectedFold = folds.includes(fold);
      if (inSelectedFold) tile.classList.add("is-in-selected-fold");

      for (const f of folds) {
        const seg = document.createElement("span");
        seg.className = "widget-participant-tile-segment";
        seg.style.background = FOLD_COLORS[f % FOLD_COLORS.length]!;
        tile.appendChild(seg);
      }

      const sr = document.createElement("span");
      sr.className = "widget-visually-hidden";
      sr.textContent =
        method === "ordinary"
          ? `Participant ${p.participantId}: windows appear in ${folds.map((f) => `Fold ${f + 1}`).join(", ")}.`
          : `Participant ${p.participantId}: Fold ${p.groupedFold + 1}.`;
      tile.appendChild(sr);

      participantGrid.appendChild(tile);
    }
  }

  async function drawConfusionPlot(): Promise<void> {
    if (destroyed) return;
    const result = findKResult(data, k);
    const matrix = result[method].confusionPerFold[fold]!;
    const heatmap = {
      type: "heatmap" as const,
      x: activityNames,
      y: activityNames,
      z: matrix,
      colorscale: "Viridis" as const,
      colorbar: { title: { text: "count" }, thickness: 12 },
      hovertemplate: "actual %{y}<br>predicted %{x}<br>count %{z}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 420,
      margin: { b: 90, l: 110 },
      xaxis: { title: { text: "Predicted activity" }, tickangle: -35, type: "category" as const },
      yaxis: {
        title: { text: "Actual activity" },
        type: "category" as const,
        autorange: "reversed" as const,
      },
    });
    await Plotly.react(confusionPlot, [heatmap], layout, PLOT_CONFIG);
    if (destroyed) return;
    confusionPlot.dataset.renderCount = String(Number(confusionPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawSummaryPlot(): Promise<void> {
    if (destroyed) return;
    const result = findKResult(data, k);
    const metrics = result[method];
    const accColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const f1Color = theme.dark ? "#d9a441" : "#b5760a";
    const highlightColor = theme.annotationText;
    const lineWidths = foldLabels.map((_, f) => (f === fold ? 3 : 0));
    const lineColors = foldLabels.map((_, f) => (f === fold ? highlightColor : "rgba(0,0,0,0)"));
    const accTrace = {
      type: "bar" as const,
      x: foldLabels,
      y: metrics.accPerFold,
      name: "Accuracy",
      marker: { color: accColor, line: { color: lineColors, width: lineWidths } },
      hovertemplate: "%{x}<br>accuracy %{y:.3f}<extra></extra>",
    };
    const f1Trace = {
      type: "bar" as const,
      x: foldLabels,
      y: metrics.f1PerFold,
      name: "Macro-F1",
      marker: { color: f1Color, line: { color: lineColors, width: lineWidths } },
      hovertemplate: "%{x}<br>macro-F1 %{y:.3f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 300,
      showlegend: true,
      yaxis: { title: { text: "Score (0-1)" }, range: [0, 1] },
    });
    await Plotly.react(summaryPlot, [accTrace, f1Trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    summaryPlot.dataset.renderCount = String(Number(summaryPlot.dataset.renderCount ?? "0") + 1);
  }

  function draw(): void {
    for (const [m, btn] of methodButtons) btn.setAttribute("aria-selected", String(m === method));
    for (const [kv, btn] of kButtons) btn.setAttribute("aria-selected", String(kv === k));
    for (const [f, btn] of foldButtons) btn.setAttribute("aria-selected", String(f === fold));
    container.dataset.currentMethod = method;
    container.dataset.currentK = String(k);
    container.dataset.currentFold = String(fold);

    drawParticipantGrid();

    const splitCount = participantsSplitAcrossFold(data, method, fold);
    splitStat.textContent =
      `Participants whose windows appear on both sides of ${foldLabels[fold]} ` +
      `(both in it and in at least one other fold): ${splitCount} of ${data.nParticipants}.`;

    const result = findKResult(data, k);
    const metrics = result[method];
    foldMetricsLine.textContent =
      `${METHOD_LABELS[method]}, k = ${k}, ${foldLabels[fold]}: ` +
      `accuracy = ${metrics.accPerFold[fold]!.toFixed(3)}, macro-F1 = ${metrics.f1PerFold[fold]!.toFixed(3)}.`;

    void drawConfusionPlot();
    void drawSummaryPlot();
  }

  for (const [m, btn] of methodButtons) {
    btn.addEventListener("click", () => {
      method = m;
      draw();
    });
  }
  for (const [kv, btn] of kButtons) {
    btn.addEventListener("click", () => {
      k = kv;
      draw();
    });
  }
  for (const [f, btn] of foldButtons) {
    btn.addEventListener("click", () => {
      fold = f;
      draw();
    });
  }
  resetBtn.addEventListener("click", () => {
    method = "ordinary";
    k = defaultK;
    fold = 0;
    draw();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void drawConfusionPlot();
    void drawSummaryPlot();
  });

  draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(confusionPlot);
      Plotly.purge(summaryPlot);
    },
  };
}

export const harFoldCompareComponent: WidgetComponent<HarFoldCompareConfig, HarFoldCompareData> = {
  type: "har-fold-compare",
  parseData: (raw) => parseHarFoldCompareData(raw),
  mount,
};
