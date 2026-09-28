# WP43RR report: one rerun and production verification

## Success or failure

**Failed — the same rerun, at the same head SHA, reproduced the exact same
single Playwright timeout as WP43R.** Per this WP's Gate B, the rerun was
performed exactly once and no retry, fix, or second push followed.
**Production remains completely unaffected**: `gh-pages` is unchanged and
the live site still serves the pre-WP41 content. Live verification of
Exercises 1 and 2 (Gate C) was not performed, because the workflow did not
succeed and there is nothing new to verify.

## Gate A — preflight (all confirmed, nothing had drifted)

- Branch/status: `main`, one commit ahead of `origin/main` (the local-only
  `WP43R: reports` commit, `39dd049`), plus the untracked WP43RR text file
  itself. No other untracked or modified files. `Homework_Materials/` not
  touched.
- Local `main`: `39dd04946b74176b6a7f6971c16786d1365bf8c9`.
- `origin/main`: `89c9bccab37c1ab295f16ef55251d4c90a04a0cf` — matches the
  WP43R report exactly.
- `origin/gh-pages`: `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`
  (`deploy: 58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`) — matches the WP43R
  report exactly, unchanged.
- Most recent workflow run before this WP:
  [`36414417778`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36414417778),
  head SHA `89c9bcc`, conclusion `failure` (the WP43R run). No run was
  active or queued.
- `requirements.txt` confirmed still pins `ipywidgets==8.1.9`; `deploy.yml`
  confirmed still contains the course-toolbar build step, the JupyterLite
  build step, and the combined `End-to-end test the combined book +
  JupyterLite build` step, all at the current `origin/main` tip.
- No reset, stash, stage, rebase, or push was performed in this gate.

Nothing had advanced or diverged from what the WP43R report described, so
the rerun proceeded on the existing pushed SHA as authorized.

## Gate B — the one rerun

Triggered `gh run rerun 36414417778` (no new commit, no new push) at
2026-09-28T11:54:36Z. This created **attempt 2** of the existing run, same
run ID, same head SHA `89c9bcc`.

- Run: [`36414417778`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36414417778)
  (attempt 2), job `build-and-deploy` (`108915252487`).
- Started: 2026-09-28T11:54:43Z. Completed: 2026-09-28T12:23:32Z.
  **Duration: 28m49s** — inside the ~40-minute bound, consistent with the
  prior run's 29m2s.
- **Result: failure.**

### What passed

Every step through **"Build JupyterLite (Exercises 1 and 2)"** succeeded
again, identically to WP43R: dependency install, course-toolbar build,
Python unit tests (`ipywidgets` import fixed), Jupyter Book build, notebook
execution-error check, JupyterLite build, and the standalone widget-app
end-to-end suite.

### What failed — recurred exactly

**"End-to-end test the combined book + JupyterLite build"**, using
`playwright test --config playwright.book.config.ts`, **2 workers**, 149
tests:

```
1) [chromium] › e2e-book/exercise-02-lite.spec.ts:110:3 ›
   Exercise 2 — JupyterLite notebook › Section 8 slider is operable and
   updates the figure

Error: expect(locator).toBeVisible() failed
Locator:  locator('.widget-slider .noUi-handle').first()
Expected: visible
Received: <element(s) not found>
Timeout:  5000ms

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('.widget-slider .noUi-handle').first()

  125 |     await expect(handle).toBeVisible({ timeout: 5_000 });
      |                          ^
  at interactive/e2e-book/exercise-02-lite.spec.ts:125:26

148 passed (18.2m)
1 failed
```

- Same spec file, same line (110:3), same failing assertion (line 125:26),
  same locator (`.widget-slider .noUi-handle`), same 5000ms timeout, same
  `<element(s) not found>` result as WP43R's run.
- **Worker count: 2 workers in both attempt 1 (the WP43R run) and attempt 2
  (this rerun)** — confirmed by pulling attempt 1's own log
  (`Running 149 tests using 2 workers`, job `108901997609`). This
  contradicts the "6-worker parallel-load contention" flakiness hypothesis
  WP43R's report offered as the leading explanation; the actual CI worker
  count for this suite is 2 in both runs, not 6.
- **Individual test timing was nearly identical across both attempts**: the
  test itself ran 1.9m before failing in attempt 1, 2.0m in attempt 2 — the
  failure is not an early- or late-timing outlier in either run, and the
  overall suite duration was 18.2m in both.
