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

const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description:
    'Course navigation, download, reset, and save-status toolbar for migrated exercise notebooks.',
  autoStart: true,
  requires: [INotebookTracker, IDocumentManager],
  activate: (
    _app: JupyterFrontEnd,
    tracker: INotebookTracker,
    _docManager: IDocumentManager
  ) => {
    tracker.widgetAdded.connect((_sender, panel) => {
      void panel.context.ready.then(() => {
        addButtons(panel, DEFAULT_SETTINGS);
        addStatusReadout(panel);
      });
    });
  }
};

export default plugin;
