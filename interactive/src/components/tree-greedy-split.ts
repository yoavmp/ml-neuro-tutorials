// Production activity: Exercise 6's "Build a Tree Greedily" (WP29).
//
// Walks a student through three predetermined active nodes of a small
// synthetic regression-tree example (root, then one child, then the other
// child of the root split): at each node the student picks a feature and a
// candidate threshold, locks that choice, then reveals the greedy optimum
// computed at that node and compares it with their own proposal. The next
// node to examine is always chosen by the activity (the true greedy-optimal
// split from the previous node), not by the student's own proposal -- the
// dataset and every candidate threshold/MSE value are precomputed
// (scripts/export_tree_greedy_widget.py); nothing is recomputed live and no
// optimum is ever exposed before the student reveals it.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { TreeGreedySplitConfig } from "../config";
import {
  parseTreeGreedySplitData,
  type TreeGreedySplitData,
  type TreeGreedySplitObservation,
  type TreeGreedySplitRound,
} from "../tree-greedy-split-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

type FeatureKey = "x1" | "x2";

interface AcceptedSplit {
  roundId: string;
  feature: FeatureKey;
  threshold: number;
  bounds: Bounds;
}

interface Bounds {
  x1min: number;
  x1max: number;
  x2min: number;
  x2max: number;
}

const PADDING = 0.7;

function boundsOf(observations: TreeGreedySplitObservation[], ids: number[]): Bounds {
  const active = observations.filter((o) => ids.includes(o.id));
  const x1s = active.map((o) => o.x1);
  const x2s = active.map((o) => o.x2);
  return {
    x1min: Math.min(...x1s) - PADDING,
    x1max: Math.max(...x1s) + PADDING,
    x2min: Math.min(...x2s) - PADDING,
    x2max: Math.max(...x2s) + PADDING,
  };
}

