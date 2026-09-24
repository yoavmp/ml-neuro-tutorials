# WP39 — Deploy Exercise 10

## Purpose

Merge the completed and reviewed Exercise 10 work into `main`, push it once, allow the existing
GitHub Actions workflow to build and publish the book, and verify the live Exercise 10 page.

The release source is the final clean tip of:

`fix/wp38r-exercise10-review`

This is a deployment-only work package. Do not alter notebook content, model results, data
artifacts, widget behavior, dependencies, or tests unless a pre-deployment stop condition is
encountered. If anything fails, stop and report; do not repair it inside WP39.

WP40 must not be started.

---

## 1. Starting-state verification

Before doing anything destructive or state-changing:

1. Run `git status --short --branch`.
2. Record the full SHAs of:
   - `fix/wp38r-exercise10-review`;
   - local `main`;
   - `origin/main` after one `git fetch origin main`.
3. Confirm the WP38R branch contains:
   - WP38 checkpoint `06fd62af0ea0eee8bcf5cc20274c8a5a1d8f7602`;
   - WP38 implementation `61a16c6f26a81b32c76c884b3122d266edc31bc1`;
   - WP38 report commit `3b8cdeaf40413ceeec8585ac6c0b838387a82ee2`;
   - WP38R checkpoint `6c8a3a7a67dce0993a4e775e26c00bd6352ecc2f`;
   - all WP38R implementation commits listed in `WPs/reports/WP38R_REPORT.md`;
   - one final WP38R report commit at the branch tip.
4. Read the actual WP38R tip SHA from Git. Do not infer or guess it from the report.
5. Confirm the WP38R working tree is clean.
6. Confirm local `main` is still based on `origin/main` and differs only by the expected local-only
   WP37/WP37V documentation commits:
   - `bf6aaa2`;
   - `2f74ccae826d14da9dee9997d890697d159d91c0`.
7. Confirm `origin/main` is still at, or is an ancestor of, the previously deployed release
   `f792ad55f34342e627ed1fe3b85ff60777507d85`.
8. Confirm the Syllabus and Word course overview have not changed on the WP38R branch relative to
   local `main`.

If `origin/main` has advanced unexpectedly, the branch is dirty, ancestry differs, or unrelated
files have changed, stop and report. Do not pull, reset, rebase, stash, force-push, or resolve
divergence automatically.

Save this specification at:

`WPs/WP39_DEPLOY_EXERCISE_10.md`

Commit only this specification on `fix/wp38r-exercise10-review` as a deployment checkpoint before
running validation.

Record the resulting checkpoint SHA. This checkpoint becomes part of the release tree.

---

## 2. Confirm the intended release diff

Inspect the complete diff from local `main` to the WP39 checkpoint.

The diff should contain only the reviewed WP38/WP38R work and documentation, including:

- Exercise 10 canonical and portable notebooks;
- Exercise 10 widget configs, components, data, and tests;
- UCI HAR compact data and provenance;
- the KNN leakage laboratory and its audited artifact;
- the five-balance classification activity and its audited artifact;
- shared iframe resizing fixes and their tests;
- portable-generator/launch-button registration for Chapter 10;
- placeholder/test updates needed because Exercise 10 is now complete;
- WP38, WP38R, and WP39 documentation.

Confirm that the diff does **not** modify:

- `book/syllabus.md`;
- the Word course-overview document;
- Exercises 1–9 notebook content, except shared infrastructure/tests that WP38R explicitly
  documented;
- Exercises 11–12 placeholder content;
- dependency pins or the deployment workflow, unless such a change was already explicitly
  documented in WP38/WP38R.

If the diff contains an unexpected file or content change, stop without merging.

---

## 3. Bounded pre-deployment validation

Use the project's existing virtual environment and installed frontend dependencies. Do not
upgrade packages or refresh model/data artifacts.

Run each gate once, in this order:

1. Exercise 10 committed-artifact checks, offline only:
   - UCI HAR compact-data/provenance check;
   - HAR grouped-split audit check;
   - HAR widget-export check;
   - KNN leakage-lab export check;
   - class-balance comparison export check;
   - relevant ABIDE manifest/self-consistency check.
