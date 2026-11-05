#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PYTHON = sys.executable


PER_FILE_TIMEOUT = 600


def _iter_test_files(filter_substr: str | None):

    files = sorted(HERE.glob("test_*.py"))
    if filter_substr:
        needle = filter_substr.lower()
        files = [f for f in files if needle in f.stem.lower()]
    return files


def _dotted_name(path: Path) -> str:
    return f"tests.{path.stem}"


def _run_one(path: Path) -> tuple:
    env = dict(os.environ)


    env.setdefault("QT_QPA_PLATFORM", "offscreen")


    env.setdefault("PYTHONIOENCODING", "utf-8")

    cmd = [PYTHON, "-m", "unittest", _dotted_name(path), "-v"]
    t0 = time.monotonic()
    try:
        r = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PER_FILE_TIMEOUT,
        )
        return (
            r.returncode == 0,
            time.monotonic() - t0,
            (r.stdout or "") + (r.stderr or ""),
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"") + (exc.stderr or b"")
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return False, time.monotonic() - t0, out + (
            f"\n!! TIMEOUT ({PER_FILE_TIMEOUT}s)"
        )
    except Exception as exc:
        return False, time.monotonic() - t0, f"!! не удалось запустить: {exc}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Прогон всех тестов Rizpaq одной командой.",
    )
    parser.add_argument(
        "filter", nargs="?", default=None,
        help="подстрока имени файла (без test_ и .py)",
    )
    parser.add_argument(
        "--stop", action="store_true",
        help="остановиться на первом упавшем файле",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="не печатать вывод упавших тестов (только имена файлов)",
    )
    args = parser.parse_args(argv)

    files = _iter_test_files(args.filter)
    if not files:
        print("Не найдено ни одного файла тестов.")
        return 1

    print(f"Прогон {len(files)} файлов тестов.")
    print()

    results = []
    failed_outputs = []
    total_start = time.monotonic()

    for i, path in enumerate(files, 1):
        name = path.stem
        ok, dt, output = _run_one(path)
        results.append((name, ok, dt))
        mark = "OK  " if ok else "FAIL"
        print(f"  [{i:2d}/{len(files)}] {mark} {name:<40} {dt:6.2f}s")

        if not ok and not args.quiet:
            failed_outputs.append((name, output))

        if not ok and args.stop:
            print()
            print(f"Останавливаюсь на {name} (--stop).")
            break

    total_dt = time.monotonic() - total_start
    failed = [r for r in results if not r[1]]

    for name, output in failed_outputs:
        print()
        print("=" * 72)
        print(f"  ВЫВОД УПАВШЕГО ФАЙЛА: {name}")
        print("=" * 72)
        print(output)

    print()
    print("=" * 72)
    if failed:
        print(
            f"ИТОГ: упало {len(failed)} из {len(results)} файлов "
            f"за {total_dt:.1f}s."
        )
        for name, _ok, _dt in failed:
            print(f"  FAIL {name}")
        return 1

    print(f"ИТОГ: все {len(results)} файлов прошли за {total_dt:.1f}s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
