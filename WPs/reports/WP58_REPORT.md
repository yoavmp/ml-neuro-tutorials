# WP58 Report — Exercise 10: Deep Learning (local review only)

## Summary

Built a from-scratch, Colab/local-Jupyter-only **Exercise 10: Deep
Learning** notebook on feature branch
`feature/wp58-active-exercise-10-deep-learning`, branched from `main` at
`c94628f`. **Nothing was merged, pushed, built into the Jupyter Book site,
or deployed.** No workflow ran. Exercises 1–9 and 12 are untouched;
Exercise 11 was not touched; the preserved legacy Exercise 10 notebook
(`book/chapters/chapter_10/exercise_10.ipynb`, "Examples and Common
Mistakes", WP38/WP38R) and its portable copy, and the live published
placeholder stub (`book/chapters/chapter_10/placeholder.md`), are all
**completely untouched** — confirmed by `git status`/`git diff` returning
nothing for `book/chapters/chapter_10/` throughout this WP, and by the new
`LegacyExerciseTenUntouched` test class.

**Gate A result: PyTorch does not work in this course's actual pinned
JupyterLite build.** Verified directly, not assumed (see below). The
notebook was therefore built for Python 3.11 in Colab and ordinary local
Jupyter only, per the WP's own fallback instruction. The live book page
stays the existing "coming later" placeholder — no JupyterLite template,
no live/manifest/toc wiring, nothing that could look like a live route.

**Result: notebook, private teacher-filled reference copy, generator,
and 29 focused structural tests all green; one full teacher-filled
execution on CPU in an isolated Python 3.11 environment completed in
7.8 s wall time (comfortably under the 15–20 min target); honest final
numbers recorded below (neither model clears 60% accuracy; the network
modestly outperforms the regularized-logistic-regression baseline on
accuracy/AUC but has lower sensitivity).**

## Gate A — runtime and data feasibility

### 1. JupyterLite/PyTorch (bounded to ~30 minutes, two independent checks)

This course's actual pinned browser kernel is `jupyterlite-pyodide-kernel
== 0.8.5` (`requirements-lite.txt`), which — read directly from the
installed package's `constants.py`, not documentation — pins **Pyodide
v314.0.5** (Python 3.14.2, `wasm32`/`emscripten`). Two checks against that
*exact* build, not a generic browser demo:

1. **The build's own published package lockfile.** Fetched
   `https://cdn.jsdelivr.net/pyodide/v314.0.5/full/pyodide-lock.json`
   (the same CDN URL `jupyterlite_pyodide_kernel.constants.PYODIDE_CDN_URL`
   uses) — 356 packages listed, built for `arch=wasm32,
   platform=emscripten_5_0_3, python=3.14.2`. **No `torch` entry.**
2. **A real headless-Chromium run of that exact build.** Via Playwright
   (already installed for this repo's own e2e suite), loaded
   `https://cdn.jsdelivr.net/pyodide/v314.0.5/full/pyodide.js` in a real
   browser page, called `loadPyodide()`, loaded `micropip`, and ran
   `await micropip.install("torch")`. Result:

   ```
   ValueError: Can't find a pure Python 3 wheel for 'torch'.
   See: https://pyodide.org/en/stable/usage/faq.html#why-can-t-micropip-find-a-pure-python-wheel-for-a-package
   ```

   PyTorch has no official `wasm32` wheel on PyPI, so `micropip` (which
   can only install pure-Python or already-Pyodide-packaged wheels) has
   nothing to find. This confirms the lockfile result with a live attempt,
   not just a static list.

**Conclusion: not reliable — in fact, not possible at all with this
course's current pinned build or with any wheel on PyPI.** No install
cell was added to JupyterLite, no NumPy-based imitation of PyTorch was
substituted, and no JupyterLite launch button was created for this
exercise. The live placeholder page is unchanged. Whether/how to offer
Exercise 10 on the real site as a Colab-only download is left as an open
release decision for the course author (see "Release decisions" below).

Elapsed time for this check: ~20 minutes (environment/version discovery,
the lockfile fetch, writing and running the Playwright script) — within
the ~30-minute budget, and no attempt was made to port PyTorch or adopt an
unmaintained WebAssembly wheel.

### 2. Python 3.11/Colab/local PyTorch actually works

Verified directly in an isolated Python 3.11.16 virtual environment
(`python3.11 -m venv`, CPU-only `torch` from
`https://download.pytorch.org/whl/cpu`): tensors, `requires_grad_`/
`.backward()` autograd, an `nn.Linear` module, and a real
`torch.optim.Adam` step all ran correctly (`torch 2.2.2`, `numpy 1.26.4` —
see "Deviations" for why `numpy<2` was pinned). This environment is also
where the full notebook was later executed end-to-end (see "Verification"
below).

### 3. ABIDE-II structural feature families (verified live, not assumed)

Inspected the same pinned NeuroHackademy/Yarkoni source this course
already uses for Exercises 2–9
(`book/config/abide_modeling.json`, commit
`e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b`, CC-BY-4.0) by actually running
`scripts/abide_modeling_data.py --audit` (network) rather than trusting
its docstring:

- **1,004 participants** (unique, no duplicates), merged frame 1,452
  columns.
- **Four complete structural feature families**, each a genuinely
  bilateral 360-column block (180 HCP-MMP1/Glasser ROIs × 2 hemispheres):
  cortical thickness (`fsCT`, mm), cortical surface area (`fsArea`, mm²),
  grey-matter volume (`fsVol`, mm³), local gyrification index (`fsLGI`,
  unitless). **1,440 structural features total, 0 missing cells** —
  verified live; not assumed, per the WP's own instruction not to assume
  all four families are complete.
- Raw `abide2.tsv` download size: **10.48 MB** (verified via a live
  fetch+length check, not the docstring's number).
- Target: the table's own native `group` column (1=autism, 2=control;
  recoded here to autism=1/control=0), **463 autism / 541 control, 0
  missing**, present for all 1,004 participants (no join against the
  phenotypic file is needed for this target — unlike Exercise 2/9's `age`
  target, `group` is native to `abide2.tsv` itself).
- 17 sites (`site` column) — never used as a predictor; only brain-derived
  columns and `group` are selected into `X`/`y`. No `DX_GROUP`-style,
  site, participant-id, or demographic column enters `X` (same leakage
  guard logic as `abide_modeling_data.assert_brain_only`, reused by
  construction via `abide_modeling_data.bundle_columns` at *generation*
  time only — the generated notebook's own embedded loader does not import
  `scripts/` at runtime, for portability).

**How this differs from the earlier cortical-thickness-only notebooks:**
Exercises 2–9 use `fsCT` alone (360 predictors). This notebook uses all
four families together (1,440 predictors) for the same 1,004 participants
— "beyond cortical thickness," as the WP asked, with the actual counts
shown live in the notebook's own first data cell, not asserted in prose.

## Notebook content

- **Files:**
  `book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb`
  (student, Colab/local) and
  `scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb`
  (teacher-filled, private, never published) — both generated by the one
  new `scripts/generate_exercise_10_deep_learning_notebook.py`, which
  renders one shared cell list twice (`mode="student"` /
  `mode="reference"`), so the two notebooks are structurally synchronized
  by construction, not by hand-maintained duplication. 44 cells each;
  identical cell order and source except the three intentional blanks.
- **Sections (1–6, matching "What this notebook covers"):** (1) setup and
  task — conditional `%pip install torch` cell, live data load showing
  1,004 participants / 1,440 features / class balance, explicit
  JupyterLite-limitation note with the Gate A evidence; (2) hold-out
  design and tensors — stratified train/val/test split (602/201/201),
  train-only `SimpleImputer`/`StandardScaler` (with an honest note that
  this particular table has zero missing values, so the imputer is a
  no-op defensive step here, not fabricated missingness), a required
  student blank building `float32` tensors + `TensorDataset`/`DataLoader`
  (batch size 64), followed by a shape/dtype/finite-value check with
  friendly (non-crashing) feedback; (3) a required student blank defining
  `AutismClassifierNet` (`nn.Module`, two hidden layers, `ReLU`, one output
  logit, no sigmoid before `BCEWithLogitsLoss`), with a forward-pass shape
  check; (4) a required student blank completing `train_one_epoch`/
  `evaluate` (forward pass + loss only — `zero_grad`/`backward`/`step`
  are given), then ready-to-run training with fixed seeds, early stopping
  on validation loss restoring the best-epoch weights, and a learning-curve
  plot; (5) one-time test evaluation — confusion matrix, accuracy,
  balanced accuracy, sensitivity, specificity, ROC AUC, a majority-class
  dummy baseline, and a regularized logistic-regression baseline on the
  *same* train-only-scaled 1,440 features, with Exercise 3's
  cortical-thickness-only result named once as context only ("not… a
  directly controlled comparison"); (6) six single-choice `show_question`
  checks (tensor shape, logits/`BCEWithLogitsLoss`, gradient-accumulation
  order, train-only scaling, overfitting/early stopping, why the test set
  cannot choose hyperparameters) plus a wrap-up citing a real structural
  (not functional-MRI-motion) harmonization study, with an explicit
  no-diagnostic/no-causal/no-definitive-ceiling disclaimer.
- **Hint hygiene:** every `# YOUR CODE HERE` comment in the student
  notebook describes *what* to do, never the literal expression (e.g.
  "run the model on this batch of inputs", not `model(xb)`) — the
  `test_student_blanks_contain_ellipsis_placeholder_not_full_solution`
  test asserts none of ten literal solution phrases (`nn.Linear(...)`,
  `self.fc3(x)`, `logits = model(xb)`, etc.) appear in any blank-tagged
  student cell; they do appear in the reference notebook's matching cells.
- **Hidden-key questions:** `_QUESTIONS` (prompt/options/`correct_index`/
  per-question shuffle seed) and `show_question()` are embedded as literal
  source *inside* the one hidden setup cell (`jupyter.source_hidden`,
  matching the exact mechanism Exercises 1–9/12 already use) — a visible
  `show_question("q-...")` call never prints or displays a
  `correct_index`. `test_correct_index_never_appears_outside_hidden_setup_cell`
  asserts this directly. Options are written correct-answer-first for
  generator readability; `show_question` shuffles the *displayed* order
  with a fixed per-question seed, so the correct option is not always in
  the same position.
- **No MyST directives anywhere** (`` ```{admonition} `` /
  `` ```{dropdown} ``) — this notebook has no Jupyter Book page at all, so
  there is nothing for those directives to render against; plain Markdown
  throughout.

## Honest results (one teacher-filled run, fixed seeds, never re-run to
pick a better outcome)

Split (stratified by `group`, `random_state=42`, two-stage
`train_test_split`, `test_size=0.4` then `0.5`):

| Partition | n | autism | control |
|---|---|---|---|
| train | 602 | 278 | 324 |
| validation | 201 | 92 | 109 |
| test | 201 | 93 | 108 |

Network: two hidden layers (128, 32), `ReLU`, `BCEWithLogitsLoss`, Adam
(`lr=1e-3`, `weight_decay=1e-4`), batch size 64, up to 50 epochs with
patience 8. Hidden-layer sizes, learning rate, and the logistic-regression
`C` (0.003) were all chosen by comparing a small grid of configurations on
**validation** performance only, before the test set was touched; this is
recorded transparently in the notebook's own markdown rather than
presented as an untuned default. Training early-stopped after epoch 10;
best validation loss at epoch 2 (0.6801); training loss fell from 0.6860
to 0.0193 over the 10 epochs run (visible overfitting past epoch 2, which
is exactly why the best-epoch weights — not the final epoch's — are
restored and reported).

Test set, evaluated exactly once, after every choice above was already
fixed:

| Model | Accuracy | Balanced acc. | Sensitivity | Specificity | ROC AUC |
|---|---|---|---|---|---|
| Dummy (majority class) | 0.537 | 0.500 | 0.000 | 1.000 | 0.500 |
| Logistic regression (C=0.003, 1,440 features) | 0.552 | 0.547 | 0.473 | 0.620 | 0.601 |
| Neural network | 0.577 | 0.562 | 0.366 | 0.759 | 0.615 |

**Reported honestly, as instructed:** the network modestly outperforms
the regularized-logistic-regression baseline on accuracy, balanced
accuracy, and AUC — but its sensitivity (0.366) is *lower* than the
baseline's (0.473): it is more conservative, catching proportionally
fewer true autism cases while classifying controls more confidently. Its
higher accuracy partly reflects the test set's own control-majority
composition, not a uniform improvement. **Neither model clears 60%
accuracy.** No seed was selected using test performance — the single seed
used throughout (`42` for data splitting, `42` for PyTorch/NumPy/`random`)
was fixed before any test-set result was seen, and the test set was
evaluated exactly once, by construction (one cell, run once per normal
pass through the notebook).

For context only (named once, explicitly flagged as not a controlled
comparison, since the feature set, split, and model all differ): Exercise
3's cortical-thickness-only logistic regression on this same `group`
target reached 54.6% test accuracy (AUC 0.569) —
`scripts/classification_model_audit_result.json`, unchanged by this WP.

## Verification

- **Generator `--check`:** both outputs match what
  `scripts/generate_exercise_10_deep_learning_notebook.py` would produce
  right now (also asserted by the new
  `ExerciseTenGeneratorStaleness` test, which imports the generator module
  directly rather than shelling out).
- **29 new focused structural tests**
  (`tests/test_exercise_10_deep_learning_notebook.py`), covering: nbformat
  validity, title/overview/section structure, the Colab/local-only and
  Gate A-evidence language, the single conditional install cell, exact
  data counts, no MyST fences, no engineering vocabulary, the three
  tagged blanks and their no-full-solution hint hygiene, all six
  `show_question` calls and hidden-key placement, train-only-scaling and
  early-stopping/one-time-test-evaluation language, the baseline
  comparison, the citation's exact qualifications, no diagnostic/ceiling
  claim, no repository-relative dependency in the portable notebook,
  student/reference structural synchronization, generator-staleness, and
  that the legacy notebook/placeholder are untouched. All 29 pass.
- **Genuinely shared/affected checks run** (per the WP's own instruction
  not to run the course-wide suite): `tests/test_abide_modeling_data.py`
  (24 tests, unmodified shared data module this notebook's *generator*
  reads from at build time), `tests/test_exercise_10_notebook.py` (the
  existing legacy-notebook test, confirming it still passes unchanged),
  and `tests/test_exercise_manifest.py` (confirming the manifest — which
  this WP does not touch — is still internally consistent). All green; 53
  tests total across these three files plus the new one above = 82 tests
  run for this WP, in well under one second of test time.
- **Full teacher-filled execution, end-to-end, on CPU, in an isolated
  environment (Python 3.11.16, `torch==2.2.2`+cpu, `numpy==1.26.4`,
  freshly created `python3.11 -m venv`, never reused from a prior WP):**
  `jupyter nbconvert --to notebook --execute` on
  `scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb`.
  **Zero errors.** Wall time **7.8 s** (repeated: 7.8 s and 9.7 s across
  two separate runs — both comfortably under the 15–20 minute target by
  roughly two orders of magnitude), covering kernel startup, the live
  10.48 MB network fetch + SHA-256 verification, the full split/scale/
  train/early-stop/plot/evaluate pipeline, and all six quiz-widget
  renders. **Caveat:** this machine already had `torch` installed in
  that environment; a learner's very first run, where the conditional
  `%pip install torch` cell actually has to install the package, adds
  roughly another 15–35 s one-time cost (measured separately, in a
  second from-scratch Python 3.11 venv with no `torch` present at all —
  the install-and-import succeeded cleanly, no error). Either way, total
  time stays far under the 15–20 minute target.
- **Student (blank) notebook, executed with every blank left unfilled**
  (to check the "no cascade of red exceptions" requirement): the two
  check cells for Sections 2–3 print a friendly "Not finished yet"/"Not
  quite" message and continue; the ready-to-run training cell (Section 4,
  not itself a check cell, but gated) raises one clear
  `RuntimeError: Not ready yet -- go back and complete the earlier
  blank(s) for: ...` naming exactly which variables are missing, instead
  of a deep `AttributeError` from inside `forward()`. In real Jupyter/
  Colab "Run All" behavior (stop at first error, the default — not the
  `--allow-errors` flag used only for this specific test), a learner
  sees exactly that one message and nothing past it.
- **Student notebook, blanks correctly filled (the reference notebook's
  own execution, above, is exactly this case by construction — same
  scaffold, same cell ids, real solutions in the three blank cells):**
  reaches the honest results reported above with no errors.
- **No real-Colab or real-JupyterLite-build run was performed** — this
  WP's "verified" claims are the four items above (Pyodide lockfile,
  live headless-Chromium `micropip.install` attempt, isolated-venv CPU
  execution, and the ABIDE-II live network audit); real Google Colab
  acceptance remains separately pending, as it does for every other
  active exercise in this course (see `book/config/exercise_manifest.json`'s
  own `$comment`). This is recorded here explicitly rather than implied.
