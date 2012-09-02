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

        self.directory = directory
        self.branch = ''
        self.upstream = ''
        self.diff = 0

    def begin_update(self):
        self.notify_observers(DashboardRepo.message_about_to_update)

    def updated(self):
        self.notify_observers(DashboardRepo.message_updated)

command_directory = {
    # DashboardModel.message_set_config: SetConfigCommand,
}
