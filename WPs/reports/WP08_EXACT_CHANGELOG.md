# WP08 — exact change log

WP08 is a release / deployment work package. It introduces **no substantive
source-code change**: the only tracked content it adds is this report pair and
the `WPs/WP08_MERGE_MAIN_AND_DEPLOY.md` brief (captured in the pre-WP checkpoint).
Everything else WP08 did is Git topology and GitHub Pages deployment state,
recorded below.

---

## 1. Git objects created by WP08

| Item | Value |
|---|---|
| Pre-WP checkpoint commit | `76ec840755f2d1bda3c209e4f98e0013c888e2fb` — `checkpoint: before WP08` |
| Checkpoint parent (feature HEAD before WP08) | `c2cb917` — `WP07 report: document final corrections` |
| Checkpoint contents | adds `WPs/WP08_MERGE_MAIN_AND_DEPLOY.md` only (1 file, +207 lines); tree otherwise identical to `c2cb917` |
| Annotated tag | `wp08-start` → `76ec840` (tagger `yoavmp <yoavmp@gmail.com>`, "Checkpoint before WP08 (merge feature to main and deploy)"). Name was free; **no numeric suffix needed**. |
| Feature-branch HEAD after checkpoint | `76ec840755f2d1bda3c209e4f98e0013c888e2fb` |
| Merge commit on `main` | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` — `Merge interactive EDA tutoring notebook` |
| Merge commit parents | `24398db68db6228fd5227f4ba22d4fa42625ae45` (1st, previous `main`) + `76ec840755f2d1bda3c209e4f98e0013c888e2fb` (2nd, feature) |
| Merge strategy | `--no-ff` (explicit merge commit), `ort` strategy, **zero conflicts** |
| Previous `origin/main` | `24398db68db6228fd5227f4ba22d4fa42625ae45` — `Stop tracking generated Jupyter Book files` |
| Pushed `origin/main` | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` (fast-forward `24398db..81b2e15`, no force) |
| Report-only commit | `WP08 report: document main deployment` — adds `WPs/reports/WP08_REPORT.md` + `WPs/reports/WP08_EXACT_CHANGELOG.md` only. Its hash and the workflow run it triggers are recorded in the session terminal summary (a report cannot contain its own commit hash). |
| Pushed `origin/main` after report commit | the report commit (fast-forward `81b2e15..`, no force) |

Tags `wp01-start` … `wp07-start` and branch
`feature/reusable-interactive-widgets` are **unchanged and undeleted**.

---

## 2. Divergence assessment (WP08 §2)

`git fetch origin --prune` run twice (before checkpoint, before merge). It only
added the pre-existing `origin/gh-pages` tracking ref; no new `main` commits.

| Pair | behind / ahead | Meaning |
|---|---|---|
| `feature/reusable-interactive-widgets` vs `origin/main` (pre-checkpoint) | `0 / 21` | feature strictly ahead |
| `feature/reusable-interactive-widgets` vs `origin/main` (post-checkpoint) | `0 / 22` | +1 = the WP08 checkpoint |
| local `main` vs `origin/main` | `0 / 0` | identical (`24398db`) |
| commits on `origin/main` absent from feature branch | **none** | `git log origin/main --not feature/…` is empty |

There were **no unrelated upstream commits on `origin/main`**. Nothing had to be
preserved or fast-forwarded in; `git pull --ff-only origin main` reported
"Already up to date". No merge conflict arose anywhere (notebook, portable
notebook, workflow, `_config.yml`, or otherwise), so no conflict description is
required.

---

## 3. What the merge brought onto `main` (`24398db..81b2e15`)

`git diff --stat` = **88 files changed, 17 858 insertions(+), 2 410 deletions(-)**.
This is exactly the union of WP01–WP07 implementation + report commits plus the
WP08 brief and checkpoint. Nothing was authored during WP08 itself.

WP-commit ancestry verified — every one of these is an ancestor of `81b2e15`:

```
414a38a checkpoint: before WP01      c3c899c WP01 impl      c2a10eb WP01 report
3b2208b checkpoint: before WP02      94db34e WP02 impl      f6c4b0f WP02 report
dfb4076 checkpoint: before WP03      4b4ab42 WP03 impl      a417761 WP03 report
9818cc3 checkpoint: before WP04      851b3f7 WP04 impl      c7cd18b WP04 report
444aa14 checkpoint: before WP05      004a3fd WP05 impl      044be5f WP05 report
5926d44 checkpoint: before WP06      34d7442 WP06 impl      6c083c4 WP06 report
d201cec checkpoint: before WP07      1b209c8 WP07 impl      c2cb917 WP07 report
76ec840 checkpoint: before WP08
```

Notable deletions in the merge (all legitimate, all originating on the feature
branch, none re-introduced): tracked `.DS_Store` files at repo root,
`.github/`, `.github/workflows/`, `book/chapters/`, `book/chapters/chapter_01/`;
and `book/chapters/chapter_01/.ipynb_checkpoints/exercise_01-checkpoint.ipynb`.
`.gitignore` was extended on the feature branch to keep them out.

