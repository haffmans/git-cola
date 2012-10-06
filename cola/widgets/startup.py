"""
Provides the git-cola startup dialog

The startup dialog is presented when no repositories can be
found at startup.

"""
import os

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL

from cola import core
from cola import dash
from cola import git
from cola import guicmds
from cola import settings
from cola import qtutils
from cola import utils
from cola.widgets import defs
from cola.widgets.standard import Dialog

class StartupDialog(Dialog):
    """Provides a GUI to Open or Clone a git repository."""

    def __init__(self, parent=None):
        Dialog.__init__(self, parent)
        self.setWindowTitle(self.tr('git-cola'))
        self._gitdir = None

        self._layt = QtGui.QHBoxLayout()
        self._layt.setMargin(defs.margin)
        self._layt.setSpacing(defs.spacing)

        self._new_btn = QtGui.QPushButton('New...')
        self._new_btn.setIcon(qtutils.new_icon())

        self._open_btn = QtGui.QPushButton('Open...')
        self._open_btn.setIcon(qtutils.open_icon())

        self._clone_btn = QtGui.QPushButton('Clone...')
        self._clone_btn.setIcon(qtutils.git_icon())

        self._close_btn = QtGui.QPushButton('Close')

        self._layt.addWidget(self._open_btn)
        self._layt.addWidget(self._clone_btn)
        self._layt.addWidget(self._new_btn)
        self._layt.addStretch()
        self._layt.addWidget(self._close_btn)

        self.model = settings.Settings()

        self._vlayt = QtGui.QVBoxLayout()
        self._vlayt.setMargin(defs.margin)
        self._vlayt.setSpacing(defs.margin)

        self._bookmark_label = QtGui.QLabel(self.tr('Select Repository...'))
        self._bookmark_label.setAlignment(Qt.AlignCenter)

        self._dashboard_model = dash.model.DashboardModel()
        self._bookmark_list = dash.view.DashboardView(self._dashboard_model, self)

        if (self._dashboard_model.rowCount() == 0):
            self._bookmark_label.setMinimumHeight(1)
            self._bookmark_list.setMinimumHeight(1)
            self._bookmark_label.hide()
            self._bookmark_list.hide()

        self._vlayt.addWidget(self._bookmark_label)
        self._vlayt.addWidget(self._bookmark_list)
        self._vlayt.addLayout(self._layt)

        self.setLayout(self._vlayt)

        qtutils.connect_button(self._open_btn, self._open)
        qtutils.connect_button(self._clone_btn, self._clone)
        qtutils.connect_button(self._new_btn, self._new)
        qtutils.connect_button(self._close_btn, self.reject)

        self.connect(self._bookmark_list,
                     SIGNAL('open(const QString &)'),
                     self._open_bookmark)

        self.widget_version = 1
        qtutils.apply_state(self)

    def closeEvent(self, event):
        s = settings.Settings()
        qtutils.save_state(self, handler=s)
        Dialog.closeEvent(self, event)

    def done(self, r):
        # Save settings prior to closing; closeEvent is filtered on accept/reject
        s = settings.Settings()
        qtutils.save_state(self, handler=s)
        Dialog.done(self, r)

    def apply_state(self, state):
        """Imports data for save/restore"""
        # 1 is the widget version; change when widgets are added/removed
        Dialog.apply_state(self, state)
        if (state['bookmark_list']):
            self._bookmark_list.apply_state(state['bookmark_list'])

    def export_state(self):
        """Exports data for save/restore"""
        state = Dialog.export_state(self)
        if (self._bookmark_list.isVisible()):
            state['bookmark_list'] = self._bookmark_list.export_state()
        return state

    def find_git_repo(self):
        """
        Return a path to a git repository

        This is the entry point for external callers.
        This method finds a git repository by allowing the
        user to browse to one on the filesystem or by creating
        a new one with git-clone.

        """
        self.show()
        self.raise_()
        if self.exec_() == QtGui.QDialog.Accepted:
            return self._gitdir
        return None

    def _open(self):
        self._gitdir = self._get_selected_bookmark()
        if not self._gitdir:
            self._gitdir = qtutils.opendir_dialog('Open Git Repository...',
                                                  os.getcwd())
        if self._gitdir:
            self.accept()

    def _clone(self):
        gitdir = guicmds.clone_repo(spawn=False)
        if gitdir:
            self._gitdir = gitdir
            self.accept()

    def _new(self):
        dlg = QtGui.QFileDialog(self)
        dlg.setFileMode(QtGui.QFileDialog.Directory)
        dlg.setOption(QtGui.QFileDialog.ShowDirsOnly)
        if dlg.exec_() != QtGui.QFileDialog.Accepted:
            return
        paths = dlg.selectedFiles()
        if not paths:
            return
        upath = unicode(paths[0])
        if not upath:
            return
        path = core.encode(unicode(paths[0]))
        # Avoid needlessly calling `git init`.
        if git.is_git_dir(path):
            # We could prompt here and confirm that they really didn't
            # mean to open an existing repository, but I think
            # treating it like an "Open" is a sensible DWIM answer.
            self._gitdir = upath
            self.accept()
            return

        os.chdir(path)
        status, out, err = utils.run_command(['git', 'init'])
        if status != 0:
            title = 'Error Creating Repository'
            msg = 'git init returned exit status %d' % status
            details = 'output:\n%s\n\nerrors:\n%s' % (out, err)
            qtutils.critical(title, msg, details)
        else:
            self._gitdir = upath
            self.accept()

    def _open_bookmark(self, directory):
        self._gitdir = unicode(directory)
        if self._gitdir:
            self.accept()

    def _get_selected_bookmark(self):
        selected = self._bookmark_list.selectedIndexes()
        if(len(selected) > 0 and selected[0].row() != 0):
            return unicode(self._bookmark_model.data(selected[0]).toString())
        return None
