# WP37 — Deploy Exercises 7–9

## Purpose

Deploy the accumulated, locally reviewed course-book work from WP32 through WP36 so the latest
versions of Exercises 7–9 become available on GitHub Pages.

This is a **deployment-only** work package. Do not redesign, edit, regenerate, or otherwise change
notebook, widget, dataset, model, test, configuration, dependency, or workflow content. The only
permitted new files are:

- this WP37 specification, committed as a checkpoint before release work;
- the two final WP37 deployment reports, committed locally after the deployment attempt.

The release should make these completed notebooks live:

- Exercise 7: **Boosting and Gradient Boosting**;
- Exercise 8: **Unsupervised Learning**;
- Exercise 9: **Advanced Models**.

Exercises 1–6 must remain intact. Exercises 10–12 must remain placeholder pages. The Syllabus and
Word course overview must remain unchanged.

---

## 1. Expected starting state

Start from `fix/wp36-pcr-pls-alignment-scale`, whose reported final full branch-tip SHA is:

```text
46efa0889e3b7b67a7e4b80f838000c5c21f12ac
```

Treat the following as expectations to verify, not assumptions to force:

- `origin/main` was last successfully deployed at
  `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4` (WP31R3 release);
- local `main` was then reported one documentation-only commit ahead at
  `a64e3492d8796dcda67c7f59b414df5977e8b989`;
- the WP32–WP36 branch chain should descend linearly from that local `main`;
- `fix/wp36-pcr-pls-alignment-scale` should include the complete WP32 → WP33 → WP34 → WP35 →
  WP36 history and all of their reports;
- the only permitted pre-existing untracked files are:
  - `WPs/reports/WP16_ARCHITECT_REPORT.md`;
  - `WPs/reports/WP21_DEPLOYMENT_REPORT.md`;
  - this WP37 specification before its checkpoint commit.

Do not touch, add, delete, rename, or commit the two legacy untracked reports.

If the observed state differs materially from these expectations, stop and report it. Do not
resolve divergence automatically.

---

## 2. Save the deployment specification first

1. Switch to `fix/wp36-pcr-pls-alignment-scale` if necessary.
2. Record:
   - `git status --short --branch`;
   - `git rev-parse HEAD`;
   - `git log --oneline --decorate -12`.
3. Confirm HEAD is exactly
   `46efa0889e3b7b67a7e4b80f838000c5c21f12ac` and that no unexpected modified or untracked file
   exists.
4. Save this specification as:

   ```text
   WPs/WP37_DEPLOY_EXERCISES_7_TO_9.md
   ```

5. Commit **only** this specification as a deployment checkpoint.
6. Record its full SHA as `WP37_CHECKPOINT_SHA`.

Do not begin release validation before this checkpoint exists.

---

## 3. Verify local and remote ancestry

Run exactly one remote update before comparing history:

```bash
git fetch origin main
```

Then verify all of the following with read-only Git commands:

1. `origin/main` is still exactly
   `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`.
2. Local `main` is still exactly
   `a64e3492d8796dcda67c7f59b414df5977e8b989`.
3. `origin/main` is an ancestor of local `main`.
4. `origin/main..main` contains exactly the expected WP31R3 documentation-only commit and no
   implementation change.
5. Local `main` is an ancestor of `WP37_CHECKPOINT_SHA`.
6. The checkpoint contains the linear WP32–WP36 history, including these branch milestones as
   discoverable in the local repository:
   - WP32 Exercise 7 implementation and reports;
   - WP33 Exercise 8 implementation and reports;
   - WP34 Exercise 8 correction and Exercise 9 implementation and reports;
   - WP35 Exercises 7–9 review corrections and reports;
   - WP36 PCR/PLS correction and reports.
7. The diff `main..WP37_CHECKPOINT_SHA` contains only intended Exercises 7–9 work, shared
   infrastructure/tests required by those exercises, their portable notebooks, and WP
   documentation. It must not contain an intentional Syllabus or Word-overview change.
8. The working tree contains no file other than the two whitelisted untracked legacy reports.

Capture the relevant full SHAs, ancestry results, decorated graph, commit list, and diff summaries
for the final report.

### Mandatory stop condition

