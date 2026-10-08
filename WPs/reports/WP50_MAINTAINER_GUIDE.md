# WP50 maintainer guide: change-aware testing and deployment

This is the operating manual for the release gate WP50 built. It assumes
you have read `WPs/WP50_CHANGE_AWARE_NOTEBOOK_RELEASE.md` and
`WPs/reports/WP49_REPORT.md` section H (the policy this implements).

## 1. The idea in one paragraph

Every push to `main` (except a WP-docs-only one, unchanged from WP49) now
runs `scripts/classify_release_change.py` first. It diffs the pushed commit
against the **source commit of the last successfully published site**
(read from the `gh-pages` branch's own `deploy: <sha>` marker commit --
written by `peaceiris/actions-gh-pages` only when a publish actually
happens, so a failed or cancelled run never becomes the new base), decides
which of four gates the change needs (`skip` / `prose` / `exercise` /
`full`), and the rest of `.github/workflows/deploy.yml` runs only the
checks that gate requires before the one, unchanged publish step. The same
script and the same gates are available locally.

## 2. Where wording is edited, and what to regenerate

Exercise prose does not live in `book/chapters/chapter_0N/exercise_0N.ipynb`
by itself -- it is authored as string literals inside
`scripts/generate_exercise_0N_notebook.py` (the lesson/markdown cells and
the code cells) and `scripts/generate_exercise_0N_transition_page.py` (the
"Open Exercise N" page). After editing either file:

```
.venv/bin/python scripts/generate_exercise_0N_notebook.py --write
.venv/bin/python scripts/generate_exercise_0N_transition_page.py --write
```

This regenerates every derived file: the JupyterLite template
(`book/lite/files/exercise_0N.ipynb`), its served portable copy
(`book/lite/files/exercise_0N_portable.ipynb`), the downloadable copy
(`book/downloads/chapter_0N/exercise_0N_portable.ipynb`), the reference
notebook (`scripts/reference_notebooks/exercise_0N_reference.ipynb`), and
the transition page (`book/chapters/chapter_0N/exercise_0N.ipynb`).
**Commit the regenerated files together with the generator edit** -- the
classifier compares the *generated* notebooks, not the generator source, so
a generator edit with stale generated output is a correctness bug the
`--check` step (run for every gate) will catch, but you should not rely on
CI to find it for you.

## 3. What gate your change gets, and why

Run this any time, before or after committing, to see exactly what the next
push will do and why:

```
.venv/bin/python scripts/classify_release_change.py
```

It prints the comparison base, every changed path with its classification,
the prose-only verdict for each touched exercise, the final gate, and the
reason. Pass `--format json` for the machine-readable form CI uses, or
`--format both` for both.

