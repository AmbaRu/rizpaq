from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


_ISOLATED_IMPORT = """
import builtins, sys, os

_real = builtins.__import__

def _fake(name, *a, **k):
    if name.startswith("PySide6"):
        raise ImportError("PySide6 is not available (isolated import)")
    if name == "ui" or name.startswith("ui."):
        raise ImportError("ui package is not available (isolated import)")
    return _real(name, *a, **k)

builtins.__import__ = _fake

sys.path.insert(0, {root!r})

import core.headless as h

# Проверим, что ключевые имена есть и что подмена действительно
# не пропустила ни PySide6, ни ui.* в sys.modules.
assert "PySide6" not in sys.modules, "PySide6 всё-таки импортирован"
assert not any(m == "ui" or m.startswith("ui.") for m in sys.modules), \\
    "пакет ui всё-таки импортирован"

for name in ("_headless_task", "_parse_task_args", "_build_test_cmd",
             "_write_temp_error", "_write_task_log", "is_headless_op",
             "run_headless", "ACTION_TEST"):
    assert hasattr(h, name), "нет имени: " + name

print("OK")
"""


class TestIsolatedImport(unittest.TestCase):

    def _run(self, timeout: int = 60):
        script = _ISOLATED_IMPORT.format(root=str(ROOT))
        return subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

    def test_import_headless_without_qt(self):
        r = self._run()
        self.assertIn(
            "OK", r.stdout,
            f"импорт не прошёл. stdout={r.stdout!r} stderr={r.stderr!r}",
        )

    def test_headless_does_not_pull_tasks_to_qt(self):
        script = _ISOLATED_IMPORT.format(root=str(ROOT))
        r = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        self.assertNotIn(
            "PySide6", r.stderr or "",
            f"импорт core.tasks потянул Qt: {r.stderr}",
        )


class TestNoQtImportsAtModuleLevel(unittest.TestCase):

    def _module_ast(self):
        path = ROOT / "core" / "headless.py"
        return ast.parse(path.read_text(encoding="utf-8"))

    def test_no_top_level_qt_imports(self):
        tree = self._module_ast()
        offenders = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith(("PySide6", "PyQt")):
                        offenders.append((node.lineno, a.name))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith(("PySide6", "PyQt")):
                    offenders.append((node.lineno, mod))
                if mod == "ui" or mod.startswith("ui."):
                    offenders.append((node.lineno, mod))
        self.assertEqual(
            offenders, [],
            f"на уровне модуля не должно быть Qt/ui-импортов: {offenders}",
        )

    def test_tasks_import_present_at_module_level(self):
        tree = self._module_ast()
        found = False
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and (node.module or "") == "core.tasks":
                found = True
                break
        self.assertTrue(
            found,
            "core.tasks должен импортироваться на уровне модуля",
        )


class TestParseTaskArgs(unittest.TestCase):


    def _fn(self):
        from core.headless import _parse_task_args
        return _parse_task_args

    def test_empty_returns_empty_strings(self):
        f = self._fn()
        self.assertEqual(f([]), ("", ""))
        self.assertEqual(f(None), ("", ""))

    def test_path_and_job(self):
        f = self._fn()
        path, job = f([r"C:\tasks.rzp", "--job", "abc-123"])
        self.assertEqual(path, r"C:\tasks.rzp")
        self.assertEqual(job, "abc-123")

    def test_path_only(self):
        f = self._fn()
        path, job = f([r"C:\tasks.rzp"])
        self.assertEqual(path, r"C:\tasks.rzp")
        self.assertEqual(job, "")

    def test_missing_job_value(self):

        f = self._fn()
        path, job = f([r"C:\tasks.rzp", "--job"])
        self.assertEqual(path, r"C:\tasks.rzp")
        self.assertEqual(job, "")

    def test_job_before_path_is_not_found(self):
        f = self._fn()
        path, job = f(["--job", "abc", r"C:\tasks.rzp"])

        self.assertEqual(path, "--job")

        self.assertEqual(job, "")

    def test_extra_args_ignored(self):

        f = self._fn()
        path, job = f([r"C:\tasks.rzp", "--job", "abc", "--verbose"])
        self.assertEqual(path, r"C:\tasks.rzp")
        self.assertEqual(job, "abc")

    def test_whitespace_trimmed(self):
        f = self._fn()
        path, job = f(["  C:\\tasks.rzp  ", "--job", "  abc  "])
        self.assertEqual(path, "C:\\tasks.rzp")
        self.assertEqual(job, "abc")


