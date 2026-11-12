                       


















from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config as config_mod
from core import notify as N


def _settings(mode="off", token="token", chat="42"):
    return SimpleNamespace(
        notify_mode=mode,
        notify_telegram_token=token,
        notify_telegram_chat_id=chat,
    )


class _Resp:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _NotifyTest(unittest.TestCase):
    def setUp(self):
        N._strings_cache.clear()
        patcher = mock.patch.object(N, "current_language", return_value="en")
        patcher.start()
        self.addCleanup(patcher.stop)
                                                                    
        pause = mock.patch.object(N, "_RETRY_PAUSE", 0.0)
        pause.start()
        self.addCleanup(pause.stop)
                                                                      
                                                                   
        log_patcher = mock.patch.object(N, "_log_failure")
        self.log_failure = log_patcher.start()
        self.addCleanup(log_patcher.stop)


class TestShouldNotify(unittest.TestCase):
    def test_off_never(self):
        for status in ("ok", "error", "busy", ""):
            with self.subTest(status=status):
                self.assertFalse(N.should_notify("off", status))

    def test_errors_only_error(self):
        self.assertTrue(N.should_notify("errors", "error"))
        self.assertFalse(N.should_notify("errors", "ok"))
        self.assertFalse(N.should_notify("errors", "busy"))

    def test_all_ok_and_error(self):
        self.assertTrue(N.should_notify("all", "ok"))
        self.assertTrue(N.should_notify("all", "error"))

    def test_busy_never_notified(self):
        pass
        self.assertFalse(N.should_notify("all", "busy"))

    def test_unknown_mode_and_status(self):
        self.assertFalse(N.should_notify("weird", "ok"))
        self.assertFalse(N.should_notify("all", "weird"))
        self.assertFalse(N.should_notify(None, None))

    def test_mode_and_status_case_insensitive(self):
        self.assertTrue(N.should_notify("ALL", "OK"))
        self.assertTrue(N.should_notify(" errors ", " error "))


class TestFormatJobMessage(_NotifyTest):
    def test_ok_message_contains_fields(self):
        text = N.format_job_message(
            "Документы",
            "Ночной бэкап",
            "ok",
            archive=r"D:\arc\docs.zpaq",
            when=datetime(2026, 11, 12, 9, 5),
        )
        self.assertIn("[Rizpaq] Job completed", text)
        self.assertIn("Work: Документы", text)
        self.assertIn("Job: Ночной бэкап", text)
        self.assertIn(r"Archive: D:\arc\docs.zpaq", text)
        self.assertIn("Time: 12.11.2026 09:05", text)
        self.assertNotIn("Reason:", text)

    def test_error_message_has_title_and_reason(self):
        text = N.format_job_message(
            "Работа", "Проверка", "error", reason="par2_missing"
        )
        self.assertIn("[Rizpaq] Job failed", text)
        self.assertIn("Reason: set not created", text)

    def test_unknown_reason_is_shown_as_token(self):
        text = N.format_job_message("W", "J", "error", reason="future_reason")
        self.assertIn("Reason: future_reason", text)

    def test_empty_optional_fields_are_omitted(self):
        text = N.format_job_message("", "", "ok")
        self.assertNotIn("Work:", text)
        self.assertNotIn("Job:", text)
        self.assertNotIn("Archive:", text)

    def test_message_is_bounded(self):
        text = N.format_job_message("W" * 10000, "J", "ok")
        self.assertLessEqual(len(text), N._MAX_TEXT)
        self.assertTrue(text.endswith("…"))

    def test_time_format_is_day_month_year(self):
        text = N.format_job_message(
            "W", "J", "ok", when=datetime(2026, 1, 2, 3, 4)
        )
        self.assertIn("02.01.2026 03:04", text)


