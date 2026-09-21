// Production activity: Exercise 8's "Explore PCA and K-Means" (WP33).
//
// PCA is fit once on the real ABIDE cohort (n=1004); every participant's
// PC1/PC2 score is the same for every retained-PC count because PCA
// components are nested. A precomputed catalogue
// (scripts/export_pca_kmeans_widget.py) covers every (retainedPc, k, seed)
// combination the student can select; nothing is fit live here. The scatter
// plot always shows only PC1-PC2, even though clustering itself used every
// retained component -- the widget states this visibly. External variables
// (diagnosis, sex, site, age) are never inputs to clustering; they are
// joined onto the selected combination's cluster labels only for the
// composition panel, after the student picks which one to inspect.

import Plotly from "plotly.js-cartesian-dist-min";
import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { PcaKmeansExplorerConfig, PcaKmeansExternalVariable } from "../config";
import {
  parsePcaKmeansExplorerData,
  catalogEntryFor,
  externalValuesFor,
  type PcaKmeansExplorerData,
} from "../pca-kmeans-explorer-data";
import {
  clusterColor,
  sharedAxisRange,
  indicesForCluster,
  categoryShareByCluster,
  siteShareMatrix,
  agesByCluster,
} from "../pca-kmeans-explorer";
import { getPlotlyTheme, buildPlotLayout, PLOT_CONFIG } from "./plotly-policy";
import { getActiveTheme, subscribeToThemeChanges } from "../theme";

