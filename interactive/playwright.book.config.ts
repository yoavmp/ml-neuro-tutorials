import { defineConfig, devices } from "@playwright/test";

// End-to-end tests that run against the *built Jupyter Book* under
// book/_build/html. Requires `jupyter-book build book` to have run first
// (CI does this before invoking `npm run test:e2e:book`).
const PORT = 4174;

export default defineConfig({
  testDir: "./e2e-book",
  // WP49/WP52: Exercises 10-12 are intentionally excluded from
  // book/_toc.yml for this release (their JupyterLite-native migration
  // hasn't started and their legacy iframe-embedded notebook experience
  // should not be published alongside the Exercises 1-9 Lite hub) --
  // chapter 10 no longer exists in the built book, so chapter10.spec.ts,
  // which exists only to exercise that now-unpublished page, would fail on
  // a 404, not on a genuine regression. It is excluded here, not deleted:
  // its source stays for whenever Exercises 10-12 are migrated and
  // republished. WP52 migrated Exercise 9 (see chapter09.spec.ts and
  // exercise-09-lite.spec.ts, both now part of this run) -- its own former
  // iframe-based page, and chapter09-dark-mode.spec.ts's Plotly-color
  // regression guard for that page's iframes, no longer exist at all
  // (deleted, not excluded; see WPs/reports/WP52_REPORT.md).
  // iframe-height-contract.spec.ts stays excluded for an unrelated reason:
  // it generically enumerates every iframe in the built book, and every
  // migrated exercise's transition page (now 1-9) has none -- there is
  // nothing left for it to check until Exercise 10+ migrates too.
  testIgnore: ["**/chapter10.spec.ts", "**/iframe-height-contract.spec.ts"],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  // WP49: the first-ever full combined run across all of Exercises 1-8's
  // lite specs (WP46/47 each deliberately deferred this exact run --
  // "once every notebook is migrated," now true) reproduced real
  // cross-test CPU contention under full default parallelism: 8 failures,
  // every one in Exercises 1/4/6/7's heaviest tests (each a genuine
  // scikit-learn fit running inside Pyodide's WASM sandbox), and every one
  // of those 8 passed cleanly once rerun serialized (`--workers=1`) with
  // zero other tests running concurrently. This is the same contention
  // this file's own screenshot/video/trace history already documents for
  // a smaller exercise count (comment below) -- now reproducing more
  // broadly simply because there are more Pyodide-heavy files to contend
  // with. CI's runner has fewer cores than most local dev machines, so it
  // is more exposed to this, not less. Capped to 1 worker on CI only --
  // slower, not flakier; local runs stay fully parallel for fast iteration.
  ...(process.env.CI ? { workers: 1 } : {}),
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    // WP43RR found this suite's CI failures left nothing to inspect but a
    // bare timeout message. `screenshot: "only-on-failure"` is genuinely
    // free on a passing test (it fires once, only on failure) and stays.
    //
    // Three things were tried and reverted after real CI evidence ruled
    // each one out, in order:
    //   1. `video: "retain-on-failure"` -- Playwright records video
    //      continuously for every test to support this mode. The very
    //      next CI run broke a different, previously always-green test
    //      (iframe-height-contract.spec.ts's Chapter 5 Ridge/Lasso check,
    //      which settle-detects via page.waitForFunction with
    //      { polling: "raf" }) at 1578px received vs >=1620px required.
    //   2. Removing video alone didn't fix it -- the identical test failed
    //      again with the *exact same* 1578px reading, which first looked
    //      like cross-worker CPU contention on CI's 2-vCPU runner (the
    //      other worker was mid-Pyodide-computation at the same wall-clock
    //      moment), so CI was capped to 1 worker to remove that entirely.
    //   3. That didn't fix it either -- fully serialized (1 worker, zero
    //      cross-test contention possible), the exact same test failed
    //      with the exact same 1578px reading a third time. The one
    //      constant across all three failures was `trace:
    //      "retain-on-failure"`, which (like video) records continuously
    //      to support "retain on failure" -- removed here as the real
    //      suspect. If CI evidence ever shows it wasn't `trace` either,
    //      the next thing to suspect is the settle-detection algorithm
    //      itself (rAF-polling can misjudge "stable" under any added
    //      per-frame overhead, self-inflicted or not), not another
    //      capture-mode guess.
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