| Gate | When | What runs before publish |
| --- | --- | --- |
| `skip` | Only `WPs/**` changed | Nothing -- no build, no publish (the push doesn't even trigger the workflow, via `paths-ignore`) |
| `prose` | Every touched exercise's *generated* notebooks differ only in markdown-cell wording from the last published version | That exercise's generator `--check`, its structural tests (`test_exercise_0N_lite_notebook.py` + `test_exercise_0N_transition_page.py`), one combined site build, `scripts/smoke_release_routes.py` for that exercise. No kernel execution, no browser. |
| `exercise` | A touched exercise has a real code/metadata/structure change (or an uncertain one), and nothing shared changed | The above, plus that exercise's `test_exercise_0N_reference_execution.py` and its own `exercise-0N-lite.spec.ts` + `chapterNN.spec.ts` Playwright specs. Multiple touched exercises: union of all of the above. |
| `full` | Any shared/global path changed (CSS, a shared script, exported data, the manifest, book/JupyterLite config, a workflow file, a Playwright shared fixture/config, the deploy mechanism itself), or any path the classifier doesn't recognize, or the comparison base itself is untrustworthy | The entire existing release gate, unchanged: full offline Python suite, full `npm run test:e2e:book`, frontend typecheck/unit/audit, the standalone widget app's own e2e, the chapter_02 portable-notebook kernel smoke. |

**A shared/unknown path always wins.** If your push touches one exercise's
own files *and* a shared file, it gets the full gate -- the exercise-scoped
and prose gates never apply to a mixed change. An unrecognized path (a
brand-new top-level file, a renamed file whose new name doesn't match a
known pattern, `README.md`, anything under `Homework_Materials/`, etc.)
is treated the same as a shared-surface change: conservative by default,
on purpose. Extending the "safe to skip/scope" pattern list is a deliberate
future change to `scripts/classify_release_change.py`, not something to
work around.

**Why "prose-only" is based on the generated notebooks, not the commit
message or the generator diff:** matching a file name or trusting a commit
message ("just a wording fix") is exactly what the WP50 spec rules out.
The classifier instead diffs the actual committed `.ipynb` JSON at the base
commit against HEAD for every one of an exercise's generated artifacts:
cell order and type must match, every code cell's `source` must be
byte-identical, and all cell/notebook metadata and outputs must be
unchanged. Only markdown-cell wording may differ. A changed string inside a
code cell -- including a multiple-choice option's label -- fails this check
and escalates to the `exercise` gate, per the spec's explicit example.

## 4. Requesting a full run

- **A full run is automatic** whenever the classifier can't justify
  anything narrower (see the table above) -- you don't need to do anything.
- **To force a full run on demand without a real content change**: push to
  a branch that touches any shared path (trivially,
  `.github/workflows/deploy.yml` itself, even a comment-only edit), or use
  the manual workflow below.
- **To run the full suite without publishing anything**: trigger
  **Full regression (manual)** (`.github/workflows/full-regression.yml`)
  from the Actions tab (`workflow_dispatch`). It runs the same broad
  Python + browser coverage the full gate does and has no publish step at
  all -- nothing it does can change the live site, pass or fail.
- **Exercises 9-10's own smoke test** (legacy, unpublished content) is
  unchanged from WP49: `.github/workflows/legacy-notebook-smoke.yml`, on
  demand (`workflow_dispatch`) or when `scripts/smoke_portable_notebook.py`
  or either chapter's downloads change. It never gates
  Exercises 1-8's publish.
- There is deliberately **no manual "skip tests" switch** anywhere in
  `deploy.yml` -- the only way to get a narrower gate than `full` is for the
  classifier to actually verify the change qualifies.

## 5. Seeing why CI chose a gate

Every run's **classify** job prints the full human-readable report (base,
every changed path and its classification, the prose verdict per exercise,
the final gate and reason) to its own step log, and sets it as that job's
outputs (`gate`, `exercises`, `reason`) -- visible in the Actions UI without
opening the log, and consumed by `build-and-deploy`'s step `if:`
conditions. To see what *would* happen before pushing, run
`scripts/classify_release_change.py` locally (section 3) -- it is the exact
same code, run the exact same way.

## 6. Running the same checks locally

```
.venv/bin/python scripts/run_selected_checks.py --phase pretest     # generator --check + structural/reference tests
# ... build the site once (see WP49_REPORT.md section H) ...
.venv/bin/python scripts/run_selected_checks.py --phase postbuild   # route smoke-check + (exercise gate only) the browser spec
```

Both recompute the classification themselves -- there's nothing to pass in.
If the classification is `full`, both print a note and exit 0 immediately;
run the existing broad suites (`python -m unittest discover -s tests`,
`npm run test:e2e:book`) directly, as before WP50.

`--phase pretest` needs nothing but the Python environment.
`--phase postbuild` needs `book/_build/html` to already exist (build it
first: `jupyter-book build book`, then the `jupyter lite build` step from
`deploy.yml`) and, for the `exercise` gate, a Chromium install
(`npx playwright install --with-deps chromium` from `interactive/`).

## 7. A note on scope

This WP did not re-derive which exercises actually share which widget-data
export or CSS rule -- any shared-surface change takes the full gate
unconditionally, rather than computing its precise blast radius. This is
simpler, more maintainable, and strictly more conservative than trying to
track exact shared-dependency graphs, and it is what the spec's own gate
table asks for ("Shared helper/CSS, data export, ... -- Full release
gate"). If a specific shared surface turns out to be worth scoping more
finely later, that is a deliberate, separate change to
`scripts/classify_release_change.py`'s pattern list -- not a sign this WP's
design is incomplete.

Exercises 9-12 are not fast-pathed either: they are legacy, unpublished
content (see `book/config/exercise_manifest.json`'s own `$comment`), and a
change confined to their source always takes the full gate, same as before
this WP, since optimizing their gate was never in scope here.
