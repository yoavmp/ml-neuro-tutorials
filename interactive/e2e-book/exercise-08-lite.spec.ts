import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// End-to-end proof that the migrated Exercise 8 JupyterLite notebook works
// in a real browser against the actual combined jupyter-book + jupyter-lite
// build (WP47), modeled on exercise-07-lite.spec.ts. Deliberately kept SMALL
// per the WP47 spec's own time-discipline instruction ("a small Exercise 8
// Playwright smoke and a teacher-completed path"), not the larger per-blank
// coverage exercise-06/07-lite.spec.ts use for notebooks with far heavier
// per-blank compute (a GridSearchCV search taking up to 15-20 minutes
// alone). Exercise 8's own heaviest supplied step (Section 5's pipeline:
// component_grid x k_grid = 20 combinations x 5 folds, up to 100 PCA
// components, on 753 training rows) is two orders of magnitude cheaper than
// that, so this file budgets proportionally less wait time.
//
// None of this notebook's five "YOUR CODE HERE" blanks (the PCA fit,
// variance figure, PC1-vs-PC2 scatter, loadings figure, and K-means
// results) is guarded by a raise-on-missing-prerequisite cell: each one's
// own check cell (or, for the one supplied cell that reads a blank's output,
// an explicit `"X_pca" in globals()` guard) degrades gracefully to "Not
// complete yet" instead, so "Run All Cells" on the UNTOUCHED template
// produces zero error cells at all (verified offline first in
// tests/test_exercise_08_reference_execution.py's companion student-template
// execution check, and confirmed again here, live, in a real Pyodide
// kernel).
//
// Exercise 8's own JupyterLite notebook view has no per-exercise dark-mode
// Playwright coverage, matching the exact precedent already set by
// Exercises 1-7's own *-lite.spec.ts files (none of them test dark mode
// either) -- the dedicated per-chapter dark-mode specs this course does
// have (chapter01-dark-mode.spec.ts etc.) only ever covered the OLD,
// Plotly-in-iframe activities that read `prefers-color-scheme` directly;
// once an exercise migrates to a native JupyterLite notebook, that
// mechanism and its own dark-mode regression risk no longer exist (the
// notebook runs inside JupyterLite's own application theme, not the book's
// pydata-sphinx-theme toggle). This is flagged explicitly in the WP47
// report rather than silently skipped.

test.setTimeout(240_000);

const NOTEBOOK_URL = "/lite/notebooks/index.html?path=exercise_08.ipynb";

async function scrollWindowed(page: Page, fraction: number) {
  await page.evaluate((f) => {
    const el = document.querySelector(".jp-WindowedPanel-outer");
    if (el) el.scrollTop = el.scrollHeight * f;
  }, fraction);
  await page.waitForTimeout(400);
}

async function scrollToVisible(
  page: Page,
  text: string,
  cellSelector = ".jp-CodeCell",
): Promise<import("@playwright/test").Locator> {
  const locator = page.locator(cellSelector, { hasText: text }).first();
  for (let f = 0; f <= 1.001; f += 0.05) {
    await scrollWindowed(page, f);
    if ((await locator.count()) > 0 && (await locator.boundingBox())) {
      return locator;
    }
  }
  throw new Error(`cell containing "${text}" never became visible while scrolling`);
}

// WP49: replaced this file's old fixed 90_000ms wait with a poll on
// JupyterLab's own semantic kernel-status attribute (unknown -> busy ->
// idle, confirmed live by watching it transition across a real Run All
// Cells) -- environment-independent, unlike a fixed duration. Found live
// (exercise-04/06/07-lite.spec.ts, WP49): a fixed wait that is usually
// enough can still leave the kernel genuinely busy when a test
// interacts right after, which can trigger a JupyterLite app-level
// reload. See exercise-07-lite.spec.ts for the full writeup.
async function waitForKernelIdle(page: Page, timeoutMs = 600_000) {
  await page.waitForFunction(
    () => document.querySelector(".jp-Notebook-ExecutionIndicator")?.getAttribute("data-status") === "idle",
    undefined,
    { timeout: timeoutMs, polling: 1_000 },
  );
}

async function runAllCells(page: Page) {
  await page.click("text=Run");
  await page.waitForTimeout(200);
  await page.locator(".lm-Menu-itemLabel", { hasText: "Run All Cells" }).first().click();
  await waitForKernelIdle(page);
}

async function fillBlank(page: Page, anchorText: string, solution: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  const isMac = process.platform === "darwin";
  await page.keyboard.press(`${isMac ? "Meta" : "Control"}+A`);
  await page.keyboard.press("Backspace");
  await page.keyboard.insertText(solution);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(600);
}

