import os
import sys
from collections import deque

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QThread
from PyQt4.QtCore import QTimer

from cola import qtutils
from cola import settings
from cola import utils
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

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self._openAction = QtGui.QAction(self.tr("Open"), self)
        self.connect(self._openAction, SIGNAL('triggered()'), self.open_current)
        self.addAction(self._openAction)

        self._openNewAction = QtGui.QAction(self.tr("Open in new window"), self)
        self.connect(self._openNewAction, SIGNAL('triggered()'), self.open_current_new)
        self.addAction(self._openNewAction)

        self._fetch_upstream = QtGui.QAction(self.tr("Fetch upstream"), self)
        self.connect(self._fetch_upstream, SIGNAL('triggered()'), self.fetch_current)
        self.addAction(self._fetch_upstream)

        self._unbookmark = QtGui.QAction(self.tr("Delete bookmark"), self)
        self.connect(self._unbookmark, SIGNAL('triggered()'), self.delete_current)
        self.addAction(self._unbookmark)

    def open_current(self):
        if (len(self.selected_rows()) > 0):
            row = self.selected_rows()[0]
            self.emit(SIGNAL('open_bookmark(QString)'), self.repo_dir(row))

    def open_current_new(self):
        for row in self.selected_rows():
            self.emit(SIGNAL('open_bookmark_new_window(QString)'), self.repo_dir(row))

    def fetch_current(self):
        for row in self.selected_rows():
            self.emit(SIGNAL('fetch(QString)'), self.repo_dir(row))

    def delete_current(self):
        for row in self.selected_rows():
            self.emit(SIGNAL('delete(QString)'), self.repo_dir(row))

    def selected_rows(self):
        return sorted(set([i.row() for i in self.selectedIndexes()]))

    def repo_dir(self, row):
        return self.model().data(self.model().index(row, 0)).toString()

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

    def set_actions_enabled(self, enabled):
        self._fetch_upstream.setEnabled(enabled)
        self._unbookmark.setEnabled(enabled)

class DashboardView(standard.Widget):
    def __init__(self, model, parent=None):
        standard.Widget.__init__(self, parent=parent)
        self.setWindowTitle(self.tr('Dashboard'))
        self.resize(600, 360)
        self._layt = QtGui.QVBoxLayout()

        self._model = model
        self._table = StatusTable(self._model)

        # Connect model results
        self.connect(self._model, SIGNAL('update_complete(int)'), self.update_next)
        self.connect(self._model, SIGNAL('fetch_complete(int)'), self.fetch_next)

        # Init table
        self.connect(self._table, SIGNAL('activated(QModelIndex)'), self.open_bookmark)
        self.connect(self._table, SIGNAL('open_bookmark(QString)'), SIGNAL('open(QString)'))
        self.connect(self._table, SIGNAL('open_bookmark_new_window(QString)'), self.open_new_window)
        self.connect(self._table, SIGNAL('fetch(QString)'), self.fetch)
        self.connect(self._table, SIGNAL('delete(QString)'), self.delete_bookmark)

        # Action bar at top (buttons)
        self._actionlayt = QtGui.QHBoxLayout()
        self._new_bookmark = QtGui.QPushButton(self.tr("New bookmark..."), self)
        self._new_bookmark.setIcon(qtutils.icon('add.svg'))
        self.connect(self._new_bookmark, SIGNAL('clicked()'), self.add_bookmark)
        self._update_all = QtGui.QPushButton(self.tr("Fetch all..."), self)
        self._update_all.setIcon(qtutils.icon('view-refresh.svg'))
        self.connect(self._update_all, SIGNAL('clicked()'), self.fetch_all)
        self._actionlayt.addWidget(self._new_bookmark)
        self._actionlayt.addWidget(self._update_all)
        self._actionlayt.setAlignment(self._new_bookmark, QtCore.Qt.AlignLeft)
        self._actionlayt.setAlignment(self._update_all, QtCore.Qt.AlignRight)

        # Init layout
        self._layt.addLayout(self._actionlayt)
        self._layt.addWidget(self._table)
        self.setLayout(self._layt)

        self._update_running = False
        self._update_queue = deque()
        self._fetch_running = False
        self._fetch_queue = deque()

        self._last_open_dir = os.getcwd()

    def apply_state(self, state):
        try:
            if (state['horizontalHeader']):
                self._table.horizontalHeader().restoreState(
                    QtCore.QByteArray.fromBase64(str(state['horizontalHeader']))
                )
        except:
            pass

        try:
            if (state['last_open_dir'] and os.path.isdir(state['last_open_dir'])):
                self._last_open_dir = state['last_open_dir']
        except:
            pass

    def export_state(self):
        return {
            'horizontalHeader': unicode(self._table.horizontalHeader().saveState().toBase64().data()),
            'last_open_dir': self._last_open_dir,
        }

    def add_bookmark(self):
        path = qtutils.opendir_dialog(self.tr("Add a bookmark..."), self._last_open_dir)
        if (len(path) == 0):
            return
        index = self._model.add_repo(path, False)

        if (index >= 0):
            # Get final directory
            path = str(self._model.data(self._model.index(index, 0)).toString())
            self._last_open_dir = os.path.dirname(path)
            self._model.save()

            # Update row
            self._update_queue.append(index)
            if (not self._update_running):
                self.update_next()

        elif (index == -1):
            qtutils.information(self.tr("Add a bookmark"), self.tr("Repository already bookmarked"))
        elif (index == -2):
            qtutils.information(self.tr("Add a bookmark"), self.tr("Directory is not a git repository"))

    def delete_bookmark(self, directory):
        self._model.delete_repo(directory)
        self._model.save()

    def open_new_window(self, directory):
        utils.fork([sys.executable, sys.argv[0], '--repo', str(directory)])

    def fetch_all(self):
        self._fetch_queue.clear()
        self._fetch_queue.extend(range(self._model.rowCount()))
        self.fetch_next()

    def fetch(self, repo):
        row = self._model.row_of(str(repo))
        if (row < 0 or any([r for r in self._fetch_queue if r == row])):
            return
        self._fetch_queue.append(row)
        if (not self._fetch_running):
            self.fetch_next()

    def open_bookmark(self, index):
        self.abort_tasks()
        directory_index = index.sibling(index.row(), 0)
        directory = self._model.data(directory_index).toString()
        self.emit(SIGNAL('open(QString)'), directory)

    def showEvent(self, event):
        # Delay-load all repos
        self._update_queue.clear()
        self._update_queue.extend(range(self._model.rowCount()))
        self.update_next()

    def update_next(self):
        if (len(self._update_queue) == 0):
            self._update_running = False
            self.enable_actions()
            return
        self._update_running = True
        self.enable_actions()
        repo = self._update_queue.popleft()
        self._model.update(repo)

    def fetch_next(self):
        if (len(self._fetch_queue) == 0):
            self._fetch_running = False
            self.enable_actions()
            return
        self._fetch_running = True
        self.enable_actions()
        repo = self._fetch_queue.popleft()
        self._model.fetch(repo)

    def enable_actions(self):
        enabled = (not (self._update_running or self._fetch_running))
        self._new_bookmark.setEnabled(enabled)
        self._update_all.setEnabled(enabled)
        self._table.set_actions_enabled(enabled)

    def abort_tasks(self):
        self._update_queue.clear()
        self._fetch_queue.clear()
        self._model.abort_tasks()


if __name__ == "__main__":
    import sys
    from cola.prefs import preferences

    app = QtGui.QApplication(sys.argv)
    view = dashboard()
    sys.exit(app.exec_())
