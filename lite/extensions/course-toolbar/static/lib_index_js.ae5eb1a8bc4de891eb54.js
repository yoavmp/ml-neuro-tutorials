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
const plugin = {
    id: PLUGIN_ID,
    description: 'Course navigation, download, reset, and save-status toolbar for migrated exercise notebooks.',
    autoStart: true,
    requires: [_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_2__.INotebookTracker, _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__.IDocumentManager],
    activate: (_app, tracker, _docManager) => {
        tracker.widgetAdded.connect((_sender, panel) => {
            void panel.context.ready.then(() => {
                addButtons(panel, DEFAULT_SETTINGS);
                addStatusReadout(panel);
            });
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }

}]);
//# sourceMappingURL=lib_index_js.ae5eb1a8bc4de891eb54.js.map