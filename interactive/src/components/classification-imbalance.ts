// Production activity: Exercise 4's class-imbalance / misleading-accuracy
// interactive (WP18 sec 4). Every ratio/seed combination's counts and
// metrics are precomputed offline (scripts/export_classification_imbalance_data.py)
// from real resampled ABIDE participants -- the browser only selects and
// displays, it never refits. Controls select a class ratio (control always
// the majority class) and one of five predetermined split seeds; the chart
// compares the logistic-regression model's test accuracy against the
// majority-class baseline accuracy for that SAME test partition. Every
// entry uses the same fixed C from Section 3 (C = 1.0, WP19) -- never
// re-tuned per ratio or seed.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ClassificationImbalanceConfig } from "../config";
import {
  findEntry,
  type ClassificationImbalanceData,
  type ClassificationImbalanceEntry,
} from "../classification-imbalance-data";
import { parseClassificationImbalanceData } from "../classification-imbalance-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function mount(
  args: MountArgs<ClassificationImbalanceConfig, ClassificationImbalanceData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());

  let currentRatio = data.ratios[0]!.key;
  let currentSeed = data.splitSeeds[0]!;
  let destroyed = false;

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

  const imbalanceNote = document.createElement("p");
  imbalanceNote.className = "widget-note";
  imbalanceNote.textContent = config.imbalanceNote;
  container.appendChild(imbalanceNote);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "cls-imb-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  const metricsLine = document.createElement("p");
  metricsLine.className = "widget-stats";
  metricsLine.setAttribute("data-testid", "cls-imb-metrics");
  container.appendChild(metricsLine);

  const countsLine = document.createElement("p");
  countsLine.className = "widget-note";
  countsLine.setAttribute("data-testid", "cls-imb-counts");
  container.appendChild(countsLine);

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

  async function drawPlot(entry: ClassificationImbalanceEntry): Promise<void> {
    if (destroyed) return;
    const modelColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const baselineColor = theme.dark ? "#d9a441" : "#b5760a";
    const trace = {
      type: "bar" as const,
      x: ["Logistic regression", "Majority-class baseline"],
      y: [entry.accuracy, entry.majorityBaselineAccuracy],
      marker: { color: [modelColor, baselineColor] },
      text: [entry.accuracy, entry.majorityBaselineAccuracy].map((v) => `${(v * 100).toFixed(1)}%`),
      textposition: "outside" as const,
      // WP22: bar "outside" text does not reliably inherit `layout.font` in
      // every Plotly version -- pin it explicitly rather than let it fall
      // back to Plotly's own default (near-black, invisible on a dark card).
      textfont: { color: theme.axisColor },
      hovertemplate: "%{x}<br>%{y:.1%}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 340,
      margin: { t: 28 },
      title: { text: `Test accuracy at class ratio ${currentRatio}`, font: { size: 13, color: theme.axisColor } },
      yaxis: { title: { text: "Test accuracy" }, range: [0, 1.12], tickformat: ".0%" },
    });
    await Plotly.react(plot, [trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    plot.dataset.modelAccuracy = entry.accuracy.toFixed(4);
    plot.dataset.baselineAccuracy = entry.majorityBaselineAccuracy.toFixed(4);
    const n = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(n);
  }

  function draw(): void {
    const entry = findEntry(data, currentRatio, currentSeed);
    const ratioMeta = data.ratios.find((r) => r.key === currentRatio)!;
    cohortLine.textContent =
      `Full cohort for ${currentRatio}: ${entry.cohort.n} participants ` +
      `(${entry.cohort.nMajority} ${data.majorityClass}, ${entry.cohort.nMinority} ${data.minorityClass}; ` +
      `target ratio ${(ratioMeta.majorityPct * 100).toFixed(0)}:${(ratioMeta.minorityPct * 100).toFixed(0)}), seed ${currentSeed}.`;

    metricsLine.textContent =
      `AUC = ${entry.auc.toFixed(3)}  ·  balanced accuracy = ${entry.balancedAccuracy.toFixed(3)}  ·  ` +
      `sensitivity = ${entry.sensitivity.toFixed(3)}  ·  specificity = ${entry.specificity.toFixed(3)}`;

    const nTest = entry.nTestMajority + entry.nTestMinority;
    countsLine.textContent =
      `Test set: ${nTest} participants (${entry.nTestMajority} ${data.majorityClass}, ` +
      `${entry.nTestMinority} ${data.minorityClass}).`;

    container.dataset.currentRatio = currentRatio;
    container.dataset.currentSeed = String(currentSeed);
    void drawPlot(entry);
  }

  ratioSelect.addEventListener("change", () => {
    currentRatio = ratioSelect.value;
    draw();
  });
  seedSelect.addEventListener("change", () => {
    currentSeed = Number(seedSelect.value);
    draw();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    draw();
  });

  draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(plot);
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
