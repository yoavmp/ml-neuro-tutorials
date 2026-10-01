# WP47 report: active Exercise 8 (Unsupervised Learning) in JupyterLite

## Success or failure — read this first

Exercise 8 (Unsupervised Learning) is migrated to the JupyterLite-native,
generator-authored architecture established by WP41/WP42/WP44/WP45/WP46,
following `scripts/generate_exercise_07_notebook.py`'s exact generator
shape. Unlike Exercises 6 and 7, this was a genuine **content redesign**,
not a line-for-line port: the legacy notebook taught PCA and K-means almost
entirely through supplied code and two embedded iframes; the new notebook
teaches the same material primarily through **five guided student blanks**,
**one native interactive activity**, and **six checked conceptual
questions**, per the WP47 spec's explicit instruction.

- The PCA fit, the two-panel explained-variance figure, the PC1-vs-PC2
  scatter colored by age, the loadings inspection, and the K-means
  inertia/silhouette computation are all now genuine `# YOUR CODE HERE`
  tasks with a reference solution, a generous-tolerance check cell, and a
  commented (never executable) hint.
- The old "Find the Best Projection" iframe is **dropped** (see "Deliberate
  scope trims" below) and the old "Explore PCA and K-Means" iframe is ported
  to a native `ipywidgets` control that **prefers the student's own
  completed `X_pca`**, with a clearly labeled, independently computed
  fallback when that task is not yet done.
- Section 5 ("Using PCA in a Supervised Pipeline") stays **supplied, runnable
  code** (per the WP47 spec's explicit instruction, since this is the
  already-audited leakage-safe comparison, not a new activity), with a new
  checked question on why Section 2's full-cohort `pca_explore` must never
  be reused to score the held-out test set.
- A new, genuinely different numerical finding from WP46's: **PCA and
  K-means (and KNN's Euclidean distance) are mathematically invariant to the
  360-feature column order**, unlike a decision tree's greedy per-feature
  split search. Verified directly (see "Numbers verified before writing a
  line" below) — Sections 1-4's numbers reproduce the legacy, network-sourced
  audit almost exactly; Section 5's PCA+KNN pipeline selects a genuinely
  different `k` at a near-tied cross-validation margin, a real,
  honestly-computed difference, not a bug.
- A new per-exercise answer-key-visibility mechanism (the WP47 spec's
  "Multiple-choice answer visibility" section): every checked question's
  `correct_index`/`correct_indices` now lives only in the hidden, collapsed
  setup cell, behind a `show_question(question_id)` wrapper — no visible
  question cell in this notebook ever prints or displays its own answer key.
  This is a readability improvement, not real answer-key secrecy; the honest
  limit is stated in this report and in the notebook's own closing summary
  (see "Answer-key visibility" below).
- A new, Exercise-8-only data sidecar
  (`book/lite/files/data/abide_age_brain_demographics.csv`,
  `scripts/export_abide_demographics_lite_data.py`) supplies sex and
  acquisition site for **post-fit coloring only** — the existing shared
  `abide_age_brain.csv` export (used by Exercises 2, 4, 5, 6, 7) is
  **unmodified**.
- Untouched-template "Run All Cells" produces **zero error cells**: every
  blank's own check cell (or, for the one supplied cell that reads a
  blank's output, an explicit `"X_pca" in globals()` guard) degrades
  gracefully to "Not complete yet", verified both offline (executing the
  actual student-template cell sources in one shared namespace) and live in
  a real Chromium/Pyodide session.
- The teacher-completed reference notebook runs end to end, reproducing
  every established number, verified both offline and live in a real
  Chromium/Pyodide session (every checked question, the native widget's
  every control, 390px, Reset/Back, download-contains-edits).

No merge, no push, no deployment, no GitHub Actions interaction at any
point. `book/config/exercise_manifest.json`'s Exercise 8 entry stays
`migrationState: "legacy"` with every Lite field `null`, deliberately,
pending the real-Colab acceptance gate (WP41_MAINTAINER_GUIDE.md section
11) — the same treatment Exercises 3-7's entries already have.

## Branches and SHAs

Starting SHA (local `main`): `dcc53655b8e4b3eac67ba741e165ff6bbbf0cf3d`,
matching `origin/main` (unchanged since WP46).

Checkpoint: branch `checkpoint/wp47-pre-work`, at the tip of
`feature/wp46-active-exercises-6-and-7` (`eefadef` — "WP46: reports —
execution report and exact changelog"). Working tree had no unexplained
changes at checkout time (only the new, untracked
`WPs/WP47_ACTIVE_EXERCISE_8_UNSUPERVISED_LEARNING.md` and the author's
reference image `WPs/image.png`).

Feature branch: `feature/wp47-active-exercise-8-unsupervised-learning`,
created from that same tip.

Commits made by this WP, in order:
1. `dbc50ee` — checkpoint the WP spec and reference image on the dedicated
   feature branch.
2. `c871806` — Gate B: migrate Exercise 8 to a JupyterLite-native notebook
   (24 files changed, +9007/-2623; see `WPs/reports/WP47_EXACT_CHANGELOG.md`
   for the full file list).
3. This report + this changelog (committed together as this WP's closing
   commit; see `git log -1` after that commit for the final SHA).

## The reference image

The author's attached two-panel PCA figure (`WPs/image.png`, checkpointed
unmodified in commit 1) specifies, exactly as the WP47 spec describes:
left, a scree bar chart for PCs 1-15 (explained variance ratio, y-axis
starting at 0); right, cumulative explained variance for PCs 1-50 (percent,
y-axis starting at 0%), a dashed 50% guide, and an annotation marking PC1
alone (visually ≈36.1% individual, ≈70% cumulative by PC50). The generated
notebook's Section 2 "Plot explained variance" blank reproduces this exact
two-panel layout from `pca_explore`'s own `explained_variance_ratio_`,
computed fresh from this notebook's actual data and preprocessing (see
below) — the image's illustrative numbers were never hardcoded; they are
also, as it happens, what this notebook's own computation produces almost
exactly.

## Numbers verified before writing a line

Before writing the generator, `book/lite/files/data/abide_age_brain.csv`
(the established same-origin export Exercises 2, 4, 5, 6, and 7 already
share — no change made to it) and the legacy notebook's own executed outputs
were read directly, then a standalone verification script was run against
the committed CSV to confirm or refute WP46's finding would carry over to
PCA/K-means. **It does not carry over in the same way** — the key finding of
this WP:

**PCA, K-means, and Euclidean-distance KNN are mathematically invariant to
column order.** Permuting the 360 `fsCT_*` columns changes nothing about a
covariance matrix's eigenvalues (explained variance), a participant's
PCA-transformed score, a K-means cluster assignment, or a Euclidean
distance between two participants — unlike a decision tree's greedy
per-feature split search, which can pick a different near-tied split when
column order changes a tie-break. Verified directly, section by section,
against the committed CSV (not assumed):

- **PCA** (`StandardScaler` then `PCA(n_components=50, random_state=0)` on
  all 1004 participants, 360 standardized features): PC1 explained
  variance = 36.1414%, cumulative at PC2/5/10/20/50 = 42.0024% / 49.4155% /
  54.3078% / 60.0997% / 70.1822% — matches
  `scripts/pca_kmeans_audit_result.json` (computed from the network source)
  to 4 decimal places; the tiny remaining difference at PC20/PC50 (60.0997%
  vs. 60.1007%; 70.1822% vs. 70.1730%) traces to the CSV export's
  ~6-significant-figure rounding, not column order.
- **K-means** (`N_CLUSTER_COMPONENTS=10`, `K_CANDIDATES=[1..6]`,
  `random_state=0`, `n_init=10`): inertia falls monotonically (196290.19 at
  k=1 to 65155.73 at k=6); silhouette (k≥2 only) = 0.3784 (k=2), **0.2650
  (k=3) — an exact match to the legacy audit's demo k=3 silhouette of
  0.265**, 0.1923 (k=4), 0.1890 (k=5), 0.1936 (k=6) — no strong elbow,
  consistent with the legacy notebook's own stated finding; the "research
  example" cluster sizes `{0: 397, 1: 412, 2: 195}` at the legacy's own
  `(retained_pc=10, k=3, seed=0)` combination match **exactly**, byte for
  byte.
- **Section 5 supervised pipeline** (`test_size=0.25, random_state=42,
  stratify=group`; `KFold(5, shuffle=True, random_state=13)` on the
  753-row development partition; `component_grid=[5,10,20,50,100]`,
  `k_grid=[5,10,20,40]`): this notebook's own data source selects
  **(n_components=20, k=5)**, mean CV MSE=24.9069 — very close to, but
  genuinely different from, the legacy audit's **(n_components=20, k=10)**,
  mean CV MSE=24.8286. The margin between `k=5` and `k=10` at
  `n_components=20` is only ≈0.08 MSE (24.9069 vs. ~25.12 in this
  notebook's own CV table) — close enough that the CSV's
  6-significant-figure rounding (which does not affect PCA scores'
  *direction*, but does affect their last digit, and therefore which
  training-fold neighbors are nearest at a near-tied margin) is enough to
  flip which `k` wins. This is the same class of near-tied-margin
  sensitivity WP46 documented for deep trees, arising here for a different
  underlying reason (floating-point rounding at a genuine near-tie in a
  distance-based method, not column reordering changing a tree's split
  choice) — verified directly, not assumed, and reported honestly rather
  than silently matched to the legacy number. Locked-test MSE/R² for this
  notebook's own selection: **19.1311 / 0.795060** (legacy, at its own
  k=10 selection: 21.0491 / 0.774513).
- **The raw-feature (no-PCA) KNN baseline matches the legacy audit
  exactly**: selected k=5, mean CV MSE=35.3979, locked-test MSE/R²
  =32.0452/0.656718 — Euclidean distance over all 360 features does not
  depend on column order at all, so this computation shows no divergence
  whatsoever (every reported digit matches).

All of the above were computed directly against the committed CSV with a
standalone script before any generator code was written, and are the exact
numbers embedded in the generator's `EXPECTED_*` constants and check-cell
tolerances; none were copied from the legacy audit without independent
verification.

## Sex/site: a new, Exercise-8-only sidecar export

Exercise 8's spec requires sex and acquisition site for coloring an
already-fitted plot (never as a PCA/K-means input). The established shared
export, `book/lite/files/data/abide_age_brain.csv`, deliberately does not
carry either field (WP41 maintainer guide section 3: "keep exports slim —
only the columns a notebook actually needs"). Rather than widen that shared
file — a change every other migrated exercise's committed checksum would
have to absorb, explicitly out of this WP's scope — a second, small,
Exercise-8-only export was created:

- `scripts/export_abide_demographics_lite_data.py` (`--write` / `--check`,
  same convention as every other export script) produces
  `book/lite/files/data/abide_age_brain_demographics.csv` (columns `age`,
  `sex`, `site`; 1004 rows) and its sidecar manifest.
- Row alignment with the existing `abide_age_brain.csv` is **not assumed**:
  both scripts start from the identical
  `abide_modeling_data.load_modeling_frame()` call, filtered to the
  identical `age.notna()` mask, in the frame's own original order (neither
  script sorts or shuffles). The new script's own `age` column exists
  purely as an explicit, row-by-row alignment check — both its own
  `--check` and `tests/test_export_abide_demographics_lite_data.py` assert
  the two files' `age` columns match **exactly**, confirmed directly: 1004/
  1004 rows match with zero mismatches.
- The public-fallback path (a bare downloaded notebook, or Colab, neither of
  which has either sidecar file) needs no second URL: the one pinned,
  checksummed ABIDE-II TSV every other exercise's fallback already points at
  was confirmed, directly against the live source, to already carry `sex`,
  `site`, `age`, and `group` columns — `load_demographics_table()`'s
  fallback branch re-reads that same TSV and applies the identical
  `dropna(subset=["age"]).reset_index(drop=True)` filter the main loader
  uses, guaranteeing matching row order on that path too.
- The existing shared `abide_age_brain.csv` and its sidecar manifest are
  **byte-for-byte unmodified** — confirmed by `scripts/export_abide_lite_data.py
  --check` still passing against its original committed checksum after this
  WP's work.

## Common notebook contract

The generator follows `scripts/generate_exercise_07_notebook.py`'s pattern
exactly: a `Blank(student, reference, id, tags)` class; `--student` /
`--reference` / `--check` / `--write`; a hidden, collapsed setup cell
duplicating (never importing) `load_abide_age_brain_table()`,
`load_demographics_table()`, `make_single_choice_question`,
`make_multi_choice_question`, and (new this WP) `_QUESTIONS` +
`show_question()`; a "Run the cell below first" notice; cell ids of the
form `wp47-NNN-slug`; every blank's check cell degrading to "Not complete
yet" rather than raising; `# YOUR CODE HERE` stubs with commented,
non-executable hints; "Required output name(s): ..." as the last line of
each activity's instructions. The generator is fully self-contained (WP41
maintainer guide section 4.7) — it does not import from any other
exercise's generator.

## Exercise 8 — Unsupervised Learning: what changed, section by section

1. **Learning Without a Target.** Trimmed from the legacy's longer
   supervised-vs-unsupervised prose to a single concise paragraph plus a
   bulleted list of what unsupervised methods can help with. The data-load
   cell (supplied, not a blank) loads both `load_abide_age_brain_table()`
   and the new `load_demographics_table()`, with the same
   `except NameError: raise RuntimeError(...)` actionable-error pattern
   every migrated exercise uses, and an explicit printed note that
   diagnosis/sex/site/age are loaded only for later coloring. Two checked
   questions (new per spec): "what can an unsupervised analysis help us
   explore" and the retained/adapted "with no target column supplied, what
   information can an unsupervised algorithm actually use" (correct
   explanation: predictor patterns/distances/variance, never hidden access
   to the external characteristics).
