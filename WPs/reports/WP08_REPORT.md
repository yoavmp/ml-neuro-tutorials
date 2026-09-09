# WP08 implementation report — merge the completed EDA work into `main` and deploy GitHub Pages

## Outcome

Status: **SUCCESS**

`feature/reusable-interactive-widgets` (WP01–WP07) was merged into `main` with an
explicit non-fast-forward merge commit, the exact merged commit passed the full
WP07 CI-equivalent suite locally, `main` was pushed without any history rewrite,
the "Build and deploy Jupyter Book" workflow and the GitHub Pages deployment both
completed green, and the live public site now serves the new Chapter 1 page, the
three working browser activities, the repaired sidebar control, and the portable
notebook (byte-identical to the committed file) at its `main` Colab / raw URLs.

One pre-existing, non-blocking console warning on the built page is documented
under **Warnings**; it is present in a local build too and is not introduced by
this release. Nothing requires Yoav's action for the release itself.

## Git safety checkpoint (WP08 §1)

- Branch at start: `feature/reusable-interactive-widgets` (confirmed; not changed
  before the checkpoint).
- Only uncommitted item: untracked `WPs/WP08_MERGE_MAIN_AND_DEPLOY.md`. No build
  output, cache, `.DS_Store`, credential, token, or private data was present.
- **Checkpoint commit: `76ec840755f2d1bda3c209e4f98e0013c888e2fb`**
  ("checkpoint: before WP08") — adds the WP08 brief only (1 file, +207 lines).
- **Checkpoint tag: `wp08-start`** (annotated; points at `76ec840`). The name was
  free, so **no numeric suffix** was needed.
- Feature-branch HEAD after the checkpoint: `76ec840755f2d1bda3c209e4f98e0013c888e2fb`.
- WP01–WP07 implementation **and** report commits, and every `wpNN-start` tag
  (`wp01-start`…`wp07-start`), were verified to be ancestors of the feature
  HEAD and of the merge commit (`git merge-base --is-ancestor`, all OK).
- No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
  `git revert`, or history rewrite was run at any point.

## Divergence assessment (WP08 §2)

`git fetch origin --prune` was run before the checkpoint and again before the
merge. It only added the pre-existing `origin/gh-pages` tracking ref.

| Pair | behind / ahead |
|---|---|
| feature vs `origin/main` (before checkpoint) | 0 / 21 |
| feature vs `origin/main` (after checkpoint) | 0 / 22 |
| local `main` vs `origin/main` | 0 / 0 (both `24398db`) |
| commits on `origin/main` absent from feature | **none** |

There were **no unrelated upstream commits** on `origin/main`. `git pull --ff-only
origin main` reported "Already up to date". **No upstream change had to be
incorporated**, and **no merge conflict arose** anywhere — notebook, generated
portable notebook, `deploy.yml`, `book/_config.yml`, or otherwise. The merge used
the `ort` strategy with zero conflicts.

## Merge (WP08 §3)

```
git switch main
git pull --ff-only origin main            # Already up to date
git merge --no-ff feature/reusable-interactive-widgets -m "Merge interactive EDA tutoring notebook"
```

- **Merge commit: `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3`**
  ("Merge interactive EDA tutoring notebook").
- Parents: `24398db68db6228fd5227f4ba22d4fa42625ae45` (previous `main`) +
  `76ec840755f2d1bda3c209e4f98e0013c888e2fb` (feature checkpoint).
- `24398db..81b2e15` = **88 files changed, +17 858 / −2 410**, exactly the union of
  WP01–WP07 + the WP08 brief/checkpoint. Legitimate deletions carried from the
  feature branch: tracked `.DS_Store` files and
  `book/chapters/chapter_01/.ipynb_checkpoints/exercise_01-checkpoint.ipynb`.
- Working tree after merge: **clean**. No `book/_build`, `book/.jupyter_cache`,
  `book/_static/widgets/app`, `interactive/node_modules`, `__pycache__`, or
  Playwright artifact was staged (all git-ignored; confirmed with
  `git status --ignored`).
- The feature branch and all `wpNN-start` tags were **not** deleted.

## Local tests on the exact merged `main` commit (WP08 §4)

Run from `81b2e156…` with the project's `.venv` (Python 3.12.7, jupyter-book
1.0.4.post1) and `interactive/` (Node 24 locally; CI pins 22).

