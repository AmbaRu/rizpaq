
from __future__ import annotations

import os
import re
import shutil
import string
import tempfile
from pathlib import Path


                                                                         
                                                                      
                                                                       
                                        
                         
                                          
                         
                                                                         
 
                                                                     
                                                                    
                                                               
MULTIPART_RE = re.compile(r"(?<=_)\d{4}\.zpaq$", re.IGNORECASE)


def multipart_pattern(path) -> str:
    pass



    if not path:
        return str(path) if path is not None else path
    p = str(path)
    if MULTIPART_RE.search(p):
        return MULTIPART_RE.sub("????.zpaq", p)
    return p


_BACKSLASH = chr(92)

_INVALID_FILENAME_CHARS = set('<>:"/' + _BACKSLASH + '|?*')

_RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def sanitize_filename(name: str) -> str:
    pass










    if not name:
        return "extracted"

    name = str(name).strip().rstrip("/" + _BACKSLASH)

    if len(name) == 2 and name[1] == ":" and name[0].isalpha():
        return name[0].upper()

    cleaned = []
    for ch in name:
        if ch in _INVALID_FILENAME_CHARS or ord(ch) < 32:
            cleaned.append("_")
        else:
            cleaned.append(ch)
    name = "".join(cleaned)

    name = name.rstrip(". ")
    if not name:
        return "extracted"

    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = "_" + name

    return name


def is_top_level_drive(path: str) -> bool:
    pass
    p = str(path or "").strip().rstrip("/" + _BACKSLASH)
    return len(p) == 2 and p[1] == ":" and p[0].isalpha()


def windows_drives() -> list:
    pass
    out = []

    for letter in string.ascii_uppercase:
        root = letter + ":" + _BACKSLASH
        if os.path.exists(root):
            out.append(root)

    return out


def same_name(a: str, b: str) -> bool:
    pass
    return os.path.normcase(a) == os.path.normcase(b)


def is_root(path) -> bool:
    pass
    try:
        p = Path(path)
        return p.parent == p
    except Exception:
        return True


def is_inside(child, ancestor) -> bool:
    pass









    try:
        c = os.path.normcase(os.path.abspath(str(child)))
        a = os.path.normcase(os.path.abspath(str(ancestor)))
    except Exception:
        return False

    return c.startswith(a.rstrip("/" + _BACKSLASH) + os.sep)


def nearest_existing(path):
    pass
    p = Path(path)

    while not p.exists():
        if p.parent == p:
            return None
        p = p.parent

    return p


def is_temp_path(path) -> bool:
    pass
    try:
        t = os.path.normcase(os.path.abspath(tempfile.gettempdir()))
        p = os.path.normcase(os.path.abspath(str(path)))
        return p == t or p.startswith(t + os.sep)
    except Exception:
        return False


def valid_filename(name: str) -> bool:
    pass
    name = (name or "").strip()

    if not name or name in (".", ".."):
        return False

    if any(ch in _INVALID_FILENAME_CHARS for ch in name):
        return False

                                                                       
                                                              
                                                                         
                                    
    if any(ord(ch) < 32 for ch in name):
        return False

                                                                           
    if name.rstrip(". ") != name:
        return False

    if name.split(".")[0].upper() in _RESERVED_NAMES:
        return False

    return True


def retarget_path(p, old, new):
    pass




    try:
        pa = os.path.abspath(str(p))
        oa = os.path.abspath(str(old))
    except Exception:
        return None

    if same_name(pa, oa):
        return str(new)

    if is_inside(pa, old):
                                                                     
                                                                      
                                                                 
                                                                        
                                                                     
                                                              
                                                                   
                                           
        try:
            rel = os.path.relpath(pa, oa)
        except ValueError:
                                                                        
                                             
            return None
        return os.path.normpath(os.path.join(str(new), rel))

    return None


def directory_not_empty(path: Path) -> bool:
    try:
        return any(path.iterdir())
    except Exception:
        return False


                                                                            
                                                             
 
                                           
            
            
            
 
                                                                    
            
 
                                                                        
                                                                 
                                                                            


