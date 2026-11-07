
































































































































from __future__ import annotations

import base64
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

                                                                  
                                                                    
                                                     
from core.container_lock import ContainerLockBusy, container_lock

__all__ = [
    "CONTAINER_FORMAT",
    "CONTAINER_VERSION",
    "CONTAINER_NAME",
    "WORK_FIELDS",
    "JOB_FIELDS",
    "ACTION_BACKUP",
    "ACTION_TEST",
    "ACTIONS",
    "TEST_MODE_FULL",
    "TEST_MODE_CHECKSUM",
    "TEST_MODE_VERIFY",
    "TEST_MODE_PARANOID",
    "TEST_MODE_PAR2",
    "TEST_MODES",
    "JOB_STATUS_OK",
    "JOB_STATUS_ERROR",
    "JOB_STATUS_BUSY",
    "JOB_STATUSES",
    "LOG_MODE_SHORT",
    "LOG_MODE_FULL",
    "LOG_MODE_NONE",
    "LOG_MODES",
    "ContainerLockBusy",
    "container_path",
    "empty_container",
    "load_container",
    "save_container",
    "update_container",
    "iter_jobs",
    "iter_container_meta",
    "find_work",
    "find_job",
    "add_work",
    "update_work",
    "remove_work",
    "add_job",
    "update_job",
    "remove_job",
    "update_job_meta",
    "JOB_REASONS",
    "PAR2_REASON_BY_STATE",
    "job_to_runnable_settings",
    "work_slug",
    "scheduler_task_name",
    "new_id",
]

                                                                   
                                                                  
                                                  
CONTAINER_FORMAT = "rizpaq.tasks"
CONTAINER_VERSION = 1

                                                                  
                                                                     
CONTAINER_NAME = "tasks.rzp"

                                                                 
                                                                  
          
 
                                                                    
                                                                      
                                                                    
                                                                    
WORK_FIELDS = (
    "title",
    "sources",
    "dest",
    "password_b64",
    "only_masks",
    "not_masks",
    "comment",
                                                                     
                                                                     
                              
     
                                                                       
                                                                        
                                                                       
                                              
     
                                                                    
                                                                    
                                                                   
                                                                 
    "par2_size",
    "par2_created",
)

                                                                      
                                                            
 
                                                                 
                                                     
                                                              
                                                                    
                                          
 
                                                            
                                                                      
                                                                  
                                                                 
                                                              
                                                                   
                     
JOB_FIELDS = (
    "action",
    "test_mode",
    "level",
    "level_key",
    "hash",
    "hash_key",
    "method_params",
    "verify",
    "longpath",
    "date",
    "norecursion",
    "forcewindows",
    "force_xls",
    "nochecksum",
    "nodedup",
    "vss",
    "checkspace",
    "noonedrive",
    "ignore",
    "errorlog",
    "shutdown",
    "sfx",
    "chunk",
    "copy",
    "schedule",
    "task_log_mode",
                                                                  
                                                                   
                                                      
    "par2_enabled",
    "par2_options",
)

                                                                    
                                                                    
ACTION_BACKUP = "backup"
ACTION_TEST = "test"
                                                                  
                                                                 
                                                            
ACTION_CROP = "crop"
                                                                
                                                         
ACTION_CONSOLIDATE = "consolidate"
                                                          
                                                            
ACTION_SFX = "sfx"
                                                                       
                                              
ACTION_INFO = "info"
                                                                      
                               
ACTION_PASSWORD = "password"
                                                                           
ACTION_CHECKPASSWORD = "checkpassword"
ACTIONS = (ACTION_BACKUP, ACTION_TEST, ACTION_CROP, ACTION_CONSOLIDATE, ACTION_SFX, ACTION_INFO, ACTION_PASSWORD, ACTION_CHECKPASSWORD)

                                                                   
                                                                 
                                
TEST_MODE_FULL = "full"
TEST_MODE_CHECKSUM = "checksum"
TEST_MODE_VERIFY = "verify"
TEST_MODE_PARANOID = "paranoid"
                                                                     
                                                                        
                                                                
                                                   
TEST_MODE_PAR2 = "par2"
                                                               
                                                                   
                                                                  
                                               
TEST_MODE_VERIFY_FS = "verify_fs"
TEST_MODES = (
    TEST_MODE_FULL,
    TEST_MODE_CHECKSUM,
    TEST_MODE_VERIFY,
    TEST_MODE_PARANOID,
    TEST_MODE_PAR2,
    TEST_MODE_VERIFY_FS,
)

                                                 
 
                                                                
                                                       
                                                                   
                                                                   
        
 
                                                                    
                                                              
                                                            
                           
