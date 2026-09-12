// Runtime entry point. Responsibilities, in order:
//   1. read + validate the `config` URL from the page URL (same-origin only)
//   2. fetch + validate the config JSON (explicit schemaVersion + typed union)
//   3. resolve the data URL against the CONFIG url (not the page), same-origin
//   4. fetch + validate the data via the component's own schema
//   5. dispatch to the component looked up in the registry
//
// URL / config / DOM-state logic lives here and in urls.ts / config.ts. All
// plotting + data-shape logic lives in the component. No eval, no innerHTML with
// external strings — error text goes through textContent only.

import "./styles.css";
import { parseActivityConfigJson } from "./config";
import { resolveConfigUrl, resolveDataUrl } from "./urls";
import { registry } from "./components/registry";
import type { MountHandle } from "./components/types";

const root = document.getElementById("app");

function renderStatus(message: string): void {
  if (!root) return;
  root.replaceChildren();
  const p = document.createElement("p");
  p.className = "widget-status";
  p.setAttribute("role", "status");
  p.setAttribute("aria-live", "polite");
  p.textContent = message;
  root.appendChild(p);
}

function renderError(summary: string, detail?: string): void {
  if (!root) return;
  root.replaceChildren();
  const box = document.createElement("section");
  box.className = "widget-error";
  box.setAttribute("role", "alert");
  box.setAttribute("data-testid", "widget-error");

  const h = document.createElement("h2");
  h.textContent = "This activity could not be loaded";
  box.appendChild(h);

  const p = document.createElement("pre");
  p.setAttribute("data-testid", "widget-error-message");
  p.textContent = detail ? `${summary}\n\n${detail}` : summary;
  box.appendChild(p);

  root.appendChild(box);
}

async function fetchText(url: URL, what: string): Promise<string> {
  let res: Response;
  try {
    res = await fetch(url.href, { credentials: "omit", mode: "same-origin" });
  } catch (e) {
    throw new Error(`Could not fetch ${what} (${url.href}): ${(e as Error).message}`);
  }
  if (!res.ok) {
    throw new Error(`Could not fetch ${what}: HTTP ${res.status} for ${url.href}`);
  }
  return res.text();
}

let activeHandle: MountHandle | undefined;

async function boot(): Promise<void> {
  if (!root) return;
  window.addEventListener("beforeunload", () => activeHandle?.destroy());

  renderStatus("Loading activity…");

  const configUrlResult = resolveConfigUrl(window.location.href);
  if (!configUrlResult.ok) {
    renderError(configUrlResult.error);
    return;
  }
  const configUrl = configUrlResult.url;

  let configText: string;
  try {
    configText = await fetchText(configUrl, "the activity config");
  } catch (e) {
    renderError((e as Error).message);
    return;
  }

  const configResult = parseActivityConfigJson(configText);
  if (!configResult.ok) {
    renderError(configResult.error);
    return;
  }
  const config = configResult.config;

  const component = registry.get(config.type);
  if (!component) {
    renderError(
      `No component is registered for activity type "${config.type}". ` +
        `Known types: ${registry.knownTypes().join(", ") || "(none)"}.`,
    );
    return;
  }

  const dataUrlResult = resolveDataUrl(configUrl.href, config.data);
  if (!dataUrlResult.ok) {
    renderError(dataUrlResult.error);
    return;
  }

  renderStatus("Loading activity data…");
  let dataText: string;
  try {
    dataText = await fetchText(dataUrlResult.url, "the activity data");
  } catch (e) {
    renderError((e as Error).message);
    return;
  }

  let dataJson: unknown;
  try {
    dataJson = JSON.parse(dataText);
  } catch (e) {
    renderError(`Activity data is not valid JSON: ${(e as Error).message}`);
    return;
  }

  const dataResult = await component.parseData(dataJson, dataUrlResult.url);
  if (!dataResult.ok) {
    renderError(dataResult.error);
    return;
  }

  try {
    root.replaceChildren();
    activeHandle = component.mount({
      container: root,
      config,
      data: dataResult.data,
    });
    root.setAttribute("data-widget-ready", "true");
  } catch (e) {
    renderError("The activity failed while rendering.", (e as Error).message);
  }
}

void boot();
