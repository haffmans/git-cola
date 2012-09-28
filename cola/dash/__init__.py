from cola.dash.view import DashboardView
from cola.dash.model import DashboardModel

def dashboard(model=None, parent=None):
    if model is None:
        model = DashboardModel()
    dash = DashboardView(model)
    dash.show()
    dash.raise_()
    return dash
