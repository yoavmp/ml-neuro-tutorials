# WP61 — Exercise 11: Embeddings and Representational Similarity Analysis (local review only)

## Goal and boundary

Build the first real content for Exercise 11 ("Embeddings and Representational
Similarity Analysis"), currently a placeholder stub
(`book/chapters/chapter_11/exercise_11.md`, `migrationState: "legacy"` in
`book/config/exercise_manifest.json`). Build it locally, in the same
JupyterLite-native, generator-authored style as Exercises 1–9 and 12. **Do not
merge, push, publish, deploy, run production CI, or change the live site in
this WP.** Do not touch Exercises 1–10, 12, or any shared infrastructure except
where a genuinely shared file must change. Do not flip Exercise 11's manifest
entry to `migrated`, add it to `book/_toc.yml`/`book/_config.yml`'s build set,
or wire a launch button on the chapter page — that is a later, explicitly
authorized release WP (the WP51→WP52, WP57→WP57 release, WP58→WP59 pattern).
The JupyterLite route itself is still built and tested locally by placing the
template under `book/lite/files/` and navigating to it directly, exactly as
WP51/WP57/WP58 did before their own release WPs.

Start by reading `NOTEBOOK_AUTHORING_STANDARDS.md`, `WPs/WP51_ACTIVE_EXERCISE_09_LOCAL.md`,
`WPs/reports/WP51_REPORT.md`, and `scripts/generate_exercise_09_notebook.py` in
full before writing a line of code. The repo is authoritative for filenames,
generator conventions, manifest state, and local build commands.

Create a starting git checkpoint and work on `feature/wp61-embeddings-and-rsa`.

## Gate A — real Haxby data, prepared offline

This exercise is the first in the course to use real fMRI data and the first
to use `nilearn`/`nibabel`. Neither belongs in the student's browser kernel
(no Pyodide wheels for a C-extension-heavy neuroimaging stack); they are
maintainer-only, network-mode tools for an offline export script, exactly
mirroring the UCI-HAR/ABIDE precedent (`scripts/export_uci_har_data.py`,
`scripts/export_abide_lite_data.py`).

1. Inspect the original Haxby et al. (2001) visual-object fMRI dataset as
   nilearn distributes it: condition/run (`chunks`) labels, the ventral-
   temporal (VT) mask, the data's terms of reuse, and the paper itself. Use
   subject 2 — `nilearn.datasets.fetch_haxby`'s own documented default
   (`subjects=(2,)`) — as the preselected main example. Do not try other
   subjects looking for a stronger RSA result.
2. Write `scripts/export_haxby_rsa_data.py` (`--write`/`--refresh` network
   mode; offline `--check` mode, following the UCI-HAR script's split).
   Derive one ventral-temporal voxel-response pattern per stimulus category
   per run, with a method that is explicit about block timing and
   hemodynamic lag (state the TR, block length, and any discarded onset
   TRs; do not silently average whole blocks if the plateau-only approach is
   used). Use the broad VT mask (`mask_vt`) — never a face/house-selective
   mask — since the comparisons in Section 5 must not be circular. Document
   every choice (preprocessing, exclusions, dimensions, checks performed,
   source URL/version, file checksum) in the script's docstring and in a
   JSON sidecar next to the derived file, following the UCI-HAR
   `provenance.json` shape.
3. Verify every retained run has all required categories present, and that
   an odd-run subset and an even-run subset are each complete enough to
   build a full RDM. Treat the result as **category-level patterns** — do
   not imply that per-picture responses or original presentation order
   survive this averaging.
4. Export a small prepared file to `book/lite/files/data/` (run × category ×
   voxel patterns) plus its manifest sidecar (sha256, dimensions,
   attribution, and the dataset's actual license). The student notebook
   must load this small export, never fetch or process the ~300 MB raw
   functional file. Make the same export reachable from a downloaded/Colab
   notebook via the same relative-path convention Exercises 1–9/12 already
   use, verified from the real JupyterLite kernel's actual working
   directory (see WP60's cwd finding — `data/...` only resolves correctly
   when the notebook sits flat in `book/lite/files/`, not in a subdirectory).
5. Report the real measured RDM, split-half reliability, and
   hypothesis-match numbers — including if any of them come out weak or
   unexpected. Do not adjust the method post hoc to produce a cleaner
   result.

## Student notebook sections

Follow `generate_exercise_09_notebook.py`'s exact shape: hidden setup cell
(`source_hidden`), `show_question()` hidden-key/shuffled-order pattern,
`Blank`-tagged student tasks with a hint comment and an explicitly-labeled
"example shape only" comment (never a working solution, commented out), two
native `ipywidgets`/Matplotlib activities with heavy work precomputed so a
dropdown/toggle redraws instantly, and the standard opening
(title → "What this notebook covers" numbered list → Prerequisites).

1. **Load the data.** Given, mostly visible, code loads run × category × VT-
   voxel patterns from the same-origin export (with the established
   Colab/offline URL fallback). Explain what each array dimension means. A
   small heatmap of a handful of raw response patterns (e.g. one run) shows
   students what a "pattern" actually looks like before any distance math.
2. **Build the neural RDM.** Students compute pairwise correlation distance
   between every pair of category patterns (averaged appropriately across
   runs — state exactly which averaging happens, and when) and assemble a
   square representational dissimilarity matrix. Supply a graceful checker:
   condition-label order matches a fixed reference list, shape is square,
   the matrix is symmetric within tolerance, every entry is finite, and the
   diagonal is (near) zero.
3. **2-D MDS embedding.** Students project the neural RDM into 2-D with
   `sklearn.manifold.MDS` and label each category's point. State plainly
   that the plot's axes are arbitrary and that displayed distances only
   approximate the RDM's real geometry (MDS does not preserve it exactly in
   2 dimensions).
4. **Split-half reliability.** Students build two RDMs — odd runs and even
   runs — and compare them (e.g. a correlation between their upper
   triangles) as a stability check on the whole method.
5. **Model comparison.** Compare the neural RDM against two predeclared
   category-hypothesis RDMs: faces vs. all other meaningful categories, and
   animate vs. inanimate. State the conceptual reason scrambled pictures are
   excluded from the animacy comparison (they have no animacy) before
   reporting either model's score. Students build one hypothesis RDM
   themselves and compare its upper triangle against the neural RDM's;
   supply the other hypothesis RDM worked out as a given example.
6. **Interpretation and limits.** Report RDM correlations descriptively.
   Explicitly flag that category pairs inside one RDM are not independent
   observations, so a naive p-value on this correlation is not presented or
   implied to be valid.

## Native interactive activities

- **(A) Distance-metric explorer.** A toggle between correlation distance
  and Euclidean distance recomputes the RDM and the 2-D embedding and
  redraws both (heatmap + scatter). Precompute both variants up front so the
  toggle only switches which precomputed render is shown.
- **(B) Category-grouping explorer.** Students assign the (non-scrambled)
  categories into two groups and see the resulting 2-group hypothesis RDM
  and its descriptive match to the real neural RDM. Label this activity
  explicitly as exploration: optimizing a grouping against the same brain
  data it is then scored against is not an independent test, and the
  notebook must say so plainly, once, near this activity.

## Checked questions and blanks

About six `show_question()`-style checked questions (single/multi-choice,
hidden key, fixed-but-per-question shuffle seed) covering: what a row/column
(a voxel) of the loaded data represents, what one RDM cell means, why
condition-label order must be checked before comparing RDMs, what is lost
(and what survives) when a high-dimensional RDM is shown in a 2-D MDS plot,
what split-half reliability is actually checking, and what a strong match to
the face-hypothesis RDM does and does not establish about face-selective
processing. Three or four real coding blanks (RDM construction, the
hypothesis-RDM upper-triangle comparison, and one more drawn from the
sections above) with directional hints only.

Keep a teacher-filled reference notebook (`scripts/reference_notebooks/exercise_11_reference.ipynb`,
generated the same way exercise_09's is) separate from the student export;
never commit teacher answers into the student-facing file.

## Focused verification and handoff

- Follow the change-aware testing policy: test Exercise 11's own generator
  `--check`, structural/reference-execution tests, data-export checksum/
  dimension test, both activities' logic, and its lite route. **Do not run
  Exercises 1–10/12's execution or browser suites** unless a shared file
  genuinely changes, and say so if it does.
- Build the combined Jupyter Book + JupyterLite site locally once and test
  Exercise 11's actual lite route in a real browser directly by URL (not via
  a manifest-driven launch button, since the manifest stays untouched this
  WP): kernel start, data load, both activities' controls, every checked
  question's correct/incorrect feedback, a blank student edit/save/reload
  round-trip, and the downloaded `.ipynb`.
- Execute the private teacher-completed copy locally (offline, like the
  other exercises' reference-execution tests) to confirm it runs end to end
  with no errors. Mark real Google Colab verification as unverified unless
  it is actually performed in this WP — do not claim it.
- Record the prepared export's size, checksum, and provenance; the actual
  measured RDM/reliability/model-match numbers; local preview URL(s);
  timing for every command that ran more than five minutes; every
  deviation from this spec; and a full account in
  `WPs/reports/WP61_REPORT.md` plus `WPs/reports/WP61_EXACT_CHANGELOG.md`.
- Commit the branch with a clean working tree and give its SHA. Stop for
  the author's review: no merge, push, deployment, or next WP.
