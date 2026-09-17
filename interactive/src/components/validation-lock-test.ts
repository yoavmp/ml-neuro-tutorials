// Production activity: Exercise 4 "Choose k Before Revealing the Test Set"
// (WP27, revised by WP27R).
//
// Every candidate k's training MSE, validation MSE, and locked test MSE/R2
// is precomputed (scripts/wp27_validation_audit.py) on the Exercise 2 outer
// holdout split and its development (fit/validation) split -- nothing is
// recomputed in the browser. The student compares training-selected and
// validation-selected k using only training/validation numbers, picks a
// final k, and only then reveals the test result -- once. The seed was not
// chosen to guarantee any particular value wins; see the WP27R report.
//
// WP27R: the figure is one aligned three-panel plot (training MSE,
// validation MSE, test MSE) instead of a two-trace plot plus prose. Before
// locking, only the training and validation panels are drawn -- no test-MSE
// number is ever placed in a Plotly trace, hover template, DOM text node, or
// `hidden` element until the student presses "Lock Choice and Reveal Test
// Result". Every candidate's `testMseIfLocked` already lives in the parsed
// `data` object in memory (as it always has, for every WP27 widget); the
// requirement is that nothing student-inspectable renders it early.
import Plotly from "plotly.js-cartesian-dist-min";
import type { PlotData } from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { ValidationLockTestConfig } from "../config";
import {
  parseValidationLockTestData,
  type ValidationLockTestData,
} from "../validation-lock-test-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