function mount(args: MountArgs<PcaKmeansExplorerConfig, PcaKmeansExplorerData>): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  let theme = getPlotlyTheme(getActiveTheme());
  let destroyed = false;

  const retainedPcGrid = data.retainedPcGrid;
  const kGrid = data.kGrid;
  const seeds = data.seeds;

  let retainedPc = retainedPcGrid.includes(config.defaultRetainedPc) ? config.defaultRetainedPc : retainedPcGrid[0]!;
  let k = kGrid.includes(config.defaultK) ? config.defaultK : kGrid[0]!;
  let seed = seeds.includes(config.defaultSeed) ? config.defaultSeed : seeds[0]!;
  let externalVariable: PcaKmeansExternalVariable = config.defaultExternalVariable;

  const pc1Range = sharedAxisRange(data.participants.pc1, 0.08);
  const pc2Range = sharedAxisRange(data.participants.pc2, 0.08);

  // --- header ---------------------------------------------------------
  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const instructions = document.createElement("p");
  instructions.className = "widget-instructions";
  instructions.textContent = config.instructions;
  container.appendChild(instructions);

  const cohortNote = document.createElement("p");
  cohortNote.className = "widget-note";
  cohortNote.setAttribute("data-testid", "pca-kmeans-cohort-note");
  cohortNote.textContent = data.cohortNote;
  container.appendChild(cohortNote);

  // --- controls ---------------------------------------------------------
  const controls = document.createElement("div");
  controls.className = "widget-controls";

  function buildSelect(id: string, testId: string, labelText: string, options: (string | number)[]): {
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
      o.value = String(opt);
      o.textContent = String(opt);
      select.appendChild(o);
    }
    group.append(label, select);
    return { group, select };
  }

  const pcControl = buildSelect("pca-kmeans-retained-pc", "pca-kmeans-retained-pc-select", "Retained principal components:", retainedPcGrid);
  const kControl = buildSelect("pca-kmeans-k", "pca-kmeans-k-select", "Number of clusters (k):", kGrid);
  const seedControl = buildSelect("pca-kmeans-seed", "pca-kmeans-seed-select", "Initialization seed:", seeds);
  const externalControl = buildSelect(
    "pca-kmeans-external",
    "pca-kmeans-external-select",
    "Inspect after clustering:",
    [],
  );
  for (const [value, label] of Object.entries(data.externalVariableLabels)) {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = label;
    externalControl.select.appendChild(o);
  }

  controls.append(pcControl.group, kControl.group, seedControl.group, externalControl.group);
  container.appendChild(controls);

  const usesAllRetainedNote = document.createElement("p");
  usesAllRetainedNote.className = "widget-note";
  usesAllRetainedNote.setAttribute("data-testid", "pca-kmeans-uses-all-pc-note");
  usesAllRetainedNote.textContent =
    "Clustering uses every retained principal component selected above, even though the scatter plot below always shows only PC1 and PC2.";
  container.appendChild(usesAllRetainedNote);

  const stats = document.createElement("p");
  stats.className = "widget-stats";
  stats.setAttribute("data-testid", "pca-kmeans-stats");
  stats.setAttribute("role", "status");
  stats.setAttribute("aria-live", "polite");
  container.appendChild(stats);

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

  const scatterPlot = panel("Participants in PC1-PC2 space, colored by cluster", "pca-kmeans-scatter-plot");
  const inertiaPlot = panel("Inertia across candidate k (selected retained-PC count and seed)", "pca-kmeans-inertia-plot");
  const silhouettePlot = panel("Silhouette score across candidate k (same setting)", "pca-kmeans-silhouette-plot");
  const sizesPlot = panel("Cluster sizes", "pca-kmeans-sizes-plot");
  const compositionPlot = panel("Cluster composition for the selected external characteristic", "pca-kmeans-composition-plot");

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

  // --- helpers ---------------------------------------------------------

  function currentEntry() {
    return catalogEntryFor(data, retainedPc, k, seed);
  }

  // --- drawing ---------------------------------------------------------

  async function drawScatter(): Promise<void> {
    if (destroyed) return;
    const entry = currentEntry();
    const traces = [];
    for (let c = 0; c < k; c++) {
      const idx = indicesForCluster(entry.clusterLabels, c);
      traces.push({
        type: "scattergl" as const,
        mode: "markers" as const,
        name: `Cluster ${c}`,
        x: idx.map((i) => data.participants.pc1[i]!),
        y: idx.map((i) => data.participants.pc2[i]!),
        marker: { color: clusterColor(c), size: 5, opacity: 0.65 },
        hovertemplate: `PC1 %{x:.2f}<br>PC2 %{y:.2f}<br>cluster ${c}<extra></extra>`,
      });
    }
    traces.push({
      type: "scatter" as const,
      mode: "markers" as const,
      name: "Cluster centers (arbitrary labels)",
      x: entry.centersPC1PC2.map((c) => c[0]),
      y: entry.centersPC1PC2.map((c) => c[1]),
      marker: {
        color: entry.centersPC1PC2.map((_, c) => clusterColor(c)),
        size: 16,
        symbol: "x" as const,
        line: { color: theme.axisColor, width: 2 },
      },
      hovertemplate: "center PC1 %{x:.2f}<br>PC2 %{y:.2f}<extra></extra>",
    });
    const layout = buildPlotLayout(theme, {
      height: 380,
      showlegend: true,
      xaxis: { title: { text: "PC1" }, range: [...pc1Range] },
      yaxis: { title: { text: "PC2" }, range: [...pc2Range] },
    });
    await Plotly.react(scatterPlot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    scatterPlot.dataset.renderCount = String(Number(scatterPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawInertiaAndSilhouette(): Promise<void> {
    if (destroyed) return;
    const entries = kGrid.map((candidateK) => catalogEntryFor(data, retainedPc, candidateK, seed));

    const inertiaTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Inertia",
      x: kGrid,
      y: entries.map((e) => e.inertia),
      line: { color: theme.markerPrimary },
      marker: {
        color: kGrid.map((candidateK) => (candidateK === k ? theme.diagonalLine : theme.markerPrimary)),
        size: kGrid.map((candidateK) => (candidateK === k ? 12 : 7)),
      },
      hovertemplate: "k=%{x}<br>inertia %{y:.1f}<extra></extra>",
    };
    const inertiaLayout = buildPlotLayout(theme, {
      height: 260,
      xaxis: { title: { text: "k" } },
      yaxis: { title: { text: "Inertia (lower is tighter)" } },
    });
    await Plotly.react(inertiaPlot, [inertiaTrace], inertiaLayout, PLOT_CONFIG);
    if (destroyed) return;
    inertiaPlot.dataset.renderCount = String(Number(inertiaPlot.dataset.renderCount ?? "0") + 1);

    const silhouetteValues = entries.map((e) => e.silhouette);
    const silhouetteTrace = {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Silhouette score",
      x: kGrid,
      y: silhouetteValues,
      line: { color: theme.markerPrimary },
      marker: {
        color: kGrid.map((candidateK) => (candidateK === k ? theme.diagonalLine : theme.markerPrimary)),
        size: kGrid.map((candidateK) => (candidateK === k ? 12 : 7)),
      },
      connectgaps: false,
      hovertemplate: "k=%{x}<br>silhouette %{y:.3f}<extra></extra>",
    };
    const silhouetteLayout = buildPlotLayout(theme, {
      height: 260,
      xaxis: { title: { text: "k" } },
      yaxis: { title: { text: "Silhouette score (higher is more separated)" }, range: [-1, 1] },
    });
    await Plotly.react(silhouettePlot, [silhouetteTrace], silhouetteLayout, PLOT_CONFIG);
    if (destroyed) return;
    silhouettePlot.dataset.renderCount = String(Number(silhouettePlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawSizes(): Promise<void> {
    if (destroyed) return;
    const entry = currentEntry();
    const trace = {
      type: "bar" as const,
      x: entry.clusterSizes.map((_, c) => `Cluster ${c}`),
      y: entry.clusterSizes,
      marker: { color: entry.clusterSizes.map((_, c) => clusterColor(c)) },
      hovertemplate: "%{x}: %{y} participants<extra></extra>",
    };
    const layout = buildPlotLayout(theme, {
      height: 240,
      xaxis: { title: { text: "Cluster" } },
      yaxis: { title: { text: "Participants" } },
    });
    await Plotly.react(sizesPlot, [trace], layout, PLOT_CONFIG);
    if (destroyed) return;
    sizesPlot.dataset.renderCount = String(Number(sizesPlot.dataset.renderCount ?? "0") + 1);
  }

  async function drawComposition(): Promise<void> {
    if (destroyed) return;
    const entry = currentEntry();
    const values = externalValuesFor(data, externalVariable);
    let traces: Record<string, unknown>[];
    let layout: Record<string, unknown>;

    if (externalVariable === "age") {
      const ages = agesByCluster(entry.clusterLabels, k, values as number[]);
      traces = ages.map((clusterAges, c) => ({
        type: "box" as const,
        name: `Cluster ${c}`,
        y: clusterAges,
        marker: { color: clusterColor(c) },
        boxpoints: false,
      }));
      layout = buildPlotLayout(theme, { height: 300, yaxis: { title: { text: "Age" } } });
    } else if (externalVariable === "site") {
      const { sites, z } = siteShareMatrix(entry.clusterLabels, k, values as string[]);
      traces = [
        {
          type: "heatmap" as const,
          x: Array.from({ length: k }, (_, c) => `Cluster ${c}`),
          y: sites,
          z,
          colorscale: "Viridis" as const,
          colorbar: { title: { text: "share of site" }, thickness: 12 },
          hovertemplate: "site=%{y}<br>%{x}<br>share %{z:.2f}<extra></extra>",
        },
      ];
      layout = buildPlotLayout(theme, {
        height: Math.max(260, sites.length * 18 + 80),
        xaxis: { title: { text: "Cluster" }, type: "category" as const },
        yaxis: { title: { text: "Acquisition site" }, type: "category" as const },
      });
    } else {
      // group (diagnosis) or sex: normalized bars per cluster.
      const stringValues = (externalVariable === "group" ? (values as number[]).map(String) : (values as string[]));
      const shares = categoryShareByCluster(entry.clusterLabels, k, stringValues);
      traces = shares.map(({ category, sharesByCluster }) => ({
        type: "bar" as const,
        name: externalVariable === "group" ? (category === "1" ? "Autism (group=1)" : "Control (group=2)") : category,
        x: Array.from({ length: k }, (_, c) => `Cluster ${c}`),
        y: sharesByCluster,
        hovertemplate: "%{x}<br>share %{y:.2f}<extra></extra>",
      }));
      layout = buildPlotLayout(theme, {
        height: 300,
        showlegend: true,
        barmode: "stack" as const,
        xaxis: { title: { text: "Cluster" } },
        yaxis: { title: { text: "Proportion" }, range: [0, 1] },
      });
    }

    await Plotly.react(compositionPlot, traces, layout, PLOT_CONFIG);
    if (destroyed) return;
    compositionPlot.dataset.renderCount = String(Number(compositionPlot.dataset.renderCount ?? "0") + 1);
  }

  function drawText(): void {
    const entry = currentEntry();
    const sizesText = entry.clusterSizes.map((s, c) => `cluster ${c}=${s}`).join(", ");
    const silText = entry.silhouette === null ? "not computable" : entry.silhouette.toFixed(3);
    stats.textContent =
      `Retained PCs = ${retainedPc}  ·  k = ${k}  ·  seed = ${seed}  ·  inertia = ${entry.inertia.toFixed(1)}  ·  ` +
      `silhouette = ${silText}  ·  sizes: ${sizesText}.`;
    container.dataset.retainedPc = String(retainedPc);
    container.dataset.k = String(k);
    container.dataset.seed = String(seed);
    container.dataset.externalVariable = externalVariable;
    container.dataset.inertia = entry.inertia.toFixed(2);
  }

  async function draw(): Promise<void> {
    if (destroyed) return;
    drawText();
    await Promise.all([drawScatter(), drawInertiaAndSilhouette(), drawSizes(), drawComposition()]);
  }

  pcControl.select.value = String(retainedPc);
  kControl.select.value = String(k);
  seedControl.select.value = String(seed);
  externalControl.select.value = externalVariable;

  pcControl.select.addEventListener("change", () => {
    retainedPc = Number(pcControl.select.value);
    void draw();
  });
  kControl.select.addEventListener("change", () => {
    k = Number(kControl.select.value);
    void draw();
  });
  seedControl.select.addEventListener("change", () => {
    seed = Number(seedControl.select.value);
    void draw();
  });
  externalControl.select.addEventListener("change", () => {
    externalVariable = externalControl.select.value as PcaKmeansExternalVariable;
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
      Plotly.purge(scatterPlot);
      Plotly.purge(inertiaPlot);
      Plotly.purge(silhouettePlot);
      Plotly.purge(sizesPlot);
      Plotly.purge(compositionPlot);
    },
  };
}

export const pcaKmeansExplorerComponent: WidgetComponent<PcaKmeansExplorerConfig, PcaKmeansExplorerData> = {
  type: "pca-kmeans-explorer",
  parseData: parsePcaKmeansExplorerData,
  mount,
};
