# Resources

A practical link directory for material actually used in Exercises 1-9 --
not a general collection. For citable works, see [References](references.md).

## Course text

- [An Introduction to Statistical Learning: with Applications in Python](https://hastie.su.domains/ISLP/ISLP_website.pdf.download.html) --
  the official, freely available PDF edition used throughout this course.
- [statlearning.com](https://www.statlearning.com/) -- the book's official
  hub (editions, data, and code for both the R and Python versions).

## Datasets and data provenance

- [ABIDE II](https://fcon_1000.projects.nitrc.org/indi/abide/abide_II.html) --
  the official Autism Brain Imaging Data Exchange II site. Exercises 1-9
  all work with ABIDE II phenotypic and derived cortical-thickness data.
- [ABIDE II Phenotypic Data Legend](https://fcon_1000.projects.nitrc.org/indi/abide/ABIDEII_Data_Legend.pdf) --
  the official column/field definitions for the ABIDE II phenotypic tables.
- [NeuroHackademy `abide2.tsv`](https://raw.githubusercontent.com/neurohackademy/nh2020-curriculum/e4eed3c4daa7f40b0ba931182a8c7e5e691dba6b/tu-machine-learning-yarkoni/data/abide2.tsv) --
  the pinned, checksummed public copy every exercise's data loader falls
  back to when this site's own same-origin file isn't available (a bare
  downloaded `.ipynb`, or Colab).
- This course's own <a href="lite/files/data/abide_age_brain.csv"><code>abide_age_brain.csv</code></a>,
  <a href="lite/files/data/abide_age_brain_demographics.csv"><code>abide_age_brain_demographics.csv</code></a>,
  and <a href="lite/files/data/abide_phenotypes.csv"><code>abide_phenotypes.csv</code></a> --
  curated exports selected to the columns each exercise actually uses, built
  from the ABIDE II source above. These are this course's own derived
  files, not the original ABIDE II release.

## Python and Jupyter documentation

- [NumPy documentation](https://numpy.org/doc/stable/)
- [pandas documentation](https://pandas.pydata.org/docs/)
- [Matplotlib documentation](https://matplotlib.org/stable/)
- [scikit-learn documentation](https://scikit-learn.org/stable/) -- the
  modeling library used throughout Exercises 1-9.
- [ipywidgets documentation](https://ipywidgets.readthedocs.io/) -- powers
  every notebook-native interactive activity in this course.
- [JupyterLite documentation](https://jupyterlite.readthedocs.io/) -- the
  in-browser notebook platform this site's exercises run on.
- [Google Colab](https://colab.research.google.com/) -- an alternative way
  to run a downloaded exercise notebook outside the browser platform above.
