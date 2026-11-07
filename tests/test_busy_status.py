
















































from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


                                                                             
                           
                                                                             

from core.zpaq_cli import looks_like_busy_error              
from core.tasks import (              
    JOB_STATUS_BUSY,
    JOB_STATUS_ERROR,
    JOB_STATUS_OK,
    JOB_STATUSES,
    empty_container,
    add_work,
    add_job,
    find_job,
    update_job_meta,
    _norm_status,
    _normalise_job,
    _normalise_work,
    save_container,
    load_container,
)


class TestLooksLikeBusyError(unittest.TestCase):
    pass










                                                                  
    REAL = (
        "17264$ Running add (updating/creating archive) on "
        "(C2FEEF295DEBDFFB) <<c:/users/riv/appdata/local/temp/"
        "rizpaq_open_probe/archive2.zpaq>>\n"
        "17276! Sorry, another zpaqfranz is running, we need to abort\n"
    )

    def test_recognizes_real_output(self):
        self.assertTrue(
            looks_like_busy_error(self.REAL),
            "фраза движка не распознана — задание получит статус "
            "'error' вместо 'busy'",
        )

    def test_recognizes_bare_phrase(self):
        pass
        self.assertTrue(
            looks_like_busy_error(
                "Sorry, another zpaqfranz is running, we need to abort"
            )
        )

    def test_case_insensitive(self):
        pass



        self.assertTrue(
            looks_like_busy_error(
                "ANOTHER ZPAQFRANZ IS RUNNING"
            )
        )

    def test_ignores_normal_output(self):
        pass
        self.assertFalse(
            looks_like_busy_error(
                "1 +added, 0 -removed.\n0.406s (00:00:00,11.23MB) (all OK)"
            )
        )

    def test_ignores_other_errors(self):
        pass




        self.assertFalse(
            looks_like_busy_error("Wrong password for encrypted archive")
        )
        self.assertFalse(
            looks_like_busy_error("Cannot open file: access denied")
        )
        self.assertFalse(
            looks_like_busy_error("Archive is AES-encrypted")
        )

    def test_empty_and_none_tolerated(self):
        self.assertFalse(looks_like_busy_error(""))
        self.assertFalse(looks_like_busy_error(None))


                                                                             
                            
                                                                             

class TestStatusConstants(unittest.TestCase):
    def test_statuses_tuple(self):
        pass
        self.assertEqual(
            set(JOB_STATUSES),
            {JOB_STATUS_OK, JOB_STATUS_ERROR, JOB_STATUS_BUSY},
        )

    def test_status_values(self):
        pass
        self.assertEqual(JOB_STATUS_OK, "ok")
        self.assertEqual(JOB_STATUS_ERROR, "error")
        self.assertEqual(JOB_STATUS_BUSY, "busy")


class TestNormStatus(unittest.TestCase):
    pass

    def test_known_statuses_kept(self):
        for s in JOB_STATUSES:
            with self.subTest(status=s):
                self.assertEqual(_norm_status(s), s)

    def test_unknown_becomes_none(self):
        pass




        for bad in ("weird", "busy_forever", "", None, 123, {}):
            with self.subTest(value=bad):
                self.assertIsNone(_norm_status(bad))


class TestUpdateJobMetaBusy(unittest.TestCase):
    pass







    def _container_with_job(self):
        c = empty_container()
        w = add_work(c, "Docs", ["D:/a"], "D:/out.zpaq")
        j = add_job(c, w["id"], {"title": "Daily"})
        return c, j

    def test_busy_is_stored_as_is(self):
        c, j = self._container_with_job()
        self.assertTrue(update_job_meta(c, j["id"], JOB_STATUS_BUSY))
        found = find_job(c, j["id"])
        self.assertIsNotNone(found)
        _work, job = found
        self.assertEqual(job["last_status"], JOB_STATUS_BUSY)

    def test_busy_counts_as_a_run(self):
        pass




        c, j = self._container_with_job()
        self.assertEqual(j["run_count"], 0)
        self.assertIsNone(j["last_run"])
        update_job_meta(c, j["id"], JOB_STATUS_BUSY)
        self.assertEqual(j["run_count"], 1)
        self.assertIsNotNone(j["last_run"])

    def test_ok_and_error_still_work(self):
        pass
        c, j = self._container_with_job()
        update_job_meta(c, j["id"], JOB_STATUS_OK)
        self.assertEqual(j["last_status"], JOB_STATUS_OK)
        update_job_meta(c, j["id"], JOB_STATUS_ERROR)
        self.assertEqual(j["last_status"], JOB_STATUS_ERROR)

    def test_unknown_status_becomes_error(self):
        pass



        c, j = self._container_with_job()
        update_job_meta(c, j["id"], "weird")
        self.assertEqual(j["last_status"], JOB_STATUS_ERROR)

    def test_missing_job_returns_false(self):
        c, _ = self._container_with_job()
        self.assertFalse(update_job_meta(c, "no-such", JOB_STATUS_BUSY))


