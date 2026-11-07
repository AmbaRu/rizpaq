













from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def csv_line(name: str, pad: int = 0) -> bytes:
    pass
    path = "C:/dir/test_" + name + "_" + ("a" * pad)
    return (
        "2026-10-22 10:00:00\tA....\t734\t107%\t0002\t#\t" + path
    ).encode("ascii")


def path_name(entry) -> str:
    pass
    return entry.path.split("test_")[-1].split("_", 1)[0]


                                                                     
                                                              
                                                                     
                                                       
CHILD = (
    "import sys, time\n"
    "w = sys.stdout.buffer.write\n"
    "f = sys.stdout.buffer.flush\n"
    f"w({csv_line('alpha', 4400)!r}); f(); time.sleep(0.2)\n"
    f"w(b'\\n'); f(); time.sleep(0.2)\n"
    f"w({csv_line('beta')!r} + b'\\r'); f(); time.sleep(0.2)\n"
    f"w({csv_line('gamma')!r}); f(); time.sleep(0.15)\n"
                                                                  
                                                                
    f"w(b'\\r'); f(); time.sleep(0.15)\n"
    f"w(b'\\n'); f(); time.sleep(0.15)\n"
    f"w({csv_line('delta')!r} + b'\\n'); f(); time.sleep(0.15)\n"
                                                                      
    f"w({csv_line('epsilon')!r}); f()\n"
)

EXPECTED = ["alpha", "beta", "gamma", "delta", "epsilon"]


class TestListWorkerSplitLines(unittest.TestCase):
    pass

    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtCore import QCoreApplication

            cls._app = QCoreApplication.instance() or QCoreApplication([])
        except Exception:
            cls._app = None

    def test_split_lines_all_collected(self):
        import shutil
        import tempfile

        from workers.list_worker import StreamingListWorker

        tmp = Path(tempfile.mkdtemp(prefix="rizpaq_split_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        body = tmp / "child.py"
        body.write_bytes(CHILD.encode("ascii"))
        stub = tmp / "zpaqfranz.cmd"
        stub.write_text(
            '@echo off\r\n"%s" -u "%s" %%*\r\n' % (sys.executable, body),
            encoding="ascii",
        )
        arc = tmp / "backup.zpaq"
        arc.write_bytes(b"x" * 32)

        results = []
        worker = StreamingListWorker(
            [str(stub), "l", str(arc)], context={"marker": "ok"}
        )
        worker.result.connect(results.append)
                                                                      
        worker.run()

        self.assertEqual(len(results), 1, "сигнал result должен прийти один")
        res = results[0]
        self.assertEqual(res["marker"], "ok", "контекст потерялся")
        self.assertEqual(res["rc"], 0, f"rc != 0: {res['tail'][:400]}")
        self.assertFalse(res["cancelled"])

        names = [path_name(e) for e in res["entries"]]
        self.assertEqual(
            names, EXPECTED,
            f"строки потерялись или продублировались: {names}")
                                                                   
                                                                       
        self.assertGreater(
            len(res["entries"][0].path), 4096,
            "строка alpha короче порции чтения — разрезание не проверено")
        self.assertEqual(
            res["report"].dropped, 0,
            "потери разбора там, где их быть не должно: "
            f"{res['report'].log_text()}")
        self.assertEqual(res["report"].service, 0)


if __name__ == "__main__":
    unittest.main()
