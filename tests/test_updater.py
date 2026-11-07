                       





from __future__ import annotations

import io
import json
import os
import shutil
import stat
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication              

_APP = QApplication.instance() or QApplication(sys.argv)

from ui import i18n              
from ui.update_actions import UpdateActionsMixin              
from ui.update_dialog import UpdateDialog              

from core import config as config_mod              
from core import updater              

ALL_LANGS = ("en", "ru", "it", "de", "fr", "es", "zh", "pt", "ja", "pl")


                                                                            


class _Response(io.BytesIO):
    pass

    def __init__(self, data: bytes, headers: dict | None = None):
        super().__init__(data)
        raw = dict(headers or {})
        self.headers = SimpleNamespace(
            get=lambda key, default=None: raw.get(key, default),
            get_content_charset=lambda: "utf-8",
        )


def _opener(data: bytes, headers: dict | None = None):
    calls = []

    def open_func(request, timeout=None):
        calls.append((request, timeout))
        return _Response(data, headers)

    open_func.calls = calls
    return open_func


def _make_zip(path: Path, names: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, b"data")
    return path


def _release_zip(path: Path, flat: bool = False) -> Path:
    root = "" if flat else "Rizpaq/"
    return _make_zip(path, [
        root + "Rizpaq.exe",
        root + "_internal/python3.dll",
        root + "_internal/PySide6/Qt6Core.dll",
    ])


class _Host(UpdateActionsMixin):
    pass

    def __init__(self, cfg=None):
        self._cfg = cfg or SimpleNamespace(
            update_url=None,
            update_check_enabled=True,
            last_update_check=None,
            skipped_version=None,
        )
        self._workers = []
        self.shown = []
        self.messages = []

    def statusBar(self):
        host = self

        class _Bar:
            def showMessage(self, text, *a):
                host.messages.append(text)

        return _Bar()

    def _show_update_dialog(self, info, manual):
        self.shown.append((dict(info), bool(manual)))


                                                                            


class VersionTests(unittest.TestCase):
    def test_version_key_parses_numbers(self):
        self.assertEqual(updater.version_key("2.9.0"), (2, 9, 0))
        self.assertEqual(updater.version_key("v2.9.0-beta"), (2, 9, 0))
        self.assertEqual(updater.version_key(" 2.7.12 "), (2, 7, 12))

    def test_version_key_rejects_text_without_numbers(self):
        for bad in ("", None, "latest", "v"):
            with self.assertRaises(updater.UpdateError):
                updater.version_key(bad)

    def test_newer(self):
        self.assertTrue(updater.is_newer("2.9.0", "2.7.2"))
        self.assertTrue(updater.is_newer("2.7.10", "2.7.9"))
        self.assertFalse(updater.is_newer("2.7.2", "2.7.2"))
        self.assertFalse(updater.is_newer("2.7", "2.7.0"))          
        self.assertFalse(updater.is_newer("2.6.9", "2.7.0"))

    def test_short_versions_compared_as_zero_padded(self):
        self.assertTrue(updater.is_newer("2.9", "2.8.9"))
        self.assertFalse(updater.is_newer("2.9", "2.9.0"))


                                                                            


