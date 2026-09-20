# WP31R2 Exact Changelog

Diff scope, `WP31R_RELEASE_SHA` (`de564b3dccedfc92eb14f6460efd4ffb459d4c5e`)
to `WP31R2_RELEASE_SHA` (`f12967beaed9a4e16b4930e2881e28435478d388`):

```
 WPs/WP31R2_MERMAID_DEPENDENCY_AND_REDEPLOY.md | 318 ++++++++++++++++++++++++++
 WPs/reports/WP31R_EXACT_CHANGELOG.md          | 130 +++++++++++
 WPs/reports/WP31R_REPORT.md                   | 293 ++++++++++++++++++++++++
 requirements.txt                              |   1 +
 tests/test_deploy_dependency_contract.py      | 104 +++++++++
 5 files changed, 846 insertions(+)
```

`WPs/reports/WP31R_EXACT_CHANGELOG.md` and `WPs/reports/WP31R_REPORT.md` were
already-committed local-only content from WP31R (its documentation commit,
`7b17c5f`, one commit ahead of `origin/main` at the start of this WP); they
were merged unchanged. `WPs/WP31R2_MERMAID_DEPENDENCY_AND_REDEPLOY.md` is
this WP's own specification, committed as its first checkpoint (`1274242`)
before any implementation change.

## The narrow correction itself

### `requirements.txt` (+1 line)

```diff
@@ -1,4 +1,5 @@
 jupyter-book==1.0.4.post1
+sphinxcontrib-mermaid==2.1.1
 jupyterlab
 ipykernel
 numpy
```

Exact pin proven by the working local environment (`pip show
sphinxcontrib-mermaid` → `2.1.1`) and confirmed compatible with CI's Python
3.11 (`Requires-Python: >=3.10`). Placed next to `jupyter-book`'s own exact
pin to match the file's existing style. No other line changed; no other
package upgraded; no second `pip install` added to `.github/workflows/deploy.yml`.

### `tests/test_deploy_dependency_contract.py` (new, 104 lines)

New offline test module, `MermaidDependencyContract` (2 tests):

* `test_mermaid_extension_is_still_declared_and_mapped` — asserts
  `book/_config.yml`'s `sphinx.extra_extensions` still lists
  `sphinxcontrib.mermaid` and that it is present in the module's
  `EXTENSION_DISTRIBUTIONS` map.
* `test_every_enabled_extension_with_a_known_distribution_is_exactly_pinned`
  — parses `.github/workflows/deploy.yml`'s `pip install -r <file>` command
  to locate the canonical requirements file (not hardcoded), parses its
  `name==version` lines, and asserts every `extra_extensions` entry with a
  known distribution mapping is exactly pinned there. Failure message names
  both the missing Sphinx extension and the PyPI distribution it requires.

`EXTENSION_DISTRIBUTIONS = {"sphinxcontrib.mermaid": "sphinxcontrib-mermaid"}`
— a small explicit table, deliberately not a universal import-to-PyPI
resolver.

## Commits, in order

| Commit | Message | Files |
|---|---|---|
| `1274242` | WP31R2: add specification (initial checkpoint) | `WPs/WP31R2_MERMAID_DEPENDENCY_AND_REDEPLOY.md` (new) |
| `1187c01` | Pin Mermaid dependency for CI book builds | `requirements.txt`, `tests/test_deploy_dependency_contract.py` (new) |
| `f12967b` | Pin Mermaid dependency for CI book builds (merge, `--no-ff`) | merges `1187c01` into `main`; `WP31R2_RELEASE_SHA` |

Pushed to `origin/main`: `de564b3..f12967b`. Triggered GitHub Actions run
`35510061137` (headSha `f12967b`): "Build Jupyter Book" **passed**
(confirming this fix); "End-to-end test the built Chapter 1 page" failed on
one unrelated pre-existing flaky/timing-sensitive dark-mode test
(`e2e-book/chapter01-dark-mode.spec.ts:121`), 85/86 tests in that step
otherwise passing. See `WPs/reports/WP31R2_REPORT.md` §9 for the full
failure log and stop-condition rationale. No further push or fix was made
within WP31R2.
