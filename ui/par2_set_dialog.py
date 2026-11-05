from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.par2_options import Par2OptionsWidget


_LAST_OPTIONS: dict = {}


def last_options() -> dict:
    return dict(_LAST_OPTIONS)


def remember_options(options: dict) -> None:
    global _LAST_OPTIONS
    _LAST_OPTIONS = dict(options or {})


class Par2SetDialog(QDialog):


    def __init__(self, archive_name: str = "", options: dict = None,
                 parent=None):
        super().__init__(parent)

        title = tr("par2.set_dialog_title")
        if archive_name:
            title = f"{title}: {archive_name}"
        self.setWindowTitle(title)
        self.setModal(True)

        lay = QVBoxLayout(self)

        self.widget = Par2OptionsWidget(show_master=False)
        self.widget.apply(options or {})


        self.widget.intro.setVisible(True)


        scroll = QScrollArea()
        scroll.setWidget(self.widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        lay.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Ok).setText(tr("par2.set_create"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("progress.cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def options(self) -> dict:

        return self.widget.collect()
