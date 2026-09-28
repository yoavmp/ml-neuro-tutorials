# WP43 exact changelog

Deployment-preparation branch `prep/wp43-deploy-jupyterlite-exercises`,
fast-forward-merged into local `main` and pushed once to `origin/main`
(`58ed1c6..7d0f9d3`). Two commits, one file of substance
(`.github/workflows/deploy.yml`) plus this WP's own spec/report files.

## Commit `b6a8ed0` — WP43 Gate B: wire JupyterLite build into the Pages deploy workflow

Files:
- `.github/workflows/deploy.yml` (modified)
- `WPs/WP43_DEPLOY_JUPYTERLITE_EXERCISES_1_AND_2.md` (added — this WP's own
  instruction file, per the repository's established pattern of committing
  the WP spec alongside its first substantive commit)

### `.github/workflows/deploy.yml` diff (as originally committed in `b6a8ed0`)

```diff
       - name: Install Python dependencies
-        run: pip install -r requirements.txt
+        run: pip install -r requirements.txt -r requirements-lite.txt

       - name: Set up Node
         uses: actions/setup-node@v4
         with:
           node-version: "22"
           cache: npm
           cache-dependency-path: interactive/package-lock.json

       - name: Install frontend dependencies
         working-directory: interactive
         run: npm ci

+      - name: Install and build the course-toolbar JupyterLite extension
+        working-directory: book/lite/extensions/course-toolbar
+        run: |
+          npm ci
+          npm run build
+
       - name: Type-check and unit-test the frontend
         working-directory: interactive
         run: |
           npm run typecheck
           npm run test:unit

       - name: Audit production frontend dependencies
         working-directory: interactive
         run: npm audit --omit=dev

       - name: Build the interactive widget app
         working-directory: interactive
         run: npm run build

       - name: Validate both committed ABIDE data artifacts (offline)
         run: python scripts/export_widget_data.py --check --artifact all

+      - name: Validate the JupyterLite exercise data exports (offline)
+        run: |
+          python scripts/export_abide_lite_data.py --check
+          python scripts/export_abide_phenotypes_lite_data.py --check
+
+      - name: Check the migrated exercise generators are not stale (offline)
+        run: |
+          python scripts/generate_exercise_01_notebook.py --check
+          python scripts/generate_exercise_02_notebook.py --check
+          python scripts/generate_exercise_01_transition_page.py --check
+          python scripts/generate_exercise_02_transition_page.py --check
+
       - name: Unit-test the Python scripts (offline)
         run: python -m unittest discover -s tests -v

       - name: Check the portable notebook is not stale (offline)
         run: python scripts/build_portable_notebook.py --check

       - name: Install Playwright Chromium
         working-directory: interactive
         run: npx playwright install --with-deps chromium

       - name: End-to-end test the standalone widget app
         working-directory: interactive
         run: npx playwright test

       - name: Build Jupyter Book
         run: jupyter-book build book

       - name: Fail on notebook execution errors
         run: |
           shopt -s globstar nullglob
           reports=(book/_build/**/*.err.log)
           if (( ${#reports[@]} )); then
             echo "::error::Notebook execution-error reports were produced:"
             for f in "${reports[@]}"; do
               echo "---- $f ----"
               cat "$f"
             done
             exit 1
           fi
           echo "No notebook execution-error reports found."

-      - name: End-to-end test the built Chapter 1 page
+      - name: Build JupyterLite (Exercises 1 and 2)
+        run: |
+          jupyter lite build \
+            --config book/lite/jupyter_lite_config.json \
+            --lite-dir book/lite \
+            --output-dir book/_build/html/lite
+
+      - name: End-to-end test the combined book + JupyterLite build
         working-directory: interactive
         run: npm run test:e2e:book

       - name: Execute the portable notebook outside the repository
         run: python scripts/smoke_portable_notebook.py

       - name: Publish website
         uses: peaceiris/actions-gh-pages@v4
         with:
           github_token: ${{ secrets.GITHUB_TOKEN }}
           publish_dir: ./book/_build/html
```

## Commit `7d0f9d3` — WP43 Gate C: fix course-toolbar build step (found live, not assumed)

Files:
- `.github/workflows/deploy.yml` (modified)

Found by actually running the Gate B recipe locally from a fresh
`book/_build/` (not assumed from reading the config): `npm ci` + `npm run
build` in `book/lite/extensions/course-toolbar` fails —
`npm run build` delegates to `jlpm run build:labextension:dev`, and
`jupyter labextension build`'s own bundled Yarn resolver expects a
Yarn-managed tree, not one `npm ci` just populated. Replaced with the exact
recipe the WP41 maintainer guide (section 6) already documents.

```diff
       - name: Install and build the course-toolbar JupyterLite extension
         working-directory: book/lite/extensions/course-toolbar
         run: |
           npm ci
-          npm run build
+          npx tsc
+          jupyter labextension build --development True .
```

## Net result

`.github/workflows/deploy.yml`: 1 file changed, 30 insertions(+), 2
deletions(-) relative to its pre-WP43 state (compares Gate B's and Gate C's
diffs together against the original file).

## Not changed by this WP

No notebook content, generator, test, or data file was modified. No
teaching content was migrated or redesigned. `requirements.txt` was **not**
modified — the `ipywidgets` gap that failed Gate D (see
`WPs/reports/WP43_REPORT.md`) is a pre-existing dependency-contract gap,
left as the concrete, reported blocker rather than patched, per the WP's
explicit Gate D instruction not to push a speculative fix after a failed
deployment run.

## What was pushed to `origin/main`

Both commits above, plus the full WP41/WP41R/WP42 feature history already
committed on `feature/wp42-exercise2-polish-exercise1-migration`
(unmodified by this WP — see `WPs/reports/WP41_EXACT_CHANGELOG.md` and
`WPs/reports/WP42_EXACT_CHANGELOG.md` for that content). Pushed once:
`58ed1c6..7d0f9d3 main -> main`. No force-push; no archive/checkpoint
branch was pushed (the three checkpoint refs created in Gate A are local
only: `refs/checkpoints/wp43-pre-work-main`,
`refs/checkpoints/wp43-pre-work-feature`,
`refs/checkpoints/wp43-production-pre-wp41`).

This report and `WPs/reports/WP43_REPORT.md` are committed on local `main`
after the push above but are **not** pushed in this WP, to avoid triggering
a second `Build and deploy Jupyter Book` run after Gate D's failure.
