from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import QModelIndex

from cola import git
from cola import gitcmds

class DashboardModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.repos = list()

        # Initialize the git command object
        self._git = git.instance()

    def rowCount(self, parent=QModelIndex()):
        return len(self.repos)

    def columnCount(self, parent=QModelIndex()):
        return 4 if not parent.isValid() else 0

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if (role != Qt.DisplayRole or orientation != Qt.Horizontal):
            return QVariant()
        if (section == 0):
            return QVariant("Directory")
        if (section == 1):
            return QVariant("Branch")
        if (section == 2):
            return QVariant("Upstream")
        if (section == 3):
            return QVariant("Difference")
        return QVariant()

    def data(self, index, role = Qt.DisplayRole):
        repo = self.repos[index.row()]
        if (role != Qt.DisplayRole):
            return QVariant()

        if (index.column() == 0):
            return QVariant(repo.directory)
        if (index.column() == 1):
            return QVariant(repo.branch)
        if (index.column() == 2):
            return QVariant(repo.upstream)
        if (index.column() == 3):
            return QVariant(repo.diff)

    def clear(self):
        """ Remove all repositories from the model. """
        self.emit("modelAboutToBeReset()")
        self.repos = list()
        self.emit("modelReset()")

    def add_repo(self, directory, load_status=True):
        """ Adds a new repository to the model (by directory) and returns the row number.

            The repository's data is not initialized; use update(row) to retrieve
            the full status
        """
        index = len(self.repos)
        self.emit(SIGNAL("rowsAboutToBeInserted(QModelIndex, int, int)"), QModelIndex(), index, index)
        self.repos.append(DashboardRepo(directory))
        if (load_status):
            self._load_status(self.repos[index])

        self.emit(SIGNAL("rowsInserted(QModelIndex, int, int)"), QModelIndex(), index, index)
        return index

    def update(self, row):
        """ Update a repository's status at the given row. """
        if (row < 0 or row >= len(self.repos)):
            return
        self._load_status(self.repos[row])
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex'), self.index(row, 1), self.index(row, self.columnCount()))

    def _set_worktree(self, repo, worktree=None):
        if (worktree == None):
            worktree = repo.directory
        self._git.set_worktree(worktree)
        return self._git.is_valid()

    def _load_status(self, repo):
        if not self._set_worktree(repo):
            return False

        status = gitcmds.head_tracking_status()
        repo.branch = status.get('head')
        repo.upstream = status.get('upstream')
        repo.diff = int(status.get('amount')) if status.get('status') == 'ahead' else  - int(status.get('amount'))

class DashboardRepo:
    """ Simple structure representing a repository's status. """
    def __init__(self, directory):
        self.directory = directory
        self.branch = ''
        self.upstream = ''
        self.diff = 0
