import { defineConfig, devices } from "@playwright/test";

// End-to-end tests that run against the *built Jupyter Book* under
// book/_build/html. Requires `jupyter-book build book` to have run first
// (CI does this before invoking `npm run test:e2e:book`).
const PORT = 4174;

export default defineConfig({
  testDir: "./e2e-book",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  // CI's runner has 2 vCPUs and this config's default (unset) workers
  // count used both of them. Two consecutive real CI runs (17b13fc,
  // a016d8e) showed that a CPU-heavy JupyterLite/Pyodide test on one
  // worker starves a completely unrelated, timing-sensitive test running
  // concurrently on the other -- iframe-height-contract.spec.ts's Chapter
  // 5 check uses page.waitForFunction(..., { polling: "raf" }) to detect
  // layout settle, and a busy second worker delays its rAF callbacks
  // enough to report a too-early "stable" height (reproducibly: both
  // failures landed on the exact same 1578px reading). Serializing CI
  // removes that class of cross-test contention entirely; it costs wall-
  // clock time, not correctness, and this workflow has no time limit
  // tighter than GitHub's own 360-minute job default.
  ...(process.env.CI ? { workers: 1 } : {}),
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    // WP43RR found this suite's CI failures left no trace or screenshot to
    // inspect -- only a bare timeout message. `trace`/`screenshot` capture
    // on failure only (zero cost to a green run). `video` was tried too
    // (commit a016d8e) but reverted: Playwright records video continuously
    // for every test to support "retain-on-failure", and the very next CI
    // run failed a *different*, previously always-green test
    // (iframe-height-contract.spec.ts's Chapter 5 check) on a
    // requestAnimationFrame-driven settle-detection race -- exactly the
    // kind of test a busier main thread (continuous video encoding, across
    // every parallel worker) would perturb. Not worth the added CI-load
    // risk for a suite already timing-sensitive under 2-worker CI.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "node e2e-book/serve-book.mjs",
    port: PORT,
    reuseExistingServer: !process.env.CI,
    stdout: "pipe",
    env: { PORT: String(PORT) },
  },
});
