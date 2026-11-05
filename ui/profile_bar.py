from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.i18n import tr
from ui.profile_bridge import PROFILES, profile_title


_ACTION_SPECS = (

    ("menu.file.create_archive", None,
     "_on_create_archive_current", ("archive",)),
    ("menu.file.open_archive", None,
     "_on_open_archive_dialog", ("archive",)),

    ("task.run_menu", "task.run_menu.tip",
     "_on_run_task", ("backup",)),
    ("task.edit_menu", "task.edit_menu.tip",
     "_on_edit_task", ("backup",)),
    ("scheduler.manager_menu", "scheduler.manager_menu_tip",
     "_on_open_scheduler", ("backup",)),

    ("menu.go.refresh", None,
     "_on_refresh", "*"),
)


class ProfileBar(QWidget):


    profile_changed = Signal(str)
    dashboard_requested = Signal()

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self._host = host

        self.setObjectName("profileBar")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(6)


        self._switch_row = QWidget(self)
        self._switch_row.setObjectName("profileSwitchRow")
        switch_layout = QHBoxLayout(self._switch_row)
        switch_layout.setContentsMargins(0, 0, 0, 0)
        switch_layout.setSpacing(0)

        self._profile_buttons: dict = {}
        for index, code in enumerate(PROFILES):
            btn = QPushButton(profile_title(code), self._switch_row)


            if index == 0:
                btn.setObjectName("profileSwitchLeft")
            else:
                btn.setObjectName("profileSwitchMiddle")
            btn.setCheckable(True)
            btn.setAutoDefault(False)
            btn.setDefault(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, code=code: self._on_profile_clicked(code)
            )
            switch_layout.addWidget(btn)
            self._profile_buttons[code] = btn

        self._dashboard_button = QPushButton(tr("profile.dashboard"),
                                             self._switch_row)
        self._dashboard_button.setObjectName("profileSwitchRight")
        self._dashboard_button.setCheckable(True)
        self._dashboard_button.setAutoDefault(False)
        self._dashboard_button.setDefault(False)
        self._dashboard_button.setCursor(Qt.PointingHandCursor)
        self._dashboard_button.setToolTip(tr("dashboard.menu.tip"))
        self._dashboard_button.clicked.connect(self._on_dashboard_clicked)
        switch_layout.addWidget(self._dashboard_button)

        switch_layout.addStretch(1)
        outer.addWidget(self._switch_row)


        self._actions_row = QWidget(self)
        self._actions_row.setObjectName("profileActionsRow")
        actions_layout = QHBoxLayout(self._actions_row)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)

        self._action_buttons: list = []
        for label_key, tip_key, handler_name, applies_to in _ACTION_SPECS:
            btn = QPushButton(tr(label_key), self._actions_row)
            btn.setObjectName("profileActionButton")
            btn.setAutoDefault(False)
            btn.setDefault(False)


            btn.setProperty("active", "true")

            handler = getattr(self._host, handler_name, None)
            if callable(handler):
                btn.clicked.connect(
                    lambda checked=False, b=btn, h=handler: self._on_action_clicked(b, h)
                )

            actions_layout.addWidget(btn)
            self._action_buttons.append(
                (btn, label_key, tip_key, applies_to)
            )

        actions_layout.addStretch(1)
        outer.addWidget(self._actions_row)

        self.rebuild()


    def _current_profile(self) -> str:
        getter = getattr(self._host, "current_profile", None)
        if callable(getter):
            try:
                return getter()
            except Exception:
                pass
        return PROFILES[0]

    def _on_profile_clicked(self, code: str):
        self.profile_changed.emit(code)

    def _on_dashboard_clicked(self):
        self.dashboard_requested.emit()

    def sync_mode(self, mode: str = None):
        dash = self._dashboard_button
        try:
            if mode == "dashboard":
                for btn in self._profile_buttons.values():
                    btn.setChecked(False)
                dash.setChecked(True)
            else:
                dash.setChecked(False)
                current = mode if mode in PROFILES else None
                self._sync_profile_checked(current)
        except Exception:
            pass

    def _sync_profile_checked(self, current: str = None):
        if current is None:
            current = self._current_profile()
        for code, btn in self._profile_buttons.items():
            try:
                btn.setChecked(code == current)
            except Exception:
                pass


    def _on_action_clicked(self, btn, handler):
        try:
            if btn.property("active") == "false":
                return
        except Exception:
            return
        try:
            handler()
        except Exception:
            pass

    def rebuild(self, profile: str = None):
        current = profile if profile in PROFILES else self._current_profile()


        for code, btn in self._profile_buttons.items():
            try:
                btn.setText(profile_title(code))
            except Exception:
                pass


        try:
            self._dashboard_button.setText(tr("profile.dashboard"))
        except Exception:
            pass


        for btn, label_key, _tip_key, _applies in self._action_buttons:
            try:
                btn.setText(tr(label_key))
            except Exception:
                pass


        self._sync_profile_checked(current)
        try:
            self._dashboard_button.setChecked(False)
        except Exception:
            pass


        for btn, _label, tip_key, applies_to in self._action_buttons:
            active = (applies_to == "*") or (current in applies_to)


            new_value = "true" if active else "false"
            try:
                if btn.property("active") != new_value:
                    btn.setProperty("active", new_value)
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
            except Exception:
                pass


            try:
                btn.setCursor(Qt.PointingHandCursor if active else Qt.ArrowCursor)
            except Exception:
                pass


            base_tip = tr(tip_key) if tip_key else ""
            if active:
                btn.setToolTip(base_tip)
            else:
                target = (
                    applies_to[0]
                    if isinstance(applies_to, tuple) and applies_to
                    else None
                )
                if target:
                    hint = tr("profile.inactive_hint",
                              profile=profile_title(target))
                    full = f"{base_tip} · {hint}" if base_tip else hint
                else:
                    full = base_tip
                try:
                    btn.setToolTip(full)
                except Exception:
                    pass


        try:
            for btn, *_ in self._action_buttons:
                btn.setMinimumWidth(0)
            widths = [btn.sizeHint().width() for btn, *_ in self._action_buttons]
            if widths:
                widest = max(widths)
                for btn, *_ in self._action_buttons:
                    btn.setMinimumWidth(widest)
        except Exception:
            pass
