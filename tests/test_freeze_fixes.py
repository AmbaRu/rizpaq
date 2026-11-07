




























from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.scheduler as sched              
from ui.archive_table import (              
    _CMDLINE_LIMIT,
    _chunk_patterns,
    _extract_for_drag,
)

                                                                   
                                                               
SCHEDULER_DIALOG_SRC = ROOT / "ui" / "scheduler_dialog.py"


class TestChunkPatterns(unittest.TestCase):
    pass

    def test_empty_gives_one_empty_chunk(self):
        self.assertEqual(_chunk_patterns([]), [[]])

    def test_small_list_is_one_chunk(self):
        self.assertEqual(_chunk_patterns(["a", "b", "c"]), [["a", "b", "c"]])

    def test_all_masks_are_preserved(self):
        pats = [f"path/to/file_{i:05d}.txt" for i in range(500)]
        chunks = _chunk_patterns(pats)
        flat = [p for c in chunks for p in c]
        self.assertEqual(flat, pats, "ни одна маска не потеряна и не переставлена")

    def test_huge_list_is_split(self):
        pats = ["x" * 200] * 1000
        chunks = _chunk_patterns(pats)
        self.assertGreater(len(chunks), 1, "список должен быть разбит")

    def test_each_chunk_fits_command_line(self):
        pats = ["y" * 300] * 2000
        for i, chunk in enumerate(_chunk_patterns(pats)):
            size = sum(len(p) + 8 for p in chunk)
            self.assertLessEqual(
                size,
                _CMDLINE_LIMIT,
                f"пачка {i} не помещается в командную строку: {size}",
            )

    def test_no_empty_chunks(self):
        for chunk in _chunk_patterns(["a", "b"] + ["z" * 400] * 100):
            self.assertTrue(chunk, "пустых пачек быть не должно")