2. **PCA: Representing Many Features with Fewer Dimensions** — four guided
   blanks, the bulk of this migration's redesign:
   - **PCA fit** (`wp47-activity-pca`): students implement
     `StandardScaler` then `PCA(n_components=50, random_state=0)` on the
     brain predictors only, producing `Xs`, `pca_explore`, and `X_pca`
     (required names, matching the spec's naming exactly). The check cell
     validates shapes and a generous-tolerance PC1-explained-variance
     comparison.
   - **Two-panel explained-variance figure** (`wp47-activity-variance`):
     the exact scree/cumulative layout the author's reference image
     specifies (PCs 1-15 scree; PCs 1-50 cumulative with a dashed 50% line
     and a PC1 annotation), computed from the student's own `pca_explore`.
   - **PC1-vs-PC2 scatter colored by age** (`wp47-activity-scatter`): a
     continuous, reversed-sequential (`viridis_r`) colorbar so brighter
     means younger, exactly as the spec requires. A supplied (non-graded)
     follow-on cell demonstrates re-coloring by diagnosis as a categorical
     pattern reusable for sex/site; a checked question on what visible
     separation can and cannot establish follows.
   - **Loadings inspection** (`wp47-activity-loadings`): top-8
     largest-|loading| regions per component for PC1/PC2, signed bars
     (never magnitude-only), with a note on sign-flip non-significance.
   - The legacy's grouped-by-anatomical-bundle loading summary (frontal/
     parietal/temporal/occipital mean-|loading|) is **dropped** as a
     deliberate scope trim (see below) — the spec's content sequence for
     this section does not name it, and the per-ROI loadings bars already
     carry the section's interpretive point.
