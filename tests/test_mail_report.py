









from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import config as config_mod
from core import mail_report
from core.zpaq_cli import mask_secrets, safe_cmdline


def _mail(**kwargs):
    base = dict(
        enabled=True,
        server="smtp.example.com",
        from_addr="me@example.com",
        to="me@example.com",
    )
    base.update(kwargs)
    return mail_report.MailConfig(**base)


class TestMailConfig(unittest.TestCase):
    def test_default_port_depends_on_tls(self):
        self.assertEqual(_mail(tls="starttls").port_value, 587)
        self.assertEqual(_mail(tls="ssl").port_value, 465)

    def test_explicit_port_wins(self):
        self.assertEqual(_mail(port=2525).port_value, 2525)

    def test_bad_port_and_tls_fall_back(self):
        mail = _mail(port=99999, tls="plain")
        self.assertEqual(mail.port, 0)
        self.assertEqual(mail.tls, "starttls")

    def test_ready_and_missing(self):
        self.assertTrue(_mail().ready())
        self.assertEqual(_mail().missing(), [])
        self.assertFalse(_mail(server="").ready())
        self.assertEqual(_mail(server="", to="").missing(), ["server", "to"])

    def test_disabled_is_not_ready(self):
        self.assertFalse(_mail(enabled=False).ready())


class TestReportArgs(unittest.TestCase):
    def test_starttls_minimal(self):
        args = mail_report.report_args(_mail())
        self.assertEqual(
            args,
            [
                "-mailserver", "smtp.example.com",
                "-mailfrom", "me@example.com",
                "-mailfull", "me@example.com",
            ],
        )
        self.assertNotIn("-mailssl", args)
        self.assertNotIn("-mailport", args)

    def test_ssl_and_explicit_port(self):
        args = mail_report.report_args(
            _mail(tls="ssl", port=2465, user="u", password="pw")
        )
        self.assertIn("-mailssl", args)
        self.assertEqual(args[args.index("-mailport") + 1], "2465")
        self.assertEqual(args[args.index("-mailuser") + 1], "u")
        self.assertEqual(args[args.index("-mailpassword") + 1], "pw")

    def test_user_without_password(self):
        args = mail_report.report_args(_mail(user="u", password=""))
        self.assertIn("-mailuser", args)
        self.assertNotIn("-mailpassword", args)

    def test_customer_from_argument_or_settings(self):
        args = mail_report.report_args(_mail(customer="Job A"), "Job B")
        self.assertEqual(args[args.index("-customer") + 1], "Job B")
        args = mail_report.report_args(_mail(customer="Job A"))
        self.assertEqual(args[args.index("-customer") + 1], "Job A")
        args = mail_report.report_args(_mail())
        self.assertNotIn("-customer", args)

    def test_not_ready_gives_nothing(self):
        self.assertEqual(mail_report.report_args(_mail(enabled=False)), [])
        self.assertEqual(mail_report.report_args(_mail(to="")), [])
        self.assertEqual(mail_report.report_args(_mail(server="")), [])


class TestTestEmailCmd(unittest.TestCase):
    def test_command_shape(self):
        cmd = mail_report.test_email_cmd(
            "zpaqfranz", _mail(password="pw"), "Hello"
        )
        self.assertEqual(cmd[:3], ["zpaqfranz", "work", "email"])
        self.assertIn("-mailto", cmd)
        self.assertIn("-mailsubject", cmd)
        self.assertEqual(cmd[cmd.index("-mailsubject") + 1], "Hello")
        self.assertNotIn("-mailfull", cmd)

    def test_password_masked_in_log(self):
        cmd = mail_report.test_email_cmd(
            "zpaqfranz", _mail(user="u", password="TopSecret"), "x"
        )
        text = safe_cmdline(cmd)
        self.assertNotIn("TopSecret", text)
        self.assertIn("-mailpassword ***", text)

    def test_password_masked_without_archive_password(self):
                                                                   
                                      
        cmd = ["zpaqfranz", "a", "x.zpaq", "-mailpassword", "pw2"]
        self.assertNotIn("pw2", " ".join(mask_secrets(cmd)))


