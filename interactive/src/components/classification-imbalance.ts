// Production activity: Exercise 4's class-imbalance / stratified-split
// interactive (WP17 sec 5). Every ratio/seed combination's counts and
// metrics are precomputed offline (scripts/export_classification_imbalance_data.py)
// from real resampled ABIDE participants -- the browser only selects and
// displays, it never refits. Controls select a class ratio (control always
// the majority class) and one of five predetermined split seeds, then show
// a stratified vs. an unstratified train_test_split side by side on the
// SAME resampled cohort.

import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ClassificationImbalanceConfig } from "../config";
import {
  findEntry,
  type ClassificationImbalanceData,
  type ClassificationImbalanceSide,
} from "../classification-imbalance-data";
import { parseClassificationImbalanceData } from "../classification-imbalance-data";

interface Panel {
  readonly key: "stratified" | "unstratified";
  readonly label: string;
  readonly testid: string;
}

const PANELS: Panel[] = [
  { key: "stratified", label: "Stratified split (train_test_split(..., stratify=y))", testid: "cls-imb-stratified" },
  { key: "unstratified", label: "Unstratified split (train_test_split without stratify)", testid: "cls-imb-unstratified" },
];

function formatAuc(auc: number | null): string {
  return auc === null ? "undefined: both classes are required" : auc.toFixed(3);
}

