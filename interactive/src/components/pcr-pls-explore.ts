// Production activity: Exercise 9's "PCR or PLS?" (WP34).
//
// A fixed, deterministic synthetic 2-D predictor cloud with a fixed 40/20
// train/validation split. One direction explains most of the predictors'
// own variance but only weakly relates to the target; another explains
// less variance but relates to the target more strongly. Only the target's
// alignment preset (weak/moderate/strong alignment with the
// highest-variance direction) changes which precomputed PCR/PLS fit is
// shown -- nothing is fit live here (scripts/export_pcr_pls_widget.py).

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { PcrPlsExploreConfig, PcrPlsMethod, PcrPlsPreset } from "../config";
import {
  parsePcrPlsExploreData,
  catalogEntryFor,
  targetsFor,
  directionLinePoints,
  type PcrPlsExploreData,
} from "../pcr-pls-explore-data";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function symmetricRange(points: readonly { x: number; y: number }[], padFrac: number): [number, number] {
  const maxAbs = Math.max(...points.flatMap((p) => [Math.abs(p.x), Math.abs(p.y)]));
  const padded = maxAbs * (1 + padFrac);
  return [-padded, padded];
}

function mount(args: MountArgs<PcrPlsExploreConfig, PcrPlsExploreData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  const methods = data.methods;
  const componentGrid = data.componentGrid;
  const presetKeys = Object.keys(data.presets) as PcrPlsPreset[];

  let method: PcrPlsMethod = methods.includes(config.defaultMethod) ? config.defaultMethod : methods[0]!;
  let nComponents = componentGrid.includes(config.defaultNComponents) ? config.defaultNComponents : componentGrid[0]!;
  let preset: PcrPlsPreset = presetKeys.includes(config.defaultPreset) ? config.defaultPreset : presetKeys[0]!;

  const axisRange = symmetricRange(data.points, 0.15);

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const syntheticNote = document.createElement("p");
  syntheticNote.className = "widget-note";
  syntheticNote.setAttribute("data-testid", "pcr-pls-synthetic-note");
  syntheticNote.textContent = data.syntheticDataNote;
  container.appendChild(syntheticNote);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  function buildSelect(id: string, testId: string, labelText: string, options: { value: string; label: string }[]): {
    group: HTMLDivElement;
    select: HTMLSelectElement;
  } {
    const group = document.createElement("div");
    group.className = "widget-control";
    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelText;
    const select = document.createElement("select");
    select.id = id;
    select.setAttribute("data-testid", testId);
    for (const opt of options) {
      const o = document.createElement("option");
      o.value = opt.value;
      o.textContent = opt.label;
      select.appendChild(o);
    }
    group.append(label, select);
    return { group, select };
  }

  const methodControl = buildSelect(
    "pcr-pls-method",
    "pcr-pls-method-select",
    "Method:",
    methods.map((m) => ({ value: m, label: m === "pcr" ? "PCR" : "PLS" })),
  );
  const nComponentsControl = buildSelect(
    "pcr-pls-ncomponents",
    "pcr-pls-ncomponents-select",
    "Number of components:",
    componentGrid.map((n) => ({ value: String(n), label: String(n) })),
  );
  // The select's own option text stays short (a native <select> sizes its
  // closed box to its widest OPTION, which cannot wrap) -- the full preset
  // description already lives in the control's own label text above it.
  const PRESET_OPTION_LABELS: Record<PcrPlsPreset, string> = { weak: "Weak", moderate: "Moderate", strong: "Strong" };
  const presetControl = buildSelect(
    "pcr-pls-preset",
    "pcr-pls-preset-select",
    "Target alignment with the highest-variance direction:",
    presetKeys.map((p) => ({ value: p, label: PRESET_OPTION_LABELS[p] ?? data.presets[p]!.label })),
  );

  controls.append(methodControl.group, nComponentsControl.group, presetControl.group);
  container.appendChild(controls);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "pcr-pls-stats");
  stats.setAttribute("role", "status");
  stats.setAttribute("aria-live", "polite");
  container.appendChild(stats);

  const constructionNote = document.createElement("p");
  constructionNote.className = "widget-note";
  constructionNote.setAttribute("data-testid", "pcr-pls-construction-note");
  container.appendChild(constructionNote);

  // --- panels ---------------------------------------------------------
  function panel(titleText: string, testId: string): HTMLDivElement {
    const h = document.createElement("h2");
    h.className = "widget-subhead";
    h.textContent = titleText;
    container.appendChild(h);
    const div = document.createElement("div");
    div.className = "widget-plot";
    div.setAttribute("data-testid", testId);
    div.dataset.renderCount = "0";
    container.appendChild(div);
    return div;
  }

  const cloudPlot = panel("Predictor cloud, colored by target value, with the selected first component", "pcr-pls-cloud-plot");
  const predPlot = panel("Observed versus predicted validation values", "pcr-pls-pred-plot");

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

  // --- drawing ---------------------------------------------------------

  function currentEntry() {
    return catalogEntryFor(data, method, nComponents, preset);
  }

  async function drawCloud(): Promise<void> {
    if (destroyed) return;
    const targets = targetsFor(data, preset);
    const trainSet = new Set(data.trainIds);
    const entry = currentEntry();

    const cloudTrace = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Observations",
      x: data.points.map((p) => p.x),
      y: data.points.map((p) => p.y),
      marker: {
        color: data.points.map((p) => targets[p.id]!),
        colorscale: "Viridis" as const,
        colorbar: { title: { text: "target value" }, thickness: 12 },
        size: data.points.map((p) => (trainSet.has(p.id) ? 8 : 10)),
        symbol: data.points.map((p) => (trainSet.has(p.id) ? "circle" : "diamond")),
        line: { color: theme.axisColor, width: 0.5 },
      },
      hovertemplate: `${data.featureX.label} %{x:.2f}<br>${data.featureY.label} %{y:.2f}<br>target %{marker.color:.2f}<extra></extra>`,
    };

    const halfLength = axisRange[1];
    const line = directionLinePoints(entry.firstComponentDirection, halfLength);
    const directionTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: `First ${method.toUpperCase()} component`,
      x: line.x,
      y: line.y,
      line: { color: theme.diagonalLine, width: 3 },
      hoverinfo: "skip" as const,
    };

    const layout = buildPlotLayout(theme, {
      height: 420,
      showlegend: true,
      xaxis: { title: { text: data.featureX.label }, range: [...axisRange] },
      yaxis: { title: { text: data.featureY.label }, range: [...axisRange], scaleanchor: "x" as const, scaleratio: 1 },
    });
    await Plotly.react(cloudPlot, [cloudTrace, directionTrace], layout, PLOT_CONFIG);
    if (destroyed) return;
    cloudPlot.dataset.renderCount = String(Number(cloudPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawPredictions(): Promise<void> {
    if (destroyed) return;
    const targets = targetsFor(data, preset);
    const entry = currentEntry();
    const observed = data.valIds.map((id) => targets[id]!);
    const predicted = entry.valPredictions;
    const lo = Math.min(...observed, ...predicted);
    const hi = Math.max(...observed, ...predicted);
    const pad = (hi - lo) * 0.1 || 1;

    const scatterTrace = {
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Validation observations",
      x: observed,
      y: predicted,
      marker: { color: theme.markerPrimary, size: 9 },
      hovertemplate: "observed %{x:.2f}<br>predicted %{y:.2f}<extra></extra>",
    };
    const diagonalTrace = {
      type: "scatter" as const,
      mode: "lines" as const,
      name: "Perfect prediction",
      x: [lo - pad, hi + pad],
      y: [lo - pad, hi + pad],
      line: { color: theme.diagonalLine, dash: "dash" as const },
      hoverinfo: "skip" as const,
    };

    const layout = buildPlotLayout(theme, {
      height: 340,
      showlegend: true,
      xaxis: { title: { text: "Observed target" }, range: [lo - pad, hi + pad] },
      yaxis: { title: { text: "Predicted target" }, range: [lo - pad, hi + pad] },
    });
    await Plotly.react(predPlot, [scatterTrace, diagonalTrace], layout, PLOT_CONFIG);
    if (destroyed) return;
    predPlot.dataset.renderCount = String(Number(predPlot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const entry = currentEntry();
    stats.textContent =
      `Method = ${method.toUpperCase()}  ·  components = ${nComponents}  ·  ` +
      `training MSE = ${entry.trainMse.toFixed(2)}  ·  validation MSE = ${entry.valMse.toFixed(2)}.`;
    constructionNote.textContent = entry.constructionNote;
    container.dataset.method = method;
    container.dataset.nComponents = String(nComponents);
    container.dataset.preset = preset;
    container.dataset.trainMse = entry.trainMse.toFixed(4);
    container.dataset.valMse = entry.valMse.toFixed(4);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    drawText();
    await Promise.all([drawCloud(), drawPredictions()]);
  }

  methodControl.select.value = method;
  nComponentsControl.select.value = String(nComponents);
  presetControl.select.value = preset;

  methodControl.select.addEventListener("change", () => {
    method = methodControl.select.value as PcrPlsMethod;
    void draw();
  });
  nComponentsControl.select.addEventListener("change", () => {
    nComponents = Number(nComponentsControl.select.value);
    void draw();
  });
  presetControl.select.addEventListener("change", () => {
    preset = presetControl.select.value as PcrPlsPreset;
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
      Plotly.purge(cloudPlot);
      Plotly.purge(predPlot);
    },
  };
}

export const pcrPlsExploreComponent: WidgetComponent<PcrPlsExploreConfig, PcrPlsExploreData> = {
  type: "pcr-pls-explore",
  parseData: parsePcrPlsExploreData,
  mount,
};