class ManifestTests(unittest.TestCase):
    def _valid(self, **extra):
        data = {
            "version": "2.9.0",
            "url": "https://rizpaq.ru/updates/rizpaq-2.9.0-win64.zip",
        }
        data.update(extra)
        return data

    def test_parses_minimal_manifest(self):
        info = updater.parse_manifest(json.dumps(self._valid()))
        self.assertEqual(info["version"], "2.9.0")
        self.assertEqual(info["url"],
                         "https://rizpaq.ru/updates/rizpaq-2.9.0-win64.zip")
        self.assertEqual(info["notes"], "")
        self.assertEqual(info["notes_url"], "")
        self.assertEqual(info["published"], "")
        self.assertEqual(info["sha256"], "")

    def test_parses_full_manifest_and_bytes(self):
        sha = "a" * 64
        raw = json.dumps(self._valid(
            notes="Что нового",
            notes_url="https://rizpaq.ru/news/2.9.0",
            published="2026-11-01",
            sha256=sha.upper(),
        ), ensure_ascii=False).encode("utf-8")
        info = updater.parse_manifest(raw)
        self.assertEqual(info["notes"], "Что нового")
        self.assertEqual(info["notes_url"], "https://rizpaq.ru/news/2.9.0")
        self.assertEqual(info["published"], "2026-11-01")
        self.assertEqual(info["sha256"], sha)                               

    def test_rejects_bad_manifests(self):
        cases = [
            {"url": "https://rizpaq.ru/a.zip"},                                
            {"version": "2.9.0"},                                            
            {"version": "", "url": "https://rizpaq.ru/a.zip"},
            {"version": "latest", "url": "https://rizpaq.ru/a.zip"},
            self._valid(url="http://rizpaq.ru/a.zip"),                        
            self._valid(url="file:///C:/a.zip"),
            self._valid(notes_url="http://rizpaq.ru/news"),
            self._valid(sha256="abc"),
            self._valid(sha256="g" * 64),
        ]
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(updater.UpdateError):
                    updater.parse_manifest(json.dumps(data))

    def test_rejects_non_object_and_bad_json(self):
        for raw in ("[]", "{not json", b"\xff\xfe\x00"):
            with self.subTest(raw=raw):
                with self.assertRaises(updater.UpdateError):
                    updater.parse_manifest(raw)

    def test_fetch_uses_https_and_user_agent(self):
        opener = _opener(json.dumps(self._valid()).encode("utf-8"))
        info = updater.fetch_manifest(
            "https://rizpaq.ru/updates/latest.json", opener=opener)
        self.assertEqual(info["version"], "2.9.0")
        request, timeout = opener.calls[0]
        self.assertEqual(request.full_url,
                         "https://rizpaq.ru/updates/latest.json")
        self.assertIn("Rizpaq-updater", request.get_header("User-agent"))
        self.assertEqual(timeout, updater.DEFAULT_TIMEOUT)

    def test_fetch_rejects_http_before_network(self):
        opener = _opener(b"{}")
        with self.assertRaises(updater.UpdateError):
            updater.fetch_manifest("http://rizpaq.ru/latest.json",
                                   opener=opener)
        self.assertEqual(opener.calls, [])

    def test_fetch_rejects_oversized_manifest(self):
        opener = _opener(b"x" * (updater.MAX_MANIFEST_BYTES + 1))
        with self.assertRaises(updater.UpdateError):
            updater.fetch_manifest(opener=opener)

    def test_fetch_wraps_network_error(self):
        def boom(request, timeout=None):
            raise OSError("no route to host")

        with self.assertRaises(updater.UpdateError) as ctx:
            updater.fetch_manifest(opener=boom)
        self.assertIn("no route to host", str(ctx.exception))


                                                                             


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_dl_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.payload = b"PK" + b"x" * (updater._CHUNK + 10)
        self.info = {
            "version": "2.9.0",
            "url": "https://rizpaq.ru/updates/rizpaq-2.9.0-win64.zip",
            "sha256": "",
        }

    def test_downloads_bytes_and_reports_progress(self):
        opener = _opener(self.payload,
                         {"Content-Length": str(len(self.payload))})
        seen = []
        dest = updater.download_update(
            self.info, self._tmp,
            progress=lambda read, total: seen.append((read, total)),
            opener=opener,
        )
        self.assertEqual(dest.name, "rizpaq-2.9.0-win64.zip")
        self.assertEqual(dest.read_bytes(), self.payload)
        self.assertTrue(seen)
        self.assertEqual(seen[-1], (len(self.payload), len(self.payload)))
        self.assertEqual(opener.calls[0][1], updater.DEFAULT_TIMEOUT)

    def test_download_checks_sha256(self):
        import hashlib

        digest = hashlib.sha256(self.payload).hexdigest()
        info = dict(self.info, sha256=digest)
        dest = updater.download_update(
            info, self._tmp, opener=_opener(self.payload))
        self.assertTrue(dest.is_file())

    def test_sha256_mismatch_removes_file(self):
        info = dict(self.info, sha256="0" * 64)
        with self.assertRaises(updater.UpdateError):
            updater.download_update(info, self._tmp,
                                    opener=_opener(self.payload))
        self.assertEqual(list(self._tmp.iterdir()), [])

    def test_cancel_stops_and_removes_partial_file(self):
        def cancel():
            return True

        with self.assertRaises(updater.UpdateCancelled):
            updater.download_update(self.info, self._tmp,
                                    is_cancelled=cancel,
                                    opener=_opener(self.payload))
        self.assertEqual(list(self._tmp.iterdir()), [])

    def test_too_large_archive_rejected_by_header(self):
        opener = _opener(self.payload,
                         {"Content-Length": str(updater.MAX_ARCHIVE_BYTES + 1)})
        with self.assertRaises(updater.UpdateError):
            updater.download_update(self.info, self._tmp, opener=opener)

    def test_archive_name_is_sanitized(self):
        info = dict(self.info,
                    url="https://rizpaq.ru/updates/%2e%2e/%2e%2e/evil.zip?x=1")
        opener = _opener(b"x")
        dest = updater.download_update(info, self._tmp, opener=opener)
        self.assertEqual(dest.name, "evil.zip")
        self.assertEqual(dest.parent.resolve(), self._tmp.resolve())


                                                                             


