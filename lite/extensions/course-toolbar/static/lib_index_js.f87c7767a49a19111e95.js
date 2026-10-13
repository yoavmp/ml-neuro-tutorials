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
function nextAnimationFrame() {
    return new Promise(resolve => requestAnimationFrame(() => resolve()));
}
const HEADER_TEXT_TIMEOUT_MS = 2000;
// Dialog's own `ready` promise (resolves once attached and focused) only
// waits on its *body* widget's React render, when the body happens to be
// a ReactWidget (see dialog.js's onAfterAttach/setFocus) -- it never
// tracks the *header*'s own, separate React render at all. Confirmed
// live: reading the header's textContent synchronously right after
// `ready`, or even after two queued animation frames, still read back
// empty more than once in a row, while the exact same node unambiguously
// held "Select Kernel" moments later. Polling once per animation frame
// (paced to the browser's own paint cycle, not a fixed-length sleep)
// until real text shows up, bounded by HEADER_TEXT_TIMEOUT_MS as a safety
// net, is what actually observes the header reliably.
async function waitForHeaderText(node, timeoutMs) {
    var _a, _b;
    const deadline = Date.now() + timeoutMs;
    for (;;) {
        const text = (_b = (_a = node.querySelector('.jp-Dialog-header')) === null || _a === void 0 ? void 0 : _a.textContent) === null || _b === void 0 ? void 0 : _b.trim();
        if (text) {
            return text;
        }
        if (Date.now() >= deadline) {
            return text;
        }
        await nextAnimationFrame();
    }
}
// WP55R: the recovery below only solves half of the actually-reported
// symptom. There is a second, independent way a *visible, blocking*
// "Select Kernel" modal appears -- one this extension's own code never
// touches at all. @jupyterlab/docregistry's ``Context._populate()``
// calls ``sessionContext.initialize()`` itself, as soon as the notebook
// document is populated (not awaited there, so it races this
// extension's own ``panel.context.ready`` handler below), and -- if
// that resolves "needs selection" -- opens
// ``SessionContextDialogs.selectKernel()`` directly: the exact native
// dialog in the reported screenshot (title "Select Kernel", "No
// Kernel" shown as the current kernel, and "Start <language>
// Kernel"/"Use No Kernel"/"No Kernel"/"Start Kernel" as the grouped
// options -- all confirmed by reading that dialog's own source, not
// assumed). That modal is created and shown independently of this
// extension entirely, so starting Python in the background (below)
// does not, by itself, make an already-open copy of it go away.
//
// Confirmed root cause for *why* "needs selection" happens: reading
// ``@jupyterlab/apputils``'s shipped ``sessioncontext.js``,
// ``SessionContext.startKernel()`` (via ``Private.getDefaultKernel()``)
// reads ``this.specsManager.specs`` *synchronously* -- if the Pyodide
// kernel's federated extension chunk has not yet finished registering
// its kernelspec at that exact moment, ``specs`` is still ``null``,
// ``getDefaultKernel()`` returns ``null`` unconditionally
// (``if (!specs || canStart === false) return null;``), no kernel name
// can be chosen, and ``_populate()`` opens the dialog immediately --
// well before this function's own 30-second recovery window could ever
// run. This is a faster, independent race from the one the function
// below already recovers from (confirmed fixed and verified in WP55).
//
// The cleanest available fix would disable
// ``@jupyterlab/apputils-extension``'s own session-dialogs plugin
// (``@jupyterlab/apputils-extension:sessionDialogs``) via
// ``disabledExtensions`` and replace it with one that waits for
// kernelspecs before ever asking. That needs ``disabledExtensions`` to
// reach the built ``jupyter-lite.json``, and reading the installed
// ``jupyterlite_core`` package's own ``federated_extensions`` addon
// (``patch_jupyterlite_json`` only ever copies each extension's
// ``jupyterlab._build`` field, never a ``disabledExtensions`` list)
// confirms this version does not propagate that from a labextension's
// own ``package.json`` -- so that route would need a build-time patch
// to the generated ``jupyter-lite.json``, not just a change here.
//
// Instead, this uses the dialog's own public API, already shared as a
// JupyterLab singleton (see ``sharedPackages`` in this extension's own
// ``package.json``): every ``Dialog``, including this one, registers
// itself in the static ``Dialog.tracker`` the moment it is
// constructed -- *before* ``launch()`` ever shows it -- and exposes a
// public ``reject()`` that resolves it exactly as if its own Cancel
// button had been clicked. ``SessionContextDialogs.selectKernel()``
// itself only acts further when its result's button was *accepted*
// (``if (sessionContext.isDisposed || !result.button.accept) return;``),
// so rejecting it is a safe no-op from its own perspective -- it never
// reaches the branch that could call ``sessionContext.shutdown()``.
//
// This only ever acts on the *first* "Select Kernel" dialog seen while
// armed, and the guard disarms itself (stops listening for new dialogs
// entirely) the moment the kernel reaches a real post-startup status --
// an explicit, later "Change Kernel" request from the user always
// happens after that point, so it is left to show the normal selector,
// untouched, exactly as the WP requires.
//
// Two things below look obvious in hindsight but were both wrong in
// earlier versions of this guard, each only caught by live Playwright
// reproduction (see the WP55R report's own account of both):
//
// 1. This guard's *armed lifetime* must not be tied to
//    ensureKernelStartedInner() returning early. A first version did
//    exactly that (disconnected everything in ensureKernelStarted's own
//    `finally`). ``panel.sessionContext.session?.kernel`` -- and
//    therefore ``panel.sessionContext.ready`` -- becomes truthy as soon
//    as a KernelConnection *object* exists, which can be well before
//    the underlying kernel process (here, a multi-megabyte Pyodide WASM
//    download) has actually finished starting. ensureKernelStartedInner's
//    first bounded wait exits the moment that connection object
//    appears, tearing this guard down seconds before a dialog opened
//    during the still-ongoing download in a Playwright reproduction
//    that delayed the Pyodide kernel's own CDN assets (not the
//    kernelspec extension) -- reproducing the exact "fix starts Python
//    in the background but an earlier dialog stays open" failure mode
//    the WP warned against.
// 2. For the same reason, the *decision to dismiss a given dialog* must
//    not re-check ``session?.kernel`` either -- a second version did,
//    reasoning "never touch a dialog once a kernel exists," and a live
//    reproduction (clicking the real kernel-name toolbar item while it
//    still read "No Kernel", during the same CDN-delay window) showed
//    exactly this: a KernelConnection object already existed by the
//    time the dialog's own `ready` resolved, even though the kernel was
//    still "starting" and the toolbar's own label was stale -- so that
//    check silently left the dialog open. The ``armed`` flag below,
//    tied to the kernel's real status rather than connection-object
//    existence, is already the single correct signal for "are we still
//    in the startup window": if a dialog is seen at all while armed, it
//    is intercepted, full stop.
const DIALOG_GUARD_TIMEOUT_MS = 60000;
const KERNEL_NOT_YET_STARTED_STATUSES = new Set([
    'starting',
    'unknown',
    'restarting',
    'autorestarting'
]);
function interceptAutomaticKernelSelectDialog(panel) {
    let handled = false;
    let armed = true;
    const onDialogAdded = (_sender, dialog) => {
        if (!armed || handled) {
            return;
        }
        // Dialog.resolve()/reject() are documented no-ops until launch() has
        // actually set its internal promise, which happens before the
        // dialog is attached to the DOM but synchronously inside launch()
        // itself -- waiting for the dialog's own `ready` (resolves after
        // its first render/focus) guarantees launch() has already run.
        //
        // The title check also has to wait, and `ready` alone is not
        // enough: Dialog's header is a React-rendered widget (see
        // dialog.js's own Renderer.createHeader()), and Dialog never sets
        // the Lumino `Widget.title` property at all (that property is for
        // things like dock-panel tabs, not this header) --
        // `dialog.title.label` is always `''` for every Dialog, confirmed
        // live (an earlier version of this check read `dialog.title.label`
        // and, because of that, never matched a single dialog). Reading the
        // rendered header text instead -- `.jp-Dialog-header`, the exact
        // class name createHeader() adds -- is what the title actually ends
        // up as in the DOM; see waitForHeaderText's own comment for why
        // `dialog.ready` alone is not a late-enough signal to read it.
        void dialog.ready.then(async () => {
            const headerText = await waitForHeaderText(dialog.node, HEADER_TEXT_TIMEOUT_MS);
            if (!armed ||
                handled ||
                headerText !== 'Select Kernel' ||
                panel.isDisposed ||
                panel.sessionContext.isDisposed) {
                return;
            }
            handled = true;
            dialog.reject();
        });
    };
    _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.tracker.widgetAdded.connect(onDialogAdded);
    const disarm = () => {
        if (!armed) {
            return;
        }
        armed = false;
        _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.tracker.widgetAdded.disconnect(onDialogAdded);
        panel.sessionContext.statusChanged.disconnect(onStatusChanged);
        clearTimeout(ceiling);
    };
    function onStatusChanged(_sender, status) {
        if (!KERNEL_NOT_YET_STARTED_STATUSES.has(status)) {
            disarm();
        }
    }
    panel.sessionContext.statusChanged.connect(onStatusChanged);
    const ceiling = setTimeout(disarm, DIALOG_GUARD_TIMEOUT_MS);
    return disarm;
}
async function ensureKernelStarted(app, panel) {
    var _a;
    if ((_a = panel.sessionContext.session) === null || _a === void 0 ? void 0 : _a.kernel) {
        return;
    }
    await ensureKernelStartedInner(app, panel);
}
async function ensureKernelStartedInner(app, panel) {
    var _a, _b;
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
    if ((_a = panel.sessionContext.session) === null || _a === void 0 ? void 0 : _a.kernel) {
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
    if ((_b = panel.sessionContext.session) === null || _b === void 0 ? void 0 : _b.kernel) {
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
            // Arm the Select-Kernel-dialog guard here, synchronously, rather
            // than inside the panel.context.ready callback below. A panel is
            // added to `tracker` -- and so becomes reachable as
            // `tracker.currentWidget` -- as soon as the widget itself exists,
            // which can be *before* panel.context.ready resolves (that
            // promise additionally waits on the contents manager and the
            // document's own population). A live reproduction
            // (kernel-select-dialog-race.spec.ts) caught exactly this gap:
            // deferring arming behind `.then()` left a real window, confirmed
            // live, where a Select Kernel dialog could open and never get
            // intercepted because this extension had not registered its
            // listener yet. `panel.sessionContext` itself (unlike the
            // document being populated) already exists as soon as the panel
            // does, so there is no reason to wait here at all.
            interceptAutomaticKernelSelectDialog(panel);
            void panel.context.ready.then(() => {
                addButtons(panel, DEFAULT_SETTINGS);
                addStatusReadout(panel);
                void ensureKernelStarted(app, panel);
            });
        });
        // Test-only hook for interactive/e2e-book/kernel-select-dialog-
        // race.spec.ts. Repeated, varied, real network-delay fault
        // injection against the actual kernelspec federated extension
        // (documented in that spec and in the WP55R report) never won the
        // live race inside ``Context._populate()`` -- this app's own
        // bootstrap gates document population behind every plugin's own
        // activation finishing, so ``specsManager.specs`` is, in
        // practice, always already populated by the time any notebook is
        // ever opened here. This calls the exact same, unmodified
        // ``SessionContextDialogs.selectKernel()`` JupyterLab ships (see
        // interceptAutomaticKernelSelectDialog's own comment above)
        // against a real panel's real sessionContext, so a test can
        // deterministically open the identical dialog
        // ``Context._populate()`` would have opened, without depending on
        // winning that unreachable-in-practice race. Not wired to any
        // command, menu, keybinding, or palette entry -- a plain function
        // on `window`, under a name no production code reads.
        window.__courseToolbarOpenSelectKernelDialogForTest = async () => {
            const panel = tracker.currentWidget;
            if (!panel) {
                return false;
            }
            void new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.SessionContextDialogs().selectKernel(panel.sessionContext);
            return true;
        };
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }

}]);
//# sourceMappingURL=lib_index_js.f87c7767a49a19111e95.js.map