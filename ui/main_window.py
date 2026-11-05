from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow

from ui.app_info import APP_NAME, APP_VERSION_FULL
from ui.app_services import AppServicesMixin
from ui.archive_actions import ArchiveActionsMixin
from ui.par2_actions import Par2ActionsMixin
from ui.archive_loader import ArchiveLoaderMixin
from ui.config_bridge import _load_cfg, _merge_cfg
from ui.drag_drop import DragDropMixin
from ui.extraction import ExtractionMixin
from ui.fs_actions import FsActionsMixin
from ui.language_bridge import LanguageBridgeMixin
from ui.profile_bridge import ProfileBridgeMixin
from ui.skin_bridge import SkinBridgeMixin
from ui.menu_actions import MenuActionsMixin
from ui.navigation import NavigationMixin
from ui.progress_bridge import ProgressBridgeMixin
from ui.qt_compat import WIDGET_SHORTCUT, multipart_pattern
from ui.table_events import TableEventsMixin
from ui.table_fill import TableFillMixin
from ui.tree_events import TreeEventsMixin
from ui.update_actions import UpdateActionsMixin
from ui.version_menu import VersionMenuMixin
from ui.window_layout import WindowLayoutMixin
from ui.window_shell import WindowShellMixin
from ui.worker_launch import WorkerLaunchMixin


