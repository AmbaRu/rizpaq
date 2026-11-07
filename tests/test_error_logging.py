













from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.config as cfg              


class TestWriteErrorLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _with_config_dir(self, d: Path):
        pass
        return mock.patch.object(
            cfg, "default_path", return_value=d / cfg.CONFIG_NAME
        )

    def test_writes_next_to_config(self):
        with self._with_config_dir(self.dir):
            path = cfg.write_error_log("Traceback: something broke")

        self.assertIsNotNone(path, "лог не записан никуда")
        self.assertEqual(path.parent, self.dir)
        self.assertTrue(path.is_file())
        self.assertIn("something broke", path.read_text(encoding="utf-8"))

    def test_log_has_timestamp_header(self):
        with self._with_config_dir(self.dir):
            path = cfg.write_error_log("boom")
        text = path.read_text(encoding="utf-8")
        self.assertIn("Rizpaq error", text)
        self.assertIn("boom", text)

    def test_creates_missing_directory(self):
        deep = self.dir / "a" / "b" / "c"
        with self._with_config_dir(deep):
            path = cfg.write_error_log("boom")
        self.assertTrue(path.is_file(), "вложенные папки должны создаваться")

    def test_not_current_directory_by_default(self):
        pass



        with self._with_config_dir(self.dir):
            path = cfg.write_error_log("boom")
        self.assertNotEqual(path.parent, Path.cwd() / ".")

    def test_falls_back_when_preferred_dir_unwritable(self):
        pass



        with self._with_config_dir(self.dir):
            real_mkdir = Path.mkdir

            def guarded(self_dir, *a, **k):
                if self_dir == self.dir:
                    raise PermissionError("read-only")
                return real_mkdir(self_dir, *a, **k)

            fallback = self.dir / "fallback_dir"
            with mock.patch.object(Path, "mkdir", guarded):
                path = cfg.write_error_log("boom")

        self.assertIsNotNone(path, "не нашлось места для лога")
        self.assertIn("boom", path.read_text(encoding="utf-8"))
        self.assertNotEqual(path.parent, self.dir, "упали на основной путь")

    def test_returns_none_when_nothing_writable(self):
        with self._with_config_dir(self.dir):
            with mock.patch.object(Path, "write_text", side_effect=OSError("nope")), \
                 mock.patch.object(Path, "open", side_effect=OSError("nope")), \
                 mock.patch.object(Path, "mkdir", side_effect=PermissionError("x")):
                path = cfg.write_error_log("boom")
        self.assertIsNone(path, "ожидался None при полном отказе записи")

    def test_empty_text_is_not_written(self):
        with self._with_config_dir(self.dir):
            self.assertIsNone(cfg.write_error_log(""))

    def test_second_error_appends(self):
        pass
        with self._with_config_dir(self.dir):
            cfg.write_error_log("ПЕРВОЕ ПАДЕНИЕ")
            cfg.write_error_log("ВТОРОЕ ПАДЕНИЕ")
            text = (self.dir / cfg.LOG_NAME).read_text(encoding="utf-8")

        self.assertIn("ПЕРВОЕ ПАДЕНИЕ", text)
        self.assertIn("ВТОРОЕ ПАДЕНИЕ", text)

    def test_huge_log_is_trimmed(self):
        with self._with_config_dir(self.dir):
            log = self.dir / cfg.LOG_NAME
            log.write_text("x" * (cfg.LOG_MAX_BYTES + 1000), encoding="utf-8")
            path = cfg.write_error_log("СВЕЖАЯ ОШИБКА")
            text = path.read_text(encoding="utf-8")

        self.assertIn("СВЕЖАЯ ОШИБКА", text, "новая ошибка обязана попасть в лог")
        self.assertLess(
            len(text), cfg.LOG_MAX_BYTES, "лог должен быть подрезан, а не расти"
        )

    def test_deduplicates_same_path(self):
        pass
        with self._with_config_dir(self.dir):
            cands = cfg._log_candidates(cfg.LOG_NAME)
        self.assertLessEqual(
            len(cands), len(set(str(c) for c in cands)), "в кандидатах есть дубли"
        )

    def test_candidates_include_fallbacks(self):
        with self._with_config_dir(self.dir):
            cands = [str(c) for c in cfg._log_candidates(cfg.LOG_NAME)]
        has_temp = any("Temp" in c or "TEMP" in c.upper() for c in cands)
        self.assertTrue(has_temp, "в кандидатах должен быть %TEMP%")


