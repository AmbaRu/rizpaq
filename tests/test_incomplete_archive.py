from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ui.archive_actions as aa
from core.incomplete_archive import (
    archive_encryption,
    incomplete_archive_action,
    incomplete_repair_check_command,
    incomplete_repair_command,
    incomplete_repair_plan,
    incomplete_repair_verified,
    repair_temp_path,
)


class _Stub:
    def __init__(self):
        self.status_messages: list = []
        self.logged: list = []
        self.commands: list = []
        self.started: list = []
        self.refreshed: list = []
        self._workers: list = []
        self.zpaq_bin = "zpaq"

    def statusBar(self):
        return self

    def showMessage(self, msg):
        self.status_messages.append(msg)

    def log_output(self, text):
        self.logged.append(text)

    def log_command(self, cmd, password=None):
        self.commands.append((list(cmd), password))

    def _cleanup_worker(self, worker):
        pass

    def _start_incomplete_repair(self, dest, plan):
        self.started.append((dest, dict(plan)))

    def _refresh_index_after_create(self, dest, password=None):
        self.refreshed.append((dest, password))


class _FakeBox:
    Yes = 1
    No = 0

    def __init__(self):
        self.calls: list = []
        self.answer = self.No

    def warning(self, parent, title, text):
        self.calls.append(("warning", title, text))

    def information(self, parent, title, text):
        self.calls.append(("information", title, text))

    def question(self, parent, title, text, buttons=None):
        self.calls.append(("question", title, text))
        return self.answer


class TestIncompleteArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_inc_"))
        self.addCleanup(lambda: _rmtree(self.tmp))
        self.stub = _Stub()
        self.box = _FakeBox()
        self._real_box = aa.QMessageBox
        self._real_tr = aa.tr
        aa.QMessageBox = self.box
        aa.tr = lambda key, **kw: f"[{key}|{kw}]"
        self.addCleanup(setattr, aa, "QMessageBox", self._real_box)
        self.addCleanup(setattr, aa, "tr", self._real_tr)

    def _call(self, dest, is_update, output="", password=None):
        aa.ArchiveActionsMixin._handle_incomplete_archive(
            self.stub, str(dest), is_update, output, password)

    def _file(self, name="out.zpaq", data=b"x" * 1024):
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def _plain(self, name="out.zpaq"):
        return self._file(name, b"7kSt" + b"x" * 1020)

    def _encrypted(self, name="out.zpaq"):
        return self._file(name, b"\x01\x02\x03\x04" + b"x" * 1020)

    def test_missing_file_is_noop(self):
        self._call(self.tmp / "нет.zpaq", False)
        self.assertEqual(self.box.calls, [], "диалог не должен появляться")
        self.assertEqual(self.stub.status_messages, [])

    def test_new_archive_is_deleted(self):
        p = self._file()
        self._call(p, False)
        self.assertFalse(p.exists(), "неполный файл обязан быть удалён")
        self.assertEqual(len(self.box.calls), 0,
                         "предупреждать не нужно: удалять безопасно")
        self.assertTrue(self.stub.status_messages,
                        "пользователь должен узнать, что файл удалён")
        self.assertIn("create.incomplete_deleted",
                      self.stub.status_messages[0],
                      "в статус-баре должно быть сказано про удаление")

    def test_existing_plain_archive_warns_and_offers_repair(self):
        p = self._plain()
        engine_text = ("Detected a 'gap' in the archive due to incomplete "
                       "transaction(s) 1\nSuggestion: use the trim command ASAP")
        self._call(p, True, engine_text)
        self.assertTrue(p.exists(),
                        "существовавший архив удалять нельзя — это потеря данных")
        self.assertEqual([c[0] for c in self.box.calls],
                         ["warning", "question"])
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("trim", text.lower(),
                      "совет движка обязан дойти до пользователя")
        self.assertIn(engine_text[-60:], text,
                      "текст ошибки движка должен быть показан целиком")
        self.assertIn("create.incomplete_repair_ask", self.box.calls[1][2])
        self.assertEqual(self.stub.started, [],
                         "без согласия пользователя ремонт не начинается")

    def test_repair_starts_for_plain_archive(self):
        p = self._plain()
        self.box.answer = _FakeBox.Yes
        self._call(p, True)
        self.assertEqual(len(self.stub.started), 1)
        dest, plan = self.stub.started[0]
        self.assertEqual(dest, str(p))
        self.assertEqual(plan["action"], "trim")
        self.assertIsNone(plan["password"])
        self.assertTrue(plan["temp"].endswith(".zpaq"))

    def test_encrypted_archive_without_password_is_not_repaired(self):
        p = self._encrypted()
        self._call(p, True)
        self.assertTrue(p.exists())
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_encrypted", text)
        self.assertEqual(self.stub.started, [])

    def test_encrypted_archive_with_password_uses_crop(self):
        p = self._encrypted()
        self.box.answer = _FakeBox.Yes
        self._call(p, True, password="pw")
        self.assertEqual(len(self.stub.started), 1)
        dest, plan = self.stub.started[0]
        self.assertEqual(dest, str(p))
        self.assertEqual(plan["action"], "crop")
        self.assertEqual(plan["password"], "pw")

    def test_delete_failure_warns_and_keeps(self):
        p = self._file()

        def boom(self, *a, **k):
            raise OSError("доступ запрещён")

        with mock.patch.object(Path, "unlink", boom):
            self._call(p, False)
        self.assertTrue(p.exists(), "при неудаче удаления файл остаётся")
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_delete_error", text,
                      "должен быть запрошен ключ про неудачу удаления")
        self.assertIn("доступ запрещён", text,
                      "причина неудачи обязана дойти до пользователя")

    def test_existing_archive_without_engine_text(self):
        p = self._plain()
        self._call(p, True, "")
        self.assertTrue(p.exists())
        self.assertEqual([c[0] for c in self.box.calls],
                         ["warning", "question"])
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_text", text)
        self.assertTrue(text, "пустое предупреждение бесполезно")


