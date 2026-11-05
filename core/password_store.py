from __future__ import annotations

import base64
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple


CORRUPT_SUFFIX = ".corrupt"


TMP_PREFIX = ".rizpaq_pw_"
TMP_SUFFIX = ".tmp"


STORE_NAME = "archive_passwords.json"


_LEGACY_DIR_NAME = ".rizpaq"


def _store_dir() -> Path:
    from core.config import default_path

    return default_path().parent


def _store_path() -> Path:
    return _store_dir() / STORE_NAME


def _legacy_store_path() -> Path:
    return Path.home() / _LEGACY_DIR_NAME / STORE_NAME


def _migrate_legacy_store(target: Path) -> Optional[str]:
    try:
        if target.exists():
            return None
        legacy = _legacy_store_path()
        if not legacy.is_file():
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(legacy), str(target))


        return (
            f"перенесено: {legacy} -> {target}. "
            f"Старый файл оставлен на месте, его можно удалить вручную."
        )
    except Exception as exc:
        return (
            f"не удалось перенести хранилище паролей из "
            f"{_legacy_store_path()} в {target}: {type(exc).__name__}: {exc}"
        )


def _norm_key(archive_path: str) -> str:

    try:
        return os.path.normcase(os.path.abspath(str(archive_path)))
    except Exception:
        return str(archive_path)


def _report(message: str) -> None:
    try:
        from core.config import write_error_log

        write_error_log(message, name="password_store.log")
    except Exception:


        pass


def _load() -> Tuple[dict, str]:
    try:
        path = _store_path()
    except Exception as exc:
        return {}, f"не удалось определить путь хранилища: {exc}"


    migration_note = _migrate_legacy_store(path)
    if migration_note:
        if migration_note.startswith("перенесено"):

            _report(migration_note)
        else:


            return {}, migration_note

    if not path.exists():
        return {}, ""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, f"файл паролей не читается: {path} ({exc})"

    if not text.strip():
        return {}, ""

    try:
        data = json.loads(text)
    except ValueError as exc:
        return {}, (
            f"файл паролей повреждён и не будет прочитан: {path} ({exc}). "
            f"При следующем сохранении он будет отодвинут в "
            f"{path.name}{CORRUPT_SUFFIX}."
        )

    if not isinstance(data, dict):
        return {}, (
            f"файл паролей имеет неожиданный вид и не будет прочитан: "
            f"{path}. При следующем сохранении он будет отодвинут в "
            f"{path.name}{CORRUPT_SUFFIX}."
        )

    return data, ""


def _quarantine(path: Path) -> None:
    try:
        os.replace(str(path), str(path) + CORRUPT_SUFFIX)
    except OSError:


        try:
            shutil.copy2(str(path), str(path) + CORRUPT_SUFFIX)
        except Exception:
            pass
        _report(
            "не удалось отодвинуть испорченный файл паролей; "
            f"предыдущее содержимое сохранено в {path}{CORRUPT_SUFFIX} "
            "только если копирование прошло успешно"
        )


def _atomic_write(path: Path, data: dict) -> Optional[str]:
    tmp_name = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=TMP_PREFIX, suffix=TMP_SUFFIX, dir=str(path.parent)
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()


            try:
                os.fsync(fh.fileno())
            except OSError:


                pass
        os.replace(tmp_name, str(path))
        tmp_name = None
        return None
    except Exception as exc:
        return f"не удалось сохранить пароль в {path}: {type(exc).__name__}: {exc}"
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def get_password(archive_path: str):

    data, problem = _load()

    if problem:


        _report(problem)
        return None

    encoded = data.get(_norm_key(archive_path))
    if not encoded:
        return None

    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception as exc:
        _report(
            f"запись пароля для {_norm_key(archive_path)} не расшифровывается: "
            f"{type(exc).__name__}: {exc}"
        )
        return None


def set_password(archive_path: str, password) -> None:

    try:
        path = _store_path()
    except Exception as exc:
        _report(f"не удалось определить путь хранилища: {exc}")
        return

    data, problem = _load()

    if problem:


        _report(problem)
        if path.exists():
            _quarantine(path)
        data = {}

    key = _norm_key(archive_path)

    if password:
        data[key] = base64.b64encode(
            str(password).encode("utf-8")
        ).decode("ascii")
    else:
        data.pop(key, None)

    error = _atomic_write(path, data)
    if error:
        _report(error)
