// Production activity: ABIDE-II complete-case retention.
//
// Accessible grouped checkboxes pick the "core" variables; a labelled summary
// and a Plotly *bar* trace of retained-percentage-by-site are recomputed from
// the pure, unit-tested `computeRetention` (src/retention.ts) on every change.
// No Python kernel, no CDN, no participant-level detail — the chart hover shows
// aggregate site counts only.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { EdaRetentionConfig } from "../config";
import { computeRetention, type CellValue } from "../retention";
import {
  parseAbideRetentionData,
  type AbideRetentionData,
} from "../retention-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

const DEFAULT_LOW_RETENTION_PCT = 50;

interface VariableRef {
  name: string;
  label: string;
  group: string;
}

function mount(args: MountArgs<EdaRetentionConfig, AbideRetentionData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const allVariables: VariableRef[] = config.groups.flatMap((g) =>
    g.variables.map((v) => ({ name: v.name, label: v.label, group: g.label })),
  );
  const labelOf = new Map(allVariables.map((v) => [v.name, v.label]));

  const missingColumns = allVariables
    .map((v) => v.name)
    .filter((name) => !Object.prototype.hasOwnProperty.call(data.columns, name));
  if (missingColumns.length > 0) {
    throw new Error(
      `The data file is missing column(s) required by this activity: ${missingColumns.join(", ")}.`,
    );
  }
  const siteLabels = data.columns[config.siteField] as string[] | undefined;
  if (!siteLabels) {
    throw new Error(`The data file has no "${config.siteField}" column for site grouping.`);
  }

  const lowRetentionPct = config.lowRetentionWarningPct ?? DEFAULT_LOW_RETENTION_PCT;
  const suggested = config.defaultVariables;

  // --- header ---
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  // --- preset controls ---
  const presetRow = document.createElement("div");
  presetRow.className = "widget-controls";
  const suggestedBtn = document.createElement("button");
  suggestedBtn.type = "button";
  suggestedBtn.setAttribute("data-testid", "retention-suggested");
  suggestedBtn.textContent = "Use suggested core set";
  const selectAllBtn = document.createElement("button");
  selectAllBtn.type = "button";
  selectAllBtn.setAttribute("data-testid", "retention-select-all");
  selectAllBtn.textContent = "Select all";
  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.setAttribute("data-testid", "retention-clear");
  clearBtn.textContent = "Clear";
  presetRow.append(suggestedBtn, selectAllBtn, clearBtn);
  container.appendChild(presetRow);

  // --- grouped checkboxes ---
  const checkboxes = new Map<string, HTMLInputElement>();
  const groupsWrap = document.createElement("div");
  groupsWrap.className = "widget-checkbox-groups";
  for (const group of config.groups) {
    const fieldset = document.createElement("fieldset");
    fieldset.className = "widget-checkbox-group";
    const legend = document.createElement("legend");
    legend.textContent = group.label;
    fieldset.appendChild(legend);
    for (const variable of group.variables) {
      const id = `retention-var-${variable.name}`;
      const wrapper = document.createElement("label");
      wrapper.className = "widget-checkbox";
      wrapper.setAttribute("for", id);
      const input = document.createElement("input");
      input.type = "checkbox";
      input.id = id;
      input.value = variable.name;
      input.setAttribute("data-testid", id);
      const text = document.createElement("span");
      text.textContent = variable.label;
      wrapper.append(input, text);
      fieldset.appendChild(wrapper);
      checkboxes.set(variable.name, input);
    }
    groupsWrap.appendChild(fieldset);
  }
  container.appendChild(groupsWrap);

  // --- selection summary ---
  const selectedLine = document.createElement("p");
  selectedLine.className = "widget-stats";
  selectedLine.setAttribute("data-testid", "retention-selected");
  container.appendChild(selectedLine);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "retention-stats");
  container.appendChild(stats);

  const message = document.createElement("p");
  message.className = "widget-empty";
  message.setAttribute("data-testid", "retention-message");
  message.hidden = true;
  container.appendChild(message);

  const warning = document.createElement("p");
  warning.className = "widget-warning";
  warning.setAttribute("data-testid", "retention-warning");
  warning.setAttribute("role", "status");
  warning.hidden = true;
  container.appendChild(warning);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "retention-plot");
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

  let theme = getPlotlyTheme(getActiveTheme());

  let destroyed = false;

  function selectedNames(): string[] {
    // Deterministic: config order, not DOM-event order.
    return allVariables.map((v) => v.name).filter((name) => checkboxes.get(name)?.checked);
  }

  function setSelection(names: Iterable<string>): void {
    const wanted = new Set(names);
    for (const [name, input] of checkboxes) input.checked = wanted.has(name);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    const selected = selectedNames();
    const result = computeRetention(
      data.columns as Record<string, ReadonlyArray<CellValue>>,
      siteLabels!,
      selected,
    );

    // selection summary
    if (selected.length === 0) {
      selectedLine.textContent = "Selected variables: none";
    } else {
      const labels = selected.map((n) => labelOf.get(n) ?? n);
      selectedLine.textContent = `Selected variables (${selected.length}): ${labels.join(", ")}`;
    }

    stats.textContent =
      `Retained ${result.retained.toLocaleString()} of ${result.total.toLocaleString()} ` +
      `participants (${result.retainedPct.toFixed(1)}%) · ` +
      `${result.excluded.toLocaleString()} excluded`;

    const low = !result.noSelection && result.retainedPct < lowRetentionPct;

    message.hidden = !result.noSelection;
    if (result.message) message.textContent = result.message;

    warning.hidden = !low;
    if (low) {
      warning.textContent =
        `This selection keeps under ${lowRetentionPct}% of participants ` +
        `(${result.retainedPct.toFixed(1)}%). Complete-case filtering here removes a large ` +
        `part of the sample — check whether the participants left still represent the ` +
        `sites and groups your question depends on. (${lowRetentionPct}% is a prompt to ` +
        `look closely, not a universal cutoff.)`;
    }

    // machine-testable state
    plot.dataset.selected = selected.join(",");
    plot.dataset.selectedCount = String(selected.length);
    plot.dataset.total = String(result.total);
    plot.dataset.retainedN = String(result.retained);
    plot.dataset.excludedN = String(result.excluded);
    plot.dataset.retainedPct = result.retainedPct.toFixed(2);
    plot.dataset.siteCount = String(result.sites.length);
    plot.dataset.noSelection = String(result.noSelection);
    plot.dataset.lowRetention = String(low);

    const okColor = theme.dark ? "#5a9bd4" : "#2a6f9e";
    const warnColor = theme.dark ? "#d9a441" : "#b5760a";
    const lineColor = theme.dark ? "#d98b8b" : "#a12f2f";
    const barColor = low ? warnColor : okColor;
    const trace = {
      type: "bar" as const,
      x: result.sites.map((s) => s.site),
      y: result.sites.map((s) => s.retainedPct),
      customdata: result.sites.map((s) => [s.retained, s.total] as [number, number]),
      marker: { color: barColor },
      hovertemplate:
        "%{x}<br>Retained %{customdata[0]} of %{customdata[1]} " +
        "(%{y:.1f}%)<extra></extra>",
    };

    const layout = buildPlotLayout(theme, {
      margin: { b: 110 },
      height: 380,
      bargap: 0.2,
      xaxis: {
        title: { text: config.siteLabel },
        tickangle: -45,
      },
      yaxis: {
        title: { text: "Participants retained (%)" },
        range: [0, 105],
      },
      shapes: [
        {
          type: "line" as const,
          xref: "paper" as const,
          x0: 0,
          x1: 1,
          yref: "y" as const,
          y0: result.retainedPct,
          y1: result.retainedPct,
          line: { color: lineColor, width: 1.5, dash: "dash" },
        },
      ],
      annotations: [
        {
          xref: "paper" as const,
          yref: "y" as const,
          x: 1,
          y: result.retainedPct,
          xanchor: "right" as const,
          yanchor: "bottom" as const,
          showarrow: false,
          text: `Overall ${result.retainedPct.toFixed(1)}%`,
          font: { color: lineColor, size: 11 },
        },
      ],
    });

    await Plotly.react(plot, [trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    plot.dataset.barCount = String(result.sites.length);
    const next = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(next);
  }

  for (const input of checkboxes.values()) {
    input.addEventListener("change", () => void draw());
  }
  suggestedBtn.addEventListener("click", () => {
    setSelection(suggested);
    void draw();
  });
  selectAllBtn.addEventListener("click", () => {
    setSelection(allVariables.map((v) => v.name));
    void draw();
  });
  clearBtn.addEventListener("click", () => {
    setSelection([]);
    void draw();
  });

  const unsubscribeTheme = subscribeToThemeChanges((next) => {
    theme = getPlotlyTheme(next);
    void draw();
  });

  // Initial state = the suggested core set.
  setSelection(suggested);
  void draw();

  return {
    destroy() {
      destroyed = true;
      unsubscribeTheme();
      Plotly.purge(plot);
    },
  };
}

export const retentionComponent: WidgetComponent<EdaRetentionConfig, AbideRetentionData> = {
  type: "eda-retention",
  parseData: parseAbideRetentionData,
  mount,
};
