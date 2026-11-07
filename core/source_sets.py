




















from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

SOURCE_SET_FORMAT = "rizpaq.source-set"
SOURCE_SET_VERSION = 1


def build_source_set(name: str, nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    pass
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "format": SOURCE_SET_FORMAT,
        "version": SOURCE_SET_VERSION,
        "name": str(name or "").strip() or "source-set",
        "created": now,
        "modified": now,
        "selection": {
            "mode": "fs",
            "nodes": nodes,
        },
        "archive": {
            "dest": "",
            "level": "",
            "hash": "",
            "comment": "",
            "only": [],
            "not": [],
            "options": {},
            "password": {"set": False},
        },
    }


def save_source_set(path: Path, data: Dict[str, Any]) -> None:
    pass
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".source_set_",
        suffix=".tmp",
        dir=str(p.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, str(p))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def load_source_set(path: Path) -> Dict[str, Any]:
    pass
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid source set file")
    return data
