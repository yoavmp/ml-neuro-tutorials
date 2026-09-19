// Production activity: Exercise 5's "Shrink the Coefficients" activity.
//
// A model select (Linear Regression / Ridge / Lasso) and a log-scale
// regularization-strength (alpha) control, synchronized between a range
// slider and a paired dropdown of exact grid values, drive three coordinated
// displays: observed-vs-predicted validation scatter with the
// perfect-prediction diagonal, a bar chart of a small fixed set of tracked
// standardized coefficients, and a performance summary (train/validation
// MSE, the selected alpha, the best validation alpha, the unregularized
// linear-regression baseline, nonzero-coefficient count, coefficient norm).
// Every (model, alpha) configuration is precomputed offline
// (scripts/export_regularization_widget.py) on one fixed fitting/validation
// split; the outer test set never appears here. No Python kernel, no CDN,
// no test results.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { RegularizationExploreConfig, RegularizationExploreModel } from "../config";
import { sharedAxisRange, formatAlpha, clampAlphaIndex } from "../regularization-explore";
import {
  parseRegularizationExploreData,
  type RegularizationExploreData,
  type RegularizationModelMetrics,
} from "../regularization-explore-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const MODEL_LABELS: Record<RegularizationExploreModel, string> = {
  linear: "Linear Regression",
  ridge: "Ridge",
  lasso: "Lasso",
};

