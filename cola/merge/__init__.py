import cola
from cola import gitcmds
from cola import qtutils
from cola.merge.view import MergeView


def local_merge():
    """Provides a dialog for merging branches"""
    model = cola.model()
    view = MergeView(model, qtutils.active_window())
    view.show()
    view.raise_()
    return view


def abort_merge():
    """Prompts before aborting a merge in progress
    """
    title = qtutils.tr('Abort Merge...')
    txt = ('Aborting the current merge will cause '
           '*ALL* uncommitted changes to be lost.\n'
           'Recovering uncommitted changes is not possible.')
    info_txt = 'Aborting the current merge?'
    ok_txt = 'Abort Merge'
    if qtutils.confirm(title, txt, info_txt, ok_txt,
                       default=False, icon=qtutils.icon('undo.svg')):
        gitcmds.abort_merge()


if __name__ == '__main__':
    from cola import app

    app = app.ColaApplication([])
    view = local_merge()
    cola.model().update_status()
    app.exec_()
