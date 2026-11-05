from __future__ import annotations

import ast
import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LOADER = Path(__file__).resolve().parent.parent / "ui" / "archive_loader.py"
TREE = ast.parse(LOADER.read_text(encoding="utf-8"))


def _func(name: str):
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"функция {name} не найдена в {LOADER.name}")


def _calls_in_order(func: ast.FunctionDef) -> list:
    calls = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = getattr(f, "id", None) or getattr(f, "attr", None)
        if name:
            calls.append((node.lineno, name))
    calls.sort(key=lambda c: c[0])
    return [name for _lineno, name in calls]


def _count_call(func: ast.FunctionDef, name: str) -> int:

    return sum(
        1 for node in ast.walk(func)
        if isinstance(node, ast.Call)
        and ((getattr(node.func, "id", None) == name)
             or (getattr(node.func, "attr", None) == name))
    )


class TestTwoPhasesAreOneOperation(unittest.TestCase):
    def test_info_phase_raises_busy(self):
        calls = _calls_in_order(_func("_load_info"))
        self.assertIn(
            "_start_busy",
            calls,
            "фаза «информация об архиве» не поднимает индикацию операции",
        )

    def test_list_stop_happens_after_handling(self):
        order = _calls_in_order(_func("_on_streaming_list_result"))

        self.assertIn("_apply_list_entries", order,
                      "обработка списка пропала")
        self.assertIn("_stop_busy", order,
                      "ветка списка больше не гасит индикацию")
        self.assertLess(
            order.index("_apply_list_entries"),
            order.index("_stop_busy"),
            f"_stop_busy для списка вызывается ДО обработки: окошко мигнёт "
            f"между фазами. Порядок в коде: {order}",
        )

    def test_info_stop_happens_after_handling(self):

        order = _calls_in_order(_func("_on_worker_result"))

        self.assertIn("_handle_info_result", order,
                      "обработка информации пропала")
        self.assertIn("_stop_busy", order,
                      "ветка информации не гасит индикацию")
        self.assertLess(
            order.index("_handle_info_result"),
            order.index("_stop_busy"),
            f"информация гасится до её обработки. Порядок в коде: {order}",
        )

    def test_both_kinds_stop_busy(self):
        n_list = _count_call(_func("_on_streaming_list_result"), "_stop_busy")
        n_info = _count_call(_func("_on_worker_result"), "_stop_busy")
        self.assertEqual(
            (n_list, n_info), (1, 1),
            f"ожидалось по одному вызову _stop_busy на фазу "
            f"(list, info), найдено ({n_list}, {n_info})",
        )


class TestNoticeWiring(unittest.TestCase):
    def test_ensure_notice_exists_in_services(self):
        from ui.app_services import AppServicesMixin

        for name in ("_ensure_notice", "_start_busy", "_stop_busy"):
            with self.subTest(method=name):
                self.assertTrue(
                    hasattr(AppServicesMixin, name),
                    f"в AppServicesMixin нет метода {name}",
                )

    def test_busy_uses_counter_not_flag(self):
        from ui.app_services import AppServicesMixin

        src = Path(inspect.getfile(AppServicesMixin)).read_text(encoding="utf-8")
        start = src.index("def _stop_busy")
        body = src[start:start + 700]
        self.assertIn(
            "_busy_depth",
            body,
            "_stop_busy не уменьшает счётчик параллельных операций",
        )

    def test_main_window_initializes_notice_state(self):

        mw = (
            Path(__file__).resolve().parent.parent / "ui" / "main_window.py"
        ).read_text(encoding="utf-8")
        for attr in ("_busy_depth", "_notice"):
            with self.subTest(attr=attr):
                self.assertIn(f"self.{attr}", mw, f"main_window не инициализирует {attr}")

    def test_tick_busy_does_not_stomp_foreign_message(self):
        from ui.app_services import AppServicesMixin

        src = Path(inspect.getfile(AppServicesMixin)).read_text(encoding="utf-8")
        start = src.index("def _tick_busy")
        body = src[start:start + 600]
        self.assertIn(
            "currentMessage",
            body,
            "_tick_busy затирает сообщения, выставленные другими обработчиками",
        )


if __name__ == "__main__":
    unittest.main()
