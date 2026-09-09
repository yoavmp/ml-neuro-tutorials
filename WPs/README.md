# Interactive-widget work-package protocol

WP03 has been reviewed by ChatGPT. Only this work package is now authorized:

1. `WP04_MISSING_DATA_RETENTION.md`

Do not create or begin WP05. After WP04, generate `reports/WP04_REPORT.md`, commit it, and stop. Yoav will return the report to ChatGPT; ChatGPT will review it and issue WP05 if needed.

WP04 uses these commits:

```text
checkpoint: before WP04
WP04: add ABIDE missing-data retention activity
WP04 report: document results
```

Continue following `CLAUDE_INTERACTIVE_WIDGETS.md`, including the mandatory checkpoint/tag, safety rules, separate implementation/report commits, and prohibition on pushing.

## Required report format

Create `WPs/reports/WP04_REPORT.md` with these sections:

```markdown
# WP04 implementation report

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

## Retention data artifact
- Source URL/hash:
- Rows and fields:
- Site grouping treatment:
- Missing-value representation:
- Participant-identifier check:
- Artifact size/hash/determinism:

## Retention behavior
- Candidate/default variables:
- Complete-case rule:
- No-selection behavior:
- Overall and site outputs:
- Student-facing prompts:

## Legacy cleanup

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

## Recommended scope for WP05
- Recommendations only. Do not create or begin WP05.

## Instructions for reviewer
Paste this entire report into the ChatGPT conversation that produced WP04.
```

Every interactive claim must be supported by a browser test against the final built Chapter 1 HTML.

