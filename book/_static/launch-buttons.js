/*
 * WP12 -- per-page "Open in Colab" article-header button.
 *
 * Background
 * ----------
 * `book/_config.yml` deliberately does NOT enable sphinx-book-theme's built-in
 * `launch_buttons.colab_url` (see the comment there, WP07): that feature builds
 * one Colab URL per page from `repository.branch` + the CANONICAL Jupyter Book
 * source path (e.g. `book/chapters/chapter_02/exercise_02.ipynb`), which embeds
 * iframes and MyST directives that only render inside Sphinx. Opening that file
 * in Colab is broken, not just less nice.
 *
 * Every chapter's canonical notebook has a matching PORTABLE notebook under
 * `book/downloads/<chapter>/` (scripts/build_portable_notebook.py) that is a
 * plain, self-contained Colab/Jupyter notebook. The chapter opening ("Run or
 * download this notebook") already links to it directly. This script adds a
 * second, always-visible control in the same place the theme puts its own
 * download button -- the article header -- so the Colab destination does not
 * depend on a reader noticing the opening admonition.
 *
 * This is a static, explicit page -> portable-notebook mapping (checked by
 * interactive/e2e-book/launch-buttons.spec.ts against the *built* HTML), not a
 * guess from the current URL pattern: unmapped pages (Introduction, Syllabus,
 * Contents) get no button.
 */
(function () {
  "use strict";

  var REPO = "yoavmp/ml-neuro-tutorials";
  var BRANCH = "main";

  // path (as it appears in the page URL, without a leading slash) -> portable
  // notebook path relative to the repository root.
  var PAGE_TO_PORTABLE = {
    "chapters/chapter_01/exercise_01.html":
      "book/downloads/chapter_01/exercise_01_portable.ipynb",
    "chapters/chapter_02/exercise_02.html":
      "book/downloads/chapter_02/exercise_02_portable.ipynb",
    "chapters/chapter_03/exercise_03.html":
      "book/downloads/chapter_03/exercise_03_portable.ipynb",
  };

  function portableFor(pathname) {
    for (var page in PAGE_TO_PORTABLE) {
      if (pathname.indexOf(page) !== -1) {
        return PAGE_TO_PORTABLE[page];
      }
    }
    return null;
  }

  function colabUrl(portablePath) {
    return (
      "https://colab.research.google.com/github/" +
      REPO +
      "/blob/" +
      BRANCH +
      "/" +
      portablePath
    );
  }

  function init() {
    var portable = portableFor(window.location.pathname);
    if (!portable) {
      return;
    }
    var host = document.querySelector(".header-article-items__end .article-header-buttons");
    if (!host || host.querySelector('[data-testid="colab-launch-button"]')) {
      return;
    }

    var wrap = document.createElement("div");
    wrap.className = "dropdown-launch-button";

    var link = document.createElement("a");
    link.href = colabUrl(portable);
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.className = "btn btn-sm";
    link.title = "Open the portable notebook in Colab";
    link.setAttribute("aria-label", "Open the portable notebook in Colab");
    link.setAttribute("data-testid", "colab-launch-button");
    link.setAttribute("data-bs-placement", "bottom");
    link.setAttribute("data-bs-toggle", "tooltip");
    link.innerHTML =
      '<i class="fas fa-rocket" aria-hidden="true"></i> ' +
      '<span class="colab-launch-label">Colab</span>';

    wrap.appendChild(link);
    // Placed before the source/download dropdowns so it reads left-to-right as
    // "run it" (Colab) then "get it" (source / download), and is first in tab
    // order among the header-article buttons.
    host.insertBefore(wrap, host.firstChild);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
