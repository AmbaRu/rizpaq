















import tempfile
import unittest
from pathlib import Path

from core import tasks as T
from core.run_history import log_path_for, parse_log
from ui.archive_actions import ArchiveActionsMixin


class _FakeHost:
    pass

    def __init__(self, container, path):
        self._c = container
        self._p = path

    def _load_container(self):
        return self._c, self._p


class TestGuiRunLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = T.container_path(self.tmp.name)
        c = T.empty_container()
        w = T.add_work(c, "Фото", ["D:/Dasha"], "F:/Dasha.zpaq")
        j = T.add_job(c, w["id"], {
            "title": "Еженедельный бэкап",
            "action": "backup",
        })
        T.save_container(self.path, c)
        self.container = c
        self.job_id = j["id"]
        self.log_file = log_path_for(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, status, rc=None, output=None, job_id=None):
        host = _FakeHost(self.container, self.path)
        ArchiveActionsMixin._write_run_log_record(
            host, str(self.path), job_id or self.job_id, status, rc, output)

    def _entries(self):
        text = self.log_file.read_text(encoding="utf-8", errors="replace") \
            if self.log_file.is_file() else ""
        return parse_log(text)

    def test_error_written_and_parsed(self):
        self._write("error", rc=2, output="строка один\nстрока два\n")
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e.status, "error")
        self.assertEqual(e.rc, 2)
        self.assertEqual(e.work_title, "Фото")
        self.assertEqual(e.job_title, "Еженедельный бэкап")
        self.assertEqual(e.action, "backup")
        self.assertIn("строка два", e.tail)
                                                      
        self.assertIsNotNone(e.ts_dt)

    def test_ok_written(self):
        self._write("ok", rc=0)
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].status, "ok")
        self.assertEqual(entries[0].rc, 0)

    def test_busy_written_as_busy(self):
                                                                 
                                                   
        self._write("busy", rc=1)
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].status, "busy")

    def test_mode_none_skipped(self):
        found = T.find_job(self.container, self.job_id)
        found[1]["task_log_mode"] = "none"
                                                                
        T.save_container(self.path, self.container)
        self._write("error", rc=2, output="не должно попасть в лог")
        self.assertFalse(self.log_file.is_file())

    def test_unknown_job_and_bad_path_swallowed(self):
                                                                    
        self._write("ok", rc=0, job_id="нет-такого")
        host = _FakeHost(self.container, self.path)
        ArchiveActionsMixin._write_run_log_record(
            host, "Z:/несуществующий/путь.rzp", self.job_id, "ok", 0, None)
        self.assertEqual(self._entries(), [])

    def test_gui_and_headless_records_coexist(self):
                                                                
                                                     
        self._write("ok", rc=0)
        from core.headless import _build_log_header, _write_task_log
        found = T.find_job(self.container, self.job_id)
        work, job = found
        header = _build_log_header(str(self.path), work, job, 0)
        _write_task_log(str(self.path), header, "", mode="short", rc=0)
        entries = self._entries()
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e.status == "ok" for e in entries))


if __name__ == "__main__":
    unittest.main()