If `origin/main` advanced, local `main` differs unexpectedly, ancestry is not linear, the feature
branch does not descend from local `main`, or an unrelated change appears, **stop immediately**.
Do not pull, reset, rebase, cherry-pick, stash, force-update, delete, or resolve anything
automatically. Report the discrepancy and ask for direction.

---

## 4. Bounded pre-deployment validation

Run these gates once, in order, on the WP37 checkpoint branch. This WP is not permitted to repair
implementation. If any gate fails, stop and document the failure for a separate correction WP.

### 4.1 Stored-artifact and portable-notebook checks

1. Run the existing **check-only** modes for the committed Exercise 7–9 artifacts. At minimum,
   inspect the repository and run the applicable existing commands for:
   - gradient-boosting model results;
   - boosting-step widget data;
   - boosting-parameter widget data;
   - PCA/K-means results;
   - PCA-projection widget data;
   - PCA/K-means widget data;
   - advanced-model comparison results;
   - PCR/PLS widget data;
   - SVM-explorer widget data.

   Use `--check` or the repository's equivalent only. Do **not** run `--run`, `--refresh`, or any
   command that recomputes/replaces committed artifacts. In particular, do not rerun the expensive
   Exercise 7 grid or Exercise 9 nested-CV audit in this deployment WP.

2. Run the portable-notebook generator's deterministic check for all registered notebooks:

   ```bash
   python scripts/build_portable_notebook.py --check --notebook all
   ```

3. Run the repository's registered portable-notebook smoke command once. Do not add another
   independent smoke execution unless the current registry demonstrably omits Exercise 7, 8, or 9.
   If one of those chapters is omitted, smoke-execute only that missing portable notebook once in a
   `mktemp -d` directory and remove the temporary directory afterward.

### 4.2 Repository and build gates

4. Run the full offline Python test suite once:

   ```bash
   python -m unittest discover -s tests -p 'test_*.py'
   ```

5. In `interactive/`, run once each:

   ```bash
   npm run typecheck
   npm test
   npm run build
   ```

   If `npm test` already includes typecheck in the current package scripts, do not run the same
   typecheck a second time; record the actual behavior.

6. Run one clean Jupyter Book build using the project's active virtual environment and existing
   pinned dependencies:

   ```bash
   jupyter-book clean book
   jupyter-book build book
   ```

   Do not install or upgrade dependencies unless a dependency is genuinely missing; if one is
   missing, stop rather than modifying dependency files in this deployment WP.

### 4.3 Focused browser gates

7. Run the existing focused standalone Playwright specifications for all Exercise 7–9 activities
   once.
8. Run the existing built-book Playwright specifications for:
   - Exercises 7, 8, and 9;
   - their dark-mode behavior;
   - iframe-height behavior;
   - launch/download/Colab buttons;
   - the Chapter 1 dark-mode regression test that previously blocked deployment.
9. Include a 390px/narrow-viewport check through existing specs. Do not create a permanent test or
   modify production code in WP37 merely to repeat a check already covered.

The full standalone and built-book suites passed in WP36. Do **not** rerun both entire Playwright
suites locally unless inspection shows that the deployment workflow itself requires them as a
pre-publish gate that the focused selection above does not reproduce. The GitHub Actions workflow
will remain the authoritative full integration run.

### Validation discipline

- One attempt per gate.
- No speculative reruns.
- No stress loops or `--repeat-each` runs.
- No arbitrary sleeps.
- No weakened assertions, skipped tests, global retries, or test edits.
- No notebook re-execution or artifact refresh unless a listed check explicitly requires it.
- If a gate fails, stop; do not fix it under WP37.

Record every command, duration where readily available, pass/fail result, warning, and skipped test
in the report.

---

## 5. Merge into local `main`

Only after every pre-deployment gate passes:

1. Switch to local `main`.
2. Reconfirm:
   - HEAD is still exactly `a64e3492d8796dcda67c7f59b414df5977e8b989`;
   - `origin/main` is still the verified release ancestor;
   - the working tree is clean except for the two whitelisted legacy reports.
3. Merge with one non-fast-forward commit:

   ```bash
   git merge --no-ff fix/wp36-pcr-pls-alignment-scale -m "Merge Exercises 7-9 course materials"
   ```

4. If any conflict occurs, stop without resolving it.
5. Record the full merge SHA as `RELEASE_SHA`.
6. Prove that the merged `main` tree is identical to the WP37 checkpoint tree. The histories may
   differ because of the merge commit; file contents must not.
