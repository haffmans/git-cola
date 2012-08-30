from cola import gitcfg
from cola import observable
from cola.cmds import BaseCommand


class DashboardModel(observable.Observable):

    def __init__(self):
        observable.Observable.__init__(self)
        self.repos = list()
        self.repos.append(DashboardRepo('/dev/p1'))
        self.repos.append(DashboardRepo('/dev/p2'))
        self.repos.append(DashboardRepo('/dev/p3'))


class DashboardRepo(observable.Observable):
    def __init__(self, path):
        observable.Observable.__init__(self)
        self.path = path
        self.branch = "master"
        self.ahead = +2


command_directory = {
    # DashboardModel.message_set_config: SetConfigCommand,
}
