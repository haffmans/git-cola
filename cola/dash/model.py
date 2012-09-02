from cola import git
from cola import gitcmds
from cola import observable


class DashboardModel(observable.Observable):

    def __init__(self):
        observable.Observable.__init__(self)
        self.repos = list()
        self.repos.append(DashboardRepo('/dev/p1'))
        self.repos.append(DashboardRepo('/dev/p2'))
        self.repos.append(DashboardRepo('/dev/p3'))


class DashboardRepo(observable.Observable):
    message_about_to_update = 'about_to_update'
    message_updated         = 'updated'

    def __init__(self, directory):
        observable.Observable.__init__(self)

        # Initialize the git command object
        self.git = git.instance()

        self.directory = directory
        self.branch = ''
        self.upstream = ''
        self.diff = 0

    def set_worktree(self, worktree=None):
        if worktree == None:
            worktree = self.directory
        self.git.set_worktree(worktree)
        return self.git.is_valid()

    def update_status(self):
        if not self.set_worktree():
            return False
        self.notify_observers(message_about_to_update)
        status = gitcmds.head_tracking_status()
        self.branch = status.get('head')
        self.upstream = status.get('upstream')
        self.diff = int(status.get('amount')) if status.get('status') == 'ahead' else  - int(status.get('amount'))
        self.notify_observers(message_updated)

command_directory = {
    # DashboardModel.message_set_config: SetConfigCommand,
}