- No browser/Playwright test of this exercise was run, per the WP's own
  instruction ("do not run a browser test that cannot execute PyTorch") —
  there is no JupyterLite build of this notebook to test in a browser.

## Local preview instructions (no `cd` needed)

Open directly in Jupyter, from the repository root:

```
jupyter notebook book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb
```

or in JupyterLab:

```
jupyter lab book/downloads/chapter_10/exercise_10_deep_learning_portable.ipynb
```

Requires `torch` (install with `pip install torch` if not already
present — the notebook's own first code cell in Section 1 does this
automatically if it is missing) plus the packages already in
`requirements.txt` (`numpy`, `pandas`, `matplotlib`, `scikit-learn`,
`ipywidgets`). Needs network access once, to fetch the pinned 10.48 MB
`abide2.tsv` (SHA-256-verified against the same pin
`book/config/abide_modeling.json` already uses).

For the private teacher-filled reference copy (same instructions, point
at the other file):

```
jupyter notebook scripts/reference_notebooks/exercise_10_deep_learning_reference.ipynb
```

For Colab: upload either `.ipynb` file directly (File → Upload notebook)
— both are fully self-contained (no repository-relative paths, no `_static/`
reference, no `<iframe>`, no MyST directive). Real Colab acceptance has
not yet been checked by the course author; see "Release decisions" below.

