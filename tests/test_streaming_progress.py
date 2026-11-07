












from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QCoreApplication              

from workers.streaming import StreamingZpaqThread              

_APP = QCoreApplication.instance() or QCoreApplication([])

EXTRACT_LINE = "Extract 1234 bytes (1 KB) in 5 files (2 folders)\n"
ADD_LINE = "Add 2026-10-19 12:00:00 1.234 (7.890 dirs)\n"


class TestProgressInfoEmission(unittest.TestCase):
    def _collect(self, line: str):
        code = (
            "import sys; "
            f"sys.stdout.write({line!r}); "
            "sys.stdout.flush()"
        )
        worker = StreamingZpaqThread([sys.executable, "-u", "-c", code])
        infos: list = []
        worker.progress_info.connect(infos.append)

        try:
            rc, _text = worker._run_stream()
        finally:
                                                                       
                                                                     
            proc = getattr(worker, "_proc", None)
            stream = getattr(proc, "stdout", None) if proc is not None else None
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass

        _APP.processEvents()
        return rc, infos

    def test_extraction_emits_dirs_total(self):
        pass


        rc, infos = self._collect(EXTRACT_LINE)

        self.assertEqual(rc, 0)
        dirs = [i["dirs_total"] for i in infos if "dirs_total" in i]
        self.assertIn(2, dirs, f"dirs_total не эмитился: {infos}")

    def test_extraction_emits_files_and_dirs_together(self):
        pass
        rc, infos = self._collect(EXTRACT_LINE)

        self.assertEqual(rc, 0)
        self.assertTrue(
            any(
                i.get("files_total") == 5 and i.get("dirs_total") == 2
                for i in infos
            ),
            f"нет общего обновления files/dirs: {infos}",
        )

    def test_add_still_emits_dirs_total(self):
        pass
        rc, infos = self._collect(ADD_LINE)

        self.assertEqual(rc, 0)
        self.assertTrue(
            any(i.get("dirs_total") == 7890 for i in infos),
            f"dirs_total при создании пропал: {infos}",
        )


if __name__ == "__main__":
    unittest.main()
