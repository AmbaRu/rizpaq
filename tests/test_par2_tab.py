from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

_APP = QApplication.instance() or QApplication([])
from PySide6.QtGui import QFont
_APP = QApplication.instance()
if _APP is not None:
    _APP.setFont(QFont("Segoe UI", 9))


from ui.i18n import set_language, tr


set_language("ru", str(ROOT / "locales"))

from ui.archive_create_dialog import ArchiveCreateDialog

SRC = ["D:/Данные"]
DEST = r"D:\backup.zpaq"


EXPECTED_KEYS_AUTO = {
    "redundancy", "block_size", "block_count", "recursion", "uniform",
}
EXPECTED_KEYS_MANUAL = {
    "redundancy", "block_size", "recursion", "uniform",
}


def _settings(manual: bool, enabled: bool = True, redundancy: int = 5,
              **extra):
    options = {
        "redundancy": redundancy,
        "block_size": 65536 if manual else None,
        "block_count": None,
        "memory_mb": None,
        "threads": None,
        "recursion": False,
        "uniform": False,
    }
    options.update(extra)
    return {
        "sources": SRC, "dest": DEST, "task_log_mode": "short",
        "action": "backup",
        "par2_enabled": enabled,
        "par2_options": options,
    }


class _TabCase(unittest.TestCase):
    def setUp(self):
        self.dlg = ArchiveCreateDialog(SRC, DEST)

    def tearDown(self):
        self.dlg.deleteLater()

    def enable(self):
        self.dlg._opt_par2.setChecked(True)
        return self.dlg


class TestTabPlacement(_TabCase):


    def _titles(self):
        tabs = self.dlg._tabs
        return [tabs.tabText(i) for i in range(tabs.count())]

    def test_tab_exists(self):
        self.assertIn(tr("create.tab_protection"), self._titles())

    def test_before_advanced(self):
        titles = self._titles()
        prot = titles.index(tr("create.tab_protection"))
        adv = titles.index(tr("create.tab_advanced"))
        self.assertLess(
            prot, adv,
            f"«Защита» должна идти перед «Дополнительно», а не после: "
            f"{titles}",
        )

    def test_no_settings_button_anymore(self):
        self.assertFalse(hasattr(self.dlg, "_on_par2_settings"))


class TestIntroText(_TabCase):


    def _labels(self):
        from PySide6.QtWidgets import QLabel

        return [w.text() for w in self.dlg.findChildren(QLabel)]

    def test_intro_present(self):
        self.assertIn(tr("par2.intro"), self._labels())

    def test_intro_is_short(self):
        text = tr("par2.intro")
        self.assertLess(len(text), 400,
                        "текст в начале вкладки стал слишком длинным")

    def test_limits_note_still_present(self):

        self.assertIn(tr("par2.limits_note"), self._labels())


class TestMasterSwitch(_TabCase):


    def test_fields_on_tab(self):
        for name in ("_par2_redundancy", "_par2_auto_blocks",
                     "_par2_manual_blocks", "_par2_block_size",
                     "_par2_block_count", "_par2_memory", "_par2_threads",
                     "_par2_recursion", "_par2_uniform"):
            self.assertTrue(hasattr(self.dlg, name), f"нет поля {name}")

    def test_group_disabled_but_visible(self):
        self.dlg._opt_par2.setChecked(False)
        self.assertFalse(self.dlg._par2_box.isEnabled(),
                         "поля должны гаснуть при снятой галочке")
        self.assertFalse(self.dlg._par2_box.isHidden(),
                         "поля должны оставаться видимыми, а не прятаться")
        self.assertFalse(self.dlg._par2_redundancy.isHidden())

    def test_group_enabled(self):
        self.dlg._opt_par2.setChecked(True)
        self.assertTrue(self.dlg._par2_box.isEnabled())

    def test_not_clickable_while_disabled(self):
        self.dlg._opt_par2.setChecked(False)
        self.assertFalse(self.dlg._par2_manual_blocks.isEnabled())
        self.dlg._par2_manual_blocks.click()
        self.assertFalse(self.dlg._par2_manual_blocks.isChecked())

        self.dlg._opt_par2.setChecked(True)
        self.dlg._par2_manual_blocks.click()
        self.assertTrue(self.dlg._par2_manual_blocks.isChecked())

    def test_off_toggle_keeps_values_visible(self):
        self.dlg._apply_settings(_settings(True, enabled=True,
                                           redundancy=17))
        self.dlg._opt_par2.setChecked(False)
        self.assertEqual(self.dlg._par2_redundancy.value(), 17)


class TestBlockMode(_TabCase):


    def test_auto_mode_disables_manual_fields(self):
        self.enable()
        self.dlg._par2_auto_blocks.click()
        self.assertFalse(self.dlg._par2_block_size.isEnabled())
        self.assertFalse(self.dlg._par2_block_count.isEnabled())

    def test_manual_mode_enables_fields(self):
        self.enable()
        self.dlg._par2_manual_blocks.click()
        self.assertTrue(self.dlg._par2_block_size.isEnabled())
        self.assertTrue(self.dlg._par2_block_count.isEnabled())

    def test_hints_follow_mode(self):
        self.enable()
        self.dlg._par2_auto_blocks.click()
        self.assertFalse(self.dlg._par2_auto_hint.isHidden())
        self.assertTrue(self.dlg._par2_block_warning.isHidden())

        self.dlg._par2_manual_blocks.click()
        self.assertTrue(self.dlg._par2_auto_hint.isHidden())
        self.assertFalse(self.dlg._par2_block_warning.isHidden())

    def test_auto_collects_no_block_size(self):
        self.enable()
        self.dlg._par2_auto_blocks.click()
        self.assertIsNone(self.dlg._par2_collect()["block_size"])

    def test_manual_collects_block_size(self):
        self.enable()
        self.dlg._par2_manual_blocks.click()
        self.dlg._par2_block_size.setValue(65536)
        self.assertEqual(self.dlg._par2_collect()["block_size"], 65536)

    def test_never_both_size_and_count(self):
        self.enable()
        for manual in (True, False):
            with self.subTest(manual=manual):
                if manual:
                    self.dlg._par2_manual_blocks.click()
                else:
                    self.dlg._par2_auto_blocks.click()
                opts = self.dlg._par2_collect()
                self.assertIsNone(opts.get("block_count"))


