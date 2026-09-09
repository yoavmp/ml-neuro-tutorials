// URL handling for the widget runtime.
//
// Pure functions only: no DOM, no fetch, no Plotly. Everything here is unit
// tested in tests/urls.test.ts. The runtime never trusts a URL it did not
// resolve and same-origin-check through these helpers.

export type UrlResult =
  | { ok: true; url: URL }
  | { ok: false; error: string };

const ALLOWED_PROTOCOLS = new Set(["http:", "https:"]);

function checkSafe(url: URL, sameOrigin: URL, label: string): UrlResult {
  if (!ALLOWED_PROTOCOLS.has(url.protocol)) {
    return {
      ok: false,
      error: `${label} must use http or https, not "${url.protocol}". ` +
        `file:// and other protocols are not supported.`,
    };
  }
  if (url.username !== "" || url.password !== "") {
    return { ok: false, error: `${label} must not embed credentials.` };
  }
  if (url.origin !== sameOrigin.origin) {
    return {
      ok: false,
      error:
        `${label} must be same-origin as the activity page ` +
        `(${sameOrigin.origin}); got ${url.origin}.`,
    };
  }
  return { ok: true, url };
}

/**
 * Read the required `config` query parameter from the application page URL and
 * resolve it against that page URL. Rejects missing / malformed / cross-origin /
 * credentialed / non-http(s) values with a readable message.
 */
export function resolveConfigUrl(pageUrl: string): UrlResult {
  let page: URL;
  try {
    page = new URL(pageUrl);
  } catch {
    return { ok: false, error: "The activity page URL is not a valid URL." };
  }

  const raw = page.searchParams.get("config");
  if (raw === null || raw.trim() === "") {
    return {
      ok: false,
      error:
        'Missing required "config" query parameter. Embed this activity as ' +
        "…/app/index.html?config=../configs/<activity>.json",
    };
  }

  let resolved: URL;
  try {
    resolved = new URL(raw, page);
  } catch {
    return { ok: false, error: `The "config" value is not a resolvable URL: ${raw}` };
  }

  return checkSafe(resolved, page, 'The "config" URL');
}

/**
 * Resolve a data reference found *inside* a config file against the config file's
 * own URL — never against the browser page — then apply the same safety checks.
 */
export function resolveDataUrl(configUrl: string, dataRef: string): UrlResult {
  let base: URL;
  try {
    base = new URL(configUrl);
  } catch {
    return { ok: false, error: "The config URL used to resolve data is invalid." };
  }

  if (typeof dataRef !== "string" || dataRef.trim() === "") {
    return { ok: false, error: 'The config "data" field must be a non-empty URL string.' };
  }

  let resolved: URL;
  try {
    resolved = new URL(dataRef, base);
  } catch {
    return { ok: false, error: `The config "data" value is not a resolvable URL: ${dataRef}` };
  }

  return checkSafe(resolved, base, 'The config "data" URL');
}
