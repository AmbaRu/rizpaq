
















from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from ui.i18n import tr

                                                                  
                                                               


class SalvageOptionsDialog(QDialog):
    pass

    def __init__(self, archive_name: str = "", parent=None):
        super().__init__(parent)

        title = tr("salvage.dialog_title")
        if archive_name:
            title = f"{title}: {archive_name}"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)

        intro = QLabel(tr("salvage.intro"))
        intro.setWordWrap(True)
        lay.addWidget(intro)

        ram_row = QLabel(tr("salvage.ram_label"))
        lay.addWidget(ram_row)

        self.ram = QComboBox()
        for gb in (1, 2, 4, 8):
            self.ram.addItem(tr("salvage.ram_gb").format(gb=gb), gb)
                                                           
        lay.addWidget(self.ram)

        warn = QLabel(tr("salvage.warn_partial"))
        warn.setWordWrap(True)
        lay.addWidget(warn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Ok).setText(
            tr("salvage.start_button")
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def ram_gb(self) -> int:
        pass
        return self.ram.currentData()
