// Production activity: compare DataFrame.head(), .tail(), and .sample() on the
// curated ABIDE-II table.
//
// A radio group picks the inspection method, a range input sets the row count,
// and (for sample) a "Reshuffle" button advances the seed. An accessible
// <table> and a compact evidence summary (site count, missing cells) are
// recomputed from the pure, unit-tested helpers in src/table-inspection.ts on
// every change. No Python kernel, no CDN, no Plotly. The artifact it reads
// (abide_table_inspection.json) carries every column of the 13-column curated
// table, including the two identifier columns SITE_ID and SUB_ID, because
// seeing the real rows — identifier column included — is the point of comparing
// head(), tail() and sample().

import type { MountArgs, MountHandle, WidgetComponent } from "./types";
import type { TableInspectionConfig } from "../config";
import type { CellValue } from "../retention";
import {
  formatCell,
  selectRowIndices,
  summariseView,
  type InspectionMethod,
} from "../table-inspection";
import {
  parseAbideTableInspectionData,
  type AbideTableInspectionData,
} from "../table-inspection-data";

const METHOD_LABEL: Record<InspectionMethod, string> = {
  head: "head()",
  tail: "tail()",
  sample: "sample()",
};

function mount(
  args: MountArgs<TableInspectionConfig, AbideTableInspectionData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const displayColumns = config.columns.map((c) => c.name);
  const missingColumns = displayColumns.filter(
    (name) => !Object.prototype.hasOwnProperty.call(data.columns, name),
  );
  if (missingColumns.length > 0) {
    throw new Error(
      `The data file is missing column(s) required by this activity: ${missingColumns.join(", ")}.`,
    );
  }
  const siteLabels = data.columns[config.siteField] as string[] | undefined;
  if (!siteLabels) {
    throw new Error(`The data file has no "${config.siteField}" column for site grouping.`);
  }
  const totalRows = data.rowCount;

  let method: InspectionMethod = config.defaultMethod;
  let rows = config.rowCount.default;
  let seed = config.sampleSeed ?? 0;
  let renderCount = 0;
  let destroyed = false;

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

  const methodFieldset = document.createElement("fieldset");
  methodFieldset.className = "widget-radio-group";
  const methodLegend = document.createElement("legend");
  methodLegend.textContent = "Method";
  methodFieldset.appendChild(methodLegend);
  const methodInputs = new Map<InspectionMethod, HTMLInputElement>();
  for (const m of config.methods) {
    const id = `table-inspection-method-${m}`;
    const wrapper = document.createElement("label");
    wrapper.className = "widget-radio";
    wrapper.setAttribute("for", id);
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "table-inspection-method";
    input.id = id;
    input.value = m;
    input.checked = m === method;
    input.setAttribute("data-testid", id);
    const text = document.createElement("span");
    text.textContent = METHOD_LABEL[m];
    wrapper.append(input, text);
    methodFieldset.appendChild(wrapper);
    methodInputs.set(m, input);
  }
  controls.appendChild(methodFieldset);

  const rowsControl = document.createElement("div");
  rowsControl.className = "widget-control";
  const rowsLabel = document.createElement("label");
  rowsLabel.setAttribute("for", "table-inspection-rows");
  rowsLabel.textContent = "Rows";
  const rowsInput = document.createElement("input");
  rowsInput.type = "range";
  rowsInput.id = "table-inspection-rows";
  rowsInput.min = String(config.rowCount.min);
  rowsInput.max = String(config.rowCount.max);
  rowsInput.step = "1";
  rowsInput.value = String(rows);
  rowsInput.setAttribute("data-testid", "table-inspection-rows");
  const rowsValue = document.createElement("span");
  rowsValue.className = "widget-bin-value";
  rowsValue.setAttribute("data-testid", "table-inspection-rows-value");
  rowsValue.textContent = String(rows);
  rowsControl.append(rowsLabel, rowsInput, rowsValue);
  controls.appendChild(rowsControl);

  const reshuffleBtn = document.createElement("button");
  reshuffleBtn.type = "button";
  reshuffleBtn.setAttribute("data-testid", "table-inspection-reshuffle");
  reshuffleBtn.textContent = "Reshuffle sample";
  if (config.methods.includes("sample")) controls.appendChild(reshuffleBtn);

  container.appendChild(controls);

  // --- evidence summary ---
  const summary = document.createElement("p");
  summary.className = "widget-stats";
  summary.setAttribute("data-testid", "table-inspection-summary");
  summary.setAttribute("role", "status");
  summary.setAttribute("aria-live", "polite");
  container.appendChild(summary);

  // --- table ---
  const scroll = document.createElement("div");
  scroll.className = "widget-table-scroll";
  const table = document.createElement("table");
  table.className = "widget-table";
  table.setAttribute("data-testid", "table-inspection-table");
  const caption = document.createElement("caption");
  caption.setAttribute("data-testid", "table-inspection-caption");
  table.appendChild(caption);
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const col of config.columns) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = col.label;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  table.appendChild(tbody);
  scroll.appendChild(table);
  container.appendChild(scroll);

  if (config.reflectionPrompts && config.reflectionPrompts.length > 0) {
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

  function render(): void {
    if (destroyed) return;
    const indices = selectRowIndices(method, totalRows, rows, seed);
    const view = summariseView(
      data.columns as Record<string, ReadonlyArray<CellValue>>,
      siteLabels as ReadonlyArray<string>,
      displayColumns,
      indices,
    );

    rowsValue.textContent = String(rows);
    reshuffleBtn.hidden = method !== "sample";

    const captionTail =
      method === "sample"
        ? `${view.rowCount} rows, seed ${seed}`
        : method === "head"
          ? `first ${view.rowCount} rows`
          : `last ${view.rowCount} rows`;
    caption.textContent = `phenotypes.${METHOD_LABEL[method]} — ${captionTail}`;

    tbody.replaceChildren();
    for (const rowIndex of indices) {
      const tr = document.createElement("tr");
      for (const col of config.columns) {
        const td = document.createElement("td");
        const value = (data.columns[col.name] as ReadonlyArray<CellValue>)[rowIndex];
        if (value === null || value === undefined) {
          td.className = "widget-cell-missing";
          td.textContent = formatCell(value);
          const sr = document.createElement("span");
          sr.className = "widget-visually-hidden";
          sr.textContent = "missing";
          td.appendChild(sr);
        } else {
          td.textContent = formatCell(value);
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }

    // The number of acquisition sites is part of the evidence; the list of site
    // names is deliberately NOT spelled out here (WP10 §1) — the SITE_ID column
    // is visible in the table for anyone who wants the names. `view.sites` is
    // still kept on the table's data-sites attribute for tests/state only.
    const siteWord = view.siteCount === 1 ? "site" : "sites";
    summary.textContent =
      `${METHOD_LABEL[method]} shows ${view.rowCount} rows from ` +
      `${view.siteCount} acquisition ${siteWord}; ` +
      `${view.missingCells} of ${view.totalCells} cells are missing.`;

    table.dataset.method = method;
    table.dataset.rowCount = String(view.rowCount);
    table.dataset.siteCount = String(view.siteCount);
    table.dataset.sites = view.sites.join(",");
    table.dataset.missingCells = String(view.missingCells);
    table.dataset.totalCells = String(view.totalCells);
    table.dataset.seed = String(seed);
    renderCount += 1;
    table.dataset.renderCount = String(renderCount);
  }

  for (const [m, input] of methodInputs) {
    input.addEventListener("change", () => {
      if (input.checked) {
        method = m;
        render();
      }
    });
  }
  rowsInput.addEventListener("input", () => {
    const next = Number(rowsInput.value);
    if (Number.isFinite(next)) {
      rows = Math.max(config.rowCount.min, Math.min(config.rowCount.max, Math.round(next)));
      render();
    }
  });
  reshuffleBtn.addEventListener("click", () => {
    seed = (seed + 1) >>> 0;
    if (method !== "sample") {
      method = "sample";
      const sampleInput = methodInputs.get("sample");
      if (sampleInput) sampleInput.checked = true;
    }
    render();
  });

  render();

  return {
    destroy() {
      destroyed = true;
    },
  };
}

export const tableInspectionComponent: WidgetComponent<
  TableInspectionConfig,
  AbideTableInspectionData
> = {
  type: "table-inspection",
  parseData: parseAbideTableInspectionData,
  mount,
};