class TestLogPath(unittest.TestCase):
    def test_log_next_to_config(self):
        with mock.patch.object(cfg, "default_path", return_value=Path("C:/x/zpaq_gui.json")):
            self.assertEqual(cfg.log_path(), Path("C:/x") / cfg.LOG_NAME)

    def test_log_name_is_not_the_old_cwd_name(self):
        pass
        self.assertNotEqual(cfg.LOG_NAME, "zpaq_gui_error.log")

    def test_config_module_does_not_import_qt(self):
        pass







        import ast

        tree = ast.parse(Path(cfg.__file__).read_text(encoding="utf-8"))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if "PySide6" in a.name:
                        offenders.append(f"строка {node.lineno}: {a.name}")
            if isinstance(node, ast.ImportFrom):
                if node.module and "PySide6" in node.module:
                    offenders.append(f"строка {node.lineno}: {node.module}")
        self.assertEqual(offenders, [], f"core/config.py тянет Qt: {offenders}")

    def test_log_survives_without_qt_importable(self):
        pass
        import subprocess

        script = (
            "import sys, builtins\n"
            "real = builtins.__import__\n"
            "def fake(name, *a, **k):\n"
            "    if name.startswith('PySide6'):\n"
            "        raise ImportError('Qt is broken')\n"
            "    return real(name, *a, **k)\n"
            "builtins.__import__ = fake\n"
            f"sys.path.insert(0, {str(Path(cfg.__file__).resolve().parent.parent)!r})\n"
            "import tempfile, os\n"
            "d = tempfile.mkdtemp()\n"
            "os.environ['ZPAQ_GUI_CONFIG'] = os.path.join(d, 'zpaq_gui.json')\n"
            "import core.config as c\n"
            "p = c.write_error_log('Qt broken but log works')\n"
            "print('LOG_WRITTEN' if p else 'LOG_FAILED')\n"
            "print(p)\n"
        )
        r = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=120,
        )
        self.assertIn("LOG_WRITTEN", r.stdout, f"лог не записался без Qt: {r.stdout} {r.stderr}")


class TestMainConsoleGuard(unittest.TestCase):
    pass




    def test_has_console_true_for_tty(self):
        import main as app_main

        fake = io.StringIO()
        fake.isatty = lambda: True
        with mock.patch.object(sys, "stdin", fake):
            self.assertTrue(app_main._has_console())

    def test_has_console_false_for_pipe(self):
        import main as app_main

        fake = io.StringIO()
        fake.isatty = lambda: False
        with mock.patch.object(sys, "stdin", fake):
            self.assertFalse(app_main._has_console())

    def test_has_console_false_for_none(self):
        import main as app_main

        with mock.patch.object(sys, "stdin", None):
            self.assertFalse(app_main._has_console())

    def test_has_console_survives_broken_stdin(self):
        import main as app_main

        class Broken:
            def isatty(self):
                raise ValueError("stream detached")

        with mock.patch.object(sys, "stdin", Broken()):
            self.assertFalse(app_main._has_console())

    def test_report_fatal_does_not_block_without_console(self):
        pass



        import main as app_main

        broken = io.StringIO()
        broken.isatty = lambda: False

        with mock.patch.object(sys, "stdin", broken), \
             mock.patch("builtins.input", side_effect=AssertionError("input() нельзя!")), \
             mock.patch.object(sys, "stderr", io.StringIO()):
            app_main._report_fatal("boom")

    def test_report_fatal_asks_enter_with_console(self):
        import main as app_main

        tty = io.StringIO()
        tty.isatty = lambda: True

        with mock.patch.object(sys, "stdin", tty), \
             mock.patch("builtins.input", return_value="") as inp, \
             mock.patch.object(sys, "stderr", io.StringIO()):
            app_main._report_fatal("boom")

        self.assertEqual(inp.call_count, 1, "с консолью пользователь должен узнать путь к логу")

    def test_report_fatal_writes_log(self):
        import main as app_main

                                                                           
                                               
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.dict(os.environ, {"ZPAQ_GUI_CONFIG": str(Path(d) / "zpaq_gui.json")}), \
             mock.patch.object(sys, "stdin", None), \
             mock.patch.object(sys, "stderr", io.StringIO()):
            app_main._report_fatal("уникальный текст ошибки 12345")

            log = Path(d) / cfg.LOG_NAME
            self.assertTrue(log.is_file(), "лог должен быть записан")
            self.assertIn(
                "уникальный текст ошибки 12345",
                log.read_text(encoding="utf-8"),
            )