3. **K-Means on Your PCA Result** (new section, replacing the legacy's
   separate "Clustering concept" + "Research Example" sections): one
   guided blank (`wp47-activity-kmeans`). `N_CLUSTER_COMPONENTS=10` and
   `K_CANDIDATES=[1,2,3,4,5,6]` are supplied, predeclared constants, sliced
   directly from the student's own `X_pca` (never a fresh, secret PCA
   refit, per the spec's explicit instruction). Students fit one `KMeans`
   per candidate `k` with explicit `n_init=10, random_state=0`, recording
   inertia for every `k` and silhouette for every `k≥2` (k=1 correctly
   excluded, since silhouette is undefined there), then plot both curves.
   A checked question follows on what inertia/silhouette do and do not
   prove.
4. **Interactive Activity — Explore PCA and K-Means.** Ported to a native
   `ipywidgets` control: retained-PC, k, seed, and color-by dropdowns,
   reusing the *exact* established grid from
   `book/config/abide_modeling.json`'s `unsupervised.kmeans_catalog`
   (`retained_pc_grid=[2,5,10,20,50]`, `k_grid=[2,3,4,5,6]`,
   `seeds=[0,1,2]`, `n_init=10`, same defaults) — the whole
   (retained_pc × k × seed) grid (75 combinations) is computed once at
   setup time, not per interaction, exactly like Exercise 7's parameter
   explorer. The activity **prefers the student's own completed `X_pca`**
   from Section 2 when it exists, falling back to an independently
   computed projection with an explicitly printed note otherwise — the
   spec's own instruction ("label if it uses a fixed example or cached
   projection rather than the student's X_pca... provide helpful guidance
   when that student task is incomplete"), confirmed live in a real
   Pyodide session on both paths. The legacy's "guided look at choosing k"
   walkthrough prose is preserved as the activity's own follow-on note
   (age-discretization caution; explicit "must never be called autism
   subtypes"). One checked question follows, confirming that retained-PC
   count (not just the visible PC1/PC2 scatter) actually changes what feeds
   K-means.
5. **Using PCA in a Supervised Pipeline.** Kept as supplied, runnable code
   per the spec's explicit instruction (this is the already-audited
   leakage-safe comparison, not a new student activity): the same
   `component_grid`/`k_grid`/`KFold` recipe as the legacy notebook,
   `StandardScaler`/`PCA` fit **inside** the `Pipeline` on every fold —
   never reusing Section 2's full-cohort `Xs`/`pca_explore` (verified
   structurally: `pca_explore` does not appear anywhere in the pipeline
   cell). A new checked question (per spec) asks why that reuse would leak
   information even though PCA never looks at the target. A "Think first"
   written-answer blockquote (reused from the legacy notebook verbatim) and
   a closing practical-takeaway paragraph complete the section.
