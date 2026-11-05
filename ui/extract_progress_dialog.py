from __future__ import annotations

from ui.i18n import tr
from ui.operation_progress_dialog import (
    OperationProgressDialog,
    _elide_mid,
)


class ExtractProgressDialog(OperationProgressDialog):


    def __init__(self, parent=None):
        super().__init__(tr("progress.title"), parent)

        self._mode = "extract"
        self._auto_close_on_ok = True


    def begin_file(self, name: str = "") -> None:

        self._mode = "single"
        self.begin(tr("progress.title_file"), _elide_mid(name or "", 140))

    def begin_folder(self, total: int) -> None:

        self._mode = "files"

        self.begin(tr("progress.title_folder"), tr("progress.preparing"))

        try:
            total = max(int(total or 0), 0)
        except Exception:
            total = 0

        self._bar.setRange(0, max(total, 1))
        self._bar.setValue(0)
        self._files_label.setText(f"0 / {total}")

    def begin_batch(self) -> None:

        self._mode = "batch"
        self.begin(tr("progress.title_folder"), tr("progress.batch_pass"))

    def finish(self, ok: bool, msg: str = "") -> None:

        super().finish(ok, msg or "")
