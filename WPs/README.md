# Interactive-widget work-package protocol

Only this work package is currently authorized:

1. `WP01_AUDIT_AND_BASELINE.md`

Do not create or begin WP02. After WP01, generate `reports/WP01_REPORT.md`, commit it, and stop. Yoav will return the report to ChatGPT. ChatGPT will review the evidence and only then issue WP02.

WP01 uses these commits:

```text
checkpoint: before WP01
WP01: audit interactive notebook baseline
WP01 report: document results
```

## Required report format

Create `WPs/reports/WPXX_REPORT.md` at the end of every WP:

```markdown
# WPXX implementation report

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
- Failures, warnings, browser limitations, data concerns, or uncertainty.
- Write `None` only if genuinely none remain.

## Git commits created
- Checkpoint commit and tag.
- Implementation commit.
- The report commit is printed in the terminal summary because the report cannot contain its own future hash.

## Recommended scope for the next WP
- Recommendations only. Do not create or begin the next WP.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WPXX.
```

Record blockers precisely, including the failing command and a concise error excerpt. Never describe an untested behavior as working.

