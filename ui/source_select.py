


from __future__ import annotations

from ui.source_select_window import SourceSelectWindow


class SourceSelectMixin:
    pass

    def _on_source_select(self):
        dlg = SourceSelectWindow(parent=self)
        dlg.exec()
