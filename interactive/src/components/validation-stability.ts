// Production activity: Exercise 4 "One Split or Several Folds?" (WP27).
//
// A combined single-split-instability + fixed-model cross-validation
// activity. Sample size, split seed, and fold count are all discrete,
// predeclared, audited controls (scripts/wp27_validation_audit.py) -- no
// value is computed in the browser. The participant pool for each sample
// size is a fixed, nested prefix of one master permutation of the eligible
// cohort, so changing the seed re-partitions the SAME pool of participants
// rather than drawing a new sample -- see the data file's `source` /
// scripts/wp27_validation_audit.py docstring. KNN's `k` is fixed throughout:
// this activity evaluates a model, it does not tune one.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ValidationStabilityConfig } from "../config";
import {
  parseValidationStabilityData,
  type ValidationStabilityData,
  type SizeEntry,
} from "../validation-stability-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function mean(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}
function range(xs: number[]): number {
  return Math.max(...xs) - Math.min(...xs);
}

function mount(
  args: MountArgs<ValidationStabilityConfig, ValidationStabilityData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const sizeByKey = new Map(data.sizes.map((s) => [s.sizeKey, s]));
  const missingSizes = config.sizeKeys.filter((k) => !sizeByKey.has(k));
  if (missingSizes.length > 0) {
    throw new Error(`The data file is missing sample size(s): ${missingSizes.join(", ")}.`);
  }
  if (!data.foldOptions.includes(config.defaultFolds)) {
    throw new Error(`config.defaultFolds ${config.defaultFolds} is not one of the audited fold options.`);
  }

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  let sizeKey = config.defaultSizeKey;
  let seed = config.defaultSeed;
  let folds = config.defaultFolds;

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const kLine = document.createElement("p");
  kLine.className = "widget-stats";
  kLine.textContent =
    `Every model below uses the same fixed number of neighbours, k = ${data.fixedK}. ` +
    `This activity evaluates that one model -- it does not choose k. Lower MSE (mean squared error) is better.`;
  container.appendChild(kLine);

  // --- controls --------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const sizeGroup = document.createElement("div");
  sizeGroup.className = "widget-control";
  const sizeLabel = document.createElement("span");
  sizeLabel.id = "validation-stability-size-label";
  sizeLabel.textContent = "Sample size:";
  const sizeTabs = document.createElement("div");
  sizeTabs.className = "widget-tabs";
  sizeTabs.setAttribute("role", "tablist");
  sizeTabs.setAttribute("aria-labelledby", "validation-stability-size-label");
  const sizeButtons = new Map<string, HTMLButtonElement>();
  for (const key of config.sizeKeys) {
    const entry = sizeByKey.get(key)!;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = entry.label;
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `validation-stability-size-${key}`);
    btn.setAttribute("aria-selected", String(key === sizeKey));
    sizeTabs.appendChild(btn);
    sizeButtons.set(key, btn);
  }
  sizeGroup.append(sizeLabel, sizeTabs);
  controls.appendChild(sizeGroup);

  const seedFieldset = document.createElement("fieldset");
  seedFieldset.className = "widget-radio-group";
  const seedLegend = document.createElement("legend");
  seedLegend.textContent = "Random seed (changes the partition, not the participants)";
  seedFieldset.appendChild(seedLegend);
  const seedInputs = new Map<number, HTMLInputElement>();
  for (const s of data.splitSeeds) {
    const id = `validation-stability-seed-${s}`;
    const wrapper = document.createElement("label");
    wrapper.className = "widget-radio";
    wrapper.setAttribute("for", id);
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "validation-stability-seed";
    input.id = id;
    input.checked = s === seed;
    input.setAttribute("data-testid", id);
    const text = document.createElement("span");
    text.textContent = String(s);
    wrapper.append(input, text);
    seedFieldset.appendChild(wrapper);
    seedInputs.set(s, input);
  }
  controls.appendChild(seedFieldset);

  const foldsFieldset = document.createElement("fieldset");
  foldsFieldset.className = "widget-radio-group";
  const foldsLegend = document.createElement("legend");
  foldsLegend.textContent = "Number of folds";
  foldsFieldset.appendChild(foldsLegend);
  const foldsInputs = new Map<number, HTMLInputElement>();
  for (const f of data.foldOptions) {
    const id = `validation-stability-folds-${f}`;
    const wrapper = document.createElement("label");
    wrapper.className = "widget-radio";
    wrapper.setAttribute("for", id);
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "validation-stability-folds";
    input.id = id;
    input.checked = f === folds;
    input.setAttribute("data-testid", id);
    const text = document.createElement("span");
    text.textContent = String(f);
    wrapper.append(input, text);
    foldsFieldset.appendChild(wrapper);
    foldsInputs.set(f, input);
  }
  controls.appendChild(foldsFieldset);

  container.appendChild(controls);

  // --- status / summary --------------------------------------------------
  const summary = document.createElement("p");
  summary.className = "widget-stats";
  summary.setAttribute("data-testid", "validation-stability-summary");
  summary.setAttribute("role", "status");
  summary.setAttribute("aria-live", "polite");
  container.appendChild(summary);

  const smallNNote = document.createElement("p");
  smallNNote.className = "widget-warning";
  smallNNote.hidden = true;
  smallNNote.setAttribute("data-testid", "validation-stability-small-n-note");
  container.appendChild(smallNNote);

  // --- single-split plot ---------------------------------------------
  const singleHeading = document.createElement("h2");
  singleHeading.className = "widget-subhead";
  singleHeading.textContent = "One split, five seeds";
  container.appendChild(singleHeading);

  const singlePlot = document.createElement("div");
  singlePlot.className = "widget-plot";
  singlePlot.setAttribute("data-testid", "validation-stability-single-plot");
  singlePlot.dataset.renderCount = "0";
  container.appendChild(singlePlot);

  const singleEmpty = document.createElement("p");
  singleEmpty.className = "widget-empty";
  singleEmpty.hidden = true;
  singleEmpty.setAttribute("data-testid", "validation-stability-single-empty");
  container.appendChild(singleEmpty);

  // --- CV plot ----------------------------------------------------------
  const cvHeading = document.createElement("h2");
  cvHeading.className = "widget-subhead";
  cvHeading.textContent = "Cross-validation folds";
  container.appendChild(cvHeading);

  const cvPlot = document.createElement("div");
  cvPlot.className = "widget-plot";
  cvPlot.setAttribute("data-testid", "validation-stability-cv-plot");
  cvPlot.dataset.renderCount = "0";
  container.appendChild(cvPlot);

  const cvEmpty = document.createElement("p");
  cvEmpty.className = "widget-empty";
  cvEmpty.hidden = true;
  cvEmpty.setAttribute("data-testid", "validation-stability-cv-empty");
  container.appendChild(cvEmpty);

  const cvStats = document.createElement("p");
  cvStats.className = "widget-stats";
  cvStats.setAttribute("data-testid", "validation-stability-cv-stats");
  container.appendChild(cvStats);

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

  async function draw(): Promise<void> {
    if (destroyed) return;
    const size: SizeEntry = sizeByKey.get(sizeKey)!;

    for (const [key, btn] of sizeButtons) btn.setAttribute("aria-selected", String(key === sizeKey));
    container.dataset.sizeKey = sizeKey;
    container.dataset.seed = String(seed);
    container.dataset.folds = String(folds);

    smallNNote.hidden = !size.instabilityMeaningful;
    if (!smallNNote.hidden) {
      smallNNote.textContent =
        `At this sample size, at least one predeclared seed produces a single-split test ` +
        `R² below zero -- worse than always predicting the mean age.`;
    }

    const validSingles = size.singleSplit.filter((s) => s.valid);
    const chosenSingle = size.singleSplit.find((s) => s.seed === seed);

    summary.textContent = chosenSingle
      ? chosenSingle.valid
        ? `Sample size ${size.nActual}, seed ${seed}: single-split test MSE = ${chosenSingle.test_mse.toFixed(1)} ` +
          `(R² = ${chosenSingle.test_r2.toFixed(3)}), n_train = ${chosenSingle.n_train}, n_test = ${chosenSingle.n_test}.`
        : `Sample size ${size.nActual}, seed ${seed}: this split is too small to evaluate (${chosenSingle.reason}).`
      : "";

    // Single-split plot: test MSE for every predeclared seed, this sample size.
    Plotly.purge(singlePlot);
    if (validSingles.length === 0) {
      singlePlot.hidden = true;
      singleEmpty.hidden = false;
      singleEmpty.textContent = "No seed produces a valid split at this sample size.";
    } else {
      singlePlot.hidden = false;
      singleEmpty.hidden = true;
      const trace = {
        type: "bar" as const,
        x: validSingles.map((s) => String(s.seed)),
        y: validSingles.map((s) => s.test_mse),
        marker: {
          color: validSingles.map((s) =>
            s.seed === seed ? theme.diagonalLine : theme.markerPrimary,
          ),
        },
        hovertemplate: "seed %{x}<br>test MSE %{y:.1f}<extra></extra>",
      };
      const layout = buildPlotLayout(theme, {
        height: 280,
        xaxis: { title: { text: "Random seed" } },
        yaxis: { title: { text: "Single-split test MSE (lower is better)" } },
      });
      await Plotly.react(singlePlot, [trace], layout, PLOT_CONFIG);
    }
    const n0 = Number(singlePlot.dataset.renderCount ?? "0") + 1;
    singlePlot.dataset.renderCount = String(n0);

    // CV plot: per-fold MSE for the selected seed/folds, this sample size.
    const cvEntries = size.cvByFolds[String(folds)] ?? [];
    const chosenCv = cvEntries.find((c) => c.seed === seed);
    Plotly.purge(cvPlot);
    if (!chosenCv || !chosenCv.valid) {
      cvPlot.hidden = true;
      cvEmpty.hidden = false;
      cvEmpty.textContent = !chosenCv
        ? "No cross-validation result for this combination."
        : `This combination is too small to evaluate (${chosenCv.reason}).`;
      cvStats.textContent = "";
    } else {
      cvPlot.hidden = false;
      cvEmpty.hidden = true;
      const foldLabels = chosenCv.fold_mse.map((_, i) => `Fold ${i + 1}`);
      const bar = {
        type: "bar" as const,
        x: foldLabels,
        y: chosenCv.fold_mse,
        marker: { color: theme.markerPrimary },
        name: "fold MSE",
        hovertemplate: "%{x}<br>MSE %{y:.1f}<extra></extra>",
      };
      const meanLine = {
        type: "scatter" as const,
        mode: "lines" as const,
        x: foldLabels,
        y: foldLabels.map(() => chosenCv.mean_mse),
        line: { color: theme.diagonalLine, width: 2, dash: "dash" as const },
        name: "mean MSE",
        hoverinfo: "skip" as const,
      };
      const layout = buildPlotLayout(theme, {
        height: 280,
        showlegend: true,
        xaxis: { title: { text: `MSE per fold (K = ${folds})` } },
        yaxis: { title: { text: "Fold test MSE (lower is better)" } },
      });
      await Plotly.react(cvPlot, [bar, meanLine], layout, PLOT_CONFIG);

      const validCvAtFolds = cvEntries.filter((c) => c.valid);
      const meanSpread =
        validCvAtFolds.length >= 2 ? range(validCvAtFolds.map((c) => c.mean_mse)) : null;
      cvStats.textContent =
        `Mean MSE across the ${folds} folds (seed ${seed}) = ${chosenCv.mean_mse.toFixed(1)}, ` +
        `standard deviation across folds = ${chosenCv.std_mse.toFixed(1)}. ` +
        `Training size per fold ≈ ${mean(chosenCv.fold_train_sizes).toFixed(0)}, ` +
        `test size per fold ≈ ${mean(chosenCv.fold_test_sizes).toFixed(0)}.` +
        (meanSpread !== null
          ? ` Across the ${data.splitSeeds.length} predeclared seeds, the mean-CV-MSE spread at this sample size is ${meanSpread.toFixed(1)}.`
          : "");
    }
    const n1 = Number(cvPlot.dataset.renderCount ?? "0") + 1;
    cvPlot.dataset.renderCount = String(n1);
  }

  for (const [key, btn] of sizeButtons) {
    btn.addEventListener("click", () => {
      sizeKey = key;
      void draw();
    });
  }
  for (const [s, input] of seedInputs) {
    input.addEventListener("change", () => {
      if (input.checked) {
        seed = s;
        void draw();
      }
    });
  }
  for (const [f, input] of foldsInputs) {
    input.addEventListener("change", () => {
      if (input.checked) {
        folds = f;
        void draw();
      }
    });
  }

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void draw();
  });

  void draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(singlePlot);
      Plotly.purge(cvPlot);
    },
  };
}

export const validationStabilityComponent: WidgetComponent<
  ValidationStabilityConfig,
  ValidationStabilityData
> = {
  type: "validation-stability",
  parseData: parseValidationStabilityData,
  mount,
};