| Check | Command | Result |
|---|---|---|
| Clean npm install | `interactive$ rm -rf node_modules && npm ci` | OK (100 packages) |
| TypeScript typecheck | `interactive$ npm run typecheck` | **PASS**, 0 errors |
| Frontend unit tests | `interactive$ npm run test:unit` | **143 / 143** (8 files) |
| Production dependency audit | `interactive$ npm audit --omit=dev` | **0 vulnerabilities** |
| Frontend production build | `interactive$ npm run build` | **PASS** (only the pre-existing 500 kB Plotly-chunk Vite warning; bundle `index-BcGyPnzB.js`) |
| Widget artifact validation | `python scripts/export_widget_data.py --check --artifact all` | **PASS** — both committed ABIDE artifacts valid + canonical |
| All Python unit tests | `python -m unittest discover -s tests -v` | **73 / 73** (45 export + 18 portable-generator + 10 notebook-corrections) |
| Portable-notebook stale check | `python scripts/build_portable_notebook.py --check` | **PASS** — "up to date (84 cells)" |
| Portable notebook smoke, outside the repo | `python scripts/smoke_portable_notebook.py` | **PASS** — 23 code cells executed in a temp dir, 0 errors, key values matched |
| Standalone Playwright suite | `interactive$ npx playwright test` | **40 / 40** |
| Clean Jupyter Book build | `rm -rf book/_build book/.jupyter_cache && jupyter-book build book` | **PASS** — "build succeeded, 9 warnings" (all pre-existing: missing `logo.png`, `README` not in a toctree, `syllabus` toctree title ×7) |
| `*.err.log` guard | `find book/_build -name '*.err.log'` | **empty** — PASS |
| Built-book Playwright suite | `interactive$ npm run test:e2e:book` | **13 / 13** (9 activity + 4 sidebar-toggle regression) |
| Two+ consecutive clean notebook builds, deterministic figures | 3 × `rm -rf book/_build book/.jupyter_cache && jupyter-book build book` | **byte-identical** set of 6 figure PNGs across all three builds |

### HTML inspection of the merged build (WP08 §4)

Confirmed in `book/_build/html/chapters/chapter_01/exercise_01.html`:

- **Repaired sidebar control present and functional** — the built-book
  `sidebar-toggle.spec.ts` (4/4) asserts an *observable* collapse/re-expand at
  desktop width and the nav-modal open at 390 px, and "never a no-op".
- **All three interactive activities load and respond** — `chapter01.spec.ts`
  (9/9): each `<iframe>` config + data are HTTP 200, Plotly renders, and a
  control change alters the real figure / statistics.
- **Corrected opening text** — no time budget ("Budget about" absent), the
  "Every question has a revealable answer" claim absent, the
  assessment/exam-reasoning paragraph present, "Check your reasoning" wording
  present.
- **Histogram example present** — a `hide-input` code cell with
  `sns.histplot(..., x="AGE_AT_SCAN", bins=25, ...)`, title "Distribution of age
  at scan", ylabel "Number of participants"; "Show code cell source" toggle
  present.
- **IQR equation present** — renders as MathJax input
  `\[ \mathrm{IQR} = Q_3 - Q_1 . \]` followed by the
  `Q_1 - 1.5\,\mathrm{IQR}` / `Q_3 + 1.5\,\mathrm{IQR}` fences.
- **Old built-in Colab launch control absent** — no `dropdown-launch-buttons`;
  the only `colab.research.google.com` URL on the page is the portable link.
- **New Colab/raw links target `main`** —
  `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb`
  and
  `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_01/exercise_01_portable.ipynb`.
- The `object`-dtype question is gone from the `info()` "Think first" card.

No generated build output was committed.

## Push (WP08 §5)

```
git push origin main            # 24398db..81b2e15   main -> main
```

- **No `--force` / `--force-with-lease`.** Fast-forward of `origin/main` from
  `24398db68db6228fd5227f4ba22d4fa42625ae45` to
  **`81b2e156add4c5140ebc1b96ba5c7dc0d22811a3`**.
- `git fetch` + hash comparison confirm `origin/main` == local `main` ==
  `81b2e156…`.
- No authentication or branch-protection obstruction.

## Workflow and Pages deployment (WP08 §6)

