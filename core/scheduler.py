



































from __future__ import annotations

import csv
import io
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.tasks import scheduler_task_name

                                                                     
                                                                
                                                               
                       
TASK_PREFIX = "Rizpaq_"

                                                                   
                                                                   
                                                                 
                                                                      
SCHTASKS_TIMEOUT = 20


def _run_schtasks(cmd: list) -> "subprocess.CompletedProcess | None":
    pass






    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            timeout=SCHTASKS_TIMEOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return None


def _schtasks_bin() -> str:
    return "schtasks.exe" if os.name == "nt" else "schtasks"


def _runner_exe() -> Optional[str]:
    pass









    if not getattr(sys, "frozen", False):
        return None
    try:
        cand = Path(sys.executable).resolve().parent / "rizpaq_task.exe"
    except Exception:
        return None
    return str(cand) if cand.is_file() else None


def _rizpaq_cmd() -> str:
    pass
    runner = _runner_exe()
    if runner:
        return f'"{runner}"'
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    here = Path(__file__).resolve().parent.parent
    main_py = here / "main.py"
    return f'"{sys.executable}" "{main_py}"'


                                                                             
                      
                                                                             

def _exec_cmd_for(rzp_path, job_id: str) -> str:
    pass






    rizpaq = _rizpaq_cmd()
    return f'{rizpaq} --task "{rzp_path}" --job "{job_id}"'


def create_scheduled_task(
    rzp_path,
    work: dict,
    job: dict,
    schedule: dict,
) -> bool:
    pass










    if os.name != "nt":
        return False

    task_name = scheduler_task_name(work, job)

    if not schedule or not schedule.get("enabled"):
        return remove_scheduled_task(work, job)

    frequency = schedule.get("frequency", "daily")
    time_str = schedule.get("time", "10:00")
    interval = max(1, int(schedule.get("interval", 1) or 1))
    days = schedule.get("days") or None
    day_of_month = schedule.get("day_of_month")

    cmd = [_schtasks_bin(), "/create", "/tn", task_name,
           "/tr", _exec_cmd_for(rzp_path, str(job.get("id") or "")),
           "/f"]

    if frequency == "minute":
        cmd += ["/sc", "minute", "/mo", str(interval)]
    elif frequency == "hourly":
        cmd += ["/sc", "hourly", "/mo", str(interval)]
    elif frequency == "daily":
        cmd += ["/sc", "daily", "/mo", str(interval)]
    elif frequency == "weekly":
        cmd += ["/sc", "weekly", "/mo", str(interval)]
        cmd += ["/d", ",".join(days) if days else "MON"]
    elif frequency == "monthly":
        cmd += ["/sc", "monthly", "/mo", str(interval)]
        cmd += ["/d", str(day_of_month or 1)]
    else:
        return False

    cmd += ["/st", time_str]

    result = _run_schtasks(cmd)
    return bool(result and result.returncode == 0)


def remove_scheduled_task(work: dict, job: dict) -> bool:
    pass
    if os.name != "nt":
        return False
    return remove_scheduled_task_by_name(scheduler_task_name(work, job))


def remove_scheduled_task_by_name(task_name: str) -> bool:
    pass






    if os.name != "nt" or not task_name:
        return False
    cmd = [_schtasks_bin(), "/delete", "/tn", task_name, "/f"]
    result = _run_schtasks(cmd)
    return bool(result and result.returncode == 0)


                                                                             
                    
                                                                             