class ZipLayoutTests(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_zip_"))
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def test_accepts_release_layout(self):
        path = _release_zip(self._tmp / "ok.zip")
        info = updater.inspect_update_zip(path)
        self.assertEqual(info["root"], "Rizpaq/")
        self.assertEqual(info["exe"], "Rizpaq/Rizpaq.exe")

    def test_accepts_flat_layout(self):
        path = _release_zip(self._tmp / "flat.zip", flat=True)
        info = updater.inspect_update_zip(path)
        self.assertEqual(info["root"], "")
        self.assertEqual(info["internal"], "_internal")

    def test_rejects_missing_exe_or_internal(self):
        cases = [
            ["Rizpaq/Rizpaq.exe"],                                   
            ["Rizpaq/_internal/a.dll"],                          
            ["other/file.txt"],
        ]
        for names in cases:
            with self.subTest(names=names):
                path = _make_zip(self._tmp / "bad.zip", names)
                with self.assertRaises(updater.UpdateError):
                    updater.inspect_update_zip(path)
                path.unlink()

    def test_rejects_parent_paths(self):
        path = _make_zip(self._tmp / "trav.zip",
                         ["Rizpaq/Rizpaq.exe", "Rizpaq/_internal/x",
                          "../evil.txt"])
        with self.assertRaises(updater.UpdateError):
            updater.inspect_update_zip(path)

    def test_rejects_absolute_and_drive_paths(self):
        for bad in ("/abs.txt", "C:/evil.txt", "C:\\evil.txt"):
            with self.subTest(bad=bad):
                path = _make_zip(self._tmp / "abs.zip",
                                 ["Rizpaq/Rizpaq.exe", "Rizpaq/_internal/x",
                                  bad])
                with self.assertRaises(updater.UpdateError):
                    updater.inspect_update_zip(path)
                path.unlink()

    def test_rejects_encrypted_entry(self):
        class _FakeZip:
            def infolist(self):
                exe = zipfile.ZipInfo("Rizpaq/Rizpaq.exe")
                internal = zipfile.ZipInfo("Rizpaq/_internal/a")
                internal.flag_bits |= 0x1
                return [exe, internal]

            def close(self):
                pass

        with mock.patch.object(updater.zipfile, "ZipFile",
                               return_value=_FakeZip()):
            with self.assertRaises(updater.UpdateError):
                updater.inspect_update_zip(self._tmp / "enc.zip")

    def test_rejects_symlink(self):
        path = self._tmp / "link.zip"
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("Rizpaq/Rizpaq.exe", b"x")
            info = zipfile.ZipInfo("Rizpaq/_internal/link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "target")
        with self.assertRaises(updater.UpdateError):
            updater.inspect_update_zip(path)

    def test_rejects_not_a_zip(self):
        path = self._tmp / "fake.zip"
        path.write_bytes(b"not a zip")
        with self.assertRaises(updater.UpdateError):
            updater.inspect_update_zip(path)


                                                                            


class UpdateScriptTests(unittest.TestCase):
    def test_script_waits_for_pid_and_replaces_only_app_files(self):
        script = updater.build_update_script(
            r"C:\Temp\rizpaq.zip", r"C:\Apps\Rizpaq", 12345,
            r"C:\Temp\rizpaq_update_x",
        )
        self.assertIn("$waitPid = 12345", script)
        self.assertIn("Get-Process -Id $waitPid", script)
        self.assertIn("Rizpaq.exe", script)
        self.assertIn("_internal", script)
        for data in ("zpaq_gui.json", "archive_index.sqlite", "tasks.rzp"):
            self.assertNotIn(data, script)
        self.assertIn("Expand-Archive", script)
        self.assertIn("Rename-Item", script)
        self.assertIn("rollback", script)

    def test_script_quoting_escapes_apostrophes(self):
        script = updater.build_update_script(
            "C:\\O'Brien\\u.zip", "C:\\O'Brien\\Rizpaq", 7, "C:\\T",
        )
        self.assertIn("'C:\\O''Brien\\Rizpaq'", script)

    def test_script_logs_start_and_extracts_into_stage_subdir(self):
        script = updater.build_update_script(
            r"C:\Temp\rizpaq.zip", r"C:\Apps\Rizpaq", 12345,
            r"C:\Temp\rizpaq_update_x",
        )
                                                                   
                                                                
        self.assertIn("Write-Log 'updater started'", script)
                                                                    
        self.assertIn("Expand-Archive -LiteralPath $zip "
                      "-DestinationPath $stage -Force", script)
                                                                   
                                                                 
        idx_expand = script.index("Expand-Archive")
        idx_cleanup = script.index("Remove-Item -LiteralPath $temp")
        self.assertLess(idx_expand, idx_cleanup)

    def test_prepare_update_creates_script_and_copy(self):
        tmp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_prep_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        archive = _release_zip(tmp / "src.zip")
        out_dir = tmp / "work"

        script, temp_dir = updater.prepare_update(
            archive, install_path=tmp / "install", wait_pid=42,
            temp_root=out_dir,
        )
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        self.assertTrue(script.is_file())
        self.assertTrue((temp_dir / archive.name).is_file())
        text = script.read_text(encoding="utf-8-sig")
        self.assertIn("$waitPid = 42", text)
        self.assertIn(str(temp_dir), text)

    def test_prepare_update_requires_built_app_path(self):
        tmp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_prep2_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        archive = _release_zip(tmp / "src.zip")
        with self.assertRaises(updater.UpdateError):
            updater.prepare_update(archive, install_path=None, wait_pid=1)

    def test_prepare_update_rejects_bad_zip_and_missing_file(self):
        tmp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_prep3_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        bad = tmp / "bad.zip"
        bad.write_bytes(b"nope")
        for path in (bad, tmp / "missing.zip"):
            with self.subTest(path=path):
                with self.assertRaises(updater.UpdateError):
                    updater.prepare_update(path, install_path=tmp,
                                           wait_pid=1)

    def test_launch_updater_calls_powershell(self):
        calls = []

        def fake_popen(args, **kwargs):
            calls.append((args, kwargs))
            return object()

        with mock.patch.object(updater.shutil, "which",
                               return_value=r"C:\Windows\powershell.exe"), \
                mock.patch.object(updater.subprocess, "Popen", fake_popen):
            updater.launch_updater(r"C:\Temp\u.ps1")

        args, kwargs = calls[0]
        self.assertIn("powershell.exe", args[0])
        self.assertIn("-ExecutionPolicy", args)
        self.assertIn("Bypass", args)
        self.assertIn(r"C:\Temp\u.ps1", args)
                                                                     
                                                                         
                                                      
        self.assertNotIn("cwd", kwargs)
        self.assertEqual(kwargs["creationflags"], 0x08000000)

    def test_launch_updater_without_powershell_fails(self):
        with mock.patch.object(updater.shutil, "which", return_value=None):
            with self.assertRaises(updater.UpdateError):
                updater.launch_updater("u.ps1")

    def test_install_dir_none_when_not_frozen(self):
        with mock.patch.object(updater.sys, "frozen", False, create=True):
            self.assertIsNone(updater.install_dir())


                                                                             


class _FakeSignal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)


class _FakeWorker:
    instances = []

    def __init__(self, url, version, parent=None):
        self.url = url
        self.version = version
        self.parent = parent
        self.done = _FakeSignal()
        self.finished = _FakeSignal()
        self.started = False
        _FakeWorker.instances.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return False


class UpdateActionsTests(unittest.TestCase):
    def setUp(self):
        _FakeWorker.instances = []
        self.host = _Host()
                                                      
        patcher = mock.patch("ui.update_actions._merge_cfg")
        self.merge = patcher.start()
        self.addCleanup(patcher.stop)

    def test_auto_check_skipped_within_a_day(self):
        self.host._cfg.last_update_check = int(time.time()) - 60
        patcher = mock.patch("ui.update_actions.UpdateCheckWorker", _FakeWorker)
        with patcher:
            self.assertFalse(self.host.start_update_check())
        self.assertEqual(_FakeWorker.instances, [])

    def test_auto_check_runs_when_interval_passed(self):
        self.host._cfg.last_update_check = (
            int(time.time()) - ui_interval() - 10)
        with mock.patch("ui.update_actions.UpdateCheckWorker", _FakeWorker):
            self.assertTrue(self.host.start_update_check())
        self.assertTrue(_FakeWorker.instances[0].started)
        self.assertIn(_FakeWorker.instances[0], self.host._workers)

    def test_auto_check_disabled_in_config(self):
        self.host._cfg.update_check_enabled = False
        with mock.patch("ui.update_actions.UpdateCheckWorker", _FakeWorker):
            self.assertFalse(self.host.start_update_check())
        self.assertEqual(_FakeWorker.instances, [])

    def test_manual_check_ignores_interval_and_switch(self):
        self.host._cfg.update_check_enabled = False
        self.host._cfg.last_update_check = int(time.time())
        with mock.patch("ui.update_actions.UpdateCheckWorker", _FakeWorker):
            self.assertTrue(self.host.start_update_check(manual=True))
        worker = _FakeWorker.instances[0]
        self.assertTrue(worker.started)
        self.assertEqual(worker.url, updater.DEFAULT_MANIFEST_URL)

    def test_second_check_while_worker_running_is_refused(self):
        class Running(_FakeWorker):
            def isRunning(self):
                return True

        first = Running("u", "2.9.0", parent=self.host)
        self.host._update_worker = first
        created_before = len(_FakeWorker.instances)
        with mock.patch("ui.update_actions.UpdateCheckWorker", _FakeWorker):
            self.assertFalse(self.host.start_update_check(manual=True))
        self.assertEqual(len(_FakeWorker.instances), created_before)

    def test_check_result_updates_time(self):
        with mock.patch("ui.update_actions.QMessageBox.information"):
            self.host._on_update_check_done(
                {"ok": True, "newer": False, "info": {"version": "2.7.2"}},
                manual=True,
            )
        self.assertTrue(self.merge.called)
        self.assertIsNotNone(self.host._cfg.last_update_check)

    def test_new_version_opens_dialog(self):
        self.host._on_update_check_done(
            {"ok": True, "newer": True,
             "info": {"version": "2.9.0", "url": "https://rizpaq.ru/a.zip"}},
            manual=False,
        )
        self.assertEqual(self.host.shown[0][0]["version"], "2.9.0")

    def test_skipped_version_hidden_from_auto_but_shown_manually(self):
        self.host._cfg.skipped_version = "2.9.0"
        result = {"ok": True, "newer": True,
                  "info": {"version": "2.9.0", "url": "https://rizpaq.ru/a.zip"}}
        self.host._on_update_check_done(result, manual=False)
        self.assertEqual(self.host.shown, [])
        self.host._on_update_check_done(result, manual=True)
        self.assertEqual(len(self.host.shown), 1)

    def test_check_error_reported_only_manually(self):
        result = {"ok": False, "error": "boom", "newer": False, "info": None}
        with mock.patch("ui.update_actions.QMessageBox.warning") as warning:
            self.host._on_update_check_done(result, manual=False)
            warning.assert_not_called()
            self.host._on_update_check_done(result, manual=True)
            warning.assert_called_once()

    def test_skip_remembers_version(self):
        self.host._on_update_skipped("2.9.0")
        self.assertEqual(self.host._cfg.skipped_version, "2.9.0")
        self.merge.assert_called_with(skipped_version="2.9.0")

    def test_closing_window_ignores_late_result(self):
        self.host._closing = True
        self.host._on_update_check_done(
            {"ok": True, "newer": True,
             "info": {"version": "2.9.0", "url": "https://rizpaq.ru/a.zip"}},
            manual=True,
        )
        self.assertEqual(self.host.shown, [])

    def test_auto_check_switch_is_persisted(self):
        self.host._on_auto_check_changed(False)
        self.merge.assert_called_with(update_check_enabled=False)
        self.assertFalse(self.host._cfg.update_check_enabled)

    def test_install_cancel_discards_download(self):
        from PySide6.QtWidgets import QMessageBox

        dialog = SimpleNamespace(discard_download=mock.Mock())
        with mock.patch("ui.update_actions.updater") as upd, \
                mock.patch.object(
                    QMessageBox, "question",
                    return_value=QMessageBox.StandardButton.No):
            upd.is_frozen.return_value = True
            self.host._install_update(dialog, {"version": "2.8.1"}, "p")
        dialog.discard_download.assert_called_once()


def ui_interval():
    from ui.update_actions import CHECK_INTERVAL_SECONDS

    return CHECK_INTERVAL_SECONDS


                                                                             


class UpdateDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
                                                                    
                                                         
        i18n.set_language("ru", notify=False)

    @classmethod
    def tearDownClass(cls):
        i18n.set_language("en", notify=False)

    def _dialog(self, **overrides):
        info = {
            "version": "2.9.0",
            "url": "https://rizpaq.ru/updates/rizpaq-2.9.0-win64.zip",
            "notes": "Что нового:\nкаталог архивов",
            "sha256": "a" * 64,
            "notes_url": "",
            "published": "2026-11-01",
        }
        info.update(overrides)
        dlg = UpdateDialog(info, "2.7.2", parent=None)
        self.addCleanup(dlg.deleteLater)
        return dlg

    def test_shows_versions_and_notes_as_plain_text(self):
        dlg = self._dialog()
        self.assertIn("2.9.0", dlg.header.text())
        self.assertIn("2.7.2", dlg.version_label.text())
        self.assertEqual(dlg.notes.toPlainText(), "Что нового:\nкаталог архивов")
        self.assertFalse(dlg.notes.openExternalLinks())
        self.assertIn("2026-11-01", dlg.published_label.text())

    def test_published_hidden_when_absent(self):
        dlg = self._dialog(published="")
        other = self._dialog()
                                                                          
                                                                            
        self.assertFalse(dlg.published_label.isVisibleTo(dlg))
        self.assertTrue(other.published_label.isVisibleTo(other))

    def test_warns_when_no_sha256(self):
        dlg = self._dialog(sha256="")
        self.assertIn("SHA256", dlg.warning.text())

    def test_built_app_offers_install(self):
        dlg = self._dialog()
        self.assertEqual(dlg.install_btn.text(), "Скачать и установить")
        self.assertEqual(dlg.warning.text(), "")

    def test_source_run_offers_download_only(self):
        dlg = self._dialog()
        dlg2 = UpdateDialog(
            {"version": "2.9.0", "url": "https://rizpaq.ru/a.zip"},
            "2.7.2", install_supported=False,
        )
        self.addCleanup(dlg2.deleteLater)
        self.assertEqual(dlg2.install_btn.text(), "Скачать")
        self.assertIn("собранной", dlg2.warning.text())
        self.assertEqual(dlg.install_btn.text(), "Скачать и установить")

    def test_later_emits_skip_with_version(self):
        dlg = self._dialog()
        seen = []
        dlg.skip_requested.connect(seen.append)
        dlg._on_later()
        self.assertEqual(seen, ["2.9.0"])

    def test_progress_updates_bar(self):
        dlg = self._dialog()
        dlg._on_progress({"read": 500, "total": 1000, "percent": 50})
        self.assertEqual(dlg.progress.value(), 50)
        dlg._on_progress({"read": 700, "total": 0, "percent": 0})
        self.assertEqual(dlg.progress.minimum(), 0)
        self.assertEqual(dlg.progress.maximum(), 0)                        

    def test_download_error_is_shown_and_buttons_restored(self):
        dlg = self._dialog()
        dlg.install_btn.setEnabled(False)
        with mock.patch("ui.update_dialog.QMessageBox.warning") as warning:
            dlg._on_download_done({"ok": False, "error": "boom"})
        warning.assert_called_once()
        self.assertTrue(dlg.install_btn.isEnabled())
        self.assertTrue(dlg.later_btn.isEnabled())

    def test_discard_download_removes_temp_dir(self):
        dlg = self._dialog()
        temp = Path(tempfile.mkdtemp(prefix="rizpaq_upd_disc_"))
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        dlg._download_dir = str(temp)
        dlg.discard_download()
        self.assertFalse(temp.exists())
        self.assertEqual(dlg.download_dir(), "")


                                                                            


class IntegrationTests(unittest.TestCase):
    def test_main_starts_background_check_after_show(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        show = source.index("window = MainWindow()")
        check = source.index("start_update_check", show)
        self.assertGreater(check, show)
        self.assertIn("QTimer.singleShot(1500, window.start_update_check)",
                      source)
                                                                 
        headless = (ROOT / "core" / "headless.py").read_text(encoding="utf-8")
        self.assertNotIn("start_update_check", headless)

    def test_help_menu_has_manual_check(self):
        source = (ROOT / "ui" / "menu_actions.py").read_text(encoding="utf-8")
        self.assertIn('tr("menu.help.check_updates")', source)
        self.assertIn("_on_check_updates", source)
        self.assertIn("start_update_check(manual=True)", source)

    def test_main_window_mixes_update_actions(self):
        source = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertIn("from ui.update_actions import UpdateActionsMixin", source)
        self.assertIn("UpdateActionsMixin,", source)

    def test_locales_have_all_update_keys_with_placeholders(self):
        base = json.loads(
            (ROOT / "locales" / "en.json").read_text(encoding="utf-8")
        )["strings"]
        keys = [k for k in base if k.startswith("update.")]
        self.assertGreaterEqual(len(keys), 20)
        self.assertIn("menu.help.check_updates", base)

        import re

        def placeholders(text):
            return set(re.findall(r"\{[a-z_]+\}", text))

        for code in ALL_LANGS:
            data = json.loads(
                (ROOT / "locales" / f"{code}.json").read_text(encoding="utf-8")
            )["strings"]
            for key in keys + ["menu.help.check_updates"]:
                self.assertIn(key, data, f"{code}: нет ключа {key}")
                self.assertEqual(
                    placeholders(data[key]), placeholders(base[key]),
                    f"{code}: плейсхолдеры не совпадают в {key}",
                )
                self.assertTrue(data[key].strip(), f"{code}: пустой {key}")

    def test_russian_strings_are_russian(self):
        ru = json.loads(
            (ROOT / "locales" / "ru.json").read_text(encoding="utf-8")
        )["strings"]
        self.assertIn("обновлен", ru["update.checking"].lower())
        self.assertIn("скача", ru["update.install"].lower())
        self.assertIn("версия", ru["update.available"].lower())

    def test_config_fields_are_parsed_and_defaulted(self):
        defaults = config_mod._from_dict({})
        self.assertTrue(defaults.update_check_enabled)
        self.assertIsNone(defaults.update_url)
        self.assertIsNone(defaults.last_update_check)
        self.assertIsNone(defaults.skipped_version)

        parsed = config_mod._from_dict({
            "update_url": "https://mirror.example/latest.json",
            "update_check_enabled": False,
            "last_update_check": 1700000000,
            "skipped_version": "2.9.0",
        })
        self.assertEqual(parsed.update_url,
                         "https://mirror.example/latest.json")
        self.assertFalse(parsed.update_check_enabled)
        self.assertEqual(parsed.last_update_check, 1700000000)
        self.assertEqual(parsed.skipped_version, "2.9.0")


if __name__ == "__main__":
    unittest.main()