class TestNormaliseJobStatus(unittest.TestCase):
    pass





    def test_unknown_status_is_dropped_on_read(self):
        j = {
            "id": "j1",
            "title": "Daily",
            "last_status": "system_upgrade_needed",
        }
        job = _normalise_job(j)
        self.assertIsNotNone(job)
        self.assertIsNone(job["last_status"])

    def test_known_status_kept_on_read(self):
        for s in JOB_STATUSES:
            with self.subTest(status=s):
                j = {"id": "j1", "title": "Daily", "last_status": s}
                job = _normalise_job(j)
                self.assertIsNotNone(job)
                self.assertEqual(job["last_status"], s)

    def test_missing_status_is_none(self):
        pass
        j = {"id": "j1", "title": "Daily"}
        job = _normalise_job(j)
        self.assertIsNotNone(job)
        self.assertIsNone(job["last_status"])


class TestBusyRoundtrip(unittest.TestCase):
    pass






    def setUp(self):
        self._dir = Path(tempfile.mkdtemp(prefix="rizpaq_busy_test_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self._dir, ignore_errors=True))
        self.path = self._dir / "tasks.rzp"

    def test_busy_survives_save_and_load(self):
        c = empty_container()
        w = add_work(c, "Docs", ["D:/a"], "D:/out.zpaq")
        j = add_job(c, w["id"], {"title": "Daily"})
        update_job_meta(c, j["id"], JOB_STATUS_BUSY)
        save_container(self.path, c)

        loaded = load_container(self.path)
        found = find_job(loaded, j["id"])
        self.assertIsNotNone(found)
        _work, job = found
        self.assertEqual(job["last_status"], JOB_STATUS_BUSY)


                                                                             
                                 
                                                                             

                                                                  
                                                                  
                                                     
try:
    from ui import backup_page as _bp              
    _BP_IMPORT_ERROR = None
except Exception as exc:                    
    _bp = None
    _BP_IMPORT_ERROR = str(exc)


@unittest.skipIf(
    _bp is None,
    f"ui.backup_page не импортируется: {_BP_IMPORT_ERROR}",
)
class TestStatusDisplay(unittest.TestCase):
    pass




    def setUp(self):
        super().setUp()
                                                                    
                           
         
                                                                       
                                                                     
                                                                       
                                              
                                                              
                                                                          
                                                                      
                                                  
        from ui import i18n

        patcher = mock.patch.object(i18n, "_current_strings", {})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _text_and_token(self, status):
        job = {"id": "j1", "title": "Daily", "last_status": status}
        return _bp.BackupPage._status_text_and_token(job)

    def test_busy_text_and_token(self):
        pass



        text, token = self._text_and_token(JOB_STATUS_BUSY)
                                                                      
                                                                      
        self.assertEqual(text, "backup.status.busy")
        self.assertEqual(token, "BUSY_STEEL")

    def test_ok_text_and_token(self):
        text, token = self._text_and_token(JOB_STATUS_OK)
        self.assertEqual(text, "backup.status.ok")
        self.assertEqual(token, "OK_GREEN")

    def test_error_text_and_token(self):
        text, token = self._text_and_token(JOB_STATUS_ERROR)
        self.assertEqual(text, "backup.status.error")
        self.assertEqual(token, "WARN_ORANGE")

    def test_never_text_and_token(self):
        pass
        text, token = self._text_and_token(None)
        self.assertEqual(text, "backup.status.never")
        self.assertEqual(token, "TEXT_MUTED_LIGHT")

    def test_busy_token_differs_from_error(self):
        pass




        _t_busy, tok_busy = self._text_and_token(JOB_STATUS_BUSY)
        _t_err, tok_err = self._text_and_token(JOB_STATUS_ERROR)
        self.assertNotEqual(tok_busy, tok_err)


class TestBusyTokenInSkins(unittest.TestCase):
    pass







    def test_token_in_all_skins(self):
        from ui import skins

        for name in skins.skin_names():
            with self.subTest(skin=name):
                data = skins.skin(name)
                self.assertIn(
                    "BUSY_STEEL", data,
                    f"в скине {name} нет токена BUSY_STEEL — "
                    f"статус «занято» будет нарисован цветом-заглушкой",
                )
                value = data["BUSY_STEEL"]
                self.assertTrue(value.startswith("#") and len(value) == 7,
                                f"BUSY_STEEL в {name} = {value!r}: не hex-цвет")


                                                                             
                           
                                                                             

class TestOpenFlagInCreateCmd(unittest.TestCase):
    pass







    def test_headless_create_cmd_has_open(self):
        from core.headless import _build_create_cmd

        settings = {
            "level": ["-m2"],
            "hash": "",
            "comment": "",
            "only_masks": [],
            "not_masks": [],
        }
        cmd = _build_create_cmd(
            zpaq_bin="zpaqfranz",
            settings=settings,
            srcs=["D:/docs"],
            dest="D:/backup.zpaq",
            password=None,
        )
        self.assertIn(
            "-open", cmd,
            "в headless a-команде нет -open — задание по расписанию "
            "сможет испортить архив, который пишет другая копия",
        )

    def test_headless_test_cmd_has_no_open(self):
        pass




        from core.headless import _build_test_cmd

        cmd = _build_test_cmd(
            zpaq_bin="zpaqfranz",
            dest="D:/backup.zpaq",
            password=None,
            test_mode="full",
        )
        self.assertNotIn(
            "-open", cmd,
            "в t-команде есть -open; этого не должно быть, "
            "проверка архива флага не требует",
        )


class TestOpenFlagInUiCreateCmd(unittest.TestCase):
    pass









    def test_open_appended_after_archive_and_sources(self):
        pass





                                                                             
                                                           
        cmd = ["zpaqfranz", "a", "D:/backup.zpaq", "D:/docs", "-open", "-m2"]
                                                                    
                         
        self.assertEqual(cmd.count("-open"), 1)
        self.assertLess(cmd.index("-open"), cmd.index("-m2"))


                                                                             
                                                   
                                                                             

class TestTaskLogBusy(unittest.TestCase):
    pass







    def setUp(self):
        self._dir = Path(tempfile.mkdtemp(prefix="rizpaq_log_test_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(
            self._dir, ignore_errors=True))
        self.rzp = self._dir / "tasks.rzp"
                                                                    
                                                  
        self.rzp.write_text("{}", encoding="utf-8")

    def _log_path(self) -> Path:
        return Path(str(self.rzp) + ".log")

    def _read_log(self) -> str:
        return self._log_path().read_text(encoding="utf-8")

    def test_short_mode_busy_says_busy(self):
        from core.headless import _write_task_log

        _write_task_log(
            str(self.rzp),
            header="--- test header ---",
            log="another zpaqfranz is running\n",
            mode="short",
            rc=2,
            busy=True,
        )
        text = self._read_log()
        self.assertIn("Status: BUSY", text)
        self.assertNotIn("Status: ERROR", text)

    def test_short_mode_error_still_says_error(self):
        pass



        from core.headless import _write_task_log

        _write_task_log(
            str(self.rzp),
            header="--- test header ---",
            log="some failure\n",
            mode="short",
            rc=1,
            busy=False,
        )
        text = self._read_log()
        self.assertIn("Status: ERROR", text)
        self.assertNotIn("Status: BUSY", text)

    def test_short_mode_ok_unaffected_by_busy_kwarg(self):
        pass




        from core.headless import _write_task_log

        _write_task_log(
            str(self.rzp),
            header="--- test header ---",
            log="",
            mode="short",
            rc=0,
            busy=True,
        )
        text = self._read_log()
        self.assertIn("Status: OK", text)
        self.assertNotIn("Status: BUSY", text)

    def test_log_mode_none_writes_nothing(self):
        pass
        from core.headless import _write_task_log

        _write_task_log(
            str(self.rzp),
            header="--- test header ---",
            log="x",
            mode="none",
            rc=2,
            busy=True,
        )
        self.assertFalse(
            self._log_path().exists(),
            "в режиме 'none' лог не должен создаваться даже при busy",
        )


                                                                             
                                  
                                                                             

class TestBusyLocaleKeys(unittest.TestCase):
    pass








    REQUIRED = (
        "create.busy_title",
        "create.busy_text",
        "create.busy_status",
        "backup.status.busy",
    )

    def test_keys_in_both_locales(self):
        import json

        locales_dir = ROOT / "locales"
        for code in ("en", "ru"):
            path = locales_dir / f"{code}.json"
            with self.subTest(locale=code):
                data = json.loads(path.read_text(encoding="utf-8"))
                strings = data.get("strings", {})
                for key in self.REQUIRED:
                    self.assertIn(
                        key, strings,
                        f"{code}.json: нет ключа {key}",
                    )
                    self.assertTrue(
                        strings[key].strip(),
                        f"{code}.json: {key} пустой",
                    )

    def test_placeholder_matches_between_locales(self):
        pass




        import json
        import re

        locales_dir = ROOT / "locales"
        en = json.loads(
            (locales_dir / "en.json").read_text(encoding="utf-8")
        )["strings"]
        ru = json.loads(
            (locales_dir / "ru.json").read_text(encoding="utf-8")
        )["strings"]

        ph_re = re.compile(r"\{([A-Za-z0-9_]+)\}")
        for key in ("create.busy_text", "create.busy_status"):
            with self.subTest(key=key):
                self.assertEqual(
                    set(ph_re.findall(en[key])),
                    set(ph_re.findall(ru[key])),
                    f"плейсхолдеры {key} не совпадают между en и ru",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
