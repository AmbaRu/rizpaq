























































from __future__ import annotations

import ctypes
import os
from pathlib import Path

                                                                     
                                                               
 
                                                                       
                                                                              
                                                          
READ_ONLY_SUBCOMMANDS = {"l", "t", "e", "x", "v"}


class EnginePathError(Exception):
    pass







def has_non_latin(text: str) -> bool:
    return any(not ch.isascii() for ch in str(text))


def short_path(long_path: str) -> str:
    pass





    if os.name != "nt":
        return ""
    try:
        buf = ctypes.create_unicode_buffer(4096)
        n = ctypes.windll.kernel32.GetShortPathNameW(
            str(long_path), buf, 4096
        )
        if n == 0:
            return ""
        return buf.value
    except Exception:
        return ""


def is_zpaq_cmd(cmd: list) -> bool:
    pass






    if not cmd:
        return False
    exe = cmd[0]
    if not isinstance(exe, str):
        return False
    return "zpaq" in os.path.basename(exe).lower()


def subcommand_of(cmd: list) -> str:
    pass
    for arg in cmd[1:]:
        if not (isinstance(arg, str) and arg.startswith("-")):
            return arg.lower()
    return ""


def archive_index(cmd: list) -> int:
    pass






    seen_sub = False
    for i in range(1, len(cmd)):
        arg = cmd[i]
        if isinstance(arg, str) and arg.startswith("-"):
            continue
        if not seen_sub:
            seen_sub = True
            continue
        return i
    return -1


                                                                      
                                       
                                                                      
def read_target(path: str) -> tuple:
    pass












    p = str(path)

    if not has_non_latin(p):
        return p, None, []

    short = short_path(p)                            
    if short and not has_non_latin(short):
        return short, None, []                                            

    name = Path(p).name                                          
    folder = str(Path(p).parent)
    if not has_non_latin(name) and folder:
        return name, folder, []                                           

                                                                
    arg, cwd = latin_substitute(p)
    return arg, cwd, [arg]


def latin_substitute(path: str) -> tuple:
    pass









    import shutil
    import tempfile

    src = Path(path)
    try:
        folder = tempfile.mkdtemp(prefix="rizpaq_link_")
    except Exception as exc:
        raise EnginePathError(
            f"не удалось приготовить временную папку для чтения архива: {exc}"
        ) from exc

    ascii_stem = "".join(
        ch for ch in src.stem if ch.isascii() and ch.isalnum()
    ) or "archive"
    tmp = Path(folder) / f"{ascii_stem}.zpaq"

    try:
        os.link(str(src), str(tmp))
        return str(tmp), None
    except Exception:
        pass

    try:
        shutil.copy2(str(src), str(tmp))
    except Exception as exc:
        shutil.rmtree(folder, ignore_errors=True)
        raise EnginePathError(
            f"не удалось прочитать архив с нелатинским именем: движок не "
            f"понимает такой путь, короткие имена на диске отключены, а "
            f"жёсткая ссылка и копия не получились ({exc}). Переименуйте "
            f"файл или перенесите его в папку на диске, где короткие имена "
            f"разрешены: {path}"
        ) from exc

    return str(tmp), None


                                                                      
                                
                                                                      
def create_target(path: str) -> tuple:
    pass








    p = str(path)

    if not has_non_latin(p):
        return p, None, []

    if os.path.isfile(p):
                                                                             
        return read_target(p)

    folder = str(Path(p).parent)
    if folder and has_non_latin(folder):
        return Path(p).name, folder, []                               

    return p, None, []                                                        


def engine_target(path: str) -> tuple:
    pass





    p = str(path)
    if os.path.isfile(p):
        return read_target(p)
    return create_target(p)


def describe(path: str) -> str:
    pass
    try:
        arg, cwd, subs = engine_target(path)
    except EnginePathError as exc:
        return f"НЕДОСТУПЕН: {exc}"
    if cwd:
        return f"имя={arg}, рабочий каталог={cwd}"
    if subs:
        return f"подмена={arg}"
    return f"путь={arg}"


