from __future__ import annotations

try:
    from core.config import Settings as _Cfg
    from core.config import load as _cfg_load
    from core.config import save as _cfg_save
except Exception:
    class _Cfg:
        def __init__(self):
            self.zpaq_path = None
            self.last_fs_path = None
            self.last_extract_dir = None
            self.tasks_dir = None
            self.latest_only = False
            self.language = None


            self.skin = None


            self.profile = None
            self.window_geometry = None
            self.window_maximized = False
            self.left_split = None
            self.right_sort_column = None
            self.right_sort_desc = False

    def _cfg_load():
        return _Cfg()

    def _cfg_save(cfg):
        return None


def _load_cfg() -> "_Cfg":

    try:
        return _cfg_load()
    except Exception:
        return _Cfg()


def _save_cfg(cfg) -> None:

    try:
        _cfg_save(cfg)
    except Exception:
        pass


def _merge_cfg(**changes) -> None:

    try:
        c = _load_cfg()
        for k, v in changes.items():
            if hasattr(c, k):
                setattr(c, k, v)
        _save_cfg(c)
    except Exception:
        pass
