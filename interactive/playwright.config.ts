import { defineConfig, devices } from "@playwright/test";

// `pretest:e2e` runs `npm run build` first, so book/_static/widgets/app/ exists
// before this server starts. Chromium only; the project-managed binary must be
// installed with `npx playwright install chromium`.
const PORT = 4173;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "off",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "node e2e/serve-static.mjs",
    port: PORT,
    reuseExistingServer: !process.env.CI,
    stdout: "pipe",
    env: { PORT: String(PORT) },
  },
});