def _split_inner_parts(inner) -> list:
    pass
    s = str(inner or "").replace(_BACKSLASH, "/").strip().strip("/")
    if not s:
        return []

    parts = []
    for p in s.split("/"):
        if not p or p == ".":
            continue
        parts.append(p)

    return parts


def _sanitize_fs_part(part: str) -> str:
    pass



    out_chars = []

    for ch in str(part):
        if ch in _INVALID_FILENAME_CHARS or ord(ch) < 32:
            out_chars.append("_")
        else:
            out_chars.append(ch)

    out = "".join(out_chars).rstrip(". ")
    return out or "_"


def _inner_variant_part_lists(parts: list) -> list:
    pass










    if not parts:
        return []

    raw_variants = []

    def add(variant):
        cleaned = [str(x) for x in variant if str(x)]
        if cleaned:
            raw_variants.append(cleaned)

               
    add(parts)

                                              
    add([_sanitize_fs_part(p) for p in parts])

                       
    if any(":" in p for p in parts):
        add([p.replace(":", "_") for p in parts])
        add([p.replace(":", "") for p in parts])

                                           
    first = parts[0]
    if len(first) == 2 and first[1] == ":" and first[0].isalpha():
        letter = first[0]

        for v in (
            f"{letter}_",
            f"{letter.upper()}_",
            f"{letter.lower()}_",
            letter,
            letter.upper(),
            letter.lower(),
        ):
            add([v] + parts[1:])

    seen = set()
    out = []

    for variant in raw_variants:
        t = tuple(variant)
        if t not in seen:
            seen.add(t)
            out.append(list(t))

    return out


def find_extracted_path(root, inner, want_dir=None):
    pass








    root = Path(root)
    if not root.is_dir():
        return None

    parts = _split_inner_parts(inner)
    if not parts:
        return root

    variants = _inner_variant_part_lists(parts)
    if not variants:
        return None

                                  
    for variant in variants:
        try:
            p = root.joinpath(*variant)
            if p.exists() and (want_dir is None or p.is_dir() == want_dir):
                return p
        except Exception:
            continue

                                                                     
    targets = [[x.casefold() for x in v] for v in variants]
    targets.sort(key=len, reverse=True)

            
    if want_dir is not False:
        for dirpath, _dirnames, _filenames in os.walk(root):
            try:
                rel = Path(dirpath).relative_to(root).parts
            except Exception:
                continue

            if not rel:
                continue

            low = [x.casefold() for x in rel]

            for target in targets:
                n = len(target)
                if len(low) >= n and low[-n:] == target:
                    return Path(dirpath)

            
    if want_dir is not True:
        for dirpath, _dirnames, filenames in os.walk(root):
            try:
                rel_dir = Path(dirpath).relative_to(root).parts
            except Exception:
                continue

            for name in filenames:
                low = [x.casefold() for x in rel_dir] + [name.casefold()]

                for target in targets:
                    n = len(target)
                    if len(low) >= n and low[-n:] == target:
                        return Path(dirpath) / name

    return None


def find_extracted_dir(root, inner):
    pass
    return find_extracted_path(root, inner, want_dir=True)


def find_extracted_file(root, inner):
    pass
    return find_extracted_path(root, inner, want_dir=False)


def merge_tree(src, dest):
    pass





    src = Path(src)
    dest = Path(dest)

    if not src.exists():
        raise FileNotFoundError(str(src))

    if dest.exists() and dest.is_file():
        raise NotADirectoryError(str(dest))

    dest.parent.mkdir(parents=True, exist_ok=True)

                                                    
    if not dest.exists():
        try:
            os.replace(src, dest)
            return
        except OSError:
            pass

                                                 
    elif dest.is_dir() and not directory_not_empty(dest):
        try:
            dest.rmdir()
            os.replace(src, dest)
            return
        except OSError:
            pass

                            
    shutil.copytree(src, dest, dirs_exist_ok=True)
    shutil.rmtree(src, ignore_errors=True)
