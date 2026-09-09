# Interactive-widget work-package protocol

WP01 has been reviewed by ChatGPT. Only this work package is now authorized:

1. `WP02_WIDGET_RUNTIME.md`

Do not create or begin WP03. After WP02, generate `reports/WP02_REPORT.md`, commit it, and stop. Yoav will return the report to ChatGPT; ChatGPT will review it and issue WP03.

WP02 uses these commits:

```text
checkpoint: before WP02
WP02: add and verify reusable widget runtime
WP02 report: document results
```

Continue following `CLAUDE_INTERACTIVE_WIDGETS.md`, including the mandatory checkpoint/tag, safety rules, and separate report commit.

## Required report format

Create `WPs/reports/WP02_REPORT.md`:

```markdown
# WP02 implementation report

## Outcome
Status: SUCCESS | PARTIAL SUCCESS | FAILURE

One-paragraph outcome summary.

## Git safety checkpoint
- Branch:
- Starting HEAD:
- Checkpoint commit:
- Checkpoint tag:
- Retraction guidance: identify the checkpoint only; do not execute a reset/revert.

## Work completed
- Requirement-by-requirement account.

## Files changed
- Every changed path and its purpose.

## Runtime design
- Component registry:
- Config/data validation:
- URL and same-origin handling:
- Plotly bundling:
- Static output path:

## Tests and verification
| Command/test | Result | Evidence or relevant output |
|---|---|---|

## Acceptance criteria
| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|

## Deviations from instructions
- Every deviation and why it was necessary.
- Write `None` only if there were no deviations.

## Problems and unresolved risks
- Failures, warnings, browser limitations, dependency concerns, or uncertainty.
- Write `None` only if genuinely none remain.

## Git commits created
- Checkpoint commit and tag.
- Implementation commit.
- The report commit is printed in the terminal summary because the report cannot contain its own future hash.

## Recommended scope for WP03
- Recommendations only. Do not create or begin WP03.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP02.
```

Never describe an untested behavior as working. Record a failing command with a concise relevant error excerpt.

