











from __future__ import annotations

import hashlib
import os
import random
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

from core import index_refresh, parser
from core.zpaq_cli import run_zpaq

                                                                          
                                        
MAX_DRILL_SIZE = 64 << 20


def load_entries(zpaq_bin: str, dest: str, password: str = None) -> list:
    pass



    from core import archive_index

    try:
        st = os.stat(str(dest))
        entries = archive_index.load_entries(str(dest))
        if entries and archive_index.is_fresh(
            str(dest), st.st_mtime_ns, st.st_size
        ):
            return entries
    except Exception:
        pass

    cmd = index_refresh.build_list_cmd(str(zpaq_bin), str(dest), password)
    rc, output = run_zpaq(cmd)
    if rc != 0:
        raise RuntimeError("не удалось прочитать листинг архива: %s" % (
            (output or "").strip().splitlines()[-1:]
            or "код возврата %s" % rc
        ))
    entries, _report = parser.parse_csv_list_reported(output or "")
    return entries


def pick_entry(entries: list, choose: Optional[Callable] = None):
    pass



    candidates = []
    for entry in entries or []:
        if entry is None or getattr(entry, "is_dir", False):
            continue
        if str(getattr(entry, "flag", "") or "").strip() == "-":
            continue
        size = int(getattr(entry, "size", 0) or 0)
        if size <= 0 or size > MAX_DRILL_SIZE:
            continue
        candidates.append(entry)
    if not candidates:
        return None
    latest = max(int(getattr(e, "version", 0) or 0) for e in candidates)
    recent = [e for e in candidates
              if int(getattr(e, "version", 0) or 0) == latest]
    if choose is not None:
        return choose(recent)
    return random.choice(recent)


def extract_cmd(zpaq_bin: str, dest: str, entry, target: str,
                password: str = None) -> list:
    pass
                                                                     
                                                                            
                                                                       
                                                                          
                                                
    target = str(target)
    if not target.endswith(("\\", "/")):
        target += os.sep
    cmd = [str(zpaq_bin), "x", str(dest)]
    if password:
        cmd += ["-key", password]
    cmd.append(str(entry.path))
    version = getattr(entry, "version", None)
    if version:
        cmd += ["-until", str(version)]
    cmd += ["-to", str(target)]
    return cmd


def sha256_of(path) -> Optional[str]:
    pass
    try:
        digest = hashlib.sha256()
        with open(str(path), "rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _find_extracted(folder: str):
    pass
    try:
        for root, _dirs, files in os.walk(str(folder)):
            for name in files:
                return Path(root) / name
    except OSError:
        pass
    return None


def _source_for(entry, sources) -> Optional[Path]:
    pass
    try:
        relative = Path(str(entry.path))
        for source in sources or []:
            candidate = Path(str(source)) / relative
            if candidate.is_file():
                return candidate
    except Exception:
        pass
    return None


def run_restore_drill(zpaq_bin: str, dest: str, password: str = None,
                      sources=None, choose: Optional[Callable] = None) -> tuple:
    pass


    folder = tempfile.mkdtemp(prefix="rizpaq_restore_")
    second = None
    try:
        entries = load_entries(zpaq_bin, dest, password)
        entry = pick_entry(entries, choose)
        if entry is None:
            return True, "нет подходящих файлов для проверки восстановления"

        cmd = extract_cmd(zpaq_bin, dest, entry, folder, password)
        rc, output = run_zpaq(cmd)
        if rc != 0:
            return False, "\n".join([
                "[restore] не удалось извлечь %s" % entry.path,
                str(output or ""),
            ])

        restored = _find_extracted(folder)
        actual = sha256_of(restored) if restored else None
        if not actual:
            return False, "[restore] извлечённый файл не найден: %s" % entry.path

        original = _source_for(entry, sources)
        if original is not None:
            expected = sha256_of(original)
            match = bool(expected) and expected == actual
            how = "сравнение с исходником %s" % original
        else:
            second = tempfile.mkdtemp(prefix="rizpaq_restore2_")
            rc2, out2 = run_zpaq(
                extract_cmd(zpaq_bin, dest, entry, second, password)
            )
            other = _find_extracted(second)
            second_hash = sha256_of(other) if other else None
            match = rc2 == 0 and bool(second_hash) and second_hash == actual
            how = "повторное извлечение (исходника нет на диске)"

        verdict = "OK" if match else "MISMATCH"
        return match, "\n".join([
            "[restore] файл: %s (%s байт, версия %s)" % (
                entry.path, entry.size, entry.version,
            ),
            "[restore] способ сверки: %s" % how,
            "[restore] SHA256: %s" % actual,
            "[restore] вердикт: %s" % verdict,
        ])
    except Exception as exc:
        return False, "[restore] ошибка: %s: %s" % (
            type(exc).__name__, exc
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        if second:
            shutil.rmtree(second, ignore_errors=True)
