                       











from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _popen_calls(rel: str) -> list:
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if (isinstance(f, ast.Attribute) and f.attr == "Popen"
                and isinstance(f.value, ast.Name) and f.value.id == "subprocess"):
            out.append(node)
    return out


def _stdin_is_devnull(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg != "stdin":
            continue
        value = kw.value
        if isinstance(value, ast.Attribute):
            return value.attr == "DEVNULL"
                                                                  
                                                                           
        if isinstance(value, ast.IfExp):
            return any(
                isinstance(n, ast.Attribute) and n.attr == "DEVNULL"
                for n in ast.walk(value)
            )
    return False


class TestEngineStdinDevnull(unittest.TestCase):
    def test_streaming_worker(self):
        calls = _popen_calls("workers/streaming.py")
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(
                _stdin_is_devnull(call),
                "zpaqfranz в workers/streaming.py может ждать ввода с консоли",
            )

    def test_list_worker(self):
        calls = _popen_calls("workers/list_worker.py")
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(
                _stdin_is_devnull(call),
                "листинг может ждать 'Enter AES password' вместо rc=2",
            )

    def test_extract_workers(self):
        calls = _popen_calls("workers/extract_workers.py")
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(
                _stdin_is_devnull(call),
                "распаковка может ждать ввода пароля с консоли",
            )

    def test_run_zpaq(self):
        calls = _popen_calls("core/zpaq_cli.py")
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(
                _stdin_is_devnull(call),
                "фоновый вызов движка может ждать ввода с консоли",
            )


if __name__ == "__main__":
    unittest.main()
