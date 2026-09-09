# Interactive-widget work-package protocol

WP02 has been reviewed by ChatGPT. Only this work package is now authorized:

1. `WP03_ABIDE_HISTOGRAM.md`

Do not create or begin WP04. After WP03, generate `reports/WP03_REPORT.md`, commit it, and stop. Yoav will return the report to ChatGPT; ChatGPT will review it and issue WP04.

WP03 uses these commits:

```text
checkpoint: before WP03
WP03: add production ABIDE histogram activity
WP03 report: document results
```

Continue following `CLAUDE_INTERACTIVE_WIDGETS.md`, including the mandatory checkpoint/tag, safety rules, separate implementation/report commits, and prohibition on pushing.

## Required report format

Create `WPs/reports/WP03_REPORT.md` with these sections:

```markdown
# WP03 implementation report

## Outcome
Status: SUCCESS | PARTIAL SUCCESS | FAILURE

## Git safety checkpoint
- Branch:
- Starting HEAD:
- Checkpoint commit:
- Checkpoint tag:
- Retraction guidance:

## Work completed

## Files changed

## ABIDE data artifact
- Source URL and pinned source hash:
- Source rows/columns:
- Exported rows/variables:
- Exported fields:
- Missing-value representation:
- Identifier/privacy check:
- Artifact size and deterministic hash:

## Histogram behavior
- Variables/default:
- Bin range/default:
- Empty and constant-variable behavior:
- Student-facing text:

## Build and deployment integration

## Tests and verification
| Command/test | Result | Evidence or relevant output |
|---|---|---|

## Acceptance criteria
| Criterion | PASS/FAIL/NOT TESTED | Evidence |
|---|---|---|

## Deviations from instructions

## Problems and unresolved risks

## Git commits created

## Recommended scope for WP04
- Recommendations only. Do not create or begin WP04.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP03.
```

Every claim of interactive success must be supported by a browser test against the final built Chapter 1 HTML, not only the standalone widget page.