6. **What Should We Remember?** Six takeaway questions (trimmed from the
   legacy's prose-heavier closing), plus an explicit, honest note on the
   answer-key-visibility change (see next section) — stated to the student,
   not hidden from them.

## Multiple-choice answer visibility (WP47's new requirement)

Every checked question in this notebook now renders via
`show_question("question-id")` — a single-line call with no visible
`correct_index`/`correct_indices` anywhere in that cell's source. The
`_QUESTIONS` dict (prompt, options, `correct_index`, feedback text) and the
`show_question()` dispatcher live only in the hidden, collapsed setup cell
(`wp47-000-setup`), alongside the unchanged `make_single_choice_question`/
`make_multi_choice_question` widget builders. Verified directly:

- `tests/test_exercise_08_lite_notebook.py::test_checked_questions_use_show_question_with_no_visible_answer_key`
  confirms exactly 6 visible calls, none containing `correct_index` or
  `correct_indices` as a substring.
- `tests/test_exercise_08_lite_notebook.py::test_hidden_setup_cell_carries_every_question_definition`
  confirms the hidden cell actually carries all 6 question ids and the
  `correct_index` keys.
- Live in a real Chromium/Pyodide session
  (`interactive/e2e-book/exercise-08-lite.spec.ts`): every one of the 6
  checked questions renders its prompt/options/feedback correctly; one is
  exercised with both a correct answer (confirmed `"Correct:..."` feedback)
  and, separately, a deliberately wrong answer (confirmed `"Not quite..."`
  feedback and confirmed that cell's own rendered text does not contain
  `"correct_index"`).

**Honesty about the limit, stated here and in the notebook's own closing
summary**: this is a readability/UX improvement, **not secure answer
protection**. A fully downloadable, offline, editable notebook must contain
enough information to check an answer locally — a technically curious
student can always recover the answer key by expanding the hidden setup
cell (a single click) or by inspecting the running kernel's own namespace
(`_QUESTIONS["q-..."]["correct_index"]`). No obfuscation was used, and no
claim of secrecy is made anywhere in the notebook or this report. Per the
WP47 spec's explicit instruction, a **future shared migration option** for
Exercises 1-7 (moving this same pattern into their own shared question
infrastructure) is recorded here as a forward-looking option, not
implemented now — those notebooks' own shared question-checking code was
not touched, since the author has explicitly deferred their tests in this
WP.

## Deliberate scope trims (documenting per the WP's own instruction)

- The legacy's "Find the Best Projection" interactive activity (a small
  synthetic 2-D projection-angle slider, unrelated to the ABIDE brain data)
  is **dropped outright**, not ported. The WP47 spec's content sequence
  does not name it among the five required sections, and its own teaching
  point (that PCA's first component maximizes captured variance) is now
  covered by the PCA-fit blank's own check cell and the explained-variance
  figure, which operate on real data rather than a synthetic demonstration.
  Its backing widget config/data/export script
  (`scripts/export_pca_projection_widget.py`,
  `book/_static/widgets/configs/pca_projection.json`,
  `book/_static/widgets/data/pca_projection.json`) are left in place,
  unused, matching the exact precedent WP44-46 set for every other retired
  legacy widget.
- The legacy's grouped-by-anatomical-bundle loading summary (mean absolute
  loading within frontal/parietal/temporal/occipital bundles) is dropped;
  the new per-ROI top-8 loadings bars (signed, not grouped) already carry
  the section's stated interpretive point, and the spec's content sequence
  for this section asks only for "top positive/negative or top
  absolute-loading brain features", not a grouped anatomical summary.