JOB_STATUS_OK = "ok"
JOB_STATUS_ERROR = "error"
JOB_STATUS_BUSY = "busy"
JOB_STATUSES = (JOB_STATUS_OK, JOB_STATUS_ERROR, JOB_STATUS_BUSY)

                                                           
 
                                                                
                                                                  
                                                                 
                                              
 
                                                                 
                                                                  
                                                              
                                                                
                       
REASON_PAR2_MISSING = "par2_missing"                                    
REASON_PAR2_BROKEN = "par2_broken"                                      
REASON_PAR2_DAMAGED = "par2_damaged"                                  
REASON_PAR2_UNREPAIRABLE = "par2_unrepairable"                          
REASON_PAR2_FAILED = "par2_failed"                                         
JOB_REASONS = (
    REASON_PAR2_MISSING,
    REASON_PAR2_BROKEN,
    REASON_PAR2_DAMAGED,
    REASON_PAR2_UNREPAIRABLE,
    REASON_PAR2_FAILED,
)

                                                                
                                                                    
                                                               
                                                                    
                                                                 
PAR2_REASON_BY_STATE = {
    "missing": REASON_PAR2_MISSING,
    "broken": REASON_PAR2_BROKEN,
    "damaged": REASON_PAR2_DAMAGED,
    "unrepairable": REASON_PAR2_UNREPAIRABLE,
    "failed": REASON_PAR2_FAILED,
}


                                                                  
                                                         
_RUNTIME_ONLY_KEYS = frozenset({"params_rows", "password"})

                                                                  
                                                 
LOG_MODE_SHORT = "short"
LOG_MODE_FULL = "full"
LOG_MODE_NONE = "none"
LOG_MODES = (LOG_MODE_SHORT, LOG_MODE_FULL, LOG_MODE_NONE)


                                                                             
           
                                                                             

def _now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def new_id() -> str:
    pass
    return str(uuid.uuid4())


def _encode_password(password: Optional[str]) -> Optional[str]:
    if not password:
        return None
    return base64.b64encode(str(password).encode("utf-8")).decode("ascii")


def _decode_password(encoded: Optional[str]) -> Optional[str]:
    if not encoded:
        return None
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        return None


def _norm_action(value) -> str:
    pass







    return value if value in ACTIONS else ACTION_BACKUP


def _norm_test_mode(value) -> str:
    pass
    return value if value in TEST_MODES else TEST_MODE_FULL


def _norm_par2_size(value) -> Optional[int]:
    pass







    if value is None:
        return None
    try:
        size = int(value)
    except (TypeError, ValueError):
        return None
                                                            
    return size if size >= 0 else None


def _norm_status(value) -> Optional[str]:
    pass









    return value if value in JOB_STATUSES else None


def _norm_reason(value) -> Optional[str]:
    pass







    return value if value in JOB_REASONS else None


def container_path(tasks_dir) -> Path:
    pass






    return Path(tasks_dir) / CONTAINER_NAME


                                                                             
                 
                                                                             

def empty_container(name: Optional[str] = None) -> dict:
    pass
    now = _now()
    return {
        "format": CONTAINER_FORMAT,
        "version": CONTAINER_VERSION,
        "name": str(name or "").strip() or None,
        "created": now,
        "modified": now,
        "works": [],
    }


def _validate(data: Any) -> Optional[dict]:
    pass






    if not isinstance(data, dict):
        return None
    if data.get("format") != CONTAINER_FORMAT:
        return None
    works = data.get("works")
    if not isinstance(works, list):
        return None

                                                                    
                                                                      
                                                                       
               
    out = empty_container(data.get("name"))
    out["created"] = str(data.get("created") or out["created"])
    out["modified"] = str(data.get("modified") or out["modified"])

    for w in works:
        if not isinstance(w, dict):
            continue
        work = _normalise_work(w)
        if work is not None:
            out["works"].append(work)

    return out


def _normalise_work(w: dict) -> Optional[dict]:
    wid = w.get("id")
    if not isinstance(wid, str) or not wid:
                                                                   
                                                                      
        return None

    work = {
        "id": wid,
        "title": str(w.get("title") or "").strip() or "Работа",
        "created": str(w.get("created") or _now()),
        "modified": str(w.get("modified") or _now()),
        "sources": [str(s) for s in (w.get("sources") or []) if str(s).strip()],
        "dest": str(w.get("dest") or ""),
        "password_b64": w.get("password_b64") or None,
        "only_masks": [str(m) for m in (w.get("only_masks") or [])],
        "not_masks": [str(m) for m in (w.get("not_masks") or [])],
        "comment": str(w.get("comment") or ""),
                                                                      
                                                         
        "par2_size": _norm_par2_size(w.get("par2_size")),
        "par2_created": str(w.get("par2_created") or "") or None,
        "jobs": [],
    }

    for j in w.get("jobs") or []:
        if not isinstance(j, dict):
            continue
        job = _normalise_job(j)
        if job is not None:
            work["jobs"].append(job)

    return work


