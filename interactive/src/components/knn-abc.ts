// Production activity: Exercise 3 Section 3's interactive honest-vs-invalid
// KNN comparison (WP14 §4.4), replacing the old static k=15 A/B/C table and
// separate static k=1 demonstration with one interactive control.
//
// A k slider AND a synchronized numeric input (shared range 1..min(n_train,
// n_test), since C's reference pool is the smaller test set) drive three
// synchronized observed-vs-predicted panels, all standardized KNN regression
// for age on Exercise 2's own locked 753/251 outer split:
//   A. valid        -- fit on training rows, evaluate test rows;
//   B. resubstitution -- fit on training rows, evaluate those training rows;
//   C. invalid (leakage) -- fit on test rows, evaluate those same test rows.
// Changing k recomputes all three real prediction arrays, plots, R2 and MSE
// from the precomputed neighbour-ordered target arrays
// (scripts/export_knn_abc_data.py) -- never merely relabels. No Python
// kernel, no CDN, no brain features, no participant identifiers.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { KnnAbcConfig } from "../config";
import { r2Score, meanSquaredError, sharedAxisRange, predictAllForK } from "../knn-explore";
import { parseKnnAbcData, type KnnAbcData } from "../knn-abc-data";

function prefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function clampK(value: number, kMax: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(kMax, Math.max(1, Math.round(value)));
}

interface Panel {
  readonly key: "A" | "B" | "C";
  readonly label: string;
  readonly subtitle: string;
  readonly testid: string;
  readonly neighborTargets: readonly (readonly number[])[];
  readonly observed: readonly number[];
}

