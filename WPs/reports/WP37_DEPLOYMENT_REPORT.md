# WP37 — Deployment Execution Report

## 1. Overall result

**FAILURE at the time of the original WP37 run** (bounded stop condition reached during workflow
monitoring). **See the WP37V addendum at the end of this report (dated 2026-09-23): the workflow
in fact completed successfully shortly after WP37 stopped watching it, and full production
verification of Exercises 7–9 has since passed.** The narrative below is preserved exactly as
written at the time of the original stop, for an accurate record of what was and was not known
at each point.

The merge to `main` and the single push to `origin/main` both succeeded, and every bounded
pre-deployment validation gate passed with no failures. However, the single foreground GitHub
Actions watcher exceeded the WP-mandated 15-minute hard wall-clock limit while the workflow was
still `in_progress` (partway through step 18 of 20). Per WP37 §7.6 and §9 ("watcher exceeds 15
minutes" is an explicit stop condition), monitoring was stopped at that point. The workflow's
final conclusion was not observed, and Section 8 (production verification) was therefore not
attempted. WP38 has not been started.

---

## 2. Starting state

- Starting WP36 branch tip (as reported): `46efa0889e3b7b67a7e4b80f838000c5c21f12ac`
- Confirmed actual HEAD of `fix/wp36-pcr-pls-alignment-scale` at the start of this WP:
  `46efa0889e3b7b67a7e4b80f838000c5c21f12ac` (exact match).
- Working tree at start: clean except for the untracked `WPs/WP37_DEPLOY_EXERCISES_7_TO_9.md`
  (this specification, not yet committed).
- Note: the two "legacy" reports the specification treats as permitted pre-existing untracked
  files (`WPs/reports/WP16_ARCHITECT_REPORT.md`, `WPs/reports/WP21_DEPLOYMENT_REPORT.md`) were
  found to be already **tracked** (committed), not untracked, in the actual repository state.
  This is a benign, non-material divergence from the specification's expectation — it leaves the
  working tree cleaner than the floor the specification anticipated, and does not affect any
  ancestry, validation, merge, or push step. Documented here per the "verify, not assume"
  guidance in WP37 §1; not treated as a stop condition.
- `WP37_CHECKPOINT_SHA` (this specification committed as a checkpoint):
  `d2d32551664c6c9794a2b4c205ff7bda01049f03`

---

## 3. Verified starting `main` / `origin/main` SHAs and ancestry

- `origin/main` (after `git fetch origin main`): `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`
  — matches expectation exactly.
- Local `main`: `a64e3492d8796dcda67c7f59b414df5977e8b989` — matches expectation exactly.
- `origin/main` confirmed an ancestor of local `main` (`git merge-base --is-ancestor` → true).
- `origin/main..main` contains exactly one commit:
  `a64e349 WP31R3: document Chapter 1 dark-mode fix and successful redeploy` — documentation-only,
  as expected.
- Local `main` confirmed an ancestor of `WP37_CHECKPOINT_SHA` (`git merge-base --is-ancestor` →
  true).
- Decorated graph `main..WP37_CHECKPOINT_SHA` (oldest first) showed a fully linear chain:
  ```
  71267fd WP32: add specification (initial checkpoint)
  73d802b (feature/wp32-exercise7-gradient-boosting) WP32: Exercise 7 — Boosting and Gradient Boosting
  d76437d WP33: add specification (initial checkpoint)
  0d9bf16 WP33: Exercise 8 — Unsupervised Learning
  a5c6971 (feature/wp33-exercise8-unsupervised-learning) WP33: reports — Exercise 8 execution report and exact changelog
  9daffdc WP34: add specification (initial checkpoint)
  c2575e0 WP34: Part A — Exercise 8 PCA+KNN correction; Part B — Exercise 9 Advanced Models
  3cb1e81 (feature/wp34-exercise9-advanced-models) WP34: reports — Exercise 8/9 execution report and exact changelog
  96a9263 WP35: add specification (initial checkpoint)
  918a0eb WP35: Exercises 7-9 review corrections and reusable iframe auto-resize
  0e10af7 (fix/wp35-exercises7-9-review) WP35: reports — Exercises 7-9 review execution report and exact changelog
  0342867 WP36: add specification (initial checkpoint)
  ba11f3f WP36: correct PCR/PLS alignment activity to a variance-controlled target
  46efa08 WP36: reports — PCR/PLS alignment correction execution report and exact changelog
  d2d3255 WP37: add specification (initial checkpoint)
  ```
  All expected WP32–WP36 milestones (implementation + reports for each) are present and linear.
- `git diff --name-only main..WP37_CHECKPOINT_SHA` (125 files changed, 164884 insertions(+),
  132 deletions(-)) contained only: WP specification/report docs, `NOTEBOOK_AUTHORING_STANDARDS.md`,
  Exercise 7/8/9 notebooks and markdown wrappers, their widget configs/data, portable notebooks
  (all 9 chapters, only 7/8/9 newly added), the shared `interactive/` components/tests/e2e specs
  for the new widgets, the `scripts/` audit and export scripts and their result JSON artifacts, and
  the corresponding `tests/` files. **No Syllabus file and no Word-course-overview file appeared
  in the diff** — confirmed unchanged.
- Working tree contained no file other than the WP37 specification (untracked) at this checkpoint;
  no other untracked or modified files were present.

No divergence from expectations was found in this section; validation proceeded.

---

## 4. Pre-deployment validation gates — commands, results, durations

All gates run once, in order, on the WP37 checkpoint branch, using the project's existing
`.venv` virtual environment. **All gates passed.**

### 4.1 Stored-artifact and portable-notebook checks

| Command | Result | Duration |
|---|---|---|
| `python scripts/gradient_boosting_model_audit.py --check` | OK: self-consistent | 0.25s |
| `python scripts/export_boosting_step_widget.py --check` | OK: self-consistent | 3.60s |
| `python scripts/export_boosting_parameter_widget.py --check` | OK: self-consistent | 0.15s |
| `python scripts/pca_kmeans_audit.py --check` | OK: self-consistent | 0.15s |
| `python scripts/export_pca_projection_widget.py --check` | OK: self-consistent | 0.20s |
| `python scripts/export_pca_kmeans_widget.py --check` | OK: self-consistent | 0.22s |
| `python scripts/advanced_models_audit.py --check` | OK: self-consistent | 0.17s |
| `python scripts/export_pcr_pls_widget.py --check` | OK: self-consistent | 3.36s |
| `python scripts/export_svm_explorer_widget.py --check` | OK: self-consistent | 42.13s |
| `python scripts/build_portable_notebook.py --check --notebook all` | All 9 chapters up to date (incl. 7, 8, 9) | 1.97s |
| `python scripts/smoke_portable_notebook.py` (registered default `--notebook all`, already covers chapters 7–9, so no additional smoke run was added) | `OK` for all 9 chapters, incl. 7/8/9 | 5m47.86s |

Notable committed-artifact values re-confirmed by `--check` (offline, no recomputation):
- PCR/PLS one-component validation MSE: weak 1.247 → moderate 0.767 → strong 0.253 (PCR),
  weak 0.597 → moderate 0.537 → strong 0.223 (PLS) — improves monotonically, and the PLS
  advantage over PCR shrinks from weak to strong, consistent with the WP36 correction.

### 4.2 Repository and build gates

| Command | Result | Duration |
|---|---|---|
| `python -m unittest discover -s tests -p 'test_*.py'` | 990 tests, OK (11 skipped — pre-existing: optional `python-docx` dependency, one conditional figure-inclusion skip in `test_exercise_06_notebook.py`) | 10.55s |
| `npm test` (interactive/; runs `typecheck && test:unit`, so a separate `npm run typecheck` was not run to avoid duplicating it) | typecheck clean; 34 test files / 426 tests passed | 7.74s |
| `npm run build` (interactive/) | Build succeeded; one pre-existing chunk-size warning (>500kB, unrelated to WP32–37 scope) | 7.67s |
| `jupyter-book clean book` | Emptied `_build` (except `.jupyter_cache`) | — |
| `jupyter-book build book` | Build succeeded, 2 warnings (one shown: `book/README.md` not in any toctree — pre-existing, unrelated to Exercises 7–9) | 6.12s |

### 4.3 Focused browser gates

| Suite | Result | Duration |
|---|---|---|
| Standalone specs: `boosting-parameter-explorer`, `boosting-step-by-step`, `pca-kmeans-explorer`, `pca-projection`, `pcr-pls-explore`, `svm-explorer` | 50 passed, 0 failed | 14.19s (12.8s reported by Playwright) |
| Built-book specs: `chapter07`, `chapter08`, `chapter09`, their dark-mode specs, `iframe-height-contract` (Exercises 1–9), `launch-buttons` (all chapters), and `chapter01-dark-mode` (the historical Chapter 1 dark-mode regression test) | 75 passed, 0 failed | 40.79s (39.1s reported by Playwright) |

390px narrow-viewport checks are embedded in the relevant specs themselves (confirmed present in
`boosting-*`, `pca-*`, `pcr-pls-explore`, `svm-explorer`, and `iframe-height-contract` prior to
running) — no separate/new narrow-viewport test was created.

No gate failed. No speculative reruns, no `--repeat-each`, no sleeps, no weakened assertions,
skipped tests, retries, or edits were used. No notebook re-execution or artifact refresh occurred
outside the listed checks.

---

## 5. Merge into local `main`

- Preconditions reconfirmed: local `main` HEAD was still `a64e3492d8796dcda67c7f59b414df5977e8b989`;
  `origin/main` still `4f0dc06bc4c0c26f8259d4f679832b9e3eb813a4`; working tree clean.
- `git merge --no-ff fix/wp36-pcr-pls-alignment-scale -m "Merge Exercises 7-9 course materials"`
  completed with **no conflicts** (merge strategy: `ort`).
- **`RELEASE_SHA` = `f792ad55f34342e627ed1fe3b85ff60777507d85`**
- Tree identity proven: `git diff RELEASE_SHA WP37_CHECKPOINT_SHA --stat` and
  `git diff-tree -r RELEASE_SHA WP37_CHECKPOINT_SHA` both produced **empty output** — the merged
  `main` tree is byte-identical to the WP37 checkpoint tree.
- Working tree after merge: clean, no untracked files.

---

## 6. Push

- `git push origin main` succeeded on the first and only attempt:
  `4f0dc06..f792ad5  main -> main`
- Read-only verification: `git ls-remote origin main` →
  `f792ad55f34342e627ed1fe3b85ff60777507d85 refs/heads/main` — confirms `origin/main` points to
  `RELEASE_SHA`.
- Exactly one push was performed. No retry was needed or attempted.

---

## 7. Workflow discovery and monitoring

- Workflow discovery: `gh run list --commit f792ad55f34342e627ed1fe3b85ff60777507d85 --limit 5`
  found a matching run on the **first query** (no 30-second wait/second query was needed).
- **Workflow name:** "Build and deploy Jupyter Book"
- **Run ID:** `35881835065`
- **Job:** `build-and-deploy` (ID `107251956939`)
- Single foreground watcher started: `gh run watch 35881835065 --exit-status`.
- The watcher's own execution exceeded the tool environment's per-call limit and continued running
  as the same single background-tracked process (not a second watcher); its live output and,
  subsequently, a read-only `gh run view` status query were used to track it without starting any
  additional watcher or polling loop beyond what was needed to enforce the WP's own 15-minute cap.
- Run created at `2026-09-23T15:28:38Z`. At `2026-09-23T15:44:49Z` (≈16m11s elapsed — past the
  15-minute hard limit), the run was still `in_progress`.
- **Last visible workflow state at the moment of interruption** (steps 1–17 of 20, all `success`):
  1. Set up job ✓
  2. Check out repository ✓
  3. Set up Python ✓
  4. Install Python dependencies ✓
  5. Set up Node ✓
  6. Install frontend dependencies ✓
  7. Type-check and unit-test the frontend ✓
  8. Audit production frontend dependencies ✓
  9. Build the interactive widget app ✓
  10. Validate both committed ABIDE data artifacts (offline) ✓
  11. Unit-test the Python scripts (offline) ✓
  12. Check the portable notebook is not stale (offline) ✓
  13. Install Playwright Chromium ✓
  14. End-to-end test the standalone widget app ✓
  15. Build Jupyter Book ✓
  16. Fail on notebook execution errors ✓
  17. End-to-end test the built Chapter 1 page ✓
  18. **Execute the portable notebook outside the repository — `in_progress`, started
      `2026-09-23T15:40:13Z`** (running ≈4m36s at the moment of interruption)
  19. Publish website — `pending`
  20. Post-job cleanup steps — `pending`
- Per WP37 §7.6 and §9, the watcher was interrupted exactly once (`TaskStop`) upon exceeding the
  15-minute limit. No second watcher was started, no additional polling occurred afterward, the
  run was not rerun or cancelled, and no repair commit was pushed.
- **Overall workflow conclusion: unknown at the time this WP was stopped.** Steps 1–17 had
  succeeded; step 18 was still running; the workflow had not failed as of the last observation,
  but its final result was not confirmed within the bounded monitoring window.

---

## 8. Production verification

**Not performed.** WP37 §8 gates production verification on workflow success being observed;
since the workflow's conclusion was not observed within the 15-minute bounded window, no
production checks (site structure, Exercise 7/8/9 content, theme/responsive/iframe/runtime
checks) were attempted, per the stop-condition discipline in §9 ("Do not... start WP38" applies
equally to skipping ahead into verification without a confirmed successful run).

---

## 9. Items requiring the user's attention

1. **The GitHub Actions run's final conclusion is unknown.** Run ID `35881835065`
   ("Build and deploy Jupyter Book") was still `in_progress` at step 18/20
   ("Execute the portable notebook outside the repository") when the WP37-mandated 15-minute
   watcher limit was reached. All prior steps (1–17), including the full built-book Chapter 1
   E2E gate and the Jupyter Book build itself, had already succeeded at that point. The user
   should check the run directly:
   `https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/35881835065`
2. **`origin/main` already points to `RELEASE_SHA`** (the merge was pushed). This cannot be
   undone within WP37's rules (no force-push, no reset). If the workflow ultimately fails, a
   follow-up WP will be needed to investigate and fix — WP37 is explicitly barred from repairing
   anything itself.
3. Per WP37 rules, no repair, rerun, or repush was attempted, and WP38 was not started.
4. Minor pre-existing/unrelated observations recorded for completeness (not stop conditions):
   the two "legacy" whitelisted reports are tracked, not untracked, in the current repository;
   the Jupyter Book build emits a pre-existing `book/README.md` not-in-toctree warning; the
   frontend build emits a pre-existing large-chunk warning; 11 unittest skips are pre-existing
   and unrelated to Exercises 7–9.

---

## 10. Final git status and log

```text
## main...origin/main
```

(Clean — no modified or untracked files; local `main` and `origin/main` are in sync at
`RELEASE_SHA`, prior to the documentation commit below.)

```text
f792ad5 (HEAD -> main, origin/main, origin/HEAD) Merge Exercises 7-9 course materials
d2d3255 (fix/wp36-pcr-pls-alignment-scale) WP37: add specification (initial checkpoint)
46efa08 WP36: reports — PCR/PLS alignment correction execution report and exact changelog
ba11f3f WP36: correct PCR/PLS alignment activity to a variance-controlled target
0342867 WP36: add specification (initial checkpoint)
0e10af7 (fix/wp35-exercises7-9-review) WP35: reports — Exercises 7-9 review execution report and exact changelog
```

(The two WP37 report files below are committed locally on `main`, on top of `f792ad5`, as one
documentation-only commit — `DOCUMENTATION_SHA` — which is **not pushed**, per WP37 §10.)

---

## Addendum — WP37V production-status verification (2026-09-23, dated)

A follow-up work package, WP37V, queried the same run exactly once
(`gh run view 35881835065 --json status,conclusion,url,jobs`) and found it had in fact reached
**`status: completed`, `conclusion: success`** — all 20 steps succeeded, including the previously
in-progress "Execute the portable notebook outside the repository" (completed
`2026-09-23T15:46:16Z`) and "Publish website" (completed `2026-09-23T15:46:21Z`). Total run
duration: 17m43s (`15:28:38Z` → `15:46:21Z`).

WP37V then performed full Section 8 production verification against
`https://yoavmp.github.io/ml-neuro-tutorials/` and confirmed:

- **Site structure (§8.1):** Exercises 1–6 titles unregressed; Exercises 7/8/9 live with their
  intended titles (no placeholder text); Exercises 10–12 still placeholders with correct topic
  titles; Exercise 13 absent (HTTP 404); Syllabus present (HTTP 200, title "Syllabus"); Word
  course overview unchanged (confirmed via the repository release diff in the original WP37 run —
  this file is not part of the GitHub Pages build).
- **Exercise 7 (§8.2):** title/structure, both activities loading and updating (config/data
  HTTP 200, controls change plots/metrics), narrow-viewport (390px), and dark-mode/reload-while
  -dark theme sync all reused unmodified against production via `chapter07.spec.ts` and
  `chapter07-dark-mode.spec.ts` (which also already asserts zero unexpected console errors) — all
  passed. The "computational cost is also part of model design" framing is present verbatim.
- **Exercise 8 (§8.3):** title/structure and both activities (PCA-projection, PCA/K-means) verified
  via `chapter08.spec.ts` and `chapter08-dark-mode.spec.ts` reused against production — all passed.
  Confirmed present verbatim: the Section 8 title "Using PCA in a Supervised Pipeline"; cumulative
  explained-variance reporting; the K-means framing ("we use K-means as one practical example for
  understanding how clustering works" — not the only possible method); and inertia/silhouette
  guidance text.
- **Exercise 9 (§8.4):** title/structure and both activities (PCR/PLS, SVM boundary) verified via
  `chapter09.spec.ts` and `chapter09-dark-mode.spec.ts` reused against production — all passed.
  Confirmed present verbatim: the "highest-variance direction" framing; the "same signal strength
  and the same noise level; only the direction of the predictive signal changes" framing; and the
  real ABIDE-II five-model comparison, with all five committed MSE values
  (OLS 49.14, PCR 31.74, PLS 32.42, Linear SVR 40.28, RBF SVR 20.38) appearing verbatim on the live
  page, rendered immediately (not gated behind the expensive nested-CV audit).
- **Theme/responsive/iframe/runtime (§8.5):** `iframe-height-contract.spec.ts` (Exercises 1–9,
  including dark mode at 390px) and `launch-buttons.spec.ts` (all chapters, incl. 7–9 Colab/download
  links) both reused unmodified against production — all passed. A small throwaway console-error
  sweep (light mode + toggled dark mode) covering Exercises 7–9 — needed because only
  `chapter07-dark-mode.spec.ts` already asserted this; Exercises 8 and 9 had no equivalent existing
  check — found **zero unexpected console/runtime errors** on any of the three pages, distinguishing
  correctly from the two known pre-existing Thebe/theme-bootstrap messages (neither of which
  appeared at all in this sweep).

**Method:** per WP37 §8's preference for "existing production-capable Playwright specs," all
checks above reused the repository's own `interactive/e2e-book/*.spec.ts` files unmodified, run
against `https://yoavmp.github.io` via a temporary Playwright config and one small temporary
throwaway spec (console sweep), both created only inside a `mktemp -d` directory and deleted
immediately after use — never committed, confirmed via `git status --short --branch` showing a
clean tree throughout and after. No implementation file was edited, no rerun/repush occurred, and
WP38 was not started.

**Revised overall result: SUCCESS.** Exercises 7, 8, and 9 are confirmed live in production at
`https://yoavmp.github.io/ml-neuro-tutorials/`, matching the merged `RELEASE_SHA`
(`f792ad55f34342e627ed1fe3b85ff60777507d85`) content exactly.

See `WPs/reports/WP37V_REPORT.md` and `WPs/reports/WP37V_EXACT_CHANGELOG.md` for the full,
self-contained WP37V record.
