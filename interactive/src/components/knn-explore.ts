// Production activity: Exercise 3's "vary k" KNN exploration.
//
// A k slider AND a synchronized numeric input (WP14 §4.5) drive standardized
// KNN regression for age refit at that k: fitting R2/MSE, validation R2/MSE,
// an observed-vs-predicted validation scatter, and the full fitting/
// validation error curve with the current k highlighted. Three deterministic
// training-sample tabs (WP14 §4.8) switch which bootstrap resample of the
// fitting pool feeds that scatter, alongside an empirical training-sample-
// sensitivity ("variance") proxy and a binned-calibration bias-like proxy
// (WP14 §4.9) computed across all three samples. Predictions come from the
// precomputed neighbour-ordered target arrays (scripts/export_knn_explore_data.py)
// via client-side prefix means -- a genuine recomputation, not a relabelling.
// No Python kernel, no CDN, no brain features, no participant identifiers.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { KnnExploreConfig } from "../config";
import {
  sharedAxisRange,
  predictAllForK,
  varianceProxy,
  calibrationSlope,
  ensembleMeanForK,
} from "../knn-explore";
import { parseKnnExploreData, type KnnExploreData } from "../knn-explore-data";

const SAMPLE_LABELS = ["A", "B", "C"] as const;
type SampleLabel = (typeof SAMPLE_LABELS)[number];

function prefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function resolveDefaultK(config: KnnExploreConfig, data: KnnExploreData): number {
  return config.defaultK === "validation-optimal" ? data.validationOptimalK : config.defaultK;
}

function clampK(value: number, nFit: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(nFit, Math.max(1, Math.round(value)));
}