class TestExtractForDragBatching(unittest.TestCase):
    pass




    def _run(self, targets, expect_calls=None, **kwargs):
        with mock.patch("ui.archive_table.tempfile.mkdtemp") as mk, \
             mock.patch("ui.archive_table.subprocess.run") as run, \
             mock.patch("ui.archive_table.find_extracted_path") as find:
            import tempfile as real_tempfile

            real_dir = real_tempfile.mkdtemp(prefix="rizpaq_drag_test_")
            mk.return_value = real_dir
            find.side_effect = lambda tmp, inner, want_dir=False: f"{tmp}/found_{inner}"
            run.return_value = mock.Mock(returncode=0, stdout=b"", stderr=b"")
            try:
                                                            
                urls, temp_dir, notes = _extract_for_drag(
                    "zpaq.exe", "C:/a.zpaq", None, targets, **kwargs
                )
            finally:
                import shutil

                shutil.rmtree(real_dir, ignore_errors=True)
            return urls, run.call_count, [
                c.args[0] if c.args else c.kwargs.get("args")
                for c in run.call_args_list
            ], notes

    def test_many_targets_mean_one_call(self):
        targets = [(f"d:/a/f{i}.txt", False) for i in range(120)]
        urls, calls, cmds, _notes = self._run(targets)

        self.assertEqual(
            calls, 1, f"ожидался один вызов движка, было {calls} — возврат к зависанию"
        )
        cmd = cmds[0]
        only_count = cmd.count("-only")
        self.assertEqual(only_count, 120, "в команде должно быть 120 масок")
        self.assertIn("-noeta", cmd)

    def test_single_target_still_one_call(self):
        _, calls, _, _ = self._run([("d:/a/f.txt", False)])
        self.assertEqual(calls, 1)

    def test_directory_target_gets_star_pattern(self):
        targets = [("d:/a/folder", True)]
        _, _, cmds, _ = self._run(targets)
        cmd = cmds[0]
        i = cmd.index("-only")
        self.assertEqual(cmd[i + 1], "d:/a/folder/*")

    def test_password_is_passed(self):
        targets = [("d:/a/f.txt", False)]
        with mock.patch("ui.archive_table.tempfile.mkdtemp") as mk, \
             mock.patch("ui.archive_table.subprocess.run") as run, \
             mock.patch("ui.archive_table.find_extracted_path") as find:
            import shutil
            import tempfile as real_tempfile

            real_dir = real_tempfile.mkdtemp(prefix="rizpaq_drag_test_")
            mk.return_value = real_dir
            find.return_value = real_dir
            run.return_value = mock.Mock(returncode=0)
            try:
                _extract_for_drag("zpaq.exe", "C:/a.zpaq", "s3cret", targets)
            finally:
                shutil.rmtree(real_dir, ignore_errors=True)

        cmd = run.call_args_list[0].args[0]
        i = cmd.index("-key")
        self.assertEqual(cmd[i + 1], "s3cret")

    def test_timeout_is_passed_to_subprocess(self):
        _, _, cmds, _ = self._run([("d:/a/f.txt", False)])
        self.assertTrue(cmds, "движок вообще не вызван")

    def test_every_call_receives_a_timeout(self):
        pass
        import shutil
        import tempfile as real_tempfile

        with mock.patch("ui.archive_table.tempfile.mkdtemp") as mk, \
             mock.patch("ui.archive_table.subprocess.run") as run, \
             mock.patch("ui.archive_table.find_extracted_path") as find:
            real_dir = real_tempfile.mkdtemp(prefix="rizpaq_drag_test_")
            mk.return_value = real_dir
            find.return_value = real_dir
            run.return_value = mock.Mock(returncode=0)
            try:
                _extract_for_drag("zpaq.exe", "C:/a.zpaq", None,
                                  [(f"d:/a/f{i}.txt", False) for i in range(120)])
            finally:
                shutil.rmtree(real_dir, ignore_errors=True)

        for call in run.call_args_list:
            self.assertIsNotNone(
                call.kwargs.get("timeout"),
                "у вызова движка нет таймаута — зависший движок заблокирует UI",
            )
            self.assertLessEqual(call.kwargs["timeout"], 120)

    def test_timeout_exhausted_stops_early(self):
        pass
        urls, calls, _, notes = self._run(
            [(f"d:/a/f{i}.txt", False) for i in range(50)], timeout=-1
        )
        self.assertEqual(calls, 0, "при исчерпанном таймауте движок звать нельзя")

    def test_timeout_expired_breaks_loop(self):
        pass
        import shutil
        import tempfile as real_tempfile

        with mock.patch("ui.archive_table.tempfile.mkdtemp") as mk, \
             mock.patch("ui.archive_table.subprocess.run") as run, \
             mock.patch("ui.archive_table.find_extracted_path") as find, \
             mock.patch("ui.archive_table.time.monotonic") as mono:
            real_dir = real_tempfile.mkdtemp(prefix="rizpaq_drag_test_")
            mk.return_value = real_dir
            find.return_value = None
            run.return_value = mock.Mock(returncode=0)
                                                       
            mono.side_effect = [0.0, 0.0, 100.0, 100.0]
            try:
                _extract_for_drag(
                    "zpaq.exe", "C:/a.zpaq", None,
                    [(f"d:/a/f{i}.txt", False) for i in range(4000)],
                    timeout=10,
                )
            finally:
                shutil.rmtree(real_dir, ignore_errors=True)

        self.assertLessEqual(
            run.call_count, 9, "после исчерпания таймаута вызовы должны прекратиться"
        )

    def test_no_arguments_returns_nothing(self):
        urls, temp_dir, notes = _extract_for_drag(None, None, None,
                                                   [("a", False)])
        self.assertEqual(urls, [])
        self.assertIsNone(temp_dir)
        self.assertIsNotNone(notes, "сведения о ходе возвращаются всегда")

    def test_exhausted_timeout_is_reported(self):
        pass







        _urls, calls, _, notes = self._run(
            [(f"d:/a/f{i}.txt", False) for i in range(50)], timeout=-1
        )
        self.assertEqual(calls, 0, "при исчерпанном таймауте движок звать нельзя")
        self.assertTrue(
            notes["timed_out"],
            "прерывание по времени не помечено — вызывающий не сможет "
            "объяснить пользователю, что произошло")

    def test_timeout_reported_in_notes(self):
        pass






        _urls, _calls, _, notes = self._run([("d:/a/f.txt", False)],
                                            timeout=42)
        self.assertEqual(notes["timeout"], 42,
                         "в notes попал не тот предел, который применялся")

    def test_no_timeout_means_no_preemption(self):
        _urls, _calls, _, notes = self._run([("d:/a/f.txt", False)])
        self.assertFalse(notes["timed_out"],
                         "успешный перенос помечен как прерванный")

    def test_pump_called_between_chunks(self):
        pass






        calls = []
                                                                          
                                     
        targets = [("d:/a/" + "x" * 300 + f"/f{i}.txt", False)
                   for i in range(300)]
        _urls, _c, _cmds, notes = self._run(targets,
                                            pump=lambda: calls.append(1))
        self.assertGreater(notes["chunks"], 1,
                           "нужно несколько пачек, иначе проверка ни о чём")
        self.assertTrue(calls, "оживление окна между пачками не вызывалось")

    def test_pump_failure_does_not_break_drag(self):
        pass





        def bad_pump():
            raise RuntimeError("виджет удалён")

        urls, calls, _cmds, notes = self._run([("d:/a/f.txt", False)],
                                              pump=bad_pump)
        self.assertEqual(calls, 1)
        self.assertTrue(urls, "перенос сломался из-за сбоя оживления")
        self.assertFalse(notes["timed_out"])


                                                                   
                                                                       
                                                          
