

























































from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

                                                              
ENV_OVERRIDE = "ZPAQ_GUI_CONFIG"

                     
CONFIG_NAME = "zpaq_gui.json"

                                                                         
                                                                         
                                               
LOG_NAME = "rizpaq_error.log"

                                                                      
                                                 
LOG_MAX_BYTES = 256 * 1024
LOG_KEEP_BYTES = 64 * 1024

                                                                
PORTABLE_MARKERS = ("portable.txt", "portable")

                                                  
APP_DIR_NAME = "Rizpaq"


@dataclass
class Settings:
    pass
    zpaq_path: Optional[str] = None
    seven_zip_path: Optional[str] = None
    last_fs_path: Optional[str] = None
    last_extract_dir: Optional[str] = None
    tasks_dir: Optional[str] = None
    latest_only: bool = False
    language: Optional[str] = None
    skin: Optional[str] = None
    profile: Optional[str] = None
    window_geometry: Optional[list] = None                 
    window_maximized: bool = False
    left_split: Optional[list] = None                       
    right_sort_column: Optional[int] = None                
    right_sort_desc: bool = False
                                                                         
                                                                     
                                                                  
                                                                     
                                                                  
                                  
    associations_asked: bool = False
                                                                      
                                                                     
                                                                       
                                                                      
                                                                    
                                                                  
                                 
    engine_stall_timeout: Optional[int] = None
                                                                     
                                                           
    catalog_roots: Optional[list] = None
    catalog_index_on_scan: bool = True
                                                                 
                                   
    update_url: Optional[str] = None
    update_check_enabled: bool = True
    last_update_check: Optional[int] = None
    skipped_version: Optional[str] = None
                                                                       
                                                                  
                                                              
                                                              
    last_close: Optional[int] = None
    digest_enabled: bool = True


                                                                             
                                   
                                                                             

def _portable_base() -> Optional[Path]:
    pass



    candidates = []
    if getattr(sys, "frozen", False):
        try:
            candidates.append(Path(sys.executable).resolve().parent)
        except OSError:
            pass
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))
    try:
        candidates.append(Path(__file__).resolve().parent.parent)
    except (NameError, OSError):
        pass

    for base in candidates:
        for marker in PORTABLE_MARKERS:
            if (base / marker).exists():
                return base
    return None


def _user_config_dir() -> Path:
    pass
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME
        return Path.home() / "AppData" / "Roaming" / APP_DIR_NAME
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME.lower()
    return Path.home() / ".config" / APP_DIR_NAME.lower()


def _legacy_candidates() -> list:
    pass
    cands = []
    if getattr(sys, "frozen", False):
        try:
            cands.append(Path(sys.executable).resolve().parent)
        except OSError:
            pass
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cands.append(Path(meipass))
    try:
        cands.append(Path(__file__).resolve().parent.parent)
    except (NameError, OSError):
        pass
    return cands


def _maybe_migrate(target: Path) -> None:
    pass
    if target.is_file():
        return
    for base in _legacy_candidates():
        legacy = base / CONFIG_NAME
        if not legacy.is_file():
            continue
        try:
            if legacy.resolve() == target.resolve():
                return
        except OSError:
            pass
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(legacy, target)
        except OSError:
            pass
        return


def default_path() -> Path:
    pass






    override = os.environ.get(ENV_OVERRIDE)
    if override:
        return Path(override)
    portable = _portable_base()
    if portable is not None:
        return portable / CONFIG_NAME
    return _user_config_dir() / CONFIG_NAME


                                                                             
            
                                                                             
                                                                          
                                                                           
                                                    

def log_path() -> Path:
    pass
    return default_path().parent / LOG_NAME


def _log_candidates(name: str) -> list:
    pass
    out: list = []

    try:
        out.append(default_path().parent / name)
    except Exception:
        pass

    for var in ("LOCALAPPDATA", "APPDATA"):
        value = os.environ.get(var)
        if value:
            out.append(Path(value) / APP_DIR_NAME / name)

    for var in ("TEMP", "TMP"):
        value = os.environ.get(var)
        if value:
            out.append(Path(value) / name)

                                                               
                                                                          
    try:
        out.append(Path.cwd() / name)
    except Exception:
        pass

                                                                     
                                                                  
    seen = set()
    unique = []
    for p in out:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)

    return unique


def _trim_log(path: Path) -> str:
    pass
    try:
        if path.is_file() and path.stat().st_size > LOG_MAX_BYTES:
            data = path.read_bytes()[-LOG_KEEP_BYTES:]
                                                                         
            cut = data.find(b"\n")
            if cut >= 0:
                data = data[cut + 1:]
            return data.decode("utf-8", errors="replace")
    except Exception:
        pass
    return ""