function mount(
  args: MountArgs<ClassificationImbalanceConfig, ClassificationImbalanceData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let currentRatio = data.ratios[0]!.key;
  let currentSeed = data.splitSeeds[0]!;

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
  cohortLine.setAttribute("data-testid", "cls-imb-cohort");
  container.appendChild(cohortLine);

  // --- controls: ratio select + seed select -------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const ratioGroup = document.createElement("div");
  ratioGroup.className = "widget-control";
  const ratioLabel = document.createElement("label");
  ratioLabel.setAttribute("for", "cls-imb-ratio");
  ratioLabel.textContent = `Class ratio (${data.majorityClass} : ${data.minorityClass}):`;
  const ratioSelect = document.createElement("select");
  ratioSelect.id = "cls-imb-ratio";
  ratioSelect.setAttribute("data-testid", "cls-imb-ratio-select");
  ratioSelect.setAttribute("aria-label", `Class ratio, ${data.majorityClass} to ${data.minorityClass}`);
  for (const r of data.ratios) {
    const opt = document.createElement("option");
    opt.value = r.key;
    opt.textContent = r.key;
    ratioSelect.appendChild(opt);
  }
  ratioGroup.append(ratioLabel, ratioSelect);

  const seedGroup = document.createElement("div");
  seedGroup.className = "widget-control";
  const seedLabel = document.createElement("label");
  seedLabel.setAttribute("for", "cls-imb-seed");
  seedLabel.textContent = "Split seed:";
  const seedSelect = document.createElement("select");
  seedSelect.id = "cls-imb-seed";
  seedSelect.setAttribute("data-testid", "cls-imb-seed-select");
  seedSelect.setAttribute("aria-label", "Predetermined split seed");
  for (const s of data.splitSeeds) {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = `seed ${s}`;
    seedSelect.appendChild(opt);
  }
  seedGroup.append(seedLabel, seedSelect);

  controls.append(ratioGroup, seedGroup);
  container.appendChild(controls);

  const stratNote = document.createElement("p");
  stratNote.className = "widget-note";
  stratNote.textContent = config.stratificationNote;
  container.appendChild(stratNote);

  const grid = document.createElement("div");
  grid.className = "widget-compare-grid";
  container.appendChild(grid);

  const panelEls: Record<Panel["key"], { splitLine: HTMLParagraphElement; table: HTMLTableElement; metricsLine: HTMLParagraphElement; baselineLine: HTMLParagraphElement }> =
    {} as Record<Panel["key"], { splitLine: HTMLParagraphElement; table: HTMLTableElement; metricsLine: HTMLParagraphElement; baselineLine: HTMLParagraphElement }>;

  for (const panel of PANELS) {
    const card = document.createElement("div");
    card.className = "widget-compare-panel";
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = panel.label;

    const splitLine = document.createElement("p");
    splitLine.className = "widget-stats";
    splitLine.setAttribute("data-testid", `${panel.testid}-split-counts`);

    const table = document.createElement("table");
    table.className = "widget-confusion-matrix";
    table.setAttribute("data-testid", `${panel.testid}-confusion-matrix`);
    table.innerHTML = `
      <thead>
        <tr><th scope="col"></th><th scope="col">predicted ${data.majorityClass}</th><th scope="col">predicted ${data.minorityClass}</th></tr>
      </thead>
      <tbody>
        <tr><th scope="row">actual ${data.majorityClass}</th><td data-testid="${panel.testid}-cm-tn"></td><td data-testid="${panel.testid}-cm-fp"></td></tr>
        <tr><th scope="row">actual ${data.minorityClass}</th><td data-testid="${panel.testid}-cm-fn"></td><td data-testid="${panel.testid}-cm-tp"></td></tr>
      </tbody>`;

    const metricsLine = document.createElement("p");
    metricsLine.className = "widget-stats";
    metricsLine.setAttribute("data-testid", `${panel.testid}-metrics`);

    const baselineLine = document.createElement("p");
    baselineLine.className = "widget-note";
    baselineLine.setAttribute("data-testid", `${panel.testid}-baseline`);

    card.append(h, splitLine, table, metricsLine, baselineLine);
    grid.appendChild(card);
    panelEls[panel.key] = { splitLine, table, metricsLine, baselineLine };
  }

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

  function fillPanel(key: Panel["key"], side: ClassificationImbalanceSide): void {
    const els = panelEls[key];
    const nTrain = side.nTrainMajority + side.nTrainMinority;
    const nTest = side.nTestMajority + side.nTestMinority;
    els.splitLine.textContent =
      `train: ${nTrain} (${side.nTrainMajority} ${data.majorityClass} / ${side.nTrainMinority} ${data.minorityClass})  ·  ` +
      `test: ${nTest} (${side.nTestMajority} ${data.majorityClass} / ${side.nTestMinority} ${data.minorityClass})`;

    const cm = side.confusionMatrix;
    els.table.querySelector(`[data-testid$="-cm-tn"]`)!.textContent = String(cm.tn);
    els.table.querySelector(`[data-testid$="-cm-fp"]`)!.textContent = String(cm.fp);
    els.table.querySelector(`[data-testid$="-cm-fn"]`)!.textContent = String(cm.fn);
    els.table.querySelector(`[data-testid$="-cm-tp"]`)!.textContent = String(cm.tp);

    els.metricsLine.textContent = `accuracy = ${side.accuracy.toFixed(3)}  ·  AUC = ${formatAuc(side.auc)}`;
    els.baselineLine.textContent =
      `Majority-class ("always predict ${data.majorityClass}") baseline accuracy on this test set: ` +
      `${(side.majorityBaselineAccuracy * 100).toFixed(1)}%.`;
  }

  function draw(): void {
    const entry = findEntry(data, currentRatio, currentSeed);
    const ratioMeta = data.ratios.find((r) => r.key === currentRatio)!;
    cohortLine.textContent =
      `Full cohort for ${currentRatio}: ${entry.cohort.n} participants ` +
      `(${entry.cohort.nMajority} ${data.majorityClass}, ${entry.cohort.nMinority} ${data.minorityClass}; ` +
      `target ratio ${(ratioMeta.majorityPct * 100).toFixed(0)}:${(ratioMeta.minorityPct * 100).toFixed(0)}), seed ${currentSeed}.`;
    fillPanel("stratified", entry.stratified);
    fillPanel("unstratified", entry.unstratified);
    container.dataset.currentRatio = currentRatio;
    container.dataset.currentSeed = String(currentSeed);
  }

  ratioSelect.addEventListener("change", () => {
    currentRatio = ratioSelect.value;
    draw();
  });
  seedSelect.addEventListener("change", () => {
    currentSeed = Number(seedSelect.value);
    draw();
  });

  draw();

  return {
    destroy() {
      // no Plotly instances to purge -- confusion matrices are plain tables.
    },
  };
}

export const classificationImbalanceComponent: WidgetComponent<
  ClassificationImbalanceConfig,
  ClassificationImbalanceData
> = {
  type: "classification-imbalance",
  parseData: (raw) => parseClassificationImbalanceData(raw),
  mount,
};