| Item | Value |
|---|---|
| Workflow | **Build and deploy Jupyter Book** (`.github/workflows/deploy.yml`) |
| Run | **ID `34403890290`** — <https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/34403890290> |
| Run head SHA | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` (= pushed merge commit) |
| Result | **success**, 2 m 06 s (job `build-and-deploy`, ID 102642096851); every step green, including typecheck/unit, `npm audit --omit=dev`, widget build, offline artifact validation, `unittest discover`, portable `--check`, standalone Playwright, Jupyter Book build, `*.err.log` guard, built-book Playwright, out-of-repo portable execution, and "Publish website" |
| Non-blocking annotation | "Node.js 20 is deprecated … actions/checkout@v4, actions/setup-node@v4 forced to Node.js 24" — GitHub-runner notice only |
| Publish mechanism | `peaceiris/actions-gh-pages@v4` pushed `book/_build/html` to branch `gh-pages` |
| `gh-pages` HEAD after publish | `67fe73ad6880c1b9eae3aa4eedf3a0b7da2209fc` — commit message `deploy: 81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` |
| Pages build/deploy run | **pages build and deployment**, **ID `34404095697`**, branch `gh-pages`, head `67fe73ad…`, **result success** |
| Deployed commit corresponds to | `81b2e156…` — the pushed `main` merge commit (confirmed by the `deploy:` trailer **and** by a byte comparison of live vs locally built HTML), not an older queued workflow |

No repository secret, permission, branch-protection rule, or Pages setting was
changed.

## Live verification (WP08 §7)

All checks against the **public** site (cache-busting query string), not
localhost.

| # | Check | Result |
|---|---|---|
| — | `…/chapters/chapter_01/exercise_01.html` | **HTTP 200**; rendered HTML **byte-identical** to the locally built merged `main` after normalizing the 6 Matplotlib figure content-hash filenames (see Warnings) |
| 1 | WP07 markers on the live page | **PASS** — "Run or download this notebook" card; "Open the portable notebook in Colab"; "View or download" the portable `.ipynb`; corrected guidance ("exam questions expect", "explaining the analytical choices"); `bins=25` age example ("Distribution of age at scan" / "Number of participants"); `\mathrm{IQR} = Q_3 - Q_1` + fences. Absent: any time budget, "Every question has a revealable answer", the `object`-dtype question, and the old `dropdown-launch-buttons` control. |
| 2 | Sidebar button at desktop and narrow width | **PASS** (live Playwright) — at 1280 px one click sets `pst-sidebar-hidden` and moves the sidebar out of the viewport, a second click restores it (`hidden false→true→false`); at 390 px one click opens `#pst-primary-sidebar-modal` (`open=true`) |
| 3 | Three embedded activities load and a control updates the view | **PASS** (live Playwright) — histogram renders a Plotly SVG, bin-slider change redraws (marks 26→38); retention renders, checkbox toggles change the bar geometry; correlation renders, dropdown changes redraw the figure (marks 779→290) |
| 4 | Raw portable notebook | **PASS** — HTTP 200; SHA-1 `a6dbcc7f1c5214843ab608fa2bd6d05ba000532a`; **byte-identical** to the committed `book/downloads/chapter_01/exercise_01_portable.ipynb`; `nbformat.validate` OK, 84 cells |
| 5 | Colab URL | **PARTIAL / documented limitation** — the URL names the portable notebook on `main`; `HEAD` returns 405 (Colab rejects HEAD, expected). Interactive Colab rendering was not machine-verified because Google serves an app shell / auth wall to headless automation. The raw target and URL structure are verified instead, per WP08 §7.5. |
| 6 | Mixed-content / missing-resource / console / iframe errors | **PASS for missing-resource / mixed-content / iframe** (all live `_static/widgets/app/*`, `configs/*.json`, `data/*.json` return HTTP 200; iframes load and function). One **pre-existing** console warning remains — see Warnings. |
| — | Live widget bundle | `index-BcGyPnzB.js` / `index-BXTsUyV7.css` filenames on the live site match the local `npm run build` output |

## Warnings, deviations, deferred checks

1. **Pre-existing console noise on the built page (not a WP08 regression).**
   Headless Chromium reports two `pageerror`/`console.error` messages on the
   Chapter 1 page:
   - `Identifier 'THEBE_JS_URL' has already been declared` — Jupyter Book /
     `sphinx-thebe` injects its launch script twice. `THEBE_JS_URL` appears
     **twice in a local build too**; `book/_config.yml` has no `thebe` /
     `launch_buttons` key (WP07 only *removed* `launch_buttons`). This is the
     carried-forward "trim `sphinx-thebe`" item from the WP06/WP07 reports.
   - `Got invalid theme mode: . Resetting to auto.` — benign
     `pydata-sphinx-theme` start-up message.
   Neither is a mixed-content, 404, or iframe error, and neither affects the
   activities, the sidebar fix, or the notebook content. Left as-is (out of
   WP08 scope; WP08 must not make design changes).

