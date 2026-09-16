// Centralized dark/light theme detection for every embedded activity (WP22).
//
// Root cause this replaces: every component used to call
// `window.matchMedia("(prefers-color-scheme: dark)")` once, at mount time,
// on the IFRAME's OWN window. That only reflects the OS/browser preference.
// The published book (pydata-sphinx-theme) resolves the reader's own
// light/dark/auto choice onto `document.documentElement.dataset.theme` (and
// `.dataset.mode`) of the PARENT document -- see
// pydata_sphinx_theme/assets/scripts/pydata-sphinx-theme.js `setTheme()`.
// Toggling that control does not touch `prefers-color-scheme` at all, so an
// iframe that only checks its own media query silently keeps rendering
// whatever theme it started in, and never redraws when the reader switches.
//
// This module is the one place that knows how to resolve "what theme is
// active" and how to be told when that changes. Every Plotly-bearing
// component subscribes here instead of re-deriving its own answer.
export type Theme = "light" | "dark";

function resolveFromElement(el: Element | null | undefined): Theme | null {
  if (!el) return null;
  const theme = el.getAttribute("data-theme");
  if (theme === "light" || theme === "dark") return theme;
  const mode = el.getAttribute("data-mode");
  if (mode === "light" || mode === "dark") return mode;
  return null;
}

function prefersDarkMedia(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return null;
  try {
    return window.matchMedia("(prefers-color-scheme: dark)");
  } catch {
    return null;
  }
}

// Same-origin only: a cross-origin parent throws on `.document` access, and a
// standalone/top-level load has no parent to read at all. Both are normal,
// supported ways to open this app, not failures.
function parentDocumentElement(): Element | null {
  try {
    if (typeof window !== "undefined" && window.parent && window.parent !== window) {
      return window.parent.document.documentElement;
    }
  } catch {
    // cross-origin parent: fall through to the app's own signals.
  }
  return null;
}

/** The theme that should be active right now. */
export function getActiveTheme(): Theme {
  const fromParent = resolveFromElement(parentDocumentElement());
  if (fromParent) return fromParent;

  // Defensive: covers a standalone page (or a test harness) that sets
  // data-theme/data-mode directly on its own document, same as the book does
  // on its parent.
  const fromOwn = typeof document !== "undefined" ? resolveFromElement(document.documentElement) : null;
  if (fromOwn) return fromOwn;

  const media = prefersDarkMedia();
  if (media && media.matches) return "dark";
  return "light";
}

/**
 * Calls `onChange` with the newly-active theme whenever it changes: the
 * parent book's `data-theme`/`data-mode` attribute is toggled, this app's own
 * document is (test harnesses), or -- when neither parent nor own attributes
 * are present -- the OS/browser `prefers-color-scheme` preference changes.
 * Returns a cleanup function that disconnects every observer/listener; safe
 * to call more than once.
 */
export function subscribeToThemeChanges(onChange: (theme: Theme) => void): () => void {
  const cleanups: Array<() => void> = [];
  // Callers (this app's own `main.ts`) legitimately write the resolved theme
  // onto this document's own root so styles.css can key off it -- so a
  // "notify only when the resolved theme actually changed" guard is not
  // just an optimization here, it is what keeps the own-document observer
  // below from re-triggering itself: without it, writing "dark" over an
  // already-"dark" attribute still fires a MutationObserver record, which
  // would call back in and write "dark" again, forever.
  let lastNotified = getActiveTheme();
  const notify = () => {
    const next = getActiveTheme();
    if (next === lastNotified) return;
    lastNotified = next;
    onChange(next);
  };

  const parentEl = parentDocumentElement();
  if (parentEl) {
    try {
      const observer = new MutationObserver(notify);
      observer.observe(parentEl, { attributes: true, attributeFilter: ["data-theme", "data-mode"] });
      cleanups.push(() => observer.disconnect());
    } catch {
      // Same-origin access can still be denied by an embedding policy this
      // app doesn't control; degrade to the fallbacks below instead of
      // throwing out of a component's mount().
    }
  } else if (typeof document !== "undefined") {
    // Only watched when there is no parent to defer to: a standalone page
    // (or a test harness) that sets data-theme/data-mode directly on its own
    // document, the same way the book sets it on its parent. When embedded,
    // this app's own root is a WRITE target (main.ts mirrors the resolved
    // theme onto it for styles.css), never a source of truth, so watching it
    // too would just be observing this app's own writes.
    try {
      const ownObserver = new MutationObserver(notify);
      ownObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme", "data-mode"],
      });
      cleanups.push(() => ownObserver.disconnect());
    } catch {
      // ignore
    }
  }

  const media = prefersDarkMedia();
  if (media) {
    try {
      media.addEventListener("change", notify);
      cleanups.push(() => media.removeEventListener("change", notify));
    } catch {
      // Safari < 14
      type LegacyMediaQueryList = MediaQueryList & {
        addListener(listener: (ev: MediaQueryListEvent) => void): void;
        removeListener(listener: (ev: MediaQueryListEvent) => void): void;
      };
      const legacy = media as LegacyMediaQueryList;
      legacy.addListener(notify);
      cleanups.push(() => legacy.removeListener(notify));
    }
  }

  return () => {
    for (const cleanup of cleanups) cleanup();
  };
}