2. `python scripts/build_portable_notebook.py --check --notebook all`.
3. Smoke-execute only Chapter 10's portable notebook outside the repository using the registered
   smoke command.
4. Run the focused Python tests for Exercise 10, its exporters/audits, portable behavior, and
   launch/book structure.
5. Run the full offline Python test suite once.
6. In `interactive/`, run frontend typecheck and the full unit-test suite once.
7. Run one frontend production build.
8. Run the focused standalone Playwright specs for:
   - the multiple-selection quiz;
   - KNN leakage laboratory;
   - HAR participant-group activity;
   - class-balance comparison;
   - resize-shrink regression.
9. Run one clean Jupyter Book build.
10. Run focused built-book specs for:
    - Chapter 10 structure/interactions;
    - launch buttons;
    - quantitative iframe-height contract;
    - dark-mode behavior;
    - 390 px layout and overflow;
    - unexpected console errors.
11. Perform one manual local visual check of Exercise 10 at desktop and 390 px in light and dark
    mode, confirming:
    - the quiz question does not overlap its options;
    - every activity fits its content without a large empty lower region;
    - no plot label, legend, control, or feedback panel is clipped;
    - correct/leaky R² and MSE are both visible;
    - the five class balances and both logistic models work.

WP38R already ran all full Playwright suites against the exact implementation tree. Do not repeat
the full standalone or full built-book Playwright suites in WP39 unless the checkpoint itself
changes executable content, which it must not. GitHub Actions will independently run its normal
release gates.

### Bounded failure rule

- If a gate fails because of a genuine product, data, or test defect, stop and report the failure.
- Do not fix it in WP39.
- Do not rerun a failed gate speculatively.
- A clearly identified environmental/transient command failure may receive one identical rerun
  only if no file was changed; document it precisely.
- Do not use repeated stress runs, sleeps, seed changes, artifact refreshes, or weakened
  assertions.

---

## 4. Merge into local `main`

Proceed only if every pre-deployment gate passed.

1. Record the WP39 checkpoint tree SHA.
2. Confirm the working tree is clean.
3. Switch to local `main`.
4. Reconfirm that local `main` and `origin/main` remain at the verified SHAs from Section 1.
5. Merge with a non-fast-forward merge:

   `git merge --no-ff fix/wp38r-exercise10-review -m "Merge Exercise 10 course materials"`

6. Stop on any conflict. Do not resolve conflicts automatically.
7. Record the resulting `RELEASE_SHA`.
8. Prove tree identity between `RELEASE_SHA` and the WP39 checkpoint using both a normal diff and
   a recursive tree diff. Both must be empty.
9. Confirm the working tree is clean.

If tree identity fails, stop without pushing.

---

## 5. Push exactly once

Before pushing:

1. confirm `origin/main` has not advanced since Section 1;
2. confirm `origin/main` is an ancestor of `RELEASE_SHA`;
3. confirm the working tree is clean.

Then run exactly one push:

`git push origin main`

After the push, verify once with `git ls-remote origin main` that `origin/main` equals
`RELEASE_SHA`.

If the push is rejected or the remote SHA does not match, stop. Do not force-push, pull, rebase,
or attempt a second push.

---

## 6. Discover and monitor the deployment workflow

Find the workflow run for `RELEASE_SHA` using one `gh run list --commit RELEASE_SHA` query. If no
matching run appears, wait 30 seconds and query once more. If it is still absent, stop and report.

Once found, record its run ID and URL.

Monitor it using one foreground command only:

`gh run watch RUN_ID --exit-status`

### Monitoring limit

- Allow up to **30 minutes** of wall-clock time.
- WP37 demonstrated that this workflow can legitimately take approximately 18 minutes, largely
  because of portable-notebook execution.
- Do not start a second watcher, recurring poll, scheduled wake-up loop, or background polling
  process.
- If the one foreground watcher exceeds 30 minutes, interrupt it once and stop. Record the last
  visible workflow state; do not continue querying in WP39.