- The legacy's separate "Research Example — Exploring Neuroanatomical
  Profiles" section (a fully supplied, single-configuration PCA→K-means
  demo with its own external-characteristic comparison) is folded into the
  new Section 3's guided student blank: the same core computation (PCA
  scores → K-means → inertia/silhouette) is now something the student does
  themselves across a small `k` grid, rather than watching a single
  pre-chosen configuration run. The legacy's own established numbers at
  its specific `(retained_pc=10, k=3, seed=0)` configuration are preserved
  exactly as one point on the new blank's own curve (see "Numbers verified"
  above: cluster sizes and silhouette match the legacy audit exactly).
- Neither trim altered any audited number materially or removed a
  pedagogical point the surrounding text claims to make.
- WP46's own deliberate trims (Exercise 6/7 widget grid subsets) were not
  touched, per this WP's own instruction not to fold unrelated WP46 polish
  into this WP without a concrete need — none arose.

## A no-cascade check

The untouched student template was executed cell-by-cell (the same offline
executor `tests/test_exercise_08_reference_execution.py` uses, applied to
the *student*, not reference, notebook) before any browser testing: zero
exceptions, every one of the five blanks' own check cells printed its own
"Not complete yet" guidance in place of a result, and Section 4's activity
and Section 5's pipeline — both independent of the student's own blanks —
still ran and printed real results. Confirmed again live in a real
Chromium/Pyodide session (`.jp-mod-error` count of 0 on "Run All Cells" for
the untouched template).

One genuine, documented finding from building the live-browser
teacher-completed-path test (not a notebook defect): Section 4's native
widget cell, like any notebook cell, does not retroactively re-execute just
because an earlier cell's output changed. A student who runs the whole
notebook once, then goes back and fills in Section 2's PCA blank, must
re-run Section 4's widget cell (by reaching it in normal top-to-bottom
order, or via "Run All Cells" again) before it will pick up their own
`X_pca` instead of its own independently computed fallback. This is
ordinary, expected Jupyter behavior (identical to every other cell-ordering
dependency in this course), not a bug — flagged here because it is the
first Exercise-8-specific instance of a native activity depending on a
student blank's own output, a pattern Exercises 6/7's own native widgets
did not have (their activities depend only on Section 1's supplied data
load, never a student blank).

## Verification and stop conditions

Scope, per the WP47 spec's explicit instruction: **Exercise 8 and directly
changed support code only.** No full Python/browser suite, no old-notebook
retest, no course-wide suite was run in this WP.

### Generators
`python scripts/generate_exercise_08_notebook.py --check` and
`python scripts/generate_exercise_08_transition_page.py --check` both pass:
every committed output file is byte-identical to what the generator
produces now. `python scripts/export_abide_lite_data.py --check` (the
existing, **unmodified** shared export) and
`python scripts/export_abide_demographics_lite_data.py --check` (the new
sidecar, including its own row-alignment check against the existing export)
both pass. `python scripts/build_portable_notebook.py --check --notebook
all` passes (now scoped to chapters 9-10 only, Exercise 8 correctly
removed).

