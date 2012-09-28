import os

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QTimer

from cola import qtutils
from cola import git
from cola import gitcfg
from cola import gitcmds
from cola import settings
from cola.widgets import defs
from cola.widgets import standard

class StatusTable(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent)
        self.setModel(model)
        self.verticalHeader().hide()
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.horizontalHeader().setCascadingSectionResizes(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

class DashboardView(standard.Widget):
    def __init__(self, model, parent=None):
        standard.Widget.__init__(self, parent=parent)
        self.setWindowTitle(self.tr('Dashboard'))
        self.resize(600, 360)
        self._layt = QtGui.QVBoxLayout()

        self._model = model
        self._table = StatusTable(self._model)

        # Init model
        self._settingsModel = settings.Settings()
        for bookmark in self._settingsModel.bookmarks:
            self._model.add_repo(bookmark)

        # Init table
        self.connect(self._table, SIGNAL('activated(QModelIndex)'), self.open_bookmark)

        # Init layout
        self._layt.addWidget(self._table)
        self.setLayout(self._layt)

        # Initialize the git command object
        self._git = git.instance()
        self._update_queue = list()

    def open_bookmark(self, index):
        directory_index = index.sibling(index.row(), 0)
        directory = self._model.data(directory_index).toString()
        self.emit(SIGNAL('open(QString)'), directory)

    def showEvent(self, event):
        # Delay-load all repos
        del self._update_queue[:]
        self._update_queue.extend(self._model.repos)
        self._update_queue.reverse()
        QTimer.singleShot(10, self.update_next)

    def set_worktree(self, repo, worktree=None):
        if (worktree == None):
            worktree = repo.directory
        self._git.set_worktree(worktree)
        return self._git.is_valid()

    def update_next(self):
        if (len(self._update_queue) == 0):
            return
        repo = self._update_queue.pop()
        self.update_status(repo)
        QTimer.singleShot(10, self.update_next)

    def update_status(self, repo):
        if not self.set_worktree(repo):
            return False
        repo.begin_update()

        status = gitcmds.head_tracking_status()
        repo.branch = status.get('head')
        repo.upstream = status.get('upstream')
        repo.diff = int(status.get('amount')) if status.get('status') == 'ahead' else  - int(status.get('amount'))
        repo.updated()

if __name__ == "__main__":
    import sys
    from cola.prefs import preferences

    app = QtGui.QApplication(sys.argv)
    view = dashboard()
    sys.exit(app.exec_())
