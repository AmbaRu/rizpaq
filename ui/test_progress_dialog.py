




from __future__ import annotations

from ui.i18n import tr
from ui.operation_progress_dialog import OperationProgressDialog


class TestProgressDialog(OperationProgressDialog):
    pass

    def __init__(
        self,
        archive_name: str = "",
        mode_label: str = "",
        parent=None,
    ):
        title = tr("test.title")

        if archive_name:
            title = f"{title}: {archive_name}"

        super().__init__(title, parent)

        self._mode = "test"
        self._auto_close_on_ok = True

        self.begin_test(archive_name, mode_label)

    def begin_test(
        self,
        archive_name: str = "",
        mode_label: str = "",
    ) -> None:
        pass
        title = tr("test.title")

        if archive_name:
            title = f"{title}: {archive_name}"

        status = mode_label or tr("progress.preparing")
        self.begin(title, status)
