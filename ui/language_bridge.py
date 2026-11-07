



















from __future__ import annotations

from ui.config_bridge import _merge_cfg
from ui.i18n import (
    current_language,
    detect_language,
    on_language_changed,
    set_language,
    tr,
)


class LanguageBridgeMixin:
    pass

    def _init_language(self):
        pass
        lang = getattr(self._cfg, "language", None)

        if not lang:
            lang = detect_language()

        set_language(lang, notify=False)

    def _setup_language_listener(self):
        pass
        if getattr(self, "_language_listener_registered", False):
            return

        on_language_changed(self._retranslate_ui)
        self._language_listener_registered = True

    def _switch_language(self, lang: str):
        pass
        if lang == current_language():
            return

        try:
            self._cfg.language = lang
        except Exception:
            pass

        try:
            _merge_cfg(language=lang)
        except Exception:
            pass

        set_language(lang, notify=True)

        try:
            self.statusBar().showMessage(tr("status.language_changed"))
        except Exception:
            pass

    def _retranslate_ui(self):
        pass
                                                                
                                            
        latest_checked = bool(getattr(self._cfg, "latest_only", False))

        try:
            latest_checked = bool(self.latest_only_action.isChecked())
        except Exception:
            pass

                                              
        try:
            self._create_actions()
        except Exception:
            pass

        try:
            self.latest_only_action.setChecked(latest_checked)
        except Exception:
            pass

                                                                   
        try:
            self._rebuild_versions_menu()
        except Exception:
            pass

                                                                   
                                                              
        bar = getattr(self, "profile_bar", None)
        if bar is not None:
            try:
                bar.rebuild()
            except Exception:
                pass

                                                                       
                                                                      
                                                                      
        page = getattr(self, "backup_page", None)
        if page is not None:
            retranslate = getattr(page, "retranslate", None)
            if callable(retranslate):
                try:
                    retranslate()
                except Exception:
                    pass

                                                                  
                                                                
                       
        dash = getattr(self, "dashboard_page", None)
        if dash is not None:
            dash_retranslate = getattr(dash, "retranslate", None)
            if callable(dash_retranslate):
                try:
                    dash_retranslate()
                except Exception:
                    pass

                  
        try:
            self.table.setHorizontalHeaderLabels(
                [
                    tr("table.name"),
                    tr("table.size"),
                    tr("table.date"),
                    tr("table.version"),
                    tr("table.path"),
                ]
            )
        except Exception:
            pass

                
        try:
            self.search_edit.setPlaceholderText(tr("search.placeholder"))
        except Exception:
            pass

                 
        try:
            self.tree.setHeaderLabel(tr("tree.header"))
        except Exception:
            pass

                         
        try:
            self._update_title()
        except Exception:
            pass