## Deviations

1. **Pinned `numpy<2` in the verification environment.** The CPU wheel of
   `torch==2.2.2` (the version actually resolved by
   `pip install torch --index-url https://download.pytorch.org/whl/cpu`
   in this environment at verification time) was compiled against
   NumPy's 1.x ABI and prints (non-fatal) `_ARRAY_API not found` warnings
   under NumPy 2.x. Pinning `numpy<2` in the *verification* venv removed
   the warning entirely and is the simplest fix; this is not something
   the notebook itself needs to pin, since `%pip install torch` on Colab
   or a learner's own machine will resolve whatever current, mutually
   compatible `torch`/`numpy` pair PyPI serves at the time — the
   notebook's own code uses no NumPy 1.x-only / 2.x-only API, so it is
   expected to work with either major NumPy version. Recorded here as an
   observation for the course author, not a change made to the notebook.
2. **Logistic-regression `C` and network hidden-layer sizes were chosen
   via a small validation-only grid**, not fixed by course design the way
   Exercise 3's `C=1.0` is. This was a deliberate reading of "Use
   validation for early stopping and model choices" (WP58 §"Notebook
   content and student activities" item 4) applied to item 5's baseline
   comparison too — the alternative (an arbitrarily fixed `C`/architecture)
   seemed more likely to produce an unrepresentative comparison by chance
   than a validation-selected one. Both choices, and the grids tried, are
   stated in the notebook's own markdown and in this report so the course
   author can revise the specific grid or revert to a fixed value if they
   prefer the Exercise-3-style framing.
