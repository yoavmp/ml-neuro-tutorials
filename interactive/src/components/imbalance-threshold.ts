// Production activity: Exercise 10's "High accuracy can still miss the
// minority class" -- a fixed 90:10 control:autism test cohort with FIXED
// predicted probabilities from an ordinary and a class-weighted logistic
// regression (WP38). Moving the threshold slider recomputes a real confusion
// matrix and every threshold-dependent metric from those fixed probabilities
// -- the model is never refit. ROC-AUC and PR-AUC are threshold-independent
// and read straight from the artifact.
//
// Visual hierarchy per the WP38 spec: accuracy-vs-majority-baseline and
// PR-AUC-vs-prevalence are the two large, primary tiles; F1/precision/recall
// and ROC-AUC are smaller secondary text. This component never claims
// class-weighting is universally better -- any evaluative sentence it shows
// is explicitly hedged.

import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ImbalanceThresholdConfig } from "../config";
import {
  parseImbalanceThresholdData,
  type ImbalanceThresholdData,
  type ImbalanceThresholdModelKey,
} from "../imbalance-threshold-data";
import {
  accuracyFromCounts,
  balancedAccuracyFromCounts,
  confusionMatrix,
  f1FromCounts,
  precisionFromCounts,
  predictAtThreshold,
  recallFromCounts,
} from "../classification-metrics";

const DEFAULT_THRESHOLD = 0.5;
const MIN_THRESHOLD = 0;
const MAX_THRESHOLD = 1;
const STEP = 0.01;
const DEFAULT_MODEL: ImbalanceThresholdModelKey = "ordinary";

function clampThreshold(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_THRESHOLD;
  const clamped = Math.min(MAX_THRESHOLD, Math.max(MIN_THRESHOLD, value));
  return Math.round(clamped * 100) / 100;
}

