



















from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import par2_ops              

                                                                    
                                                                   
                                                                    
                                                         
from PySide6.QtWidgets import QApplication              

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))

from core.par2_ops import (              
    STATE_BROKEN,
    STATE_DAMAGED,
    STATE_FAILED,
    STATE_MISSING,
    STATE_OK,
    STATE_UNREPAIRABLE,
    Par2Result,
    classify_verify_log,
    cleanup_orphans,
    create_parset,
    find_par2,
    needs_subst,
    par2_main_name,
    par2_set_files,
    par2_temp_set_name,
    read_recorded_size,
    refresh_par2_set,
    remove_par2_set,
    repair_parset,
    set_is_stale,
    verify_parset,
)

                                                                
                                                        
_temp_set_files = par2_ops._temp_set_files

PAR2_BIN = find_par2()
HAVE_PAR2 = bool(PAR2_BIN) and os.path.isfile(PAR2_BIN)

requires_par2 = unittest.skipUnless(
    HAVE_PAR2, "par2.exe не найден — тесты на живом движке пропущены"
)


class _TempCase(unittest.TestCase):
    pass

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="par2_ops_test_"))
        self.arch = self.base / "backup.zpaq"
        self.arch.write_bytes(b"A" * 30000)
                                                                         
                                                                         
                                                                        
                                  
        self.fake_bin = self.base / "par2.exe"
        self.fake_bin.write_bytes(b"not a real binary")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def damage(self, count=9000, step=300):
        pass
        data = bytearray(self.arch.read_bytes())
        for off in range(0, count, step):
            data[off] ^= 0xFF
        self.arch.write_bytes(bytes(data))

    def _make_temp_set(self):
        pass
        tmp = Path(par2_temp_set_name(str(self.arch)))
        tmp.write_bytes(b"x")
        vol = self.base / tmp.name.replace(".par2", ".vol00+01.par2")
        vol.write_bytes(b"x")


                                                                     
                                            
                                                                     

class TestSetNaming(unittest.TestCase):
    pass




    def test_main_name_appends_not_replaces(self):
        pass
        self.assertEqual(
            par2_main_name(r"D:\backup.zpaq"), r"D:\backup.zpaq.par2"
        )
        self.assertEqual(
            par2_main_name(r"D:\отчёт.v2.zpaq"), r"D:\отчёт.v2.zpaq.par2"
        )

    def test_main_name_of_replacement_would_be_wrong(self):
        pass



        naive = r"D:\backup.par2"
        self.assertNotEqual(naive, par2_main_name(r"D:\backup.zpaq"))

    def test_main_name_keeps_subfolders(self):
        p = r"D:\a\b\c\backup.zpaq"
        self.assertEqual(par2_main_name(p), p + ".par2")


class TestSetFileListing(_TempCase):
    pass

    def test_empty_when_nothing_created(self):
        self.assertEqual(par2_set_files(str(self.arch)), [])

    def test_finds_main_and_volumes(self):
        main = Path(par2_main_name(str(self.arch)))
        main.write_bytes(b"x")
        (self.base / "backup.zpaq.vol00+01.par2").write_bytes(b"x")
        (self.base / "backup.zpaq.vol127+35.par2").write_bytes(b"x")
                                   
        (self.base / "чужой.par2").write_bytes(b"x")

        found = [Path(p).name for p in par2_set_files(str(self.arch))]
        self.assertIn("backup.zpaq.par2", found)
        self.assertIn("backup.zpaq.vol00+01.par2", found)
        self.assertIn("backup.zpaq.vol127+35.par2", found)
        self.assertNotIn("чужой.par2", found)

    def test_remove_returns_deleted_and_leaves_nothing(self):
        Path(par2_main_name(str(self.arch))).write_bytes(b"x")
        (self.base / "backup.zpaq.vol00+01.par2").write_bytes(b"x")

        removed = remove_par2_set(str(self.arch))
        self.assertEqual(len(removed), 2)
        self.assertEqual(par2_set_files(str(self.arch)), [])

    def test_remove_survives_missing_file(self):
        pass
        self.assertEqual(remove_par2_set(str(self.base / "нет.zpaq")), [])


                                                                     
                                             
                                                                     

