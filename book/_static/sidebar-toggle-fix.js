/*
 * WP07 — primary/secondary sidebar-toggle fix for sphinx-book-theme 1.3.0 on
 * pydata-sphinx-theme 0.17.1.
 *
 * Root cause
 * ----------
 * Each page renders TWO `.primary-toggle` buttons (and two `.secondary-toggle`
 * buttons):
 *   1. a hidden one inside `#pst-header` (CSS: `.bd-header button.sidebar-toggle
 *      { display: none }`), and
 *   2. the visible one inside `.bd-header-article` that the reader actually sees
 *      ("Toggle primary sidebar" / "Toggle secondary sidebar").
 * Both theme scripts wire their click handlers with
 * `document.querySelector(".primary-toggle")`, which returns the FIRST match in
 * DOM order — the hidden `#pst-header` button. The visible article-header button
 * therefore has no handler and does nothing on click or keyboard activation.
 *
 * Fix
 * ---
 * Forward activation from each visible article-header toggle to its already
 * correctly-wired hidden counterpart. This re-uses the theme's own behaviour
 * unchanged: at >= 992 px it toggles `.pst-sidebar-hidden` on the persistent
 * sidebar; below 992 px it opens the sidebar `<dialog>` modal. No theme
 * internals are patched and no behaviour is re-implemented here.
 */
(function () {
  "use strict";

  function forward(visibleSelector, hiddenSelector) {
    var visible = document.querySelector(visibleSelector);
    var hidden = document.querySelector(hiddenSelector);
    if (!visible || !hidden || visible === hidden) {
      return;
    }
    if (visible.dataset.sbtToggleForwarded === "1") {
      return;
    }
    visible.dataset.sbtToggleForwarded = "1";
    visible.addEventListener("click", function (event) {
      // Only act on the genuine activation of the visible button; the
      // synthetic click we dispatch on `hidden` never re-enters here.
      event.preventDefault();
      hidden.click();
    });
  }

  function init() {
    forward(".bd-header-article .primary-toggle", "#pst-header .primary-toggle");
    forward(".bd-header-article .secondary-toggle", "#pst-header .secondary-toggle");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
