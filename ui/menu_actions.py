



















from __future__ import annotations

from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ui.i18n import available_languages, current_language, tr
from ui.test_modes import menu_entries as test_mode_entries


class MenuActionsMixin:
    pass

    def _create_actions(self):
        mb = self.menuBar()
        mb.clear()

                                                                             
        m_file = mb.addMenu(tr("menu.file"))

        act_create = m_file.addAction(tr("menu.file.create_archive"))
        act_create.setShortcut("Ctrl+N")
        act_create.triggered.connect(self._on_create_archive_current)

        act_open = m_file.addAction(tr("menu.file.open_archive"))
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._on_open_archive_dialog)

        m_file.addSeparator()

        act_exit = m_file.addAction(tr("menu.file.exit"))
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)

                                                                             
        m_view = mb.addMenu(tr("menu.view"))

        act_refresh = m_view.addAction(tr("menu.go.refresh"))
        act_refresh.setShortcut("F5")
        act_refresh.triggered.connect(self._on_refresh)

        m_view.addSeparator()

        self.latest_only_action = m_view.addAction(tr("menu.view.latest_only"))
        self.latest_only_action.setCheckable(True)
        self.latest_only_action.setChecked(False)
        self.latest_only_action.setStatusTip(tr("menu.view.latest_only.tip"))
        self.latest_only_action.triggered.connect(self._on_toggle_latest)

                                                                             
        m_arc = mb.addMenu(tr("menu.archive"))

        act_create_arc = m_arc.addAction(tr("menu.file.create_archive"))
        act_create_arc.triggered.connect(self._on_create_archive_current)

        m_arc.addSeparator()

        self.archive_info_action = m_arc.addAction(tr("menu.tools.archive_info"))
        self.archive_info_action.setShortcut("Alt+Return")
        self.archive_info_action.setStatusTip(tr("menu.tools.archive_info.tip"))
        self.archive_info_action.setEnabled(False)
        self.archive_info_action.triggered.connect(self._on_archive_info)

                                                               
        self.convert_action = m_arc.addAction(tr("context.convert_to_zpaq"))
        self.convert_action.setStatusTip(tr("context.convert_to_zpaq"))
        self.convert_action.setEnabled(False)
        self.convert_action.triggered.connect(self._on_convert_current_to_zpaq)

        m_arc.addSeparator()

        m_unpack = m_arc.addMenu(tr("menu.unpack"))
        self._unpack_menu = m_unpack
        self._unpack_all_action = m_unpack.addAction(tr("menu.unpack.all"))
        self._unpack_all_action.triggered.connect(self._on_unpack_all)
        self._unpack_ver_menu = m_unpack.addMenu(tr("menu.unpack.version"))
        m_unpack.aboutToShow.connect(self._rebuild_unpack_menu)
        self._salvage_action = m_unpack.addAction(tr("menu.unpack.salvage"))
        self._salvage_action.triggered.connect(self._on_salvage_archive)

        m_test = m_arc.addMenu(tr("menu.test"))
        self._test_menu = m_test
                                                                   
                                                                
        for mode, label in test_mode_entries():
            act = m_test.addAction(label)
            act.setData(mode)
            act.triggered.connect(
                lambda _c=False, m=mode: self._on_test_archive(None, m)
            )

        m_arc.addSeparator()

        self._versions_menu = m_arc.addMenu(tr("menu.view.versions"))
        self._versions_menu.setEnabled(False)
        self._ver_group = None

        self.compare_action = m_arc.addAction(tr("menu.view.compare"))
        self.compare_action.setStatusTip(tr("menu.view.compare.tip"))
        self.compare_action.setEnabled(False)
        self.compare_action.triggered.connect(self._on_compare_versions)

        m_arc.addSeparator()

        self.search_action = m_arc.addAction(tr("menu.go.search"))
        self.search_action.setShortcut("Ctrl+F")
        self.search_action.setEnabled(False)
        self.search_action.triggered.connect(self._focus_search)

                                                                       
                                                                       
                                                               
         
                                                                      
                                                                     
                                                                       
                                                                
        self.global_search_action = m_arc.addAction(tr("menu.go.global_search"))
        self.global_search_action.setShortcut("Ctrl+Shift+F")
        self.global_search_action.triggered.connect(self._on_global_search)

                                                                       
                                                                        
                                               
        self.all_archives_action = m_arc.addAction(
            tr("menu.go.all_archives"))
        self.all_archives_action.triggered.connect(
            self._on_show_all_archives)

                                                                             
        m_backup = mb.addMenu(tr("menu.backup"))

        act_run_task = m_backup.addAction(tr("task.run_menu"))
        act_run_task.setStatusTip(tr("task.run_menu.tip"))
        act_run_task.triggered.connect(self._on_run_task)

        act_edit_task = m_backup.addAction(tr("task.edit_menu"))
        act_edit_task.setStatusTip(tr("task.edit_menu.tip"))
        act_edit_task.triggered.connect(self._on_edit_task)

        m_backup.addSeparator()

        act_scheduler = m_backup.addAction(tr("scheduler.manager_menu"))
        act_scheduler.setStatusTip(tr("scheduler.manager_menu_tip"))
        act_scheduler.triggered.connect(self._on_open_scheduler)

                                                                             
                                                                    
                                                                   
                                                                     
                                  
        m_par2 = mb.addMenu(tr("menu.par2"))

        self._par2_menu_create_action = m_par2.addAction(
            tr("par2.create_now")
        )
        self._par2_menu_create_action.triggered.connect(
            self._par2_menu_create
        )

        m_par2.addSeparator()

        self._par2_menu_verify_action = m_par2.addAction(
            tr("par2.verify_menu")
        )
        self._par2_menu_verify_action.triggered.connect(
            self._par2_menu_verify
        )

        self._par2_menu_repair_action = m_par2.addAction(tr("par2.repair"))
        self._par2_menu_repair_action.triggered.connect(
            self._par2_menu_repair
        )

        m_par2.aboutToShow.connect(self._refresh_par2_menu)
                                                                 
                                                                       
                      
        self._refresh_par2_menu()

                                                                             
        m_settings = mb.addMenu(tr("menu.settings"))

        act_zq = m_settings.addAction(tr("menu.file.zpaq_path"))
        act_zq.setStatusTip(tr("menu.file.zpaq_path.tip"))
        act_zq.triggered.connect(self._choose_zpaq_path)

        act_7z = m_settings.addAction(tr("menu.file.seven_zip_path"))
        act_7z.setStatusTip(tr("menu.file.seven_zip_path.tip"))
        act_7z.triggered.connect(self._choose_7z_path)

        m_settings.addSeparator()

                                                                 
                                                                      
        try:
            self._build_profile_menu(m_settings)
        except Exception:
            pass

                                                                   
                                                
        try:
            self._build_skin_menu(m_settings)
        except Exception:
            pass

        m_lang = m_settings.addMenu(tr("menu.tools.language"))
        old_group = getattr(self, "_lang_group", None)
        if old_group is not None:
            try:
                old_group.deleteLater()
            except Exception:
                pass
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        self._lang_group = lang_group
        current = current_language()
        for code, native_name in available_languages().items():
            act_lang = m_lang.addAction(native_name)
            act_lang.setCheckable(True)
            act_lang.setChecked(code == current)
            act_lang.triggered.connect(
                lambda checked=False, code=code: self._change_language(code)
            )
            lang_group.addAction(act_lang)

        m_settings.addSeparator()

                                                                
        act_assoc = m_settings.addAction(tr("menu.settings.integration"))
        act_assoc.setStatusTip(tr("menu.settings.integration.tip"))
        act_assoc.triggered.connect(self._on_open_association_dialog)

        m_settings.addSeparator()

                                                                        
                                                             
        act_notify = m_settings.addAction(tr("menu.settings.notifications"))
        act_notify.setStatusTip(tr("menu.settings.notifications.tip"))
        act_notify.triggered.connect(self._on_open_notify_dialog)

                                                                             
        m_help = mb.addMenu(tr("menu.help"))

        act_guide = m_help.addAction(tr("menu.help.guide"))
        act_guide.triggered.connect(self._on_open_manual)

                                                                        
                                                           
        act_updates = m_help.addAction(tr("menu.help.check_updates"))
        act_updates.triggered.connect(self._on_check_updates)

        act_about = m_help.addAction(tr("menu.help.about"))
        act_about.triggered.connect(self._on_about)

                                                                     

    def _on_convert_current_to_zpaq(self):
        pass
        if self.archive_path and self.mode == "universal":
            self._convert_universal_to_zpaq(self.archive_path)

    def _on_check_updates(self):
        pass
        self.start_update_check(manual=True)

    def _on_open_association_dialog(self):
        pass
        from ui.association_dialog import AssociationDialog
        dlg = AssociationDialog(self)
        dlg.exec()

    def _on_open_notify_dialog(self):
        pass






        from PySide6.QtWidgets import QDialog

        from ui.notify_dialog import NotifyDialog

        try:
            from core import config as config_mod
            cfg = config_mod.load()
        except Exception:
            cfg = None

        dlg = NotifyDialog(cfg, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        saved = dlg.saved_settings()
        if saved is None:
            return
        for name in ("notify_mode", "notify_telegram_token",
                     "notify_telegram_chat_id"):
            try:
                setattr(self._cfg, name, getattr(saved, name))
            except Exception:
                pass

    def _on_open_archive_dialog(self):
        pass
        path, _ = QFileDialog.getOpenFileName(
            self, tr("menu.file.open_archive"), "", tr("create.filter")
        )
        if path:
            self._enter_archive(path)

    def _on_global_search(self):
        pass
        from ui.global_search_dialog import GlobalSearchDialog

        dlg = GlobalSearchDialog(self)
        dlg.archive_requested.connect(self._on_global_archive_requested)
                                                                    
                                                                
                                                                      
        open_catalog = {"flag": False}

        def _request_catalog():
            open_catalog["flag"] = True
            dlg.accept()

        dlg.catalog_requested.connect(_request_catalog)
                                                                     
                                                                   
                                               
        dlg.reset_search()
        dlg.exec()

        if open_catalog["flag"]:
            self._on_show_all_archives()

    def _on_show_all_archives(self):
        pass
        from PySide6.QtWidgets import QDialog

        from core import config as config_mod
        from ui.archive_catalog_dialog import ArchiveCatalogDialog

        try:
            cfg = getattr(self, "_cfg", None) or config_mod.load()
        except Exception:
            cfg = None

        dlg = ArchiveCatalogDialog(
            roots=getattr(cfg, "catalog_roots", None),
            index_on_scan=getattr(cfg, "catalog_index_on_scan", True),
            zpaq_bin=getattr(self, "zpaq_bin", "") or "",
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted and dlg.chosen_path():
            self._enter_archive(dlg.chosen_path())

    def _on_global_archive_requested(self, path: str):
        pass
        if not path:
            return
        self._enter_archive(path)

    def _on_open_scheduler(self):
        pass








        from ui.scheduler_dialog import SchedulerManagerDialog

        def _container_provider():
            try:
                container, _path = self._load_container()
                return container or {}
            except Exception:
                return {}

        dlg = SchedulerManagerDialog(
            self, container_provider=_container_provider
        )
        dlg.exec()

                                                                      

    def _change_language(self, code: str):
        handler = getattr(self, "_switch_language", None)
        if callable(handler):
            handler(code)
            return
        try:
            self.statusBar().showMessage(tr("status.language_switch_unavailable"))
        except Exception:
            pass
