




from __future__ import annotations

from ui.i18n import tr
from ui.operation_progress_dialog import OperationProgressDialog


class ArchiveProgressDialog(OperationProgressDialog):
    pass

    def __init__(self, archive_name: str, parent=None):
        title = f"{tr('create.progress_title')}: {archive_name}"

        super().__init__(title, parent)

        self._mode = "archive"
        self.setModal(True)

        self.begin(title, tr("progress.preparing"))

    def finish(self, ok: bool, name: str = "", stay: bool = False) -> None:
        pass








        super().finish(ok, name or "")
        if not stay:
            self.accept()

    def begin_par2_stage(self, archive_name: str) -> None:
        pass














        self.next_stage(
            tr("progress.par2_stage", name=archive_name),
            tr("progress.par2_running"),
        )
        self.hide_info_fields(keep=("elapsed",))
