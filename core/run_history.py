





















from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.tasks import container_path

_SEP = "=" * 50
_HEADER_PREFIX = "--- Rizpaq task run "
_TAIL_MARKER = "--- Last output lines ---"

                                                                  
_MAX_TAIL = 10


@dataclass
class RunEntry:
    pass

    ts: str = ""                                                
    ts_dt: Optional[datetime] = None                                    
    work_id: str = ""
    work_title: str = ""
    job_id: str = ""
    job_title: str = ""
    action: str = ""
    rc: Optional[int] = None
    status: str = "ok"                              
    tail: tuple[str, ...] = field(default_factory=tuple)


def log_path_for(tasks_dir) -> Path:
    pass
    return Path(str(container_path(tasks_dir)) + ".log")


def load_history(tasks_dir, limit: Optional[int] = None) -> list[RunEntry]:
    pass





    path = log_path_for(tasks_dir)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    entries = parse_log(text)
    if limit is not None and limit > 0:
        entries = entries[:limit]
    return entries


def parse_log(text: str) -> list[RunEntry]:
    pass
    entries: list[RunEntry] = []
    if not text:
        return entries

    lines = text.splitlines()
                                                               
    starts = [
        i for i, ln in enumerate(lines) if ln.startswith(_HEADER_PREFIX)
    ]
    for n, start in enumerate(starts):
                                                                    
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        entry = _parse_record(lines[start:end])
        if entry is not None:
            entries.append(entry)

                                                                       
                                                 
    entries.reverse()
    return entries


def _parse_record(lines: list[str]) -> Optional[RunEntry]:
    pass
    entry = RunEntry()

    header = lines[0][len(_HEADER_PREFIX):].strip()
    if header.endswith("---"):
        header = header[:-3].strip()
    entry.ts = header
    try:
        entry.ts_dt = datetime.fromisoformat(header)
    except ValueError:
        entry.ts_dt = None

    tail_start: Optional[int] = None
    seen_status = False
    for i, ln in enumerate(lines[1:], start=1):
        stripped = ln.strip()
        if stripped.startswith("Work id:"):
            entry.work_id = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Work:"):
            entry.work_title = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Job id:"):
            entry.job_id = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Job:"):
            entry.job_title = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Action:"):
            entry.action = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Return code:"):
            try:
                entry.rc = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                entry.rc = None
        elif stripped.startswith("Status:"):
            seen_status = True
            body = stripped.split(":", 1)[1].strip()
            if body.startswith("OK"):
                entry.status = "ok"
            elif body.startswith("BUSY"):
                entry.status = "busy"
            else:
                entry.status = "error"
        elif stripped == _TAIL_MARKER:
            tail_start = i + 1

                                                                
    if not seen_status and entry.rc is not None:
        entry.status = "ok" if entry.rc == 0 else "error"

    if tail_start is not None:
        tail = [
            ln.strip() for ln in lines[tail_start:] if ln.strip()
            and ln.strip() != _SEP
        ]
        entry.tail = tuple(tail[:_MAX_TAIL])

    return entry
