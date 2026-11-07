


















from __future__ import annotations

import os
import os.path
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.engine_path import (              
    has_non_latin,
    rewrite_cmd,
)

                                                                   
                                                            
ZPAQ_NAME = "zpaqfranz.exe"
from workers.streaming import StreamingZpaqThread              

                                                                            
                                                                          
ECHO_ARGV = (
    "import os, sys, time\n"
    "sys.stdout.write('|ARGV|' + ' ;; '.join(sys.argv[1:]) + chr(10))\n"
    "sys.stdout.write('|CWD|' + os.getcwd() + chr(10))\n"
    "sys.stdout.flush()\n"
    "time.sleep(120)\n"
)

                                       
SILENT = "import time\ntime.sleep(120)\n"

                                                                            
                                                                               
                                                                              
                                                                             
                                                                           
                                                                           
                                                                             
ECHO_QUICK = (
    "import os, sys\n"
    "sys.stdout.write('|ARGV|' + ' ;; '.join(sys.argv[1:]) + chr(10))\n"
    "sys.stdout.write('|CWD|' + os.getcwd() + chr(10))\n"
    "sys.stdout.flush()\n"
)

                                                                            
                                   
PROMPTING = (
    "import sys, time\n"
    "sys.stdout.write('zpaqfranz v64.7g' + chr(10))\n"
    "sys.stdout.write('Archive is AES-encrypted' + chr(10))\n"
    "sys.stdout.write('Enter AES password:  :' + chr(10))\n"
    "sys.stdout.flush()\n"
    "time.sleep(120)\n"
)


class StreamingBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
                                                                      
                                                                      
                                                 
        try:
            from PySide6.QtCore import QCoreApplication

            cls._app = QCoreApplication.instance() or QCoreApplication([])
        except Exception:
            cls._app = None

    def setUp(self):
        import shutil
        import tempfile

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_str_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def child(self, name: str, source: str) -> Path:
        p = self.dir / name
        p.write_text(source, encoding="utf-8")
        return p

    def run_worker(self, cmd, timeout=30, stall_timeout=1):
        pass





        import threading

        import workers.streaming as st

        real = st.STALL_TIMEOUT
        st.STALL_TIMEOUT = stall_timeout
        box = {}

        def target():
            worker = StreamingZpaqThread(cmd)
            box["rc"], box["text"] = worker._run_stream()

        th = threading.Thread(target=target, daemon=True)
        t0 = time.monotonic()
        try:
            th.start()
            th.join(timeout=timeout)
        finally:
            st.STALL_TIMEOUT = real

        return box, time.monotonic() - t0, th.is_alive()


class TestPathPreparation(StreamingBase):
    pass







    def test_russian_folder_makes_argument_latin(self):
        pass








        folder = self.dir / "Резерв"
        folder.mkdir()
        arc = folder / "backup.zpaq"
        arc.write_bytes(b"x" * 32)

        out, _cwd, _subs = rewrite_cmd([ZPAQ_NAME, "l", str(arc)])

        self.assertFalse(
            has_non_latin(out[2]),
            f"в движок ушёл нелатинский путь: {out[2]} — движок на нём "
            f"зависает")

    def test_worker_passes_command_through_rewrite(self):
        pass







        import workers.streaming as st

        seen = {}
        real = st.rewrite_cmd

        def spy(cmd):
            seen["cmd"] = list(cmd)
            return real(cmd)

        folder = self.dir / "Резерв"
        folder.mkdir()
        arc = folder / "backup.zpaq"
        arc.write_bytes(b"x" * 32)

        st.rewrite_cmd = spy
        try:
            worker = StreamingZpaqThread(
                [sys.executable, "-u", "child.py", str(arc)]
            )
            worker._run_stream()
        finally:
            st.rewrite_cmd = real

        self.assertIn(
            "cmd", seen,
            "воркер не вызвал rewrite_cmd — подготовка пути не работает")

    def test_latin_path_left_alone(self):
        pass
        arc = self.dir / "archive.zpaq"
        arc.write_bytes(b"x" * 32)

        box, dt, alive = self.run_worker(
            [sys.executable, "-u", str(self.child("echo.py", ECHO_ARGV)),
             str(arc)],
            timeout=20,
        )
        self.assertFalse(alive)
        self.assertIn(str(arc), box.get("text", ""))

    def zpaq_stub(self, source: str) -> Path:
        pass















        import sys as _sys

        body = self.child("stub_body.py", source)
        stub = self.dir / "zpaqfranz.cmd"
        stub.write_text(
            f'@echo off\r\n"{_sys.executable}" -u "{body}" %*\r\n',
            encoding="ascii",
        )
        return stub

    def test_explicit_cwd_wins(self):
        pass

















        import core.engine_path as ep
        import workers.streaming as st

        explicit = self.dir / "wanted"
        explicit.mkdir()
        arc = self.dir / "Резерв" / "backup.zpaq"
        arc.parent.mkdir()
        arc.write_bytes(b"x" * 32)

        stub = self.zpaq_stub(ECHO_QUICK)
                                                                           
                                                
        real_short = ep.short_path
        ep.short_path = lambda p: ""
        real_stall = st.STALL_TIMEOUT
        st.STALL_TIMEOUT = 1
                                                                          
                                                                           
                                                                         
                                                                         
                                                                      
                            
        cmd = [str(stub), "l", str(arc)]
        try:
            _prepared, hint, _subs = rewrite_cmd(list(cmd))
            self.assertTrue(
                hint,
                "подсказка рабочего каталога не появилась — сравнивать нечего, "
                "проверка снова холостая")

            worker = StreamingZpaqThread(cmd, cwd=str(explicit))
            _rc, text = worker._run_stream()
        finally:
            st.STALL_TIMEOUT = real_stall
            ep.short_path = real_short

        seen = next(
            (ln[len("|CWD|"):] for ln in text.splitlines()
             if ln.startswith("|CWD|")),
            "",
        )
        self.assertTrue(seen, f"потомок не отпечатал каталог: {text[:200]}")
        self.assertEqual(
            os.path.normcase(os.path.abspath(seen)),
            os.path.normcase(os.path.abspath(str(explicit))),
            f"рабочий каталог подменён: процесс видел {seen}, "
            f"а подсказка из подготовки пути предлагала {hint}")


