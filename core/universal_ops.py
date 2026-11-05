from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple

from core.models import ArchiveEntry


def find_7z() -> Optional[str]:
    env_bin = os.environ.get("SEVEN_ZIP_BIN")
    if env_bin and os.path.isfile(env_bin):
        return env_bin


    if not getattr(sys, "frozen", False):
        try:
            here = Path(__file__).resolve().parent.parent
            cand = here / "7z.exe"
            if cand.is_file():
                return str(cand)
        except Exception:
            pass


    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "7-Zip" / "7z.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "7-Zip" / "7z.exe",
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
    return None


def check_7z(bin_path: str) -> bool:

    if not bin_path or not os.path.isfile(bin_path):
        return False
    try:
        res = subprocess.run(
            [bin_path, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return b"7-Zip" in res.stdout or res.returncode in (0, 7)
    except Exception:
        return False


def _popen_kwargs() -> dict:

    kw = {}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


def _decode(data: bytes) -> str:

    if not data:
        return ""
    for enc in ("utf-8", "cp1251", "cp866", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def mask_password(text: str, password: Optional[str]) -> str:
    if not text:
        return text
    if not password:
        return text


    needle = "-p" + password
    masked = text.replace(needle, "-p***")


    if password in masked:
        masked = masked.replace(password, "***")
    return masked


def list_universal(
    bin_path: str,
    archive_path: str,
    password: Optional[str] = None
) -> Tuple[List[ArchiveEntry], str]:

    cmd = [bin_path, "l", "-slt", "-ba", "-sccUTF-8", archive_path]
    if password:


        cmd += [f"-p{password}"]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,


            stdin=subprocess.DEVNULL,
            timeout=300,
            **_popen_kwargs(),
        )
        raw_text = _decode(proc.stdout)
    except Exception as e:


        return [], f"Error running 7z: {mask_password(str(e), password)}"

    entries = []
    current = {}

    def _process_block(block: dict):
        path = block.get("Path", "")
        if not path:
            return

        size_str = block.get("Size", "0")
        try:
            size = int(size_str) if size_str else 0
        except ValueError:
            size = 0

        attr = block.get("Attributes", "")
        is_dir = "D" in attr.upper()

        clean_path = path.replace("\\", "/")
        if is_dir:
            clean_path = clean_path.rstrip("/")

        entries.append(
            ArchiveEntry(
                path=clean_path,
                size=size,
                datetime=block.get("Modified", ""),
                version=None,
                flag="+",
                is_dir=is_dir,
                attr=attr,
                ratio="",
                raw="",
            )
        )

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            if current:
                _process_block(current)
                current = {}
            continue

        if " = " in line:
            key, _, val = line.partition(" = ")
            current[key.strip()] = val.strip()

    if current:
        _process_block(current)

    return entries, raw_text
