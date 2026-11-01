# WP61R — Exercise 11 author-requested revisions (local only, continues WP61)

## Goal and boundary

Revise the Exercise 11 notebook WP61 built, per the author's direct review
of the local build. Continue on `feature/wp61-embeddings-and-rsa` (no new
branch). **Do not merge, push, publish, or deploy.** Edit
`scripts/generate_exercise_11_notebook.py` and regenerate its student,
portable, and reference notebooks; keep the three synchronized by
construction. Also correct the Haxby data manifest's license field (CC BY-SA
3.0, not "unknown" -- verified against pymvpa.org's own license statement),
and add a genuinely working, locally-verified link to the manifest from the
notebook and from `book/resources.md`, plus the Haxby citation to
`book/references.md`/`book/resources.md`.

## Author corrections (verbatim list, numbered as given)

1. Overview: "run x category x voxel response patterns" (drop
   "ventral-temporal-").
2. Section 1: remove the circularity sentence; keep a concise VT mask
   description.
3. Section 1: replace the raw-scan paragraph with concise wording + a short,
   accurate averaging description + a direct link to the manifest (no
   "find it in JupyterLite's data folder" explanation -- superseded by the
   correction below).
4. Manifest accessibility: a direct clickable link to
   `haxby_rsa_patterns.manifest.json` in the notebook **and** on the
   Resources page (not a folder-navigation explanation); add the Haxby
   source + manifest to Resources/References; verify both links against a
   local build; do not describe either as already public.
5. Heatmap intro: "Supplied:" to "Here we can see ...", shortened.
6. Thin black boundary lines between the heatmap's 8 category rows.
7. "# Example shape only (not a real result):" to "# Example format (not a
   real result):" everywhere in this notebook.
8. Move `show_question("q-row-voxel")` to right after the run-0 heatmap,
   before `CATEGORY_PATTERNS` is introduced.
9. Fix the MDS `n_init` FutureWarning with an explicit `n_init=4` on every
   `MDS(...)` call in this notebook (including the distance-measure
   activity) -- not a global warning suppression.
10. Given MDS scatter cell: treat an all-zero `neural_rdm` as unfinished
    (print "Not complete yet" instead of plotting a degenerate scatter).
11. MDS reflection: remove the "prompt for the written-answer cell below"
    sentence.
12. Remove the entire Split-Half Reliability section (code, blank, check,
    question) and `show_question("q-condition-order")`; delete both
    questions' `_QUESTIONS` entries; renumber sections/cell ids; update the
    overview, closing summary, and every dependent reference; keep a short
    category-order note if useful.
13. Trim other long student-facing passages, preserving the meaning of RDM,
    MDS, both hypothesis comparisons, and the one-participant/descriptive
    limits discussion.
14. Remove the final "hidden question keys are not secure" paragraph;
    search every other current generator for the same/substantially similar
    **student-facing** text (not the maintainer-only Python comment variant
    in Exercises 1-3/5-7) and remove it wherever found; regenerate only the
    affected notebooks; change nothing else in them.
15. Confirm the grouping and distance-measure widgets keep working, the
    distance-measure activity is warning-free, and both its dropdown
    options redraw both plots.

## Verification (focused, per the task's instruction)

Generator `--check` + checksum/structural tests for Exercise 11 (and for
any other notebook touched by item 14's search); one combined local
Jupyter Book + JupyterLite build; Exercise 11's own Playwright suite
re-run against it, confirming no MDS FutureWarning anywhere and both
widgets still redraw correctly. Do not run Exercises 1-10/12's browser
suites unless item 14 touches their content, in which case run only that
exercise's own focused structural/content check, not its browser suite.
Monitor any long-running command (builds, Playwright) autonomously and
report its actual final result.

## Handoff

Report: local preview URL, a concise change report keyed to the numbered
list above, the corrected license text and how it was verified, the exact
manifest-link path verified against the local build, and any unresolved
issue. Commit on the same branch with a clean working tree. Stop before
merge or deployment.
