







































































































from __future__ import annotations

import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from core.models import ArchiveEntry

                                                               
                                                 
INDEX_FILENAME = "archive_index.sqlite"

                                                                
                                                                     
                                                                      
                                                                         
           
 
                                                      
                                                                      
                           
SCHEMA_VERSION = 2

                       
 
                                                           
                                                                    
                                                               
                                                                    
                                                              
                           
                                                                     
                                                               
_WAL = "WAL"
_SYNCHRONOUS = "NORMAL"
_BUSY_TIMEOUT_MS = 3000

                                                            
 
                                                                
                                                                  
                                              
_conn: Optional[sqlite3.Connection] = None
_lock = threading.RLock()

                                                                      
                                                                   
_override_path: Optional[Path] = None

                                                
_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS archives (
        path           TEXT PRIMARY KEY,
        mtime_ns       INTEGER NOT NULL,
        size           INTEGER NOT NULL,
        entries_count  INTEGER NOT NULL DEFAULT 0,
        updated_at     INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entries (
        archive_path   TEXT NOT NULL,
        path_inside    TEXT NOT NULL,
        name           TEXT NOT NULL,
        size           INTEGER NOT NULL,
        date           TEXT NOT NULL,
        version        INTEGER,
        flag           TEXT NOT NULL,
        is_dir         INTEGER NOT NULL,
        attr           TEXT NOT NULL DEFAULT '',
        ratio          TEXT NOT NULL DEFAULT '',
        position       INTEGER NOT NULL,
        PRIMARY KEY (archive_path, position)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_entries_archive ON entries(archive_path)",
                                                                          
                                                                         
                                                                         
                                                                          
                                                                  
    """
    CREATE TABLE IF NOT EXISTS catalog (
        path           TEXT PRIMARY KEY,
        size           INTEGER NOT NULL DEFAULT 0,
        mtime_ns       INTEGER NOT NULL DEFAULT 0,
        discovered_at  INTEGER NOT NULL DEFAULT 0,
        missing        INTEGER NOT NULL DEFAULT 0
    )
    """,
)

                                                         
                                                                       
                        
_DROP_STATEMENTS = (
    "DROP INDEX IF EXISTS idx_entries_archive",
    "DROP TABLE IF EXISTS entries",
    "DROP TABLE IF EXISTS archives",
)


                                                                             
                       
                                                                             

def index_path() -> Path:
    pass






    if _override_path is not None:
        return _override_path

    from core.config import default_path

    return default_path().parent / INDEX_FILENAME


def _set_index_path_for_tests(path: Optional[Path]) -> None:
    pass









    global _override_path
    with _lock:
        _close_locked()
        _override_path = Path(path) if path else None


                                                                             
                              
                                                                             

def _read_user_version(conn: sqlite3.Connection) -> int:
    pass
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
        if row is None:
            return 0
        return int(row[0])
    except Exception:
        return 0


def _write_user_version(conn: sqlite3.Connection, version: int) -> None:
    pass
    try:
        conn.execute(f"PRAGMA user_version = {int(version)}")
    except Exception:
        pass


def _migrate_if_needed(conn: sqlite3.Connection) -> None:
    pass















    current = _read_user_version(conn)
    if current >= SCHEMA_VERSION:
        return

    for statement in _DROP_STATEMENTS:
        try:
            conn.execute(statement)
        except Exception:
            pass

    for statement in _SCHEMA_STATEMENTS:
        conn.execute(statement)

    _write_user_version(conn, SCHEMA_VERSION)


def _open_locked() -> sqlite3.Connection:
    pass






    global _conn

    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
                                                           
    conn.execute(f"PRAGMA journal_mode={_WAL}")
    conn.execute(f"PRAGMA synchronous={_SYNCHRONOUS}")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")

    _migrate_if_needed(conn)
    conn.commit()

    _conn = conn
    return conn


def _get_connection() -> sqlite3.Connection:
    pass






    with _lock:
        if _conn is not None:
            return _conn
        return _open_locked()


def _close_locked() -> None:
    pass
    global _conn
    if _conn is None:
        return
    try:
        _conn.close()
    except Exception:
        pass
    _conn = None


def close() -> None:
    pass






    with _lock:
        _close_locked()


                                                                             
                
                                                                             

def _is_supported(path: str) -> bool:
    pass






    if not path:
        return False
    if "?" in str(path):
        return False
    return True


def is_fresh(path: str, mtime_ns: int, size: int) -> bool:
    pass







    if not _is_supported(path):
        return False

    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return False

        try:
            row = conn.execute(
                "SELECT mtime_ns, size FROM archives WHERE path = ?",
                (str(path),),
            ).fetchone()
        except Exception:
            return False

    if row is None:
        return False
    return int(row[0]) == int(mtime_ns) and int(row[1]) == int(size)


def list_archives() -> list:
    pass














    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return []

        try:
            rows = conn.execute(
                "SELECT path, mtime_ns, size, entries_count, updated_at "
                "FROM archives ORDER BY path",
            ).fetchall()
        except Exception:
            return []

    out: list = []
    for row in rows:
        path = str(row[0])
        if not _is_supported(path):
                                                                      
                                                                       
                                   
            continue
        out.append({
            "path": path,
            "mtime_ns": int(row[1]),
            "size": int(row[2]),
            "entries_count": int(row[3] or 0),
            "updated_at": int(row[4] or 0),
        })
    return out


def load_entries(path: str) -> Optional[list]:
    pass















    if not _is_supported(path):
        return None

    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return None

        p = str(path)
        try:
            head = conn.execute(
                "SELECT 1 FROM archives WHERE path = ?",
                (p,),
            ).fetchone()
            if head is None:
                                                                      
                                    
                return None

            rows = conn.execute(
                "SELECT path_inside, size, date, version, flag, is_dir, "
                "       attr, ratio "
                "FROM entries WHERE archive_path = ? "
                "ORDER BY position",
                (p,),
            ).fetchall()
        except Exception:
            return None

    out: list = []
    for row in rows:
        path_inside, size, date, version, flag, is_dir, attr, ratio = row
        out.append(
            ArchiveEntry(
                path=str(path_inside),
                size=int(size),
                datetime=str(date),
                version=int(version) if version is not None else None,
                flag=str(flag),
                is_dir=bool(is_dir),
                attr=str(attr or ""),
                ratio=str(ratio or ""),
            )
        )
    return out


def store_entries(
    path: str,
    mtime_ns: int,
    size: int,
    entries: list,
) -> None:
    pass





















    if not _is_supported(path):
        return

    p = str(path)
    now = int(time.time())

    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute("DELETE FROM entries WHERE archive_path = ?", (p,))
                if entries:
                    rows = [
                        (
                            p,
                            str(e.path),
                            str(e.name or ""),
                            int(e.size or 0),
                            str(e.datetime or ""),
                            int(e.version) if e.version is not None else None,
                            str(e.flag or ""),
                            1 if e.is_dir else 0,
                            str(e.attr or ""),
                            str(e.ratio or ""),
                            i,
                        )
                        for i, e in enumerate(entries)
                    ]
                    conn.executemany(
                        "INSERT INTO entries "
                        "(archive_path, path_inside, name, size, date, version, "
                        " flag, is_dir, attr, ratio, position) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        rows,
                    )
                conn.execute(
                    "INSERT OR REPLACE INTO archives "
                    "(path, mtime_ns, size, entries_count, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (p, int(mtime_ns), int(size), len(entries), now),
                )
        except Exception:
                                                                    
            pass


                                                                             
                          
                                                                             
 
                                                                  
                                                                       
                                                                        
                                                                    
                                                                  
                                                                  
                                                   
 
                                                               
                                                                   
                                                                      
                                              

def _norm(path: str) -> str:
    pass
    try:
        return os.path.normcase(os.path.normpath(str(path)))
    except Exception:
        return str(path)


def _under_root(path: str, root: str) -> bool:
    pass
    p = _norm(path)
    r = _norm(root)
    if not r:
        return False
    if p == r:
        return True
    if not r.endswith(os.sep):
        r += os.sep
    return p.startswith(r)


def catalog_upsert(path: str, size: int, mtime_ns: int) -> None:
    pass





    if not path:
        return

    p = str(path)
    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO catalog "
                    "(path, size, mtime_ns, discovered_at, missing) "
                    "VALUES (?, ?, ?, ?, 0)",
                    (p, int(size or 0), int(mtime_ns or 0), int(time.time())),
                )
        except Exception:
            pass