- The test failed on the **final assertion in the test** (line 125, waiting
  for the slider handle), after roughly two minutes of prior test body
  (kernel start, same-origin data load, prior-section checks/executions for
  this notebook) had already completed inside the same test — i.e., by the
  time the slider-visibility wait began, the notebook, kernel, and earlier
  cells for this test were already up and had already passed their own
  checks earlier in the same spec. Playwright's list reporter does not
  print sub-test step timestamps, so it cannot be determined from this log
  alone whether the specific widget-rendering cell for Section 8 had begun
  executing, finished executing, or errored silently before the 5-second
  visibility wait started; no trace, screenshot, or video artifact exists
  to inspect further (see below).
- No trace/screenshot/video artifact is available for either attempt: the
  workflow (`.github/workflows/deploy.yml`) has no `upload-artifact` step
  for Playwright output, and `gh api .../runs/36414417778/artifacts`
  returned an empty list. This is a pre-existing gap in the workflow, not
  something this WP introduced or was authorized to fix.
- No `Execute the portable notebook outside the repository` or
  `Publish website` step ran (both `skipped`, since they sit after the
  failed step in the same job).

**Assessment**: two independent CI runs of the identical workflow at the
identical commit, on different GitHub-hosted runners, both failed at the
exact same assertion with the exact same symptom and near-identical timing.
This is evidence *against* the "isolated, transient CI-resource
contention" theory WP43R's report offered as plausible-but-unconfirmed; a
genuinely load-driven flake would be less likely to reproduce this
precisely twice in a row. It is *consistent with* a real, deterministic
issue specific to Exercise 2's Section 8 slider widget under this
CI/build/runner combination (e.g., a JupyterLite/Pyodide widget-rendering
timing issue that does not occur, or occurs faster, in the maintainer's
local `.venv`/browser environment used for the 149/149 local runs in WP43
and WP43R). This WP does not investigate further or propose a fix — that
determination and any change is explicitly out of this WP's scope per Gate
B ("Stop after this one failed rerun. Do not weaken assertions, raise
timeouts blindly, change notebook code, push a fix, or start another
workflow in this WP").

## Gate C — not applicable

The workflow did not succeed, so Gate C's live-site verification of
Exercises 1 and 2 was **not performed** — there is nothing new published to
verify. Confirmed instead, per Gate B's closing instruction, that
production remains unchanged:

- `origin/gh-pages` re-fetched after the rerun: still
  `f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`
  (`deploy: 58ed1c61f43f0b3c6d23c1f32212bf2d3b9c9f0b`) — identical to the
  Gate A baseline. The "Publish website" step never ran (`skipped`).
- Live HTTP checks: hub `https://yoavmp.github.io/ml-neuro-tutorials/` →
  `200` (unchanged pre-WP41 content); `lite/notebooks/index.html` → `404`
  (the JupyterLite tree is still not published).
- **No partial or broken deployment. Production is exactly as it was
  before this WP**, identical to the state WP43 and WP43R each left it in.

## Current state and concrete next step for the course author

- `origin/main` is unchanged at `89c9bcc` (all of WP41/41R/42/43/43R).
  Pages has still not republished; the live site is untouched.
- The `ipywidgets` clean-CI fix from WP43R remains proven and stable across
  three separate CI runs now (WP43R's run + this WP's two attempts all pass
  the same dependency, build, and unit-test steps cleanly).
- The sole remaining blocker is unchanged in identity but is now better
  characterized: `exercise-02-lite.spec.ts:110` ("Section 8 slider is
  operable and updates the figure") has failed identically in **two
  consecutive CI runs** of the unmodified spec and unmodified notebook, at
  2 workers each time, with near-identical timing. Given WP43/WP43R's own
  149/149 clean local runs, the discrepancy looks CI-environment-specific
  rather than purely random flakiness, and reproducing twice in a row
  lowers confidence in a one-off-timeout explanation. Recommended next
  step for a future, separately authorized WP: reproduce this specific
  test against a real, unmodified JupyterLite build in an environment as
  close to the GitHub-hosted runner as practical (or add a Playwright
  trace/screenshot/video upload step to the workflow first, to get direct
  evidence next time, without touching the test or notebook itself), before
  deciding whether the issue is CI-runner performance, a genuine
  Section-8-widget timing race, or something else. That investigation and
  any code change is for the next WP, not this one.

## Deviations from the WP text

None of substance. This report and the exact changelog are committed
locally on `main` but are **not pushed**, to avoid triggering a fourth
`Build and deploy Jupyter Book` run solely to publish reports, per the WP's
explicit instruction.
