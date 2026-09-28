# WP43R exact changelog

One commit, pushed once to `origin/main`.

## Commit `89c9bcc` — WP43R Gate A/B: pin ipywidgets in requirements.txt for clean CI

Files:
- `requirements.txt` (modified)
- `WPs/WP43R_CI_DEPENDENCY_AND_DEPLOY_RECOVERY.md` (added — this WP's own
  instruction file, per the repository's established pattern)

### `requirements.txt` diff

```diff
 jupyter-book==1.0.4.post1
 sphinxcontrib-mermaid==2.1.1
 jupyterlab
 ipykernel
+ipywidgets==8.1.9
 numpy
 pandas
 matplotlib
 seaborn
 scikit-learn
```

One line added. `requirements-lite.txt` (the JupyterLite build-tooling
file) and every notebook generator, test, and data asset are unchanged.

## Net result

`requirements.txt`: 1 file changed, 1 insertion(+).

## Not changed by this WP

No notebook content, generator, test, workflow YAML, or data file was
modified. `.github/workflows/deploy.yml` is byte-for-byte what WP43 left
it — this WP's entire code change is the one dependency pin above.

## What was pushed to `origin/main`

Commit `89c9bcc`, plus the previously-unpushed WP43 report commit
(`e76c690`, carried forward automatically since it was already the parent
of this commit) and the full WP41/41R/42/43 history already on `main`.
Pushed once: `7d0f9d3..89c9bcc main -> main`. No force-push; no
archive/checkpoint branch was pushed (the two checkpoint refs created in
Gate A are local only: `refs/checkpoints/wp43r-pre-work-main`,
`refs/checkpoints/wp43r-production-pre-fix`).

## Triggered workflow

Run
[`36414417778`](https://github.com/yoavmp/ml-neuro-tutorials/actions/runs/36414417778),
head SHA `89c9bccab37c1ab295f16ef55251d4c90a04a0cf`, conclusion
**failure**, 29m2s. Failed at "End-to-end test the combined book +
JupyterLite build" (148/149 Playwright tests passed; 1 timeout in
`exercise-02-lite.spec.ts:110`, unrelated content, not modified by this
WP). The dependency fix itself is proven: "Unit-test the Python scripts
(offline)", "Build Jupyter Book", and "Build JupyterLite (Exercises 1 and
2)" all passed on this run, none of which passed on WP43's run
(`36410198395`). See `WPs/reports/WP43R_REPORT.md` for full detail.

`gh-pages` is unchanged (`f6ddfc28e5102d44f94dc5dc86ba9875ad36db8a`) — the
publish step never ran. No second push or workflow rerun was made in this
WP.

This report and `WPs/reports/WP43R_REPORT.md` are committed on local `main`
after the push above but are **not** pushed in this WP, to avoid
triggering a third deploy run.