3. **No same-origin local CSV data export was created** (unlike
   `book/lite/files/data/abide_age_brain.csv` for the JupyterLite
   exercises). Reasoning: that mechanism exists specifically because
   JupyterLite's in-browser kernel cannot reach `raw.githubusercontent.com`
   reliably/at all from inside a sandboxed `iframe` context; this
   notebook runs in Colab or local Jupyter, both of which already have
   ordinary network access, so it fetches the pinned, SHA-256-verified
   URL directly — the same pattern every other exercise's *portable*
   (non-Lite) copy already uses. No portable notebook in this course
   ships a bundled data file (confirmed: `book/downloads/chapter_02`,
   `chapter_09`, and `chapter_12` each contain only the `.ipynb`).
4. **The install cell does not pin a CPU-specific PyTorch index URL** —
   plain `%pip install torch`. On Colab this installs whatever `torch`
   build matches the runtime (CPU or GPU); on a learner's own machine it
   installs the current default wheel for their platform. The notebook
   never calls `.cuda()`/`.to("cuda")`, so it runs identically either way
   — this keeps the install instruction simple, per the WP's own
   direction to avoid "vague `pip install -r requirements.txt`" style
   complexity, while still working correctly regardless of which backend
   gets installed.
5. One sentence of the notebook's own opening ("Open this notebook
   directly in Colab... or in a local Jupyter installation") was revised
   mid-WP after an initial draft said "if you are reading this on the
   course website, download this notebook" — inaccurate, since nothing
   in this WP creates any course-website route to this notebook at all.
   Caught before the final generation pass; not a published-then-fixed
   error.