class TestSendTelegram(_NotifyTest):
    def test_success_builds_expected_request(self):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["request"] = request
            captured["timeout"] = timeout
            return _Resp(200)

        with mock.patch.object(N.urllib.request, "urlopen", fake_urlopen):
            ok = N.send_telegram("TOKEN", "123", "hello")

        self.assertTrue(ok)
        request = captured["request"]
        self.assertEqual(
            request.full_url,
            "https://api.telegram.org/botTOKEN/sendMessage",
        )
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["chat_id"], "123")
        self.assertEqual(payload["text"], "hello")
        self.assertTrue(payload["disable_web_page_preview"])
        self.assertEqual(captured["timeout"], N._TIMEOUT)

    def test_network_error_returns_false(self):
        pass
        with mock.patch.object(
            N.urllib.request,
            "urlopen",
            side_effect=OSError("no network"),
        ) as urlopen:
            self.assertFalse(N.send_telegram("T", "1", "text"))
        self.assertEqual(urlopen.call_count, N._RETRY_COUNT)

    def test_network_error_then_success(self):
        pass
        calls = []

        def flaky(request, timeout=None):
            calls.append(request)
            if len(calls) < 3:
                raise OSError("connection reset")
            return _Resp(200)

        with mock.patch.object(N.urllib.request, "urlopen", flaky):
            self.assertTrue(N.send_telegram("T", "1", "text"))
        self.assertEqual(len(calls), 3)

    def test_http_error_returns_false(self):
        error = urllib.error.HTTPError(
            "https://api.telegram.org", 401, "Unauthorized", {}, None
        )
        with mock.patch.object(
            N.urllib.request, "urlopen", side_effect=error
        ) as urlopen:
            self.assertFalse(N.send_telegram("T", "1", "text"))
                                                               
        self.assertEqual(urlopen.call_count, 1)

    def test_too_many_requests_is_retried(self):
        pass
        error = urllib.error.HTTPError(
            "https://api.telegram.org", 429, "Too Many Requests", {}, None
        )
        with mock.patch.object(
            N.urllib.request, "urlopen", side_effect=error
        ) as urlopen:
            self.assertFalse(N.send_telegram("T", "1", "text"))
        self.assertEqual(urlopen.call_count, N._RETRY_COUNT)

    def test_failure_reason_is_logged(self):
        pass
        error = urllib.error.HTTPError(
            "https://api.telegram.org", 400, "Bad Request", {}, None
        )
        with mock.patch.object(
            N.urllib.request, "urlopen", side_effect=error
        ):
            self.assertFalse(N.send_telegram("T", "1", "text"))
        self.assertTrue(self.log_failure.called)
        text = self.log_failure.call_args[0][0]
        self.assertIn("400", text)

    def test_http_status_500_returns_false(self):
        with mock.patch.object(
            N.urllib.request, "urlopen", return_value=_Resp(500)
        ):
            self.assertFalse(N.send_telegram("T", "1", "text"))

    def test_invalid_arguments_do_not_hit_network(self):
        with mock.patch.object(N.urllib.request, "urlopen") as urlopen:
            self.assertFalse(N.send_telegram("", "1", "text"))
            self.assertFalse(N.send_telegram("T", "", "text"))
            self.assertFalse(N.send_telegram("T", "1", ""))
            urlopen.assert_not_called()

    def test_token_and_chat_are_stripped(self):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["request"] = request
            return _Resp(200)

        with mock.patch.object(N.urllib.request, "urlopen", fake_urlopen):
            self.assertTrue(N.send_telegram("  T  ", "  1  ", "x"))

        payload = json.loads(captured["request"].data.decode("utf-8"))
        self.assertEqual(payload["chat_id"], "1")
        self.assertIn("/botT/sendMessage", captured["request"].full_url)


class TestNotifyJob(_NotifyTest):
    def _work_job(self):
        return (
            {"title": "Работа", "dest": r"D:\arc\w.zpaq"},
            {"title": "Задание"},
        )

    def test_off_mode_does_not_send(self):
        work, job = self._work_job()
        with mock.patch.object(N, "send_telegram") as send:
            self.assertFalse(
                N.notify_job(_settings("off"), work, job, "error")
            )
            send.assert_not_called()

    def test_errors_mode_skips_ok(self):
        work, job = self._work_job()
        with mock.patch.object(N, "send_telegram") as send:
            self.assertFalse(
                N.notify_job(_settings("errors"), work, job, "ok")
            )
            send.assert_not_called()

    def test_errors_mode_sends_error(self):
        work, job = self._work_job()
        with mock.patch.object(
            N, "send_telegram", return_value=True
        ) as send:
            self.assertTrue(
                N.notify_job(
                    _settings("errors"), work, job, "error",
                    reason="par2_missing",
                )
            )
        args = send.call_args[0]
        self.assertEqual(args[0], "token")
        self.assertEqual(args[1], "42")
        self.assertIn("[Rizpaq] Job failed", args[2])
        self.assertIn("Reason: set not created", args[2])

    def test_all_mode_sends_ok(self):
        work, job = self._work_job()
        with mock.patch.object(
            N, "send_telegram", return_value=True
        ) as send:
            self.assertTrue(
                N.notify_job(_settings("all"), work, job, "ok")
            )
        send.assert_called_once()

    def test_missing_token_or_chat_does_not_send(self):
        work, job = self._work_job()
        for token, chat in (("", "42"), ("token", ""), (" ", " ")):
            with self.subTest(token=token, chat=chat):
                with mock.patch.object(N, "send_telegram") as send:
                    self.assertFalse(
                        N.notify_job(
                            _settings("all", token, chat), work, job, "ok"
                        )
                    )
                    send.assert_not_called()

    def test_archive_defaults_to_work_dest(self):
        work, job = self._work_job()
        with mock.patch.object(
            N, "send_telegram", return_value=True
        ) as send:
            N.notify_job(_settings("all"), work, job, "ok")
        self.assertIn(r"Archive: D:\arc\w.zpaq", send.call_args[0][2])

    def test_explicit_archive_wins(self):
        work, job = self._work_job()
        with mock.patch.object(
            N, "send_telegram", return_value=True
        ) as send:
            N.notify_job(
                _settings("all"), work, job, "ok", archive=r"E:\other.zpaq"
            )
        self.assertIn(r"Archive: E:\other.zpaq", send.call_args[0][2])

    def test_send_failure_is_returned(self):
        work, job = self._work_job()
        with mock.patch.object(N, "send_telegram", return_value=False):
            self.assertFalse(
                N.notify_job(_settings("all"), work, job, "ok")
            )


