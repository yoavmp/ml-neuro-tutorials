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
| `prose` | Every touched exercise's *generated* notebooks differ only in markdown-cell wording from the last published version, **and** every touched top-level page (`book/intro.md`, `book/contents.md`, `book/resources.md`, `book/references.md`) differs only in prose wording (WP56; see section 9) | That exercise's generator `--check`, its structural tests (`test_exercise_0N_lite_notebook.py` + `test_exercise_0N_transition_page.py`), one combined site build, `scripts/smoke_release_routes.py` for that exercise and/or page. No kernel execution, no browser. |
| `exercise` | A touched exercise has a real code/metadata/structure change (or an uncertain one), nothing shared changed, and no touched page is non-prose | The above, plus that exercise's `test_exercise_0N_reference_execution.py` and its own `exercise-0N-lite.spec.ts` + `chapterNN.spec.ts` Playwright specs. Multiple touched exercises: union of all of the above. |
| `full` | Any shared/global path changed (CSS, a shared script, exported data, the manifest, book/JupyterLite config, a workflow file, a Playwright shared fixture/config, the deploy mechanism itself), any path the classifier doesn't recognize, any touched top-level page with a non-prose change, or the comparison base itself is untrustworthy | The entire existing release gate, unchanged: full offline Python suite, full `npm run test:e2e:book`, frontend typecheck/unit/audit, the standalone widget app's own e2e, the chapter_02 portable-notebook kernel smoke. |

**A shared/unknown path always wins.** If your push touches one exercise's
own files *and* a shared file, it gets the full gate -- the exercise-scoped
and prose gates never apply to a mixed change. An unrecognized path (a
brand-new top-level file, a renamed file whose new name doesn't match a
known pattern, `README.md`, anything under `Homework_Materials/`, etc.)
is treated the same as a shared-surface change: conservative by default,
on purpose. Extending the "safe to skip/scope" pattern list is a deliberate
future change to `scripts/classify_release_change.py`, not something to
work around.

**A non-prose page change always wins to `full`, never merely to
`exercise`.** A touched page with a structural change forces `full` even
alongside an otherwise-prose-only exercise change -- see section 9.

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

## 8. Long-running local commands and CI watches must survive session interruptions

WP54 hit this directly: the harness's own background-task tracking
(`run_in_background: true`, and a `Monitor`/`until`-loop wrapper waiting on
it) does not reliably survive a session restart. The first two times a
full offline-suite run (`python -m unittest discover -s tests`, ~20-25
minutes) was launched that way, the *actual process was killed*, not just
the harness's record of it -- the run had to start over from zero both
times. The third attempt, launched fully detached from the harness's
process tree, survived three separate session restarts and completed
normally, with its full output intact on disk the whole time. Follow this
pattern for any local command expected to run more than a couple of
minutes: the full offline suite, `jupyter-book build`, `jupyter lite
build`, `npm run test:e2e:book`, and any `gh run` poll loop.

**Launch detached, not only via the harness's own background flag:**

```
nohup <command> > <durable-log-path> 2>&1 < /dev/null &
disown
echo "launched PID $!"
```

`nohup` blocks `SIGHUP`; `disown` removes the job from the shell's own job
table so it is not signaled when that shell exits. Redirect both
stdout/stderr to a durable log path under your scratchpad directory (never
a path that gets cleaned between sessions) -- this is the authoritative
record of what the command actually did, independent of whether anything
else watching it survives. Confirm the process actually detached (`ppid`
reparented to `1`, not the interactive shell) before trusting it to
survive a restart:

```
ps -o pid,ppid,pgid,command -p <PID>
```

**Record the PID and the log path in your own response to the user**, not
only in your own reasoning -- a session restart loses anything that was
only in context and never written down.

**Recover after a restart by checking real state, never by assuming either
success or failure:**

```
ps -p <PID>                 # still running?
tail -c 2000 <log-path>     # what has it actually produced so far?
grep -n "Ran .* tests\|OK$\|FAILED\|Error\|Traceback" <log-path>
```

A log file with no final summary line and no live process most often means
the harness's own watcher was killed, not the underlying computation --
check the log's actual content and modification time before concluding a
job failed, hung, or needs restarting. **Never re-launch a check "to be
safe" without first confirming, from the PID and log, that the previous
one is not still running and did not already finish.** A duplicate launch
wastes the full run time again and, for anything that writes output files
(a build, a regenerated notebook, a report), can race the first run and
corrupt the result.

**Poll autonomously once a command is launched detached** -- do not ask
the user whether it is done. A lightweight wrapper
(`until ! kill -0 <PID> 2>/dev/null; do sleep N; done; tail ...`, via
`run_in_background: true`) is a convenience for getting an in-session
notification when the command exits, but it is not load-bearing: if that
wrapper itself dies to a restart, re-check the log/PID directly instead of
re-running the underlying command. Report real progress (lines produced,
elapsed time) at reasonable intervals, matching the existing WP50-spec
rule for long commands: record its process ID, monitor it until exit, read
its exit status and actual failure output immediately, and report a status
update at least every five minutes -- never leave a finished or crashed
job idle awaiting a prompt.