### Reference-notebook execution and no-cascade (offline, exact)
`tests/test_exercise_08_reference_execution.py` (14 tests, ~12s): executes
every cell's actual source, in order, in one shared namespace (the same
semantics a kernel uses — never `nbclient`, since this notebook's native
widget uses `ipywidgets.Output()` as a context manager, which hangs a real
ZMQ kernel with no frontend attached), from a clean working directory
containing only the two committed same-origin CSVs. Every established
number above is asserted against the notebook's own recomputed values,
with generous tolerances on the one genuinely data-source-sensitive number
(Section 5's selected `k`/test MSE). The *untouched student template* is
separately executed the same way: zero exceptions, every blank's own check
cell prints "Not complete yet", and Section 4/5 still produce real results.

### Structural / offline
`tests/test_exercise_08_lite_notebook.py` (28 tests): all 5 required
blanks exist and are not pre-solved even in comment form (hint lines are
always commented out), no `NotImplementedError`, no install cell, no
iframe or legacy-widget-config reference anywhere, all 6 checked questions
carry no visible answer key (verified against the hidden setup cell
instead), the K-means activity's native widget and its "prefers the
student's own X_pca, labeled fallback otherwise" behavior are both
structurally confirmed, Section 5's pipeline is confirmed supplied (not a
blank) and confirmed to never reference `pca_explore`, and the student
template / portable copy / reference notebook stay structurally
synchronized cell-by-cell (only `Blank`-tagged cells may differ).
`tests/test_exercise_08_transition_page.py` (9 tests): H1 unchanged,
correct Lite/download links, no raw-GitHub or Colab deep link, no
duplicated analysis code. `tests/test_export_abide_demographics_lite_data.py`
(6 tests): header/participant-count, sex values in {1,2}, multiple site
levels present, and — the one that matters most — exact row-order alignment
with the existing `abide_age_brain.csv`'s own `age` column.

### Repository-wide content audit
`tests/test_wp35_content_audit.py` (7 tests, scanning every canonical and
portable notebook including the new Exercise 8 transition page and
portable copy) passes — no author-facing phrase, no stray WP-number
reference, no "development partition" phrasing anywhere a student can see
it. Two such leaks were caught and fixed during this WP's own verification
pass, before this report was written: a script-path reference
(`scripts/export_abide_demographics_lite_data.py`) in the
`load_demographics_table()` docstring, and a WP-number reference
(`WP47 "Multiple-choice answer visibility"`) in a setup-cell comment — both
were student-facing (inside the generated notebook's own hidden setup
cell), both rewritten to generic phrasing, and the fix was re-verified
green before proceeding. `tests/test_exercise_manifest.py`,
`tests/test_wp19_content_audit.py`, `tests/test_wp24_content_audit.py`,
`tests/test_wp25_content_audit.py`, `tests/test_exercise_09_notebook.py`,
and `tests/test_placeholder_exercises.py` all pass unchanged (125 tests
total across this focused re-run, confirming the Exercise 8 retirement did
not disturb Exercise 9's own cross-reference check or the manifest's
hardcoded `migrated == [1, 2]`).

**Full offline Python suite across all ten exercises was explicitly NOT
run**, per the WP's own scope instruction — the author wants one
comprehensive suite later, once every notebook is migrated.

### Frontend
`npx tsc --noEmit` (from `interactive/`) passes with no errors, both
immediately after the e2e spec rewrites and after the new
`exercise-08-lite.spec.ts` file was added.

### Jupyter Book + JupyterLite build
`jupyter-book build book --all` succeeds in 4 seconds (2 pre-existing,
unrelated warnings only: a missing `logo.png`, and `book/README.md` not in
any toctree — both present before this WP, unrelated to Exercise 8).
`jupyter lite build --config book/lite/jupyter_lite_config.json --lite-dir
book/lite --output-dir book/_build/html/lite` succeeds in 5 seconds;
`exercise_08.ipynb`, `exercise_08_portable.ipynb`, and the new
`abide_age_brain_demographics.csv`/`.manifest.json` all copy into the built
`lite/files/` tree correctly, with no per-exercise JupyterLite registration
needed.

### Playwright, built book (real headless Chromium, actual combined build)
Every command's expected duration was stated and a hard timeout set before
running, per the WP's own time-discipline instruction; actual elapsed time
is recorded below for each.

- `chapter08.spec.ts` (expected: seconds; timeout: 3 min; actual: **3.0s**,
  4/4 passed): transition page has no iframe, exactly one correctly-labeled
  Lite link, a working download link, no top-bar Colab button, no
  raw-GitHub/Colab deep link.
- `exercise-08-lite.spec.ts`'s untouched-template tests alone (expected:
  2-3 min; timeout: 6 min; actual: **1.6 min**, 3/3 passed): "Run All
  Cells" produces zero error cells, the data-load line prints, all five
  blanks' check cells show "Not complete yet", and Section 4/5 still
  produce real results; 390px usability; Reset/Back.
- `exercise-08-lite.spec.ts`'s teacher-completed-path test alone (expected:
  5-10 min; timeout: 15 min; actual: **2.5 min** after one live fix — see
  below). This file's own heaviest supplied step (Section 5's pipeline:
  `component_grid × k_grid` = 20 combinations × 5 folds, up to 100 PCA
  components, on 753 rows) is roughly two orders of magnitude cheaper than
  Exercise 7's `GridSearchCV` pipeline, so this test is deliberately
  smaller than Exercise 6/7's own per-blank coverage, per the WP47 spec's
  own "a small Exercise 8 Playwright smoke" instruction — one live bug
  found and fixed (documented in full, not glossed over): the test
  initially checked the native widget's "using your own completed PCA"
  message immediately after filling all five blanks via individual
  Shift+Enter, without ever re-running Section 4's own widget cell — which
  had already executed once (with its independently computed fallback)
  during the test's own initial "Run All Cells". This is the exact,
  expected "a cell does not retroactively re-execute" behavior documented
  above, not a notebook bug; fixed by explicitly re-running the widget cell
  before checking it, mirroring Exercise 7's own established `runCell()`
  step-forward pattern.
