from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"__pycache__", "build", "dist", "version", "locales", "doc"}


WATCHED = [
    ROOT / "core" / "zpaq_cli.py",
    ROOT / "core" / "universal_ops.py",
    ROOT / "core" / "tasks.py",
]


ALLOWED_DEAD = {
    "core/source_sets.py": "заготовка фичи «наборы источников», ждёт решения",
}


def _project_files():
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        yield p


def reachable_from_production(module: Path):
    src = module.read_text(encoding="utf-8")
    tree = ast.parse(src)

    funcs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[node.name] = node


    calls = {name: set() for name in funcs}
    for name, node in funcs.items():
        seen = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                called = getattr(f, "id", None) or getattr(f, "attr", None)
                if called in funcs and called != name:
                    seen.add(called)
            elif isinstance(sub, ast.Name) and sub.id in funcs and sub.id != name:
                seen.add(sub.id)
            elif isinstance(sub, ast.Attribute) and sub.attr in funcs and sub.attr != name:
                seen.add(sub.attr)
        calls[name] = seen


    mod_name = module.stem
    entries = set()
    for other in _project_files():
        if other == module:
            continue
        rel = other.relative_to(ROOT)
        if str(rel).startswith("tests"):
            continue
        try:
            t = ast.parse(other.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        for node in ast.walk(t):
            hit = False
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(mod_name):
                hit = True
            if isinstance(node, ast.Attribute) and node.attr in funcs:
                hit = True
            if isinstance(node, ast.Name) and node.id in funcs:
                hit = True
            if hit:
                for f in funcs:
                    if (
                        (isinstance(node, ast.ImportFrom) and any(
                            a.name == f for a in node.names))
                        or (isinstance(node, ast.Attribute) and node.attr == f)
                        or (isinstance(node, ast.Name) and node.id == f)
                    ):
                        entries.add(f)

    reachable = set()
    stack = list(entries)
    while stack:
        name = stack.pop()
        if name in reachable or name not in funcs:
            continue
        reachable.add(name)
        stack.extend(calls.get(name, ()))

    return reachable, set(funcs) - reachable


class TestNoDeadCodeInCore(unittest.TestCase):

    def test_no_unreachable_functions(self):
        problems = []
        for module in WATCHED:
            if not module.is_file():
                continue
            reachable, dead = reachable_from_production(module)
            if not dead:
                continue
            key = module.relative_to(ROOT).as_posix()
            if key in ALLOWED_DEAD:
                continue
            size = sum(
                n.end_lineno - n.lineno + 1
                for n in ast.parse(module.read_text(encoding="utf-8")).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name in dead
            )
            problems.append(
                f"{key}: недостижимые функции {sorted(dead)} (~{size} строк)"
            )
        self.assertEqual(
            problems,
            [],
            "Обнаружен недостижимый код — удалите его:\n" + "\n".join(problems),
        )

    def test_allowed_dead_modules_still_exist(self):
        for key, reason in ALLOWED_DEAD.items():
            with self.subTest(module=key):
                path = ROOT / key
                if not path.is_file():
                    self.fail(
                        f"{key} больше не существует — уберите его из ALLOWED_DEAD"
                    )
                reachable, dead = reachable_from_production(path)
                if not dead:
                    self.fail(
                        f"{key} стал достижимым ({sorted(reachable)}), "
                        f"исключение больше не нужно"
                    )

    def test_zpaq_cli_has_no_extraction_code_left(self):
        src = (ROOT / "core" / "zpaq_cli.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        names = {
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for forbidden in (
            "extract_one_file",
            "extract_folder_batch",
            "run_zpaq_streaming",
            "_stream_lines",
            "run_zpaq_stdout_to_file",
            "find_extracted_file",
        ):
            self.assertNotIn(
                forbidden, names, f"{forbidden} вернулась в core/zpaq_cli.py"
            )

    def test_extraction_lives_in_workers(self):

        path = ROOT / "workers" / "extract_workers.py"
        self.assertTrue(path.is_file(), "workers/extract_workers.py исчез")
        src = path.read_text(encoding="utf-8")
        for cls in (
            "ExtractFileWorker",
            "ExtractFolderBatchWorker",
            "ExtractFolderWorker",
        ):
            self.assertIn(cls, src, f"{cls} исчез из workers/extract_workers.py")

    def test_removed_functions_are_not_imported_anywhere(self):

        removed = {
            "extract_one_file",
            "extract_folder_batch",
            "run_zpaq_streaming",
            "_stream_lines",
            "run_zpaq_stdout_to_file",
            "find_extracted_file",
            "parse_progress_line",
        }
        leftovers = []
        for path in _project_files():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        if a.name in removed:
                            leftovers.append(
                                f"{path.relative_to(ROOT)} импортирует {a.name}"
                            )
        self.assertEqual(leftovers, [], "\n".join(leftovers))


class TestOrphanedCopiesRemoved(unittest.TestCase):

    ORPHAN_PATH = ROOT / "tests" / "association_dialog.py"

    def test_orphan_file_is_gone(self):
        if not self.ORPHAN_PATH.is_file():
            return
        rel = self.ORPHAN_PATH.relative_to(ROOT).as_posix()
        self.fail(
            f"{rel} снова существует.\n"
            f"\n"
            f"Это дорелизная копия ui/association_dialog.py — не тест. "
            f"Она не попадает в прогон (run_all.py ищет test_*.py), не "
            f"импортируется никем и сохраняет дорелизный вариант снятия "
            f"ассоциаций (возврат unregister_* игнорировался, UserChoice "
            f"не снимался, диалог молчал об ошибке).\n"
            f"\n"
            f"Удалите файл:\n"
            f"    del {self.ORPHAN_PATH}\n"
            f"(или через Проводник — правой кнопкой «Удалить»).\n"
            f"\n"
            f"Если копия нужна для работы — это ошибка: рабочая версия "
            f"лежит в ui/association_dialog.py и уже содержит "
            f"исправления 2.3.1."
        )

    def test_ui_copy_still_present(self):
        ui_path = ROOT / "ui" / "association_dialog.py"
        self.assertTrue(
            ui_path.is_file(),
            "ui/association_dialog.py исчез — это рабочий модуль, "
            "его удаление сломает диалог интеграции с проводником",
        )

    def test_ui_copy_is_still_imported(self):
        consumers = [
            ROOT / "ui" / "menu_actions.py",
        ]
        found = False
        for path in consumers:
            if not path.is_file():
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod == "ui.association_dialog":
                        found = True
                        break


                    if mod.endswith(".association_dialog") and "ui" in mod:
                        found = True
                        break
                if isinstance(node, ast.Call):
                    f = node.func
                    name = getattr(f, "id", None) or getattr(f, "attr", None)
                    if name == "AssociationDialog":
                        found = True
                        break
            if found:
                break
        self.assertTrue(
            found,
            "ui/association_dialog.py больше не используется — "
            "проверьте, нужен ли он вообще. Если да — обновите "
            "test_ui_copy_is_still_imported (укажите модуль-потребитель); "
            "если нет — удалите рабочий файл вместе с тестом.",
        )


if __name__ == "__main__":
    unittest.main()
