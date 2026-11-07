
































from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication              

from core.paths import merge_tree              
from workers.extract_workers import ExtractFolderBatchWorker              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


                                                                     
DATA = "данные".encode("utf-8") * 50


class _Worker(ExtractFolderBatchWorker):
    pass






    def __init__(self, dest, files, rc=0):
        super().__init__(
            zpaq="zpaqfranz",                          
            archive="archive.zpaq",                     
            password=None,
            inner_prefix="",
            version=None,
            dest_folder=str(dest),
        )
        self._files = files
        self._rc = rc
                                                                      
                                                                       
                                                                          
        self.staging_seen = None

    def _run_stream(self):
        pass
        staging = Path(self.cmd[-1])                                     
        self.staging_seen = staging
        for name, data in self._files.items():
            p = staging / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        return self._rc, "[test] распаковано"


class StagingTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _make_dest(self, block: bool) -> Path:
        pass





        dest = self.tmp / "dest"
        dest.mkdir()
        (dest / "уже_было.txt").write_text("старое\n", encoding="utf-8")
        if block:
            (dest / "папка").write_text("я файл, а не папка\n", encoding="utf-8")
        return dest

    def _run(self, dest, files, rc=0):
        pass
        captured = {}
        w = _Worker(dest, files, rc=rc)
        w.done.connect(lambda res: captured.update(res))
                                                                      
                                                                       
                                              
        w.worker_started.connect(lambda: None)
        w.run()                                                    
        return captured, w


class TestFailureKeepsData(StagingTestBase):
    pass

    def test_merge_really_fails(self):
        pass
        dest = self._make_dest(block=True)
        src = self.tmp / "staging_probe"
        (src / "папка").mkdir(parents=True)
        (src / "папка" / "f.txt").write_bytes(DATA)

        raised = False
        try:
            merge_tree(src, dest)
        except Exception:
            raised = True
        self.assertTrue(
            raised,
            "признак не сработал: перенос прошёл, тест проверял бы не то")

    def test_data_survives_failed_merge(self):
        pass
        dest = self._make_dest(block=True)
        files = {
            "папка/внутри.txt": DATA,
            "report.docx": "документ".encode("utf-8") * 100,
        }

        res, w = self._run(dest, files)

        self.assertFalse(
            res.get("ok"), "перенос не должен был пройти успешно")

        staging = res.get("staging") or ""
        self.assertTrue(
            staging,
            "воркер не сообщил, где остались данные: ключ 'staging' пуст")
        staging_path = Path(staging)

                                                                           
        self.assertEqual(
            staging_path, w.staging_seen,
            "отчёт назвал не ту папку, которую создал движок")
        self.assertTrue(
            staging_path.exists(),
            f"временная папка удалена при провале: {staging}")
        self.assertTrue(
            (staging_path / "папка" / "внутри.txt").exists(),
            "файл из вложенной папки потерян")
        self.assertTrue(
            (staging_path / "report.docx").exists(),
            "документ потерян: его нет ни во временной папке, ни в назначении")

    def test_log_points_at_kept_data(self):
        pass
        dest = self._make_dest(block=True)
        res, w = self._run(dest, {"папка/внутри.txt": DATA})
        log = res.get("log", "")

        self.assertIn("temporary data kept", log,
                      "в логе нет указания, что данные сохранены")
        self.assertIn(str(res.get("staging")), log,
                      "в логе нет пути к сохранённым данным")


class TestSuccessAndCancelCleanUp(StagingTestBase):
    pass

    def test_success_removes_staging(self):
        dest = self._make_dest(block=False)
        res, w = self._run(dest, {"a.txt": DATA})

        self.assertTrue(res.get("ok"), f"перенос не прошёл: {res.get('log')}")
        self.assertEqual(
            res.get("staging"), "",
            "при успехе путь к сохранённым данным должен быть пустым")
        self.assertIsNotNone(w.staging_seen, "воркер не дошёл до разговора с движком")
        self.assertFalse(
            w.staging_seen.exists(),
            f"при успехе временная папка осталась на диске: {w.staging_seen}")
        self.assertTrue(
            (dest / "a.txt").exists(),
            "файл не оказался в назначении")

    def test_cancel_removes_staging(self):
        dest = self._make_dest(block=False)
        w = _Worker(dest, {"a.txt": DATA})
        w._cancel = True
        captured = {}
        w.done.connect(lambda res: captured.update(res))
                                                            
        w.worker_started.connect(lambda: None)
        w.run()

        self.assertTrue(captured.get("cancelled"), "отмена не распознана")
        self.assertFalse(captured.get("ok"))
        self.assertEqual(
            captured.get("staging"), "",
            "после отмены нечего сохранять, путь должен быть пустым")
        self.assertIsNotNone(w.staging_seen, "воркер не дошёл до разговора с движком")
        self.assertFalse(
            w.staging_seen.exists(),
            f"после отмены осталась папка с недораспакованным: {w.staging_seen}")

    def test_engine_error_keeps_data(self):
        pass



        dest = self._make_dest(block=False)
        res, w = self._run(dest, {"a.txt": DATA}, rc=2)

        self.assertFalse(res.get("ok"), "ошибка движка прошла как успех")

        staging = res.get("staging") or ""
        self.assertTrue(
            staging,
            "при ошибке движка распакованное удалять нельзя, "
            "а воркер вернул пустой путь — значит, удалил")
        self.assertTrue(
            Path(staging).exists(),
            f"временная папка удалена при ошибке движка: {staging}")
        self.assertEqual(
            Path(staging), w.staging_seen,
            "отчёт назвал не ту папку, которую создал движок")
        self.assertTrue(
            (Path(staging) / "a.txt").exists(),
            "файл потерян после ошибки движка")


class TestMergeTreeKeepsSource(unittest.TestCase):
    pass





    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_merge_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_source_survives_failed_copy(self):
        src = self.tmp / "staging"
        (src / "папка").mkdir(parents=True)
        (src / "папка" / "file.txt").write_bytes(DATA)

        dest = self.tmp / "dest"
        dest.mkdir()
        (dest / "папка").write_text("я файл, а не папка\n", encoding="utf-8")

        raised = False
        try:
            merge_tree(src, dest)
        except Exception:
            raised = True

        self.assertTrue(raised, "копирование должно было упасть")
        self.assertTrue(
            src.exists(),
            f"источник удалён при неудачном копировании: {src}")
        self.assertEqual(
            (src / "папка" / "file.txt").read_bytes(), DATA,
            "содержимое источника изменилось")


if __name__ == "__main__":
    unittest.main()
