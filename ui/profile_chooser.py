from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ui.i18n import tr
from ui.profile_bridge import DEFAULT_PROFILE, PROFILES, profile_title


class ProfileChooserDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("profile_chooser.title"))
        self.setMinimumWidth(480)
        self._chosen = DEFAULT_PROFILE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        intro = QLabel(tr("profile_chooser.intro"))
        intro.setWordWrap(True)
        intro.setObjectName("profileChooserIntro")
        layout.addWidget(intro)


        for code in PROFILES:
            layout.addWidget(self._make_choice_button(code))

        layout.addStretch(1)

    def _make_choice_button(self, code: str) -> QPushButton:
        title = profile_title(code)
        desc_key = f"profile_chooser.{code}_desc"
        desc = tr(desc_key)

        btn = QPushButton(f"{title}\n\n{desc}", self)
        btn.setObjectName("profileChooserButton")
        btn.setMinimumHeight(96)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.clicked.connect(lambda checked=False, c=code: self._choose(c))
        return btn

    def _choose(self, code: str) -> None:
        self._chosen = code
        self.accept()

    def chosen_profile(self) -> str:
        return self._chosen
