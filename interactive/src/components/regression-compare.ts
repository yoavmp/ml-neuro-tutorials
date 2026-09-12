// Production activity: Exercise II feature-set comparison.
//
// Two independent panels (Model A, Model B). Each picks a measurement subset and
// an anatomical ROI bundle; the component looks the resulting recipe up in the
// pre-computed catalog (scripts/export_regression_catalog.py) and draws observed
// vs out-of-fold predicted FIQ with a perfect-prediction diagonal, plus the
// cross-validated R2 / MSE, the participant count, and the feature count. Both
// panels share identical axis limits so the comparison is visually fair. Every
// catalog entry uses the same cohort and the same deterministic folds, so a
// control change is a genuine re-computation, not a relabelling. No Python
// kernel, no CDN, no training scores.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { RegressionCompareConfig } from "../config";
import {
  catalogKey,
  r2Score,
  meanSquaredError,
  sharedAxisRange,
} from "../regression-compare";
import {
  parseRegressionCatalog,
  type RegressionCatalog,
  type RegressionModelEntry,
} from "../regression-compare-data";

function prefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

interface PanelState {
  measuresKey: string;
  bundle: string;
}

function mount(args: MountArgs<RegressionCompareConfig, RegressionCatalog>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  // --- config x data consistency -------------------------------------------
  const subsetByKey = new Map(config.measurementSubsets.map((s) => [s.measures.join("+"), s]));
  const bundleLabel = new Map(config.bundles.map((b) => [b.key, b.label]));
  const missing: string[] = [];
  for (const b of config.bundles) {
    if (!data.bundles[b.key]) missing.push(`bundle "${b.key}"`);
  }
  for (const s of config.measurementSubsets) {
    for (const m of s.measures) if (!data.measures[m]) missing.push(`measure "${m}"`);
  }
  for (const [, s] of subsetByKey) {
    for (const b of config.bundles) {
      if (!data.models.some((mdl) => mdl.key === catalogKey({ bundle: b.key, measures: s.measures }))) {
        missing.push(`catalog entry ${b.key} x ${s.measures.join("+")}`);
      }
    }
  }
  if (missing.length > 0) {
    throw new Error(`The catalog is missing: ${[...new Set(missing)].join(", ")}.`);
  }

  const dark = prefersDark();
  const axisColor = dark ? "#c9c9c9" : "#333333";
  const gridColor = dark ? "#3a3a3a" : "#e2e2e2";
  const markerColor = dark ? "rgba(120,170,210,0.55)" : "rgba(42,111,158,0.5)";
  const diagColor = dark ? "#d98b5f" : "#b5622f";
  const plotConfig = { displayModeBar: false, responsive: true };

  // Shared axis range: observed plus every enabled model's predictions.
  const allValues: number[] = [...data.observed];
  for (const m of data.models) if (!m.disabled && m.predicted) allValues.push(...m.predicted);
  const axisRange = sharedAxisRange(allValues, 0.05);

  let destroyed = false;

  // --- header -------------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const lit = document.createElement("details");
  lit.className = "widget-note";
  lit.setAttribute("data-testid", "regression-literature-note");
  const litSummary = document.createElement("summary");
  litSummary.textContent = "Where these ROI bundles come from";
  const litBody = document.createElement("p");
  litBody.textContent = config.literatureNote;
  lit.append(litSummary, litBody);
  container.appendChild(lit);

  const cohortLine = document.createElement("p");
  cohortLine.className = "widget-stats";
  cohortLine.setAttribute("data-testid", "regression-cohort");
  cohortLine.textContent =
    `Every configuration is scored on the same ${data.cohort.n} participants ` +
    `(${data.cohort.requirement}) with the same ${data.crossValidation.nSplits} folds ` +
    `(${data.crossValidation.randomState === 0 ? "seed 0" : `seed ${data.crossValidation.randomState}`}). ` +
    `${data.cohort.diagnosisNote}.`;
  container.appendChild(cohortLine);

  const panelsWrap = document.createElement("div");
  panelsWrap.className = "widget-compare-grid";
  container.appendChild(panelsWrap);

  const selectionNote = document.createElement("p");
  selectionNote.className = "widget-empty";
  selectionNote.setAttribute("data-testid", "regression-selection-bias");
  selectionNote.textContent = config.selectionBiasNote;
  container.appendChild(selectionNote);

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

  // --- one panel --------------------------------------------------------
  function buildPanel(name: "A" | "B", initial: PanelState) {
    const state: PanelState = { ...initial };

    const panel = document.createElement("section");
    panel.className = "widget-compare-panel";
    panel.setAttribute("data-testid", `regression-panel-${name}`);

    const title = document.createElement("h2");
    title.className = "widget-subhead";
    title.textContent = `Model ${name}`;
    panel.appendChild(title);

    const controls = document.createElement("div");
    controls.className = "widget-controls";

    const measGroup = document.createElement("div");
    measGroup.className = "widget-control";
    const measLabel = document.createElement("label");
    measLabel.setAttribute("for", `regression-${name}-measures`);
    measLabel.textContent = "Measurement:";
    const measSelect = document.createElement("select");
    measSelect.id = `regression-${name}-measures`;
    measSelect.setAttribute("data-testid", `regression-${name}-measures`);
    for (const s of config.measurementSubsets) {
      const opt = document.createElement("option");
      opt.value = s.measures.join("+");
      opt.textContent = s.label;
      measSelect.appendChild(opt);
    }
    measSelect.value = state.measuresKey;
    measGroup.append(measLabel, measSelect);

    const bundleGroup = document.createElement("div");
    bundleGroup.className = "widget-control";
    const bundleLabelEl = document.createElement("label");
    bundleLabelEl.setAttribute("for", `regression-${name}-bundle`);
    bundleLabelEl.textContent = "ROI bundle:";
    const bundleSelect = document.createElement("select");
    bundleSelect.id = `regression-${name}-bundle`;
    bundleSelect.setAttribute("data-testid", `regression-${name}-bundle`);
    for (const b of config.bundles) {
      const opt = document.createElement("option");
      opt.value = b.key;
      opt.textContent = b.label;
      bundleSelect.appendChild(opt);
    }
    bundleSelect.value = state.bundle;
    bundleGroup.append(bundleLabelEl, bundleSelect);

    controls.append(measGroup, bundleGroup);
    panel.appendChild(controls);

    const metrics = document.createElement("p");
    metrics.className = "widget-stats";
    metrics.setAttribute("data-testid", `regression-${name}-metrics`);
    panel.appendChild(metrics);

    const plot = document.createElement("div");
    plot.className = "widget-plot";
    plot.setAttribute("data-testid", `regression-${name}-plot`);
    plot.dataset.renderCount = "0";
    panel.appendChild(plot);

    const disabledMsg = document.createElement("p");
    disabledMsg.className = "widget-empty";
    disabledMsg.setAttribute("data-testid", `regression-${name}-disabled`);
    disabledMsg.hidden = true;
    panel.appendChild(disabledMsg);

    const roiDisclosure = document.createElement("details");
    roiDisclosure.className = "widget-note";
    const roiSummary = document.createElement("summary");
    roiSummary.setAttribute("data-testid", `regression-${name}-roi-summary`);
    const roiList = document.createElement("p");
    roiList.className = "widget-roi-list";
    roiList.setAttribute("data-testid", `regression-${name}-roi-list`);
    roiDisclosure.append(roiSummary, roiList);
    panel.appendChild(roiDisclosure);

    function currentModel(): RegressionModelEntry {
      const key = catalogKey({ bundle: state.bundle, measures: state.measuresKey.split("+") });
      const model = data.models.find((m) => m.key === key);
      if (!model) throw new Error(`No catalog entry for ${key}`);
      return model;
    }

    async function draw(): Promise<void> {
      if (destroyed) return;
      state.measuresKey = measSelect.value;
      state.bundle = bundleSelect.value;
      const model = currentModel();
      const bundleInfo = data.bundles[state.bundle]!;
      const measLabels = state.measuresKey
        .split("+")
        .map((m) => data.measures[m]?.label ?? m)
        .join(" + ");

      roiSummary.textContent =
        `${bundleInfo.rois.length} ROIs x ${state.measuresKey.split("+").length} measure` +
        `${state.measuresKey.includes("+") ? "s" : ""} x 2 hemispheres = ${model.featureCount} features`;
      roiList.textContent = bundleInfo.rois.join(", ");

      panel.dataset.modelKey = model.key;
      panel.dataset.featureCount = String(model.featureCount);
      panel.dataset.disabled = String(Boolean(model.disabled));

      if (model.disabled || !model.predicted) {
        Plotly.purge(plot);
        plot.hidden = true;
        disabledMsg.hidden = false;
        disabledMsg.textContent = model.reason ?? "This combination is not available.";
        metrics.textContent =
          `${bundleLabel.get(state.bundle) ?? state.bundle} - ${measLabels}: ` +
          `${model.featureCount} features, not fitted.`;
        panel.dataset.r2 = "";
        panel.dataset.mse = "";
        const n0 = Number(plot.dataset.renderCount ?? "0") + 1;
        plot.dataset.renderCount = String(n0);
        return;
      }

      disabledMsg.hidden = true;
      plot.hidden = false;

      const r2 = r2Score(data.observed, model.predicted);
      const mse = meanSquaredError(data.observed, model.predicted);
      const rmse = Math.sqrt(mse);
      metrics.textContent =
        `Out-of-sample R2 = ${r2.toFixed(3)}  ·  CV MSE = ${mse.toFixed(1)} ` +
        `(RMSE ${rmse.toFixed(1)} ${data.target.unit})  ·  n = ${data.cohort.n}  ·  ` +
        `${model.featureCount} features` +
        (r2 < 0 ? "  ·  below 0: worse than predicting the mean" : "");
      panel.dataset.r2 = r2.toFixed(4);
      panel.dataset.mse = mse.toFixed(3);

      const scatter = {
        type: "scattergl" as const,
        mode: "markers" as const,
        x: data.observed,
        y: model.predicted,
        marker: { color: markerColor, size: 6 },
        hovertemplate:
          `observed ${data.target.label} %{x}<br>predicted %{y:.1f}<extra></extra>`,
        name: "participants",
      };
      const diag = {
        type: "scatter" as const,
        mode: "lines" as const,
        x: axisRange,
        y: axisRange,
        line: { color: diagColor, width: 2, dash: "dash" as const },
        hoverinfo: "skip" as const,
        name: "perfect prediction",
      };
      const layout = {
        margin: { t: 12, r: 12, b: 48, l: 56 },
        height: 320,
        autosize: true,
        showlegend: false,
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: axisColor },
        xaxis: {
          title: { text: `Observed ${data.target.label}` },
          gridcolor: gridColor,
          zeroline: false,
          range: [...axisRange],
        },
        yaxis: {
          title: { text: `Predicted ${data.target.label} (out of fold)` },
          gridcolor: gridColor,
          zeroline: false,
          range: [...axisRange],
          scaleanchor: "x" as const,
          scaleratio: 1,
        },
      };
      await Plotly.react(plot, [scatter, diag], layout, plotConfig);
      if (destroyed) return;
      const n = Number(plot.dataset.renderCount ?? "0") + 1;
      plot.dataset.renderCount = String(n);
    }

    measSelect.addEventListener("change", () => void draw());
    bundleSelect.addEventListener("change", () => void draw());

    return { panel, draw };
  }

  const panelA = buildPanel("A", {
    measuresKey: config.defaultA.measures.join("+"),
    bundle: config.defaultA.bundle,
  });
  const panelB = buildPanel("B", {
    measuresKey: config.defaultB.measures.join("+"),
    bundle: config.defaultB.bundle,
  });
  panelsWrap.append(panelA.panel, panelB.panel);

  void panelA.draw();
  void panelB.draw();

  return {
    destroy() {
      destroyed = true;
      for (const p of [panelA, panelB]) {
        const node = p.panel.querySelector<HTMLElement>(".widget-plot");
        if (node) Plotly.purge(node);
      }
    },
  };
}

export const regressionCompareComponent: WidgetComponent<
  RegressionCompareConfig,
  RegressionCatalog
> = {
  type: "regression-compare",
  parseData: parseRegressionCatalog,
  mount,
};
