/**
 * WP41 reusable JupyterLite notebook toolbar.
 *
 * Adds four things to every open notebook, for every migrated course
 * exercise, without any per-exercise code:
 *   - "Back to course contents"
 *   - "Download my notebook" (exports the CURRENT in-browser state, not
 *     the original template)
 *   - "Reset from course template" (after a confirmation dialog)
 *   - a plain-text save/autosave status readout
 *
 * "Reset" and "Back" both need to know where the pristine template and the
 * book's Contents page live relative to the running app. Both are derived
 * from window.location rather than hard-coded, so the same extension works
 * unmodified under any GitHub Pages base path: this page is always served
 * at ".../lite/notebooks/index.html", the untouched static template for the
 * open document is always at the sibling ".../lite/files/<same path>", and
 * the book hub's Contents page is two levels up from "lite/". A relative URL
 * resolved against "index.html" already drops the filename for free, so
 * reaching "lite/" from "notebooks/index.html" takes exactly one "../", and
 * the site root takes exactly two -- not one/two more, a common off-by-one.
 */
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { Dialog, showDialog, ToolbarButton } from '@jupyterlab/apputils';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { Widget } from '@lumino/widgets';

const PLUGIN_ID = 'course-toolbar:plugin';

interface ICourseToolbarSettings {
  contentsUrl: string;
}

// The book Contents page is three directory levels above every notebook
// app page (".../lite/notebooks/index.html" -> "..." site root). Not yet
// exposed as a live setting: there is only one book hub for this whole
// site, so a single constant is simpler than a schema-backed override.
const DEFAULT_SETTINGS: ICourseToolbarSettings = {
  contentsUrl: '../../contents.html'
};

function liteFilesRoot(): URL {
  // window.location.href is ".../lite/notebooks/index.html?path=...".
  // Resolving a relative URL against it already drops "index.html" for
  // free, so a single "../" strips "notebooks/", leaving the "lite/" root
  // that "files/" (the untouched static templates) sits under.
  return new URL('../', window.location.href);
}

function templateUrlFor(path: string): string {
  return new URL(`files/${path}`, liteFilesRoot()).toString();
}

function download(filename: string, content: unknown): void {
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

function addStatusReadout(panel: NotebookPanel): void {
  const node = document.createElement('span');
  node.className = 'course-toolbar-status';
  node.textContent = 'Saved';
  const widget = new Widget({ node });
  widget.addClass('course-toolbar-status-widget');

  const context = panel.context;
  const refresh = () => {
    if (context.model.dirty) {
      node.textContent = 'Unsaved changes (stored only in this browser)';
      node.dataset.state = 'dirty';
    } else {
      node.textContent = 'Saved in this browser';
      node.dataset.state = 'saved';
    }
  };
  context.saveState.connect((_sender, state) => {
    if (state === 'started') {
      node.textContent = 'Saving…';
      node.dataset.state = 'saving';
    } else {
      refresh();
    }
  });
  context.model.stateChanged.connect(refresh);
  refresh();

  panel.toolbar.addItem('courseToolbarStatus', widget);
}

function addButtons(
  panel: NotebookPanel,
  settings: ICourseToolbarSettings
): void {
  const backButton = new ToolbarButton({
    label: 'Back to course contents',
    tooltip: 'Return to the course Contents page',
    onClick: () => {
      window.location.href = new URL(
        settings.contentsUrl,
        window.location.href
      ).toString();
    }
  });

  const downloadButton = new ToolbarButton({
    label: 'Download my notebook',
    tooltip: 'Download this notebook, including your edits, as it is now',
    onClick: () => {
      const context = panel.context;
      void context.save().then(() => {
        const filename = context.path.split('/').pop() ?? 'notebook.ipynb';
        download(filename, context.model.toJSON());
      });
    }
  });

  const resetButton = new ToolbarButton({
    label: 'Reset from course template',
    tooltip: 'Discard your edits and restore the original course template',
    onClick: () => {
      void showDialog({
        title: 'Reset from course template?',
        body:
          'This discards every edit and answer you have made in this ' +
          'browser for this notebook and replaces it with the original ' +
          'course template. Download your notebook first if you want to ' +
          'keep your work. This cannot be undone.',
        buttons: [
          Dialog.cancelButton({ label: 'Cancel' }),
          Dialog.warnButton({ label: 'Reset' })
        ]
      }).then(async result => {
        if (!result.button.accept) {
          return;
        }
        const context = panel.context;
        const response = await fetch(templateUrlFor(context.path));
        if (!response.ok) {
          void showDialog({
            title: 'Reset failed',
            body: `Could not load the course template (HTTP ${response.status}).`,
            buttons: [Dialog.okButton()]
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
async function ensureKernelStarted(
  app: JupyterFrontEnd,
  panel: NotebookPanel
): Promise<void> {
  // The normal automatic path (SessionContext.initialize(), already
  // in flight by the time a notebook's document context becomes ready)
  // either already won the race above, or already lost it -- either way
  // it has settled by now, synchronously from this function's point of
  // view, so check the outcome directly instead of awaiting
  // sessionContext.ready: in the exact failure this recovers from, that
  // promise never resolves (see above), so awaiting it here would just
  // trade "stuck on No Kernel" for "stuck awaiting here" instead.
  if (panel.sessionContext.session?.kernel) {
    return;
  }

  // No kernel yet -- wait, bounded, for the kernelspec registry itself
  // (not a fixed sleep: resolves as soon as the registry is actually
  // ready, which is the real event this is waiting on).
  const kernelSpecs = app.serviceManager.kernelspecs;
  const specs = await Promise.race([
    kernelSpecs.ready.then(() => kernelSpecs.specs),
    new Promise<null>(resolve => setTimeout(() => resolve(null), 30_000))
  ]);

  if (panel.sessionContext.session?.kernel) {
    return; // started on its own while this function was waiting
  }

  const defaultName = specs?.default;
  if (!specs || !defaultName || !specs.kernelspecs[defaultName]) {
    // A genuine failure (e.g. the kernel's own assets never loaded --
    // offline, or a CDN outage): report it plainly instead of leaving an
    // unexplained "No Kernel" or waiting indefinitely.
    void showDialog({
      title: 'Kernel did not start',
      body:
        'The Python (Pyodide) kernel did not become available after ' +
        'waiting 30 seconds. This usually means a network or CDN problem ' +
        'while loading the kernel. Try reloading this page; if it keeps ' +
        'happening, check your network connection.',
      buttons: [Dialog.okButton()]
    });
    return;
  }

  try {
    await panel.sessionContext.changeKernel({ name: defaultName });
  } catch (err) {
    void showDialog({
      title: 'Kernel did not start',
      body: `Could not start the Python (Pyodide) kernel: ${
        err instanceof Error ? err.message : String(err)
      }. Try reloading this page.`,
      buttons: [Dialog.okButton()]
    });
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description:
    'Course navigation, download, reset, and save-status toolbar for migrated exercise notebooks.',
  autoStart: true,
  requires: [INotebookTracker, IDocumentManager],
  activate: (
    app: JupyterFrontEnd,
    tracker: INotebookTracker,
    _docManager: IDocumentManager
  ) => {
    tracker.widgetAdded.connect((_sender, panel) => {
      void panel.context.ready.then(() => {
        addButtons(panel, DEFAULT_SETTINGS);
        addStatusReadout(panel);
        void ensureKernelStarted(app, panel);
      });
    });
  }
};

export default plugin;
