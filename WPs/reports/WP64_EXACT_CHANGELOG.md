# WP64 — Exact changelog

## scripts/generate_exercise_07_notebook.py

Cell `wp46-104-load` (Section 1, the data-loading cell), inside the
existing `try: df = load_abide_age_brain_table() except NameError ...`
block, immediately after it:

**Before:**
```python
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score
```

**After:**
```python
try:
    from sklearn.model_selection import train_test_split, KFold, GridSearchCV
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.metrics import mean_squared_error, r2_score
except ModuleNotFoundError as exc:
    if sys.platform != "emscripten" or exc.name not in (
        "sklearn", "scipy", "joblib", "threadpoolctl",
    ):
        raise
    # In the browser, scikit-learn and its scipy/joblib/threadpoolctl
    # dependencies are fetched together the first time a cell imports
    # them, not at kernel startup -- see book/lite/overrides.json. A
    # one-off network hiccup fetching any one of the four leaves it (and
    # anything that imports it) unimportable even though it is correctly
    # part of this build, and surfaces here as a plain ModuleNotFoundError
    # naming whichever one didn't arrive. Retry the fetch once before
    # giving up.
    import micropip

    try:
        await micropip.install(["scikit-learn"])
        from sklearn.model_selection import train_test_split, KFold, GridSearchCV
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.metrics import mean_squared_error, r2_score
    except Exception as retry_exc:
        raise RuntimeError(
            "scikit-learn failed to load over the network, twice in a row. "
            "This is almost always a brief connectivity problem, not a "
            "missing package -- check your connection and run this cell "
            "again (Shift+Enter); your saved notebook is not affected."
        ) from retry_exc
```

`sys` is already imported by the notebook's setup cell (`wp46-000-setup`)
and shares the same kernel namespace; no new top-of-cell import was added.
Outside the browser (`sys.platform != "emscripten"`) this re-raises
immediately, so local-Jupyter/Colab behavior is unchanged byte-for-byte.

## Regenerated files (via `--write`, never hand-edited)

- `book/lite/files/exercise_07.ipynb`
- `book/lite/files/exercise_07_portable.ipynb`
- `book/downloads/chapter_07/exercise_07_portable.ipynb`
- `scripts/reference_notebooks/exercise_07_reference.ipynb`

No other file changed.
