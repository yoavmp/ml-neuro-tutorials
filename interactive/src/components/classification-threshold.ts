// Production activity: Exercise 3's decision-threshold interactive (WP17
// sec 4). Uses the FIXED honest test-set predicted probabilities -- the
// model is never refit when the threshold changes. Moving the threshold
// slider recomputes a real confusion matrix, accuracy, sensitivity,
// specificity, and percent-predicted-autism from those probabilities; the
// ROC curve and its AUC are computed once from the same fixed probabilities
// and never change with the threshold -- only the marked point on the curve
// moves. No Python kernel, no CDN, no brain features, no participant
// identifiers.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ClassificationThresholdConfig } from "../config";
import {
  accuracyFromCounts,
  aucTrapezoidal,
  confusionMatrix,
  percentPredictedPositive,
  predictAtThreshold,
  rocCurve,
  rocPointAtThreshold,
  sensitivityFromCounts,
  specificityFromCounts,
} from "../classification-metrics";
import { parseClassificationThresholdData, type ClassificationThresholdData } from "../classification-threshold-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const DEFAULT_THRESHOLD = 0.5;
const MIN_THRESHOLD = 0.05;
const MAX_THRESHOLD = 0.95;
const STEP = 0.01;

function clampThreshold(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_THRESHOLD;
  const clamped = Math.min(MAX_THRESHOLD, Math.max(MIN_THRESHOLD, value));
  return Math.round(clamped * 100) / 100;
}

