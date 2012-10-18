from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import QModelIndex

from cola import git
from cola import gitcfg
from cola import gitcmds
from cola import settings

class DashboardModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._storage = settings.Settings()
        self._repos = list()

        # Initialize the git command object
        self._git = git.instance()

        for bookmark in self._storage.bookmarks:
            self._repos.append(DashboardRepo(bookmark))

    def rowCount(self, parent=QModelIndex()):
        return len(self._repos)

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
        repo = self._repos[index.row()]

        if (not index.isValid()):
            return QVariant()

        if (role == Qt.DisplayRole):
            if (index.column() == 0):
                return QVariant(repo.directory)
            elif (index.column() == 1):
                return QVariant(repo.branch)
            elif (index.column() == 2):
                return QVariant(repo.upstream)
            elif (index.column() == 3):
                return QVariant(repo.diff)

        elif (role == Qt.ToolTipRole):
            if (index.column() == 0):
                return QVariant(repo.directory)
            elif (index.column() == 1):
                return QVariant(repo.branch)
            elif (index.column() == 2):
                return QVariant(repo.upstream)
            elif (index.column() == 3):
                if (repo.diff > 0):
                    return QVariant(str(repo.diff) + " commits ahead of upstream")
                elif (repo.diff < 0):
                    return QVariant(str(repo.diff) + " commits behind upstream")
                return QVariant("Not ahead of or behind upstream")

        elif (role == Qt.FontRole):
            font = QtGui.QFont()
            if (index.column() == 0):
                font.setBold(True)
            elif (index.column() == 1):
                pass
            elif (index.column() == 2):
                pass
            elif (index.column() == 3):
                font.setBold(True)
            return font

        elif (role == Qt.ForegroundRole):
            if (index.column() == 1):
                pass
            if (index.column() == 2):
                pass
            if (index.column() == 3):
                if (repo.diff == '...'):
                    return QVariant()
                elif (repo.diff > 0):
                    # Green
                    return QtGui.QBrush(self._compute_color(120/360.0, 1, 1, index.row()))
                elif (repo.diff < 0):
                    # Red
                    return QtGui.QBrush(self._compute_color(0/360.0, 1, 1, index.row()))
                else:
                    # Yellow
                    return QtGui.QBrush(self._compute_color(60/360.0, 1, 1, index.row()))

        return QVariant()

    def _compute_color(self, hue, saturation, alpha, row):
        palette = QtGui.QPalette()
        background = palette.color(QtGui.QPalette.Base).toHsl() if (row % 2 == 0) else palette.color(QtGui.QPalette.AlternateBase).toHsl()
        if (background.lightnessF() <= .50):
            # .50-.75
            light = max(.50, .50 + ((background.lightnessF()-.25)/1.2))
        else:
            light = min(.25, .125 + ((background.lightnessF()-.5)/2.5))

        return QtGui.QColor.fromHslF(hue, saturation, light, alpha)

    def clear(self):
        """ Remove all repositories from the model. """
        self.emit("modelAboutToBeReset()")
        del self._repos[:]
        self.emit("modelReset()")

    def save(self):
        del self._storage.bookmarks[:]
        self._storage.bookmarks.extend([ r.directory for r in self._repos ])
        self._storage.save()

    def add_repo(self, directory, load_status=True):
        """ Adds a new repository to the model (by directory) and returns the row number.
            The actual added directory may be a parent of the input; the root of
            the git repository is detected and added.

            Returns -1 if the directory is already added to the model. Returns
            -2 if the directory is not a valid git repository.
        """

        # Find git repository base
        valid = False

        # Check if git repo
        self._git.set_worktree(directory)
        if (not self._git.is_valid()):
            return -2

        directory = self._git.worktree()

        # Check if already added
        if (any([r.directory == directory for r in self._repos])):
            return -1

        index = len(self._repos)
        self.beginInsertRows(QModelIndex(), index, index)
        self._repos.append(DashboardRepo(directory))
        if (load_status):
            self._load_status(self._repos[index])

        self.endInsertRows()
        return index

    def delete_repo(self, directory):
        for i in [ x for x in range(len(self._repos) - 1, -1, -1) if (self._repos[x].directory == directory) ]:
            self.beginRemoveRows(QModelIndex(), i, i)
            del self._repos[i]
            self.endRemoveRows()

    def row_of(self, directory):
        return next((i for i, v in enumerate(self._repos) if v.directory == directory), -1)

    def update(self, row):
        """ Update a repository's status at the given row. """
        task = ActionTask(self._update, row)
        QtCore.QThreadPool.globalInstance().start(task)

    def _update(self, row):
        if (row < 0 or row >= len(self._repos)):
            self.emit(SIGNAL('update_complete(int)'), row)
            return
        if self._load_status(self._repos[row]):
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.index(row, 1), self.index(row, self.columnCount()))
        self.emit(SIGNAL('update_complete(int)'), row)

    def _set_worktree(self, repo, worktree=None):
        if (worktree is None):
            worktree = repo.directory
        self._git.set_worktree(worktree)
        return self._git.is_valid()

    def _load_status(self, repo):
        if not self._set_worktree(repo):
            return False

        gitcfg.instance().reset()
        status = gitcmds.head_tracking_status()
        if (status is None):
            return False
        repo.branch = status.get('head')
        repo.upstream = status.get('upstream')
        repo.diff = int(status.get('amount')) if status.get('status') == 'ahead' else  - int(status.get('amount'))
        return True

    def fetch(self, row):
        task = ActionTask(self._fetch, row)
        QtCore.QThreadPool.globalInstance().start(task)

    def _fetch(self, row):
        if (row < 0 or row >= len(self._repos)):
            self.emit(SIGNAL('fetch_complete(int)'), row)
            return False
        repo = self._repos[row]
        if (not repo.upstream):
            self.emit(SIGNAL('fetch_complete(int)'), row)
            return False
        if not self._set_worktree(repo):
            self.emit(SIGNAL('fetch_complete(int)'), row)
            return False

        repo.diff = '...'
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.index(row, 3), self.index(row, 3))

        # Call git fetch
        (remote, refspec) = repo.upstream.split('/', 1)
        self._git.fetch(remote, refspec)
        self._update(row)
        self.emit(SIGNAL('fetch_complete(int)'), row)

    def abort_tasks(self):
        QtCore.QThreadPool.globalInstance().waitForDone()

class ActionTask(QtCore.QRunnable):
    def __init__(self, method, row):
        QtCore.QRunnable.__init__(self)
        self.method = method
        self.row = row

    def run(self):
        """Runs the model action and captures the result"""
        self.method(self.row)

class DashboardRepo:
    """ Simple structure representing a repository's status. """
    def __init__(self, directory):
        self.directory = directory
        self.branch = '...'
        self.upstream = '...'
        self.diff = '...'