class MainWindow(
    WindowShellMixin,
    DragDropMixin,
    QMainWindow,
    AppServicesMixin,
    ArchiveLoaderMixin,
    ArchiveActionsMixin,
    Par2ActionsMixin,
    WorkerLaunchMixin,
    ProgressBridgeMixin,
    VersionMenuMixin,
    ExtractionMixin,
    TableFillMixin,
    TableEventsMixin,
    TreeEventsMixin,
    FsActionsMixin,
    LanguageBridgeMixin,
    SkinBridgeMixin,
    ProfileBridgeMixin,
    NavigationMixin,
    WindowLayoutMixin,
    MenuActionsMixin,
    UpdateActionsMixin,
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION_FULL}")
        self.resize(1320, 820)

        self._cfg = _load_cfg()


        self._init_language()


        self._init_skin()


        if getattr(self._cfg, "profile", None) is None:
            self._choose_profile_on_first_run()


        self._init_profile()

        self.zpaq_bin = os.environ.get("ZPAQ_BIN", "zpaqfranz")
        if self._cfg.zpaq_path and os.path.isfile(self._cfg.zpaq_path):
            self.zpaq_bin = self._cfg.zpaq_path
        self.zpaq_available = False


        self.seven_zip_bin = os.environ.get("SEVEN_ZIP_BIN", "")
        if not self.seven_zip_bin:
            try:
                if self._cfg.seven_zip_path and os.path.isfile(self._cfg.seven_zip_path):
                    self.seven_zip_bin = self._cfg.seven_zip_path
            except Exception:
                pass
        if not self.seven_zip_bin:
            try:
                from core.universal_ops import find_7z
                self.seven_zip_bin = find_7z() or ""
            except Exception:
                pass
        self.seven_zip_available = False

        self.mode = "fs"
        self.fs_path: Optional[Path] = None
        self.archive_path: Optional[str] = None
        self.archive_inner: str = ""
        self.version_slice: Optional[int] = None
        self.password: Optional[str] = None
        self.last_extract_dir = self._cfg.last_extract_dir
        self._search_query: str = ""
        self._last_search_archive: Optional[str] = None
        self._arc_cache: dict = {}
        self.entries: list = []
        self.versions: list = []
        self.summary = None
        self._workers: list = []
        self._wait_cursor = False
        self._nav_key = None
        self._load_req: Optional[dict] = None
        self._busy_base = ""
        self._busy_n = 0


        self._busy_depth = 0
        self._notice = None


        self._bold_font = self.font()
        self._bold_font.setBold(True)


        self._right_sort_column = getattr(self._cfg, "right_sort_column", None)
        self._right_sort_desc = getattr(self._cfg, "right_sort_desc", False)


        self._pending_info_path: Optional[str] = None
        self._pending_create_report: Optional[dict] = None


        self._profile = getattr(self, "_profile", "archive")
        self._profile_group = None
        self._profile_actions = None


        self.profile_bar = None


        self._main_stack = None
        self._archive_page = None
        self.backup_page = None
        self.dashboard_page = None


        self._versions_menu = None
        self._ver_group = None
        self.compare_action = None
        self.convert_action = None
        self.archive_info_action = None
        self.latest_only_action = None
        self._unpack_all_action = None
        self._unpack_ver_menu = None
        self._lang_group = None

        self._create_ui()
        self._setup_drag_drop()
        self._setup_tree_context_menu()


        self._retranslate_ui()

        self._setup_language_listener()


        if self.profile_bar is not None:
            try:
                self.profile_bar.profile_changed.connect(self._switch_profile)
            except Exception:
                pass
            try:
                self.profile_bar.dashboard_requested.connect(
                    self._on_dashboard_requested
                )
            except Exception:
                pass


        self._apply_profile_to_ui(self.current_profile())

        try:
            self.extract_bar.cancelRequested.connect(self._cancel_long_operations)
        except Exception:
            pass

        try:
            if self.latest_only_action is not None:
                self.latest_only_action.setChecked(bool(self._cfg.latest_only))
        except Exception:
            pass

        self._apply_persisted_geometry()

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self._apply_search)

        self.crumb.set_callbacks(
            self.navigate_fs,
            lambda inner: self.navigate_archive(inner),
        )
        self.tree.fs_selected.connect(self._on_tree_fs_selected)
        self.tree.arc_selected.connect(self._on_tree_arc_selected)
        self.tree.arc_open_requested.connect(self._on_tree_arc_open_requested)

        QShortcut(
            QKeySequence("Esc"),
            self.search_edit,
            self._clear_search,
            context=WIDGET_SHORTCUT,
        )
        QShortcut(
            QKeySequence("Delete"),
            self.table,
            self._delete_table_current,
            context=WIDGET_SHORTCUT,
        )
        QShortcut(
            QKeySequence("F2"),
            self.table,
            self._rename_table_current,
            context=WIDGET_SHORTCUT,
        )

        self._busy_timer = QTimer(self)
        self._busy_timer.setInterval(350)
        self._busy_timer.timeout.connect(self._tick_busy)

        self._verify_zpaq()
        self._verify_7z()

        start = Path.home()
        try:
            if self._cfg.last_fs_path:
                p = Path(self._cfg.last_fs_path)
                if p.is_dir():
                    start = p
        except Exception:
            pass
        self._show_fs(start)


    def _choose_profile_on_first_run(self) -> None:
        try:
            from PySide6.QtWidgets import QDialog

            from ui.profile_bridge import DEFAULT_PROFILE
            from ui.profile_chooser import ProfileChooserDialog

            dlg = ProfileChooserDialog(parent=None)
            code = DEFAULT_PROFILE
            if dlg.exec() == QDialog.Accepted:
                code = dlg.chosen_profile()

            self._cfg.profile = code
            try:
                _merge_cfg(profile=code)
            except Exception:
                pass
        except Exception:
            pass


    def _apply_profile_to_ui(self, profile: str):
        bar = getattr(self, "profile_bar", None)
        if bar is not None:
            try:
                bar.rebuild(profile)
            except Exception:
                pass
        self._switch_main_page(profile)

    def _on_dashboard_requested(self):
        self._switch_main_page("dashboard")

    def show_startup_digest(self):
        from ui.startup_digest_panel import show_if_needed

        try:
            show_if_needed(self)
        except Exception:
            pass

    def _switch_main_page(self, page_name: str):
        stack = getattr(self, "_main_stack", None)
        if stack is None:
            return

        page = None
        if page_name == "dashboard":
            page = getattr(self, "dashboard_page", None)
            if page is not None:
                try:
                    page.refresh()
                except Exception:
                    pass
        if page is None and page_name == "backup":
            page = getattr(self, "backup_page", None)
            if page is not None:
                try:
                    page.refresh()
                except Exception:
                    pass
        if page is None:
            page = getattr(self, "_archive_page", None)
        if page is None:
            return

        try:
            idx = stack.indexOf(page)
            if idx >= 0:
                stack.setCurrentIndex(idx)
        except Exception:
            pass


        bar = getattr(self, "profile_bar", None)
        if bar is not None and hasattr(bar, "sync_mode"):
            try:
                bar.sync_mode("dashboard" if page_name == "dashboard"
                              else page_name)
            except Exception:
                pass


    def _load_archive_list(self, path, make_active=False, inner=""):
        return super()._load_archive_list(
            multipart_pattern(path), make_active=make_active, inner=inner
        )


    def _open_rzp(self, path: str) -> None:
        if not path:
            return
        p = Path(path)
        if p.suffix.lower() != ".rzp":
            return
        if not p.is_file():
            return


        folder = str(p.parent)
        try:
            if getattr(self, "_cfg", None) is not None:
                self._cfg.tasks_dir = folder
        except Exception:
            pass
        try:
            _merge_cfg(tasks_dir=folder)
        except Exception:
            pass


        self._switch_main_page("backup")
        if getattr(self, "profile_bar", None) is not None:
            try:
                self.profile_bar.rebuild("backup")
            except Exception:
                pass


        page = getattr(self, "backup_page", None)
        if page is not None:
            try:
                page.refresh()
            except Exception:
                pass
