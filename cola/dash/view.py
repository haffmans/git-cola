import os

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from cola import qtutils
from cola import gitcfg
from cola.qtutils import relay_signal
from cola.widgets import defs
from cola.widgets import standard

class StatusWidget(standard.Widget):
    def __init__(self, repo, parent=None):
        standard.Widget.__init__(self, parent=parent)

        self._path = QtGui.QLabel()
        self._path.setText("<b>" + repo.path + "</b>")

        self._branch = QtGui.QLabel()
        self._branch.setText(repo.branch)

        self._ahead = QtGui.QLabel()
        color = "#00ff00" if repo.ahead > 0 else "#0000ff" if repo.ahead == 0 else "#ff0000"
        aheadstr = ('%+d' % repo.ahead)
        self._ahead.setText("<b><font color=\"" + color + "\">" + aheadstr + "</font></b>")
        print aheadstr

        self._layt = QtGui.QHBoxLayout()
        self._layt.setMargin(defs.margin)
        self._layt.setSpacing(defs.spacing)
        self._layt.addWidget(self._path)
        self._layt.addWidget(self._branch)
        self._layt.addWidget(self._ahead)
        self.setLayout(self._layt)

class DashboardView(standard.Widget):
    def __init__(self, model, parent=None):
        standard.Widget.__init__(self, parent=parent)
        self.setWindowTitle(self.tr('Dashboard'))
        self.resize(600, 360)

        self._layt = QtGui.QVBoxLayout()

        for repo in model.repos:
            self._layt.addWidget(StatusWidget(repo, self))

        self.setLayout(self._layt)


if __name__ == "__main__":
    import sys
    from cola.prefs import preferences

    app = QtGui.QApplication(sys.argv)
    dashboard()
    sys.exit(app.exec_())
