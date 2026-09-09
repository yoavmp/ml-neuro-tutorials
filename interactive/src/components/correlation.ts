// Production activity: ABIDE-II feature correlation explorer.
//
// Labelled X-variable, Y-variable, method (Pearson / Spearman) and grouping
// (None / Diagnostic group / Sex) controls drive a Plotly scatter of the
// pairwise-complete observations. Every coefficient and count comes from the
// pure, unit-tested `computeCorrelation` (src/correlation.ts). No Python kernel,
// no CDN, no participant-level detail — hover shows the two plotted values only,
// and no trend line is drawn (a single line would misrepresent Spearman and
// grouped views).

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { EdaCorrelationConfig } from "../config";
import {
  computeCorrelation,
  type CorrelationMethod,
  type GroupingInput,
  type NumCell,
} from "../correlation";
import {
  parseAbideCorrelationData,
  numericColumn,
  type AbideCorrelationData,
} from "../correlation-data";

// Okabe–Ito: colourblind-safe, and deliberately not a good/bad ramp.
const GROUP_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"];
const UNGROUPED_COLOR_LIGHT = "#33566b";
const UNGROUPED_COLOR_DARK = "#8fb6cc";

function prefersDark(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function fmtR(r: number | null): string {
  return r === null ? "not defined" : (r >= 0 ? "+" : "") + r.toFixed(2);
}

function mount(args: MountArgs<EdaCorrelationConfig, AbideCorrelationData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const labelOf = new Map(config.variables.map((v) => [v.name, v.label]));

  const missingColumns = config.variables
    .map((v) => v.name)
    .filter((name) => !Object.prototype.hasOwnProperty.call(data.columns, name));
  for (const g of config.groupings) {
    if (!Object.prototype.hasOwnProperty.call(data.columns, g.field)) {
      missingColumns.push(g.field);
    }
  }
  if (missingColumns.length > 0) {
    throw new Error(
      `The data file is missing column(s) required by this activity: ${missingColumns.join(", ")}.`,
    );
  }

  // --- header ---
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  // --- controls ---
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  function makeSelect(
    id: string,
    labelText: string,
    options: ReadonlyArray<{ value: string; text: string }>,
    initial: string,
  ): { group: HTMLDivElement; select: HTMLSelectElement } {
    const group = document.createElement("div");
    group.className = "widget-control";
    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelText;
    const select = document.createElement("select");
    select.id = id;
    select.setAttribute("data-testid", id);
    for (const o of options) {
      const opt = document.createElement("option");
      opt.value = o.value;
      opt.textContent = o.text;
      select.appendChild(opt);
    }
    select.value = initial;
    group.append(label, select);
    return { group, select };
  }

  const varOptions = config.variables.map((v) => ({ value: v.name, text: v.label }));
  const { group: xGroup, select: xSelect } = makeSelect(
    "correlation-x",
    "X variable:",
    varOptions,
    config.defaultX,
  );
  const { group: yGroup, select: ySelect } = makeSelect(
    "correlation-y",
    "Y variable:",
    varOptions,
    config.defaultY,
  );
  const { group: methodGroup, select: methodSelect } = makeSelect(
    "correlation-method",
    "Method:",
    [
      { value: "pearson", text: "Pearson (linear)" },
      { value: "spearman", text: "Spearman (rank-based)" },
    ],
    config.defaultMethod,
  );
  const groupOptions = [
    { value: "none", text: "No grouping" },
    ...config.groupings.map((g) => ({ value: g.key, text: g.label })),
  ];
  const { group: groupGroup, select: groupSelect } = makeSelect(
    "correlation-group",
    "Colour by:",
    groupOptions,
    "none",
  );
  controls.append(xGroup, yGroup, methodGroup, groupGroup);
  container.appendChild(controls);

  // --- readouts ---
  const sameVar = document.createElement("p");
  sameVar.className = "widget-empty";
  sameVar.setAttribute("data-testid", "correlation-same-var");
  sameVar.hidden = true;
  sameVar.textContent =
    "X and Y are the same variable. Choose two different variables to compare.";
  container.appendChild(sameVar);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "correlation-stats");
  container.appendChild(stats);

  const missingLine = document.createElement("p");
  missingLine.className = "widget-stats";
  missingLine.setAttribute("data-testid", "correlation-missing");
  container.appendChild(missingLine);

  const groupsHeading = document.createElement("p");
  groupsHeading.className = "widget-stats";
  groupsHeading.setAttribute("data-testid", "correlation-groups");
  groupsHeading.hidden = true;
  container.appendChild(groupsHeading);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "correlation-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  if (config.reflectionPrompts.length > 0) {
    const promptsHeading = document.createElement("h2");
    promptsHeading.className = "widget-subhead";
    promptsHeading.textContent = "Reflect";
    const list = document.createElement("ul");
    list.className = "widget-prompts";
    for (const prompt of config.reflectionPrompts) {
      const li = document.createElement("li");
      li.textContent = prompt;
      list.appendChild(li);
    }
    container.append(promptsHeading, list);
  }

  // --- theme ---
  const dark = prefersDark();
  const axisColor = dark ? "#c9c9c9" : "#333333";
  const gridColor = dark ? "#3a3a3a" : "#e2e2e2";
  const ungroupedColor = dark ? UNGROUPED_COLOR_DARK : UNGROUPED_COLOR_LIGHT;
  const plotConfig = { displayModeBar: false, responsive: true };
  let destroyed = false;

  function groupingInput(key: string): GroupingInput | null {
    if (key === "none") return null;
    const g = config.groupings.find((gg) => gg.key === key);
    if (!g) return null;
    const codes = numericColumn(data, g.field) as (number | null)[] | undefined;
    if (!codes) return null;
    return { field: g.field, codes, values: g.values };
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    const xName = xSelect.value;
    const yName = ySelect.value;
    const method = methodSelect.value as CorrelationMethod;
    const groupKey = groupSelect.value;
    const xLabel = labelOf.get(xName) ?? xName;
    const yLabel = labelOf.get(yName) ?? yName;

    plot.dataset.activeX = xName;
    plot.dataset.activeY = yName;
    plot.dataset.activeMethod = method;
    plot.dataset.activeGroup = groupKey;

    const methodName = method === "pearson" ? "Pearson" : "Spearman";

    if (xName === yName) {
      sameVar.hidden = false;
      groupsHeading.hidden = true;
      stats.textContent = `${methodName} correlation: not defined (X and Y are the same variable).`;
      missingLine.textContent = "";
      plot.dataset.sameVariable = "true";
      plot.dataset.n = "0";
      plot.dataset.r = "null";
      plot.dataset.excludedN = "0";
      plot.dataset.traceCount = "0";
      await Plotly.react(plot, [], { autosize: true }, plotConfig);
      if (destroyed) return;
      const bump = Number(plot.dataset.renderCount ?? "0") + 1;
      plot.dataset.renderCount = String(bump);
      return;
    }
    sameVar.hidden = true;
    plot.dataset.sameVariable = "false";

    const xCol = numericColumn(data, xName) as NumCell[] | undefined;
    const yCol = numericColumn(data, yName) as NumCell[] | undefined;
    if (!xCol || !yCol) {
      throw new Error(`Column data for "${xName}" or "${yName}" is unavailable.`);
    }
    const grouping = groupingInput(groupKey);
    const result = computeCorrelation(xCol, yCol, method, grouping);

    // --- text readouts ---
    if (result.overall.r === null) {
      stats.textContent =
        `${methodName} correlation: not defined — ${result.overall.reason} ` +
        `(n = ${result.overall.n.toLocaleString()} pairwise-complete).`;
    } else {
      stats.textContent =
        `${methodName} correlation r = ${fmtR(result.overall.r)} · ` +
        `n = ${result.overall.n.toLocaleString()} pairwise-complete participants ` +
        `(of ${result.missing.total.toLocaleString()}).`;
    }

    missingLine.textContent =
      `${xLabel} missing: ${result.missing.x.toLocaleString()} · ` +
      `${yLabel} missing: ${result.missing.y.toLocaleString()} · ` +
      `excluded because either is missing: ${result.missing.either.toLocaleString()} ` +
      `of ${result.missing.total.toLocaleString()}.`;

    if (result.groups) {
      groupsHeading.hidden = false;
      const parts = result.groups.map((g) => {
        const value = g.r === null ? "not defined" : `r = ${fmtR(g.r)}`;
        return `${g.label}: ${value} (n = ${g.n.toLocaleString()})`;
      });
      groupsHeading.textContent = `Within groups — ${parts.join(" · ")}`;
    } else {
      groupsHeading.hidden = true;
      groupsHeading.textContent = "";
    }

    // --- traces ---
    const hover = `${xLabel}: %{x}<br>${yLabel}: %{y}`;
    let traces: Record<string, unknown>[];
    if (result.groups && result.points.group) {
      const groupCodes = result.points.group;
      traces = config.groupings
        .find((g) => g.key === groupKey)!
        .values.map((v, i) => {
          const xs: number[] = [];
          const ys: number[] = [];
          for (let k = 0; k < groupCodes.length; k += 1) {
            if (groupCodes[k] === v.code) {
              xs.push(result.points.x[k]!);
              ys.push(result.points.y[k]!);
            }
          }
          return {
            type: "scatter" as const,
            mode: "markers" as const,
            name: v.label,
            x: xs,
            y: ys,
            marker: {
              color: GROUP_COLORS[i % GROUP_COLORS.length],
              size: 6,
              opacity: 0.6,
            },
            hovertemplate: `${hover}<extra>${v.label}</extra>`,
          };
        });
    } else {
      traces = [
        {
          type: "scatter" as const,
          mode: "markers" as const,
          name: "Participants",
          x: result.points.x,
          y: result.points.y,
          marker: { color: ungroupedColor, size: 6, opacity: 0.55 },
          hovertemplate: `${hover}<extra></extra>`,
        },
      ];
    }

    const layout = {
      margin: { t: 12, r: 12, b: 52, l: 62 },
      height: 420,
      autosize: true,
      showlegend: Boolean(result.groups),
      legend: { orientation: "h" as const, y: -0.2 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: axisColor },
      xaxis: {
        title: { text: xLabel },
        gridcolor: gridColor,
        zeroline: false,
      },
      yaxis: {
        title: { text: yLabel },
        gridcolor: gridColor,
        zeroline: false,
      },
    };

    await Plotly.react(plot, traces, layout, plotConfig);
    if (destroyed) return;

    plot.dataset.n = String(result.overall.n);
    plot.dataset.r = result.overall.r === null ? "null" : result.overall.r.toFixed(4);
    plot.dataset.excludedN = String(result.missing.either);
    plot.dataset.traceCount = String(traces.length);
    plot.dataset.groupCount = String(result.groups ? result.groups.length : 0);
    const next = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(next);
  }

  for (const select of [xSelect, ySelect, methodSelect, groupSelect]) {
    select.addEventListener("change", () => void draw());
  }

  void draw();

  return {
    destroy() {
      destroyed = true;
      Plotly.purge(plot);
    },
  };
}

export const correlationComponent: WidgetComponent<
  EdaCorrelationConfig,
  AbideCorrelationData
> = {
  type: "eda-correlation",
  parseData: parseAbideCorrelationData,
  mount,
};