// Panel vertical domains, top to bottom: training, validation, test. Fixed
// regardless of lock state so the test panel's slot is always visibly
// reserved (spec: "keep the third panel visibly locked or empty").
const DOMAIN_TRAIN: [number, number] = [0.72, 1];
const DOMAIN_VAL: [number, number] = [0.37, 0.65];
const DOMAIN_TEST: [number, number] = [0, 0.28];

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
    `Lower MSE (mean squared error) is better on every panel below.`;
  container.appendChild(sizesLine);

  // --- selection labels -------------------------------------------------
  const selectionLine = document.createElement("p");
  selectionLine.className = "widget-stats";
  selectionLine.setAttribute("data-testid", "validation-lock-test-selection");
  const trainRow = rowByK.get(data.trainingSelectedK)!;
  const valRow = rowByK.get(data.validationSelectedK)!;
  selectionLine.textContent =
    `Training-selected k = ${data.trainingSelectedK} (lowest training MSE, ${trainRow.trainMse.toFixed(1)}). ` +
    `Validation-selected k = ${data.validationSelectedK} (lowest validation MSE, ${valRow.valMse.toFixed(1)}). ` +
    `Both are marked with a dotted (training) or dashed (validation) vertical line on every panel below; ` +
    `your own choice is marked with a solid line.`;
  container.appendChild(selectionLine);

  // --- three-panel plot -----------------------------------------------
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
    "Resetting and re-choosing after seeing the revealed test curve would not be a valid analysis. " +
    "In real research, the test set is examined once, after the tuning choice is already made -- " +
    "not repeatedly, and not to search for a better-looking curve.";
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
  const methodologyWarning = document.createElement("p");
  methodologyWarning.className = "widget-warning";
  methodologyWarning.setAttribute("data-testid", "validation-lock-test-methodology-warning");
  methodologyWarning.textContent =
    "This complete test-MSE curve is revealed only as a teaching demonstration, after your choice was " +
    "already locked. In a real analysis, evaluating every candidate k on the test set like this would use " +
    "the test set for tuning, which is exactly what a held-out test set must not be used for -- so your " +
    "choice of k must not change now that you can see it.";
  reveal.append(revealStats, revealCompare, methodologyWarning);
  container.appendChild(reveal);

  if (config.reflectionPrompts && config.reflectionPrompts.length > 0) {
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = "Reflect before revealing";
    const list = document.createElement("ul");
    list.className = "widget-prompts";
    for (const p of config.reflectionPrompts) {
      const li = document.createElement("li");
      li.textContent = p;
      list.appendChild(li);
    }
    container.append(h, list);
  }

  const postRevealSection = document.createElement("div");
  postRevealSection.setAttribute("data-testid", "validation-lock-test-post-reveal-reflect");
  postRevealSection.hidden = true;
  if (config.postRevealReflectionPrompts && config.postRevealReflectionPrompts.length > 0) {
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = "Reflect after revealing";
    const list = document.createElement("ul");
    list.className = "widget-prompts";
    for (const p of config.postRevealReflectionPrompts) {
      const li = document.createElement("li");
      li.textContent = p;
      list.appendChild(li);
    }
    postRevealSection.append(h, list);
  }
  container.appendChild(postRevealSection);

  function sharedYRange(includeTest: boolean): [number, number] {
    const values = data.rows.flatMap((r) =>
      includeTest ? [r.trainMse, r.valMse, r.testMseIfLocked] : [r.trainMse, r.valMse],
    );
    const max = Math.max(...values);
    return [0, max * 1.08];
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
      xaxis: "x",
      yaxis: "y",
      line: { color: theme.markerPrimary },
      hovertemplate: "k = %{x}<br>training MSE %{y:.1f}<extra></extra>",
    };
    const valTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      x: ks,
      y: data.rows.map((r) => r.valMse),
      name: "validation MSE",
      xaxis: "x2",
      yaxis: "y2",
      line: { color: theme.diagonalLine },
      hovertemplate: "k = %{x}<br>validation MSE %{y:.1f}<extra></extra>",
    };
    // The test trace (and every number in it) is constructed only when
    // `locked` is true -- before that, it simply does not exist, so no test
    // value can appear in the DOM, a hover template, or anywhere else.
    const traces: PlotData[] = [trainTrace, valTrace];
    if (locked) {
      traces.push({
        type: "scatter" as const,
        mode: "lines+markers" as const,
        x: ks,
        y: data.rows.map((r) => r.testMseIfLocked),
        name: "test MSE (revealed)",
        xaxis: "x3",
        yaxis: "y3",
        line: { color: theme.annotationText },
        hovertemplate: "k = %{x}<br>test MSE %{y:.1f}<extra></extra>",
      });
    }

    const [yMin, yMax] = sharedYRange(locked);
    const panelTitle = (text: string, domain: [number, number]): Record<string, unknown> => ({
      text,
      xref: "paper" as const,
      yref: "paper" as const,
      x: 0,
      xanchor: "left" as const,
      y: domain[1] + 0.035,
      yanchor: "bottom" as const,
      showarrow: false,
      font: { color: theme.annotationText, size: 13 },
    });

    const annotations: Record<string, unknown>[] = [
      panelTitle("Training MSE", DOMAIN_TRAIN),
      panelTitle("Validation MSE", DOMAIN_VAL),
      panelTitle(locked ? "Test MSE (revealed)" : "Test MSE -- locked until you reveal it", DOMAIN_TEST),
    ];
    if (!locked) {
      annotations.push({
        text: "Locked until you press “Lock Choice and Reveal Test Result” below.",
        xref: "paper" as const,
        yref: "paper" as const,
        x: 0.5,
        xanchor: "center" as const,
        y: (DOMAIN_TEST[0] + DOMAIN_TEST[1]) / 2,
        yanchor: "middle" as const,
        showarrow: false,
        font: { color: theme.annotationText, size: 12 },
      });
    }

    // Vertical marker lines for the chosen / training-selected /
    // validation-selected k, spanning the full figure height (paper y 0-1)
    // at the shared, matched x position -- visible on every drawn panel at
    // once without needing one shape per panel.
    const markerShapes = [
      { k: data.trainingSelectedK, dash: "dot" as const, width: 1.5 },
      { k: data.validationSelectedK, dash: "dash" as const, width: 1.5 },
      { k: chosenK, dash: "solid" as const, width: 2 },
    ].map(({ k, dash, width }) => ({
      type: "line" as const,
      xref: "x" as const,
      yref: "paper" as const,
      x0: k,
      x1: k,
      y0: 0,
      y1: 1,
      line: { color: theme.annotationText, dash, width },
    }));

    const layout = buildPlotLayout(theme, {
      height: 620,
      showlegend: true,
      legend: { y: 1.06 },
      annotations,
      shapes: markerShapes,
      xaxis: { type: "log" as const, domain: [0, 1] },
      xaxis2: { type: "log" as const, domain: [0, 1], matches: "x" },
      xaxis3: {
        type: "log" as const,
        domain: [0, 1],
        matches: "x",
        title: { text: "Number of neighbours (k)" },
      },
      yaxis: { domain: DOMAIN_TRAIN, title: { text: "MSE" }, range: [yMin, yMax] },
      yaxis2: { domain: DOMAIN_VAL, title: { text: "MSE" }, range: [yMin, yMax] },
      yaxis3: { domain: DOMAIN_TEST, title: { text: "MSE" }, range: [yMin, yMax] },
    });

    await Plotly.react(plot, traces, layout, PLOT_CONFIG);
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
    postRevealSection.hidden = !locked;

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
        `Look at the shape of the three panels above: the test curve tracks the validation curve's shape -- both dip to a ` +
        `minimum partway through the k range -- far more closely than it tracks the training curve, which keeps rising as k ` +
        `grows. The validation-selected value is expected to generalise better than the training-selected value, but a single ` +
        `test split can still favour a different k by chance, as it may or may not have done here.`;
    }
  }

  for (const [k, btn] of kButtons) {
    btn.addEventListener("click", () => {
      if (locked) return;
      chosenK = k;
      render();
      void drawPlot();
    });
  }
  lockBtn.addEventListener("click", () => {
    if (locked) return;
    locked = true;
    render();
    void drawPlot();
  });
  resetBtn.addEventListener("click", () => {
    locked = false;
    chosenK = config.defaultK;
    render();
    void drawPlot();
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