function mount(
  args: MountArgs<ClassificationThresholdConfig, ClassificationThresholdData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());

  const points = rocCurve(data.labels, data.probabilities);
  const auc = aucTrapezoidal(points);

  let destroyed = false;
  let threshold = DEFAULT_THRESHOLD;

  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "cls-threshold-cohort");
  cohortLine.textContent =
    `Test set: ${data.split.nTest} participants (${data.positiveClass} = positive class), never refit -- ` +
    `these are the exact held-out predicted probabilities from ${data.model}.`;
  container.appendChild(cohortLine);

  // --- controls: slider + synchronized numeric input + reset -------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";
  const group = document.createElement("div");
  group.className = "widget-control";

  const label = document.createElement("label");
  label.setAttribute("for", "cls-threshold");
  label.textContent = "Decision threshold:";

  const slider = document.createElement("input");
  slider.id = "cls-threshold";
  slider.type = "range";
  slider.min = String(MIN_THRESHOLD);
  slider.max = String(MAX_THRESHOLD);
  slider.step = String(STEP);
  slider.value = String(DEFAULT_THRESHOLD);
  slider.setAttribute("data-testid", "cls-threshold-slider");
  slider.setAttribute("aria-label", `Decision threshold, from ${MIN_THRESHOLD} to ${MAX_THRESHOLD}`);

  const number = document.createElement("input");
  number.type = "number";
  number.id = "cls-threshold-number";
  number.min = String(MIN_THRESHOLD);
  number.max = String(MAX_THRESHOLD);
  number.step = String(STEP);
  number.value = String(DEFAULT_THRESHOLD);
  number.setAttribute("data-testid", "cls-threshold-number");
  number.setAttribute("aria-label", `Decision threshold, exact value, from ${MIN_THRESHOLD} to ${MAX_THRESHOLD}`);
  number.className = "widget-number-input";

  const valueOut = document.createElement("output");
  valueOut.setAttribute("for", "cls-threshold");
  valueOut.setAttribute("data-testid", "cls-threshold-value");
  valueOut.className = "widget-bin-value";
  valueOut.textContent = DEFAULT_THRESHOLD.toFixed(2);

  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset to 0.50";
  resetBtn.setAttribute("data-testid", "cls-threshold-reset");

  group.append(label, slider, number, valueOut, resetBtn);
  controls.appendChild(group);
  container.appendChild(controls);

  const thresholdNote = document.createElement("p");
  thresholdNote.className = "widget-note";
  thresholdNote.textContent = config.thresholdNote;
  container.appendChild(thresholdNote);

  const metrics = document.createElement("p");
  metrics.className = "widget-stats";
  metrics.setAttribute("data-testid", "cls-metrics");
  container.appendChild(metrics);

  // --- confusion matrix (HTML table, not Plotly) --------------------------
  const cmHeading = document.createElement("h2");
  cmHeading.className = "widget-subhead";
  cmHeading.textContent = "Confusion matrix (rows: actual diagnosis, columns: predicted diagnosis)";
  container.appendChild(cmHeading);

  const table = document.createElement("table");
  table.className = "widget-confusion-matrix";
  table.setAttribute("data-testid", "cls-confusion-matrix");
  const posLabel = data.positiveClass;
  const negLabel = data.negativeClass;
  table.innerHTML = `
    <thead>
      <tr><th scope="col"></th><th scope="col">predicted ${negLabel}</th><th scope="col">predicted ${posLabel}</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">actual ${negLabel}</th><td data-testid="cls-cm-tn"></td><td data-testid="cls-cm-fp"></td></tr>
      <tr><th scope="row">actual ${posLabel}</th><td data-testid="cls-cm-fn"></td><td data-testid="cls-cm-tp"></td></tr>
    </tbody>`;
  container.appendChild(table);

  const rocHeading = document.createElement("h2");
  rocHeading.className = "widget-subhead";
  rocHeading.textContent = "ROC curve";
  container.appendChild(rocHeading);

  const rocPlot = document.createElement("div");
  rocPlot.className = "widget-plot";
  rocPlot.setAttribute("data-testid", "cls-roc-plot");
  rocPlot.dataset.renderCount = "0";
  container.appendChild(rocPlot);

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

  async function drawRoc(): Promise<void> {
    if (destroyed) return;
    const rocColor = theme.dark ? "#8fb8da" : "#2a6f9e";
    const chanceColor = theme.dark ? "#b0b0b0" : "#888888";
    const markerColor = theme.dark ? "#f0915c" : "#b5622f";
    const point = rocPointAtThreshold(data.labels, data.probabilities, threshold);
    const rocTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: points.map((p) => p.fpr),
      y: points.map((p) => p.tpr),
      line: { color: rocColor, width: 2.5 },
      name: `ROC curve (AUC = ${auc.toFixed(3)})`,
      hovertemplate: "FPR %{x:.2f}<br>TPR %{y:.2f}<extra></extra>",
    };
    const chanceTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: [0, 1],
      y: [0, 1],
      line: { color: chanceColor, width: 1.5, dash: "dash" as const },
      hoverinfo: "skip" as const,
      name: config.rocChanceLabel,
    };
    const currentPointTrace = {
      type: "scatter" as const,
      mode: "markers" as const,
      x: [point.fpr],
      y: [point.tpr],
      marker: { color: markerColor, size: 11, symbol: "circle" },
      name: `Selected threshold (${threshold.toFixed(2)})`,
      hovertemplate: `threshold ${threshold.toFixed(2)}<br>FPR %{x:.2f}<br>TPR %{y:.2f}<extra></extra>`,
    };
    const layout = buildPlotLayout(theme, {
      height: 360,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.18, font: { size: 10 } },
      xaxis: { title: { text: "False positive rate" }, range: [-0.02, 1.02] },
      yaxis: { title: { text: "True positive rate (sensitivity)" }, range: [-0.02, 1.02] },
    });
    await Plotly.react(rocPlot, [rocTrace, chanceTrace, currentPointTrace], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(rocPlot.dataset.renderCount ?? "0") + 1;
    rocPlot.dataset.renderCount = String(n);
  }

  function draw(): void {
    slider.value = String(threshold);
    number.value = threshold.toFixed(2);
    valueOut.textContent = threshold.toFixed(2);
    container.dataset.currentThreshold = threshold.toFixed(2);

    const predicted = predictAtThreshold(data.probabilities, threshold);
    const cm = confusionMatrix(data.labels, predicted);
    const accuracy = accuracyFromCounts(cm);
    const sensitivity = sensitivityFromCounts(cm);
    const specificity = specificityFromCounts(cm);
    const pctPositive = percentPredictedPositive(data.probabilities, threshold);

    metrics.textContent =
      `threshold = ${threshold.toFixed(2)}  ·  accuracy = ${accuracy.toFixed(3)}  ·  ` +
      `sensitivity = ${sensitivity.toFixed(3)}  ·  specificity = ${specificity.toFixed(3)}  ·  ` +
      `predicted ${posLabel} = ${pctPositive.toFixed(1)}%  ·  AUC (fixed, threshold-independent) = ${auc.toFixed(3)}`;

    container.querySelector('[data-testid="cls-cm-tn"]')!.textContent = String(cm.tn);
    container.querySelector('[data-testid="cls-cm-fp"]')!.textContent = String(cm.fp);
    container.querySelector('[data-testid="cls-cm-fn"]')!.textContent = String(cm.fn);
    container.querySelector('[data-testid="cls-cm-tp"]')!.textContent = String(cm.tp);

    void drawRoc();
  }

  function setThreshold(next: number): void {
    threshold = clampThreshold(next);
    draw();
  }

  slider.addEventListener("input", () => {
    valueOut.textContent = Number(slider.value).toFixed(2);
    number.value = slider.value;
  });
  slider.addEventListener("change", () => setThreshold(Number(slider.value)));

  number.addEventListener("change", () => {
    const raw = Number(number.value);
    if (!Number.isFinite(raw) || raw < MIN_THRESHOLD || raw > MAX_THRESHOLD) {
      number.value = threshold.toFixed(2);
      return;
    }
    setThreshold(raw);
  });

  resetBtn.addEventListener("click", () => setThreshold(DEFAULT_THRESHOLD));

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    draw();
  });

  draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(rocPlot);
    },
  };
}

export const classificationThresholdComponent: WidgetComponent<
  ClassificationThresholdConfig,
  ClassificationThresholdData
> = {
  type: "classification-threshold",
  parseData: (raw) => parseClassificationThresholdData(raw),
  mount,
};