function mount(args: MountArgs<TreeGreedySplitConfig, TreeGreedySplitData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let roundIndex = 0;
  let selectedFeature: FeatureKey = "x1";
  let selectedThresholdIndex = 0;
  let locked = false;
  let revealed = false;
  let finished = false;
  const acceptedSplits: AcceptedSplit[] = [];

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
  syntheticNote.setAttribute("data-testid", "tree-greedy-synthetic-note");
  syntheticNote.textContent = data.syntheticDataNote;
  container.appendChild(syntheticNote);

  const roundLabel = document.createElement("p");
  roundLabel.className = "widget-stats";
  roundLabel.setAttribute("data-testid", "tree-greedy-round-label");
  roundLabel.setAttribute("role", "status");
  roundLabel.setAttribute("aria-live", "polite");
  container.appendChild(roundLabel);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const featureGroup = document.createElement("div");
  featureGroup.className = "widget-control";
  const featureLabel = document.createElement("label");
  featureLabel.setAttribute("for", "tree-greedy-feature");
  featureLabel.textContent = "Feature to split on:";
  const featureSelect = document.createElement("select");
  featureSelect.id = "tree-greedy-feature";
  featureSelect.setAttribute("data-testid", "tree-greedy-feature-select");
  for (const key of ["x1", "x2"] as const) {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = data.features[key].label;
    featureSelect.appendChild(opt);
  }
  featureGroup.append(featureLabel, featureSelect);
  controls.appendChild(featureGroup);

  const thresholdGroup = document.createElement("div");
  thresholdGroup.className = "widget-control";
  const thresholdLabel = document.createElement("label");
  thresholdLabel.setAttribute("for", "tree-greedy-threshold");
  thresholdLabel.textContent = "Candidate threshold:";
  const thresholdSelect = document.createElement("select");
  thresholdSelect.id = "tree-greedy-threshold";
  thresholdSelect.setAttribute("data-testid", "tree-greedy-threshold-select");
  thresholdGroup.append(thresholdLabel, thresholdSelect);
  controls.appendChild(thresholdGroup);
  container.appendChild(controls);

  const buttonRow = document.createElement("div");
  buttonRow.className = "widget-controls";

  const lockButton = document.createElement("button");
  lockButton.type = "button";
  lockButton.textContent = "Lock My Answer";
  lockButton.setAttribute("data-testid", "tree-greedy-lock-button");

  const revealButton = document.createElement("button");
  revealButton.type = "button";
  revealButton.textContent = "Reveal Best Split";
  revealButton.setAttribute("data-testid", "tree-greedy-reveal-button");
  revealButton.disabled = true;

  const continueButton = document.createElement("button");
  continueButton.type = "button";
  continueButton.textContent = "Continue to Next Node";
  continueButton.setAttribute("data-testid", "tree-greedy-continue-button");
  continueButton.disabled = true;

  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.textContent = "Reset Tree";
  resetButton.setAttribute("data-testid", "tree-greedy-reset-button");

  buttonRow.append(lockButton, revealButton, continueButton, resetButton);
  container.appendChild(buttonRow);

  // --- panels ---------------------------------------------------------
  const featurePlotHeading = document.createElement("h2");
  featurePlotHeading.className = "widget-subhead";
  featurePlotHeading.textContent = "Feature space";
  container.appendChild(featurePlotHeading);

  const featurePlot = document.createElement("div");
  featurePlot.className = "widget-plot";
  featurePlot.setAttribute("data-testid", "tree-greedy-feature-plot");
  featurePlot.dataset.renderCount = "0";
  container.appendChild(featurePlot);

  const msePlotHeading = document.createElement("h2");
  msePlotHeading.className = "widget-subhead";
  msePlotHeading.textContent = "Candidate-threshold error";
  container.appendChild(msePlotHeading);

  const msePlot = document.createElement("div");
  msePlot.className = "widget-plot";
  msePlot.setAttribute("data-testid", "tree-greedy-mse-plot");
  msePlot.dataset.renderCount = "0";
  container.appendChild(msePlot);

  const scoreCard = document.createElement("p");
  scoreCard.className = "widget-stats";
  scoreCard.setAttribute("data-testid", "tree-greedy-scorecard");
  container.appendChild(scoreCard);

  const revealPanel = document.createElement("p");
  revealPanel.className = "widget-stats";
  revealPanel.setAttribute("data-testid", "tree-greedy-reveal-panel");
  revealPanel.hidden = true;
  container.appendChild(revealPanel);

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

  function currentRound(): TreeGreedySplitRound {
    return data.rounds[roundIndex]!;
  }

  function currentBounds(): Bounds {
    return boundsOf(data.observations, currentRound().activeObservationIds);
  }

  function refreshThresholdOptions(): void {
    const r = currentRound();
    const candidates = r.candidates[selectedFeature];
    thresholdSelect.replaceChildren();
    candidates.thresholds.forEach((t, i) => {
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = data.features[selectedFeature].label + " ≤ " + t.toFixed(2);
      thresholdSelect.appendChild(opt);
    });
    if (selectedThresholdIndex >= candidates.thresholds.length) selectedThresholdIndex = 0;
    thresholdSelect.value = String(selectedThresholdIndex);
  }

  function proposedSplitMSE(): number {
    const c = currentRound().candidates[selectedFeature];
    return c.splitMSE[selectedThresholdIndex]!;
  }

  function proposedCounts(): { nLeft: number; nRight: number } {
    const c = currentRound().candidates[selectedFeature];
    return { nLeft: c.nLeft[selectedThresholdIndex]!, nRight: c.nRight[selectedThresholdIndex]! };
  }

  // --- drawing ---------------------------------------------------------

  async function drawFeaturePlot(): Promise<void> {
    if (destroyed) return;
    const r = currentRound();
    const activeSet = new Set(r.activeObservationIds);

    const shapes: Record<string, unknown>[] = [];
    const bounds = currentBounds();
    shapes.push({
      type: "rect",
      x0: bounds.x1min,
      x1: bounds.x1max,
      y0: bounds.x2min,
      y1: bounds.x2max,
      line: { width: 0 },
      fillcolor: theme.dark ? "rgba(120,170,210,0.22)" : "rgba(42,111,158,0.16)",
      layer: "below",
    });

    for (const split of acceptedSplits) {
      if (split.feature === "x1") {
        shapes.push({
          type: "line",
          x0: split.threshold,
          x1: split.threshold,
          y0: split.bounds.x2min,
          y1: split.bounds.x2max,
          line: { color: theme.axisColor, width: 2, dash: "dot" },
        });
      } else {
        shapes.push({
          type: "line",
          x0: split.bounds.x1min,
          x1: split.bounds.x1max,
          y0: split.threshold,
          y1: split.threshold,
          line: { color: theme.axisColor, width: 2, dash: "dot" },
        });
      }
    }

    const candidates = r.candidates[selectedFeature];
    const threshold = candidates.thresholds[selectedThresholdIndex]!;
    if (selectedFeature === "x1") {
      shapes.push({
        type: "line",
        x0: threshold,
        x1: threshold,
        y0: bounds.x2min,
        y1: bounds.x2max,
        line: { color: theme.diagonalLine, width: 3 },
      });
    } else {
      shapes.push({
        type: "line",
        x0: bounds.x1min,
        x1: bounds.x1max,
        y0: threshold,
        y1: threshold,
        line: { color: theme.diagonalLine, width: 3 },
      });
    }

    const scatter = {
      type: "scatter" as const,
      mode: "markers" as const,
      x: data.observations.map((o) => o.x1),
      y: data.observations.map((o) => o.x2),
      text: data.observations.map((o) => `y = ${o.y.toFixed(1)}`),
      hovertemplate: "X1=%{x}<br>X2=%{y}<br>%{text}<extra></extra>",
      marker: {
        size: data.observations.map((o) => (activeSet.has(o.id) ? 14 : 9)),
        color: data.observations.map((o) => o.y),
        colorscale: "Viridis" as const,
        opacity: data.observations.map((o) => (activeSet.has(o.id) ? 1 : 0.25)),
        line: { color: theme.axisColor, width: 1 },
        showscale: true,
        colorbar: { title: { text: "target (y)" }, thickness: 12 },
      },
      showlegend: false,
    };

    const layout = buildPlotLayout(theme, {
      height: 380,
      shapes,
      xaxis: { title: { text: data.features.x1.label } },
      yaxis: { title: { text: data.features.x2.label } },
    });
    await Plotly.react(featurePlot, [scatter], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(featurePlot.dataset.renderCount ?? "0") + 1;
    featurePlot.dataset.renderCount = String(n);
  }

  async function drawMsePlot(): Promise<void> {
    if (destroyed) return;
    const r = currentRound();
    const c = r.candidates[selectedFeature];
    const colors = c.thresholds.map((_, i) => {
      if (revealed && r.optimal.feature === selectedFeature && i === r.optimal.thresholdIndex) {
        return theme.diagonalLine;
      }
      return i === selectedThresholdIndex ? theme.markerPrimary : theme.gridColor;
    });
    const bar = {
      type: "bar" as const,
      x: c.thresholds.map((t) => t.toFixed(2)),
      y: c.splitMSE,
      marker: { color: colors },
      hovertemplate: `${data.features[selectedFeature].label} ≤ %{x}<br>weighted split MSE %{y:.2f}<extra></extra>`,
    };
    const layout = buildPlotLayout(theme, {
      height: 280,
      xaxis: { title: { text: `Candidate ${data.features[selectedFeature].label} threshold` } },
      yaxis: { title: { text: "Weighted split MSE (lower is better)" } },
    });
    await Plotly.react(msePlot, [bar], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(msePlot.dataset.renderCount ?? "0") + 1;
    msePlot.dataset.renderCount = String(n);
  }

  function drawText(): void {
    const r = currentRound();
    const total = data.rounds.length;
    roundLabel.textContent =
      `Node ${roundIndex + 1} of ${total}: ${r.label}. ${r.activeObservationIds.length} observations are active here. ` +
      "Choose a feature and threshold, then lock your answer.";
    container.dataset.roundId = r.id;
    container.dataset.roundIndex = String(roundIndex);

    const { nLeft, nRight } = proposedCounts();
    const reduction = r.parentMSE - proposedSplitMSE();
    scoreCard.textContent =
      `Parent MSE = ${r.parentMSE.toFixed(2)}  ·  proposed split MSE = ${proposedSplitMSE().toFixed(2)}  ·  ` +
      `proposed MSE reduction = ${reduction.toFixed(2)}  ·  left child: ${nLeft} participants  ·  ` +
      `right child: ${nRight} participants (lower MSE is better).`;
    container.dataset.proposedSplitMse = proposedSplitMSE().toFixed(4);

    if (revealed) {
      const opt = r.optimal;
      const studentReduction = r.parentMSE - proposedSplitMSE();
      const diff = opt.reduction - studentReduction;
      revealPanel.hidden = false;
      revealPanel.textContent =
        `Greedy optimum: split on ${data.features[opt.feature].label} at threshold ${opt.threshold.toFixed(2)}, ` +
        `weighted split MSE = ${opt.splitMSE.toFixed(2)}, MSE reduction = ${opt.reduction.toFixed(2)}. ` +
        `Your proposed reduction was ${studentReduction.toFixed(2)} ` +
        `(${diff <= 1e-9 ? "you matched the greedy optimum" : `${diff.toFixed(2)} less than optimal`}). ` +
        `Left-child predicted value = ${opt.leftMean.toFixed(2)}, right-child predicted value = ${opt.rightMean.toFixed(2)}.`;
    } else {
      revealPanel.hidden = true;
      revealPanel.textContent = "";
    }

    lockButton.disabled = locked;
    featureSelect.disabled = locked;
    thresholdSelect.disabled = locked;
    revealButton.disabled = !locked || revealed;
    continueButton.disabled = !revealed || finished;
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    refreshThresholdOptions();
    drawText();
    await Promise.all([drawFeaturePlot(), drawMsePlot()]);
  }

  featureSelect.addEventListener("change", () => {
    selectedFeature = featureSelect.value as FeatureKey;
    selectedThresholdIndex = 0;
    void draw();
  });
  thresholdSelect.addEventListener("change", () => {
    selectedThresholdIndex = Number(thresholdSelect.value);
    void draw();
  });
  lockButton.addEventListener("click", () => {
    locked = true;
    void draw();
  });
  revealButton.addEventListener("click", () => {
    revealed = true;
    void draw();
  });
  continueButton.addEventListener("click", () => {
    const r = currentRound();
    acceptedSplits.push({
      roundId: r.id,
      feature: r.optimal.feature,
      threshold: r.optimal.threshold,
      bounds: currentBounds(),
    });
    if (roundIndex < data.rounds.length - 1) {
      roundIndex += 1;
      selectedFeature = "x1";
      selectedThresholdIndex = 0;
      locked = false;
      revealed = false;
    } else {
      finished = true;
    }
    void draw();
  });
  resetButton.addEventListener("click", () => {
    roundIndex = 0;
    selectedFeature = "x1";
    selectedThresholdIndex = 0;
    locked = false;
    revealed = false;
    finished = false;
    acceptedSplits.length = 0;
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
      Plotly.purge(featurePlot);
      Plotly.purge(msePlot);
    },
  };
}

export const treeGreedySplitComponent: WidgetComponent<TreeGreedySplitConfig, TreeGreedySplitData> = {
  type: "tree-greedy-split",
  parseData: parseTreeGreedySplitData,
  mount,
};