- If the run fails, stop immediately after recording the failing step and relevant log excerpt.
- Do not rerun the workflow, repair code, or push another commit in WP39.

Proceed to production verification only after the workflow reports `success`.

---

## 7. Production verification

Verify the deployed site at:

`https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_10/exercise_10.html`

Use cache-busting query strings and fresh browser contexts. Prefer the repository's existing
built-book Playwright specifications against production through a temporary configuration in a
`mktemp -d` directory. Do not edit or commit production-test configuration merely to run these
checks.

### 7.1 Page and launch behavior

Confirm:

- HTTP 200;
- title: **Exercise 10: Examples and Common Mistakes**;
- no placeholder text;
- Chapter 10 appears in the sidebar in the intended order;
- Colab and download links point to the Chapter 10 portable notebook;
- the portable notebook URL returns HTTP 200;
- Exercises 1–9 remain reachable;
- Exercises 11–12 remain placeholders;
- Syllabus remains unchanged.

### 7.2 Required Exercise 10 content

Confirm the live page includes:

- the training-data boundary principle;
- the seven-option multiple-selection question with exactly six correct answers;
- the KNN leakage laboratory with fixed `k=15`;
- paired correct/leaky R² and MSE;
- the UCI HAR random-window versus participant-grouped activity;
- the five-balance ordinary versus class-weighted logistic-regression activity;
- Fragment 4's explicit UCI HAR/new-participant framing;
- the final debugging checklist.

Confirm that the removed threshold-focused imbalance activity and stale threshold-slider text do
not appear.

### 7.3 Interactive behavior

Verify all four Exercise 10 activities:

1. multiple-selection quiz;
2. KNN leakage laboratory;
3. random windows versus new participants;
4. class-balance comparison.

For each, confirm:

- iframe/config/data load successfully;
- controls update figures or metrics, not text alone;
- reset/refresh returns the intended default state;
- no clipping;
- no large empty lower region;
- iframe grows and shrinks with content;
- no page-level horizontal overflow at 390 px;
- light mode is correct;
- book-toggle dark mode is correct;
- reload while dark gives the correct first paint;
- no unexpected console/runtime errors.

Specifically confirm:

- the wrapped quiz question never overlaps the first option;
- all leakage result views show both correct and leaky R²/MSE;
- leakage sample-size/seed/scenario controls work;
- all five class balances work;
- ordinary and class-weighted results are simultaneously visible;
- majority and PR-AUC baselines update correctly;
- no threshold slider is present.

### 7.4 Shared resize regression

Because WP38R changed shared resize infrastructure, run the production-configured quantitative
iframe-height contract across **all registered Exercises 1–10 activities**, not only Exercise 10.
Confirm both clipping and excessive trailing-space assertions pass after control expansion and
contraction/reset.

Do not perform model fitting, artifact regeneration, or repository writes during production
verification.

---

## 8. Reports and final state

Create:

- `WPs/reports/WP39_DEPLOYMENT_REPORT.md`;
- `WPs/reports/WP39_EXACT_CHANGELOG.md`.

The report must include:

1. overall success/failure;
2. exact starting WP38R tip, local-main, and origin-main SHAs;
3. WP39 checkpoint SHA;
4. every pre-deployment command, result, and duration;
5. `RELEASE_SHA` and tree-identity evidence;
6. the single push result;
7. workflow run ID/URL, duration, and final conclusion;
8. production-verification results for every Section 7 item;
9. any retry, deviation, warning, or unresolved issue;
10. confirmation that no implementation content was changed by WP39;
11. confirmation that Syllabus and Word overview remained unchanged;
12. literal final `git status --short --branch` captured before the report commit;
13. the documentation commit SHA reported in Claude's final response after the commit exists.

Commit both reports locally on `main` only after the deployment attempt is complete. Do **not**
push this documentation-only commit, because doing so would trigger another deployment.

Expected successful final state:

- `origin/main` points to `RELEASE_SHA`;
- local `main` is one documentation-only commit ahead of `origin/main`;
- working tree is clean;
- Exercise 10 is live and verified;
- WP40 has not started.

Do not merge, push, or deploy anything else.
