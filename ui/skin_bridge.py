






















from __future__ import annotations

from PySide6.QtGui import QActionGroup

from ui import skins
from ui.config_bridge import _merge_cfg
from ui.i18n import tr
from ui.palette import refresh_theme


def _app():
    pass
    from PySide6.QtWidgets import QApplication

    return QApplication.instance()


def skin_title(code: str) -> str:
    pass






    key = f"skin.{code}"
    text = tr(key)
    return code if text == key else text


class SkinBridgeMixin:
    pass

    def _init_skin(self) -> str:
        pass






        code = getattr(self._cfg, "skin", None)
        if code:
            skins.set_current(code)
        return skins.current_name()

    def _switch_skin(self, code: str) -> str:
        pass






        applied = skins.set_current(code)
        if applied != code:
                                                                            
            return applied

        try:
            self._cfg.skin = applied
        except Exception:
            pass

        try:
            _merge_cfg(skin=applied)
        except Exception:
            pass

        app = _app()
        if app is not None:
            try:
                refresh_theme(app)
            except Exception:
                pass

                                                
        try:
            self._sync_skin_menu()
        except Exception:
            pass

        try:
            self.statusBar().showMessage(tr("status.skin_changed", name=skin_title(applied)))
        except Exception:
            pass

        return applied

    def _sync_skin_menu(self) -> None:
        pass
        group = getattr(self, "_skin_group", None)
        actions = getattr(self, "_skin_actions", None)
        if group is None or actions is None:
            return
        current = skins.current_name()
        for code, action in actions.items():
            try:
                action.setChecked(code == current)
            except Exception:
                pass

    def _build_skin_menu(self, parent):
        pass







        menu = parent.addMenu(tr("menu.tools.skin"))

        old_group = getattr(self, "_skin_group", None)
        if old_group is not None:
            try:
                old_group.deleteLater()
            except Exception:
                pass

        group = QActionGroup(self)
        group.setExclusive(True)
        self._skin_group = group

        actions = {}
        current = skins.current_name()
        for code in skins.skin_names():
            action = menu.addAction(skin_title(code))
            action.setCheckable(True)
            action.setData(code)
            action.setChecked(code == current)
            action.triggered.connect(
                lambda checked=False, code=code: self._switch_skin(code)
            )
            group.addAction(action)
            actions[code] = action

        self._skin_actions = actions
        return menu
