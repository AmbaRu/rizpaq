from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.startup_digest import Digest
from ui import skins
from ui.config_bridge import _load_cfg, _merge_cfg
from ui.i18n import tr


def _fmt_when(dt) -> str:

    now = _now_year()
    text = dt.strftime("%d.%m.%Y %H:%M")
    if dt.year == now:
        text = dt.strftime("%d.%m %H:%M")
    return text


def _now_year() -> int:
    import time

    return time.localtime().tm_year


class StartupDigestDialog(QDialog):


    def __init__(self, digest: Digest, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("digest.title"))
        self.setModal(False)
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(6)

        title = QLabel(tr("digest.title"))
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        title.setFont(font)
        lay.addWidget(title)

        if digest.since_dt is not None:
            since = QLabel(tr("digest.since").format(
                when=_fmt_when(digest.since_dt)))
            since.setStyleSheet(
                f"color: {skins.color('TEXT_MUTED')};")
            lay.addWidget(since)

        lay.addSpacing(4)


        for group, ok_n, err_n, busy_n in (
            ("digest.backups", digest.backups_ok, digest.backups_err,
             digest.backups_busy),
            ("digest.tests", digest.tests_ok, digest.tests_err,
             digest.tests_busy),
        ):
            total = ok_n + err_n + busy_n
            if not total:
                continue
            parts = [tr("digest.ok_count").format(n=ok_n)]
            if err_n:
                parts.append(tr("digest.err_count").format(n=err_n))
            if busy_n:
                parts.append(tr("digest.busy_count").format(n=busy_n))
            row = QLabel(f"<b>{tr(group)}</b> — " + ", ".join(parts))
            row.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lay.addWidget(row)

        if digest.has_problem and digest.last_error is not None:
            err = digest.last_error
            when = _fmt_when(err.ts_dt) if err.ts_dt else err.ts
            name = err.job_title or err.work_title or err.job_id
            err_label = QLabel(tr("digest.last_error").format(
                job=name, when=when))
            err_label.setWordWrap(True)
            err_label.setStyleSheet(
                f"color: {skins.color('DIFF_REMOVED')};")
            lay.addSpacing(2)
            lay.addWidget(err_label)

        lay.addSpacing(6)

        self._check = QCheckBox(tr("digest.show_on_start"))
        self._check.setChecked(True)
        lay.addWidget(self._check)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        history_btn = QPushButton(tr("digest.btn.history"))
        history_btn.clicked.connect(self._open_history)
        buttons.addWidget(history_btn)
        ok_btn = QPushButton(tr("digest.btn.ok"))
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        buttons.addWidget(ok_btn)
        lay.addLayout(buttons)

    def _open_history(self):

        parent = self.parent()
        switch = getattr(parent, "_switch_main_page", None)
        if callable(switch):
            try:
                switch("dashboard")
            except Exception:
                pass
        self.accept()

    def accept(self):

        try:
            _merge_cfg(digest_enabled=bool(self._check.isChecked()))
        except Exception:
            pass
        super().accept()


def show_if_needed(host) -> None:
    try:
        cfg = _load_cfg()
    except Exception:
        return
    if not bool(getattr(cfg, "digest_enabled", True)):
        return

    tasks_dir = None
    getter = getattr(host, "_tasks_dir", None)
    if callable(getter):
        try:
            tasks_dir = getter()
        except Exception:
            tasks_dir = None

    from core.startup_digest import collect_digest

    try:
        digest = collect_digest(
            tasks_dir, since=getattr(cfg, "last_close", None))
    except Exception:
        return
    if digest is None:
        return

    dlg = StartupDigestDialog(digest, parent=host)


    try:
        dlg.adjustSize()
        geo = host.geometry()
        dlg.move(geo.x() + geo.width() - dlg.width() - 24,
                 geo.y() + geo.height() - dlg.height() - 48)
    except Exception:
        pass
    dlg.show()


    try:
        host._digest_dialog = dlg
    except Exception:
        pass
