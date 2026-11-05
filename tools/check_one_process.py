from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"


CRASH_CODES = {
    -1073741819: "0xC0000005 ACCESS_VIOLATION",
    -1073741825: "0xC000001D ILLEGAL_INSTRUCTION",
    -1073740791: "0xC0000409 STACK_BUFFER_OVERRUN / fail-fast",
    -1073741824: "0xC0000000 STATUS_UNKNOWN",
    -1073741822: "0xC0000002 STATUS_NOT_IMPLEMENTED",
}


def signed(rc: int) -> int:
    if rc is None:
        return 0
    if 0 < rc > 0x7FFFFFFF:
        return rc - 0x100000000
    return rc


def test_files(filters):
    names = sorted(p.stem for p in TESTS.glob("test_*.py"))
    if not filters:
        return names
    picked = [n for n in names
              if any(f in n.replace("test_", "") for f in filters)]
    return picked


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("filters", nargs="*",
                    help="подстроки имён файлов (без test_ и .py)")
    ap.add_argument("--list", action="store_true",
                    help="только показать, что будет прогоняться")
    ap.add_argument("--timeout", type=int, default=300,
                    help="предел ожидания, секунд (по умолчанию 300)")
    args = ap.parse_args()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    names = test_files(args.filters)
    if args.list or not names:
        print("файлов к прогону: %d" % len(names))
        for n in names:
            print("  " + n)
        return 0

    mods = ["tests." + n for n in names]
    print("Прогон %d файлов в ОДНОМ процессе..." % len(mods))
    try:
        p = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-m", "unittest"] + mods,
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, timeout=args.timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        rc = p.returncode
        out = p.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        print("ПРОВАЛ: процесс не завершился за %d с" % args.timeout)
        print("Это тоже поломка: тесты зависли намертво.")
        return 1


    tail = out.rstrip().split("\n")[-25:]
    for ln in tail:
        print("   ", ln[:160])

    rc = signed(rc)
    if rc == 0:
        print("\nПРОШЁЛ: все %d файлов в одном процессе." % len(mods))
        return 0

    if rc in CRASH_CODES:
        print("\nПРОВАЛ: процесс убит — %s" % CRASH_CODES[rc])
        print("Это не ошибка теста, а поломка Qt-состояния между файлами.")
        print("Место падения — в выводе выше (faulthandler).")
        return 1

    if rc < 0:
        print("\nПРОВАЛ: процесс убит сигналом %d (%s)"
              % (rc, CRASH_CODES.get(rc, "неизвестный сигнал")))
        return 1

    print("\nПРОВАЛ: код возврата %d — в тестах есть обычные падения." % rc)
    return 1


if __name__ == "__main__":
    sys.exit(main())
