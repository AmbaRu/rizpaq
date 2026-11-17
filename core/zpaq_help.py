










from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

REFERENCE_NAME = "zpaqfranz-commands.md"
BUILTIN_NAME = "zpaqfranz-help-builtin-ru.txt"

WIKI_URL = "https://github.com/fcorbelli/zpaqfranz/wiki/Command"

                                               
_MD_HEADING = re.compile(
    r"^###\s+([A-Za-z0-9()]+(?:\s*/\s*[A-Za-z0-9()]+)*)\s+[-—]\s+(.+?)\s*$"
)
_BUILTIN_HEADING = re.compile(r"^CMD\s+([A-Za-z0-9()]+)\b\s*(.*)$")


def _project_doc() -> Path:
    pass
    return Path(__file__).resolve().parent.parent / "doc"


def _exe_dir() -> Path:
    pass
    return Path(sys.executable).resolve().parent


def find_reference_root() -> Optional[Path]:
    pass



    exe = _exe_dir()
    for cand in (exe / "help", exe / "_internal" / "help", _project_doc()):
        try:
            if (cand / REFERENCE_NAME).is_file() or (
                cand / BUILTIN_NAME
            ).is_file():
                return cand
        except OSError:
            continue
    return None


def reference_path(root: Optional[Path] = None) -> Optional[Path]:
    pass
    root = root or find_reference_root()
    if root is None:
        return None
    path = root / REFERENCE_NAME
    return path if path.is_file() else None


def builtin_path(root: Optional[Path] = None) -> Optional[Path]:
    pass
    root = root or find_reference_root()
    if root is None:
        return None
    path = root / BUILTIN_NAME
    return path if path.is_file() else None


def _read(path: Optional[Path]) -> str:
    if path is None:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _names_from_markdown(text: str) -> list[tuple[str, str]]:
    found = []
    for line in text.splitlines():
        m = _MD_HEADING.match(line)
        if not m:
            continue
        names = [n.strip().lower() for n in m.group(1).split("/")]
        for name in names:
            found.append((name, m.group(2).strip()))
    return found


def _names_from_builtin(text: str) -> list[tuple[str, str]]:
    found = []
    for line in text.splitlines():
        m = _BUILTIN_HEADING.match(line)
        if not m:
            continue
        desc = m.group(2).strip()
        if desc:
            found.append((m.group(1).strip().lower(), desc))
    return found


def commands(root: Optional[Path] = None) -> list[tuple[str, str]]:
    pass




    md = _names_from_markdown(_read(reference_path(root)))
    builtin = _names_from_builtin(_read(builtin_path(root)))

    seen: dict[str, str] = {}
    for name, desc in builtin:
        seen.setdefault(name, desc)
    for name, desc in md:
        seen[name] = desc                                                
    return sorted(seen.items(), key=lambda item: item[0])


def _section_from_markdown(text: str, name: str) -> Optional[tuple[str, str]]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _MD_HEADING.match(line)
        if not m:
            continue
        names = [n.strip().lower() for n in m.group(1).split("/")]
        if name not in names:
            continue
        title = m.group(2).strip()
        body = []
        for follow in lines[i + 1 :]:
            if follow.startswith("### ") or follow.startswith("## "):
                break
            body.append(follow)
        return title, "\n".join(body).strip()
    return None


def _section_from_builtin(text: str, name: str) -> Optional[tuple[str, str]]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _BUILTIN_HEADING.match(line)
        if not m or m.group(1).strip().lower() != name:
            continue
        title = m.group(2).strip()
        body = [line]
        for follow in lines[i + 1 :]:
            if _BUILTIN_HEADING.match(follow) or follow.startswith("---"):
                break
            body.append(follow)
        return title, "\n".join(body).rstrip()
    return None


def lookup(command: str, root: Optional[Path] = None) -> Optional[dict]:
    pass




    name = (command or "").strip().lower().lstrip("-")
    if not name:
        return None
                                                                             
    name = name.split()[0]

    md_text = _read(reference_path(root))
    section = _section_from_markdown(md_text, name)
    if section is not None:
        return {
            "name": name,
            "title": section[0],
            "text": section[1],
            "source": REFERENCE_NAME,
        }

    builtin_text = _read(builtin_path(root))
    section = _section_from_builtin(builtin_text, name)
    if section is not None:
        return {
            "name": name,
            "title": section[0],
            "text": section[1],
            "source": BUILTIN_NAME,
        }
    return None


def search(query: str, root: Optional[Path] = None, limit: int = 100) -> list[dict]:
    pass





    q = (query or "").strip().lower()
    result = []
    for name, desc in commands(root):
        if q and q not in name and q not in desc.lower():
            continue
        result.append({"name": name, "title": desc, "snippet": ""})
        if len(result) >= limit:
            break
    return result
