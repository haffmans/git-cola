import os
from collections import deque

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QTimer

from cola import qtutils
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
        self.setAlternatingRowColors(True)

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
            # Delay updating to after show()
            self._model.add_repo(bookmark, False)

        # Init table
        self.connect(self._table, SIGNAL('activated(QModelIndex)'), self.open_bookmark)

        # Init layout
        self._layt.addWidget(self._table)
        self.setLayout(self._layt)

        self._update_queue = deque()

    def open_bookmark(self, index):
        directory_index = index.sibling(index.row(), 0)
        directory = self._model.data(directory_index).toString()
        self.emit(SIGNAL('open(QString)'), directory)

    def showEvent(self, event):
        # Delay-load all repos
        self._update_queue.clear()
        self._update_queue.extend(range(self._model.rowCount()))
        QTimer.singleShot(10, self.update_next)

    def update_next(self):
        if (len(self._update_queue) == 0):
            return
        repo = self._update_queue.popleft()
        self._model.update(repo)
        QTimer.singleShot(10, self.update_next)

if __name__ == "__main__":
    import sys
    from cola.prefs import preferences

    app = QtGui.QApplication(sys.argv)
    view = dashboard()
    sys.exit(app.exec_())
