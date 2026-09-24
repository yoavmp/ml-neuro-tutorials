// Production activity: Exercise 10's "Does higher accuracy mean a better
// classifier?" (WP38R sec 5). Replaces the removed threshold-comparison
// activity (imbalance-threshold, WP38): there is NO threshold control here.
// Every (balance, model) combination's counts and metrics are precomputed
// offline (scripts/export_class_balance_compare_data.py) from real refitted
// models scored with a FIXED decision threshold of 0.5 (`.predict()`); the
// browser only selects a class-balance level and displays both models'
// results side by side -- it never refits and never sweeps a threshold.
//
// Visual hierarchy per the WP38R spec: (1) accuracy vs majority baseline for
// both models, (2) recall and F1 for both models -- both as large primary
// tiles; balanced accuracy, precision, ROC-AUC, PR-AUC(+baseline) are smaller
// secondary text. The across-balance chart defaults to accuracy vs baseline
// and offers a toggle to recall/F1. This component never claims
// class-weighting is universally better -- every evaluative sentence it
// shows is explicitly hedged, and the underlying data does not support such
// a claim (accuracy is lower for the class-weighted model at 80:20 and
// 90:10, even though recall is never lower).

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ClassBalanceCompareConfig } from "../config";
import {
  findEntry,
  parseClassBalanceCompareData,
  type ClassBalanceCompareData,
  type ClassBalanceCompareEntry,
  type ClassBalanceCompareModelKey,
} from "../class-balance-compare-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const MODEL_KEYS: readonly ClassBalanceCompareModelKey[] = ["ordinary", "classWeighted"];

const MODEL_LABELS: Record<ClassBalanceCompareModelKey, string> = {
  ordinary: "Ordinary logistic regression",
  classWeighted: 'Class-weighted logistic regression (class_weight="balanced")',
};

const MODEL_TESTID: Record<ClassBalanceCompareModelKey, string> = {
  ordinary: "ordinary",
  classWeighted: "weighted",
};

type ChartMetric = "accuracy" | "recall-f1";

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function fmtNum(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "n/a" : v.toFixed(3);
}