class TestIncompleteArchiveDecision(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_dec_"))
        self.addCleanup(lambda: _rmtree(self.tmp))

    def test_missing_file_is_nothing(self):
        got = incomplete_archive_action(str(self.tmp / "нет.zpaq"), False)
        self.assertEqual(got["action"], "none")

    def test_new_file_is_deleted(self):
        p = self.tmp / "new.zpaq"
        p.write_bytes(b"x")
        got = incomplete_archive_action(str(p), existed_before=False)
        self.assertEqual(got["action"], "delete")

    def test_existing_file_is_kept(self):
        p = self.tmp / "old.zpaq"
        p.write_bytes(b"x")
        got = incomplete_archive_action(str(p), existed_before=True)
        self.assertEqual(got["action"], "keep",
                         "существовавший архив удалять нельзя")

    def test_directory_is_never_deleted(self):
        d = self.tmp / "папка.zpaq"
        d.mkdir()
        got = incomplete_archive_action(str(d), existed_before=False)
        self.assertEqual(got["action"], "keep",
                         "каталог удалять нельзя ни при каких условиях")
        self.assertTrue(d.exists())

    def test_reason_is_always_present(self):
        for dest, before in ((self.tmp / "a.zpaq", False),
                             (self.tmp / "b.zpaq", True)):
            dest.write_bytes(b"x")
            got = incomplete_archive_action(str(dest), before)
            self.assertTrue(got["reason"], got)


class TestIncompleteArchiveRepair(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_rep_"))
        self.addCleanup(lambda: _rmtree(self.tmp))

    def _write(self, name="arc.zpaq", data=b"7kSt" + b"x" * 100):
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def test_archive_encryption_plain(self):
        p = self._write()
        self.assertEqual(archive_encryption(str(p)), "plain")

    def test_archive_encryption_encrypted(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        self.assertEqual(archive_encryption(str(p)), "encrypted")

    def test_archive_encryption_short_file(self):
        p = self._write(data=b"7k")
        self.assertEqual(archive_encryption(str(p)), "unknown")

    def test_archive_encryption_missing_file(self):
        self.assertEqual(
            archive_encryption(str(self.tmp / "нет.zpaq")), "unknown")

    def test_repair_temp_path_stays_next_to_archive(self):
        dest = self.tmp / "arc.zpaq"
        temp = Path(repair_temp_path(str(dest)))
        self.assertEqual(temp.parent, dest.parent)
        self.assertEqual(temp.suffix, ".zpaq")
        self.assertNotEqual(temp, dest)
        self.assertIn(".repair-", temp.name)

    def test_repair_temp_path_adds_zpaq_suffix(self):
        dest = self.tmp / "arc"
        temp = Path(repair_temp_path(str(dest)))
        self.assertEqual(temp.suffix, ".zpaq")

    def test_plan_plain_archive_is_trim(self):
        p = self._write()
        plan = incomplete_repair_plan(str(p))
        self.assertEqual(plan["action"], "trim")
        self.assertIsNone(plan["password"])
        self.assertTrue(plan["temp"].endswith(".zpaq"))

    def test_plan_encrypted_without_password_needs_password(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p))
        self.assertEqual(plan["action"], "none")
        self.assertTrue(plan.get("needs_password"))
        self.assertIn("пароль", plan["reason"])

    def test_plan_encrypted_with_password_is_crop(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p), "pw")
        self.assertEqual(plan["action"], "crop")
        self.assertEqual(plan["password"], "pw")

    def test_plan_multipart_is_none(self):
        plan = incomplete_repair_plan(str(self.tmp / "arc_????.zpaq"))
        self.assertEqual(plan["action"], "none")
        self.assertIn("многотомный", plan["reason"])

    def test_plan_directory_is_none(self):
        d = self.tmp / "папка.zpaq"
        d.mkdir()
        plan = incomplete_repair_plan(str(d))
        self.assertEqual(plan["action"], "none")

    def test_plan_short_file_is_none(self):
        p = self._write(data=b"7k")
        plan = incomplete_repair_plan(str(p))
        self.assertEqual(plan["action"], "none")
        self.assertIn("формат", plan["reason"])

    def test_repair_command_trim(self):
        plan = {"action": "trim", "temp": "copy.zpaq"}
        cmd = incomplete_repair_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(
            cmd, ["zpaq", "trim", "arc.zpaq", "-to", "copy.zpaq"])

    def test_repair_command_crop(self):
        plan = {"action": "crop", "temp": "copy.zpaq", "password": "pw"}
        cmd = incomplete_repair_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(
            cmd,
            ["zpaq", "crop", "arc.zpaq", "-kill", "-to", "copy.zpaq",
             "-key", "pw"],
        )

    def test_repair_command_unknown_raises(self):
        with self.assertRaises(ValueError):
            incomplete_repair_command("zpaq", "arc.zpaq", {"action": "none"})

    def test_check_command_plain_has_no_key(self):
        plan = {"action": "trim", "temp": "copy.zpaq"}
        cmd = incomplete_repair_check_command("zpaq", "copy.zpaq", plan)
        self.assertEqual(cmd, ["zpaq", "i", "copy.zpaq"])

    def test_check_command_encrypted_has_key(self):
        plan = {"action": "crop", "temp": "copy.zpaq", "password": "pw"}
        cmd = incomplete_repair_check_command("zpaq", "copy.zpaq", plan)
        self.assertEqual(cmd, ["zpaq", "i", "copy.zpaq", "-key", "pw"])

    def test_verified_rejects_nonzero(self):
        self.assertFalse(incomplete_repair_verified("2 versions", 1))

    def test_verified_rejects_incomplete_markers(self):
        for marker in (
            "incomplete transaction",
            "incomplete trans",
            "detected a 'gap'",
            "almost certainly incomplete",
            "skipping block",
            "missing end of segment",
        ):
            with self.subTest(marker=marker):
                self.assertFalse(
                    incomplete_repair_verified(f"2 versions\n{marker}", 0))

    def test_verified_accepts_clean_listing(self):
        self.assertTrue(incomplete_repair_verified(
            "2 versions, 1 files, 1.852 bytes (1.81 KB)", 0))


class TestIncompleteArchiveRepairUi(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_rep_ui_"))
        self.addCleanup(lambda: _rmtree(self.tmp))
        self.stub = _Stub()
        self.box = _FakeBox()
        self._real_box = aa.QMessageBox
        self._real_tr = aa.tr
        aa.QMessageBox = self.box
        aa.tr = lambda key, **kw: f"[{key}|{kw}]"
        self.addCleanup(setattr, aa, "QMessageBox", self._real_box)
        self.addCleanup(setattr, aa, "tr", self._real_tr)

    def _result(self, dest, plan, rc=0, output="", cancelled=False):
        return {
            "context": {"dest": str(dest), "plan": plan},
            "rc": rc,
            "output": output,
            "cancelled": cancelled,
        }

    def test_repair_result_trim_not_needed(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        plan = {
            "action": "trim",
            "temp": str(self.tmp / "arc.repair.zpaq"),
            "password": None,
        }
        aa.ArchiveActionsMixin._on_incomplete_repair_result(
            self.stub,
            self._result(dest, plan, rc=1,
                         output="TRIM seems not necessary on size 1.852"),
        )
        self.assertEqual(len(self.box.calls), 1)
        self.assertEqual(self.box.calls[0][0], "information")
        self.assertIn("create.incomplete_repair_not_needed",
                      self.box.calls[0][2])
        self.assertEqual(self.stub._workers, [])

    def test_repair_result_empty_copy_is_removed(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        temp = self.tmp / "arc.repair.zpaq"
        temp.write_bytes(b"")
        plan = {"action": "trim", "temp": str(temp), "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_result(
            self.stub, self._result(dest, plan, output="done"))
        self.assertFalse(temp.exists())
        self.assertEqual(len(self.box.calls), 1)
        self.assertIn("create.incomplete_repair_empty", self.box.calls[0][2])

    def test_repair_check_unverified_keeps_original(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        temp = self.tmp / "arc.repair.zpaq"
        temp.write_bytes(b"7kSt" + b"y" * 10)
        plan = {"action": "trim", "temp": str(temp), "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_verified(
            self.stub,
            self._result(dest, plan, rc=0,
                         output="almost certainly incomplete"),
        )
        self.assertFalse(temp.exists())
        self.assertEqual(dest.read_bytes(), b"7kSt" + b"x" * 10)
        self.assertEqual(len(self.box.calls), 1)
        self.assertEqual(self.box.calls[0][0], "warning")
        self.assertIn("create.incomplete_repair_unverified",
                      self.box.calls[0][2])

    def test_repair_check_verified_replaces_original(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        temp = self.tmp / "arc.repair.zpaq"
        temp.write_bytes(b"7kSt" + b"y" * 10)
        plan = {"action": "trim", "temp": str(temp), "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_verified(
            self.stub,
            self._result(dest, plan, rc=0,
                         output="2 versions, 1 files, 1.852 bytes"),
        )
        self.assertFalse(temp.exists())
        self.assertEqual(dest.read_bytes(), b"7kSt" + b"y" * 10)
        self.assertEqual(self.stub.refreshed, [(str(dest), None)])
        self.assertEqual(len(self.box.calls), 1)
        self.assertEqual(self.box.calls[0][0], "information")
        self.assertIn("create.incomplete_repair_done", self.box.calls[0][2])

    def test_repair_check_verified_keeps_password_for_index(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"\x01\x02\x03\x04" + b"x" * 10)
        temp = self.tmp / "arc.repair.zpaq"
        temp.write_bytes(b"\x01\x02\x03\x04" + b"y" * 10)
        plan = {
            "action": "crop",
            "temp": str(temp),
            "password": "pw",
        }
        aa.ArchiveActionsMixin._on_incomplete_repair_verified(
            self.stub,
            self._result(dest, plan, rc=0, output="1 versions, 1 files"),
        )
        self.assertEqual(self.stub.refreshed, [(str(dest), "pw")])


def _rmtree(p: Path):
    import shutil

    shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