class TestStallGuard(StreamingBase):
    pass

    def test_silent_process_does_not_hang(self):
        pass






        box, dt, alive = self.run_worker(
            [sys.executable, "-u", str(self.child("silent.py", SILENT))],
            timeout=20,
            stall_timeout=1,
        )
        self.assertFalse(
            alive,
            f"воркер не вернулся за {dt:.0f} с при молчащем процессе — завис")
        self.assertLess(dt, 15, f"ждал {dt:.0f} с вместо предела")
        self.assertNotEqual(box.get("rc"), 0, "ненулевой код ожидаем")

    def test_password_prompt_is_explained(self):
        pass





        box, dt, alive = self.run_worker(
            [sys.executable, "-u", str(self.child("prompt.py", PROMPTING))],
            timeout=20,
            stall_timeout=1,
        )
        self.assertFalse(alive, "воркер не вернулся — завис")
        text = box.get("text", "")
        self.assertIn("пароль", text.lower(),
                      f"в результате нет упоминания пароля: {text[-200:]}")
        self.assertIn("нелатинск", text.lower(),
                      f"в результате нет указания на причину: {text[-200:]}")

    def test_no_busy_spin_while_waiting(self):
        pass







        import workers.streaming as st

        real = st.STALL_TIMEOUT
        st.STALL_TIMEOUT = 3
        cpu0 = time.process_time()
        try:
            box, dt, alive = self.run_worker(
                [sys.executable, "-u", str(self.child("silent2.py", SILENT))],
                timeout=20,
                stall_timeout=3,
            )
            cpu = time.process_time() - cpu0
        finally:
            st.STALL_TIMEOUT = real

        self.assertFalse(alive, "воркер завис")

                                                                        
                                                       
                                                                       
                           
                                                                           
                                                                      
                                                                        
                                                                    
                                                                  
                                                        
        self.assertLess(
            cpu, 0.4,
            f"процессор был занят {cpu:.2f} с при ожидании {dt:.2f} с — "
            f"цикл крутится впустую")

    def test_cancelled_run_is_not_mistaken_for_a_stall(self):
        pass







        import threading

        import workers.streaming as st

        real = st.STALL_TIMEOUT
        st.STALL_TIMEOUT = 30                                         
        box = {}
        worker = StreamingZpaqThread(
            [sys.executable, "-u", str(self.child("prompt2.py", PROMPTING))]
        )

        def target():
            box["rc"], box["text"] = worker._run_stream()

        th = threading.Thread(target=target, daemon=True)
        try:
            th.start()
            time.sleep(1.5)
            worker.cancel_request()
            th.join(timeout=15)
        finally:
            st.STALL_TIMEOUT = real

        self.assertFalse(th.is_alive(), "отмена не сработала за 15 с")
        self.assertFalse(
            "не смог открыть файл" in box.get("text", ""),
            "отмена выдана за сбой: в тексте обещана ложная диагностика")


if __name__ == "__main__":
    unittest.main()