class TestRecordedSize(unittest.TestCase):
    pass




    def test_plain_number(self):
        log = "The total size of the data files is 66000 bytes."
        self.assertEqual(read_recorded_size(log), 66000)

    def test_thousands_separator(self):
        pass
        log = "The total size of the data files is 1,234,567 bytes."
        self.assertEqual(read_recorded_size(log), 1234567)

    def test_case_insensitive(self):
        log = "THE TOTAL SIZE OF THE DATA FILES IS 500 BYTES"
        self.assertEqual(read_recorded_size(log), 500)

    def test_absent_line_returns_none(self):
        pass
        self.assertIsNone(read_recorded_size("Main packet not found."))
        self.assertIsNone(read_recorded_size(""))

    def test_zero_is_valid_value(self):
        log = "The total size of the data files is 0 bytes."
        self.assertEqual(read_recorded_size(log), 0)


class TestStaleness(unittest.TestCase):
    pass




    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="par2_stale_"))
        self.f = self.base / "a.zpaq"

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_grown_file_is_stale(self):
        self.f.write_bytes(b"x" * 1000)
        self.assertTrue(set_is_stale(str(self.f), 500))

    def test_same_size_is_fresh(self):
        self.f.write_bytes(b"x" * 1000)
        self.assertFalse(set_is_stale(str(self.f), 1000))

    def test_unknown_size_is_unknown(self):
        pass
        self.f.write_bytes(b"x" * 1000)
        self.assertIsNone(set_is_stale(str(self.f), None))

    def test_missing_file_is_unknown(self):
        self.assertIsNone(set_is_stale(str(self.base / "нет.zpaq"), 100))


class TestSubstDecision(unittest.TestCase):
    pass




    def test_short_path_needs_nothing(self):
        self.assertFalse(needs_subst(r"C:\Архивы"))

    def test_long_path_needs_letter(self):
        pass



        deep = "C:\\" + "\\".join(["Папка_с_длинным_именем_XX"] * 10)
        probe = os.path.join(
            deep, "Папка_с_длинным_именем_XX" + ".zpaq.vol127+35.par2"
        )
        self.assertGreater(len(probe), 240)
        self.assertTrue(needs_subst(deep))


                                                                     
                      
                                                                     

class TestResultStates(unittest.TestCase):
    pass





    def test_damaged_flag(self):
        self.assertTrue(Par2Result(False, STATE_DAMAGED).damaged)
        self.assertFalse(Par2Result(True, STATE_OK).damaged)
        self.assertFalse(Par2Result(False, STATE_MISSING).damaged)

    def test_has_set(self):
        self.assertTrue(Par2Result(True, STATE_OK).has_set)
        self.assertTrue(Par2Result(False, STATE_DAMAGED).has_set)
        self.assertFalse(Par2Result(False, STATE_MISSING).has_set)
        self.assertFalse(Par2Result(False, STATE_BROKEN).has_set)


class TestUnrepairableIsSeparate(unittest.TestCase):
    pass












    def test_damaged_but_not_repairable(self):
        self.assertTrue(Par2Result(False, STATE_UNREPAIRABLE).damaged)
        self.assertFalse(Par2Result(False, STATE_UNREPAIRABLE).repairable)

    def test_repairable_flag(self):
        self.assertTrue(Par2Result(False, STATE_DAMAGED).repairable)
        self.assertFalse(Par2Result(False, STATE_OK).repairable)

    def test_not_missing(self):
        pass
        r = Par2Result(False, STATE_UNREPAIRABLE)
        self.assertNotEqual(r.state, STATE_MISSING)
        self.assertTrue(r.has_set, "набор-то на месте")

    def test_has_set_includes_it(self):
        self.assertTrue(Par2Result(False, STATE_UNREPAIRABLE).has_set)


                                                                     

