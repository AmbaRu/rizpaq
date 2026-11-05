#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _pause_if_console() -> None:
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            input("\nНажми Enter для выхода...")
    except Exception:
        pass


def main() -> int:
    args = sys.argv[1:]


    if "--status" in args:
        from core.file_association import diagnose

        diagnose()
        _pause_if_console()
        return 0

    uninstall = "--uninstall" in args

    try:
        from core.file_association import diagnose, register, unregister

        if uninstall:
            unregister()
            print("Ассоциация .zpaq и .rzt удалена из HKCU.")
        else:
            register()
            print("Ассоциация .zpaq и .rzt установлена в HKCU.")
        print()
        diagnose()
    except Exception as exc:
        import traceback

        print(f"ОШИБКА: {exc}")
        traceback.print_exc()
        _pause_if_console()
        return 1

    _pause_if_console()
    return 0


if __name__ == "__main__":
    sys.exit(main())