def _normalise_job(j: dict) -> Optional[dict]:
    jid = j.get("id")
    if not isinstance(jid, str) or not jid:
        return None

    job: Dict[str, Any] = {
        "id": jid,
        "title": str(j.get("title") or "").strip() or "Задание",
        "created": str(j.get("created") or _now()),
        "modified": str(j.get("modified") or _now()),
        "last_run": j.get("last_run"),
                                                               
                                                            
                                                           
        "last_status": _norm_status(j.get("last_status")),
                                                            
                                                                     
        "last_reason": _norm_reason(j.get("last_reason")),
        "run_count": int(j.get("run_count") or 0),
        "schedule": j.get("schedule") if isinstance(j.get("schedule"), dict) else None,
        "task_log_mode": j.get("task_log_mode") if j.get("task_log_mode") in LOG_MODES else LOG_MODE_SHORT,
                                                                      
                                                                     
        "action": _norm_action(j.get("action")),
                                                                 
                                                                 
                                                 
        "test_mode": _norm_test_mode(j.get("test_mode")),
    }
    for key in JOB_FIELDS:
        if key in ("schedule", "task_log_mode", "action", "test_mode"):
            continue
        job[key] = j.get(key)
    return job


def load_container(path) -> dict:
    pass












    p = Path(path)
    if not p.is_file():
        return empty_container()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return empty_container()
    try:
        data = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return empty_container()
    normalised = _validate(data)
    if normalised is None:
        return empty_container()
    return normalised


