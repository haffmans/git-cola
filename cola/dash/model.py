from cola import observable

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import QModelIndex

class DashboardModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.repos = list()

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
        self.emit("modelAboutToBeReset()")
        self.repos = list()
        self.emit("modelReset()")

    def add_repo(self, directory):
        index = len(self.repos)
        self.emit(SIGNAL("rowsAboutToBeInserted(QModelIndex, int, int)"), QModelIndex(), index, index)
        self.repos.append(DashboardRepo(directory))
        self.emit(SIGNAL("rowsInserted(QModelIndex, int, int)"), QModelIndex(), index, index)

class DashboardRepo(observable.Observable):
    message_about_to_update = 'about_to_update'
    message_updated         = 'updated'

    def __init__(self, directory):
        observable.Observable.__init__(self)

        self.directory = directory
        self.branch = ''
        self.upstream = ''
        self.diff = 0

    def begin_update(self):
        self.notify_observers(DashboardRepo.message_about_to_update)

    def updated(self):
        self.notify_observers(DashboardRepo.message_updated)
