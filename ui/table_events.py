from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMenu

from ui.i18n import tr
from ui.test_modes import has_par2_for as par2_set_exists
from ui.test_modes import menu_entries as test_mode_entries
from ui.qt_compat import (
    K_ARC_DIR,
    K_ARC_FILE,
    K_FS_ARC,
    K_FS_DIR,
    K_FS_FILE,
    K_FS_UNI_ARC,
    K_UP,
    KIND_ROLE,
    USER_ROLE,
)


class TableEventsMixin:


    def _row_payload(self):
        row = self.table.currentRow()
        if row < 0:
            return None, None
        item = self.table.item(row, 0)
        if not item:
            return None, None
        return item.data(KIND_ROLE), item.data(USER_ROLE)

    def _on_table_double_click(self):
        kind, payload = self._row_payload()
        if kind == K_UP:
            self._go_up()
        elif kind == K_FS_DIR:
            if payload:
                self.navigate_fs(Path(payload))
        elif kind == K_FS_ARC:
            if payload:
                self._enter_archive(payload)
        elif kind == K_FS_UNI_ARC:
            if payload:
                self._enter_archive(payload)
        elif kind == K_FS_FILE:
            if payload:
                self._open_fs_path(payload)
        elif kind == K_ARC_DIR:
            if payload:
                self.navigate_archive(payload)
        elif kind == K_ARC_FILE:
            if payload:
                self._open_arc_file_entry(payload)

    def _on_table_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)
        kind, payload = self._row_payload()
        if not kind or payload is None:
            return

        menu = QMenu(self)

        if kind == K_FS_ARC:
            open_act = menu.addAction(tr("context.open_archive"))
            open_act.triggered.connect(lambda: self._enter_archive(payload))
            create_act = menu.addAction(tr("context.create_archive"))
            create_act.triggered.connect(
                lambda: self._on_create_archive_paths([payload])
            )
            menu.addSeparator()


            test_menu = menu.addMenu(tr("menu.test"))
            for mode, label in test_mode_entries():
                act = test_menu.addAction(label)
                act.setData(mode)
                act.triggered.connect(
                    lambda _c=False, m=mode: self._on_test_archive(payload, m)
                )


            if par2_set_exists(payload):
                menu.addSeparator()
                act_restore = menu.addAction(tr("par2.repair"))
                act_restore.triggered.connect(
                    lambda: self._start_par2_repair(payload)
                )


                act_recreate = menu.addAction(tr("par2.recreate_now"))
                act_recreate.triggered.connect(
                    lambda: self._start_par2_create(payload, recreate=True)
                )
            else:


                menu.addSeparator()
                act_create = menu.addAction(tr("par2.create_now"))
                act_create.triggered.connect(
                    lambda: self._start_par2_create(payload)
                )
            menu.addSeparator()
            rename_act = menu.addAction(tr("context.rename"))
            rename_act.triggered.connect(lambda: self._rename_fs_path(payload))
            delete_act = menu.addAction(tr("context.delete"))
            delete_act.triggered.connect(lambda: self._delete_fs_path(payload))

        elif kind == K_FS_UNI_ARC:
            open_act = menu.addAction(tr("context.open_archive"))
            open_act.triggered.connect(lambda: self._enter_archive(payload))

            extract_act = menu.addAction(tr("context.extract_universal"))
            extract_act.triggered.connect(
                lambda: self._extract_universal_dialog(payload)
            )

            convert_act = menu.addAction(tr("context.convert_to_zpaq"))
            convert_act.triggered.connect(
                lambda: self._convert_universal_to_zpaq(payload)
            )

            menu.addSeparator()
            rename_act = menu.addAction(tr("context.rename"))
            rename_act.triggered.connect(lambda: self._rename_fs_path(payload))
            delete_act = menu.addAction(tr("context.delete"))
            delete_act.triggered.connect(lambda: self._delete_fs_path(payload))

        elif kind in (K_FS_DIR, K_FS_FILE):
            if kind == K_FS_FILE:
                open_act = menu.addAction(tr("context.open"))
                open_act.triggered.connect(lambda: self._open_fs_path(payload))
                menu.addSeparator()
            create_act = menu.addAction(tr("context.create_archive"))
            create_act.triggered.connect(
                lambda: self._on_create_archive_paths([payload])
            )
            menu.addSeparator()
            rename_act = menu.addAction(tr("context.rename"))
            rename_act.triggered.connect(lambda: self._rename_fs_path(payload))
            delete_act = menu.addAction(tr("context.delete"))
            delete_act.triggered.connect(lambda: self._delete_fs_path(payload))

        elif kind == K_ARC_DIR:
            folder_path = payload
            open_act = menu.addAction(tr("context.open_folder"))
            open_act.triggered.connect(lambda: self.navigate_archive(folder_path))
            menu.addSeparator()
            a1 = menu.addAction(tr("context.extract_folder_latest"))
            a1.triggered.connect(
                lambda: self._extract_folder(folder_path, None)
            )
            a2 = menu.addAction(tr("context.extract_folder_version"))
            a2.triggered.connect(
                lambda: self._extract_folder_ask_version(folder_path)
            )

        elif kind == K_ARC_FILE:
            entry = payload

            open_act = menu.addAction(tr("context.open"))
            open_act.triggered.connect(lambda: self._open_arc_file_entry(entry))
            menu.addSeparator()
            version_text = (
                entry.version if entry.version is not None else "?"
            )
            a1 = menu.addAction(
                tr("context.extract_version", version=version_text)
            )
            a1.triggered.connect(lambda: self._extract_file_entry(entry))
            latest = self._latest_entry_for_path(entry.path)
            if latest:
                a2 = menu.addAction(tr("context.extract_latest"))
                a2.triggered.connect(lambda: self._extract_file_entry(latest))

        else:
            return

        self._exec_menu(menu, pos)

    def _exec_menu(self, menu, pos):
        if menu.isEmpty():
            return
        try:
            global_pos = self.table.viewport().mapToGlobal(pos)
        except Exception:
            global_pos = self.table.mapToGlobal(pos)
        try:
            menu.exec(global_pos)
        except AttributeError:
            menu.exec_(global_pos)
