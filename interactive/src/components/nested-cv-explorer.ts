// Production activity: Exercise 4 "Look Inside Nested Cross-Validation"
// (WP27).
//
// Every outer fold's inner-CV mean MSE per candidate k, selected k, and
// outer-test MSE/R2 is precomputed (scripts/wp27_validation_audit.py) --
// nothing runs a nested sklearn search in the browser. Only one candidate-k
// grid and one inner-fold count were audited (see the WP27 report), so this
// activity's only true control is which outer fold to inspect.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { NestedCvExplorerConfig } from "../config";
import {
  parseNestedCvExplorerData,
  type NestedCvExplorerData,
} from "../nested-cv-explorer-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function mount(
  args: MountArgs<NestedCvExplorerConfig, NestedCvExplorerData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const rowByFold = new Map(data.foldRows.map((r) => [r.outerFold, r]));
  if (!rowByFold.has(config.defaultOuterFold)) {
    throw new Error(`config.defaultOuterFold ${config.defaultOuterFold} is not one of the audited outer folds.`);
  }

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;
  let outerFold = config.defaultOuterFold;

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const gridLine = document.createElement("p");
  gridLine.className = "widget-stats";
  gridLine.textContent =
    `Candidate values of k audited for this activity: ${data.candidateKs.join(", ")}. ` +
    `${data.nOuter} outer folds, each with ${data.nInner}-fold inner cross-validation. Lower MSE is better.`;
  container.appendChild(gridLine);

  // --- outer-fold control -------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";
  const foldGroup = document.createElement("div");
  foldGroup.className = "widget-control";
  const foldLabel = document.createElement("span");
  foldLabel.id = "nested-cv-fold-label";
  foldLabel.textContent = "Outer fold:";
  const foldTabs = document.createElement("div");
  foldTabs.className = "widget-tabs";
  foldTabs.setAttribute("role", "tablist");
  foldTabs.setAttribute("aria-labelledby", "nested-cv-fold-label");
  const foldButtons = new Map<number, HTMLButtonElement>();
  for (const row of data.foldRows) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(row.outerFold + 1);
    btn.setAttribute("role", "tab");
    btn.setAttribute("data-testid", `nested-cv-fold-${row.outerFold}`);
    btn.setAttribute("aria-selected", String(row.outerFold === outerFold));
    foldTabs.appendChild(btn);
    foldButtons.set(row.outerFold, btn);
  }
  foldGroup.append(foldLabel, foldTabs);
  controls.appendChild(foldGroup);
  container.appendChild(controls);

  const foldStats = document.createElement("p");
  foldStats.className = "widget-stats";
  foldStats.setAttribute("data-testid", "nested-cv-fold-stats");
  foldStats.setAttribute("role", "status");
  foldStats.setAttribute("aria-live", "polite");
  container.appendChild(foldStats);

  // --- inner-CV plot for selected fold -----------------------------
  const innerHeading = document.createElement("h2");
  innerHeading.className = "widget-subhead";
  innerHeading.textContent = "Inner cross-validation: choosing k inside this outer fold";
  container.appendChild(innerHeading);

  const innerPlot = document.createElement("div");
  innerPlot.className = "widget-plot";
  innerPlot.setAttribute("data-testid", "nested-cv-inner-plot");
  innerPlot.dataset.renderCount = "0";
  container.appendChild(innerPlot);

  // --- summary across folds -------------------------------------------
  const summaryHeading = document.createElement("h2");
  summaryHeading.className = "widget-subhead";
  summaryHeading.textContent = "Summary across all outer folds";
  container.appendChild(summaryHeading);

  const summaryStats = document.createElement("p");
  summaryStats.className = "widget-stats";
  summaryStats.setAttribute("data-testid", "nested-cv-summary-stats");
  summaryStats.textContent =
    `Selected k per outer fold: ${data.selectedKPerFold.join(", ")}. ` +
    `Mean outer-test MSE = ${data.meanOuterTestMse.toFixed(1)} (standard deviation ${data.stdOuterTestMse.toFixed(1)}). ` +
    `Mean outer-test R² = ${data.meanOuterTestR2.toFixed(3)}. ` +
    (data.selectedKVariesAcrossFolds
      ? "The selected k differs across outer folds here."
      : "The selected k happened to be the same across every outer fold here -- different outer folds may " +
        "still select different k values in general, because each outer training set contains different participants.");
  container.appendChild(summaryStats);

  const table = document.createElement("table");
  table.className = "widget-table";
  table.setAttribute("data-testid", "nested-cv-summary-table");
  const caption = document.createElement("caption");
  caption.textContent = "Outer-fold results";
  table.appendChild(caption);
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Outer fold", "Selected k", "Outer-test MSE", "Outer-test R²"]) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = label;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  for (const row of data.foldRows) {
    const tr = document.createElement("tr");
    const cells = [
      String(row.outerFold + 1),
      String(row.selectedK),
      row.outerTestMse.toFixed(1),
      row.outerTestR2.toFixed(3),
    ];
    for (const c of cells) {
      const td = document.createElement("td");
      td.textContent = c;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  const scroll = document.createElement("div");
  scroll.className = "widget-table-scroll";
  scroll.appendChild(table);
  container.appendChild(scroll);

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
    const row = rowByFold.get(outerFold)!;
    for (const [k, btn] of foldButtons) btn.setAttribute("aria-selected", String(k === outerFold));
    container.dataset.outerFold = String(outerFold);

    foldStats.textContent =
      `Outer fold ${outerFold + 1}: ${row.nTrain} training participants, ${row.nTest} test participants. ` +
      `Selected k = ${row.selectedK} (best inner-CV mean MSE = ${row.bestInnerMse.toFixed(1)}). ` +
      `Outer-test MSE = ${row.outerTestMse.toFixed(1)}, outer-test R² = ${row.outerTestR2.toFixed(3)}. ` +
      `The outer-test score -- not the inner-CV score -- estimates future performance, because only the outer-test ` +
      `fold was excluded from every scaling, tuning, and preprocessing decision for this fold.`;

    const ks = data.candidateKs;
    const mses = ks.map((k) => row.innerMseByK[String(k)]!);
    const bar = {
      type: "bar" as const,
      x: ks.map(String),
      y: mses,
      marker: {
        color: ks.map((k) => (k === row.selectedK ? theme.diagonalLine : theme.markerPrimary)),
      },
      hovertemplate: "k = %{x}<br>inner-CV mean MSE %{y:.1f}<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 280,
      xaxis: { title: { text: "Candidate number of neighbours (k)" } },
      yaxis: { title: { text: "Inner-CV mean MSE (lower is better)" } },
    });
    Plotly.purge(innerPlot);
    await Plotly.react(innerPlot, [bar], layout, PLOT_CONFIG);
    const n = Number(innerPlot.dataset.renderCount ?? "0") + 1;
    innerPlot.dataset.renderCount = String(n);
  }

  for (const [k, btn] of foldButtons) {
    btn.addEventListener("click", () => {
      outerFold = k;
      void draw();
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
      Plotly.purge(innerPlot);
    },
  };
}

export const nestedCvExplorerComponent: WidgetComponent<
  NestedCvExplorerConfig,
  NestedCvExplorerData
> = {
  type: "nested-cv-explorer",
  parseData: parseNestedCvExplorerData,
  mount,
};