7. Confirm the only untracked files are still the two whitelisted legacy reports.

Do not amend, squash, rebase, fast-forward, or rewrite the accumulated WP history.

---

## 6. Push exactly once

After the merge and tree-identity checks pass:

```bash
git push origin main
```

Rules:

- Perform exactly one push during WP37.
- Never force-push.
- If the push is rejected, interrupted, or fails, stop. Do not pull, rebase, retry, or issue a
  second push.
- After success, use a read-only remote query to verify that `origin/main` points to `RELEASE_SHA`.

---

## 7. Monitor exactly one GitHub Actions run

Identify the deployment workflow run triggered by `RELEASE_SHA`.

1. Query once for a run associated with `RELEASE_SHA`.
2. If no matching run is visible, wait at most **30 seconds** and query once more.
3. If still absent, stop and report that no run was discovered. Do not continue polling.
4. Once found, record the workflow name and run ID.
5. Start exactly one foreground watcher:

   ```bash
   gh run watch RUN_ID --exit-status
   ```

6. Give that single watcher a hard wall-clock limit of **15 minutes**. If it has not returned by
   then, interrupt it once, record the last visible workflow state, and stop.
7. Do not:
   - start the watcher in the background;
   - schedule wakeups;
   - poll in parallel or afterward;
   - launch a second watcher;
   - rerun a failed/cancelled/timed-out workflow;
   - push a repair commit.

If the workflow fails, record its failing job/step and the concise relevant log excerpt, then stop.
Any repair belongs in a new WP.

---

## 8. Verify production

Perform this section only after the workflow succeeds. Verify the deployed GitHub Pages site, not
localhost:

```text
https://yoavmp.github.io/ml-neuro-tutorials/
```

Use a fresh browser context and cache-busting query strings. Confirm the live assets correspond to
`RELEASE_SHA`, rather than accepting cached HTML or JavaScript.

### 8.1 Site structure and unchanged material

Verify HTTP success, rendered titles, sidebar order, and expected status for:

- `/chapters/chapter_01/exercise_01.html` through
  `/chapters/chapter_06/exercise_06.html` — still present and not visibly regressed;
- `/chapters/chapter_07/exercise_07.html` — **Boosting and Gradient Boosting**, no longer a
  placeholder;
- `/chapters/chapter_08/exercise_08.html` — **Unsupervised Learning**, no longer a placeholder;
- `/chapters/chapter_09/exercise_09.html` — **Advanced Models**, no longer a placeholder;
- Exercises 10–12 — still placeholder pages;
- Exercise 13 — still absent;
- Syllabus — unchanged;
- Word course overview — unchanged in the repository release diff.

Verify the Colab and downloadable-notebook links for Exercises 7–9 resolve to the correct portable
notebooks.

### 8.2 Exercise 7 — Boosting and Gradient Boosting

Confirm that:

- the notebook uses student-facing language and contains no author/operator-facing audit notes;
- the boosting-step activity loads and its controls update the plot and metrics;
- the parameter-explorer activity loads and changing depth, learning rate, and number of trees
  updates the visual result;
- the partial-grid explanation clearly presents computational cost as a practical consideration;
- the complete-pipeline results appear as the intended grouped bar graph, with:
  - MSE on the y-axis;
  - max-depth groups;
  - learning-rate colors;
  - number-of-trees labels/subgroups;
- plots, legends, and labels remain visible in both themes and at narrow width.

### 8.3 Exercise 8 — Unsupervised Learning

Confirm that:

- the central question about learning from brain measurements without a target is visibly
  emphasized;
- the PCA-projection activity updates correctly;
- the cumulative explained-variance y-axis begins at 0;
- regional loading summaries are present and readable;
- K-means is framed as the method used here to demonstrate clustering, rather than the only
  possible clustering method;
- the PCA/K-means activity updates for different `k` values;
- the cluster legend remains outside the participant plot and does not cover points at larger `k`;
- the text guides students to compare inertia, silhouette score, and the age pattern without
  falsely claiming that one metric gives an unambiguous answer;
- Section 8 is titled **Using PCA in a Supervised Pipeline** and uses PCA before a previously
  learned KNN model, not PCR.

### 8.4 Exercise 9 — Advanced Models

Confirm that:

- PCR, PLS, SVM/SVR, and kernels are introduced concisely;
- the PCR/PLS activity loads and the control is framed as alignment with the
  **highest-variance direction**;