def rewrite_cmd(cmd: list) -> tuple:
    pass










    if not is_zpaq_cmd(cmd):
        return list(cmd), None, []

    idx = archive_index(cmd)
    if idx < 0 or idx >= len(cmd):
        return list(cmd), None, []

    raw = cmd[idx]
    if not isinstance(raw, str) or not has_non_latin(raw):
        return list(cmd), None, []

    sub = subcommand_of(cmd)
    try:
        if os.path.isfile(raw):
            if sub not in READ_ONLY_SUBCOMMANDS:
                                                                    
                                                                      
                short = short_path(raw)
                name = Path(raw).name
                folder = str(Path(raw).parent)
                if short and not has_non_latin(short):
                    return _replaced(cmd, idx, short), None, []
                if not has_non_latin(name) and folder:
                    return _replaced(cmd, idx, name), folder, []
                raise EnginePathError(
                    "движок не умеет работать с архивом, имя которого "
                    f"нелатинское, и пишет в него, а не только читает: {raw}. "
                    "Копию подставить нельзя — добавленное ушло бы в копию, "
                    "а настоящий архив остался бы прежним. Переименуйте "
                    "файл или перенесите его в папку на диске, где короткие "
                    "имена разрешены."
                )
            new_arg, new_cwd, subs = read_target(raw)
        else:
            new_arg, new_cwd, subs = create_target(raw)
    except EnginePathError:
        raise
    except Exception:
                                                                       
        return list(cmd), None, []

    return _replaced(cmd, idx, new_arg), new_cwd, subs


def _replaced(cmd: list, idx: int, value: str) -> list:
    out = list(cmd)
    out[idx] = value
    return out


def drop_substitutes(paths: list) -> None:
    pass










    import shutil

    for p in paths or ():
        try:
            parent = os.path.dirname(str(p))
            if os.path.isfile(str(p)):
                os.unlink(str(p))
                                                                             
            if parent and os.path.isdir(parent) and os.path.basename(
                parent
            ).startswith("rizpaq_link_"):
                shutil.rmtree(parent, ignore_errors=True)
        except Exception:
            pass


                                                                      
                                                            
                                                                      
def needs_staging(dest: str) -> bool:
    pass






    p = str(dest)
    if not has_non_latin(p):
        return False
    folder = str(Path(p).parent)
    return bool(folder) and has_non_latin(folder)


def make_staging(dest: str) -> str:
    pass











    import tempfile

    stem = Path(str(dest)).stem
    ascii_stem = "".join(ch for ch in stem if ch.isascii() and ch.isalnum())
    ascii_stem = ascii_stem or "file"

    base = None
    try:
        base = Path(tempfile.gettempdir())
    except Exception:
        base = None

    if base is not None and not has_non_latin(str(base)):
        try:
            base.mkdir(parents=True, exist_ok=True)
            fd, path = tempfile.mkstemp(
                prefix=f"{ascii_stem}_", suffix=".tmp", dir=str(base)
            )
            os.close(fd)
                                                               
             
                                                                       
                                                                      
                                
                                                                      
                                                      
                                                                            
                                                 
             
                                                                         
                                                            
            try:
                os.unlink(path)
            except Exception:
                pass
            return path
        except Exception:
            pass

    raise EnginePathError(
        f"не удалось приготовить временный файл в латинской папке для "
        f"извлечения в {dest}: системная временная папка непригодна, а "
        f"движок не умеет писать файл через нелатинскую папку. "
        f"Распакуйте в папку с латинским именем."
    )


def move_to_dest(staged: str, dest: str) -> tuple:
    pass















    import shutil

    staged = str(staged)
    dest = str(dest)

    if not os.path.isfile(staged):
        return False, f"черновик не найден: {staged}"

    if os.path.exists(dest):
        return False, (
            f"файл уже существует и не перезаписан: {dest}. "
            f"Извлечённое оставлено здесь: {staged}"
        )

    try:
        os.replace(staged, dest)                                     
        return True, ""
    except OSError:
        pass                                                      

    try:
        size_staged = os.path.getsize(staged)
        shutil.copy2(staged, dest)
        size_dest = os.path.getsize(dest)
    except Exception as exc:
        return False, (
            f"не удалось перенести извлечённый файл на место: {exc}. "
            f"Он оставлен здесь: {staged}"
        )

    if size_dest != size_staged:
        return False, (
            f"размер перенесённого файла не совпал "
            f"({size_dest} вместо {size_staged}) — возможно, копирование "
            f"прошло не полностью. Оригинал оставлен здесь: {staged}. "
            f"Проверьте вручную: {dest}"
        )

    try:
        os.unlink(staged)
    except Exception:
        pass
    return True, ""

def discard_staging_if_empty(path: str) -> bool:
    pass










    import shutil

    p = str(path or "")
    if not p:
        return False
    try:
        if os.path.isdir(p):
            if not os.listdir(p):
                os.rmdir(p)
                return True
            return False
        if os.path.isfile(p) and os.path.getsize(p) == 0:
            os.unlink(p)
            return True
    except Exception:
        pass
    return False