class TestNotifyJobAsync(_NotifyTest):
    def test_off_mode_does_not_start_thread(self):
        with mock.patch.object(N.threading, "Thread") as thread:
            self.assertFalse(
                N.notify_job_async(
                    _settings("off"), {}, {}, "error"
                )
            )
            thread.assert_not_called()

    def test_start_runs_job_in_thread(self):
        called = []

        class _SyncThread:
            def __init__(self, target, args, daemon, name):
                self._target = target
                self._args = args
                self.daemon = daemon
                self.name = name

            def start(self):
                self._target(*self._args)

        with mock.patch.object(
            N.threading, "Thread", _SyncThread
        ), mock.patch.object(
            N, "notify_job", side_effect=lambda *a, **k: called.append(a)
        ):
            ok = N.notify_job_async(
                _settings("all"),
                {"title": "W"},
                {"title": "J"},
                "ok",
            )

        self.assertTrue(ok)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][3], "ok")

    def test_thread_start_failure_returns_false(self):
        with mock.patch.object(
            N.threading, "Thread", side_effect=RuntimeError("no threads")
        ):
            self.assertFalse(
                N.notify_job_async(
                    _settings("all"), {}, {}, "ok"
                )
            )


class TestNotifyConfig(unittest.TestCase):
    def test_defaults(self):
        s = config_mod.Settings()
        self.assertEqual(s.notify_mode, "off")
        self.assertEqual(s.notify_telegram_token, "")
        self.assertEqual(s.notify_telegram_chat_id, "")

    def test_round_trip(self):
        with tempfile.TemporaryDirectory(prefix="notify_cfg_") as tmp:
            path = Path(tmp) / "cfg.json"
            config_mod.update(
                path,
                notify_mode="errors",
                notify_telegram_token="abc",
                notify_telegram_chat_id="123",
            )
            loaded = config_mod.load(path)
            self.assertEqual(loaded.notify_mode, "errors")
            self.assertEqual(loaded.notify_telegram_token, "abc")
            self.assertEqual(loaded.notify_telegram_chat_id, "123")

    def test_mode_is_normalized(self):
        with tempfile.TemporaryDirectory(prefix="notify_cfg_") as tmp:
            path = Path(tmp) / "cfg.json"
            path.write_text(
                json.dumps({"notify_mode": " ALL "}), encoding="utf-8"
            )
            self.assertEqual(config_mod.load(path).notify_mode, "all")

    def test_unknown_mode_becomes_off(self):
        with tempfile.TemporaryDirectory(prefix="notify_cfg_") as tmp:
            path = Path(tmp) / "cfg.json"
            path.write_text(
                json.dumps({"notify_mode": "everything"}),
                encoding="utf-8",
            )
            self.assertEqual(config_mod.load(path).notify_mode, "off")

    def test_old_config_without_fields(self):
        with tempfile.TemporaryDirectory(prefix="notify_cfg_") as tmp:
            path = Path(tmp) / "cfg.json"
            path.write_text(json.dumps({"zpaq_path": "x"}), encoding="utf-8")
            loaded = config_mod.load(path)
            self.assertEqual(loaded.notify_mode, "off")
            self.assertEqual(loaded.notify_telegram_token, "")
            self.assertEqual(loaded.notify_telegram_chat_id, "")

    def test_blank_strings_become_empty(self):
        with tempfile.TemporaryDirectory(prefix="notify_cfg_") as tmp:
            path = Path(tmp) / "cfg.json"
            path.write_text(
                json.dumps({
                    "notify_telegram_token": "   ",
                    "notify_telegram_chat_id": "  ",
                }),
                encoding="utf-8",
            )
            loaded = config_mod.load(path)
            self.assertEqual(loaded.notify_telegram_token, "")
            self.assertEqual(loaded.notify_telegram_chat_id, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