Working tree after merge: **clean** (`git status --porcelain` empty). No
`book/_build`, `book/.jupyter_cache`, `book/_static/widgets/app`,
`interactive/node_modules`, `__pycache__`, or Playwright artifact was staged or
committed — all are git-ignored and were confirmed ignored (`git status
--ignored`).

---

## 4. Deployment state

| Item | Value |
|---|---|
| Triggering workflow | **Build and deploy Jupyter Book** (`.github/workflows/deploy.yml`, `on: push: branches: [main]`) |
| Workflow run | ID `34403890290` — <https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/34403890290> |
| Run head SHA | `81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` (= pushed merge commit) |
| Run result | **success**, 2 m 06 s, job `build-and-deploy` (ID 102642096851) |
| Run annotation | one non-blocking notice: "Node.js 20 is deprecated … actions/checkout@v4, actions/setup-node@v4 forced to Node.js 24" |
| Publish step | `peaceiris/actions-gh-pages@v4` → pushed built `book/_build/html` to branch `gh-pages` |
| `gh-pages` HEAD after publish | `67fe73ad6880c1b9eae3aa4eedf3a0b7da2209fc`, commit message `deploy: 81b2e156add4c5140ebc1b96ba5c7dc0d22811a3` |
| Pages build/deploy run | **pages build and deployment** ID `34404095697`, branch `gh-pages`, head `67fe73ad…`, result **success** |
| Deployed content corresponds to | `81b2e156…` (the pushed `main` merge commit) — confirmed by the `deploy:` trailer and by live-vs-local HTML comparison |

### Report-only second deployment

This is expected because the repository tracks WP reports. After this report pair
is committed (`WP08 report: document main deployment`) and pushed to `main` with
`git push origin main` (no force), the same `deploy.yml` workflow runs again and
`peaceiris/actions-gh-pages@v4` republishes `gh-pages`. That run is monitored to
completion and the live site is re-checked; the report commit hash, its workflow
run ID/URL, its result, and the resulting `gh-pages` `deploy:` trailer are
recorded in the session terminal summary and reported to Yoav. The final live
deployment is confirmed to be at the report commit (or a later legitimate `main`
commit). No force push or history rewrite is used for this step.

---

## 5. Live artifacts checked (WP08 §7)

| URL | Result |
|---|---|
| `https://yoavmp.github.io/ml-neuro-tutorials/chapters/chapter_01/exercise_01.html` | HTTP 200; rendered HTML byte-identical to the locally built merged `main` **after normalizing the 6 Matplotlib figure content-hash filenames** (see report §Warnings) |
| `https://raw.githubusercontent.com/yoavmp/ml-neuro-tutorials/main/book/downloads/chapter_01/exercise_01_portable.ipynb` | HTTP 200; SHA-1 `a6dbcc7f1c5214843ab608fa2bd6d05ba000532a`; **byte-identical** to the committed `book/downloads/chapter_01/exercise_01_portable.ipynb`; `nbformat.validate` OK, 84 cells |
| `https://colab.research.google.com/github/yoavmp/ml-neuro-tutorials/blob/main/book/downloads/chapter_01/exercise_01_portable.ipynb` | URL names the portable notebook on `main`; `HEAD` → 405 (Colab rejects HEAD — expected). Interactive Colab load not machine-verified (Google app shell / auth); raw target + URL structure verified instead. |
| `_static/widgets/app/index.html`, `app/assets/index-BcGyPnzB.js`, `app/assets/index-BXTsUyV7.css`, `configs/eda_{histogram,retention,correlation}.json`, `data/abide_{histogram,retention}.json` | all HTTP 200 on the live site; bundle filenames match the local `npm run build` output |

Live-page marker strings confirmed present: "Run or download this notebook"
card, "Open the portable notebook in Colab", "View or download" the portable
`.ipynb`, corrected guidance ("exam questions expect", "explaining the
analytical choices"), `bins=25` age example with title "Distribution of age at
scan" / ylabel "Number of participants", `\mathrm{IQR} = Q_3 - Q_1` and the
`Q_1 - 1.5 IQR` / `Q_3 + 1.5 IQR` fences. Absent (as required): any time
budget ("Budget about"), "Every question has a revealable answer", the
`object`-dtype question, and the old `dropdown-launch-buttons` Colab control.

---

## 6. Commands run (no repository mutation except the two pushes)

```
git fetch origin --prune                              # ×2
git add WPs/WP08_MERGE_MAIN_AND_DEPLOY.md
git commit -m "checkpoint: before WP08"
git tag -a wp08-start -m "Checkpoint before WP08 (merge feature to main and deploy)"
git switch main
git pull --ff-only origin main                        # Already up to date
git merge --no-ff feature/reusable-interactive-widgets -m "Merge interactive EDA tutoring notebook"
git push origin main                                  # 24398db..81b2e15  (no force)
# … full local CI-equivalent suite (see report §Local tests) …
git add WPs/reports/WP08_REPORT.md WPs/reports/WP08_EXACT_CHANGELOG.md
git commit -m "WP08 report: document main deployment"
git push origin main                                  # report-only, no force
```

No `git reset --hard`, `git checkout -- <path>`, `git clean`, `git rebase`,
`git revert`, `--force`, or `--force-with-lease` was run. No repository setting,
secret, branch-protection rule, or Pages configuration was changed.