**A pushed commit's GitHub Actions run survives independently of any local
process** -- it runs on GitHub's own infrastructure and does not depend on
this session staying alive at all. Record the run ID from the `git
push`/`gh run list` output immediately, and recover it after any
interruption with:

```
gh run list --branch main --limit 5
gh run view <run-id>                       # status, per-job summary
gh run view <run-id> --job=<job-id>        # per-step status for one job
gh run view <run-id> --job=<job-id> --log  # full step log, for exact
                                            # counts/durations/failures
```

**Never re-push to "restart" a CI run** that is merely slow or whose local
watcher died -- `gh run view` always has the authoritative current status,
and GitHub Actions keeps the run and its full log regardless of local
session state. Re-pushing wastes another full release-gate run (up to
~2 hours) and, if the first run is still in progress, can race it.

## 9. Top-level book pages: prose-only fast gate (WP56)

The same "diff the actual published artifact, not the commit message"
policy section 3 describes for exercise notebooks now also applies to four
top-level book hub pages: `book/intro.md`, `book/contents.md`,
`book/resources.md`, and `book/references.md`. A change confined to one or
more of these pages (nothing shared, no exercise, no other page with a
structural change) gets the `prose` gate if every touched page's content
differs from the last published version **only in prose wording** --
exactly the same gate, and the same checks, a prose-only exercise edit
gets (section 3's table).

**`book/syllabus.md` is not one of these pages -- it was removed in WP56.**
The Syllabus page, its nav entry, and student-facing links to it are gone;
the published top-level pages are now Introduction, Contents, Resources,
and References only (`book/_toc.yml`). This is itself exactly the kind of
change the next paragraph describes as forcing the full gate (navigation
changed, a page was deleted) -- it is not, and must never become, a
prose-fast-pathable page itself.

**What counts as "prose" for a page, precisely** (implemented in
`scripts/classify_release_change.py`'s `page_differs_beyond_prose()`,
mirroring `notebooks_differ_beyond_prose()`'s shape for notebooks): every
one of the following must be **byte-identical** between the base and head
versions of the page, in order -- only the plain prose text around and
between them may differ:

- **Navigation.** Not checked at the page level at all -- any change to
  `book/_toc.yml` itself is a pre-existing shared-path pattern that already
  forces `full` regardless of what else changed (section 3's table).
- **Headings (and therefore anchors).** Every `#`..`######` line's full
  text must match. MyST/Sphinx derives a page's anchor slugs from heading
  text, so a reworded heading is a broken-anchor risk, not a wording change.
- **Link and image destinations.** Every markdown `[text](dest)` /
  `![alt](dest)`'s `dest` must match -- the visible link text/alt itself is
  prose and may change freely, only the destination may not.
- **Raw HTML markup.** Every HTML tag span (`<a href="...">`, `<img
  src="...">`, `<code>`, `</a>`, etc. -- `book/resources.md`'s data-file
  links use this, not markdown links) must match as an exact, ordered
  sequence; only the prose text between tags may differ.
- **Fenced code blocks and MyST directives.** Every ` ```...``` ` fenced
  block (a code sample, or a directive like `` ```{tableofcontents} ``)
  must match whole, fence lines included -- this book's pages use the same
  triple-backtick fence for both, so one check covers both.
- **Configuration/frontmatter.** A leading YAML frontmatter block (not
  currently used by any of the four pages, but checked regardless) must
  match whole, or be absent in both.
- **Page existence.** The page must exist, and be readable, at both base
  and head -- an added, deleted, or renamed-away-from-a-recognized-name
  page is a path-existence change, not a content diff, and escalates on
  its own (`page_is_prose_only()`'s own missing/unreadable check), before
  any text comparison runs at all.

Any other difference -- including a single changed character inside a
link's URL, or reflowing a paragraph across a changed heading -- escalates
that page, and **a non-prose page always wins straight to the full gate**,
the same way a shared/unknown path does: it never merely narrows to the
`exercise` gate, even alongside an otherwise-prose-only exercise change
pushed in the same commit (`classify()` checks touched pages before touched
exercises for exactly this reason).

**What the prose/exercise gate verifies for a touched page, after the
build:** `scripts/smoke_release_routes.py --pages <name>[,<name>...]`
(wired into `scripts/run_selected_checks.py --phase postbuild` alongside
the existing per-exercise route check) confirms the page's own route
(`<name>.html`) was actually published and is non-empty, then re-extracts
every same-repository link/image destination from the page's *source*
markdown and confirms each one resolves to something that exists in the
built site (another top-level page resolves to its own built `.html`;
anything else resolves to that same relative path under `--build-dir`,
e.g. `book/resources.md`'s links into `lite/files/data/`). External
(`http(s)://`, `mailto:`) destinations are never fetched -- this is an
offline smoke check, not a link-rot crawler. The full site build itself
(`jupyter-book build book`) is unconditional for every gate already (only
the *additional* full-gate-only suites are skipped), so "the fast gate
builds the site" was never gate-dependent to begin with -- what's new here
is only the targeted post-build check of the touched page(s) and their
links.
