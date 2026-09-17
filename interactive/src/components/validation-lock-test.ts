// Production activity: Exercise 4 "Choose k Before Revealing the Test Set"
// (WP27).
//
// Every candidate k's training MSE, validation MSE, and locked test MSE/R2
// is precomputed (scripts/wp27_validation_audit.py) on the Exercise 2 outer
// holdout split and its development (fit/validation) split -- nothing is
// recomputed in the browser. The student compares training-selected and
// validation-selected k using only training/validation numbers, picks a
// final k, and only then reveals the test result -- once. The seed was not
// chosen to guarantee any particular value wins; see the WP27 report.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ValidationLockTestConfig } from "../config";
import {
  parseValidationLockTestData,
  type ValidationLockTestData,
} from "../validation-lock-test-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function mount(
  args: MountArgs<ValidationLockTestConfig, ValidationLockTestData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const rowByK = new Map(data.rows.map((r) => [r.k, r]));
  if (!rowByK.has(config.defaultK)) {
    throw new Error(`config.defaultK ${config.defaultK} is not one of the audited candidate k values.`);
  }

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;
  let chosenK = config.defaultK;
  let locked = false;

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const sizesLine = document.createElement("p");
  sizesLine.className = "widget-stats";
  sizesLine.textContent =
    `Training-and-validation development set: ${data.nFit} participants to fit, ` +
    `${data.nVal} to validate. The test set (${data.nTest} participants) stays hidden until you lock a choice. ` +
    `Lower MSE (mean squared error) is better.`;
  container.appendChild(sizesLine);

  // --- selection labels -------------------------------------------------
  const selectionLine = document.createElement("p");
  selectionLine.className = "widget-stats";
  selectionLine.setAttribute("data-testid", "validation-lock-test-selection");
  const trainRow = rowByK.get(data.trainingSelectedK)!;
  const valRow = rowByK.get(data.validationSelectedK)!;
  selectionLine.textContent =
    `Training-selected k = ${data.trainingSelectedK} (lowest training MSE, ${trainRow.trainMse.toFixed(1)}). ` +
    `Validation-selected k = ${data.validationSelectedK} (lowest validation MSE, ${valRow.valMse.toFixed(1)}).`;
  container.appendChild(selectionLine);

  // --- train/val plot -----------------------------------------------
  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "validation-lock-test-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  // --- k choice -----------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const kGroup = document.createElement("div");
  kGroup.className = "widget-control";
  const kLabel = document.createElement("span");
  kLabel.id = "validation-lock-test-k-label";
  kLabel.textContent = "Your final choice of k:";
  const kTabs = document.createElement("div");
  kTabs.className = "widget-tabs";
  kTabs.setAttribute("role", "tablist");
  kTabs.setAttribute("aria-labelledby", "validation-lock-test-k-label");
  const kButtons = new Map<number, HTMLButtonElement>();
  for (const row of data.rows) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(row.k);
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `validation-lock-test-k-${row.k}`);
    btn.setAttribute("aria-selected", String(row.k === chosenK));
    kTabs.appendChild(btn);
    kButtons.set(row.k, btn);
  }
  kGroup.append(kLabel, kTabs);
  controls.appendChild(kGroup);
  container.appendChild(controls);

  const chosenLine = document.createElement("p");
  chosenLine.className = "widget-stats";
  chosenLine.setAttribute("data-testid", "validation-lock-test-chosen");
  container.appendChild(chosenLine);

  // --- lock / reset -----------------------------------------------------
  const actionRow = document.createElement("div");
  actionRow.className = "widget-controls";
  const lockBtn = document.createElement("button");
  lockBtn.type = "button";
  lockBtn.textContent = "Lock Choice and Reveal Test Result";
  lockBtn.setAttribute("data-testid", "validation-lock-test-lock-button");
  const resetBtn = document.createElement("button");
  resetBtn.type = "button";
  resetBtn.textContent = "Reset Activity";
  resetBtn.setAttribute("data-testid", "validation-lock-test-reset-button");
  actionRow.append(lockBtn, resetBtn);
  container.appendChild(actionRow);

  const resetNote = document.createElement("p");
  resetNote.className = "widget-warning";
  resetNote.setAttribute("data-testid", "validation-lock-test-reset-note");
  resetNote.textContent =
    "Resetting and re-choosing after seeing a test result would not be a valid analysis. " +
    "In real research, the test set is looked at once, after the choice is already made.";
  resetNote.hidden = true;
  container.appendChild(resetNote);

  // --- reveal panel -----------------------------------------------------
  const reveal = document.createElement("section");
  reveal.setAttribute("data-testid", "validation-lock-test-reveal");
  reveal.hidden = true;
  const revealStats = document.createElement("p");
  revealStats.className = "widget-stats";
  revealStats.setAttribute("data-testid", "validation-lock-test-reveal-stats");
  const revealCompare = document.createElement("p");
  revealCompare.className = "widget-stats";
  revealCompare.setAttribute("data-testid", "validation-lock-test-reveal-compare");
  reveal.append(revealStats, revealCompare);
  container.appendChild(reveal);

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

  async function drawPlot(): Promise<void> {
    if (destroyed) return;
    const ks = data.rows.map((r) => r.k);
    const trainTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      x: ks,
      y: data.rows.map((r) => r.trainMse),
      name: "training MSE",
      line: { color: theme.markerPrimary },
    };
    const valTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      x: ks,
      y: data.rows.map((r) => r.valMse),
      name: "validation MSE",
      line: { color: theme.diagonalLine },
    };
    const layout = buildPlotLayout(theme, {
      height: 300,
      showlegend: true,
      xaxis: { title: { text: "Number of neighbours (k)" }, type: "log" as const },
      yaxis: { title: { text: "MSE (lower is better)" } },
    });
    await Plotly.react(plot, [trainTrace, valTrace], layout, PLOT_CONFIG);
    const n = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(n);
  }

  function render(): void {
    for (const [k, btn] of kButtons) {
      btn.setAttribute("aria-selected", String(k === chosenK));
      btn.disabled = locked;
    }
    lockBtn.disabled = locked;
    resetBtn.hidden = !locked;
    resetNote.hidden = !locked;

    const chosen = rowByK.get(chosenK)!;
    chosenLine.textContent =
      `Chosen k = ${chosenK}: training MSE = ${chosen.trainMse.toFixed(1)}, validation MSE = ${chosen.valMse.toFixed(1)}.`;

    reveal.hidden = !locked;
    container.dataset.chosenK = String(chosenK);
    container.dataset.locked = String(locked);

    if (locked) {
      const trainSel = rowByK.get(data.trainingSelectedK)!;
      const valSel = rowByK.get(data.validationSelectedK)!;
      revealStats.textContent =
        `Test MSE for your chosen k = ${chosenK}: ${chosen.testMseIfLocked.toFixed(1)} ` +
        `(R² = ${chosen.testR2IfLocked.toFixed(3)}).`;
      revealCompare.textContent =
        `For comparison, the training-selected k = ${data.trainingSelectedK} scores ${trainSel.testMseIfLocked.toFixed(1)} ` +
        `on this test set, and the validation-selected k = ${data.validationSelectedK} scores ${valSel.testMseIfLocked.toFixed(1)}. ` +
        `The validation-selected value is expected to generalise better than the training-selected value, ` +
        `but a single test split can occasionally favour a different value by chance.`;
    }
  }

  for (const [k, btn] of kButtons) {
    btn.addEventListener("click", () => {
      if (locked) return;
      chosenK = k;
      render();
    });
  }
  lockBtn.addEventListener("click", () => {
    if (locked) return;
    locked = true;
    render();
  });
  resetBtn.addEventListener("click", () => {
    locked = false;
    chosenK = config.defaultK;
    render();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void drawPlot();
  });

  void drawPlot();
  render();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(plot);
    },
  };
}

export const validationLockTestComponent: WidgetComponent<
  ValidationLockTestConfig,
  ValidationLockTestData
> = {
  type: "validation-lock-test",
  parseData: parseValidationLockTestData,
  mount,
};
