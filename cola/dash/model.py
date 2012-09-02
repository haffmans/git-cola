from cola import observable

class DashboardModel(observable.Observable):
    message_about_to_add_row = 'about_to_add_row'
    message_added_row = 'added_row'

    def __init__(self):
        observable.Observable.__init__(self)
        self.repos = list()

    def add_repo(self, directory):
        self.notify_observers(DashboardModel.message_about_to_add_row)
        self.repos.append(DashboardRepo(directory))
        self.notify_observers(DashboardModel.message_added_row, len(self.repos)-1)


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
