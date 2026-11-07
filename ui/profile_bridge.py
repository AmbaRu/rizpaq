



























from __future__ import annotations

from PySide6.QtGui import QActionGroup

from ui.config_bridge import _merge_cfg
from ui.i18n import tr

                                                    
PROFILES = ("archive", "backup")

                                                               
                                                                  
                                                               
DEFAULT_PROFILE = "archive"


def profile_title(code: str) -> str:
    pass







    key = f"profile.{code}"
    text = tr(key)
    return code if text == key else text


class ProfileBridgeMixin:
    pass

    def _init_profile(self) -> str:
        pass






        code = getattr(self._cfg, "profile", None)
        if code not in PROFILES:
            code = DEFAULT_PROFILE
        try:
            self._profile = code
        except Exception:
            pass
        return code

    def current_profile(self) -> str:
        pass
        code = getattr(self, "_profile", None)
        if code not in PROFILES:
            code = DEFAULT_PROFILE
        return code

    def _switch_profile(self, code: str) -> str:
        pass








        if code not in PROFILES:
            return self.current_profile()

        try:
            self._profile = code
        except Exception:
            pass

        try:
            self._cfg.profile = code
        except Exception:
            pass

        try:
            _merge_cfg(profile=code)
        except Exception:
            pass

        apply = getattr(self, "_apply_profile_to_ui", None)
        if callable(apply):
            try:
                apply(code)
            except Exception:
                                                                      
                                                 
                pass

        try:
            self._sync_profile_menu()
        except Exception:
            pass

        try:
            self.statusBar().showMessage(
                tr("status.profile_changed", name=profile_title(code))
            )
        except Exception:
            pass

        return code

    def _sync_profile_menu(self) -> None:
        pass
        actions = getattr(self, "_profile_actions", None)
        if actions is None:
            return
        current = self.current_profile()
        for code, action in actions.items():
            try:
                action.setChecked(code == current)
            except Exception:
                pass

    def _build_profile_menu(self, parent):
        pass









        menu = parent.addMenu(tr("menu.settings.profile"))

        old_group = getattr(self, "_profile_group", None)
        if old_group is not None:
            try:
                old_group.deleteLater()
            except Exception:
                pass

        group = QActionGroup(self)
        group.setExclusive(True)
        self._profile_group = group

        actions = {}
        current = self.current_profile()
        for code in PROFILES:
            action = menu.addAction(profile_title(code))
            action.setCheckable(True)
            action.setData(code)
            action.setChecked(code == current)
            action.triggered.connect(
                lambda checked=False, code=code: self._switch_profile(code)
            )
            group.addAction(action)
            actions[code] = action

        self._profile_actions = actions
        return menu