function mount(args: MountArgs<KnnAbcConfig, KnnAbcData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const kMax = data.split.kMax;
  const defaultK = data.selectedKFromAudit;
  if (defaultK < 1 || defaultK > kMax) {
    throw new Error(`selectedKFromAudit ${defaultK} is outside [1, ${kMax}]`);
  }

  const dark = prefersDark();
  const axisColor = dark ? "#c9c9c9" : "#333333";
  const gridColor = dark ? "#3a3a3a" : "#e2e2e2";
  const markerColor = dark ? "rgba(120,170,210,0.55)" : "rgba(42,111,158,0.5)";
  const diagColor = dark ? "#d98b5f" : "#b5622f";
  const plotConfig = { displayModeBar: false, responsive: true };

  const scatterAxisRange = sharedAxisRange([...data.observedTrain, ...data.observedTest], 0.05);

  const panels: Panel[] = [
    {
      key: "A",
      label: "A. Valid",
      subtitle: "fit on training rows, evaluate test rows",
      testid: "knn-abc-panel-a",
      neighborTargets: data.neighborTargetsA,
      observed: data.observedTest,
    },
    {
      key: "B",
      label: "B. Resubstitution",
      subtitle: "fit on training rows, evaluate those training rows",
      testid: "knn-abc-panel-b",
      neighborTargets: data.neighborTargetsB,
      observed: data.observedTrain,
    },
    {
      key: "C",
      label: "C. Invalid (leakage)",
      subtitle: "fit on test rows, evaluate those same test rows",
      testid: "knn-abc-panel-c",
      neighborTargets: data.neighborTargetsC,
      observed: data.observedTest,
    },
  ];

  let destroyed = false;
  let currentK = defaultK;

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
  cohortLine.setAttribute("data-testid", "knn-abc-cohort");
  cohortLine.textContent =
    `Training rows: ${data.split.nTrain} · Test rows: ${data.split.nTest} (Exercise 2's own locked ` +
    `outer split). k ranges 1..${kMax} -- the smaller of the two sample sizes, since panel C's own ` +
    `reference pool is the ${data.split.nTest}-row test set. Feature recipe: ` +
    `${data.featureRecipe.featureCount} standardized cortical-thickness features.`;
  container.appendChild(cohortLine);

  const controls = document.createElement("div");
  controls.className = "widget-controls";
  const kGroup = document.createElement("div");
  kGroup.className = "widget-control";
  const kLabel = document.createElement("label");
  kLabel.setAttribute("for", "knn-abc-k");
  kLabel.textContent = "Number of neighbours (k):";
  const kInput = document.createElement("input");
  kInput.id = "knn-abc-k";
  kInput.type = "range";
  kInput.min = "1";
  kInput.max = String(kMax);
  kInput.step = "1";
  kInput.value = String(defaultK);
  kInput.setAttribute("data-testid", "knn-abc-k-slider");
  kInput.setAttribute("aria-label", `Number of neighbours, from 1 to ${kMax}`);

  const kNumber = document.createElement("input");
  kNumber.type = "number";
  kNumber.id = "knn-abc-k-number";
  kNumber.min = "1";
  kNumber.max = String(kMax);
  kNumber.step = "1";
  kNumber.value = String(defaultK);
  kNumber.setAttribute("data-testid", "knn-abc-k-number");
  kNumber.setAttribute("aria-label", `Number of neighbours, exact value, from 1 to ${kMax}`);
  kNumber.className = "widget-number-input";

  const kValue = document.createElement("output");
  kValue.setAttribute("for", "knn-abc-k");
  kValue.setAttribute("data-testid", "knn-abc-k-value");
  kValue.className = "widget-bin-value";
  kValue.textContent = String(defaultK);
  kGroup.append(kLabel, kInput, kNumber, kValue);
  controls.appendChild(kGroup);
  container.appendChild(controls);

  const k1Note = document.createElement("p");
  k1Note.className = "widget-note";
  k1Note.setAttribute("data-testid", "knn-abc-k1-note");
  k1Note.textContent = config.k1Note;
  container.appendChild(k1Note);

  const grid = document.createElement("div");
  grid.className = "widget-compare-grid";
  container.appendChild(grid);

  const plotDivs: Record<Panel["key"], HTMLDivElement> = {} as Record<Panel["key"], HTMLDivElement>;
  const metricLines: Record<Panel["key"], HTMLParagraphElement> = {} as Record<Panel["key"], HTMLParagraphElement>;

  for (const panel of panels) {
    const card = document.createElement("div");
    card.className = "widget-compare-panel";
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = panel.label;
    const sub = document.createElement("p");
    sub.className = "widget-note";
    sub.textContent = panel.subtitle;
    const metricLine = document.createElement("p");
    metricLine.className = "widget-stats";
    metricLine.setAttribute("data-testid", `${panel.testid}-metrics`);
    const plotDiv = document.createElement("div");
    plotDiv.className = "widget-plot";
    plotDiv.setAttribute("data-testid", `${panel.testid}-plot`);
    plotDiv.dataset.renderCount = "0";
    card.append(h, sub, metricLine, plotDiv);
    grid.appendChild(card);
    plotDivs[panel.key] = plotDiv;
    metricLines[panel.key] = metricLine;
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

  async function drawPanel(panel: Panel): Promise<void> {
    if (destroyed) return;
    const predicted = predictAllForK(panel.neighborTargets, currentK);
    const r2 = r2Score(panel.observed, predicted);
    const mse = meanSquaredError(panel.observed, predicted);
    metricLines[panel.key]!.textContent = `R2 = ${r2.toFixed(3)}   MSE = ${mse.toFixed(1)}`;

    const scatter = {
      type: "scattergl" as const,
      mode: "markers" as const,
      x: panel.observed,
      y: predicted,
      marker: { color: markerColor, size: 6 },
      hovertemplate: `observed ${data.target.label} %{x}<br>predicted %{y:.1f}<extra></extra>`,
      name: panel.label,
      showlegend: false,
    };
    const diag = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: scatterAxisRange,
      y: scatterAxisRange,
      line: { color: diagColor, width: 2, dash: "dash" as const },
      hoverinfo: "skip" as const,
      name: "Perfect prediction (observed = predicted)",
      showlegend: true,
    };
    const layout = {
      margin: { t: 12, r: 8, b: 44, l: 52 },
      height: 300,
      autosize: true,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.18, font: { size: 9 } },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor, size: 10 },
      xaxis: { title: { text: "Observed" }, gridcolor: gridColor, zeroline: false, range: [...scatterAxisRange] },
      yaxis: {
        title: { text: "Predicted" },
        gridcolor: gridColor,
        zeroline: false,
        range: [...scatterAxisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    };
    await Plotly.react(plotDivs[panel.key]!, [scatter, diag], layout, plotConfig);
    if (destroyed) return;
    const n = Number(plotDivs[panel.key]!.dataset.renderCount ?? "0") + 1;
    plotDivs[panel.key]!.dataset.renderCount = String(n);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    kValue.textContent = String(currentK);
    kInput.value = String(currentK);
    kNumber.value = String(currentK);
    container.dataset.currentK = String(currentK);
    await Promise.all(panels.map((p) => drawPanel(p)));
  }

  function setK(next: number): void {
    currentK = clampK(next, kMax);
    void draw();
  }

  kInput.addEventListener("input", () => {
    kValue.textContent = kInput.value;
    kNumber.value = kInput.value;
  });
  kInput.addEventListener("change", () => setK(Number(kInput.value)));

  kNumber.addEventListener("change", () => {
    const raw = Number(kNumber.value);
    if (!Number.isInteger(raw) || raw < 1 || raw > kMax) {
      kNumber.value = String(currentK);
      return;
    }
    setK(raw);
  });

  void draw();

  return {
    destroy() {
      destroyed = true;
      for (const panel of panels) Plotly.purge(plotDivs[panel.key]!);
    },
  };
}

export const knnAbcComponent: WidgetComponent<KnnAbcConfig, KnnAbcData> = {
  type: "knn-abc",
  parseData: parseKnnAbcData,
  mount,
};