def save_container(path, container: dict) -> None:
    pass
















    p = Path(path)
    container["modified"] = _now()

    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".tasks_rzp_", suffix=".tmp", dir=str(p.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(container, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, str(p))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def update_container(
    path,
    mutate: Callable[[dict], None],
) -> dict:
    pass









































    with container_lock(path):
        container = load_container(path)
        mutate(container)
        save_container(path, container)
        return container


                                                                             
               
                                                                             

def iter_jobs(container: dict) -> List[Tuple[dict, dict]]:
    pass










    out: List[Tuple[dict, dict]] = []
    for work in container.get("works") or []:
        for job in work.get("jobs") or []:
            out.append((work, job))
    return out


def find_work(container: dict, work_id: str) -> Optional[dict]:
    for work in container.get("works") or []:
        if work.get("id") == work_id:
            return work
    return None


def find_job(container: dict, job_id: str) -> Optional[Tuple[dict, dict]]:
    pass
    for work, job in iter_jobs(container):
        if job.get("id") == job_id:
            return work, job
    return None


                                                                             
           
                                                                             

def add_work(
    container: dict,
    title: str,
    sources: List[str],
    dest: str,
    password: Optional[str] = None,
    only_masks: Optional[List[str]] = None,
    not_masks: Optional[List[str]] = None,
    comment: str = "",
) -> dict:
    pass





    now = _now()
    work = {
        "id": new_id(),
        "title": str(title or "").strip() or "Работа",
        "created": now,
        "modified": now,
        "sources": [str(s) for s in (sources or []) if str(s).strip()],
        "dest": str(dest or ""),
        "password_b64": _encode_password(password),
        "only_masks": [str(m) for m in (only_masks or [])],
        "not_masks": [str(m) for m in (not_masks or [])],
        "comment": str(comment or ""),
        "jobs": [],
    }
    container.setdefault("works", []).append(work)
    return work


def update_work(container: dict, work_id: str, **fields) -> Optional[dict]:
    pass












    work = find_work(container, work_id)
    if work is None:
        return None
    for key, value in fields.items():
        if key == "password":
            work["password_b64"] = _encode_password(value)
            continue
        if key == "title":
            text = str(value or "").strip()
            if text:
                work["title"] = text
            continue
        if key in WORK_FIELDS:
            work[key] = value
    work["modified"] = _now()
    return work


def remove_work(container: dict, work_id: str) -> bool:
    works = container.get("works") or []
    for i, work in enumerate(works):
        if work.get("id") == work_id:
            del works[i]
            return True
    return False


def add_job(container: dict, work_id: str, settings: dict) -> Optional[dict]:
    pass
















    work = find_work(container, work_id)
    if work is None:
        return None

    now = _now()
    job: Dict[str, Any] = {
        "id": new_id(),
        "title": str(settings.get("title") or "").strip() or "Задание",
        "created": now,
        "modified": now,
        "last_run": None,
        "last_status": None,
        "last_reason": None,
        "run_count": 0,
        "schedule": settings.get("schedule"),
        "task_log_mode": (
            settings.get("task_log_mode")
            if settings.get("task_log_mode") in LOG_MODES
            else LOG_MODE_SHORT
        ),
        "action": _norm_action(settings.get("action")),
        "test_mode": _norm_test_mode(settings.get("test_mode")),
    }
    for key in JOB_FIELDS:
        if key in ("schedule", "task_log_mode", "action", "test_mode"):
            continue
                                                             
        if key in _RUNTIME_ONLY_KEYS:
            continue
        job[key] = settings.get(key)
    work.setdefault("jobs", []).append(job)
    return job


def update_job(container: dict, job_id: str, **fields) -> Optional[dict]:
    pass














    found = find_job(container, job_id)
    if found is None:
        return None
    _work, job = found
    for key, value in fields.items():
        if key == "title":
            job["title"] = str(value or "").strip() or job["title"]
            continue
        if key == "task_log_mode":
            if value in LOG_MODES:
                job["task_log_mode"] = value
            continue
        if key == "action":
            job["action"] = _norm_action(value)
            continue
        if key == "test_mode":
            job["test_mode"] = _norm_test_mode(value)
            continue
        if key in JOB_FIELDS:
            job[key] = value
    job["modified"] = _now()
    return job


def remove_job(container: dict, job_id: str) -> bool:
    for work in container.get("works") or []:
        jobs = work.get("jobs") or []
        for i, job in enumerate(jobs):
            if job.get("id") == job_id:
                del jobs[i]
                return True
    return False


def update_job_meta(container: dict, job_id: str, status: str,
                    reason: Optional[str] = None) -> bool:
    pass














    found = find_job(container, job_id)
    if found is None:
        return False
    _work, job = found
    if status not in JOB_STATUSES:
        status = JOB_STATUS_ERROR
    job["last_run"] = _now()
    job["last_status"] = status
    job["last_reason"] = _norm_reason(reason) if status != JOB_STATUS_OK else None
    job["run_count"] = int(job.get("run_count") or 0) + 1
    return True


                                                                             
                                                   
                                                                             

def job_to_runnable_settings(work: dict, job: dict) -> dict:
    pass



















    settings: Dict[str, Any] = {
        "sources": list(work.get("sources") or []),
        "dest": work.get("dest") or "",
        "password": _decode_password(work.get("password_b64")),
        "only_masks": list(work.get("only_masks") or []),
        "not_masks": list(work.get("not_masks") or []),
        "comment": work.get("comment") or "",
    }
                                                                
                                                                     
                                          
    settings["title"] = job.get("title") or ""
    settings["work_title"] = work.get("title") or ""
    for key in JOB_FIELDS:
        settings[key] = job.get(key)
                                                
    settings["schedule"] = job.get("schedule")
    settings["task_log_mode"] = job.get("task_log_mode") or LOG_MODE_SHORT
    return settings


                                                                             
                     
                                                                             

def work_slug(title: str, max_len: int = 20) -> str:
    pass











    try:
        from core.archive_naming import transliterate
    except Exception:
        transliterate = lambda s: s              

    cleaned = transliterate(str(title or "")).strip("_-.")
    if not cleaned:
        cleaned = "work"
                                                                     
    cleaned = "_".join(p for p in cleaned.replace(" ", "_").split("_") if p)
    if not cleaned:
        cleaned = "work"
    return cleaned[:max_len]


def scheduler_task_name(work: dict, job: dict) -> str:
    pass















    import hashlib

    slug = work_slug(work.get("title") or "")
    job_id = str(job.get("id") or "")
    jid8 = job_id.replace("-", "")[:8] or "00000000"
    seed = f"{work.get('id','')}:{job_id}".encode("utf-8", "replace")
    h8 = hashlib.md5(seed).hexdigest()[:8]
    prefix = "t" if job.get("action") == ACTION_TEST else "b"
    return f"Rizpaq_{prefix}_{slug}_{jid8}_{h8}"


                                                                             
                              
                                                                             

def iter_container_meta(container: dict) -> List[dict]:
    pass












    out: List[dict] = []
    for work in container.get("works") or []:
        size = _archive_size(work.get("dest") or "")
        out.append({"kind": "work", "work": work, "size": size})
        for job in work.get("jobs") or []:
            out.append({"kind": "job", "work": work, "job": job, "size": size})
    return out


def _archive_size(dest: str) -> Optional[int]:
    pass





    if not dest:
        return None
    try:
        d = str(dest)
        if "?" in d:
            return None
        p = Path(d)
        if not p.is_file():
            return None
        return p.stat().st_size
    except Exception:
        return None