class TestMailFailure(unittest.TestCase):
    OK_WITH_MAIL_FAILURE = (
        "0.015s (00:00:00,1.36MB,OS REPORT 12.09MB) (all OK)\n"
        "97844! e-mail (full log) NOT sent (3, network error): "
        "cannot connect to 127.0.0.1:2525: timeout after 2 s\n"
    )

    def test_detect_english(self):
        self.assertTrue(mail_report.mail_not_sent(self.OK_WITH_MAIL_FAILURE))
        self.assertFalse(mail_report.mail_not_sent("all OK"))
        self.assertFalse(mail_report.mail_not_sent(""))
        self.assertFalse(mail_report.mail_not_sent(None))

    def test_detect_russian(self):
        self.assertTrue(
            mail_report.mail_not_sent("письмо не отправлено: нет сети")
        )

    def test_rc_downgraded_when_only_mail_failed(self):
        self.assertEqual(
            mail_report.effective_rc(1, self.OK_WITH_MAIL_FAILURE, True), 0
        )

    def test_rc_kept_without_mail(self):
        self.assertEqual(
            mail_report.effective_rc(1, self.OK_WITH_MAIL_FAILURE, False), 1
        )

    def test_rc_kept_on_real_damage(self):
        output = self.OK_WITH_MAIL_FAILURE.replace(
            "(all OK)", "(with errors)"
        ) + "01448! VERDICT: 1 file(s) CORRUPTED"
        self.assertEqual(mail_report.effective_rc(1, output, True), 1)

    def test_rc_two_stays_error(self):
        self.assertEqual(
            mail_report.effective_rc(2, self.OK_WITH_MAIL_FAILURE, True), 2
        )


class TestSettingsRoundtrip(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="rizpaq_mail_test_")
        self.path = Path(self._dir) / "cfg.json"

    def tearDown(self):
        import shutil

        shutil.rmtree(self._dir, ignore_errors=True)

    def test_save_and_load(self):
        cfg = config_mod.Settings(
            mail_report_enabled=True,
            mail_smtp_server="smtp.example.com",
            mail_smtp_port=2525,
            mail_smtp_tls="ssl",
            mail_smtp_user="user@example.com",
            mail_smtp_password="pw",
            mail_from="user@example.com",
            mail_to="me@example.com",
            mail_customer="Job",
        )
        config_mod.save(cfg, self.path)
        loaded = config_mod.load(self.path)
        mail = mail_report.from_settings(loaded)
        self.assertTrue(mail.enabled)
        self.assertEqual(mail.server, "smtp.example.com")
        self.assertEqual(mail.port_value, 2525)
        self.assertEqual(mail.tls, "ssl")
        self.assertEqual(mail.password, "pw")
        self.assertEqual(mail.to, "me@example.com")
        self.assertEqual(mail.customer, "Job")

    def test_garbage_values_sanitised(self):
        self.path.write_text(
            '{"mail_report_enabled": true, "mail_smtp_port": 70000, '
            '"mail_smtp_tls": "clear"}',
            encoding="utf-8",
        )
        loaded = config_mod.load(self.path)
        self.assertEqual(loaded.mail_smtp_port, 0)
        self.assertEqual(loaded.mail_smtp_tls, "starttls")

    def test_missing_keys_are_defaults(self):
        self.path.write_text("{}", encoding="utf-8")
        loaded = config_mod.load(self.path)
        self.assertFalse(loaded.mail_report_enabled)
        self.assertEqual(loaded.mail_smtp_tls, "starttls")
        self.assertEqual(loaded.mail_smtp_port, 0)


class TestAddressValidation(unittest.TestCase):
    def test_addresses(self):
        self.assertTrue(mail_report.looks_like_address("a@b.ru"))
        self.assertTrue(mail_report.looks_like_address("user.name@mail.co.uk"))
        self.assertFalse(mail_report.looks_like_address("a@b"))
        self.assertFalse(mail_report.looks_like_address(""))
        self.assertFalse(mail_report.looks_like_address("two@@x.ru"))