## Release decisions left to the course author

- **Whether/how to surface Exercise 10 on the live site at all** while it
  remains Colab/local-only — e.g., a plain download link with explicit
  "Colab or local Jupyter only, not JupyterLite" wording on the existing
  placeholder page, versus leaving it exactly as "coming later" until a
  JupyterLite-compatible path exists (if ever). This WP deliberately made
  **no edit** to `book/chapters/chapter_10/placeholder.md`,
  `book/intro.md`, `book/resources.md`, `book/references.md`,
  `book/_toc.yml`, or `book/config/exercise_manifest.json` — all of which
  are currently live/published — so that this decision stays entirely the
  author's, informed by this report, rather than pre-empted by a draft
  edit to a page nobody has reviewed yet. If useful, candidate wording for
  a future Introduction "installation" note and a Resources/References
  PyTorch link (software documentation, kept separate from the scholarly
  citation already embedded in the notebook itself) can be drafted on
  request once this direction is decided.
- **Real Google Colab and (separately) real browser-PyTorch acceptance**
  both remain unverified by direct Colab/browser access, consistent with
  every other active exercise in this course.
- **The validation-selected hyperparameters** (Section 5's deviation #2
  above) are a judgment call the author may want to revisit, especially
  given how close the two baselines' AUCs are (0.601 vs. 0.615) — a
  different, equally defensible small grid could shift which model "wins"
  by a point or two without changing the honest conclusion that neither
  model performs strongly on this task.

## Status

Clean on the feature branch after the commits below — `git status --short`
returns nothing. No merge, push, CI run, or deployment was performed or
attempted.
