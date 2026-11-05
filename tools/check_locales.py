#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOCALES = ROOT / "locales"

PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")
LITERAL_RE = re.compile(r"\btr\(\s*[\"']([^\"']+)[\"']")
SKIP_DIRS = {"__pycache__", "build", "dist", "locales", "tools", "tests"}


DYNAMIC_KEYS = {
    f"diff.status.{s}" for s in ("added", "removed", "changed", "unchanged")
} | {


    "create.level_method",
    "skin.soft_azure",
    "skin.white_air",
} | {


    "profile.archive",
    "profile.backup",
} | {


    "profile_chooser.archive_desc",
    "profile_chooser.backup_desc",
} | {


    "scheduler.sync_add_group",
    "scheduler.sync_disable_group",
    "scheduler.sync_remove_group",
} | {


    "par2.verify_stale",
} | {


    f"backup.reason.{r}" for r in (
        "par2_missing", "par2_broken", "par2_damaged",
        "par2_unrepairable", "par2_failed",
    )
} | {
    f"backup.reason_full.{r}" for r in (
        "par2_missing", "par2_broken", "par2_damaged",
        "par2_unrepairable", "par2_failed",
    )
}


LEGACY_KEYS = {


    "backup.status.read_error",


    "menu.settings.tasks_dir.tip",


    "scheduler.save_task_title",
    "scheduler.saved_without_schedule",

    "task.load_error",
    "task.saved_ok",


    "context.add_job",
}


KEY_TABLES = (
    ROOT / "ui" / "test_modes.py",
)


def _keys_from_tables() -> set:
    import ast

    out = set()
    for path in KEY_TABLES:
        if not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            names = {
                t.id for t in node.targets if isinstance(t, ast.Name)
            }
            if not (names & KEY_TABLE_NAMES):
                continue
            for sub in ast.walk(node.value):
                if not isinstance(sub, ast.Constant):
                    continue
                value = sub.value


                if isinstance(value, str) and "." in value:
                    out.add(value)
    return out


KEY_TABLE_NAMES = {"TEST_MODES_UI"}


def _keys_from_tr_calls(text: str) -> set:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name != "tr":
            continue
        for arg in node.args:
            found |= _strings_in(arg)
    return found


def _strings_in(node) -> set:
    if isinstance(node, ast.JoinedStr):
        return set()
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, str) else set()
    out = set()
    for child in ast.iter_child_nodes(node):
        out |= _strings_in(child)
    return out


def used_keys() -> set:

    used = set(DYNAMIC_KEYS) | set(LEGACY_KEYS)
    used |= _keys_from_tables()
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        used |= set(LITERAL_RE.findall(text))
        used |= _keys_from_tr_calls(text)


    used = {
        k for k in used
        if k and k.strip() and k != "..." and " " not in k
    }
    return used


def placeholders(text: str) -> set:
    return set(PLACEHOLDER_RE.findall(text or ""))


def main() -> int:
    used = used_keys()
    problems = 0

    locale_files = sorted(LOCALES.glob("*.json")) if LOCALES.is_dir() else []
    if not locale_files:
        print(f"[error] папка локалей пуста или не найдена: {LOCALES}")
        return 2

    en_data = None
    if (LOCALES / "en.json").is_file():
        en_data = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    else:
        print("[error] нет en.json — базового языка")
        problems += 1

    en_strings = (en_data or {}).get("strings", {})
    print(f"Ключей в коде: {len(used)}; языков в locales: {len(locale_files)}")
    print()

    for path in locale_files:
        code = path.stem
        try:
            strings = json.loads(path.read_text(encoding="utf-8")).get("strings", {})
        except Exception as exc:
            print(f"[error] {code}: битый json ({exc})")
            problems += 1
            continue

        missing = sorted(used - set(strings))
        unused = sorted(set(strings) - used)
        mism = [
            (k, sorted(placeholders(v)))
            for k, v in strings.items()
            if k in en_strings and placeholders(v) != placeholders(en_strings.get(k, ""))
        ]

        print(
            f"[{'ok' if not (missing or unused or mism) else '!!'}] {code}: "
            f"ключей {len(strings)}, нет в коде {len(unused)}, "
            f"нет в переводе {len(missing)}, плейсхолдеры {len(mism)}"
        )
        for k in missing:
            print(f"    нет перевода: {k}")
        for k in unused:
            print(f"    неиспользуемый: {k}")
        for k, ph in mism:
            print(f"    плейсхолдеры {ph} != en: {k}")
        problems += len(missing) + len(unused) + len(mism)

    print()
    if problems:
        print(f"Обнаружено проблем: {problems}")
        return 2
    print("Проблем не обнаружено.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
