


























from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
from typing import Optional

                                                                     
                                         
MANUAL_LANGS = ("ru", "en")

                                      
INDEX_NAME = "index.html"

                                                                                
ONLINE_BASE = "https://rizpaq.ru/help"


def index_name() -> str:
    pass
    return INDEX_NAME


def _project_doc() -> Path:
    pass
    return Path(__file__).resolve().parent.parent / "doc"


def _exe_dir() -> Path:
    pass
    return Path(sys.executable).resolve().parent


def _has_index(d: Path) -> bool:
    pass







    try:
        if (d / INDEX_NAME).is_file():
            return True
        for child in d.iterdir():
            if child.is_dir() and (child / INDEX_NAME).is_file():
                return True
    except OSError:
        pass
    return False


def find_manual_root() -> Optional[Path]:
    pass









    exe = _exe_dir()
    for cand in (exe / "help", exe / "_internal" / "help", _project_doc()):
        if cand.is_dir() and _has_index(cand):
            return cand
    return None


def pick_manual(lang: str | None = None) -> tuple:
    pass





    from ui.i18n import current_language

    lang = lang or current_language()
    order = [lang] + [l for l in MANUAL_LANGS if l != lang]

    root = find_manual_root()
    if root is None:
        return None, ""

    for try_lang in order:
        direct = root / try_lang / INDEX_NAME
        if direct.is_file():
            return direct, try_lang

                                                             
    direct = root / INDEX_NAME
    if direct.is_file():
        return direct, lang

    return None, ""


def _online_url(lang: str) -> str:
    pass
    return f"{ONLINE_BASE}/{lang}/{INDEX_NAME}"


def open_manual(lang: str | None = None) -> tuple:
    pass

















    from ui.i18n import current_language

    lang = lang or current_language()

    path, _used = pick_manual(lang)
    if path is not None:
        try:
            if webbrowser.open(Path(path).as_uri()):
                return True, str(path)
        except Exception:
                                                              
            pass

    order = [lang] + [l for l in MANUAL_LANGS if l != lang]
    for try_lang in order:
        url = _online_url(try_lang)
        try:
            if webbrowser.open(url):
                return True, url
        except Exception:
            continue

                                                                      
    return False, _online_url(lang)
