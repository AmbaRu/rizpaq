




























from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.config as config              
import core.password_store as ps              


class StoreTestBase(unittest.TestCase):
    pass

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_pw_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.path = self.dir / "archive_passwords.json"

                                                                     
                                                                      
                                    
        self.reports: list = []

        def spy(message, name="password_store.log"):
            self.reports.append(str(message))

        config.write_error_log = spy
        self.addCleanup(
            setattr, config, "write_error_log",
            getattr(config, "write_error_log", spy))

        self._old_path = ps._store_path
        ps._store_path = lambda: self.path
        self.addCleanup(setattr, ps, "_store_path", self._old_path)

                                                                      

    def read_raw(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def store_files(self) -> list:
        pass
        return sorted(
            p for p in self.dir.iterdir()
            if p.is_file() and p != self.path
        )

    def make_corrupt(self) -> None:
        self.path.write_text('{"C:\\\\a.zpaq": "c2VjcmV0"', encoding="utf-8")


class TestBasics(StoreTestBase):
    pass

    def test_set_then_get(self):
        ps.set_password("C:\\a\\arc.zpaq", "секрет")
        self.assertEqual(ps.get_password("C:\\a\\arc.zpaq"), "секрет")

    def test_key_is_normalised(self):
        pass
        ps.set_password("C:\\Docs\\Arc.ZPAQ", "секрет")
        self.assertEqual(ps.get_password("c:\\docs\\arc.zpaq"), "секрет")
        self.assertEqual(ps.get_password("C:\\Docs\\Arc.ZPAQ"), "секрет")

    def test_missing_returns_none(self):
        self.assertIsNone(ps.get_password("C:\\нет\\такого.zpaq"))

    def test_rewrite_keeps_other_archives(self):
        ps.set_password("C:\\a.zpaq", "первый")
        ps.set_password("C:\\b.zpaq", "второй")
        ps.set_password("C:\\a.zpaq", "изменённый")
        self.assertEqual(ps.get_password("C:\\a.zpaq"), "изменённый")
        self.assertEqual(ps.get_password("C:\\b.zpaq"), "второй")

    def test_removal(self):
        ps.set_password("C:\\a.zpaq", "секрет")
        ps.set_password("C:\\a.zpaq", None)
        self.assertIsNone(ps.get_password("C:\\a.zpaq"))

    def test_password_not_stored_in_clear(self):
        ps.set_password("C:\\a.zpaq", "оченьсекретныйпароль")
        self.assertNotIn("оченьсекретныйпароль", self.read_raw())

    def test_survives_reload(self):
        ps.set_password("C:\\a.zpaq", "секрет")
        self.assertEqual(ps.get_password("C:\\a.zpaq"), "секрет")

    def test_file_is_valid_json(self):
        ps.set_password("C:\\a.zpaq", "секрет")
        self.assertIsInstance(json.loads(self.read_raw()), dict)


class TestAtomicWrite(StoreTestBase):
    pass

    def test_no_leftover_files(self):
        pass





        ps.set_password("C:\\a.zpaq", "секрет")
        ps.set_password("C:\\b.zpaq", "ещё")
        self.assertEqual(
            self.store_files(), [],
            f"в каталоге остались лишние файлы: "
            f"{[p.name for p in self.store_files()]}")

    def test_target_not_truncated_before_swap(self):
        pass






        ps.set_password("C:\\a.zpaq", "первый")
        self.assertTrue(self.path.is_file())

        seen: dict = {}
        real_replace = os.replace

        def spy_replace(src, dst, *a, **kw):
            seen["target_intact"] = (
                self.path.is_file() and self.path.stat().st_size > 0)
            seen["source"] = str(src)
            seen["target"] = str(dst)
            return real_replace(src, dst, *a, **kw)

        os.replace = spy_replace
        try:
            ps.set_password("C:\\a.zpaq", "второй")
        finally:
            os.replace = real_replace

        self.assertTrue(
            seen.get("target_intact"),
            "в момент подмены целевой файл уже был пуст или отсутствовал — "
            "значит, запись идёт прямо в него, а не через временный файл")
        self.assertNotEqual(
            seen.get("source"), str(self.path),
            "os.replace вызван с самим целевым файлом, а не с временным")
        self.assertEqual(seen.get("target"), str(self.path))
        self.assertEqual(ps.get_password("C:\\a.zpaq"), "второй")

    def test_failed_write_keeps_previous_data(self):
        pass
        ps.set_password("C:\\a.zpaq", "первый")
        ps.set_password("C:\\b.zpaq", "второй")
        before = self.read_raw()

        real_replace = os.replace

        def boom(*a, **kw):
            raise OSError("диск занят")

        os.replace = boom
        try:
            ps.set_password("C:\\a.zpaq", "третий")
        finally:
            os.replace = real_replace

        self.assertEqual(
            self.read_raw(), before,
            "файл изменился, хотя запись упала — прежние данные потеряны")
        self.assertEqual(ps.get_password("C:\\a.zpaq"), "первый")
        self.assertEqual(ps.get_password("C:\\b.zpaq"), "второй")

    def test_failed_write_is_reported(self):
        pass
        ps.set_password("C:\\a.zpaq", "первый")
        self.reports.clear()

        real_replace = os.replace
        os.replace = lambda *a, **kw: (_ for _ in ()).throw(
            OSError("диск занят"))
        try:
            ps.set_password("C:\\b.zpaq", "второй")
        finally:
            os.replace = real_replace

        self.assertTrue(
            self.reports,
            "сбой записи промолчал: пользователю сказали бы «сохранено», "
            "а пароль не записался бы")

    def test_failed_write_leaves_no_leftovers(self):
        pass
        ps.set_password("C:\\a.zpaq", "первый")
        self.reports.clear()

        real_replace = os.replace
        os.replace = lambda *a, **kw: (_ for _ in ()).throw(
            OSError("диск занят"))
        try:
            ps.set_password("C:\\b.zpaq", "второй")
        finally:
            os.replace = real_replace

        self.assertEqual(
            self.store_files(), [],
            f"после сбойной записи остался мусор: "
            f"{[p.name for p in self.store_files()]}")


class TestCorruptFile(StoreTestBase):
    pass

    def test_read_reports_corruption(self):
        self.make_corrupt()
        self.assertIsNone(ps.get_password("C:\\a.zpaq"))
        self.assertTrue(
            self.reports,
            "повреждение файла не сообщено — это и есть молчаливая потеря")

    def test_read_does_not_touch_the_file(self):
        pass
        self.make_corrupt()
        before = self.read_raw()
        ps.get_password("C:\\a.zpaq")
        self.assertEqual(self.read_raw(), before, "чтение изменило файл")
        self.assertEqual(
            self.store_files(), [],
            "чтение что-то переместило — это не его дело")

    def test_write_heals_the_store(self):
        pass
        self.make_corrupt()
        ps.set_password("C:\\новый.zpaq", "пароль")

        self.assertEqual(
            ps.get_password("C:\\новый.zpaq"), "пароль",
            "после повреждения файла пароль сохранить не удалось")
        self.assertIsInstance(
            json.loads(self.read_raw()), dict,
            "файл остался в нечитаемом виде после сохранения")

    def test_previous_file_not_destroyed(self):
        pass
        self.make_corrupt()
        ps.set_password("C:\\новый.zpaq", "пароль")

        extra = self.store_files()
        self.assertTrue(
            extra,
            "испорченный файл исчез беследно — его содержимое пропало "
            "вместе с ним")
        self.assertEqual(
            extra[0].read_text(encoding="utf-8"),
            '{"C:\\\\a.zpaq": "c2VjcmV0"',
            "отодвинутый файл изменён")

    def test_corruption_reported_on_write_too(self):
        self.make_corrupt()
        self.reports.clear()
        ps.set_password("C:\\новый.zpaq", "пароль")
        self.assertTrue(
            self.reports,
            "при сохранении повреждение не сообщено — потеря останется "
            "незамеченной")

    def test_empty_file_is_not_corruption(self):
        pass
        self.path.write_text("", encoding="utf-8")
        self.assertIsNone(ps.get_password("C:\\a.zpaq"))
        self.assertEqual(self.reports, [],
                         "пустой файл принят за повреждённый")

    def test_wrong_shape_is_reported(self):
        pass
        self.path.write_text("[1, 2, 3]", encoding="utf-8")
        self.assertIsNone(ps.get_password("C:\\a.zpaq"))
        self.assertTrue(self.reports,
                        "неожиданный вид файла не сообщён")

    def test_undecodable_entry_is_reported(self):
        pass





        data = {ps._norm_key("C:\\a.zpaq"): "не-base64-вовсе"}
        self.path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")

        self.assertIsNone(ps.get_password("C:\\a.zpaq"))
        self.assertTrue(
            self.reports,
            "битая запись не сообщена — пароль молча не подставится")

    def test_good_entries_survive_alongside_broken_one(self):
        pass
        key_a = ps._norm_key("C:\\a.zpaq")
        key_b = ps._norm_key("C:\\b.zpaq")
        import base64

        data = {
            key_a: "совсем-не-base64",
            key_b: base64.b64encode("целый".encode("utf-8")).decode("ascii"),
        }
        self.path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(ps.get_password("C:\\b.zpaq"), "целый")
        self.assertIsNone(ps.get_password("C:\\a.zpaq"))
        self.assertTrue(self.reports)


if __name__ == "__main__":
    unittest.main()
