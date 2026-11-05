from __future__ import annotations

from ui.i18n import tr


TEST_MODES_UI = (
    ("full", "menu.test.full", "check.mode_full"),
    ("checksum", "menu.test.checksum", "check.mode_checksum"),
    ("verify", "menu.test.verify", "check.mode_verify"),
    ("paranoid", "menu.test.paranoid", "check.mode_paranoid"),
    ("par2", "menu.test.par2", "par2.test_mode"),
)


def menu_entries():

    return tuple((mode, tr(menu_key)) for mode, menu_key, _ in TEST_MODES_UI)


def combo_entries():

    return tuple(
        (mode, tr(combo_key)) for mode, _menu, combo_key in TEST_MODES_UI
    )


def mode_label(mode: str, default_key: str = "test.title") -> str:
    wanted = str(mode or "")
    for candidate, menu_key, combo_key in TEST_MODES_UI:
        if candidate == wanted:


            return tr(menu_key)
    return tr(default_key)


def has_par2_for(archive_path: str) -> bool:
    if not archive_path:
        return False
    import os

    from core.par2_ops import par2_main_name

    try:
        return os.path.isfile(par2_main_name(str(archive_path)))
    except Exception:
        return False
