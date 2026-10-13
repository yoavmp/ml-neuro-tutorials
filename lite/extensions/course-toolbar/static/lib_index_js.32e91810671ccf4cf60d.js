"use strict";
(self["webpackChunkcourse_toolbar"] = self["webpackChunkcourse_toolbar"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js"
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/docmanager */ "webpack/sharing/consume/default/@jupyterlab/docmanager");
/* harmony import */ var _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/notebook */ "webpack/sharing/consume/default/@jupyterlab/notebook");
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_3__);




const PLUGIN_ID = 'course-toolbar:plugin';
// The book Contents page is three directory levels above every notebook
// app page (".../lite/notebooks/index.html" -> "..." site root). Not yet
// exposed as a live setting: there is only one book hub for this whole
// site, so a single constant is simpler than a schema-backed override.
const DEFAULT_SETTINGS = {
    contentsUrl: '../../contents.html'
};
function liteFilesRoot() {
    // window.location.href is ".../lite/notebooks/index.html?path=...".
    // Resolving a relative URL against it already drops "index.html" for
    // free, so a single "../" strips "notebooks/", leaving the "lite/" root
    // that "files/" (the untouched static templates) sits under.
    return new URL('../', window.location.href);
}
function templateUrlFor(path) {
    return new URL(`files/${path}`, liteFilesRoot()).toString();
}
function download(filename, content) {
    const text = JSON.stringify(content, null, 1);
    const blob = new Blob([text], { type: 'application/x-ipynb+json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
}
function addStatusReadout(panel) {
    const node = document.createElement('span');
    node.className = 'course-toolbar-status';
    node.textContent = 'Saved';
    const widget = new _lumino_widgets__WEBPACK_IMPORTED_MODULE_3__.Widget({ node });
    widget.addClass('course-toolbar-status-widget');
    const context = panel.context;
    const refresh = () => {
        if (context.model.dirty) {
            node.textContent = 'Unsaved changes (stored only in this browser)';
            node.dataset.state = 'dirty';
        }
        else {
            node.textContent = 'Saved in this browser';
            node.dataset.state = 'saved';
        }
    };
    context.saveState.connect((_sender, state) => {
        if (state === 'started') {
            node.textContent = 'Saving…';
            node.dataset.state = 'saving';
        }
        else {
            refresh();
        }
    });
    context.model.stateChanged.connect(refresh);
    refresh();
    panel.toolbar.addItem('courseToolbarStatus', widget);
}
function addButtons(panel, settings) {
    const backButton = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.ToolbarButton({
        label: 'Back to course contents',
        tooltip: 'Return to the course Contents page',
        onClick: () => {
            window.location.href = new URL(settings.contentsUrl, window.location.href).toString();
        }
    });
    const downloadButton = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.ToolbarButton({
        label: 'Download my notebook',
        tooltip: 'Download this notebook, including your edits, as it is now',
        onClick: () => {
            const context = panel.context;
            void context.save().then(() => {
                var _a;
                const filename = (_a = context.path.split('/').pop()) !== null && _a !== void 0 ? _a : 'notebook.ipynb';
                download(filename, context.model.toJSON());
            });
        }
    });
    const resetButton = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.ToolbarButton({
        label: 'Reset from course template',
        tooltip: 'Discard your edits and restore the original course template',
        onClick: () => {
            void (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.showDialog)({
                title: 'Reset from course template?',
                body: 'This discards every edit and answer you have made in this ' +
                    'browser for this notebook and replaces it with the original ' +
                    'course template. Download your notebook first if you want to ' +
                    'keep your work. This cannot be undone.',
                buttons: [
                    _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.cancelButton({ label: 'Cancel' }),
                    _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.warnButton({ label: 'Reset' })
                ]
            }).then(async (result) => {
                if (!result.button.accept) {
                    return;
                }
                const context = panel.context;
                const response = await fetch(templateUrlFor(context.path));
                if (!response.ok) {
                    void (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.showDialog)({
                        title: 'Reset failed',
                        body: `Could not load the course template (HTTP ${response.status}).`,
                        buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.okButton()]
                    });
                    return;
                }
                const template = await response.json();
                context.model.fromJSON(template);
                await context.save();
            });
        }
    });
    // Left-to-right order in the toolbar: Back, Download, Reset.
    panel.toolbar.addItem('courseToolbarBack', backButton);
    panel.toolbar.addItem('courseToolbarDownload', downloadButton);
    panel.toolbar.addItem('courseToolbarReset', resetButton);
}
// WP55 item E: recover from JupyterLite's own intermittent "No Kernel"
// startup race.
//
// Root cause (confirmed by reading the shipped
// @jupyterlab/apputils SessionContext source, not assumed):
// ``SessionContext.startKernel()`` reads ``this.specsManager.specs``
// *synchronously*, without awaiting ``specsManager.ready`` first. That
// call happens as soon as a notebook's document context is ready, racing
// the Pyodide kernel's own federated extension, which registers its
// kernelspec asynchronously (it is a separate lazily-loaded JS chunk). If
// the chunk hasn't registered yet at that exact moment, ``specs`` is
// still null, no kernel name can be picked, ``startKernel()`` returns
// "needs selection" -- and, critically, *nothing ever retries*: no
// listener on ``specsManager.specsChanged`` is wired to this path, so the
// session is left on "No Kernel" permanently. A full page reload "fixes"
// this only because the browser's cache makes the second load's
// federated-extension fetch fast enough to win the race -- it is not a
// real fix, just a favorable rerun. This also compounds with a separate,
// permanent (non-racy) mismatch: every exercise notebook's own saved
// kernelspec metadata asks for "python3" by name, but this deployment's
// Pyodide kernel is actually registered as "python" (see book/lite's
// built jupyter-lite.json -> "defaultKernelName"), confirmed live against
// the deployed site -- every single page load (8/8 fresh/returning/
// launch-button attempts) logs JupyterLab's own name-mismatch fallback
// notice in the browser console, though that fallback alone did not
// reproduce a stuck "No Kernel" in those 8 runs. Both are fixed at the
// root here: not a sleep, not a reload, not a broad cache purge.
const KERNEL_RECOVERY_TIMEOUT_MS = 30000;
function afterTimeout(value, ms) {
    return new Promise(resolve => setTimeout(() => resolve(value), ms));
}
async function ensureKernelStarted(app, panel) {
    var _a, _b, _c;
    if ((_a = panel.sessionContext.session) === null || _a === void 0 ? void 0 : _a.kernel) {
        return;
    }
    // No kernel yet -- but the normal automatic path (SessionContext.
    // initialize(), already in flight by the time a notebook's document
    // context becomes ready) may simply still be in progress, not
    // necessarily stuck: a session-start request can be outstanding for a
    // little while before session?.kernel becomes set. Racing
    // sessionContext.ready against a bounded timeout distinguishes "merely
    // still settling" (ready resolves on its own -- do nothing further,
    // this function existing only to recover the *stuck* case) from the
    // actual failure this function recovers from: in that exact case,
    // ready never resolves at all (see the comment above), so this wait is
    // bounded precisely so it cannot hang forever the way sessionContext.
    // ready itself would. Without this check, starting a second kernel
    // here while the first request is still merely slow (not actually
    // stuck) would race JupyterLab's own session-preemption logic for no
    // reason -- confirmed live: the first version of this fix, which
    // skipped straight to its own recovery attempt, intermittently left a
    // benign-but-real "<id> was disposed" console error from exactly that
    // harmless collision, caught by this repo's own browser test suite.
    await Promise.race([
        panel.sessionContext.ready,
        afterTimeout(undefined, KERNEL_RECOVERY_TIMEOUT_MS)
    ]).catch(() => undefined);
    if ((_b = panel.sessionContext.session) === null || _b === void 0 ? void 0 : _b.kernel) {
        return; // the automatic path settled on its own while this waited
    }
    // Still no kernel after a full timeout window: this is the actual
    // stuck case. Wait, bounded, for the kernelspec registry itself (not a
    // fixed sleep: resolves as soon as the registry is actually ready,
    // which is the real event this is waiting on).
    const kernelSpecs = app.serviceManager.kernelspecs;
    const specs = await Promise.race([
        kernelSpecs.ready.then(() => kernelSpecs.specs),
        afterTimeout(null, KERNEL_RECOVERY_TIMEOUT_MS)
    ]);
    if ((_c = panel.sessionContext.session) === null || _c === void 0 ? void 0 : _c.kernel) {
        return; // started on its own while this function was waiting
    }
    const defaultName = specs === null || specs === void 0 ? void 0 : specs.default;
    if (!specs || !defaultName || !specs.kernelspecs[defaultName]) {
        // A genuine failure (e.g. the kernel's own assets never loaded --
        // offline, or a CDN outage): report it plainly instead of leaving an
        // unexplained "No Kernel" or waiting indefinitely.
        void (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.showDialog)({
            title: 'Kernel did not start',
            body: 'The Python (Pyodide) kernel did not become available after ' +
                'waiting a minute. This usually means a network or CDN problem ' +
                'while loading the kernel. Try reloading this page; if it keeps ' +
                'happening, check your network connection.',
            buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.okButton()]
        });
        return;
    }
    try {
        await panel.sessionContext.changeKernel({ name: defaultName });
    }
    catch (err) {
        void (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.showDialog)({
            title: 'Kernel did not start',
            body: `Could not start the Python (Pyodide) kernel: ${err instanceof Error ? err.message : String(err)}. Try reloading this page.`,
            buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.okButton()]
        });
    }
}
const plugin = {
    id: PLUGIN_ID,
    description: 'Course navigation, download, reset, and save-status toolbar for migrated exercise notebooks.',
    autoStart: true,
    requires: [_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_2__.INotebookTracker, _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__.IDocumentManager],
    activate: (app, tracker, _docManager) => {
        tracker.widgetAdded.connect((_sender, panel) => {
            void panel.context.ready.then(() => {
                addButtons(panel, DEFAULT_SETTINGS);
                addStatusReadout(panel);
                void ensureKernelStarted(app, panel);
            });
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }

}]);
//# sourceMappingURL=lib_index_js.32e91810671ccf4cf60d.js.map