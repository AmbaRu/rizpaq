from __future__ import annotations

import shutil
import tempfile

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.presentation import format_size
from workers.update_worker import UpdateDownloadWorker


class UpdateDialog(QDialog):


    ready_to_install = Signal(dict, str)
    skip_requested = Signal(str)
    auto_check_changed = Signal(bool)

    def __init__(self, info: dict, current_version: str,
                 install_supported: bool = True,
                 auto_check: bool = True, parent=None):
        super().__init__(parent)
        self._info = dict(info or {})
        self._current = str(current_version or "")
        self._install_supported = bool(install_supported)
        self._worker = None
        self._download_dir = None

        self.setWindowTitle(tr("update.title"))
        self.resize(560, 430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.header = QLabel("")
        font = self.font()
        font.setBold(True)
        self.header.setFont(font)
        layout.addWidget(self.header)

        self.version_label = QLabel("")
        layout.addWidget(self.version_label)

        self.published_label = QLabel("")
        layout.addWidget(self.published_label)

        self.notes = QTextBrowser()
        self.notes.setOpenExternalLinks(False)
        self.notes.setPlainText(str(self._info.get("notes") or ""))
        layout.addWidget(self.notes, 1)

        self.warning = QLabel("")
        self.warning.setWordWrap(True)
        layout.addWidget(self.warning)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.auto_check = QCheckBox(tr("update.auto_check"))
        self.auto_check.setChecked(bool(auto_check))
        self.auto_check.toggled.connect(self.auto_check_changed.emit)
        layout.addWidget(self.auto_check)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self.site_btn = QPushButton(tr("update.open_site"))
        self.site_btn.clicked.connect(self._open_site)
        buttons.addWidget(self.site_btn)

        self.later_btn = QPushButton(tr("update.later"))
        self.later_btn.clicked.connect(self._on_later)
        buttons.addWidget(self.later_btn)

        self.install_btn = QPushButton(tr("update.install"))
        self.install_btn.setDefault(True)
        self.install_btn.clicked.connect(self._on_install)
        buttons.addWidget(self.install_btn)

        layout.addLayout(buttons)

        self._fill()


    def _fill(self) -> None:
        version = str(self._info.get("version") or "")
        self.header.setText(tr("update.available", version=version))
        self.version_label.setText(
            tr("update.current", current=self._current, latest=version))
        published = str(self._info.get("published") or "").strip()
        if published:
            self.published_label.setText(
                tr("update.published", date=published))
        else:
            self.published_label.setVisible(False)
        if not self._info.get("sha256"):
            self.warning.setText(tr("update.no_sha256"))
        if not self._install_supported:
            self.warning.setText(tr("update.install_only_built"))
            self.install_btn.setText(tr("update.download"))


    def _open_site(self) -> None:
        url = str(self._info.get("notes_url")
                  or self._info.get("url") or "")
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))

    def _on_later(self) -> None:
        self.skip_requested.emit(str(self._info.get("version") or ""))
        self.reject()

    def _on_install(self) -> None:
        if not self._install_supported:
            self._open_site()
            return
        if self._worker is not None:
            return

        self._download_dir = tempfile.mkdtemp(prefix="rizpaq_update_dl_")
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText(tr("update.downloading"))
        self.install_btn.setEnabled(False)
        self.later_btn.setEnabled(False)

        worker = UpdateDownloadWorker(
            self._info, self._download_dir, parent=self)
        worker.progress.connect(self._on_progress)
        worker.done.connect(self._on_download_done)
        self._worker = worker
        worker.start()

    def _on_progress(self, info: dict) -> None:
        total = int(info.get("total") or 0)
        read = int(info.get("read") or 0)
        if total:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(info.get("percent") or 0))
            self.status.setText(tr(
                "update.progress",
                done=format_size(read), total=format_size(total),
            ))
        else:
            self.progress.setRange(0, 0)
            self.status.setText(tr("update.progress_unknown",
                                   done=format_size(read)))

    def _on_download_done(self, result: dict) -> None:
        worker = self._worker
        if worker is not None:
            try:
                worker.wait(2000)
            except Exception:
                pass
        self._worker = None

        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        self.install_btn.setEnabled(True)
        self.later_btn.setEnabled(True)

        if result.get("cancelled"):
            self.status.setText(tr("update.cancelled"))
            return
        if not result.get("ok"):
            self.status.setText("")
            QMessageBox.warning(
                self, tr("update.error_title"),
                tr("update.error_text", error=result.get("error") or ""),
            )
            return

        self.status.setText(tr("update.ready"))
        self.ready_to_install.emit(self._info, str(result.get("path") or ""))


    def discard_download(self) -> None:
        if self._download_dir:
            shutil.rmtree(self._download_dir, ignore_errors=True)
            self._download_dir = None

    def closeEvent(self, event) -> None:
        worker = self._worker
        if worker is not None:
            worker.cancel_request()
            try:
                worker.wait(5000)
            except Exception:
                pass
            self._worker = None
        self.discard_download()
        super().closeEvent(event)

    def download_dir(self) -> str:

        return str(self._download_dir or "")