function mount(
  args: MountArgs<RegularizationExploreConfig, RegularizationExploreData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;
  let currentModel: RegularizationExploreModel = config.defaultModel;
  let ridgeIndex = data.models.ridge.bestAlphaIndex;
  let lassoIndex = data.models.lasso.bestAlphaIndex;

  const scatterAxisRange = sharedAxisRange(
    [...data.observedValidation, ...data.models.linear.predictedValidation],
    0.05,
  );

  // --- header -------------------------------------------------------------
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
  cohortLine.setAttribute("data-testid", "regularization-cohort");
  cohortLine.textContent =
    `Fitting set: ${data.split.devSplit.nFit} participants · Validation set: ${data.split.devSplit.nVal} ` +
    `participants (both drawn from the ${data.split.outerHoldout.nTrain}-participant training partition; the ` +
    `${data.split.outerHoldout.nTest}-participant outer test set is untouched by this activity). Feature ` +
    `recipe: ${data.featureRecipe.featureCount} standardized cortical-thickness features, the same as Exercises ` +
    `2 and 4.`;
  container.appendChild(cohortLine);

  // --- controls -------------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const modelGroup = document.createElement("div");
  modelGroup.className = "widget-control";
  const modelLabel = document.createElement("label");
  modelLabel.setAttribute("for", "regularization-model");
  modelLabel.textContent = "Model:";
  const modelSelect = document.createElement("select");
  modelSelect.id = "regularization-model";
  modelSelect.setAttribute("data-testid", "regularization-model-select");
  for (const key of ["linear", "ridge", "lasso"] as const) {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = MODEL_LABELS[key];
    modelSelect.appendChild(opt);
  }
  modelSelect.value = currentModel;
  modelGroup.append(modelLabel, modelSelect);
  controls.appendChild(modelGroup);

  const alphaGroup = document.createElement("div");
  alphaGroup.className = "widget-control";
  const alphaLabel = document.createElement("label");
  alphaLabel.setAttribute("for", "regularization-alpha-slider");
  alphaLabel.textContent = "Regularization strength (alpha, log scale):";
  const alphaSlider = document.createElement("input");
  alphaSlider.type = "range";
  alphaSlider.id = "regularization-alpha-slider";
  alphaSlider.step = "1";
  alphaSlider.setAttribute("data-testid", "regularization-alpha-slider");

  const alphaSelect = document.createElement("select");
  alphaSelect.id = "regularization-alpha-select";
  alphaSelect.setAttribute("data-testid", "regularization-alpha-select");
  alphaSelect.setAttribute("aria-label", "Regularization strength, exact grid value");

  const alphaValue = document.createElement("output");
  alphaValue.setAttribute("for", "regularization-alpha-slider");
  alphaValue.setAttribute("data-testid", "regularization-alpha-value");
  alphaValue.className = "widget-bin-value";

  alphaGroup.append(alphaLabel, alphaSlider, alphaSelect, alphaValue);
  controls.appendChild(alphaGroup);
  container.appendChild(controls);

  const alphaDisabledNote = document.createElement("p");
  alphaDisabledNote.className = "widget-note";
  alphaDisabledNote.setAttribute("data-testid", "regularization-alpha-disabled-note");
  alphaDisabledNote.textContent = config.linearRegressionNote;
  container.appendChild(alphaDisabledNote);

  const metrics = document.createElement("p");
  metrics.className = "widget-stats";
  metrics.setAttribute("data-testid", "regularization-metrics");
  container.appendChild(metrics);

  const predictionsHeading = document.createElement("h2");
  predictionsHeading.className = "widget-subhead";
  predictionsHeading.textContent = "Observed vs predicted (validation set)";
  container.appendChild(predictionsHeading);

  const predictionsPlot = document.createElement("div");
  predictionsPlot.className = "widget-plot";
  predictionsPlot.setAttribute("data-testid", "regularization-predictions-plot");
  predictionsPlot.dataset.renderCount = "0";
  container.appendChild(predictionsPlot);

  const coefHeading = document.createElement("h2");
  coefHeading.className = "widget-subhead";
  coefHeading.textContent = "Largest standardized coefficients";
  container.appendChild(coefHeading);

  const coefNote = document.createElement("p");
  coefNote.className = "widget-note";
  coefNote.setAttribute("data-testid", "regularization-coefficient-note");
  coefNote.textContent = config.coefficientDisplayNote;
  container.appendChild(coefNote);

  const coefPlot = document.createElement("div");
  coefPlot.className = "widget-plot";
  coefPlot.setAttribute("data-testid", "regularization-coefficients-plot");
  coefPlot.dataset.renderCount = "0";
  container.appendChild(coefPlot);

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

  // --- model-specific lookups ----------------------------------------------

  function alphaEntryFor(model: "ridge" | "lasso") {
    return data.models[model];
  }

  function currentIndex(model: "ridge" | "lasso"): number {
    return model === "ridge" ? ridgeIndex : lassoIndex;
  }

  function setIndex(model: "ridge" | "lasso", index: number): void {
    const entry = alphaEntryFor(model);
    const clamped = clampAlphaIndex(index, entry.alphaGrid.length);
    if (model === "ridge") ridgeIndex = clamped;
    else lassoIndex = clamped;
  }

  function currentMetrics(): RegularizationModelMetrics {
    if (currentModel === "linear") return data.models.linear;
    const entry = alphaEntryFor(currentModel);
    return entry.perAlpha[currentIndex(currentModel)]!;
  }

  function refreshAlphaControls(): void {
    const isLinear = currentModel === "linear";
    alphaSlider.disabled = isLinear;
    alphaSelect.disabled = isLinear;
    alphaDisabledNote.hidden = !isLinear;

    if (currentModel === "linear") {
      alphaValue.textContent = "not applicable";
      return;
    }
    const entry = alphaEntryFor(currentModel);
    const idx = currentIndex(currentModel);
    alphaSlider.min = "0";
    alphaSlider.max = String(entry.alphaGrid.length - 1);
    alphaSlider.value = String(idx);
    alphaSlider.setAttribute(
      "aria-label",
      `Regularization strength (alpha), from ${formatAlpha(entry.alphaGrid[0]!)} to ` +
        `${formatAlpha(entry.alphaGrid[entry.alphaGrid.length - 1]!)}, log scale`,
    );

    alphaSelect.replaceChildren();
    entry.alphaGrid.forEach((a, i) => {
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = `alpha = ${formatAlpha(a)}`;
      alphaSelect.appendChild(opt);
    });
    alphaSelect.value = String(idx);
    alphaValue.textContent = `alpha = ${formatAlpha(entry.alphaGrid[idx]!)}`;
  }

  // --- drawing ---------------------------------------------------------

  async function drawPredictions(): Promise<void> {
    if (destroyed) return;
    const m = currentMetrics();
    const scatter = {
      type: "scattergl" as const,
      mode: "markers" as const,
      x: data.observedValidation,
      y: m.predictedValidation,
      marker: { color: theme.markerPrimary, size: 6 },
      hovertemplate: `observed ${data.target.label} %{x}<br>predicted %{y:.1f}<extra></extra>`,
      name: "validation participants",
      showlegend: false,
    };
    const diag = {
      type: "scatter" as const,
      mode: "lines" as const,
      x: scatterAxisRange,
      y: scatterAxisRange,
      line: { color: theme.diagonalLine, width: 2, dash: "dash" as const },
      hoverinfo: "skip" as const,
      name: "Perfect prediction (observed = predicted)",
      showlegend: true,
    };
    const layout = buildPlotLayout(theme, {
      height: 340,
      showlegend: true,
      legend: { orientation: "h" as const, y: 1.12 },
      xaxis: { title: { text: `Observed ${data.target.label}` }, range: [...scatterAxisRange] },
      yaxis: {
        title: { text: `Predicted ${data.target.label} (validation)` },
        range: [...scatterAxisRange],
        scaleanchor: "x" as const,
        scaleratio: 1,
      },
    });
    await Plotly.react(predictionsPlot, [scatter, diag], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(predictionsPlot.dataset.renderCount ?? "0") + 1;
    predictionsPlot.dataset.renderCount = String(n);
  }

  async function drawCoefficients(): Promise<void> {
    if (destroyed) return;
    const m = currentMetrics();
    const pairs = data.trackedFeatures
      .map((feature, i) => ({ feature, value: m.coefficients[i]! }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
    const positive = theme.dark ? "#8fb8da" : "#2a6f9e";
    const negative = theme.dark ? "#f0915c" : "#b5622f";
    const bar = {
      type: "bar" as const,
      orientation: "h" as const,
      x: pairs.map((p) => p.value),
      y: pairs.map((p) => p.feature),
      marker: { color: pairs.map((p) => (p.value >= 0 ? positive : negative)) },
      hovertemplate: "%{y}: %{x:.3f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 40 * pairs.length + 60,
      margin: { l: 150 },
      xaxis: { title: { text: "Standardized coefficient" } },
      yaxis: { title: { text: "" }, automargin: true },
    });
    await Plotly.react(coefPlot, [bar], layout, PLOT_CONFIG);
    if (destroyed) return;
    const n = Number(coefPlot.dataset.renderCount ?? "0") + 1;
    coefPlot.dataset.renderCount = String(n);
  }

  function drawMetrics(): void {
    const m = currentMetrics();
    const baseline = data.models.linear.valMSE;
    let alphaText = "not applicable (Linear Regression has no alpha)";
    let bestAlphaText = "";
    if (currentModel !== "linear") {
      const entry = alphaEntryFor(currentModel);
      const idx = currentIndex(currentModel);
      alphaText = formatAlpha(entry.alphaGrid[idx]!);
      bestAlphaText = `  ·  best validation alpha = ${formatAlpha(entry.alphaGrid[entry.bestAlphaIndex]!)}`;
    }
    metrics.textContent =
      `${MODEL_LABELS[currentModel]}  ·  alpha = ${alphaText}${bestAlphaText}  ·  ` +
      `training MSE = ${m.trainMSE.toFixed(1)}  ·  validation MSE = ${m.valMSE.toFixed(1)} ` +
      `(lower is better)  ·  unregularized linear-regression baseline validation MSE = ${baseline.toFixed(1)}  ·  ` +
      `nonzero coefficients = ${m.nonzeroCount} of ${data.featureRecipe.featureCount}  ·  ` +
      `coefficient norm = ${m.coefNorm.toFixed(1)}`;
    container.dataset.currentModel = currentModel;
    container.dataset.valMSE = m.valMSE.toFixed(4);
    container.dataset.nonzeroCount = String(m.nonzeroCount);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    refreshAlphaControls();
    drawMetrics();
    await Promise.all([drawPredictions(), drawCoefficients()]);
  }

  modelSelect.addEventListener("change", () => {
    currentModel = modelSelect.value as RegularizationExploreModel;
    void draw();
  });

  alphaSlider.addEventListener("input", () => {
    if (currentModel === "linear") return;
    alphaValue.textContent = `alpha = ${formatAlpha(alphaEntryFor(currentModel).alphaGrid[Number(alphaSlider.value)]!)}`;
    alphaSelect.value = alphaSlider.value;
  });
  alphaSlider.addEventListener("change", () => {
    if (currentModel === "linear") return;
    setIndex(currentModel, Number(alphaSlider.value));
    void draw();
  });
  alphaSelect.addEventListener("change", () => {
    if (currentModel === "linear") return;
    setIndex(currentModel, Number(alphaSelect.value));
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
      Plotly.purge(predictionsPlot);
      Plotly.purge(coefPlot);
    },
  };
}

export const regularizationExploreComponent: WidgetComponent<
  RegularizationExploreConfig,
  RegularizationExploreData
> = {
  type: "regularization-explore",
  parseData: parseRegularizationExploreData,
  mount,
};