class TestClassifyVerifyLog(unittest.TestCase):
    pass













                                   
    LOG_OK = (
        'Loading "backup.zpaq.par2".\n'
        'There are 1 recoverable files and 0 other files.\n'
        'The block size used was 4096 bytes.\n'
        'There are a total of 488 data blocks.\n'
        'The total size of the data files is 2,004,054 bytes.\n'
        '\n'
        'Verifying source files:\n'
        'Target: "backup.zpaq" - found.\n'
        '\n'
        'All files are correct, repair is not required.\n'
    )

                                       
    LOG_DAMAGED = (
        'There are 1 recoverable files and 0 other files.\n'
        'The total size of the data files is 2,004,054 bytes.\n'
        '\n'
        'Verifying source files:\n'
        'Target: "backup.zpaq" - damaged. Found 1994 of 1997 data blocks.\n'
        '\n'
        'Repair is required.\n'
        '1 file(s) exist but are damaged.\n'
        'You have 567 recovery blocks available.\n'
        'Repair is possible.\n'
        'You have an excess of 564 recovery blocks.\n'
    )

                                                                    
    LOG_UNREPAIRABLE = (
        'There are 1 recoverable files and 0 other files.\n'
        'The total size of the data files is 2,004,054 bytes.\n'
        '\n'
        'Verifying source files:\n'
        'Target: "backup.zpaq" - damaged. Found 1598 of 1997 data blocks.\n'
        '\n'
        'Repair is required.\n'
        '1 file(s) exist but are damaged.\n'
        'You have 20 recovery blocks available.\n'
        'Repair is not possible.\n'
        'You need 379 more recovery blocks to be able to repair.\n'
    )

                                                                
    LOG_TARGET_MISSING = (
        'There are 1 recoverable files and 0 other files.\n'
        'The total size of the data files is 2,004,054 bytes.\n'
        '\n'
        'Verifying source files:\n'
        'Target: "backup.zpaq" - missing.\n'
        '\n'
        'Repair is required.\n'
        '1 file(s) are missing.\n'
        'Repair is not possible.\n'
    )

    def test_intact_is_ok(self):
        self.assertEqual(
            classify_verify_log(self.LOG_OK), STATE_OK
        )

    def test_damaged_repairable(self):
        self.assertEqual(
            classify_verify_log(self.LOG_DAMAGED), STATE_DAMAGED
        )

    def test_damaged_unrepairable(self):
        pass
        self.assertEqual(
            classify_verify_log(self.LOG_UNREPAIRABLE), STATE_UNREPAIRABLE
        )

    def test_target_missing_is_missing(self):
        self.assertEqual(
            classify_verify_log(self.LOG_TARGET_MISSING), STATE_MISSING
        )

    def test_same_code_two_states(self):
        pass





        v = verify_parset                                        
        from core.par2_ops import _classify_verify

        a = _classify_verify(2, self.LOG_UNREPAIRABLE)
        b = _classify_verify(2, self.LOG_TARGET_MISSING)
        self.assertEqual(a.state, STATE_UNREPAIRABLE)
        self.assertEqual(b.state, STATE_MISSING)
        self.assertNotEqual(a.state, b.state)

    def test_empty_log_returns_none(self):
        pass





        self.assertIsNone(classify_verify_log(""))
        self.assertIsNone(classify_verify_log("что-то совсем другое\n"))

    def test_fallback_uses_code_when_log_unknown(self):
        from core.par2_ops import _classify_verify

                                           
        self.assertEqual(
            _classify_verify(3, "мусор").state, STATE_MISSING
        )
        self.assertEqual(
            _classify_verify(1, "мусор").state, STATE_DAMAGED
        )
                                                                     
                                               
        self.assertEqual(
            _classify_verify(2, "мусор").state, STATE_UNREPAIRABLE
        )

    def test_recorded_size_read_from_log(self):
        pass
        from core.par2_ops import _classify_verify

        r = _classify_verify(2, self.LOG_UNREPAIRABLE)
        self.assertEqual(r.recorded_size, 2004054)