class TestMainNoCwdLog(unittest.TestCase):
    pass

    def test_source_has_no_cwd_log_write(self):
        src = (Path(__file__).resolve().parent.parent / "main.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            'Path("zpaq_gui_error.log")',
            src,
            "лог больше не пишется в текущий каталог",
        )

    def test_error_path_uses_write_error_log(self):
        src = (Path(__file__).resolve().parent.parent / "main.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("write_error_log", src)


class TestFatalStartEndToEnd(unittest.TestCase):
    pass










    HARNESS = '''
import builtins, runpy
real = builtins.__import__
def fake(name, *a, **k):
    if name.startswith("PySide6"):
        raise ImportError("No module named 'PySide6' (check dependencies)")
    return real(name, *a, **k)
builtins.__import__ = fake
runpy.run_path("main.py", run_name="__main__")
'''

    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent
        self.harness = self.root / "_test_break_qt.py"
        self.harness.write_text(self.HARNESS, encoding="utf-8")
        self.addCleanup(self.harness.unlink, True)

    def test_broken_qt_without_console_exits_promptly(self):
        pass









        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ)
            env["ZPAQ_GUI_CONFIG"] = str(Path(d) / "zpaq_gui.json")

            proc = subprocess.Popen(
                [sys.executable, str(self.harness)],
                cwd=str(self.root),
                env=env,
                stdin=subprocess.PIPE,                                     
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                proc.wait(timeout=25)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                self.fail(
                    "Процесс не завершился за 25 с при сломанном PySide6 "
                    "и подключённом, но пустом stdin — висяк на input() вернулся"
                )
            finally:
                if proc.poll() is None:
                    proc.kill()
                out, err = proc.communicate(timeout=10)

        self.assertEqual(
            proc.returncode, 1, f"ожидался код выхода 1, получен {proc.returncode}"
        )

    def test_broken_qt_still_writes_log(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ)
            env["ZPAQ_GUI_CONFIG"] = str(Path(d) / "zpaq_gui.json")

            r = subprocess.run(
                [sys.executable, str(self.harness)],
                cwd=str(self.root),
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

            log = Path(d) / cfg.LOG_NAME
            self.assertTrue(log.is_file(), "лог должен писаться даже без Qt")
            text = log.read_text(encoding="utf-8")
            self.assertIn("ImportError", text)
            self.assertIn("No module named 'PySide6'", text)

    def test_stderr_reports_log_location(self):
        pass
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ)
            env["ZPAQ_GUI_CONFIG"] = str(Path(d) / "zpaq_gui.json")

            r = subprocess.run(
                [sys.executable, str(self.harness)],
                cwd=str(self.root),
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

        self.assertIn(
            cfg.LOG_NAME, r.stderr, "путь к логу должен печататься в stderr"
        )

    def test_source_uses_report_fatal_on_import_failure(self):
        pass







        import ast

        src = (Path(__file__).resolve().parent.parent / "main.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(src)

                                                           
        main_fn = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "main"
        )

        calls_input = False
        calls_report = False
        for node in ast.walk(main_fn):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name == "input":
                    calls_input = True
                if name == "_report_fatal":
                    calls_report = True

        self.assertFalse(
            calls_input,
            "в main() не должно быть прямого input() — это источник висяка",
        )
        self.assertTrue(
            calls_report,
            "обработчик отказа импорта Qt обязан звать _report_fatal",
        )


if __name__ == "__main__":
    unittest.main()