function mount(args: MountArgs<KnnExploreConfig, KnnExploreData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const nFit = data.split.nFit;
  const defaultK = resolveDefaultK(config, data);
  if (defaultK < 1 || defaultK > nFit) {
    throw new Error(`config.defaultK resolved to ${defaultK}, outside [1, ${nFit}]`);
  }

  const dark = prefersDark();
  const axisColor = dark ? "#c9c9c9" : "#333333";
  const gridColor = dark ? "#3a3a3a" : "#e2e2e2";
  const markerColor = dark ? "rgba(120,170,210,0.55)" : "rgba(42,111,158,0.5)";
  const diagColor = dark ? "#d98b5f" : "#b5622f";
  const fitCurveColor = dark ? "#8fb8da" : "#2a6f9e";
  const valCurveColor = dark ? "#f0915c" : "#b5622f";
  const markerLineColor = dark ? "#e2c48f" : "#8f5a1a";
  const plotConfig = { displayModeBar: false, responsive: true };

  const scatterAxisRange = sharedAxisRange([...data.observedValidation, ...data.observedFitting], 0.05);
  const sampleMatrices: Record<SampleLabel, readonly (readonly number[])[]> = {
    A: data.trainingSamples.A.neighborTargetsByProximity,
    B: data.trainingSamples.B.neighborTargetsByProximity,
    C: data.trainingSamples.C.neighborTargetsByProximity,
  };

  let destroyed = false;
  let currentK = defaultK;
  let currentSample: SampleLabel = "A";

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const dimNote = document.createElement("details");
  dimNote.className = "widget-note";
  const dimSummary = document.createElement("summary");
  dimSummary.textContent = "Why not just use every feature?";
  const dimBody = document.createElement("p");
  dimBody.textContent = config.curseOfDimensionalityNote;
  dimNote.append(dimSummary, dimBody);
  container.appendChild(dimNote);

  const kComplexityNote = document.createElement("p");
  kComplexityNote.className = "widget-note";
  kComplexityNote.setAttribute("data-testid", "knn-k-complexity-note");
  kComplexityNote.textContent = config.kComplexityNote;
  container.appendChild(kComplexityNote);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "knn-cohort");
  cohortLine.textContent =
    `Fitting set: ${data.split.nFit} participants · Validation set: ${data.split.nValidation} ` +
    `participants (both drawn from Exercise 2's own ${data.split.nOuterTrain}-participant training ` +
    `partition; the outer test set is untouched by this activity). Feature recipe: ` +
    `${data.featureRecipe.featureCount} standardized cortical-thickness features, the same as ` +
    `Exercise 2's canonical recipe.`;
  container.appendChild(cohortLine);

  // --- controls: slider + synchronized numeric input (WP14 §4.5) --------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const kGroup = document.createElement("div");
  kGroup.className = "widget-control";
  const kLabel = document.createElement("label");
  kLabel.setAttribute("for", "knn-k");
  kLabel.textContent = "Number of neighbours (k):";
  const kInput = document.createElement("input");
  kInput.id = "knn-k";
  kInput.type = "range";
  kInput.min = "1";
  kInput.max = String(nFit);
  kInput.step = "1";
  kInput.value = String(defaultK);
  kInput.setAttribute("data-testid", "knn-k-slider");
  kInput.setAttribute("aria-label", `Number of neighbours, from 1 to ${nFit}`);

  const kNumber = document.createElement("input");
  kNumber.type = "number";
  kNumber.id = "knn-k-number";
  kNumber.min = "1";
  kNumber.max = String(nFit);
  kNumber.step = "1";
  kNumber.value = String(defaultK);
  kNumber.setAttribute("data-testid", "knn-k-number");
  kNumber.setAttribute("aria-label", `Number of neighbours, exact value, from 1 to ${nFit}`);
  kNumber.className = "widget-number-input";

  const kValue = document.createElement("output");
  kValue.setAttribute("for", "knn-k");
  kValue.setAttribute("data-testid", "knn-k-value");
  kValue.className = "widget-bin-value";
  kValue.textContent = String(defaultK);
  kGroup.append(kLabel, kInput, kNumber, kValue);
  controls.appendChild(kGroup);
  container.appendChild(controls);

  const metrics = document.createElement("p");
  metrics.className = "widget-stats";
  metrics.setAttribute("data-testid", "knn-metrics");
  container.appendChild(metrics);

  const scatterHeading = document.createElement("h2");
  scatterHeading.className = "widget-subhead";
  scatterHeading.textContent = "Observed vs predicted (validation set)";
  container.appendChild(scatterHeading);

  // --- training-sample tabs (WP14 §4.8) ----------------------------------
  const sampleTabs = document.createElement("div");
  sampleTabs.className = "widget-tabs";
  sampleTabs.setAttribute("role", "tablist");
  sampleTabs.setAttribute("aria-label", "Training sample");
  const tabButtons: Record<SampleLabel, HTMLButtonElement> = {} as Record<SampleLabel, HTMLButtonElement>;
  for (const label of SAMPLE_LABELS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = `Training sample ${label}`;
    btn.setAttribute("data-testid", `knn-sample-tab-${label}`);
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", label === currentSample ? "true" : "false");
    btn.addEventListener("click", () => {
      currentSample = label;
      for (const l of SAMPLE_LABELS) tabButtons[l].setAttribute("aria-selected", String(l === currentSample));
      void drawScatter();
    });
    tabButtons[label] = btn;
    sampleTabs.appendChild(btn);
  }
  container.appendChild(sampleTabs);

  const sampleNote = document.createElement("p");
  sampleNote.className = "widget-note";
  sampleNote.textContent = config.trainingSampleInstructions;
  container.appendChild(sampleNote);

  const scatterPlot = document.createElement("div");
  scatterPlot.className = "widget-plot";
  scatterPlot.setAttribute("data-testid", "knn-scatter-plot");
  scatterPlot.dataset.renderCount = "0";
  container.appendChild(scatterPlot);

  const curveHeading = document.createElement("h2");
  curveHeading.className = "widget-subhead";
  curveHeading.textContent = "Fitting and validation error vs k";
  container.appendChild(curveHeading);

  const curvePlot = document.createElement("div");
  curvePlot.className = "widget-plot";
  curvePlot.setAttribute("data-testid", "knn-curve-plot");
  curvePlot.dataset.renderCount = "0";
  container.appendChild(curvePlot);

  // --- variance proxy + bias-like proxy (WP14 §4.8 / §4.9) ---------------
  const varianceHeading = document.createElement("h2");
  varianceHeading.className = "widget-subhead";
  varianceHeading.textContent = "How much do predictions change across training samples?";
  container.appendChild(varianceHeading);

  const varianceLine = document.createElement("p");
  varianceLine.className = "widget-stats";
  varianceLine.setAttribute("data-testid", "knn-variance-proxy");
  container.appendChild(varianceLine);

  const varianceNote = document.createElement("p");
  varianceNote.className = "widget-note";
  varianceNote.textContent = config.varianceProxyNote;
  container.appendChild(varianceNote);

  const biasHeading = document.createElement("h2");
  biasHeading.className = "widget-subhead";
  biasHeading.textContent = "Binned calibration: ensemble-mean prediction vs observed age";
  container.appendChild(biasHeading);

  const biasLine = document.createElement("p");
  biasLine.className = "widget-stats";
  biasLine.setAttribute("data-testid", "knn-bias-proxy");
  container.appendChild(biasLine);

  const biasPlot = document.createElement("div");
  biasPlot.className = "widget-plot";
  biasPlot.setAttribute("data-testid", "knn-bias-plot");
  biasPlot.dataset.renderCount = "0";
  container.appendChild(biasPlot);

  const biasNote = document.createElement("p");
  biasNote.className = "widget-note";
  biasNote.textContent = config.biasProxyNote;
  container.appendChild(biasNote);

  const endpoints = document.createElement("div");
  endpoints.className = "widget-note";
  const k1p = document.createElement("p");
  k1p.setAttribute("data-testid", "knn-endpoint-k1");
  k1p.innerHTML = `<strong>k = 1:</strong> ${config.endpointNoteK1}`;
  const kMaxP = document.createElement("p");
  kMaxP.setAttribute("data-testid", "knn-endpoint-kmax");
  kMaxP.innerHTML = `<strong>k = ${nFit} (every fitting participant):</strong> ${config.endpointNoteKMax}`;
  endpoints.append(k1p, kMaxP);
  container.appendChild(endpoints);

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

  // --- drawing ------------------------------------------------------------

  async function drawScatter(): Promise<void> {
    if (destroyed) return;
    const predicted = predictAllForK(sampleMatrices[currentSample], currentK);
    const scatter = {
      type: "scattergl" as const,
      mode: "markers" as const,
      x: data.observedValidation,
      y: predicted,
      marker: { color: markerColor, size: 6 },
      hovertemplate: `observed ${data.target.label} %{x}<br>predicted %{y:.1f}<extra></extra>`,
      name: "validation participants",
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
      margin: { t: 12, r: 12, b: 48, l: 56 },
      height: 340,
      autosize: true,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.12 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor },
      xaxis: {
        title: { text: `Observed ${data.target.label}` },
        gridcolor: gridColor,
        zeroline: false,
        range: [...scatterAxisRange],
      },
      yaxis: {
        title: { text: `Predicted ${data.target.label} (validation, training sample ${currentSample})` },
        gridcolor: gridColor,
        zeroline: false,
        range: [...scatterAxisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    };
    await Plotly.react(scatterPlot, [scatter, diag], layout, plotConfig);
    if (destroyed) return;
    const n = Number(scatterPlot.dataset.renderCount ?? "0") + 1;
    scatterPlot.dataset.renderCount = String(n);
  }

  async function drawCurve(): Promise<void> {
    if (destroyed) return;
    const kAxis = data.curve.k;
    const fitTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: kAxis,
      y: data.curve.fitMSE,
      line: { color: fitCurveColor, width: 2 },
      name: "fitting MSE",
      hovertemplate: "k=%{x}<br>fitting MSE %{y:.1f}<extra></extra>",
    };
    const valTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: kAxis,
      y: data.curve.valMSE,
      line: { color: valCurveColor, width: 2 },
      name: "validation MSE",
      hovertemplate: "k=%{x}<br>validation MSE %{y:.1f}<extra></extra>",
    };
    const currentMarker = {
      type: "scatter" as const,
      mode: "markers" as const,
      x: [currentK],
      y: [data.curve.valMSE[currentK - 1]],
      marker: { color: markerLineColor, size: 11, symbol: "line-ns-open", line: { width: 3, color: markerLineColor } },
      name: "current k",
      hoverinfo: "skip" as const,
      showlegend: false,
    };
    const layout = {
      margin: { t: 12, r: 12, b: 48, l: 56 },
      height: 320,
      autosize: true,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.15 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor },
      xaxis: {
        title: { text: "k (number of neighbours, log scale)" },
        type: "log" as const,
        gridcolor: gridColor,
        zeroline: false,
      },
      yaxis: {
        title: { text: `Mean squared error (${data.target.unit}²)` },
        gridcolor: gridColor,
        zeroline: false,
        rangemode: "tozero" as const,
      },
      shapes: [
        {
          type: "line" as const,
          x0: currentK,
          x1: currentK,
          y0: 0,
          y1: 1,
          xref: "x" as const,
          yref: "paper" as const,
          line: { color: markerLineColor, width: 1.5, dash: "dot" as const },
        },
      ],
    };
    await Plotly.react(curvePlot, [fitTrace, valTrace, currentMarker], layout, plotConfig);
    if (destroyed) return;
    const n = Number(curvePlot.dataset.renderCount ?? "0") + 1;
    curvePlot.dataset.renderCount = String(n);
  }

  function drawVarianceAndBias(): void {
    const samples = SAMPLE_LABELS.map((l) => sampleMatrices[l]);
    const perSamplePredictions = samples.map((s) => predictAllForK(s, currentK));
    const proxy = varianceProxy(perSamplePredictions);
    varianceLine.textContent =
      `Training-sample sensitivity proxy at k = ${currentK}: ${proxy.toFixed(2)} ${data.target.unit} ` +
      `(mean, across validation participants, of the SD of the three training samples' predictions).`;

    const ensemble = ensembleMeanForK(samples, currentK);
    const slope = calibrationSlope(data.observedValidation, ensemble);
    biasLine.textContent =
      `Calibration slope at k = ${currentK}: ${slope.toFixed(2)} ` +
      `(1.0 = predictions track observed age closely; 0.0 = predictions have flattened to a constant).`;

    // 6 equal-width bins across the observed validation age range.
    const NBINS = 6;
    const obsMin = Math.min(...data.observedValidation);
    const obsMax = Math.max(...data.observedValidation);
    const width = (obsMax - obsMin) / NBINS || 1;
    const binObs: number[] = new Array(NBINS).fill(0);
    const binPred: number[] = new Array(NBINS).fill(0);
    const binCount: number[] = new Array(NBINS).fill(0);
    for (let i = 0; i < data.observedValidation.length; i += 1) {
      const obs = data.observedValidation[i]!;
      let bin = Math.floor((obs - obsMin) / width);
      if (bin >= NBINS) bin = NBINS - 1;
      if (bin < 0) bin = 0;
      binObs[bin]! += obs;
      binPred[bin]! += ensemble[i]!;
      binCount[bin]! += 1;
    }
    const binMeanObs: number[] = [];
    const binMeanPred: number[] = [];
    for (let b = 0; b < NBINS; b += 1) {
      if (binCount[b]! > 0) {
        binMeanObs.push(binObs[b]! / binCount[b]!);
        binMeanPred.push(binPred[b]! / binCount[b]!);
      }
    }

    const binTrace = {
      type: "scatter" as const,
      mode: "markers+lines" as const,
      x: binMeanObs,
      y: binMeanPred,
      marker: { color: markerColor, size: 9 },
      line: { color: markerColor, width: 1.5 },
      name: "binned ensemble-mean prediction",
      showlegend: true,
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
      margin: { t: 12, r: 12, b: 48, l: 56 },
      height: 300,
      autosize: true,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.18 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor },
      xaxis: { title: { text: `Observed ${data.target.label} (bin mean)` }, gridcolor: gridColor, zeroline: false, range: [...scatterAxisRange] },
      yaxis: {
        title: { text: "Ensemble-mean predicted (bin mean)" },
        gridcolor: gridColor,
        zeroline: false,
        range: [...scatterAxisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    };
    void Plotly.react(biasPlot, [binTrace, diag], layout, plotConfig).then(() => {
      if (destroyed) return;
      const n = Number(biasPlot.dataset.renderCount ?? "0") + 1;
      biasPlot.dataset.renderCount = String(n);
    });
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    kValue.textContent = String(currentK);
    kInput.value = String(currentK);
    kNumber.value = String(currentK);

    const fitR2 = data.curve.fitR2[currentK - 1]!;
    const fitMSE = data.curve.fitMSE[currentK - 1]!;
    const valR2 = data.curve.valR2[currentK - 1]!;
    const valMSE = data.curve.valMSE[currentK - 1]!;

    metrics.textContent =
      `k = ${currentK}  ·  fitting R2 = ${fitR2.toFixed(3)} (MSE ${fitMSE.toFixed(1)})  ·  ` +
      `validation R2 = ${valR2.toFixed(3)} (MSE ${valMSE.toFixed(1)}, RMSE ${Math.sqrt(valMSE).toFixed(1)} ` +
      `${data.target.unit})`;
    container.dataset.currentK = String(currentK);
    container.dataset.valR2 = valR2.toFixed(4);
    container.dataset.fitR2 = fitR2.toFixed(4);
    container.dataset.currentSample = currentSample;

    drawVarianceAndBias();
    await Promise.all([drawScatter(), drawCurve()]);
  }

  function setK(next: number): void {
    currentK = clampK(next, nFit);
    void draw();
  }

  kInput.addEventListener("input", () => {
    kValue.textContent = kInput.value;
    kNumber.value = kInput.value;
  });
  kInput.addEventListener("change", () => setK(Number(kInput.value)));

  kNumber.addEventListener("change", () => {
    const raw = Number(kNumber.value);
    if (!Number.isInteger(raw) || raw < 1 || raw > nFit) {
      // reject invalid/non-integer input rather than silently producing an
      // invalid model (WP14 §4.5): restore the last valid k.
      kNumber.value = String(currentK);
      return;
    }
    setK(raw);
  });

  void draw();

  return {
    destroy() {
      destroyed = true;
      Plotly.purge(scatterPlot);
      Plotly.purge(curvePlot);
      Plotly.purge(biasPlot);
    },
  };
}

export const knnExploreComponent: WidgetComponent<KnnExploreConfig, KnnExploreData> = {
  type: "knn-explore",
  parseData: parseKnnExploreData,
  mount,
};
