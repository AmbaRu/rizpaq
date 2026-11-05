from __future__ import annotations

from ui.i18n import tr
from ui.operation_progress_dialog import OperationProgressDialog


class Par2OperationDialog(OperationProgressDialog):

    def __init__(self, title: str, status: str, archive_name: str,
                 parent=None):
        window_title = title
        if archive_name:
            window_title = f"{title}: {archive_name}"
        super().__init__(window_title, parent)

        self._mode = "par2"

        self._auto_close_on_ok = False

        self.hide_info_fields(keep=("elapsed",))
        self.begin(window_title, status)

    def append_log(self, log: str) -> None:
        if not log:
            return
        for line in str(log).splitlines():
            self.append_output(line)

    def finish_verdict(self, ok: bool, verdict: str, log: str = "",
                       detail: str = "") -> None:
        self.append_log(log)
        super().finish(ok, detail)
        self._title.setText(verdict)
        self._title.setProperty("state", "ok" if ok else "err")
        self._repolish(self._title)
        if not detail:
            self._current.setText("")


class Par2VerifyDialog(Par2OperationDialog):


    def __init__(self, archive_name: str = "", parent=None):
        super().__init__(
            tr("par2.test_mode"), tr("par2.verify_running"),
            archive_name, parent,
        )


class Par2CreateDialog(Par2OperationDialog):


    def __init__(self, archive_name: str = "", parent=None):
        super().__init__(
            tr("par2.create_title"), tr("par2.create_running"),
            archive_name, parent,
        )


class Par2RepairDialog(Par2OperationDialog):

    def __init__(self, archive_name: str = "", parent=None):
        super().__init__(
            tr("par2.repair_title"), tr("par2.repair_checking"),
            archive_name, parent,
        )

    def begin_repair(self) -> None:

        self._current.setText(tr("par2.repair_running"))
