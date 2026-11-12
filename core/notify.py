





























from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

                                                   
MODE_OFF = "off"
MODE_ERRORS = "errors"
MODE_ALL = "all"
MODES = (MODE_OFF, MODE_ERRORS, MODE_ALL)

                                                                          
                                                 
_TIMEOUT = 10

                                                   
 
                                                                      
                                                                       
                                                                    
                                                                   
                                                                     
                                                                   
_RETRY_COUNT = 3
_RETRY_PAUSE = 2.0

                                                                       
                                                        
_MAX_TEXT = 3900

_strings_cache: dict = {}


def _log_failure(text: str) -> None:
    pass








    if not text:
        return
    try:
        from core import config as config_mod

        config_mod.write_error_log(text, name="rizpaq_notify.log")
    except Exception:
        pass


def _locales_dir() -> Path:
    pass
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        for candidate in (base / "locales", base / "_internal" / "locales"):
            if candidate.is_dir():
                return candidate
    here = Path(__file__).resolve().parent.parent
    return here / "locales"


def _read_strings(lang: str) -> dict:
    pass
    path = _locales_dir() / f"{lang}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    strings = data.get("strings")
    return strings if isinstance(strings, dict) else {}


def _strings(lang: str) -> dict:
    pass
    if lang in _strings_cache:
        return _strings_cache[lang]
    strings = _read_strings(lang)
    if lang != "en":
        fallback = _read_strings("en")
        if fallback:
            for key, value in fallback.items():
                strings.setdefault(key, value)
    _strings_cache[lang] = strings
    return strings


def current_language() -> str:
    pass
    try:
        from core import config as config_mod

        lang = str(getattr(config_mod.load(), "language", "") or "").strip()
        return lang or "en"
    except Exception:
        return "en"


def tr(key: str, **params) -> str:
    pass






    strings = _strings(current_language())
    value = strings.get(key)
    if value is None:
        value = _strings("en").get(key, key)
    try:
        return str(value).format(**params)
    except Exception:
        return str(value)


def should_notify(mode: str, status: str) -> bool:
    pass





    mode = str(mode or MODE_OFF).strip().lower()
    status = str(status or "").strip().lower()
    if status not in ("ok", "error"):
        return False
    if mode == MODE_ALL:
        return True
    if mode == MODE_ERRORS:
        return status == "error"
    return False


def format_job_message(
    work_title: str,
    job_title: str,
    status: str,
    archive: str = "",
    reason: str = "",
    when: Optional[datetime] = None,
) -> str:
    pass




    lines = []
    if str(status).strip().lower() == "ok":
        lines.append(tr("notify.message.title_ok"))
    else:
        lines.append(tr("notify.message.title_error"))
    if work_title:
        lines.append(tr("notify.message.work", name=work_title))
    if job_title:
        lines.append(tr("notify.message.job", name=job_title))
    if archive:
        lines.append(tr("notify.message.archive", path=archive))
    if reason:
        reason_text = tr(f"backup.reason.{reason}")
        if reason_text == f"backup.reason.{reason}":
            reason_text = str(reason)
        lines.append(tr("notify.message.reason", reason=reason_text))
    moment = when or datetime.now()
    lines.append(tr("notify.message.time", time=moment.strftime("%d.%m.%Y %H:%M")))
    text = "\n".join(lines)
    if len(text) > _MAX_TEXT:
        text = text[:_MAX_TEXT - 1] + "…"
    return text


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    pass
















    token = str(token or "").strip()
    chat_id = str(chat_id or "").strip()
    if not token or not chat_id or not text:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_error = ""
    for attempt in range(1, _RETRY_COUNT + 1):
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
                status = int(getattr(response, "status", 200))
                if 200 <= status < 300:
                    return True
                _log_failure(f"Telegram: HTTP {status}")
                return False
        except urllib.error.HTTPError as exc:
                                                                  
                                                                        
            detail = ""
            try:
                body = exc.read().decode("utf-8", "replace")
                data = json.loads(body)
                detail = str(data.get("description") or "")
            except Exception:
                detail = ""
                                                                          
                                                                              
            try:
                exc.close()
            except Exception:
                pass
                                                                 
            if exc.code == 429 and attempt < _RETRY_COUNT:
                time.sleep(_RETRY_PAUSE)
                continue
            _log_failure(f"Telegram: HTTP {exc.code} {detail}".strip())
            return False
        except Exception as exc:
                                                                               
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < _RETRY_COUNT:
                time.sleep(_RETRY_PAUSE)
                continue
            _log_failure(f"Telegram: {last_error}")
            return False
    return False


def notify_job(settings, work: dict, job: dict, status: str,
               reason: str = "", archive: str = "") -> bool:
    pass





    mode = str(getattr(settings, "notify_mode", MODE_OFF) or MODE_OFF)
    if not should_notify(mode, status):
        return False
    token = str(getattr(settings, "notify_telegram_token", "") or "")
    chat_id = str(getattr(settings, "notify_telegram_chat_id", "") or "")
    if not token.strip() or not chat_id.strip():
        return False
    if not archive:
        archive = str((work or {}).get("dest") or "")
    text = format_job_message(
        str((work or {}).get("title") or ""),
        str((job or {}).get("title") or ""),
        status,
        archive=archive,
        reason=reason or "",
    )
    return send_telegram(token, chat_id, text)


def notify_job_async(settings, work: dict, job: dict, status: str,
                     reason: str = "", archive: str = "") -> bool:
    pass






    if not should_notify(
        str(getattr(settings, "notify_mode", MODE_OFF) or MODE_OFF), status
    ):
        return False
    try:
        thread = threading.Thread(
            target=notify_job,
            args=(settings, work, job, status, reason, archive),
            daemon=True,
            name="rizpaq-notify",
        )
        thread.start()
        return True
    except Exception:
        return False
