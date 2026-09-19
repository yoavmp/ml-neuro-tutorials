# WP31R Exact Changelog

Diff scope, `WP31_RELEASE_SHA` (`3da7d3f8b1ad4fe627f9581d23ef7e267a2c47ed`) to
`WP31R_RELEASE_SHA` (`de564b3dccedfc92eb14f6460efd4ffb459d4c5e`):

```
 WPs/WP31R_CI_FLOAT_PORTABILITY_AND_REDEPLOY.md | 308 +++++++++++++++++++++++++
 WPs/reports/WP31_DEPLOYMENT_REPORT.md          | 273 ++++++++++++++++++++++
 WPs/reports/WP31_EXACT_CHANGELOG.md            | 102 ++++++++
 scripts/export_tree_greedy_widget.py           |   6 +-
 scripts/semantic_json_compare.py               |  96 ++++++++
 tests/test_export_tree_greedy_widget_data.py   |  15 +-
 tests/test_semantic_json_compare.py            | 141 +++++++++++
 7 files changed, 936 insertions(+), 5 deletions(-)
```

`WPs/reports/WP31_DEPLOYMENT_REPORT.md` and `WPs/reports/WP31_EXACT_CHANGELOG.md`
were already-committed local-only content from WP31 (its documentation commit,
`9991543`, one commit ahead of `origin/main` at the start of this WP); they were
merged unchanged. `WPs/WP31R_CI_FLOAT_PORTABILITY_AND_REDEPLOY.md` is this WP's
own specification, committed as its first checkpoint (`3d405be`) before any
implementation change.

## The narrow correction itself

Two files changed, one file added (plus its regression-test file, also added):

### `scripts/export_tree_greedy_widget.py` (+6/-5 net incl. new import)

```diff
@@ -56,6 +56,8 @@ from typing import Any
 REPO_ROOT = Path(__file__).resolve().parent.parent
 OUT_PATH = REPO_ROOT / "book" / "_static" / "widgets" / "data" / "tree_greedy_split.json"
 
+from semantic_json_compare import DEFAULT_ABS_TOL, semantic_diff  # noqa: E402
+
 # --- the fixed generating formula (decided before any seed was inspected) --
 N_OBSERVATIONS = 16
 MU1, SD1 = 5.5, 2.0
@@ -366,8 +368,10 @@ def cmd_check() -> int:
         return 1
     data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
     recomputed = build_data()
-    if json.dumps(data, sort_keys=True) != json.dumps(recomputed, sort_keys=True):
+    mismatch = semantic_diff(data, recomputed, abs_tol=DEFAULT_ABS_TOL)
+    if mismatch is not None:
         print("ERROR: committed artifact does not match a fresh recomputation.", file=sys.stderr)
+        print(f"  - {mismatch}", file=sys.stderr)
         return 1
     problems = validate(data)
     if problems:
```

No change to `build_data()`, `seed_diagnostics()`, `select_seed()`,
`validate()`, `_generate_raw()`, `_feature_candidates()`, `_round_summary()`, or
any generating-formula constant. The committed artifact
`book/_static/widgets/data/tree_greedy_split.json` was **not** regenerated or
otherwise touched.

### `tests/test_export_tree_greedy_widget_data.py` (+15/-8)

```diff
@@ -21,6 +21,12 @@ import unittest
 sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
 
 import export_tree_greedy_widget as tg  # noqa: E402
+from semantic_json_compare import (  # noqa: E402
+    DEFAULT_ABS_TOL,
+    SemanticMismatch,
+    assert_semantically_equal,
+    semantic_diff,
+)
 
 
 class CommittedArtifact(unittest.TestCase):
@@ -33,10 +39,11 @@ class CommittedArtifact(unittest.TestCase):
         self.assertEqual(problems, [], problems)
 
     def test_matches_a_fresh_recomputation(self):
-        self.assertEqual(
-            json.dumps(self.data, sort_keys=True),
-            json.dumps(tg.build_data(), sort_keys=True),
-        )
+        # Semantic, not byte-for-byte: cross-platform floating-point noise
+        # (macOS vs. Linux CI, WP31 run 35437984824) can differ in the
+        # final decimal digit of a computed float without the artifact's
+        # structure or content actually changing. See semantic_json_compare.
+        assert_semantically_equal(self.data, tg.build_data(), abs_tol=DEFAULT_ABS_TOL)
```

All 12 other tests in this file are byte-for-byte unchanged.

### `scripts/semantic_json_compare.py` (new, 96 lines)

New module. Exports `DEFAULT_ABS_TOL = 2e-6`, `SemanticMismatch` (exception with
`.path`, `.a`, `.b`, `.reason`), `semantic_diff(a, b, *, abs_tol, path="$")` (returns
the first mismatch or `None`), and `assert_semantically_equal(a, b, *, abs_tol)`
(raises `AssertionError` from `semantic_diff`'s result). Full contract: exact
dict-key sets; exact list length/order (element-wise recursion); exact Boolean
type+value; exact integer value; float leaves compared via
`math.isclose(rel_tol=0.0, abs_tol=abs_tol)`; any non-finite (`NaN`/`±inf`) value
on either side is rejected outright, even if both sides are non-finite and equal
to each other.

### `tests/test_semantic_json_compare.py` (new, 141 lines, 14 tests)

`SemanticDiffTests`: accepts a sub-tolerance float difference; rejects an
over-tolerance float difference; rejects a changed `selectedSeed`; rejects a
changed optimal feature; rejects a changed optimal threshold; rejects a missing
dictionary key; rejects an extra dictionary key; rejects reordered list elements;
rejects a changed list length; reports the exact nested JSON path of a mismatch
(`$.rounds[0].candidates.x1.reduction[2]`); rejects `NaN`/`inf`/`-inf` on one
side; rejects `NaN` even when both sides carry the identical `NaN`; rejects a
changed Boolean; rejects an int-vs-Boolean type mismatch; confirms two identical
nested structures match.

## Commits, in order

| Commit | Message | Files |
|---|---|---|
| `3d405be` | WP31R: add specification (initial checkpoint) | `WPs/WP31R_CI_FLOAT_PORTABILITY_AND_REDEPLOY.md` (new) |
| `60658ed` | Fix cross-platform greedy-tree artifact verification | `scripts/export_tree_greedy_widget.py`, `scripts/semantic_json_compare.py` (new), `tests/test_export_tree_greedy_widget_data.py`, `tests/test_semantic_json_compare.py` (new) |
| `de564b3` | Fix cross-platform greedy-tree artifact verification (merge, `--no-ff`) | merges `60658ed` into `main`; `WP31R_RELEASE_SHA` |

Pushed to `origin/main`: `3da7d3f..de564b3`. Triggered GitHub Actions run
`35469646309` (headSha `de564b3`): "Unit-test the Python scripts (offline)"
**passed**; "Build Jupyter Book" failed on an unrelated pre-existing
`sphinxcontrib.mermaid` CI dependency gap. See `WPs/reports/WP31R_REPORT.md` §8
for the full failure log and stop-condition rationale. No further push or fix was
made within WP31R.