function mount(args: MountArgs<ImbalanceThresholdConfig, ImbalanceThresholdData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let model: ImbalanceThresholdModelKey = DEFAULT_MODEL;
  let threshold = DEFAULT_THRESHOLD;

  const posLabel = data.minorityClass;
  const negLabel = data.majorityClass;

  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const nTest = data.nTestMajority + data.nTestMinority;
  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "imb-cohort");
  cohortLine.textContent =
    `Cohort: ${data.cohort.n} participants (${data.cohort.nMajority} ${negLabel}, ${data.cohort.nMinority} ${posLabel}). ` +
    `Locked test set: ${nTest} participants (${data.nTestMajority} ${negLabel}, ${data.nTestMinority} ${posLabel}), never refit.`;
  container.appendChild(cohortLine);

  // --- controls: model select + threshold slider + reset -----------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const modelGroup = document.createElement("div");
  modelGroup.className = "widget-control";
  const modelLabel = document.createElement("label");
  modelLabel.setAttribute("for", "imb-model");
  modelLabel.textContent = "Model:";
  const modelSelect = document.createElement("select");
  modelSelect.id = "imb-model";
  modelSelect.setAttribute("data-testid", "imb-model-select");
  const modelOptions: Array<{ key: ImbalanceThresholdModelKey; label: string }> = [
    { key: "ordinary", label: "Ordinary logistic regression" },
    { key: "classWeighted", label: 'Class-weighted logistic regression (class_weight="balanced")' },
  ];
  for (const opt of modelOptions) {
    const el = document.createElement("option");
    el.value = opt.key;
    el.textContent = opt.label;
    modelSelect.appendChild(el);
  }
  modelGroup.append(modelLabel, modelSelect);
  controls.appendChild(modelGroup);

  const thresholdGroup = document.createElement("div");
  thresholdGroup.className = "widget-control";
  const thresholdLabel = document.createElement("label");
  thresholdLabel.setAttribute("for", "imb-threshold");
  thresholdLabel.textContent = "Classification threshold:";
  const slider = document.createElement("input");
  slider.id = "imb-threshold";
  slider.type = "range";
  slider.min = String(MIN_THRESHOLD);
  slider.max = String(MAX_THRESHOLD);
  slider.step = String(STEP);
  slider.value = String(DEFAULT_THRESHOLD);
  slider.setAttribute("data-testid", "imb-threshold-slider");
  slider.setAttribute("aria-label", `Classification threshold, from ${MIN_THRESHOLD} to ${MAX_THRESHOLD}`);

  const number = document.createElement("input");
  number.type = "number";
  number.id = "imb-threshold-number";
  number.min = String(MIN_THRESHOLD);
  number.max = String(MAX_THRESHOLD);
  number.step = String(STEP);
  number.value = String(DEFAULT_THRESHOLD);
  number.setAttribute("data-testid", "imb-threshold-number");
  number.className = "widget-number-input";
  number.setAttribute("aria-label", `Classification threshold, exact value, from ${MIN_THRESHOLD} to ${MAX_THRESHOLD}`);

  const valueOut = document.createElement("output");
  valueOut.setAttribute("for", "imb-threshold");
  valueOut.setAttribute("data-testid", "imb-threshold-value");
  valueOut.className = "widget-bin-value";
  valueOut.textContent = DEFAULT_THRESHOLD.toFixed(2);

  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset";
  resetBtn.setAttribute("data-testid", "imb-reset-button");

  thresholdGroup.append(thresholdLabel, slider, number, valueOut, resetBtn);
  controls.appendChild(thresholdGroup);
  container.appendChild(controls);

  // --- primary metric tiles: accuracy vs baseline, PR-AUC vs prevalence --
  const tileRow = document.createElement("div");
  tileRow.className = "widget-metric-row";

  const accTile = document.createElement("div");
  accTile.className = "widget-metric-tile";
  accTile.setAttribute("data-testid", "imb-acc-tile");
  const accLabel = document.createElement("p");
  accLabel.className = "widget-metric-label";
  accLabel.textContent = "Accuracy vs majority-class baseline";
  const accValue = document.createElement("p");
  accValue.className = "widget-metric-value";
  accValue.setAttribute("data-testid", "imb-accuracy");
  const accBaseline = document.createElement("p");
  accBaseline.className = "widget-metric-baseline";
  accBaseline.setAttribute("data-testid", "imb-baseline");
  accBaseline.textContent = `Always predicting ${negLabel} gets ${(data.majorityBaselineAccuracy * 100).toFixed(1)}% accuracy.`;
  accTile.append(accLabel, accValue, accBaseline);

  const praucTile = document.createElement("div");
  praucTile.className = "widget-metric-tile";
  praucTile.setAttribute("data-testid", "imb-prauc-tile");
  const praucLabel = document.createElement("p");
  praucLabel.className = "widget-metric-label";
  praucLabel.textContent = "Precision-recall AUC vs prevalence";
  const praucValue = document.createElement("p");
  praucValue.className = "widget-metric-value";
  praucValue.setAttribute("data-testid", "imb-prauc");
  const praucBaseline = document.createElement("p");
  praucBaseline.className = "widget-metric-baseline";
  praucBaseline.setAttribute("data-testid", "imb-prauc-baseline");
  praucBaseline.textContent =
    `A classifier with no real signal scores about ${data.positivePrevalence.toFixed(2)} here -- the positive prevalence, not 0. ` +
    "PR-AUC is threshold-independent, so it does not change with the slider above.";
  praucTile.append(praucLabel, praucValue, praucBaseline);

  tileRow.append(accTile, praucTile);
  container.appendChild(tileRow);

  const secondary = document.createElement("p");
  secondary.className = "widget-stats widget-metric-secondary";
  secondary.setAttribute("data-testid", "imb-secondary-metrics");
  container.appendChild(secondary);

  const hedgeNote = document.createElement("p");
  hedgeNote.className = "widget-note";
  hedgeNote.textContent =
    "Switching model changes which participants are flagged as positive at a given threshold -- compare the confusion matrix and metrics directly rather than assuming one model is simply better.";
  container.appendChild(hedgeNote);

  // --- confusion matrix (HTML table) --------------------------------------
  const cmHeading = document.createElement("h2");
  cmHeading.className = "widget-subhead";
  cmHeading.textContent = "Confusion matrix (rows: actual diagnosis, columns: predicted diagnosis)";
  container.appendChild(cmHeading);

  const table = document.createElement("table");
  table.className = "widget-confusion-matrix";
  table.setAttribute("data-testid", "imb-confusion-matrix");
  table.innerHTML = `
    <thead>
      <tr><th scope="col"></th><th scope="col">predicted ${negLabel}</th><th scope="col">predicted ${posLabel}</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">actual ${negLabel}</th><td data-testid="imb-cm-tn"></td><td data-testid="imb-cm-fp"></td></tr>
      <tr><th scope="row">actual ${posLabel}</th><td data-testid="imb-cm-fn"></td><td data-testid="imb-cm-tp"></td></tr>
    </tbody>`;
  container.appendChild(table);

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

  function draw(): void {
    modelSelect.value = model;
    slider.value = String(threshold);
    number.value = threshold.toFixed(2);
    valueOut.textContent = threshold.toFixed(2);
    container.dataset.currentModel = model;
    container.dataset.currentThreshold = threshold.toFixed(2);

    const modelResult = data.models[model];
    const predicted = predictAtThreshold(modelResult.predictedProbaPositive, threshold);
    const cm = confusionMatrix(data.testLabels, predicted);
    const accuracy = accuracyFromCounts(cm);
    const balancedAccuracy = balancedAccuracyFromCounts(cm);
    const precision = precisionFromCounts(cm);
    const recall = recallFromCounts(cm);
    const f1 = f1FromCounts(cm);

    accValue.textContent = `${(accuracy * 100).toFixed(1)}%`;
    praucValue.textContent = modelResult.prAuc.toFixed(3);

    secondary.textContent =
      `Balanced accuracy = ${Number.isFinite(balancedAccuracy) ? balancedAccuracy.toFixed(3) : "n/a"}  ·  ` +
      `F1 = ${Number.isFinite(f1) ? f1.toFixed(3) : "n/a"}  ·  ` +
      `Precision = ${Number.isFinite(precision) ? precision.toFixed(3) : "n/a"}  ·  ` +
      `Recall = ${Number.isFinite(recall) ? recall.toFixed(3) : "n/a"}  ·  ` +
      `ROC-AUC (fixed, threshold-independent) = ${modelResult.rocAuc.toFixed(3)}`;

    container.querySelector('[data-testid="imb-cm-tn"]')!.textContent = String(cm.tn);
    container.querySelector('[data-testid="imb-cm-fp"]')!.textContent = String(cm.fp);
    container.querySelector('[data-testid="imb-cm-fn"]')!.textContent = String(cm.fn);
    container.querySelector('[data-testid="imb-cm-tp"]')!.textContent = String(cm.tp);
  }

  function setThreshold(next: number): void {
    threshold = clampThreshold(next);
    draw();
  }

  modelSelect.addEventListener("change", () => {
    model = modelSelect.value as ImbalanceThresholdModelKey;
    draw();
  });

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

  resetBtn.addEventListener("click", () => {
    model = DEFAULT_MODEL;
    threshold = DEFAULT_THRESHOLD;
    draw();
  });

  draw();

  return {
    destroy() {
      // No Plotly instances, no subscriptions, no timers.
    },
  };
}

export const imbalanceThresholdComponent: WidgetComponent<ImbalanceThresholdConfig, ImbalanceThresholdData> = {
  type: "imbalance-threshold",
  parseData: (raw) => parseImbalanceThresholdData(raw),
  mount,
};
