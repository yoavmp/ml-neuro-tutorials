# Introduction

These are the practice-session materials for **Machine Learning for
Neuroscience**. Each practice notebook follows a short PowerPoint presentation,
which is available on Moodle; the notebook is where those ideas are put to work
on real data.

## Using the notebooks

Each notebook is a single interactive document: supplied code you can run as
is, **YOUR CODE HERE** sections you complete yourself, notebook-native
interactive activities (figures and controls that update live as you change
them), and checked understanding questions -- including some that ask you to
select more than one correct option -- that give you feedback once you
answer. Work through each notebook from top to bottom, together during the
in-class practice session or on your own at home at your own pace.

**Open the exercise directly in this site's notebook platform** -- nothing to
install, it runs in your browser. Your edits (code, written answers, and
question results) are saved automatically in that browser as you work, and a
**Download my notebook** button in the notebook's own toolbar saves your
current work, edits included, as an `.ipynb` file at any time. That saved
browser copy lives only in that browser: it will not follow you to a
different browser, device, or a cleared browser profile, so download it if
you want a copy that does.

If you would rather work outside the browser, download the notebook and open
it in [Google Colab](https://colab.research.google.com/) (**File > Upload
notebook**), or in a local Jupyter installation.

### Opening an old downloaded copy later

If you previously downloaded an edited `.ipynb` and open it again later
(locally, or re-uploaded to Colab), it still holds exactly the edits you made
at the time you downloaded it -- a downloaded file never updates itself. If
you instead want the exercise open **in your browser** to go back to the
original, current template, **download your edited copy first** if you want
to keep it, then use that notebook's own **Reset from course template**
button. This discards your in-browser edits for that one notebook and
replaces them with the latest published template; it does not touch any
`.ipynb` file you already downloaded, and it only resets the notebook you run
it in.

### Working locally (optional)

Local Jupyter or VS Code's own notebook support both work with every
exercise. **Python 3.11** is the tested and recommended version; install it
together with `numpy`, `pandas`, `matplotlib`, `scikit-learn`, and
`ipywidgets`, plus JupyterLab (or VS Code's Jupyter extension) and
`ipykernel` to run notebooks locally, for example:

```bash
pip install numpy pandas matplotlib scikit-learn ipywidgets jupyterlab
```

Retrieving a notebook's dataset the first time may require an internet
connection. This site's own in-browser notebooks run their own bundled
Python (Pyodide), not a locally installed one, and Google Colab's runtime
Python version is set by Colab itself -- neither is guaranteed to be exactly
3.11.
