from cola.dash.view import DashboardView
from cola.dash.model import DashboardModel
from cola.dash.controller import DashboardController


def dashboard(model=None):
    if model is None:
        model = DashboardModel()
    dash = DashboardView(model)
    ctl = DashboardController(model, dash)
    dash.show()
    dash.raise_()
    return ctl
