#!/usr/bin/env python3






























from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _fmt_ts(ns: int) -> str:
    pass
    try:
        return datetime.fromtimestamp(ns / 1_000_000_000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return f"(не дата: {ns})"


def _print_header() -> Path:
    pass
    from core import archive_index

    path = archive_index.index_path()
    print("=== Диагностика индекса метаданных Rizpaq ===")
    print()
    print(f"Путь к индексу: {path}")

    exists = path.is_file()
    print(f"Файл существует: {exists}")

    if exists:
        try:
            st = path.stat()
            print(f"Размер:          {st.st_size} байт")
            print(f"Изменён:         {_fmt_ts(st.st_mtime_ns)}")
        except OSError as exc:
            print(f"Не удалось прочитать размер: {exc}")

                   
    for suffix in ("-wal", "-shm"):
        p = Path(str(path) + suffix)
        if p.is_file():
            try:
                print(f"{suffix}: {p.stat().st_size} байт")
            except OSError:
                pass

    print()
    return path


def _print_archives(path: Path) -> None:
    pass
    if not path.is_file():
        print("(таблица archives не показана: файла индекса нет)")
        return

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
    except Exception as exc:
        print(f"Не удалось открыть индекс: {exc}")
        return

    try:
        try:
            rows = conn.execute(
                "SELECT path, mtime_ns, size, entries_count, updated_at "
                "FROM archives ORDER BY path"
            ).fetchall()
        except sqlite3.OperationalError as exc:
            print(f"Таблица archives не читается: {exc}")
            return

        print(f"Записей в таблице archives: {len(rows)}")
        print()
        for row in rows:
            print(f"  {row['path']}")
            print(f"    mtime_ns     = {row['mtime_ns']} "
                  f"({_fmt_ts(row['mtime_ns'])})")
            print(f"    size         = {row['size']} байт")
            print(f"    entries_count= {row['entries_count']}")
            print(f"    updated_at   = {row['updated_at']}")
    finally:
        conn.close()


def _check_one(path_str: str, show_entries: bool) -> None:
    pass
    from core import archive_index

    print("=== Проверка конкретного архива ===")
    print(f"Аргумент: {path_str}")
    print()

    p = Path(path_str)
    if not p.is_file():
        print("  Файл на диске: НЕ существует")
        print("  Вывод: индекс для несуществующего файла не имеет смысла.")
        return

    st = p.stat()
    mtime_ns = st.st_mtime_ns
    size = st.st_size

    print(f"  Файл на диске: существует")
    print(f"    mtime_ns = {mtime_ns} ({_fmt_ts(mtime_ns)})")
    print(f"    size     = {size} байт")
    print()

    try:
        fresh = archive_index.is_fresh(str(p), mtime_ns, size)
    except Exception as exc:
        print(f"  is_fresh упал с ошибкой: {exc}")
        return

    print(f"  is_fresh: {fresh}")

    try:
        entries = archive_index.load_entries(str(p))
    except Exception as exc:
        print(f"  load_entries упал с ошибкой: {exc}")
        return

    if entries is None:
        print("  load_entries: None (в индексе этого архива нет)")
    else:
        print(f"  load_entries: {len(entries)} записей")
        if entries and not show_entries:
            print(f"    первая: {entries[0].path}")
            print(f"    последняя: {entries[-1].path}")

    if show_entries and entries:
        print()
        print("  Первые 10 записей:")
        for i, e in enumerate(entries[:10]):
            print(f"    [{i}] {e.path}  size={e.size}  "
                  f"version={e.version}  is_dir={e.is_dir}")


def main() -> int:
    path = _print_header()
    _print_archives(path)

                                                                    
    args = sys.argv[1:]
    show_entries = "--entries" in args
    paths = [a for a in args if a != "--entries"]

    if paths:
        print()
        _check_one(paths[0], show_entries)

    return 0


if __name__ == "__main__":
    sys.exit(main())
