import os

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QTimer

from cola import qtutils
from cola import gitcfg
from cola.qtutils import relay_signal
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

        for repo in model.repos:
            self._layt.addWidget(StatusWidget(repo, self))

        self.setLayout(self._layt)

    def showEvent(self, event):
        self.shown.emit()


if __name__ == "__main__":
    import sys
    from cola.prefs import preferences

    app = QtGui.QApplication(sys.argv)
    dashboard()
    sys.exit(app.exec_())