class TestHeadlessAppend(unittest.TestCase):
    pass

    def _settings(self, **kwargs):
        cfg = config_mod.Settings(
            mail_report_enabled=True,
            mail_smtp_server="smtp.example.com",
            mail_from="me@example.com",
            mail_to="me@example.com",
        )
        for key, value in kwargs.items():
            setattr(cfg, key, value)
        return cfg

    def test_backup_gets_mail_args(self):
        from core.headless import _append_mail_report

        cmd = ["zpaqfranz", "a", "x.zpaq", "D:/src"]
        with mock.patch("core.config.load", return_value=self._settings()):
            ok = _append_mail_report(
                cmd, "backup", {"title": "Nightly"}, "x.zpaq", {}
            )
        self.assertTrue(ok)
        self.assertIn("-mailfull", cmd)
        self.assertEqual(cmd[cmd.index("-customer") + 1], "Nightly")

    def test_test_action_gets_mail_args(self):
        from core.headless import _append_mail_report

        cmd = ["zpaqfranz", "t", "x.zpaq"]
        with mock.patch("core.config.load", return_value=self._settings()):
            self.assertTrue(
                _append_mail_report(cmd, "test", {}, "x.zpaq", {})
            )

    def test_other_actions_untouched(self):
        from core.headless import _append_mail_report

        for action in ("crop", "sfx", "password", "consolidate", "info"):
            cmd = ["zpaqfranz", action, "x.zpaq"]
            with mock.patch("core.config.load", return_value=self._settings()):
                self.assertFalse(
                    _append_mail_report(cmd, action, {}, "x.zpaq", {})
                )
            self.assertEqual(cmd, ["zpaqfranz", action, "x.zpaq"])

    def test_disabled_adds_nothing(self):
        from core.headless import _append_mail_report

        cmd = ["zpaqfranz", "a", "x.zpaq", "D:/src"]
        cfg = self._settings(mail_report_enabled=False)
        with mock.patch("core.config.load", return_value=cfg):
            self.assertFalse(
                _append_mail_report(cmd, "backup", {}, "x.zpaq", {})
            )
        self.assertEqual(cmd, ["zpaqfranz", "a", "x.zpaq", "D:/src"])

    def test_config_error_does_not_break_job(self):
        from core.headless import _append_mail_report

        cmd = ["zpaqfranz", "a", "x.zpaq", "D:/src"]
        with mock.patch("core.config.load", side_effect=OSError("boom")):
            self.assertFalse(
                _append_mail_report(cmd, "backup", {}, "x.zpaq", {})
            )
        self.assertEqual(cmd, ["zpaqfranz", "a", "x.zpaq", "D:/src"])


class TestUiJobMailArgs(unittest.TestCase):
    pass

    def _stub(self, cfg, container):
        class Stub:
            pass

        stub = Stub()
        stub._cfg = cfg
        stub._load_container = lambda: (container, None)
        return stub

    def _cfg(self, **kwargs):
        values = dict(
            mail_report_enabled=True,
            mail_smtp_server="smtp.example.com",
            mail_from="me@example.com",
            mail_to="me@example.com",
        )
        values.update(kwargs)
        return config_mod.Settings(**values)

    def _method(self):
        from ui.archive_actions import ArchiveActionsMixin

        return ArchiveActionsMixin._job_mail_args

    def test_job_context_adds_mail_with_job_title(self):
        container = {
            "works": [{
                "id": "w1",
                "title": "Work",
                "jobs": [{"id": "j1", "title": "Nightly"}],
            }]
        }
        args = self._method()(
            self._stub(self._cfg(), container),
            {"work_id": "w1", "job_id": "j1"},
            "F:/a.zpaq",
        )
        self.assertIn("-mailfull", args)
        self.assertEqual(args[args.index("-customer") + 1], "Nightly")

    def test_manual_run_without_job_context(self):
        args = self._method()(
            self._stub(self._cfg(), {}),
            None,
            "F:/a.zpaq",
        )
        self.assertEqual(args, [])

    def test_job_without_title_uses_archive_name(self):
        container = {"works": [{"id": "w1", "jobs": [{"id": "j1"}]}]}
        args = self._method()(
            self._stub(self._cfg(), container),
            {"work_id": "w1", "job_id": "j1"},
            "F:/nightly.zpaq",
        )
        self.assertEqual(args[args.index("-customer") + 1], "nightly")

    def test_disabled(self):
        args = self._method()(
            self._stub(
                self._cfg(mail_report_enabled=False), {"works": []}
            ),
            {"work_id": "w1", "job_id": "j1"},
            "F:/a.zpaq",
        )
        self.assertEqual(args, [])

    def test_container_error_is_not_fatal(self):
        class Bad:
            _cfg = None

            def _load_container(self):
                raise OSError("no container")

        with mock.patch("core.config.load", side_effect=OSError("no cfg")):
            args = self._method()(
                Bad(), {"work_id": "w1", "job_id": "j1"}, "F:/a.zpaq"
            )
        self.assertEqual(args, [])


if __name__ == "__main__":
    unittest.main()
