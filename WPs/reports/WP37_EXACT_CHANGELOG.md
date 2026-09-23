# WP37 — Exact Changelog

WP37 is a deployment-only work package. It introduced **no notebook, widget, dataset, model,
test, configuration, dependency, or workflow content of its own**. Every such file that landed on
`main` via the `RELEASE_SHA` merge commit (`f792ad55f34342e627ed1fe3b85ff60777507d85`) originated
from the pre-existing, already-committed WP32 → WP33 → WP34 → WP35 → WP36 branch chain on
`fix/wp36-pcr-pls-alignment-scale` (tip `46efa0889e3b7b67a7e4b80f838000c5c21f12ac` at the start of
this WP). WP37 did not author, edit, or regenerate any of that content; it only validated it
(via `--check`-only and read-only commands), merged it with `--no-ff`, and pushed it.

## Files introduced by WP37 itself

| File | Nature |
|---|---|
| `WPs/WP37_DEPLOY_EXERCISES_7_TO_9.md` | This WP's specification, committed as the initial checkpoint (commit `d2d32551664c6c9794a2b4c205ff7bda01049f03`) before any release validation began. |
| `WPs/reports/WP37_DEPLOYMENT_REPORT.md` | This deployment's execution report, committed locally on `main` after the deployment attempt (not pushed). |
| `WPs/reports/WP37_EXACT_CHANGELOG.md` | This file, committed alongside the deployment report (not pushed). |

## Non-content operations WP37 performed

- One merge commit on `main`: `f792ad55f34342e627ed1fe3b85ff60777507d85`
  ("Merge Exercises 7-9 course materials"), combining `fix/wp36-pcr-pls-alignment-scale`
  (including the WP37 checkpoint) into `main` with `--no-ff`. This commit's tree is byte-identical
  to the WP37 checkpoint's tree — it introduces no content beyond what WP32–WP36 (plus the WP37
  checkpoint file above) already committed.
- One push of `main` to `origin/main`.
- One discovery query and one bounded (interrupted at 15 minutes) foreground watch of the resulting
  GitHub Actions run (`35881835065`); no code or configuration was touched by this monitoring.

## What was explicitly NOT done in WP37

- No notebook, widget component, dataset, audit script, test, portable-notebook, Jupyter Book
  config, dependency, or GitHub Actions workflow file was created, edited, or regenerated.
- No committed artifact (model results, widget data, PCR/PLS data, etc.) was recomputed or
  refreshed — all pre-deployment gates used `--check`/read-only modes only.
- No Syllabus or Word-course-overview change was introduced (confirmed absent from the
  `main..WP37_CHECKPOINT_SHA` diff prior to merge).
- No dependency file was installed, upgraded, or modified.
- No repair, rerun, retry, rebase, reset, or force-push occurred.