class TestBuildTestCmd(unittest.TestCase):

    def _fn(self):
        from core.headless import _build_test_cmd
        return _build_test_cmd

    def test_full_mode(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "full")
        self.assertEqual(cmd, ["zpaq", "t", r"C:\a.zpaq"])

    def test_checksum_mode(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "checksum")
        self.assertIn("-all", cmd)
        self.assertIn("-checksum", cmd)

    def test_verify_mode(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "verify")
        self.assertIn("-verify", cmd)
        self.assertNotIn("-paranoid", cmd)

    def test_paranoid_mode_with_tmp(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "paranoid", r"C:\tmp\out")
        self.assertIn("-verify", cmd)
        self.assertIn("-paranoid", cmd)
        self.assertIn("-to", cmd)
        i = cmd.index("-to")
        self.assertEqual(cmd[i + 1], r"C:\tmp\out")

    def test_paranoid_mode_without_tmp(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "paranoid")
        self.assertIn("-paranoid", cmd)
        self.assertNotIn("-to", cmd)

    def test_password_appended_last(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", "secret", "full")
        self.assertIn("-key", cmd)
        self.assertEqual(cmd[cmd.index("-key") + 1], "secret")

        self.assertEqual(cmd[-2:], ["-key", "secret"])

    def test_unknown_mode_falls_back_to_full(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "weird")

        self.assertEqual(cmd, ["zpaq", "t", r"C:\a.zpaq"])

    def test_missing_mode_falls_back_to_full(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, None)
        self.assertEqual(cmd, ["zpaq", "t", r"C:\a.zpaq"])

    def test_mode_case_insensitive(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", None, "CHECKSUM")
        self.assertIn("-checksum", cmd)

    def test_password_with_paranoid(self):
        f = self._fn()
        cmd = f("zpaq", r"C:\a.zpaq", "pw", "paranoid", r"C:\tmp")
        self.assertIn("-paranoid", cmd)
        self.assertIn("-to", cmd)
        self.assertIn("-key", cmd)
        self.assertEqual(cmd[cmd.index("-key") + 1], "pw")


class TestIsHeadlessOp(unittest.TestCase):

    def _fn(self):
        from core.headless import is_headless_op
        return is_headless_op

    def test_empty(self):
        self.assertFalse(self._fn()([]))
        self.assertFalse(self._fn()(None))

    def test_known_ops(self):
        f = self._fn()
        for op in ("--test", "--extract-here", "--create", "--task"):
            with self.subTest(op=op):
                self.assertTrue(f([op, "whatever"]))

    def test_unknown_op(self):
        f = self._fn()
        self.assertFalse(f(["--nope"]))
        self.assertFalse(f([r"C:\archive.zpaq"]))
        self.assertFalse(f(["--extract"]))

    def test_whitespace_around_op(self):
        f = self._fn()
        self.assertTrue(f(["  --test  ", "arg"]))


class TestConstantsReachable(unittest.TestCase):

    def test_action_test_matches_core_tasks(self):
        import core.headless as h
        import core.tasks as T
        self.assertEqual(h.ACTION_TEST, T.ACTION_TEST)
        self.assertEqual(h.ACTION_TEST, "test")

    def test_headless_ops_tuple(self):
        import core.headless as h
        self.assertEqual(
            set(h._HEADLESS_OPS),
            {"--test", "--extract-here", "--create", "--task"},
        )


class TestRunHeadlessUnknownOp(unittest.TestCase):

    def test_unknown_op_returns_one(self):
        from core.headless import run_headless


        rc = run_headless(["--nope"])
        self.assertEqual(rc, 1)

    def test_missing_arg_returns_one(self):
        from core.headless import run_headless

        rc = run_headless(["--test"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
