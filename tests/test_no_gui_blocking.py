from __future__ import annotations

import re
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SCHED = (ROOT / "ui" / "scheduler_dialog.py").read_text(encoding="utf-8")
TABLE = (ROOT / "ui" / "archive_table.py").read_text(encoding="utf-8")


def method_body(src: str, name: str) -> str:

    start = src.index(f"def {name}(")
    rest = src[start + 1:]
    nxt = re.search(r"\n    def ", rest)
    return rest[: nxt.start()] if nxt else rest


class TestSchedulerOffGuiThread(unittest.TestCase):


    def test_list_runs_in_thread(self):
        body = method_body(SCHED, "_load_tasks")
        self.assertNotIn(
            "tasks = list_rizpaq_tasks()", body,
            "список задач всё ещё читается прямо в обработчике GUI-потока")
        self.assertIn("_TaskListWorker", body,
                      "список задач не уходит в поток")

    def test_list_worker_exists(self):
        self.assertIn("class _TaskListWorker(QThread)", SCHED)
        self.assertIn("list_rizpaq_tasks", SCHED)

    def test_remove_runs_in_thread(self):
        body = method_body(SCHED, "_remove_selected")
        self.assertNotIn(
            "if remove_scheduled_task_by_name(", body,
            "удаление задачи всё ещё выполняется на GUI-потоке")
        self.assertIn("_TaskRemoveWorker", body)

    def test_remove_blocked_while_working(self):
        body = method_body(SCHED, "_remove_selected")


        self.assertIn(
            'if getattr(self, "_remove_worker", None) is not None:',
            body,
            "повторный клик по удалению не блокируется: нет защитного выхода")

    def test_queued_connection(self):
        self.assertIn("Qt.QueuedConnection", SCHED)

    def test_closed_dialog_is_safe(self):
        for name in ("_apply_tasks", "_apply_remove"):
            body = method_body(SCHED, name)
            self.assertIn(
                "isVisible()", body,
                f"{name}: результат применяется и к закрытому окну")

    def test_button_reenabled_after_work(self):
        for name in ("_on_list_finished", "_on_remove_finished"):
            body = method_body(SCHED, name)
            self.assertIn("setEnabled(True)", body,
                          f"{name}: кнопка не возвращается в рабочее")


class TestDragNoSilentCancel(unittest.TestCase):


    def test_notes_reported(self):
        body = method_body(TABLE, "_extract_for_drag")
        self.assertIn('"timed_out"', body,
                      "прерванный перенос не помечается")
        self.assertIn("notes", body, "сведения о ходе не возвращаются")

    def test_timeout_sets_flag_before_break(self):
        body = method_body(TABLE, "_extract_for_drag")
        for pattern in ("except subprocess.TimeoutExpired",
                        "if left <= 0"):
            idx = body.index(pattern)
            tail = body[idx:idx + 700]
            self.assertIn(
                "notes[\"timed_out\"] = True", tail,
                f"после «{pattern}» прерывание не помечается")

    def test_caller_shows_message(self):
        self.assertIn("notes.get(\"timed_out\")", TABLE,
                      "вызывающий не смотрит на прерывание")
        self.assertIn("drag.extract_timeout", TABLE,
                      "вызывающий не показывает сообщение о прерывании")

    def test_pump_between_chunks(self):
        body = method_body(TABLE, "_extract_for_drag")
        self.assertIn("pump", body, "оживление окна между пачками не вызывается")

    def test_status_bar_says_what_happens(self):
        self.assertIn("status.preparing_drag", TABLE,
                      "во время подготовки переноса не сказано, что происходит")


class TestNoSyncEngineCallInDialogMethods(unittest.TestCase):

    def test_scheduler_methods_have_no_sync_calls(self):
        from core.scheduler import (
            list_rizpaq_tasks,
            remove_scheduled_task_by_name,
        )

        for name in ("_load_tasks", "_remove_selected"):
            body = method_body(SCHED, name)
            for forbidden in ("list_rizpaq_tasks()",
                              "remove_scheduled_task_by_name("):
                self.assertNotIn(
                    forbidden, body,
                    f"{name}: синхронный вызов {forbidden} остался на "
                    f"GUI-потоке")


class TestMeasuredCeilingIsHonest(unittest.TestCase):

    def test_timeout_value_unchanged(self):
        m = re.search(r"_DRAG_EXTRACT_TIMEOUT\s*=\s*(\d+)", TABLE)
        self.assertIsNotNone(m, "предел ожидания переноса не найден")
        self.assertEqual(int(m.group(1)), 120,
                         "предел ожидания переноса изменён без замеров")

    def test_message_names_the_limit(self):
        import json

        for code in ("en", "ru", "it", "de", "fr", "es", "zh", "pt", "ja", "pl"):
            path = ROOT / "locales" / f"{code}.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(
                "drag.extract_timeout", data["strings"],
                f"{code}: нет ключа с сообщением о прерывании")
            self.assertIn(
                "{seconds}", data["strings"]["drag.extract_timeout"],
                f"{code}: в сообщении не назван предел ожидания")
            self.assertIn(
                "drag.error_title", data["strings"],
                f"{code}: нет заголовка диалога")

    def test_limit_taken_from_notes_not_from_outer_scope(self):
        body = method_body(TABLE, "startDrag")
        self.assertIn("notes.get(\"timeout\")", body,
                      "предел ожидания берётся не из notes")
        self.assertNotIn(
            "seconds=timeout", body,
            "используется переменная timeout, которой в этом методе нет")

    def test_notes_carry_the_limit(self):
        body = method_body(TABLE, "_extract_for_drag")
        self.assertIn('notes["timeout"]', body,
                      "разбор не сообщает, какой предел применялся")

    def test_dialog_title_is_its_own(self):
        body = method_body(TABLE, "startDrag")
        self.assertIn("drag.error_title", body,
                      "у диалога переноса нет своего заголовка")
        self.assertNotIn(
            "scheduler.manager_title", body,
            "в диалоге переноса взят заголовок другого экрана")


if __name__ == "__main__":
    unittest.main()