2. **Cross-platform Matplotlib figure bytes differ (local vs CI).** The 6
   embedded figure PNGs are byte-**deterministic within an environment** (3
   consecutive clean local builds → identical hashes; the seeded-stripplot fix
   from WP07 holds), but the CI-built PNGs have different content hashes than the
   local macOS build because CI runs Linux with an unpinned newer Matplotlib.
   After normalizing those 6 filenames the deployed HTML is byte-identical to the
   local build. This is expected (WP07 §14 flags `numpy`/`pandas`/`matplotlib`
   as unpinned) and is **not** a determinism regression. No action taken.

3. **Colab interactive load not machine-verified** (WP08 §7.5 anticipated this) —
   Google's interstitial/auth blocks headless inspection. URL structure + raw
   target verified instead.

4. **`git pull --ff-only origin main` was a no-op** — local `main` already equalled
   `origin/main`, so there was no upstream content to fast-forward. The command
   was still run, as WP08 §3.2 specifies.

5. **Node 24 locally / CI Node 22** — `engines` is `>=20.19.0 <25`; `npm audit
   --omit=dev` is clean; no Vite/Vitest change in this WP. The GitHub run's
   Node-20-deprecation annotation is a runner notice, not a build failure.

6. No deviation from the "never force-push / no history rewrite / no settings
   change" rules.

## Confirmation of safety constraints (WP08 §8)

- **No force push.** Both pushes were ordinary fast-forwards
  (`24398db..81b2e15`, then `81b2e15..` the report commit). `--force` and
  `--force-with-lease` were never used.
- **No destructive command.** No `git reset --hard`, `git checkout -- <path>`,
  `git clean`, `git rebase`, `git revert`, tag deletion, or branch deletion.
- **No settings change.** No repository secret, Actions permission, branch
  protection, or GitHub Pages configuration was touched.
- **No generated build output committed.** `book/_build`, `book/.jupyter_cache`,
  `book/_static/widgets/app`, `interactive/node_modules`, `__pycache__`, and
  Playwright artifacts remain untracked / git-ignored.
- The only tracked content WP08 adds is `WPs/WP08_MERGE_MAIN_AND_DEPLOY.md` (in
  the checkpoint) and this report pair.

## Key identifiers

| Item | Value |
|---|---|
| Checkpoint commit | `76ec840755f2d1bda3c209e4f98e0013c888e2fb` ("checkpoint: before WP08") |
| Checkpoint tag | `wp08-start` (annotated, → `76ec840`; no suffix needed) |
| Feature-branch HEAD | `76ec840755f2d1bda3c209e4f98e0013c888e2fb` |
| Previous `origin/main` | `24398db68db6228fd5227f4ba22d4fa42625ae45` ("Stop tracking generated Jupyter Book files") |
| Merge commit | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` ("Merge interactive EDA tutoring notebook") |
| Pushed `origin/main` | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` |
| Deploy workflow run | ID `34403890290` — <https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/34403890290> |
| `gh-pages` deploy commit | `67fe73ad6880c1b9eae3aa4eedf3a0b7da2209fc` (`deploy: 81b2e156…`) |
| Pages build/deploy run | ID `34404095697` (success) |
| Report-only commit + its run | recorded in the terminal summary (a report cannot contain its own hash) |

## Rollback guidance (identification only — not performed)

To undo this release while preserving history:

```
git revert -m 1 81b2e156add4c5140ebc1b96ba5c7dc0d22811a3
git push origin main
```

`-m 1` keeps the first parent (`24398db`, the pre-merge `main`) and reverts the
entire WP01–WP07 change set in one commit; the deploy workflow then republishes
the pre-merge site. The feature branch, its history, and tags `wp01-start` …
`wp08-start` are untouched by a revert and remain available to re-land the work.
Do **not** rewrite or force-push `main` to roll back.

## Instructions for reviewer

Paste this entire report (`WP08_REPORT.md`) into the ChatGPT conversation that
produced WP08. `WP08_EXACT_CHANGELOG.md` is the companion git-topology /
deployment record.
