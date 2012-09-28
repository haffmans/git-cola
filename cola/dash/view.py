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

class StatusWidget(standard.Widget):
    def __init__(self, repo, parent=None):
        standard.Widget.__init__(self, parent=parent)
        repo.add_observer(repo.message_updated, self.update)

        self._repo = repo

        self._path = QtGui.QLabel()
        self._path.setText("<b>" + repo.directory + "</b>")

        self._branch = QtGui.QLabel()

        self._ahead = QtGui.QLabel()

        self._upstream = QtGui.QLabel()

        self._layt = QtGui.QHBoxLayout()
        self._layt.setMargin(defs.margin)
        self._layt.setSpacing(defs.spacing)
        self._layt.addWidget(self._path)
        self._layt.addWidget(self._branch)
        self._layt.addWidget(self._ahead)
        self._layt.addWidget(self._upstream)
        self.setLayout(self._layt)

        self.update()

    def update(self):
        self._path.setText("<b>" + self._repo.directory + "</b>")
        color = "#80ff80" if self._repo.diff > 0 else "#8080ff" if self._repo.diff == 0 else "#ff8080"
        aheadstr = ('%+d' % self._repo.diff) if self._repo.diff != 0 else '0'
        self._ahead.setText("<b><font color=\"" + color + "\">" + aheadstr + "</font></b>")
        self._upstream.setText(self._repo.upstream)

class DashboardView(standard.Widget):
    shown = QtCore.pyqtSignal()

    def __init__(self, model, parent=None):
        standard.Widget.__init__(self, parent=parent)
        self.setWindowTitle(self.tr('Dashboard'))
        self.resize(600, 360)
        self.model = model

        self._layt = QtGui.QVBoxLayout()

        model.add_observer(model.message_added_row, self.add_row)

        # Init model
        self.settingsModel = settings.Settings()
        for bookmark in self.settingsModel.bookmarks:
            self.model.add_repo(bookmark)

        # Init view
        for i in range(0, len(self.model.repos) - 1):
            add_row(self, i)

        self.setLayout(self._layt)

        # Initialize the git command object
        self.git = git.instance()
        self.update_queue = list()

    def add_row(self, index):
        self._layt.addWidget(StatusWidget(self.model.repos[index], self))

    def showEvent(self, event):
        # Delay-load all repos
        del self.update_queue[:]
        self.update_queue.extend(self.model.repos)
        self.update_queue.reverse()
        QTimer.singleShot(10, self.update_next)

    def set_worktree(self, repo, worktree=None):
        if (worktree == None):
            worktree = repo.directory
        self.git.set_worktree(worktree)
        return self.git.is_valid()

    def update_next(self):
        if (len(self.update_queue) == 0):
            return
        repo = self.update_queue.pop()
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
