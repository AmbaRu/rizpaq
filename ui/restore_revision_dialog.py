










from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)

from ui.i18n import tr

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY_FORMAT = "%Y-%m-%d"


def normalize_date(value: str) -> str:
    pass






    text = (value or "").strip()
    if not text:
        raise ValueError("empty date")
    for fmt in (DATE_FORMAT, DAY_FORMAT):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == DAY_FORMAT:
            parsed = parsed.replace(hour=23, minute=59, second=59)
        return parsed.strftime(DATE_FORMAT)
    raise ValueError("invalid date format: " + text)


class RestoreRevisionDialog(QDialog):
    pass

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("restore.rev.title"))

        self.date_radio = QRadioButton(tr("restore.rev.mode_date"), self)
        self.all_radio = QRadioButton(tr("restore.rev.mode_all"), self)
        self.date_radio.setChecked(True)

        self.date_edit = QLineEdit(self)
        self.date_edit.setPlaceholderText(tr("restore.rev.date_hint"))
        self.date_radio.toggled.connect(self.date_edit.setEnabled)

        layout = QVBoxLayout(self)
        layout.addWidget(self.date_radio)
        form = QFormLayout()
        form.addRow(QLabel(tr("restore.rev.date_label"), self), self.date_edit)
        layout.addLayout(form)
        layout.addWidget(self.all_radio)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def mode(self) -> str:
        return "all" if self.all_radio.isChecked() else "date"

    def until(self) -> str:
        pass
        if self.mode() == "all":
            return ""
        return normalize_date(self.date_edit.text())
