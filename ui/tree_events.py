from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMenu

from ui.i18n import tr
from ui.test_modes import has_par2_for as par2_set_exists
from ui.test_modes import menu_entries as test_mode_entries
from ui.qt_compat import (
    ARC_OWNER_ROLE,
    CUSTOM_CONTEXT,
    K_ARC,
    K_FS,
    K_FS_ARC,
    K_FS_UNI_ARC,
    KIND_ROLE,
    TCOL,
    USER_ROLE,
)


class TreeEventsMixin:


    def _setup_tree_context_menu(self):

        try:
            self.tree.setContextMenuPolicy(CUSTOM_CONTEXT)
            self.tree.customContextMenuRequested.connect(
                self._on_tree_context_menu
            )
        except Exception:
            pass


    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        kind = item.data(TCOL, KIND_ROLE)
        if kind == K_FS:
            self._fs_context_menu(item, pos)
        elif kind in (K_FS_ARC, K_FS_UNI_ARC):
            self._fs_archive_context_menu(item, pos)
        elif kind == K_ARC:
            self._archive_inner_context_menu(item, pos)


    def _fs_context_menu(self, item, pos):
        path = item.data(TCOL, USER_ROLE)
        if not path:
            return
        menu = QMenu(self)
        act_open = menu.addAction(tr("context.open_folder"))
        act_open.triggered.connect(lambda: self.navigate_fs(Path(path)))
        act_create = menu.addAction(tr("context.create_archive"))
        act_create.triggered.connect(
            lambda: self._on_create_archive_paths([path])
        )

        p = Path(path)
        if p.parent != p:
            menu.addSeparator()
            act_rename = menu.addAction(tr("context.rename"))
            act_rename.triggered.connect(lambda: self._rename_fs_path(path))
            act_delete = menu.addAction(tr("context.delete"))
            act_delete.triggered.connect(lambda: self._delete_fs_path(path))
        self._exec_menu(menu, pos)

    def _fs_archive_context_menu(self, item, pos):
        arc_path = item.data(TCOL, USER_ROLE)
        if not arc_path:
            return

        is_uni = item.data(TCOL, KIND_ROLE) == K_FS_UNI_ARC

        menu = QMenu(self)
        act_open = menu.addAction(tr("context.open_archive"))
        act_open.triggered.connect(lambda: self._enter_archive(arc_path))

        if is_uni:
            extract_act = menu.addAction(tr("context.extract_universal"))
            extract_act.triggered.connect(
                lambda: self._extract_universal_dialog(arc_path)
            )
            convert_act = menu.addAction(tr("context.convert_to_zpaq"))
            convert_act.triggered.connect(
                lambda: self._convert_universal_to_zpaq(arc_path)
            )
        else:
            act_create = menu.addAction(tr("context.create_archive"))
            act_create.triggered.connect(
                lambda: self._on_create_archive_paths([arc_path])
            )
            menu.addSeparator()


            test_menu = menu.addMenu(tr("menu.test"))
            for mode, label in test_mode_entries():
                act = test_menu.addAction(label)


                act.setData(mode)
                act.triggered.connect(
                    lambda _c=False, m=mode: self._on_test_archive(arc_path, m)
                )


            if par2_set_exists(arc_path):
                menu.addSeparator()
                act_restore = menu.addAction(tr("par2.repair"))
                act_restore.triggered.connect(
                    lambda: self._start_par2_repair(arc_path)
                )


                act_recreate = menu.addAction(tr("par2.recreate_now"))
                act_recreate.triggered.connect(
                    lambda: self._start_par2_create(arc_path, recreate=True)
                )
            else:


                menu.addSeparator()
                act_create = menu.addAction(tr("par2.create_now"))
                act_create.triggered.connect(
                    lambda: self._start_par2_create(arc_path)
                )

        menu.addSeparator()
        act_rename = menu.addAction(tr("context.rename"))
        act_rename.triggered.connect(lambda: self._rename_fs_path(arc_path))
        act_delete = menu.addAction(tr("context.delete"))
        act_delete.triggered.connect(lambda: self._delete_fs_path(arc_path))

        if not is_uni and self.archive_path == arc_path:
            menu.addSeparator()
            act_info = menu.addAction(tr("context.archive_info"))
            act_info.triggered.connect(self._on_archive_info)

        self._exec_menu(menu, pos)

    def _archive_inner_context_menu(self, item, pos):
        inner = item.data(TCOL, USER_ROLE) or ""
        owner = item.data(TCOL, ARC_OWNER_ROLE) or ""
        if not inner:
            return
        menu = QMenu(self)


        if owner and owner != self.archive_path:
            act_open = menu.addAction(tr("context.open_archive_and_folder"))
            act_open.triggered.connect(
                lambda: self._tree_open_archive_inner(owner, inner)
            )
            self._exec_menu(menu, pos)
            return

        act_open = menu.addAction(tr("context.open_folder"))
        act_open.triggered.connect(lambda: self.navigate_archive(inner))
        menu.addSeparator()
        act_extract_last = menu.addAction(tr("context.extract_folder_latest"))
        act_extract_last.triggered.connect(
            lambda: self._extract_folder(inner, None)
        )
        act_extract_version = menu.addAction(
            tr("context.extract_folder_version")
        )
        act_extract_version.triggered.connect(
            lambda: self._extract_folder_ask_version(inner)
        )
        self._exec_menu(menu, pos)

    def _tree_open_archive_inner(self, arc_path: str, inner: str):

        if not arc_path:
            return
        c = self._cache(arc_path)
        if c.get("loaded"):
            self._activate_archive(arc_path)
            self.navigate_archive(inner)
            if not c.get("info_loaded"):
                self._load_info(arc_path)
        else:
            self._load_archive_list(arc_path, make_active=True, inner=inner)

    def _exec_menu(self, menu: QMenu, pos):
        if menu.isEmpty():
            return
        try:
            global_pos = self.tree.viewport().mapToGlobal(pos)
        except Exception:
            global_pos = self.tree.mapToGlobal(pos)
        try:
            menu.exec(global_pos)
        except AttributeError:
            menu.exec_(global_pos)
