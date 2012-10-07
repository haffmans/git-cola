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
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.initialFirstSize = -1
        self.resizing = False
        self.connect(self.horizontalHeader(), SIGNAL('sectionResized(int, int, int)'), self.horizontal_section_resized);

    def resizeEvent(self, event):
        header = self.horizontalHeader();
        currentWidth = sum([header.sectionSize(i) for i in range(header.count())]) + (2*self.frameWidth())

        QtGui.QTableView.resizeEvent(self, event)

        if (self.initialFirstSize == -1):
            self.initialFirstSize = header.sectionSize(0)

        diff = event.oldSize().width() - event.size().width()

        if ((currentWidth >= event.size().width() and diff < 0) or
            (currentWidth - diff < event.size().width() and diff > 0) or
            event.oldSize().width() == -1):
            return

        self.resizing = True
        firstSize = self.horizontalHeader().sectionSize(0)
        self.horizontalHeader().resizeSection(0, max(firstSize - diff, self.initialFirstSize))

        self.update()
        self.resizing = False

    def horizontal_section_resized(self, index, oldSize, newSize):
        if (self.resizing or index != 0):
            return
        self.initialFirstSize = newSize

class DashboardView(standard.Widget):
    def __init__(self, model, parent=None):
        standard.Widget.__init__(self, parent=parent)
        self.setWindowTitle(self.tr('Dashboard'))
        self.resize(600, 360)
        self._layt = QtGui.QVBoxLayout()

        self._model = model
        self._table = StatusTable(self._model)

        # Init table
        self.connect(self._table, SIGNAL('activated(QModelIndex)'), self.open_bookmark)

        # Action bar at top (buttons)
        self._actionlayt = QtGui.QHBoxLayout()
        self._new_bookmark = QtGui.QPushButton(self.tr("New bookmark..."), self)
        self._new_bookmark.setIcon(qtutils.icon('add.svg'))
        self.connect(self._new_bookmark, SIGNAL('clicked()'), self.add_bookmark)
        self._actionlayt.addWidget(self._new_bookmark)
        self._actionlayt.setAlignment(self._new_bookmark, QtCore.Qt.AlignLeft)

        # Init layout
        self._layt.addLayout(self._actionlayt)
        self._layt.addWidget(self._table)
        self.setLayout(self._layt)

        self._update_queue = deque()

    def apply_state(self, state):
        if (state['horizontalHeader']):
            self._table.horizontalHeader().restoreState(
                QtCore.QByteArray.fromBase64(str(state['horizontalHeader']))
            )

    def export_state(self):
        return {
            'horizontalHeader': unicode(self._table.horizontalHeader().saveState().toBase64().data())
        }

    def add_bookmark(self):
        path = qtutils.opendir_dialog(self.tr("Add a bookmark..."), os.getcwd())
        if (len(path) == 0):
            return
        index = self._model.add_repo(path)

        if (index >= 0):
            self._model.save()
        elif (index == -1):
            qtutils.information(self.tr("Add a bookmark"), self.tr("Repository already bookmarked"))
        elif (index == -2):
            qtutils.information(self.tr("Add a bookmark"), self.tr("Directory is not a git repository"))


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