class TestVerifyCallContract(unittest.TestCase):
    pass






















    def test_verify_parset_accepts_register(self):
        import inspect

        sig = inspect.signature(par2_ops.verify_parset)
                                      
        sig.bind("par2.exe", "a.par2", register=lambda proc: None)

    def test_verify_parset_timeout_still_positional_ok(self):
        pass
        import inspect

        sig = inspect.signature(par2_ops.verify_parset)
        sig.bind("par2.exe", "a.par2", 3600)

    def test_repair_parset_accepts_register(self):
        pass
        import inspect

        sig = inspect.signature(par2_ops.repair_parset)
        sig.bind("par2.exe", "a.par2", register=lambda proc: None)

    def test_refresh_parset_accepts_register(self):
        import inspect

        sig = inspect.signature(par2_ops.refresh_par2_set)
        sig.bind("par2.exe", "a.zpaq", register=lambda proc: None)

    def test_worker_passes_only_accepted_arguments(self):
        pass





        import ast

        known = {
            "verify_parset": set(par2_ops.verify_parset.__code__.co_varnames),
            "repair_parset": set(par2_ops.repair_parset.__code__.co_varnames),
            "refresh_par2_set": set(
                par2_ops.refresh_par2_set.__code__.co_varnames
            ),
        }

        src = (ROOT / "workers" / "par2_worker.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(src)

        problems = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = None
            if isinstance(fn, ast.Attribute) and isinstance(
                fn.value, ast.Name
            ):
                name = fn.value.id + "." + fn.attr
            if name is None or not name.startswith("par2_ops."):
                continue
            fname = name.split(".", 1)[1]
            if fname not in known:
                continue
            for kw in node.keywords:
                if kw.arg and kw.arg not in known[fname]:
                    problems.append(
                        f"{fname}: параметр '{kw.arg}' не принимается"
                    )
        self.assertEqual(problems, [], "\n".join(problems))


@requires_par2
class TestVerifyWorkerLive(_TempCase):
    pass






    def _run_worker(self):
        from workers.par2_worker import Par2VerifyWorker

        got = {}
                                                                       
                                                                  
                                                                  
                      
        worker = Par2VerifyWorker(PAR2_BIN, str(self.arch))
        worker.done.connect(lambda r: got.update(r))
        worker.start()
        worker.wait(300000)
                                                                          
                                                               
        deadline = time.monotonic() + 30
        while not got and time.monotonic() < deadline:
            QApplication.processEvents()
            time.sleep(0.02)
        QApplication.processEvents()
        return got

    def test_worker_builds_set_name_itself(self):
        pass







        create_parset(PAR2_BIN, str(self.arch))
        got = self._run_worker()
        self.assertEqual(got.get("par2_path"),
                         par2_main_name(str(self.arch)))

    def test_intact_archive(self):
        create_parset(PAR2_BIN, str(self.arch))
        got = self._run_worker()
        self.assertTrue(got, "воркер проверки не эмитил результат")
        self.assertEqual(got.get("state"), STATE_OK, got.get("log"))

    def test_damaged_archive(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()
        got = self._run_worker()
        self.assertTrue(got, "воркер проверки не эмитил результат")
        self.assertIn(got.get("state"), (STATE_DAMAGED, STATE_UNREPAIRABLE),
                      got.get("log"))

    def test_no_error_in_log(self):
        pass






        create_parset(PAR2_BIN, str(self.arch))
        got = self._run_worker()
        log = got.get("log") or ""
        self.assertNotIn("TypeError", log)
        self.assertNotIn("unexpected keyword argument", log)


class TestGuardsWithoutBinary(_TempCase):
    pass








    def test_missing_binary_wins_over_missing_set(self):
        r = verify_parset(str(self.base / "нет-бинарника.exe"),
                          str(self.base / "нет-набора.par2"))
        self.assertEqual(r.state, STATE_FAILED)

    def test_verify_without_set(self):
        pass
        r = verify_parset(str(self.fake_bin),
                          str(self.base / "нет-такого.par2"))
        self.assertEqual(r.state, STATE_MISSING)
        self.assertFalse(r.damaged)
        self.assertFalse(r.has_set)

    def test_repair_without_set(self):
        r = repair_parset(str(self.fake_bin),
                          str(self.base / "нет-такого.par2"),
                          archive_path=str(self.arch),
                          recorded_size=30000)
        self.assertEqual(r.state, STATE_MISSING)

    def test_create_without_binary(self):
        r = create_parset(str(self.base / "нет-бинарника.exe"), str(self.arch))
        self.assertFalse(r.ok)
        self.assertEqual(r.state, STATE_FAILED)


class TestRepairRefusesWithoutGuard(_TempCase):
    pass




    @requires_par2
    def test_refuses_without_recorded_size(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()

        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=str(self.arch), recorded_size=None,
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.state, STATE_FAILED)
                                                                   
        self.assertNotEqual(self.arch.read_bytes(), b"A" * 30000)

    @requires_par2
    def test_refuses_without_archive_path(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()

        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=None, recorded_size=30000,
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.state, STATE_FAILED)


                                                                     
              
                                                                     

@requires_par2
class TestLiveEngine(_TempCase):
    pass




    def test_create_makes_full_set(self):
        r = create_parset(PAR2_BIN, str(self.arch))
        self.assertTrue(r.ok, r.log)

        files = par2_set_files(str(self.arch))
                                                                     
                                              
        self.assertGreaterEqual(len(files), 2)
        self.assertTrue(Path(par2_main_name(str(self.arch))).is_file())

    def test_verify_healthy_archive(self):
        create_parset(PAR2_BIN, str(self.arch))
        r = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(r.state, STATE_OK, r.log)
        self.assertEqual(r.recorded_size, 30000)

    def test_verify_damaged_archive(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()
        r = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(r.state, STATE_DAMAGED, r.log)
        self.assertTrue(r.damaged)
        self.assertTrue(r.has_set)

    def test_verify_garbage_set_is_broken_not_damaged(self):
        pass
        bad = self.base / "broken.par2"
        bad.write_bytes(b"PAR2\x00\x00" + "совсем-не-набор".encode("utf-8"))
        r = verify_parset(PAR2_BIN, str(bad))
        self.assertIn(r.state, (STATE_BROKEN, STATE_MISSING, STATE_FAILED))
        self.assertFalse(r.damaged)

    def test_repair_restores_content(self):
        create_parset(PAR2_BIN, str(self.arch))
        self.damage()
        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=str(self.arch), recorded_size=30000,
        )
        self.assertTrue(r.ok, r.log)
        self.assertEqual(self.arch.read_bytes(), b"A" * 30000)

    def test_rollback_is_refused_and_file_kept(self):
        pass







        create_parset(PAR2_BIN, str(self.arch))
        expected = b"A" * 30000

        self.arch.write_bytes(expected + b"B" * 30000)
        self.assertEqual(self.arch.stat().st_size, 60000)

        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertTrue(set_is_stale(str(self.arch), v.recorded_size))

        r = repair_parset(
            PAR2_BIN, par2_main_name(str(self.arch)),
            archive_path=str(self.arch), recorded_size=v.recorded_size,
        )

        self.assertFalse(r.ok, "восстановление по устаревшему набору "
                               "не должно было выполниться")
        self.assertEqual(r.state, STATE_FAILED)
                                                      
        self.assertEqual(self.arch.stat().st_size, 60000)
        self.assertEqual(self.arch.read_bytes(), expected + b"B" * 30000)

    def test_create_refuses_when_set_already_exists(self):
        pass



        self.assertTrue(create_parset(PAR2_BIN, str(self.arch)).ok)
        second = create_parset(PAR2_BIN, str(self.arch))
        self.assertFalse(second.ok)

    def test_create_with_temp_name_coexists(self):
        pass



        self.assertTrue(create_parset(PAR2_BIN, str(self.arch)).ok)
        old_files = par2_set_files(str(self.arch))

        tmp_name = str(self.base / "backup.zpaq.new")
        fresh = create_parset(PAR2_BIN, str(self.arch), set_name=tmp_name)
        self.assertTrue(fresh.ok, fresh.log)

                                                 
        all_files = par2_set_files(str(self.arch))
        for f in old_files:
            self.assertIn(f, all_files)

                                                                     
        for f in old_files:
            os.remove(f)
        for p in self.base.glob("backup.zpaq.new*"):
            p.rename(p.with_name(p.name.replace(".new", "")))

        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(v.state, STATE_OK, v.log)


class TestZeroOptionsNotPassed(_TempCase):
    pass




    def _args(self, **kwargs):
        with mock.patch.object(par2_ops, "_run",
                               return_value=(0, "ok")) as m:
            create_parset(str(self.fake_bin), str(self.arch), **kwargs)
        return m.call_args[0][1]

    def test_threads_zero_not_passed(self):
        self.assertNotIn("-t0", self._args(threads=0))

    def test_threads_positive_passed(self):
        self.assertIn("-t4", self._args(threads=4))

    def test_redundancy_clamped_to_valid(self):
        self.assertIn("-r1", self._args(redundancy=0))

    def test_memory_zero_not_passed(self):
        args = self._args(memory_mb=0)
        self.assertFalse([a for a in args if str(a).startswith("-m")])


class TestOrphanCleanup(_TempCase):
    pass




    def test_nothing_to_clean_initially(self):
        self.assertEqual(cleanup_orphans(str(self.arch)), [])

    def test_removes_temp_set_only(self):
        self._make_temp_set()
        real = Path(par2_main_name(str(self.arch)))
        real.write_bytes(b"x")

        removed = cleanup_orphans(str(self.arch))

        self.assertEqual(len(removed), 2)
                                                                     
                                          
        self.assertTrue(real.exists(), "настоящий набор нельзя трогать")
        self.assertEqual(cleanup_orphans(str(self.arch)), [])

    def test_temp_name_does_not_collide_with_real(self):
        self.assertNotEqual(
            par2_temp_set_name(str(self.arch)),
            par2_main_name(str(self.arch)),
        )


@requires_par2
class TestRefreshSet(_TempCase):
    pass





    def test_creates_set_on_first_run(self):
        r = refresh_par2_set(PAR2_BIN, str(self.arch))
        self.assertTrue(r.ok, r.log)
        self.assertEqual(r.recorded_size, 30000)
        self.assertTrue(Path(par2_main_name(str(self.arch))).is_file())

    def test_second_run_replaces_set(self):
        pass
        self.assertTrue(refresh_par2_set(PAR2_BIN, str(self.arch)).ok)
        r = refresh_par2_set(PAR2_BIN, str(self.arch))
        self.assertTrue(r.ok, r.log)

                                                              
        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(v.state, STATE_OK, v.log)

    def test_no_temp_files_left_after_success(self):
        refresh_par2_set(PAR2_BIN, str(self.arch))
        refresh_par2_set(PAR2_BIN, str(self.arch))
        self.assertEqual(_temp_set_files(str(self.arch)), [])

    def test_unchanged_archive_skips_work(self):
        pass


        self.assertTrue(refresh_par2_set(PAR2_BIN, str(self.arch)).ok)

        marker = Path(par2_main_name(str(self.arch)))
        mtime_before = marker.stat().st_mtime_ns

        r = refresh_par2_set(
            PAR2_BIN, str(self.arch), unchanged_size=30000
        )
        self.assertTrue(r.ok, r.log)
        self.assertIn("не изменился", r.log)
        self.assertEqual(marker.stat().st_mtime_ns, mtime_before,
                         "набор не должен пересоздаваться")

    def test_changed_archive_is_recreated(self):
        pass
        refresh_par2_set(PAR2_BIN, str(self.arch))
        self.arch.write_bytes(b"A" * 30000 + b"B" * 10000)

        r = refresh_par2_set(PAR2_BIN, str(self.arch), unchanged_size=30000)
        self.assertTrue(r.ok, r.log)
        self.assertEqual(r.recorded_size, 40000)

        v = verify_parset(PAR2_BIN, par2_main_name(str(self.arch)))
        self.assertEqual(v.state, STATE_OK, v.log)

    def test_race_during_creation_discards_new_set(self):
        pass






        self.assertTrue(refresh_par2_set(PAR2_BIN, str(self.arch)).ok)
        old_marker = Path(par2_main_name(str(self.arch)))
        old_size = old_marker.stat().st_size

        real_getsize = os.path.getsize

        def grows_on_second_call(path):
            pass
            size = real_getsize(path)
            if str(path) == str(self.arch):
                counter["n"] += 1
                if counter["n"] == 2:
                    return size + 5000
            return size

        counter = {"n": 0}
        with mock.patch.object(
            par2_ops.os.path, "getsize", side_effect=grows_on_second_call
        ):
            r = refresh_par2_set(PAR2_BIN, str(self.arch))

        self.assertFalse(r.ok)
        self.assertIn("изменился", r.log)
                                            
        self.assertEqual(_temp_set_files(str(self.arch)), [])
        self.assertTrue(old_marker.is_file())
        self.assertEqual(old_marker.stat().st_size, old_size)

    def test_failed_creation_keeps_old_set(self):
        pass



        self.assertTrue(refresh_par2_set(PAR2_BIN, str(self.arch)).ok)
        before = sorted(Path(p).name for p in par2_set_files(str(self.arch)))

        with mock.patch.object(
            par2_ops, "create_parset",
            return_value=Par2Result(False, STATE_FAILED, "сбой"),
        ):
            r = refresh_par2_set(PAR2_BIN, str(self.arch))

        self.assertFalse(r.ok)
        after = sorted(Path(p).name for p in par2_set_files(str(self.arch)))
        self.assertEqual(before, after)

    def test_orphans_removed_before_new_creation(self):
        pass
        self._make_temp_set()
        r = refresh_par2_set(PAR2_BIN, str(self.arch))
        self.assertTrue(r.ok, r.log)
        self.assertEqual(_temp_set_files(str(self.arch)), [])


def test_failed_creation_removes_partial_temp_set(self):
        pass




        self._make_temp_set()
        with mock.patch.object(
            par2_ops, "create_parset",
            return_value=Par2Result(False, STATE_FAILED, "прервано"),
        ):
            r = refresh_par2_set(PAR2_BIN, str(self.arch))

        self.assertFalse(r.ok)
        self.assertEqual(
            _temp_set_files(str(self.arch)), [],
            "недописанный временный набор должен быть убран",
        )


if __name__ == "__main__":
    unittest.main()