def write_error_log(text: str, name: str = LOG_NAME) -> Optional[Path]:
    pass











    if not text:
        return None

    header = f"--- Rizpaq error {datetime.now().isoformat(timespec='seconds')} ---"
    body = header + "\n" + text
    if not body.endswith("\n"):
        body += "\n"

    for path in _log_candidates(name):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            previous = _trim_log(path)

            if previous:
                                                                 
                                                                       
                                          
                with path.open("w", encoding="utf-8") as f:
                    f.write("... (предыдущая запись обрезана) ...\n")
                    f.write(previous)
                    f.write(body)
            else:
                                                                       
                                     
                with path.open("a", encoding="utf-8") as f:
                    f.write(body)
            return path
        except Exception:
            continue

    return None


                                                                             
                                                   
                                                                             

def _coerce_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    return None


def _coerce_bool(v: Any, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    return default


def _coerce_str_list(v: Any) -> Optional[list]:
    pass






    if not isinstance(v, list):
        return None
    out = []
    for item in v:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
    return out or []


def _coerce_int_or_none(v: Any) -> Optional[int]:
    pass
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    return None


def _coerce_int_list(v: Any, length: int) -> Optional[list]:
    pass
    if not isinstance(v, list) or len(v) != length:
        return None
    out = []
    for x in v:
        if isinstance(x, bool) or not isinstance(x, int):
            try:
                x = int(x)
            except (TypeError, ValueError):
                return None
        out.append(x)
    return out


def _coerce_sort_column(v: Any) -> Optional[int]:
    pass
    if isinstance(v, bool):
        return None
    if isinstance(v, int) and 0 <= v <= 4:
        return v
    return None


def _from_dict(data: dict) -> Settings:
    pass
    s = Settings()
    s.zpaq_path = _coerce_str(data.get("zpaq_path"))
    s.seven_zip_path = _coerce_str(data.get("seven_zip_path"))
    s.last_fs_path = _coerce_str(data.get("last_fs_path"))
    s.last_extract_dir = _coerce_str(data.get("last_extract_dir"))
    s.tasks_dir = _coerce_str(data.get("tasks_dir"))
    s.language = _coerce_str(data.get("language"))
    s.skin = _coerce_str(data.get("skin"))
    s.profile = _coerce_str(data.get("profile"))
    s.latest_only = _coerce_bool(data.get("latest_only"), False)
    s.window_maximized = _coerce_bool(data.get("window_maximized"), False)
    s.window_geometry = _coerce_int_list(data.get("window_geometry"), 4)
    s.left_split = _coerce_int_list(data.get("left_split"), 2)
    s.right_sort_column = _coerce_sort_column(data.get("right_sort_column"))
    s.right_sort_desc = _coerce_bool(data.get("right_sort_desc"), False)
                                                                   
                                                                     
                                                                     
                                               
    s.associations_asked = _coerce_bool(data.get("associations_asked"), False)
                                                                        
                                                                   
    s.engine_stall_timeout = _coerce_int_or_none(
        data.get("engine_stall_timeout"))
    s.catalog_roots = _coerce_str_list(data.get("catalog_roots"))
    s.catalog_index_on_scan = _coerce_bool(
        data.get("catalog_index_on_scan"), True)
    s.update_url = _coerce_str(data.get("update_url"))
    s.update_check_enabled = _coerce_bool(
        data.get("update_check_enabled"), True)
    s.last_update_check = _coerce_int_or_none(
        data.get("last_update_check"))
    s.skipped_version = _coerce_str(data.get("skipped_version"))
    s.last_close = _coerce_int_or_none(data.get("last_close"))
    s.digest_enabled = _coerce_bool(data.get("digest_enabled"), True)
    return s


                                                                             
                 
                                                                             

def load(path: Optional[Path] = None) -> Settings:
    pass



    p = Path(path) if path else default_path()
    if not path:
        _maybe_migrate(p)
    if not p.is_file():
        return Settings()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return Settings()
    try:
        data = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return Settings()
    if not isinstance(data, dict):
        return Settings()
    return _from_dict(data)


def save(settings: Settings, path: Optional[Path] = None) -> None:
    pass



    p = Path(path) if path else default_path()
    payload = asdict(settings)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=".zpaq_gui_cfg_",
            suffix=".tmp",
            dir=str(p.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.replace(tmp_name, str(p))
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
    except OSError:
        return


def update(path: Optional[Path] = None, **changes: Any) -> Settings:
    pass



    s = load(path)
    known = {f.name for f in fields(Settings)}
    for k, v in changes.items():
        if k in known:
            setattr(s, k, v)
    save(s, path)
    return s


                                                                
                                                                   
                                                             
_STALL_MIN_S = 5
_STALL_MAX_S = 3600


def engine_stall_timeout(default: float, path: Optional[Path] = None) -> float:
    pass






    try:
        value = load(path).engine_stall_timeout
    except Exception:
        return float(default)
    if value is None:
        return float(default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        return float(default)
    return float(min(max(value, _STALL_MIN_S), _STALL_MAX_S))