function mount(args: MountArgs<ClassBalanceCompareConfig, ClassBalanceCompareData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const ratioKeys = data.ratios.map((r) => r.key);
  let currentRatio = ratioKeys[0]!;
  let chartMetric: ChartMetric = "accuracy";
  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  // --- header --------------------------------------------------------------
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
  cohortLine.setAttribute("data-testid", "cbc-cohort");
  container.appendChild(cohortLine);

  // --- control: balance selector (the ONLY primary control) ---------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const ratioGroup = document.createElement("div");
  ratioGroup.className = "widget-control";
  const ratioLabel = document.createElement("label");
  ratioLabel.setAttribute("for", "cbc-ratio");
  ratioLabel.textContent = `Class balance (${data.majorityClass} : ${data.minorityClass}):`;
  const ratioSelect = document.createElement("select");
  ratioSelect.id = "cbc-ratio";
  ratioSelect.setAttribute("data-testid", "cbc-ratio-select");
  ratioSelect.setAttribute("aria-label", `Class balance, ${data.majorityClass} to ${data.minorityClass}`);
  for (const key of ratioKeys) {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = key;
    ratioSelect.appendChild(opt);
  }
  ratioGroup.append(ratioLabel, ratioSelect);
  controls.appendChild(ratioGroup);
  container.appendChild(controls);

  const thresholdNote = document.createElement("p");
  thresholdNote.className = "widget-note";
  thresholdNote.textContent =
    "Both models predict at a fixed decision threshold of 0.5 (no threshold to choose here) -- " +
    "the only thing that changes below is the class balance of the sample.";
  container.appendChild(thresholdNote);

  const baselineLine = document.createElement("p");
  baselineLine.className = "widget-stats";
  baselineLine.setAttribute("data-testid", "cbc-baseline");
  container.appendChild(baselineLine);

  // --- primary tiles: accuracy vs baseline, one per model -------------------
  const accHeading = document.createElement("h2");
  accHeading.className = "widget-subhead";
  accHeading.textContent = "Accuracy vs majority-class baseline";
  container.appendChild(accHeading);

  const accRow = document.createElement("div");
  accRow.className = "widget-metric-row";
  const accValueEls: Record<ClassBalanceCompareModelKey, HTMLParagraphElement> = {} as never;
  for (const key of MODEL_KEYS) {
    const tile = document.createElement("div");
    tile.className = "widget-metric-tile";
    tile.setAttribute("data-testid", `cbc-acc-tile-${MODEL_TESTID[key]}`);
    const label = document.createElement("p");
    label.className = "widget-metric-label";
    label.textContent = MODEL_LABELS[key];
    const value = document.createElement("p");
    value.className = "widget-metric-value";
    value.setAttribute("data-testid", `cbc-accuracy-${MODEL_TESTID[key]}`);
    tile.append(label, value);
    accRow.appendChild(tile);
    accValueEls[key] = value;
  }
  container.appendChild(accRow);

  // --- primary tiles: recall + F1, one per model ----------------------------
  const recallHeading = document.createElement("h2");
  recallHeading.className = "widget-subhead";
  recallHeading.textContent = `${data.minorityClass} recall and F1 (minority-class detection)`;
  container.appendChild(recallHeading);

  const recallRow = document.createElement("div");
  recallRow.className = "widget-metric-row";
  const recallValueEls: Record<ClassBalanceCompareModelKey, HTMLParagraphElement> = {} as never;
  const f1ValueEls: Record<ClassBalanceCompareModelKey, HTMLParagraphElement> = {} as never;
  for (const key of MODEL_KEYS) {
    const tile = document.createElement("div");
    tile.className = "widget-metric-tile";
    tile.setAttribute("data-testid", `cbc-recall-tile-${MODEL_TESTID[key]}`);
    const label = document.createElement("p");
    label.className = "widget-metric-label";
    label.textContent = MODEL_LABELS[key];
    const recallValue = document.createElement("p");
    recallValue.className = "widget-metric-value";
    recallValue.setAttribute("data-testid", `cbc-recall-${MODEL_TESTID[key]}`);
    const f1Value = document.createElement("p");
    f1Value.className = "widget-metric-baseline";
    f1Value.setAttribute("data-testid", `cbc-f1-${MODEL_TESTID[key]}`);
    tile.append(label, recallValue, f1Value);
    recallRow.appendChild(tile);
    recallValueEls[key] = recallValue;
    f1ValueEls[key] = f1Value;
  }
  container.appendChild(recallRow);

  // --- secondary metrics: balanced accuracy, precision, ROC-AUC, PR-AUC -----
  const secondaryEls: Record<ClassBalanceCompareModelKey, HTMLParagraphElement> = {} as never;
  for (const key of MODEL_KEYS) {
    const p = document.createElement("p");
    p.className = "widget-stats widget-metric-secondary";
    p.setAttribute("data-testid", `cbc-secondary-${MODEL_TESTID[key]}`);
    container.appendChild(p);
    secondaryEls[key] = p;
  }

  const hedgeNote = document.createElement("p");
  hedgeNote.className = "widget-note";
  hedgeNote.textContent =
    "Class weighting is not guaranteed to help every metric: it can raise autism recall while " +
    "lowering raw accuracy, and it does not always improve balanced accuracy either -- compare the " +
    "numbers directly rather than assuming one model is simply better.";
  container.appendChild(hedgeNote);

  // --- confusion matrices, side by side -------------------------------------
  const cmHeading = document.createElement("h2");
  cmHeading.className = "widget-subhead";
  cmHeading.textContent = "Confusion matrices (rows: actual diagnosis, columns: predicted diagnosis)";
  container.appendChild(cmHeading);

  const cmGrid = document.createElement("div");
  cmGrid.className = "widget-compare-grid";
  const cmCells: Record<ClassBalanceCompareModelKey, Record<"tn" | "fp" | "fn" | "tp", HTMLTableCellElement>> =
    {} as never;
  for (const key of MODEL_KEYS) {
    const panel = document.createElement("div");
    panel.className = "widget-compare-panel";
    const panelLabel = document.createElement("p");
    panelLabel.className = "widget-metric-label";
    panelLabel.textContent = MODEL_LABELS[key];
    panel.appendChild(panelLabel);

    const table = document.createElement("table");
    table.className = "widget-confusion-matrix";
    table.setAttribute("data-testid", `cbc-confusion-matrix-${MODEL_TESTID[key]}`);
    table.innerHTML = `
      <thead>
        <tr><th scope="col"></th><th scope="col">predicted ${data.majorityClass}</th><th scope="col">predicted ${data.minorityClass}</th></tr>
      </thead>
      <tbody>
        <tr><th scope="row">actual ${data.majorityClass}</th><td data-cell="tn"></td><td data-cell="fp"></td></tr>
        <tr><th scope="row">actual ${data.minorityClass}</th><td data-cell="fn"></td><td data-cell="tp"></td></tr>
      </tbody>`;
    panel.appendChild(table);
    cmGrid.appendChild(panel);

    cmCells[key] = {
      tn: table.querySelector('[data-cell="tn"]')!,
      fp: table.querySelector('[data-cell="fp"]')!,
      fn: table.querySelector('[data-cell="fn"]')!,
      tp: table.querySelector('[data-cell="tp"]')!,
    };
  }
  container.appendChild(cmGrid);

  // --- across-balance chart --------------------------------------------------
  const chartHeading = document.createElement("h2");
  chartHeading.className = "widget-subhead";
  chartHeading.textContent = "How does each measure change as the sample becomes more imbalanced?";
  container.appendChild(chartHeading);

  const chartControls = document.createElement("div");
  chartControls.className = "widget-controls";
  const chartMetricGroup = document.createElement("div");
  chartMetricGroup.className = "widget-control";
  const chartMetricLabel = document.createElement("label");
  chartMetricLabel.setAttribute("for", "cbc-chart-metric");
  chartMetricLabel.textContent = "Chart shows:";
  const chartMetricSelect = document.createElement("select");
  chartMetricSelect.id = "cbc-chart-metric";
  chartMetricSelect.setAttribute("data-testid", "cbc-chart-metric-select");
  const chartMetricOptions: Array<{ value: ChartMetric; label: string }> = [
    { value: "accuracy", label: "Accuracy vs majority baseline" },
    { value: "recall-f1", label: `${data.minorityClass} recall and F1` },
  ];
  for (const opt of chartMetricOptions) {
    const el = document.createElement("option");
    el.value = opt.value;
    el.textContent = opt.label;
    chartMetricSelect.appendChild(el);
  }
  chartMetricGroup.append(chartMetricLabel, chartMetricSelect);
  chartControls.appendChild(chartMetricGroup);
  container.appendChild(chartControls);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "cbc-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  const auxNote = document.createElement("p");
  auxNote.className = "widget-note";
  auxNote.textContent =
    "ROC-AUC ranks participants across every possible threshold and does not depend on class balance " +
    "the way accuracy does; PR-AUC is prevalence-sensitive, which is why its no-skill baseline (shown " +
    "next to it above) falls as autism becomes rarer. Which measure matters most depends on the " +
    "scientific question and on the relative cost of a missed autism case versus a false alarm.";
  container.appendChild(auxNote);

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

  function entryFor(ratioKey: string): ClassBalanceCompareEntry {
    return findEntry(data, ratioKey);
  }

  async function drawPlot(): Promise<void> {
    if (destroyed) return;
    const ordinaryColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const weightedColor = theme.dark ? "#d9a441" : "#b5760a";
    const baselineColor = theme.axisColor;

    const entries = ratioKeys.map((k) => entryFor(k));

    let traces: Array<Record<string, unknown>>;
    let yTitle: string;
    if (chartMetric === "accuracy") {
      traces = [
        {
          type: "scatter",
          mode: "lines+markers",
          name: MODEL_LABELS.ordinary,
          x: ratioKeys,
          y: entries.map((e) => e.models.ordinary.accuracy),
          marker: { color: ordinaryColor },
          line: { color: ordinaryColor },
          hovertemplate: "%{x}<br>accuracy %{y:.1%}<extra>" + MODEL_LABELS.ordinary + "</extra>",
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: MODEL_LABELS.classWeighted,
          x: ratioKeys,
          y: entries.map((e) => e.models.classWeighted.accuracy),
          marker: { color: weightedColor },
          line: { color: weightedColor },
          hovertemplate: "%{x}<br>accuracy %{y:.1%}<extra>" + MODEL_LABELS.classWeighted + "</extra>",
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: "Majority-class baseline",
          x: ratioKeys,
          y: entries.map((e) => e.models.ordinary.majorityBaselineAccuracy),
          line: { color: baselineColor, dash: "dot" },
          marker: { color: baselineColor, symbol: "diamond" },
          hovertemplate: "%{x}<br>baseline %{y:.1%}<extra>Majority-class baseline</extra>",
        },
      ];
      yTitle = "Accuracy";
    } else {
      traces = [
        {
          type: "scatter",
          mode: "lines+markers",
          name: `${MODEL_LABELS.ordinary} -- recall`,
          x: ratioKeys,
          y: entries.map((e) => e.models.ordinary.recall),
          marker: { color: ordinaryColor },
          line: { color: ordinaryColor },
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: `${MODEL_LABELS.classWeighted} -- recall`,
          x: ratioKeys,
          y: entries.map((e) => e.models.classWeighted.recall),
          marker: { color: weightedColor },
          line: { color: weightedColor },
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: `${MODEL_LABELS.ordinary} -- F1`,
          x: ratioKeys,
          y: entries.map((e) => e.models.ordinary.f1),
          marker: { color: ordinaryColor, symbol: "square" },
          line: { color: ordinaryColor, dash: "dash" },
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: `${MODEL_LABELS.classWeighted} -- F1`,
          x: ratioKeys,
          y: entries.map((e) => e.models.classWeighted.f1),
          marker: { color: weightedColor, symbol: "square" },
          line: { color: weightedColor, dash: "dash" },
        },
      ];
      yTitle = `${data.minorityClass} recall / F1`;
    }

    const layout = buildPlotLayout(theme, {
      height: 360,
      showlegend: true,
      margin: { t: 20, b: 60 },
      xaxis: { title: { text: `Class balance (${data.majorityClass} : ${data.minorityClass})` }, type: "category" as const },
      yaxis: { title: { text: yTitle }, range: [0, 1.05], tickformat: chartMetric === "accuracy" ? ".0%" : undefined },
    });
    await Plotly.react(plot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    plot.dataset.renderCount = String(Number(plot.dataset.renderCount ?? "0") + 1);
  }

  function draw(): void {
    const entry = entryFor(currentRatio);
    const nTest = entry.nTestMajority + entry.nTestMinority;

    cohortLine.textContent =
      `Full cohort at ${currentRatio}: ${entry.cohort.n} participants ` +
      `(${entry.cohort.nMajority} ${data.majorityClass}, ${entry.cohort.nMinority} ${data.minorityClass}). ` +
      `Locked test set: ${nTest} participants (${entry.nTestMajority} ${data.majorityClass}, ${entry.nTestMinority} ${data.minorityClass}).`;

    const baseline = entry.models.ordinary.majorityBaselineAccuracy;
    baselineLine.textContent =
      `Always predicting ${data.majorityClass} on this test set gets ${fmtPct(baseline)} accuracy -- ` +
      `this majority-class baseline rises as ${data.majorityClass} becomes more common, independent of either model.`;

    for (const key of MODEL_KEYS) {
      const m = entry.models[key];
      accValueEls[key].textContent = fmtPct(m.accuracy);
      recallValueEls[key].textContent = `Recall = ${fmtNum(m.recall)}`;
      f1ValueEls[key].textContent = `F1 = ${fmtNum(m.f1)}`;
      secondaryEls[key].textContent =
        `${MODEL_LABELS[key]}: balanced accuracy = ${fmtNum(m.balancedAccuracy)}  ·  ` +
        `precision = ${fmtNum(m.precision)}  ·  ROC-AUC = ${fmtNum(m.rocAuc)}  ·  ` +
        `PR-AUC = ${fmtNum(m.prAuc)} (no-skill baseline = ${fmtNum(m.prAucBaseline)})`;

      cmCells[key].tn.textContent = String(m.confusionMatrix.tn);
      cmCells[key].fp.textContent = String(m.confusionMatrix.fp);
      cmCells[key].fn.textContent = String(m.confusionMatrix.fn);
      cmCells[key].tp.textContent = String(m.confusionMatrix.tp);
    }

    container.dataset.currentRatio = currentRatio;
    container.dataset.currentChartMetric = chartMetric;
    void drawPlot();
  }

  ratioSelect.addEventListener("change", () => {
    currentRatio = ratioSelect.value;
    draw();
  });
  chartMetricSelect.addEventListener("change", () => {
    chartMetric = chartMetricSelect.value as ChartMetric;
    void drawPlot();
    container.dataset.currentChartMetric = chartMetric;
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void drawPlot();
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

export const classBalanceCompareComponent: WidgetComponent<ClassBalanceCompareConfig, ClassBalanceCompareData> = {
  type: "class-balance-compare",
  parseData: (raw) => parseClassBalanceCompareData(raw),
  mount,
};