_WORK = {"id": "w-test", "title": "Work"}
_JOB = {"id": "j-test", "title": "Job"}
_SCHEDULE = {"enabled": True, "frequency": "daily", "time": "10:00"}


class TestSchedulerTimeouts(unittest.TestCase):
    pass








    def test_helper_passes_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=b"")
            sched._run_schtasks(["schtasks.exe", "/query"])

        self.assertIsNotNone(
            run.call_args.kwargs.get("timeout"),
            "у вызова schtasks нет таймаута",
        )
        self.assertEqual(run.call_args.kwargs["timeout"], sched.SCHTASKS_TIMEOUT)

    def test_helper_does_not_use_text_mode(self):
        pass



        with mock.patch("core.scheduler.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=b"")
            sched._run_schtasks(["schtasks.exe", "/query"])

        self.assertNotIn("text", run.call_args.kwargs)

    def test_helper_returns_none_on_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
            self.assertIsNone(sched._run_schtasks(["schtasks.exe"]))

    def test_list_tasks_survives_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
            self.assertEqual(sched.list_rizpaq_tasks(), [])

    def test_is_task_scheduled_survives_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
            self.assertFalse(sched.is_task_scheduled(_WORK, _JOB))

    def test_create_task_survives_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
                                                               
                                                                     
                                                                  
                                                  
            self.assertFalse(
                sched.create_scheduled_task(
                    "C:/x.rzp", _WORK, _JOB, _SCHEDULE
                )
            )

    def test_create_task_disabled_schedule_removes(self):
        pass






        with mock.patch("core.scheduler.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0)
            sched.create_scheduled_task(
                "C:/x.rzp", _WORK, _JOB, {"enabled": False}
            )
                                                          
        cmd = run.call_args.args[0]
        self.assertIn("/delete", cmd)

    def test_remove_task_survives_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
            self.assertFalse(sched.remove_scheduled_task(_WORK, _JOB))

    def test_remove_by_name_survives_timeout(self):
        with mock.patch("core.scheduler.subprocess.run") as run:
            run.side_effect = subprocess.TimeoutExpired(cmd="schtasks", timeout=20)
            self.assertFalse(sched.remove_scheduled_task_by_name("Rizpaq_x_1234"))

    def test_all_schtasks_calls_go_through_helper(self):
        pass




        src = Path(sched.__file__).read_text(encoding="utf-8")
        self.assertEqual(
            src.count("subprocess.run("),
            1,
            "прямых вызовов subprocess.run должно быть ровно один — в хелпере",
        )
                                                             
        helper = src.split("def _run_schtasks")[1].split("def _schtasks_bin")[0]
        self.assertIn("subprocess.run(", helper)


class TestSchedulerDialogDoesNotBlockConstructor(unittest.TestCase):
    pass

    def test_load_is_deferred(self):
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
                                                                  
                                                                     
        src = SCHEDULER_DIALOG_SRC.read_text(encoding="utf-8")

        init = src.split("def _load_tasks")[0]
        self.assertIn(
            "QTimer.singleShot(0, self._load_tasks)",
            init,
            "загрузка задач должна откладываться, а не идти из конструктора",
        )
        self.assertNotIn(
            "\n        self._load_tasks()\n",
            init,
            "прямой вызов _load_tasks() из конструктора остался",
        )

    def test_list_runs_off_gui_thread(self):
        pass







        src = SCHEDULER_DIALOG_SRC.read_text(encoding="utf-8")
        load = src.split("def _load_tasks")[1].split("    def ")[0]
        self.assertIn("_TaskListWorker", load,
                      "список задач не уходит в поток")
        self.assertNotIn("tasks = list_rizpaq_tasks()", load,
                         "список всё ещё читается на GUI-потоке")

    def test_dialog_uses_core_removal(self):
        pass
        src = SCHEDULER_DIALOG_SRC.read_text(encoding="utf-8")
        self.assertNotIn(
            "import subprocess",
            src,
            "диалог не должен вызывать schtasks сам — это делает core.scheduler",
        )
        self.assertIn("remove_scheduled_task_by_name", src)


if __name__ == "__main__":
    unittest.main()
