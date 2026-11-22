






















from __future__ import annotations

from ui.i18n import tr

                                                                  
 
                                                                  
                                                                   
                                                                       
                                                                
                          
TEST_MODES_UI = (
    ("full", "menu.test.full", "check.mode_full"),
    ("checksum", "menu.test.checksum", "check.mode_checksum"),
    ("verify", "menu.test.verify", "check.mode_verify"),
    ("paranoid", "menu.test.paranoid", "check.mode_paranoid"),
    ("par2", "menu.test.par2", "par2.test_mode"),
    ("verify_fs", "menu.test.verify_fs", "check.mode_verify_fs"),
    ("sync", "menu.test.sync", "check.mode_sync"),
    ("restore", "menu.test.restore", "check.mode_restore"),
)

                                                                 
                                                                     
                                                                 
                                                                          
                                                                     
                                                                        
                  
TEST_MODE_TIPS = {
    "full": "tip.test_archive",
    "checksum": "tip.test_archive",
    "verify": "tip.test_archive",
    "paranoid": "tip.paranoid",
    "par2": "tip.par2_verify",
    "verify_fs": "tip.verify_fs",
    "sync": "tip.sync",
    "restore": "tip.restore",
}


def mode_tooltip(mode: str) -> str:
    pass






    key = TEST_MODE_TIPS.get(str(mode or ""))
    return tr(key) if key else ""


def menu_entries():
    pass
    return tuple((mode, tr(menu_key)) for mode, menu_key, _ in TEST_MODES_UI)


def combo_entries():
    pass
    return tuple(
        (mode, tr(combo_key)) for mode, _menu, combo_key in TEST_MODES_UI
    )


def mode_label(mode: str, default_key: str = "test.title") -> str:
    pass







    wanted = str(mode or "")
    for candidate, menu_key, combo_key in TEST_MODES_UI:
        if candidate == wanted:
                                                                   
                                         
            return tr(menu_key)
    return tr(default_key)


def has_par2_for(archive_path: str) -> bool:
    pass









    if not archive_path:
        return False
    import os

    from core.par2_ops import par2_main_name

    try:
        return os.path.isfile(par2_main_name(str(archive_path)))
    except Exception:
        return False