- **A full 4-test run of `exercise-08-lite.spec.ts` together**, serialized
  (`--workers=1`, matching WP45/46's own precedent for checking
  cross-test contention): **4/4 passed, 4.3 minutes total** — no
  resource-contention flakiness observed at this notebook's much lighter
  compute profile (contrast WP46's own finding of contention in Exercise
  7's heavier file at only 7 tests).
- `launch-buttons.spec.ts` + `iframe-height-contract.spec.ts` together
  (the two shared files this WP modified): **22/22 passed, 9.5 seconds**
  — Exercise 8's Colab-button suppression test passes, and its two retired
  iframe cases are correctly absent from the height-contract list (only
  Exercises 9-10's iframes remain in that file).

**No test in this WP exceeded 5 minutes**; the full `exercise-08-lite.spec.ts`
file's total (4.3 min across 4 tests) is reported for planning, per the
WP's own instruction, even though it is under the 5-minute flag threshold.

**Full combined Playwright book suite (all ten built exercises): not
attempted**, deliberately, per the WP's own scope instruction (one
comprehensive suite later, once every notebook is migrated) and consistent
with WP45/46's own left-open item.

## Build tooling: files updated

- `book/config/exercise_manifest.json`: `$comment` extended to name
  Exercise 8 as built-and-locally-verified-pending-Colab, alongside 3-7;
  the Exercise 8 entry itself is untouched (`migrationState: "legacy"`,
  every Lite field `null`), matching the existing entries for 3-7 exactly.
  `tests/test_exercise_manifest.py` needed no changes (it already
  hardcodes `migrated == [1, 2]` unconditionally).
- `book/_static/launch-buttons.js`: `chapter_08` removed from
  `PAGE_TO_PORTABLE`; the file-header comment and its list of transition-
  page generator scripts both extended to name Exercise 8 alongside 1-7.
- `interactive/e2e-book/launch-buttons.spec.ts`: the `CHAPTERS` array no
  longer includes Chapter 8; one new "gets no top-bar Colab button"
  suppression test added for it, matching the existing Chapter 1-7 pattern.
- `interactive/e2e-book/iframe-height-contract.spec.ts`: the two
  Exercise-8 iframe cases removed from `CASES`; the file's own explanatory
  comment extended to cover Exercises 1-8 (there is no iframe-height
  contract left to check for any JupyterLite-native exercise).
- `interactive/e2e-book/chapter08-dark-mode.spec.ts`: **deleted outright**
  — a dedicated Plotly-color dark-mode regression guard for Exercise 8's
  two old iframe activities, which no longer exist, mirroring WP45/46's
  exact treatment of the analogous files for Exercises 5-7. (Exercise 8's
  own JupyterLite notebook view has no replacement per-exercise dark-mode
  coverage, matching the exact precedent Exercises 1-7's own `*-lite.spec.ts`
  files already set — none of them test dark mode either, since the
  mechanism that old guard checked no longer exists once an exercise is
  native. Flagged explicitly rather than silently dropped.)
- `scripts/build_portable_notebook.py`: `CHAPTER_08` removed from the
  `NOTEBOOKS` registry dict (its `NotebookSpec` constant left in place,
  unused, matching the existing precedent for chapters 1-7); the module
  docstring's `--notebook` choices list and explanatory comments updated.
- `scripts/smoke_portable_notebook.py`: the `chapter_08` `SMOKE` entry
  removed, with the same explanatory comment template (`ipywidgets.Output()`
  / `nbclient` hang) already used for chapters 1, 4, 5, 6, and 7; the
  module docstring's bullet list updated to match.

No changes were made to Exercises 1-7 or 9-12's own content, to
`Homework_Materials/`, to `book/lite/extensions/course-toolbar/`, to
`book/lite/overrides.json`, to `book/lite/jupyter_lite_config.json`, or to
any legacy React widget component/export-data script/config
(`interactive/src/components/pca-projection.ts`,
`pca-kmeans-explorer.ts`, and their registry entries,
`book/_static/widgets/configs/pca_projection.json`,
`book/_static/widgets/configs/pca_kmeans_explorer.json`,
`book/_static/widgets/data/pca_projection.json`,
`book/_static/widgets/data/pca_kmeans_explorer.json`,
`scripts/export_pca_projection_widget.py`,
`scripts/export_pca_kmeans_widget.py`, `scripts/pca_kmeans_audit.py`,
`scripts/pca_kmeans_audit_result.json`) — all left in place, unused,
matching the exact precedent WP44-46 already set for the analogous
Exercise 1-7 components.

## The Colab blocker

This session has no real Google Colab access (no browser session against
`colab.research.google.com`). Local verification instead ran the actual
reference/portable/student notebooks through a real Python execution
(reproducing every established number above, from the committed same-origin
CSVs) and a real headless-Chromium Playwright session against the actual
combined local build (the untouched and teacher-completed paths, every
checked question and the native widget, 390px, reset/back,
download-contains-edits). Real Colab verification for Exercise 8 is a
required, explicit open item for the course author, exactly as it already
is for Exercises 3-7.

## WP45/WP46's still-open gates, carried forward

Per the WP's explicit instruction to keep these honest rather than treat
them as closed by unrelated later work:

- Exercises 3-7's real-Colab acceptance gate (WP41 maintainer guide section
  11) is **still open**. This WP does not touch those exercises and does
  not affect that gate either way.