- the activity explicitly states that signal strength and noise are held constant and only target
  direction changes;
- one-component PCR validation performance improves from Weak → Moderate → Strong alignment;
- PLS's advantage over PCR shrinks across those same settings;
- displayed validation MSE and R² agree with the committed corrected artifact;
- PCR and PLS converge when two components are retained;
- the SVM-boundary activity responds to its controls;
- the real ABIDE advanced-model comparison remains present and unchanged from its reviewed WP35
  state;
- the expensive full nested comparison remains optional by default and the embedded results render
  immediately.

### 8.5 Theme, responsive layout, iframe height, and runtime

For every interactive activity in Exercises 7–9:

- verify light mode;
- switch the **book's own theme toggle** to dark mode while the OS/browser preference is light;
- reload at least one page while dark mode is already active and confirm correct first paint;
- verify Plotly backgrounds, gridlines, marks, legends, controls, and text follow the intended
  theme;
- verify Plotly drag layers are transparent and do not cover axis titles;
- verify controls actually change figures/metrics rather than text alone;
- verify the iframe height contracts after rendering and leaves no large empty lower region;
- verify no content is clipped after interaction;
- verify a 390px viewport has no page-level horizontal overflow.

Inspect browser-console errors and distinguish new product errors from the two historically
documented, unrelated Thebe/theme-bootstrap messages. A new runtime error is a stop condition.

Prefer the repository's existing production-capable Playwright specs. If a temporary production
verification script is required, create it only in `mktemp -d`, do not commit it, and remove the
temporary directory afterward.

---

## 9. Stop conditions

Stop immediately and do not improvise if any of these occurs:

- unexpected Git divergence, history, or working-tree content;
- failed pre-deployment validation gate;
- missing dependency during validation;
- merge conflict or merged-tree mismatch;
- failed or rejected push;
- no matching workflow after the two bounded discovery queries;
- watcher exceeds 15 minutes;
- failed or cancelled workflow;
- production serves stale or broken content after a successful workflow;
- an activity changes text but not its figure;
- material theme, iframe-height, clipping, narrow-layout, launch-link, or runtime regression.

Do not reset, repair, rerun, repush, or start WP38. Record the exact blocker for the user.

---

## 10. Deployment reports

After successful production verification—or immediately after any stop condition—create:

```text
WPs/reports/WP37_DEPLOYMENT_REPORT.md
WPs/reports/WP37_EXACT_CHANGELOG.md
```

The deployment report must include:

1. overall `SUCCESS` or `FAILURE`;
2. starting WP36 SHA and `WP37_CHECKPOINT_SHA`;
3. verified starting local `main` and `origin/main` SHAs;
4. ancestry, commit-history, and diff evidence;
5. every pre-deployment command and result, including durations where available;
6. all warnings, skips, deviations, and bounded stop decisions;
7. `RELEASE_SHA` if a merge occurred;
8. the single push result;
9. workflow name, run ID, discovery attempts, watch duration, and conclusion;
10. every production URL and behavior checked;
11. light/dark, reload, narrow-layout, iframe-height, console, Colab, and download results;
12. anything requiring the user's attention;
13. literal final `git status --short --branch` and a short decorated log.

The exact changelog must list only the files introduced by WP37 itself and accurately explain that
the release content came from the pre-existing WP32–WP36 branch chain.

Commit the two reports together **locally on `main` only** after the deployment attempt. Record
that full SHA as `DOCUMENTATION_SHA`. Do not push this documentation commit, because that would
trigger a second deployment.

The intended successful final state is:

- `origin/main` at `RELEASE_SHA`;
- local `main` exactly one documentation-only commit ahead at `DOCUMENTATION_SHA`;
- only the two whitelisted legacy reports remain untracked and untouched;
- the GitHub Pages site serves Exercises 7–9 from the new release;
- WP38 has not been started.

---

## 11. Final response to the user

Return a short summary containing:

- success/failure;
- `RELEASE_SHA` and `DOCUMENTATION_SHA` when applicable;
- workflow run ID and result;
- whether Exercises 7–9 are confirmed live;
- any issue that requires user attention;
- literal final `git status --short --branch`.

Do not merely say “done”; distinguish clearly between local merge, remote push, successful Actions
publication, and verified production state.
