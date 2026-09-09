# Notebook work-package protocol

WP05 has been reviewed by ChatGPT. Only this work package is now authorized:

1. `WP06_NOTEBOOK_EDITORIAL_AND_DESIGN.md`

Do not create or begin WP07. After WP06, generate both required reports, commit them, and stop. Yoav will return the main report to ChatGPT for review.

WP06 uses these commits:

```text
checkpoint: before WP06
WP06: polish EDA notebook content and design
WP06 report: document editorial and design changes
```

Continue following `CLAUDE_INTERACTIVE_WIDGETS.md`, including the mandatory checkpoint/tag, safety rules, separate implementation/report commits, and prohibition on pushing.

Required reports:

- `WPs/reports/WP06_REPORT.md` — outcome, design decisions, tests, deviations, risks, commits, and concise summary.
- `WPs/reports/WP06_EXACT_CHANGELOG.md` — an exact, location-specific record of every substantive correction and every cell visibility/type change.

Do not use vague report phrases such as “cleaned wording throughout.” The changelog must let Yoav identify precisely what changed without diffing notebook JSON.