async function runCell(page: Page, anchorText: string) {
  const target = await scrollToVisible(page, anchorText);
  const editor = target.locator(".cm-content").first();
  await editor.click();
  await page.waitForTimeout(150);
  await page.keyboard.press("Shift+Enter");
  await page.waitForTimeout(1_500);
}

test.describe("Exercise 8 — JupyterLite notebook, untouched template", () => {
  test("Run All Cells: no error cells, data loads, and every blank's check cell shows guidance", async ({
    page,
  }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    expect(await page.locator(".jp-mod-error").count()).toBe(0);

    await scrollWindowed(page, 0.05);
    await expect(page.locator("body")).toContainText("360 cortical-thickness predictors", { timeout: 5_000 });

    for (const anchor of [
      "define Xs, pca_explore, and X_pca above first",
      "define pca_variance_fig above first",
      "define pca_scatter_fig above first",
      "define pca_loadings_fig above first",
      "define kmeans_results, kmeans_inertia_fig, and kmeans_silhouette_fig above first",
    ]) {
      const cell = await scrollToVisible(page, anchor);
      await expect(cell.locator(".jp-OutputArea-output").last()).toContainText("Not complete yet");
    }

    // Section 4's activity and Section 5's supplied pipeline are both
    // independent of the student's own blanks, so they must still produce
    // real results on an untouched template.
    await expect(page.locator("body")).toContainText(
      "This activity is using: a fixed, independently computed PCA",
    );
    await expect(page.locator("body")).toContainText("n_train (development) = 753");
  });

  test("stays usable at a 390px viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(4000);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(2);
  });

  test("reset restores the template and Back returns to Contents", async ({ page }) => {
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await page.waitForTimeout(3000);

    await page.click("text=Reset from course template");
    await page.waitForTimeout(800);
    await page.locator(".jp-Dialog-button", { hasText: "Reset" }).first().click();
    await page.waitForTimeout(2000);

    await scrollWindowed(page, 0);
    await page.click("text=Back to course contents");
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("contents.html");
  });
});