- WP45's own full combined Playwright suite (a clean, uninterrupted
  from-scratch full-suite run covering Exercises 1-5) is **still open**;
  this WP did not attempt a combined run spanning any set of exercises (see
  above), so it provides no new data toward closing that item either way.
- WP46's own full combined Playwright suite (all ten built exercises) is
  **still open** for the same reason.

## Colab-proxy artifacts prepared for the author

Per the WP's explicit instruction, a private, **not committed, not
published** set of files was prepared for the course author's later manual
Colab check, kept outside the repository entirely (this session's own
scratch directory, not `Homework_Materials/` and not any git-tracked path):

- `exercise_08_TEACHER_FILLED_private.ipynb` — verbatim copy of
  `scripts/reference_notebooks/exercise_08_reference.ipynb`, every blank
  filled with the reference solution.
- `exercise_08_student_unfilled_portable.ipynb` — verbatim copy of the
  actual, unmodified file a student would download
  (`book/downloads/chapter_08/exercise_08_portable.ipynb`), kept alongside
  the completed copy for side-by-side comparison; the real, canonical copy
  a student downloads remains the one committed at that repository path.
- `COLAB_CHECKLIST.md` — the WP41 maintainer guide's own section 12
  checklist template, filled in with this WP's actual established numbers
  and every checked-question topic to confirm, marked **UNVERIFIED (real
  Colab not reachable from this session)** with the blocker stated, plus a
  summary of what has actually been verified locally/in-browser, ready for
  the author to complete the moment real Colab access is available.

These files were reported to the user directly at the end of this WP
(their local path is not repeated in this report to avoid implying it is a
repository path); they are not referenced from any committed file.

## Deviations and decisions requiring course-author attention

1. **Section 5's PCA+KNN pipeline selects a different `k` than the legacy
   notebook** (`k=5`, not `10`) at `n_components=20`, with a correspondingly
   different locked-test MSE/R² (19.1/0.795 vs. the legacy 21.0/0.775) — see
   "Numbers verified before writing a line" for the full explanation (a
   genuine, near-tied cross-validation margin that this data source's
   6-significant-figure rounding flips, not an error in either notebook —
   both select from the identical declared procedure). The course author
   should decide whether this deserves a one-line note in the notebook
   itself beyond what is already there, or whether the current framing
   (report only, no notebook-visible caveat, since the notebook's own
   numbers are internally consistent and correctly derived) is sufficient.
2. **Two interactive activities from the legacy notebook became one.** The
   legacy's "Find the Best Projection" (synthetic 2-D projection-angle
   slider) is dropped outright rather than ported natively — see
   "Deliberate scope trims" above for the reasoning. Flagged here in case
   the author specifically wants that activity preserved in some form; its
   backing export script and widget assets remain in the repository,
   unused, so reviving it would not require regenerating any data.
3. **The answer-key-visibility change is Exercise-8-only.** Exercises 1-7's
   own checked questions still show `correct_index=`/`correct_indices=`
   inline in their visible cells, per the WP's explicit instruction not to
   touch the shared question system or older notebooks in this WP. A future
   shared migration (moving `show_question(id)` + a hidden `_QUESTIONS`
   dict into each exercise's own setup cell, or into genuinely shared
   infrastructure) is recorded here as an option for after the course-wide
   testing gate, not implemented now.
4. **The grouped anatomical-bundle loading summary is gone.** The legacy
   notebook's frontal/parietal/temporal/occipital mean-|loading| bar chart
   is not present in the new notebook (see "Deliberate scope trims").
   Flagged here in case the author specifically wants that comparison
   preserved; `book/config/abide_modeling.json`'s own `bundles` config and
   `abide_modeling_data.bundle_columns()` helper (which produced it) are
   untouched and still available if a future WP wants to re-add it.
5. `book/README.md` still not in any toctree (pre-existing warning,
   unrelated to this WP, left as found).

## Confirmation

No merge, no push, no deployment, and no GitHub Actions interaction at any
point in this WP. `Homework_Materials/` was never inspected or modified.
Exercises 1-7 and 9-12's own content is untouched except for the narrow,
required cross-referencing changes to shared test/build-tooling files
listed under "Build tooling" above. The manifest's Exercise 8 entry remains
`migrationState: "legacy"`, exactly like Exercises 3-7, pending the course
author's own real-Colab check.