class TestCollectApply(_TabCase):


    def _round_trip(self, source):
        self.dlg._apply_settings(source)
        return self.dlg._par2_collect()

    def test_round_trip_auto(self):
        got = self._round_trip(_settings(False, redundancy=9))
        self.assertEqual(got["redundancy"], 9)
        self.assertIsNone(got["block_size"])

    def test_round_trip_manual(self):
        got = self._round_trip(_settings(True, redundancy=9))
        self.assertEqual(got["redundancy"], 9)
        self.assertEqual(got["block_size"], 65536)

    def test_round_trip_full(self):
        source = _settings(True, redundancy=23,
                           memory_mb=256, threads=3,
                           recursion=True, uniform=True)
        got = self._round_trip(source)
        self.assertEqual(got["redundancy"], 23)
        self.assertEqual(got["memory_mb"], 256)
        self.assertEqual(got["threads"], 3)
        self.assertTrue(got["recursion"])
        self.assertTrue(got["uniform"])

    def test_mode_switch_in_same_dialog(self):
        self.dlg._apply_settings(_settings(True))
        self.assertTrue(self.dlg._par2_manual_blocks.isChecked())

        self.dlg._apply_settings(_settings(False))
        self.assertTrue(self.dlg._par2_auto_blocks.isChecked(),
                        "после загрузки авто-режима выбран не тот "
                        "переключатель")
        self.assertFalse(self.dlg._par2_manual_blocks.isChecked())
        self.assertIsNone(self.dlg._par2_collect()["block_size"])

    def test_hints_correct_after_switch(self):

        self.dlg._apply_settings(_settings(True))
        self.dlg._apply_settings(_settings(False))
        self.assertFalse(self.dlg._par2_auto_hint.isHidden())
        self.assertTrue(self.dlg._par2_block_warning.isHidden())
        self.assertFalse(self.dlg._par2_block_size.isEnabled())

    def test_values_shown_when_checkbox_off(self):

        self.dlg._apply_settings(_settings(True, enabled=False,
                                           redundancy=31))
        self.assertEqual(self.dlg._par2_redundancy.value(), 31)
        self.assertFalse(self.dlg._opt_par2.isChecked())
        self.assertFalse(self.dlg._par2_box.isEnabled())

    def test_checkbox_off_omits_options(self):
        self.dlg._apply_settings(_settings(True, enabled=False))
        out = self.dlg._collect_settings()
        self.assertNotIn("par2_options", out)
        self.assertFalse(out["par2_enabled"])

    def test_checkbox_on_sends_options(self):
        self.dlg._apply_settings(_settings(True, enabled=True))
        out = self.dlg._collect_settings()
        self.assertTrue(out["par2_enabled"])
        self.assertIsInstance(out["par2_options"], dict)


class TestOptionKeys(_TabCase):

    def test_auto_keys(self):
        self.enable()
        self.dlg._par2_auto_blocks.click()
        self.assertEqual(set(self.dlg._par2_collect()), EXPECTED_KEYS_AUTO)

    def test_manual_keys(self):
        self.enable()
        self.dlg._par2_manual_blocks.click()
        self.assertEqual(set(self.dlg._par2_collect()),
                         EXPECTED_KEYS_MANUAL)

    def test_zero_means_auto_not_zero(self):
        self.dlg._par2_memory.setValue(0)
        self.dlg._par2_threads.setValue(0)
        opts = self.dlg._par2_collect()
        self.assertNotIn("memory_mb", opts)
        self.assertNotIn("threads", opts)

    def test_zero_shows_auto_in_field(self):

        self.assertEqual(self.dlg._par2_memory.specialValueText(),
                         tr("par2.automatic"))
        self.assertEqual(self.dlg._par2_threads.specialValueText(),
                         tr("par2.automatic"))

    def test_redundancy_minimum_is_one(self):
        self.assertEqual(self.dlg._par2_redundancy.minimum(), 1)


class TestOtherLanguages(_TabCase):


    def test_tab_title_translated(self):
        import io
        import json

        for code in ("en", "de", "fr", "ja", "zh"):
            with self.subTest(lang=code):
                set_language(code, str(ROOT / "locales"))
                data = json.loads(io.open(
                    ROOT / "locales" / f"{code}.json", encoding="utf-8"
                ).read())
                title = data["strings"]["create.tab_protection"]
                self.assertTrue(title.strip(), "название вкладки пустое")
                self.assertNotEqual(
                    title, data["strings"]["create.tab_advanced"],
                    "вкладка «Защита» не переведена, дословно как "
                    "«Дополнительно»",
                )
        set_language("ru", str(ROOT / "locales"))


if __name__ == "__main__":
    unittest.main()
