













from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core import config as config_mod
from ui.i18n import tr
from ui.qt_compat import PASSWORD_ECHO


class NotifyDialog(QDialog):
    pass

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("notify.title"))
        self.resize(580, 320)
        self._saved = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        form = QFormLayout()

        self._mode = QComboBox()
        self._mode.addItem(tr("notify.mode.off"), "off")
        self._mode.addItem(tr("notify.mode.errors"), "errors")
        self._mode.addItem(tr("notify.mode.all"), "all")
        form.addRow(tr("notify.mode.label"), self._mode)

        self._token = QLineEdit()
        self._token.setEchoMode(PASSWORD_ECHO)
        self._token.setPlaceholderText(tr("notify.token.placeholder"))
        form.addRow(tr("notify.token.label"), self._token)

        self._chat = QLineEdit()
        self._chat.setPlaceholderText(tr("notify.chat.placeholder"))
        form.addRow(tr("notify.chat.label"), self._chat)

        lay.addLayout(form)

        hint = QLabel(tr("notify.hint"))
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

        self._load(settings if settings is not None else config_mod.load())

    def _load(self, settings) -> None:
        mode = str(getattr(settings, "notify_mode", "off") or "off").lower()
        index = self._mode.findData(mode)
        self._mode.setCurrentIndex(index if index >= 0 else 0)
        self._token.setText(
            str(getattr(settings, "notify_telegram_token", "") or "")
        )
        self._chat.setText(
            str(getattr(settings, "notify_telegram_chat_id", "") or "")
        )

    def _save(self) -> None:
        pass






        self._saved = config_mod.update(
            notify_mode=str(self._mode.currentData() or "off"),
            notify_telegram_token=self._token.text().strip(),
            notify_telegram_chat_id=self._chat.text().strip(),
        )
        self.accept()

    def saved_settings(self):
        pass
        return self._saved
