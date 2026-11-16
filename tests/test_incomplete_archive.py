from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ui.archive_actions as aa
from PySide6.QtCore import QCoreApplication

from core.incomplete_archive import (
    REPAIR_SPACE_MARGIN,
    archive_encryption,
    incomplete_archive_action,
    incomplete_repair_check_command,
    incomplete_repair_command,
    incomplete_repair_plan,
    incomplete_repair_space,
    incomplete_repair_stdin,
    incomplete_repair_verified,
    repair_temp_path,
)

_APP = QCoreApplication.instance() or QCoreApplication([])


class _Stub:
    def __init__(self):
        self.status_messages: list = []
        self.logged: list = []
        self.commands: list = []
        self.started: list = []
        self.started_inplace: list = []
        self.refreshed: list = []
        self.mode_calls: list = []
        self.confirm_calls: list = []
        self.mode = None
        self.confirm = True
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

    def _ask_repair_mode(self, dest, copy_ok, inplace_ok):
        self.mode_calls.append((dest, copy_ok, inplace_ok))
        return self.mode

    def _confirm_inplace_repair(self, dest):
        self.confirm_calls.append(dest)
        return self.confirm

    def _start_incomplete_repair(self, dest, plan):
        self.started.append((dest, dict(plan)))

    def _start_incomplete_repair_inplace(self, dest, plan):
        self.started_inplace.append((dest, dict(plan)))

    def _repair_failed(self, dest, error):
        aa.ArchiveActionsMixin._repair_failed(self, dest, error)

    def _repair_failed_inplace(self, dest, error):
        aa.ArchiveActionsMixin._repair_failed_inplace(self, dest, error)

    def _repair_unverified_inplace(self, dest, output):
        aa.ArchiveActionsMixin._repair_unverified_inplace(
            self, dest, output)

    def _on_incomplete_repair_inplace_result(self, result):
        aa.ArchiveActionsMixin._on_incomplete_repair_inplace_result(
            self, result)

    def _on_incomplete_repair_inplace_verified(self, result):
        aa.ArchiveActionsMixin._on_incomplete_repair_inplace_verified(
            self, result)

    def _refresh_index_after_create(self, dest, password=None):
        self.refreshed.append((dest, password))


class _FakeBox:
    Yes = 1
    No = 0

    def __init__(self):
        self.calls: list = []
        self.answer = self.No
        self.last_buttons = None
        self.last_default = None

    def warning(self, parent, title, text, buttons=None, default=None):
        self.calls.append(("warning", title, text))
        self.last_buttons = buttons
        self.last_default = default
        return self.answer

    def information(self, parent, title, text):
        self.calls.append(("information", title, text))

    def question(self, parent, title, text, buttons=None):
        self.calls.append(("question", title, text))
        return self.answer


class _Signal:
    def __init__(self):
        self.slots: list = []

    def connect(self, slot):
        self.slots.append(slot)


class _FakeWorker:
    def __init__(self, kind, cmd, context=None, parent=None, cwd=None,
                 stdin_text=None):
        self.kind = kind
        self.cmd = list(cmd)
        self.context = context
        self.stdin_text = stdin_text
        self.result = _Signal()
        self.finished = _Signal()
        self.started = False

    def start(self):
        self.started = True


class _FakeMessageBox:
    Warning = 2
    AcceptRole = 3
    DestructiveRole = 4
    RejectRole = 5
    choice = None
    last = None

    def __init__(self, parent=None):
        self.parent = parent
        self.buttons = []
        self.clicked = None
        self.default = None
        self.escape = None
        _FakeMessageBox.last = self

    def setIcon(self, icon):
        self.icon = icon

    def setWindowTitle(self, title):
        self.title = title

    def setText(self, text):
        self.text = text

    def addButton(self, text, role):
        btn = (text, role)
        self.buttons.append(btn)
        return btn

    def setEscapeButton(self, btn):
        self.escape = btn

    def setDefaultButton(self, btn):
        self.default = btn

    def exec(self):
        for btn in self.buttons:
            if self.choice and self.choice in btn[0]:
                self.clicked = btn

    def clickedButton(self):
        return self.clicked


class TestIncompleteArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rizpaq_inc_"))
        self.addCleanup(lambda: _rmtree(self.tmp))
        self.stub = _Stub()
        self.box = _FakeBox()
        self._real_box = aa.QMessageBox
        self._real_tr = aa.tr
        self._real_space = aa.incomplete_repair_space
        aa.QMessageBox = self.box
        aa.tr = lambda key, **kw: f"[{key}|{kw}]"
        aa.incomplete_repair_space = lambda dest, plan: {
            "enough": True, "free": 10 ** 12, "needed": 1, "required": 1}
        self.addCleanup(setattr, aa, "QMessageBox", self._real_box)
        self.addCleanup(setattr, aa, "tr", self._real_tr)
        self.addCleanup(
            setattr, aa, "incomplete_repair_space", self._real_space)

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
        self.assertEqual([c[0] for c in self.box.calls], ["warning"])
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("trim", text.lower(),
                      "совет движка обязан дойти до пользователя")
        self.assertIn(engine_text[-60:], text,
                      "текст ошибки движка должен быть показан целиком")
        self.assertEqual(self.stub.mode_calls, [(str(p), True, True)])
        self.assertEqual(self.stub.started, [],
                         "без согласия пользователя ремонт не начинается")
        self.assertEqual(self.stub.started_inplace, [])

    def test_repair_starts_for_plain_archive(self):
        p = self._plain()
        self.stub.mode = "copy"
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
        self.stub.mode = "copy"
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
        self.assertEqual([c[0] for c in self.box.calls], ["warning"])
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_text", text)
        self.assertTrue(text, "пустое предупреждение бесполезно")

    def test_no_space_offers_only_inplace(self):
        p = self._plain()
        space = {"enough": False, "free": 1024, "needed": 10 ** 12,
                 "required": 10 ** 12}
        with mock.patch.object(aa, "incomplete_repair_space",
                               return_value=space):
            self._call(p, True)
        self.assertTrue(p.exists())
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_no_space", text)
        self.assertIn("1.0 KB", text)
        self.assertEqual(self.stub.mode_calls, [(str(p), False, True)])
        self.assertEqual(self.stub.started, [])
        self.assertEqual(self.stub.started_inplace, [])

    def test_no_space_inplace_repair_starts_after_confirmation(self):
        p = self._plain()
        space = {"enough": False, "free": 1024, "needed": 10 ** 12,
                 "required": 10 ** 12}
        self.stub.mode = "inplace"
        with mock.patch.object(aa, "incomplete_repair_space",
                               return_value=space):
            self._call(p, True)
        self.assertEqual(self.stub.confirm_calls, [str(p)])
        self.assertEqual(len(self.stub.started_inplace), 1)
        dest, plan = self.stub.started_inplace[0]
        self.assertEqual(dest, str(p))
        self.assertEqual(plan["action"], "trim_in_place")
        self.assertEqual(plan["temp"], "")
        self.assertEqual(self.stub.started, [])

    def test_inplace_repair_can_be_declined(self):
        p = self._plain()
        self.stub.mode = "inplace"
        self.stub.confirm = False
        self._call(p, True)
        self.assertEqual(self.stub.confirm_calls, [str(p)])
        self.assertEqual(self.stub.started_inplace, [])

    def test_cancel_repair_starts_nothing(self):
        p = self._plain()
        self.stub.mode = None
        self._call(p, True)
        self.assertEqual(self.stub.started, [])
        self.assertEqual(self.stub.started_inplace, [])
        self.assertEqual(self.stub.confirm_calls, [])


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

    def test_plan_plain_inplace_is_trim_in_place(self):
        p = self._write()
        plan = incomplete_repair_plan(str(p), inplace=True)
        self.assertEqual(plan["action"], "trim_in_place")
        self.assertIsNone(plan["password"])
        self.assertEqual(plan["temp"], "")
        self.assertIn("без копии", plan["reason"])

    def test_plan_encrypted_without_password_needs_password(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p))
        self.assertEqual(plan["action"], "none")
        self.assertTrue(plan.get("needs_password"))
        self.assertIn("пароль", plan["reason"])

    def test_plan_encrypted_inplace_without_password_needs_password(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p), inplace=True)
        self.assertEqual(plan["action"], "none")
        self.assertTrue(plan.get("needs_password"))

    def test_plan_encrypted_with_password_is_crop(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p), "pw")
        self.assertEqual(plan["action"], "crop")
        self.assertEqual(plan["password"], "pw")

    def test_plan_encrypted_inplace_is_crop_in_place(self):
        p = self._write(data=b"\x01\x02\x03\x04" + b"x" * 100)
        plan = incomplete_repair_plan(str(p), "pw", inplace=True)
        self.assertEqual(plan["action"], "crop_in_place")
        self.assertEqual(plan["password"], "pw")
        self.assertEqual(plan["temp"], "")
        self.assertIn("без копии", plan["reason"])

    def test_plan_multipart_is_none(self):
        plan = incomplete_repair_plan(str(self.tmp / "arc_????.zpaq"))
        self.assertEqual(plan["action"], "none")
        self.assertIn("многотомный", plan["reason"])

    def test_plan_multipart_inplace_is_none(self):
        plan = incomplete_repair_plan(
            str(self.tmp / "arc_????.zpaq"), inplace=True)
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

    def test_repair_space_enough(self):
        p = self._write()
        plan = incomplete_repair_plan(str(p))
        size = p.stat().st_size
        space = incomplete_repair_space(
            str(p), plan, free=size + REPAIR_SPACE_MARGIN)
        self.assertTrue(space["enough"])
        self.assertEqual(space["needed"], size)
        self.assertEqual(space["required"], size + REPAIR_SPACE_MARGIN)
        self.assertEqual(space["free"], size + REPAIR_SPACE_MARGIN)

    def test_repair_space_not_enough(self):
        p = self._write()
        plan = incomplete_repair_plan(str(p))
        space = incomplete_repair_space(str(p), plan, free=1024)
        self.assertFalse(space["enough"])
        self.assertEqual(space["free"], 1024)
        self.assertGreater(space["required"], space["free"])

    def test_repair_space_missing_file(self):
        plan = {
            "action": "trim",
            "temp": str(self.tmp / "arc.repair.zpaq"),
        }
        space = incomplete_repair_space(
            str(self.tmp / "нет.zpaq"), plan, free=10 ** 12)
        self.assertIsNone(space)

    def test_repair_space_checks_temp_folder(self):
        p = self._write()
        sub = self.tmp / "sub"
        sub.mkdir()
        plan = {"action": "trim",
                "temp": str(sub / "arc.repair.zpaq")}
        usage = mock.Mock(free=10 ** 12)
        with mock.patch("core.incomplete_archive.shutil.disk_usage",
                        return_value=usage) as disk_usage:
            space = incomplete_repair_space(str(p), plan)
        disk_usage.assert_called_once_with(str(sub))
        self.assertTrue(space["enough"])

    def test_repair_space_not_needed_inplace(self):
        p = self._write()
        plan = incomplete_repair_plan(str(p), inplace=True)
        with mock.patch(
                "core.incomplete_archive.shutil.disk_usage") as disk_usage:
            space = incomplete_repair_space(str(p), plan)
        self.assertIsNone(space)
        disk_usage.assert_not_called()

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

    def test_repair_command_trim_in_place(self):
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        cmd = incomplete_repair_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(cmd, ["zpaq", "trim", "arc.zpaq", "-kill"])

    def test_repair_command_crop_in_place(self):
        plan = {"action": "crop_in_place", "temp": "", "password": "pw"}
        cmd = incomplete_repair_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(
            cmd,
            ["zpaq", "crop", "arc.zpaq", "-kill", "-force", "-key", "pw"],
        )

    def test_repair_stdin_crop_in_place(self):
        self.assertEqual(
            incomplete_repair_stdin({"action": "crop_in_place"}),
            "cropplease\n",
        )

    def test_repair_stdin_copy_is_none(self):
        self.assertIsNone(incomplete_repair_stdin({"action": "crop"}))
        self.assertIsNone(incomplete_repair_stdin({"action": "trim"}))
        self.assertIsNone(incomplete_repair_stdin({"action": "trim_in_place"}))

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

    def test_check_command_crop_in_place_has_key(self):
        plan = {"action": "crop_in_place", "temp": "", "password": "pw"}
        cmd = incomplete_repair_check_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(cmd, ["zpaq", "i", "arc.zpaq", "-key", "pw"])

    def test_check_command_trim_in_place_has_no_key(self):
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        cmd = incomplete_repair_check_command("zpaq", "arc.zpaq", plan)
        self.assertEqual(cmd, ["zpaq", "i", "arc.zpaq"])

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

    def _ask_mode(self, copy_ok, inplace_ok, choice):
        real = aa.QMessageBox
        aa.QMessageBox = _FakeMessageBox
        _FakeMessageBox.choice = choice
        try:
            return aa.ArchiveActionsMixin._ask_repair_mode(
                self.stub, "arc.zpaq", copy_ok, inplace_ok)
        finally:
            aa.QMessageBox = real

    def test_ask_mode_copy_is_default(self):
        got = self._ask_mode(True, True, "with_copy")
        self.assertEqual(got, "copy")
        box = _FakeMessageBox.last
        labels = [btn[0] for btn in box.buttons]
        self.assertTrue(any("with_copy" in label for label in labels))
        self.assertTrue(any("inplace" in label for label in labels))
        self.assertTrue(any("progress.cancel" in label for label in labels))
        self.assertIn("create.incomplete_repair_choose", box.text)
        self.assertIs(box.default, box.buttons[0])
        self.assertIs(box.escape, box.buttons[-1])

    def test_ask_mode_inplace(self):
        self.assertEqual(self._ask_mode(True, True, "inplace"), "inplace")

    def test_ask_mode_cancel(self):
        self.assertIsNone(self._ask_mode(True, True, None))

    def test_ask_mode_without_copy(self):
        got = self._ask_mode(False, True, "inplace")
        self.assertEqual(got, "inplace")
        labels = [btn[0] for btn in _FakeMessageBox.last.buttons]
        self.assertFalse(any("with_copy" in label for label in labels))
        self.assertIn("progress.cancel", _FakeMessageBox.last.default[0])

    def test_ask_mode_without_inplace(self):
        got = self._ask_mode(True, False, "with_copy")
        self.assertEqual(got, "copy")
        labels = [btn[0] for btn in _FakeMessageBox.last.buttons]
        self.assertFalse(any("repair_inplace" in label for label in labels))

    def test_confirm_inplace_repair_requires_yes(self):
        dest = str(self.tmp / "arc.zpaq")
        self.box.answer = _FakeBox.Yes
        got = aa.ArchiveActionsMixin._confirm_inplace_repair(
            self.stub, dest)
        self.assertTrue(got)
        kind, title, text = self.box.calls[-1]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_inplace_warning", text)
        self.assertEqual(self.box.last_default, _FakeBox.No)
        self.box.answer = _FakeBox.No
        self.assertFalse(
            aa.ArchiveActionsMixin._confirm_inplace_repair(self.stub, dest))

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

    def test_repair_failure_removes_copy_and_keeps_original(self):
        dest = self.tmp / "arc.zpaq"
        original = b"7kSt" + b"x" * 10
        dest.write_bytes(original)
        temp = self.tmp / "arc.repair.zpaq"
        temp.write_bytes(b"7kSt" + b"y" * 10)
        plan = {"action": "trim", "temp": str(temp), "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_result(
            self.stub,
            self._result(dest, plan, rc=2,
                         output="ERROR media full, cannot write"),
        )
        self.assertFalse(temp.exists(),
                         "недоделанная копия не должна оставаться")
        self.assertEqual(dest.read_bytes(), original,
                         "при ошибке ремонта исходник неприкосновенен")
        self.assertEqual(self.stub._workers, [],
                         "проверять недоделанную копию нельзя")
        self.assertEqual(len(self.box.calls), 1)
        self.assertEqual(self.box.calls[0][0], "warning")
        self.assertIn("create.incomplete_repair_failed",
                      self.box.calls[0][2])

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

    def test_start_inplace_writes_captcha_and_force(self):
        dest = self.tmp / "arc.zpaq"
        plan = {"action": "crop_in_place", "temp": "", "password": "pw"}
        with mock.patch.object(aa, "ZpaqWorker", _FakeWorker):
            aa.ArchiveActionsMixin._start_incomplete_repair_inplace(
                self.stub, str(dest), plan)
        self.assertEqual(len(self.stub._workers), 1)
        worker = self.stub._workers[0]
        self.assertTrue(worker.started)
        self.assertEqual(worker.kind, "repair_inplace")
        self.assertEqual(
            worker.cmd,
            ["zpaq", "crop", str(dest), "-kill", "-force", "-key", "pw"],
        )
        self.assertEqual(worker.stdin_text, "cropplease\n")
        self.assertEqual(self.stub.commands, [(worker.cmd, "pw")])

    def test_inplace_result_starts_check_on_dest(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        with mock.patch.object(aa, "ZpaqWorker", _FakeWorker):
            aa.ArchiveActionsMixin._on_incomplete_repair_inplace_result(
                self.stub,
                self._result(dest, plan, rc=0, output="Trim DONE"),
            )
        self.assertEqual(len(self.stub._workers), 1)
        worker = self.stub._workers[0]
        self.assertEqual(worker.kind, "repair_check_inplace")
        self.assertEqual(worker.cmd, ["zpaq", "i", str(dest)])
        self.assertIsNone(worker.stdin_text)
        self.assertEqual(self.stub.commands[-1], (worker.cmd, ""))

    def test_inplace_failure_warns_and_keeps_original(self):
        dest = self.tmp / "arc.zpaq"
        original = b"7kSt" + b"x" * 10
        dest.write_bytes(original)
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_inplace_result(
            self.stub,
            self._result(dest, plan, rc=2, output="ERROR crop failed"),
        )
        self.assertEqual(dest.read_bytes(), original)
        self.assertEqual(self.stub._workers, [])
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_inplace_failed", text)
        self.assertIn("ERROR crop failed", text)

    def test_inplace_cancel_warns_honestly(self):
        dest = self.tmp / "arc.zpaq"
        dest.write_bytes(b"7kSt" + b"x" * 10)
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_inplace_result(
            self.stub,
            self._result(dest, plan, rc=1, cancelled=True),
        )
        self.assertEqual(self.stub._workers, [])
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_inplace_failed", text)

    def test_inplace_verified_reports_done_without_replace(self):
        dest = self.tmp / "arc.zpaq"
        repaired = b"\x01\x02\x03\x04" + b"y" * 10
        dest.write_bytes(repaired)
        plan = {
            "action": "crop_in_place",
            "temp": "",
            "password": "pw",
        }
        with mock.patch("ui.archive_actions.os.replace") as replace:
            aa.ArchiveActionsMixin._on_incomplete_repair_inplace_verified(
                self.stub,
                self._result(
                    dest, plan, rc=0,
                    output="2 versions, 1 files, 1.852 bytes"),
            )
        replace.assert_not_called()
        self.assertEqual(dest.read_bytes(), repaired)
        self.assertEqual(self.stub.refreshed, [(str(dest), "pw")])
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "information")
        self.assertIn("create.incomplete_repair_done", text)

    def test_inplace_unverified_warns(self):
        dest = self.tmp / "arc.zpaq"
        data = b"7kSt" + b"x" * 10
        dest.write_bytes(data)
        plan = {"action": "trim_in_place", "temp": "", "password": None}
        aa.ArchiveActionsMixin._on_incomplete_repair_inplace_verified(
            self.stub,
            self._result(
                dest, plan, rc=0,
                output="almost certainly incomplete"),
        )
        self.assertEqual(dest.read_bytes(), data)
        self.assertEqual(self.stub.refreshed, [])
        self.assertEqual(len(self.box.calls), 1)
        kind, title, text = self.box.calls[0]
        self.assertEqual(kind, "warning")
        self.assertIn("create.incomplete_repair_inplace_unverified", text)
        self.assertIn("almost certainly incomplete", text)


class TestStreamingStdin(unittest.TestCase):
    def test_worker_writes_stdin_text(self):
        from workers.streaming import StreamingZpaqThread

        code = "import sys; print(sys.stdin.read().strip())"
        worker = StreamingZpaqThread(
            [sys.executable, "-u", "-c", code],
            stdin_text="cropplease\n",
        )
        rc, text = worker._run_stream()
        self.assertEqual(rc, 0)
        self.assertIn("cropplease", text)


def _rmtree(p: Path):
    import shutil

    shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
