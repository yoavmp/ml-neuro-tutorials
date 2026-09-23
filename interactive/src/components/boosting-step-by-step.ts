// Production activity: Exercise 7's "Build a Boosted Model" (WP32).
//
// Walks a student through squared-error gradient boosting, stage by stage,
// on a small synthetic dataset with one continuous predictor: at stage 0 the
// ensemble predicts the training-target mean for every observation; at each
// later stage a shallow regression stump (max_depth=1) fitted to the current
// residuals is added, scaled by the selected learning rate. Every stage, for
// every declared learning rate, is precomputed
// (scripts/export_boosting_step_widget.py); nothing is fit live here.

import Plotly from "plotly.js-cartesian-dist-min";
import type { PlotData } from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { BoostingStepByStepConfig } from "../config";
import {
  parseBoostingStepByStepData,
  stagesForLearningRate,
  type BoostingStepByStepData,
  type BoostingStepByStepStage,
} from "../boosting-step-by-step-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function sharedAxisRange(values: number[], padFrac: number): [number, number] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * padFrac || 1;
  return [min - pad, max + pad];
}

function mount(args: MountArgs<BoostingStepByStepConfig, BoostingStepByStepData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  const learningRates = data.learningRates;
  let learningRate = learningRates.includes(config.defaultLearningRate) ? config.defaultLearningRate : learningRates[0]!;
  let stageIndex = 0;
  let showScaled = false;

  const xValues = data.observations.map((o) => o.x);
  const yValues = data.observations.map((o) => o.y);
  const xRange = sharedAxisRange(xValues, 0.08);
  const yRange = sharedAxisRange(yValues, 0.15);

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
  syntheticNote.setAttribute("data-testid", "boosting-step-synthetic-note");
  syntheticNote.textContent = data.syntheticDataNote;
  container.appendChild(syntheticNote);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const lrGroup = document.createElement("div");
  lrGroup.className = "widget-control";
  const lrLabel = document.createElement("label");
  lrLabel.setAttribute("for", "boosting-step-lr");
  lrLabel.textContent = "Learning rate:";
  const lrSelect = document.createElement("select");
  lrSelect.id = "boosting-step-lr";
  lrSelect.setAttribute("data-testid", "boosting-step-lr-select");
  for (const eta of learningRates) {
    const opt = document.createElement("option");
    opt.value = String(eta);
    opt.textContent = String(eta);
    lrSelect.appendChild(opt);
  }
  lrGroup.append(lrLabel, lrSelect);
  controls.appendChild(lrGroup);

  const stageGroup = document.createElement("div");
  stageGroup.className = "widget-control";
  const stageLabel = document.createElement("label");
  stageLabel.setAttribute("for", "boosting-step-stage");
  stageLabel.textContent = "Boosting stage:";
  const stageSlider = document.createElement("input");
  stageSlider.id = "boosting-step-stage";
  stageSlider.type = "range";
  stageSlider.min = "0";
  stageSlider.max = String(data.nStages);
  stageSlider.step = "1";
  stageSlider.value = "0";
  stageSlider.setAttribute("data-testid", "boosting-step-stage-slider");
  stageSlider.setAttribute("aria-label", `Boosting stage, from 0 to ${data.nStages}`);
  const stageNumber = document.createElement("input");
  stageNumber.type = "number";
  stageNumber.id = "boosting-step-stage-number";
  stageNumber.min = "0";
  stageNumber.max = String(data.nStages);
  stageNumber.step = "1";
  stageNumber.value = "0";
  stageNumber.className = "widget-number-input";
  stageNumber.setAttribute("data-testid", "boosting-step-stage-number");
  stageNumber.setAttribute("aria-label", `Boosting stage, exact value, from 0 to ${data.nStages}`);
  stageGroup.append(stageLabel, stageSlider, stageNumber);
  controls.appendChild(stageGroup);
  container.appendChild(controls);

  const buttonRow = document.createElement("div");
  buttonRow.className = "widget-controls";

  const prevButton = document.createElement("button");
  prevButton.type = "button";
  prevButton.textContent = "Previous Step";
  prevButton.setAttribute("data-testid", "boosting-step-prev-button");

  const nextButton = document.createElement("button");
  nextButton.type = "button";
  nextButton.textContent = "Next Step";
  nextButton.setAttribute("data-testid", "boosting-step-next-button");

  buttonRow.append(prevButton, nextButton);
  container.appendChild(buttonRow);

  const toggleGroup = document.createElement("div");
  toggleGroup.className = "widget-control";
  const toggleLabel = document.createElement("label");
  toggleLabel.setAttribute("for", "boosting-step-scaled-toggle");
  const toggleInput = document.createElement("input");
  toggleInput.type = "checkbox";
  toggleInput.id = "boosting-step-scaled-toggle";
  toggleInput.setAttribute("data-testid", "boosting-step-scaled-toggle");
  toggleLabel.append(toggleInput, document.createTextNode(" Show the newest tree's correction after scaling by the learning rate"));
  toggleGroup.appendChild(toggleLabel);
  container.appendChild(toggleGroup);

  const stageLabelText = document.createElement("p");
  stageLabelText.className = "widget-stats";
  stageLabelText.setAttribute("data-testid", "boosting-step-stage-label");
  stageLabelText.setAttribute("role", "status");
  stageLabelText.setAttribute("aria-live", "polite");
  container.appendChild(stageLabelText);

  // --- panels ---------------------------------------------------------
  const p1Heading = document.createElement("h2");
  p1Heading.className = "widget-subhead";
  p1Heading.textContent = "Observations and the current ensemble prediction";
  container.appendChild(p1Heading);

  const observationPlot = document.createElement("div");
  observationPlot.className = "widget-plot";
  observationPlot.setAttribute("data-testid", "boosting-step-observation-plot");
  observationPlot.dataset.renderCount = "0";
  container.appendChild(observationPlot);

  const p2Heading = document.createElement("h2");
  p2Heading.className = "widget-subhead";
  p2Heading.textContent = "Residuals before this update and the newest shallow tree";
  container.appendChild(p2Heading);

  const residualPlot = document.createElement("div");
  residualPlot.className = "widget-plot";
  residualPlot.setAttribute("data-testid", "boosting-step-residual-plot");
  residualPlot.dataset.renderCount = "0";
  container.appendChild(residualPlot);

  const p3Heading = document.createElement("h2");
  p3Heading.className = "widget-subhead";
  p3Heading.textContent = "Training MSE by stage";
  container.appendChild(p3Heading);

  const msePlot = document.createElement("div");
  msePlot.className = "widget-plot";
  msePlot.setAttribute("data-testid", "boosting-step-mse-plot");
  msePlot.dataset.renderCount = "0";
  container.appendChild(msePlot);

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

  function currentStages(): BoostingStepByStepStage[] {
    return stagesForLearningRate(data, learningRate);
  }

  function currentStage(): BoostingStepByStepStage {
    return currentStages()[stageIndex]!;
  }

  // --- drawing ---------------------------------------------------------

  async function drawObservationPlot(): Promise<void> {
    if (destroyed) return;
    const s = currentStage();
    const scatter = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Observed",
      x: xValues,
      y: yValues,
      marker: { color: theme.markerPrimary, size: 8 },
      hovertemplate: `${data.feature.label} %{x}<br>${data.target.label} %{y}<extra></extra>`,
    };
    const ensembleLine = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: `Ensemble prediction (stage ${s.stage})`,
      x: xValues,
      y: s.ensemblePrediction,
      line: { color: theme.diagonalLine, width: 3 },
      hovertemplate: `${data.feature.label} %{x}<br>prediction %{y:.2f}<extra></extra>`,
    };
    const layout = buildPlotLayout(theme, {
      height: 320,
      showlegend: true,
      xaxis: { title: { text: data.feature.label }, range: [...xRange] },
      yaxis: { title: { text: data.target.label }, range: [...yRange] },
    });
    await Plotly.react(observationPlot, [scatter, ensembleLine], layout, PLOT_CONFIG);
    if (destroyed) return;
    observationPlot.dataset.renderCount = String(Number(observationPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawResidualPlot(): Promise<void> {
    if (destroyed) return;
    const s = currentStage();
    const residualScatter = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Residual before this update",
      x: xValues,
      y: s.residualBeforeUpdate,
      marker: { color: theme.markerPrimary, size: 8 },
      hovertemplate: `${data.feature.label} %{x}<br>residual %{y:.2f}<extra></extra>`,
    };
    const traces: PlotData[] = [residualScatter];
    if (s.stump) {
      const threshold = s.stump.threshold;
      const leftValue = showScaled ? s.stump.leftValue * learningRate : s.stump.leftValue;
      const rightValue = showScaled ? s.stump.rightValue * learningRate : s.stump.rightValue;
      const stumpName = showScaled ? "Newest tree (scaled by learning rate)" : "Newest tree (fitted to residuals)";
      traces.push({
        type: "scatter" as const,
        mode: "lines" as const,
        name: stumpName,
        x: [xRange[0], threshold, threshold, xRange[1]],
        y: [leftValue, leftValue, rightValue, rightValue],
        line: { color: theme.axisColor, width: 2, dash: "dot" as const },
        hoverinfo: "skip" as const,
      });
    }
    const layout = buildPlotLayout(theme, {
      height: 300,
      showlegend: true,
      xaxis: { title: { text: data.feature.label }, range: [...xRange] },
      yaxis: { title: { text: "Residual" } },
    });
    await Plotly.react(residualPlot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    residualPlot.dataset.renderCount = String(Number(residualPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawMsePlot(): Promise<void> {
    if (destroyed) return;
    const stages = currentStages();
    const bar = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Training MSE",
      x: stages.map((s) => s.stage),
      y: stages.map((s) => s.trainMSE),
      marker: {
        color: stages.map((s) => (s.stage === stageIndex ? theme.diagonalLine : theme.markerPrimary)),
        size: stages.map((s) => (s.stage === stageIndex ? 12 : 7)),
      },
      line: { color: theme.markerPrimary },
      hovertemplate: "stage %{x}<br>training MSE %{y:.2f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 240,
      xaxis: { title: { text: "Boosting stage" } },
      yaxis: { title: { text: "Training MSE" } },
    });
    await Plotly.react(msePlot, [bar], layout, PLOT_CONFIG);
    if (destroyed) return;
    msePlot.dataset.renderCount = String(Number(msePlot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const s = currentStage();
    stageLabelText.textContent =
      s.stage === 0
        ? `Stage 0: the model predicts the training-target mean for every observation. Training MSE = ${s.trainMSE.toFixed(2)}.`
        : `Stage ${s.stage} of ${data.nStages}: a new shallow tree was fitted to the residuals left by stage ${s.stage - 1} and added, scaled by learning rate ${learningRate}. Training MSE = ${s.trainMSE.toFixed(2)}.`;
    container.dataset.learningRate = String(learningRate);
    container.dataset.stageIndex = String(stageIndex);
    container.dataset.trainMse = s.trainMSE.toFixed(4);
    prevButton.disabled = stageIndex === 0;
    nextButton.disabled = stageIndex === data.nStages;
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    drawText();
    await Promise.all([drawObservationPlot(), drawResidualPlot(), drawMsePlot()]);
  }

  function setStage(next: number): void {
    stageIndex = Math.max(0, Math.min(data.nStages, next));
    stageSlider.value = String(stageIndex);
    stageNumber.value = String(stageIndex);
    void draw();
  }

  lrSelect.value = String(learningRate);
  lrSelect.addEventListener("change", () => {
    learningRate = Number(lrSelect.value);
    void draw();
  });

  stageSlider.addEventListener("input", () => {
    stageNumber.value = stageSlider.value;
  });
  stageSlider.addEventListener("change", () => setStage(Number(stageSlider.value)));
  stageNumber.addEventListener("change", () => {
    const raw = Number(stageNumber.value);
    if (!Number.isInteger(raw) || raw < 0 || raw > data.nStages) {
      stageNumber.value = String(stageIndex);
      return;
    }
    setStage(raw);
  });

  prevButton.addEventListener("click", () => setStage(stageIndex - 1));
  nextButton.addEventListener("click", () => setStage(stageIndex + 1));

  toggleInput.addEventListener("change", () => {
    showScaled = toggleInput.checked;
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
      Plotly.purge(observationPlot);
      Plotly.purge(residualPlot);
      Plotly.purge(msePlot);
    },
  };
}

export const boostingStepByStepComponent: WidgetComponent<BoostingStepByStepConfig, BoostingStepByStepData> = {
  type: "boosting-step-by-step",
  parseData: parseBoostingStepByStepData,
  mount,
};