def catalog_list() -> list:
    pass










    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return []

        try:
            rows = conn.execute(
                "SELECT c.path, c.size, c.mtime_ns, c.discovered_at, "
                "       c.missing, "
                "       CASE WHEN a.path IS NOT NULL "
                "                 AND a.mtime_ns = c.mtime_ns "
                "                 AND a.size = c.size "
                "            THEN 1 ELSE 0 END, "
                "       COALESCE(a.entries_count, 0) "
                "FROM catalog c "
                "LEFT JOIN archives a ON a.path = c.path "
                "ORDER BY c.path",
            ).fetchall()
        except Exception:
            return []

    out: list = []
    for row in rows:
        out.append({
            "path": str(row[0]),
            "size": int(row[1] or 0),
            "mtime_ns": int(row[2] or 0),
            "discovered_at": int(row[3] or 0),
            "missing": bool(row[4]),
            "indexed": bool(row[5]),
            "entries_count": int(row[6] or 0),
        })
    return out


def catalog_mark_scanned(roots, found) -> int:
    pass








    roots = [str(r) for r in (roots or []) if str(r or "").strip()]
    if not roots:
        return 0

    found_norm = {_norm(p) for p in (found or []) if p}
    now_missing = 0

    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return 0

        try:
            rows = conn.execute("SELECT path FROM catalog").fetchall()
        except Exception:
            return 0

        try:
            with conn:
                for (path,) in rows:
                    if not any(_under_root(path, r) for r in roots):
                        continue
                    if _norm(path) in found_norm:
                        continue
                    cur = conn.execute(
                        "UPDATE catalog SET missing = 1 "
                        "WHERE path = ? AND missing = 0",
                        (path,),
                    )
                    now_missing += cur.rowcount or 0
        except Exception:
            pass

    return now_missing


def catalog_forget(path: str) -> None:
    pass






    if not path:
        return

    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute("DELETE FROM catalog WHERE path = ?", (str(path),))
        except Exception:
            pass


def catalog_forget_all() -> None:
    pass
    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute("DELETE FROM catalog")
        except Exception:
            pass


def forget(path: str) -> None:
    pass








    if not path:
        return

    p = str(path)
    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute("DELETE FROM entries WHERE archive_path = ?", (p,))
                conn.execute("DELETE FROM archives WHERE path = ?", (p,))
        except Exception:
            pass


def forget_all() -> None:
    pass







    with _lock:
        try:
            conn = _get_connection()
        except Exception:
            return

        try:
            with conn:
                conn.execute("DELETE FROM entries")
                conn.execute("DELETE FROM archives")
        except Exception:
            pass
