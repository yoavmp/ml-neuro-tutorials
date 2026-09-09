// DEVELOPER SMOKE TEST — NOT COURSE CONTENT.
//
// `runtime-smoke` exists only to prove the runtime end to end: load a validated
// config + data file, bundle Plotly locally, render a chart, and redraw it from
// a labelled control with a full Plotly.react() call. It deliberately does no
// statistics. The ABIDE histogram / retention activities are separate later work.

import Plotly from "plotly.js-cartesian-dist-min";
import { z } from "zod";
import type {
  DataResult,
  MountArgs,
  MountHandle,
  WidgetComponent,
} from "./types";
import type { RuntimeSmokeConfig } from "../config";

const seriesSchema = z.object({
  label: z.string().min(1),
  categories: z.array(z.string().min(1)).min(1),
  values: z.array(z.number().finite()).min(1),
});

const runtimeSmokeDataSchema = z
  .object({
    schemaVersion: z.literal(1),
    series: z.array(seriesSchema).min(2, "runtime-smoke needs at least two series to switch between"),
  })
  .strict()
  .superRefine((data, ctx) => {
    data.series.forEach((s, i) => {
      if (s.categories.length !== s.values.length) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["series", i],
          message: `series "${s.label}" has ${s.categories.length} categories but ${s.values.length} values`,
        });
      }
    });
  });

export type RuntimeSmokeData = z.infer<typeof runtimeSmokeDataSchema>;

function parseData(raw: unknown): DataResult<RuntimeSmokeData> {
  const parsed = runtimeSmokeDataSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => {
        const p = i.path.join(".");
        return p ? `${p}: ${i.message}` : i.message;
      })
      .join("; ");
    return { ok: false, error: `Invalid runtime-smoke data: ${msg}` };
  }
  return { ok: true, data: parsed.data };
}

function traceFor(series: RuntimeSmokeData["series"][number]) {
  return {
    type: "bar" as const,
    x: series.categories,
    y: series.values,
    name: series.label,
    marker: { color: "#2a7f62" },
  };
}

function mount(
  args: MountArgs<RuntimeSmokeConfig, RuntimeSmokeData>,
): MountHandle {
  const { container, config, data } = args;
  container.replaceChildren();

  const heading = document.createElement("h1");
  heading.className = "widget-title";
  heading.textContent = config.title;
  container.appendChild(heading);

  const devNote = document.createElement("p");
  devNote.className = "widget-devnote";
  devNote.setAttribute("data-role", "dev-smoke-marker");
  devNote.textContent =
    "Developer smoke test for the widget runtime — not student material.";
  container.appendChild(devNote);

  const controls = document.createElement("div");
  controls.className = "widget-controls";

  const label = document.createElement("label");
  label.setAttribute("for", "runtime-smoke-series");
  label.textContent = "Plotted series:";
  const select = document.createElement("select");
  select.id = "runtime-smoke-series";
  select.setAttribute("data-testid", "series-select");
  data.series.forEach((s, i) => {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = s.label;
    select.appendChild(opt);
  });
  controls.append(label, select);
  container.appendChild(controls);

  const plot = document.createElement("div");
  plot.className = "widget-plot";
  plot.setAttribute("data-testid", "runtime-smoke-plot");
  plot.dataset.renderCount = "0";
  container.appendChild(plot);

  const plotConfig = { displayModeBar: false, responsive: true };
  const layout = {
    margin: { t: 10, r: 10, b: 40, l: 40 },
    height: 320,
    bargap: 0.25,
    xaxis: { title: { text: "category" } },
    yaxis: { title: { text: "value" } },
  };

  let destroyed = false;

  async function draw(index: number): Promise<void> {
    const series = data.series[index];
    if (!series || destroyed) return;
    // Full redraw, not a partial restyle, so the trace data genuinely changes.
    await Plotly.react(plot, [traceFor(series)], layout, plotConfig);
    if (destroyed) return;
    const next = Number(plot.dataset.renderCount ?? "0") + 1;
    plot.dataset.renderCount = String(next);
    plot.dataset.activeSeries = series.label;
    plot.dataset.activeIndex = String(index);
  }

  select.addEventListener("change", () => {
    void draw(Number(select.value));
  });

  void draw(0);

  return {
    destroy() {
      destroyed = true;
      Plotly.purge(plot);
    },
  };
}

export const runtimeSmokeComponent: WidgetComponent<
  RuntimeSmokeConfig,
  RuntimeSmokeData
> = {
  type: "runtime-smoke",
  parseData,
  mount,
};