test.describe("Exercise 8 — JupyterLite notebook, teacher-completed path", () => {
  test("filling in all five blanks reproduces the established results, the native widget responds, every checked question grades, and download contains the edits", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    await page.goto(NOTEBOOK_URL, { waitUntil: "load" });
    await expect(page.locator("text=Python (Pyodide)")).toBeVisible({ timeout: 20_000 });
    await runAllCells(page);

    await fillBlank(
      page,
      "# Xs = StandardScaler().fit_transform",
      "Xs = StandardScaler().fit_transform(df[FEATURES].to_numpy(float))\n" +
        "pca_explore = PCA(n_components=50, random_state=0).fit(Xs)\n" +
        "X_pca = pca_explore.transform(Xs)\n" +
        "print(Xs.shape, X_pca.shape)",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "EVR_TOLERANCE = 0.08");
    let check = await scrollToVisible(page, "Looks good: PC1 explained variance");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# pca_variance_fig, axes = plt.subplots(1, 2",
      "cumulative = np.cumsum(pca_explore.explained_variance_ratio_)\n" +
        "pca_variance_fig, axes = plt.subplots(1, 2, figsize=(11, 4))\n" +
        "axes[0].bar(range(1, 16), pca_explore.explained_variance_ratio_[:15])\n" +
        "axes[1].plot(range(1, 51), cumulative[:50] * 100, marker='.')\n" +
        "axes[1].axhline(50, color='0.5', ls='--')\n" +
        "plt.show()",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, "CUMVAR_TOLERANCE = 0.1");
    check = await scrollToVisible(page, "Looks good: cumulative explained variance through PC50");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# pca_scatter_fig, ax = plt.subplots(figsize=(5.5, 5))",
      "pca_scatter_fig, ax = plt.subplots(figsize=(5.5, 5))\n" +
        "scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=df['age'], cmap='viridis_r', s=8, alpha=0.6)\n" +
        "plt.colorbar(scatter, ax=ax)\n" +
        "plt.show()",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, 'if "pca_scatter_fig" in globals():');
    check = await scrollToVisible(page, "Looks good: pca_scatter_fig is defined");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# loadings = pca_explore.components_",
      "loadings = pca_explore.components_\n" +
        "pca_loadings_fig, axes = plt.subplots(1, 2, figsize=(11, 4))\n" +
        "for i, ax in enumerate(axes):\n" +
        "    order = np.argsort(-np.abs(loadings[i]))[:N_TOP]\n" +
        "    ax.barh(range(N_TOP), loadings[i][order][::-1])\n" +
        "plt.show()",
    );
    await page.waitForTimeout(3_000);
    await runCell(page, 'if "pca_loadings_fig" in globals():');
    check = await scrollToVisible(page, "Looks good: pca_loadings_fig is defined");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    await fillBlank(
      page,
      "# cluster_X = X_pca[:, :N_CLUSTER_COMPONENTS]",
      "from sklearn.cluster import KMeans\n" +
        "from sklearn.metrics import silhouette_score\n" +
        "cluster_X = X_pca[:, :N_CLUSTER_COMPONENTS]\n" +
        "kmeans_results = []\n" +
        "for k in K_CANDIDATES:\n" +
        "    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(cluster_X)\n" +
        "    sil = float(silhouette_score(cluster_X, km.labels_)) if k >= 2 else None\n" +
        "    kmeans_results.append({'k': k, 'inertia': float(km.inertia_), 'silhouette': sil})\n" +
        "kmeans_inertia_fig, ax = plt.subplots()\n" +
        "ax.plot([r['k'] for r in kmeans_results], [r['inertia'] for r in kmeans_results], marker='o')\n" +
        "plt.show()\n" +
        "kmeans_silhouette_fig, ax = plt.subplots()\n" +
        "sil_results = [r for r in kmeans_results if r['silhouette'] is not None]\n" +
        "ax.plot([r['k'] for r in sil_results], [r['silhouette'] for r in sil_results], marker='o')\n" +
        "plt.show()",
    );
    await page.waitForTimeout(5_000);
    await runCell(page, "SIL_TOLERANCE = 0.15");
    check = await scrollToVisible(page, "Looks good: silhouette at k=3");
    await expect(check.locator(".jp-OutputArea-output").last()).toContainText("Looks good");

    // The native "Explore PCA and K-Means" widget cell already ran once
    // during the initial Run All Cells, before X_pca existed -- like any
    // notebook, a cell does not retroactively re-execute just because an
    // earlier cell changed. Re-run it now so it picks up the student's own
    // completed X_pca, then confirm the source note updated and that
    // changing a control visibly changes the rendered summary line.
    await runCell(page, "_act_retained_dd = widgets.Dropdown");
    await page.waitForTimeout(2_000);
    await expect(page.locator("body")).toContainText("This activity is using: your own completed PCA");
    const widget = await scrollToVisible(page, "Retained PCs:", ".jp-CodeCell");
    await expect(page.locator("body")).toContainText("retained PCs=10  k=3", { timeout: 5_000 });
    await widget.locator("select").nth(1).selectOption({ index: 2 }); // k dropdown -> 4
    await page.waitForTimeout(2_000);
    await expect(page.locator("body")).toContainText("k=4", { timeout: 10_000 });

    // Every checked question: correct feedback.
    for (const [anchor, correctSubstring] of [
      ["Without a target label, what can an unsupervised analysis help us explore?", "Correct"],
      ["With no target column supplied, what information", "Correct"],
      ["What can visible separation", "Correct"],
      ["As k increases, what happens to inertia and silhouette", "Correct"],
      ["does increasing the number of retained components change", "Correct"],
      ["Why must Section 5's pipeline refit StandardScaler and PCA", "Correct"],
    ] as const) {
      const q = await scrollToVisible(page, anchor, ".jp-OutputArea-output");
      const labels = q.locator(".widget-radio-box label");
      await expect(labels.first()).toBeVisible({ timeout: 5_000 });
      await labels.first().click();
      await q.locator("button", { hasText: "Check answer" }).click();
      await page.waitForTimeout(400);
      await expect(q.locator(`text=/^${correctSubstring}/`)).toBeVisible();
    }

    // One question, deliberately answered wrong: incorrect feedback, no
    // "Correct" text, and no visible answer key anywhere in that cell.
    const q2 = await scrollToVisible(page, "With no target column supplied, what information", ".jp-OutputArea-output");
    const q2Labels = q2.locator(".widget-radio-box label");
    await q2Labels.nth(1).click();
    await q2.locator("button", { hasText: "Check answer" }).click();
    await page.waitForTimeout(400);
    await expect(q2.locator("text=/^Not quite/")).toBeVisible();
    expect(await q2.innerText()).not.toContain("correct_index");

    // Download contains the completed work.
    const downloadDir = fs.mkdtempSync(path.join(os.tmpdir(), "wp47-e2e-"));
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("text=Download my notebook"),
    ]);
    const savePath = path.join(downloadDir, "exercise_08.ipynb");
    await download.saveAs(savePath);
    const downloaded = fs.readFileSync(savePath, "utf8");
    expect(downloaded).not.toContain("# YOUR CODE HERE\\n# Xs = StandardScaler");
    expect(downloaded).toContain("kmeans_results = []");
  });
});