def _decode_schtasks_output(data: bytes) -> str:
    pass
    for enc in ("utf-8", "cp866", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def list_rizpaq_tasks() -> List[Dict[str, str]]:
    pass
    if os.name != "nt":
        return []

    cmd = [_schtasks_bin(), "/query", "/fo", "CSV", "/nh"]
    result = _run_schtasks(cmd)
    if result is None or result.returncode != 0:
        return []

    try:
        stdout = _decode_schtasks_output(result.stdout)
        stdout = stdout.lstrip("\ufeff")

        tasks = []
        reader = csv.reader(io.StringIO(stdout))
        for row in reader:
            if len(row) < 2:
                continue
            name = row[0].strip().lstrip("\\")
            if not name.startswith(TASK_PREFIX):
                continue
            next_run = row[1].strip() if len(row) > 1 else ""
            status = row[2].strip() if len(row) > 2 else ""
            tasks.append({
                "name": name,
                "status": status,
                "next_run": next_run,
            })
        return tasks
    except Exception:
        return []


def is_task_scheduled(work: dict, job: dict) -> bool:
    pass
    if os.name != "nt":
        return False
    task_name = scheduler_task_name(work, job)
    cmd = [_schtasks_bin(), "/query", "/tn", task_name]
    result = _run_schtasks(cmd)
    return bool(result and result.returncode == 0)


def schedule_info_for_container(container: dict) -> dict:
    pass











    result: Dict[str, Dict[str, object]] = {}
    if os.name != "nt":
        return result

    try:
        tasks = list_rizpaq_tasks()
    except Exception:
        tasks = []

    by_name: Dict[str, Dict[str, str]] = {}
    for t in tasks or []:
        name = t.get("name")
        if name:
            by_name[name] = t

    from core.tasks import iter_jobs

    for work, job in iter_jobs(container):
        job_id = str(job.get("id") or "")
        if not job_id:
            continue
        try:
            name = scheduler_task_name(work, job)
        except Exception:
            continue
        entry = by_name.get(name)
        if entry is None:
            result[job_id] = {
                "scheduled": False,
                "next_run": "",
                "sched_status": "",
            }
        else:
            result[job_id] = {
                "scheduled": True,
                "next_run": entry.get("next_run", "") or "",
                "sched_status": entry.get("status", "") or "",
            }

    return result


                                                                             
                                                         
                                                                             

def container_task_map(container: dict) -> Dict[str, Tuple[dict, dict]]:
    pass













    if os.name != "nt":
        return {}

    from core.tasks import iter_jobs

    out: Dict[str, Tuple[dict, dict]] = {}
    try:
        for work, job in iter_jobs(container):
            try:
                name = scheduler_task_name(work, job)
            except Exception:
                continue
            if name:
                out[name] = (work, job)
    except Exception:
        return {}
    return out


                                                                             
                                        
                                                                             

def find_orphan_tasks(container: dict) -> List[Dict[str, str]]:
    pass











    if os.name != "nt":
        return []

    try:
        tasks = list_rizpaq_tasks()
    except Exception:
        return []

    known = set(container_task_map(container).keys())
    return [t for t in tasks if t.get("name") not in known]


def compute_sync_actions(
    container: dict,
    rzp_path,
) -> Dict[str, List]:
    pass























    empty = {"add": [], "remove": [], "disable": []}
    if os.name != "nt":
        return empty

    try:
        tasks = list_rizpaq_tasks()
    except Exception:
        tasks = []

    by_name: Dict[str, Dict[str, str]] = {}
    for t in tasks or []:
        name = t.get("name")
        if name:
            by_name[name] = t

    from core.tasks import iter_jobs

    add_list: List[Tuple[dict, dict]] = []
    disable_list: List[Tuple[dict, dict]] = []
    seen_names: set = set()

    for work, job in iter_jobs(container):
        try:
            name = scheduler_task_name(work, job)
        except Exception:
            continue
        seen_names.add(name)

        schedule = job.get("schedule")
        enabled = bool(schedule and schedule.get("enabled"))
        in_scheduler = name in by_name

        if enabled and not in_scheduler:
            add_list.append((work, job))
        elif not enabled and in_scheduler:
            disable_list.append((work, job))

    remove_list = [
        t for name, t in by_name.items()
        if name not in seen_names
    ]

    return {
        "add": add_list,
        "remove": remove_list,
        "disable": disable_list,
    }
