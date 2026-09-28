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
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    // WP43RR found this suite's CI failures left no trace, screenshot, or
    // video to inspect -- only a bare timeout message. Capture on failure
    // only, so a normal green run costs nothing extra.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
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
