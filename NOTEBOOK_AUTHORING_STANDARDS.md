# Notebook authoring standards

Internal contributor reference, established by WP20. Every future WP that creates or edits a
course notebook, interactive activity, or portable-notebook export must read this file first and
follow it. This file is **not** student-facing — do not add it to the Jupyter Book table of
contents (`book/_toc.yml`).

## 1. Audience and voice

- Write directly for students who may be completing the notebook alone at home, with no
  instructor present to interpret the text.
- Prefer "we will…", "you can…", and direct explanatory sentences.
- No author/developer notes, implementation history, internal script/report/WP references, or
  tutor-only instructions in anything a student can see (markdown, code comments, interactive
  strings, figure text).
- Explain a technical term when it first appears; use the correct term consistently afterward.
  Do not delete a necessary technical term merely because it is unfamiliar.
- Tone: professional, encouraging, precise — not chatty or "vibe tutoring."

## 2. Repeated data loading

- The first genuine data-loading example in the course (currently Exercise 1) stays visible —
  it is the lesson.
- In every later notebook, a code cell that only repeats already-taught imports/loading/
  column-selection logistics carries the `hide-input` cell tag (input collapses behind a
  "Show code cell source" toggle; output stays visible below by default). Verify this against a
  rendered build — do not guess a tag spelling from memory.
- Never use `hide-cell` for a loading cell that produces useful output (table preview,
  dimensions, class counts): `hide-cell` collapses the output too, which fails this rule.
- Never use `remove-input`/`remove-cell` for loading code — the code must stay reachable by a
  reader on the website, not just in the portable notebook.
- Do not collapse code that teaches scaling, fitting, prediction, metrics, plotting, or
  missing-data handling — only pure repeated logistics.
- Portable/Colab notebooks always keep full, runnable loading code, regardless of the website
  presentation.

## 3. Notebook opening

Every notebook begins, in this order:

```markdown
# Exercise X: [subject]

[Run/download admonition block]

## What this notebook covers

This is Exercise X of the Machine Learning for Neuroscience practice series. [One short
sentence on the practice focus, if needed.]

In this notebook, you will:

1. [Simple action matching Section 1]
2. [Simple action matching Section 2]
...
```

- The main title cell contains **only** the title — no descriptive paragraph loose beneath it.
- The identifying "This is Exercise X…" sentence lives under **What this notebook covers**,
  never directly under the title, and stays to one or two short sentences.
- The list is **numbered** (not bulleted) and its count/order matches the notebook's numbered
  `## N.` section headings exactly — one list item per main section, no more.
- Do not add a separate "Learning objectives" section unless explicitly requested.
- Remove overview prose duplicated elsewhere in the opening.

## 4. Clear headings and introductory language

- Headings must tell a beginner what the section does before they've read it. Prefer "Our data
  table" over "The modelling table"; "Testing the model on new participants" over "Honest
  evaluation" — unless the technical term is itself the lesson and is defined immediately
  (e.g. "Confusion matrix", "Bias–variance trade-off").
- A fixed worked-example setting (a chosen `k`, `C`, seed, etc.) is introduced as "the value used
  in this example" — never as "predeclared", "selected", "optimal", or "fixed by course design".
- Introductory list items use short verbs: load, inspect, predict, compare, test, interpret.
  Avoid exact sample/feature counts and implementation detail in the opening unless the number
  is the lesson.

## 5. Interactives and self-learning

- Every control states what quantity it changes.
- Every figure identifies what is plotted and defines unfamiliar lines/markers.
- Prompts are answerable from the notebook alone — never assume spoken tutor guidance.
- Interactive exploration in Exercises 1–4 is never described as formal model/feature
  selection.
- Empty/error states tell the student what to change or check, in plain language.
- Internal engineering vocabulary (catalog, artifact, payload, manifest, audit, canonical,
  schema, render count, test fixture, "implementation detail, not the lesson") must not reach a
  student-visible string — config `title`/`instructions`/notes, component-rendered text, error
  messages.

## 6. Technical integrity

- Simplify language, never scientific meaning.
- Preserve train/test separation, model settings, target definitions, metrics, and data
  provenance unless a WP explicitly changes them.
- Do not describe exploratory comparisons as causal evidence or final model optimization.
- Regenerate portable notebooks and stored outputs after any canonical-notebook edit.

## 7. Concision and duplication (WP24)

- Prefer plain language over technical jargon when the jargon is not itself the
  lesson (e.g. "fill in missing values" rather than "impute") — introduce the
  technical term only where §1 above requires it.
- Never repeat the same warning, caution, or explanation both inside an
  interactive activity's own config text and in the surrounding notebook
  markdown. Keep exactly one occurrence, placed where the student needs it —
  usually after they have used the activity, not only inside it.
- Keep interactive instructions and control labels brief and action-oriented;
  cut a long caution to one sentence wherever the meaning survives.
- A website notebook may collapse a Python cell with the `hide-cell` tag when
  it only reproduces part of an interactive figure the student already used,
  with no unique result, worked example, or later-needed code. Never apply
  this to a first demonstration of a method, a unique result, or code later
  cells depend on.
- The portable/Colab notebook must keep such a reproduction cell's code and
  saved output fully visible and runnable regardless of the website's tag —
  confirm this on every regeneration, since the portable notebook has no
  interactive widget to point back to.
- Internal implementation notes (how a feature set, threshold, or fixed value
  was actually chosen; references to an audit script, WP, or report) must
  never reach student-facing material verbatim — describe the outcome and, if
  relevant, the general method in plain language instead.

## 8. Before you start a notebook-editing WP

1. Read this file.
2. Inspect the current cell-tag convention with a rendered build — don't assume.
3. Inventory the notebook's opening, headings, and any `hide-*`/`remove-*` tags before editing.
4. After editing, regenerate portable notebooks and rerun the focused structural tests plus one
   relevant build.
