from cola.ctrl import Controller

from cola import git
from cola import gitcmds
from cola import settings
from PyQt4.QtCore import QTimer

class DashboardController(Controller):
    def __init__(self, model, view):
        Controller.__init__(self, model, view)
        self.settingsModel = settings.Settings()
        for bookmark in self.settingsModel.bookmarks:
            self.model.add_repo(bookmark)

        view.shown.connect(self.update_all)

        # Initialize the git command object
        self.git = git.instance()
        self.update_queue = list()

    def set_worktree(self, repo, worktree=None):
        if (worktree == None):
            worktree = repo.directory
        self.git.set_worktree(worktree)
        return self.git.is_valid()

    def update_all(self):
        del self.update_queue[:]
        self.update_queue.extend(self.model.repos)
        self.update_queue.reverse()
        QTimer.singleShot(10, self.update_next)

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