from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.engine_path import (
    EnginePathError,
    archive_index,
    create_target,
    discard_staging_if_empty,
    drop_substitutes,
    has_non_latin,
    is_zpaq_cmd,
    make_staging,
    move_to_dest,
    needs_staging,
    read_target,
    rewrite_cmd,
    short_path,
    subcommand_of,
)

ZPAQ = "zpaqfranz.exe"
SEVENZIP = r"C:\Program Files\7-Zip\7z.exe"


class Temp(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile

        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_ep_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def archive(self, folder="Резерв", name="backup.zpaq", data=b"x" * 32):
        f = self.dir / folder
        f.mkdir(parents=True, exist_ok=True)
        p = f / name
        p.write_bytes(data)
        return p

    def no_short(self):

        import core.engine_path as ep

        real = ep.short_path
        ep.short_path = lambda p: ""
        self.addCleanup(setattr, ep, "short_path", real)


class TestLatinDetection(unittest.TestCase):
    def test_ascii_is_latin(self):
        self.assertFalse(has_non_latin("C:\\backup\\arc.zpaq"))
        self.assertFalse(has_non_latin("C:/docs/2024/arc.zpaq"))

    def test_cyrillic_is_not_latin(self):
        self.assertTrue(has_non_latin("C:\\Резерв\\backup.zpaq"))
        self.assertTrue(has_non_latin("C:\\docs\\резерв.zpaq"))
        self.assertTrue(has_non_latin("bäckup.zpaq"))

    def test_umlaut_counts(self):

        self.assertTrue(has_non_latin("sicherung\u00e4.rzt"))
        self.assertFalse(has_non_latin("sicherung.rzt"))


class TestEngineDetection(unittest.TestCase):

    def test_zpaq_recognised(self):
        self.assertTrue(is_zpaq_cmd([ZPAQ, "l", "a.zpaq"]))
        self.assertTrue(is_zpaq_cmd(["C:\\tools\\ZPAQFRANZ.EXE", "l", "a"]))
        self.assertTrue(is_zpaq_cmd([r"D:\zpaq_gui\zpaqfranz.exe", "t", "a"]))

    def test_seven_zip_not_recognised(self):
        self.assertFalse(is_zpaq_cmd([SEVENZIP, "x", "a.zip", "-oC:\\out"]))
        self.assertFalse(is_zpaq_cmd(["C:\\Windows\\System32\\cmd.exe"]))

    def test_empty_command(self):
        self.assertFalse(is_zpaq_cmd([]))
        self.assertFalse(is_zpaq_cmd([None]))

    def test_seven_zip_command_untouched(self):
        cmd = [SEVENZIP, "x", str(self_dir() / "Резерв" / "архив.zip"),
               f"-o{self_dir() / 'Итог'}", "-sccUTF-8", "-y"]
        out, cwd, subs = rewrite_cmd(cmd)
        self.assertEqual(out, cmd, "команда 7-Zip изменена")
        self.assertIsNone(cwd)
        self.assertEqual(subs, [])

    def test_python_stand_in_not_recognised(self):
        cmd = [sys.executable, "-u", "child.py", str(self_dir() / "Резерв"
                                                    / "a.zpaq")]
        out, cwd, subs = rewrite_cmd(cmd)
        self.assertEqual(out, cmd)
        self.assertIsNone(cwd)
        self.assertEqual(subs, [])


def self_dir():
    import tempfile

    return Path(tempfile.gettempdir())


class TestCommandShape(unittest.TestCase):


    def test_subcommand(self):
        self.assertEqual(subcommand_of([ZPAQ, "l", "a.zpaq"]), "l")
        self.assertEqual(subcommand_of([ZPAQ, "X", "a.zpaq"]), "x")
        self.assertEqual(subcommand_of([ZPAQ, "a", "out.zpaq", "f.txt"]), "a")

    def test_archive_index(self):
        self.assertEqual(archive_index([ZPAQ, "l", "a.zpaq"]), 2)
        self.assertEqual(archive_index([ZPAQ, "x", "a.zpaq", "in.txt"]), 2)
        self.assertEqual(
            archive_index([ZPAQ, "a", "out.zpaq", "f1", "f2"]), 2)

    def test_global_flag_before_subcommand(self):

        self.assertEqual(archive_index([ZPAQ, "-quiet", "l", "a.zpaq"]), 3)

    def test_no_archive(self):
        self.assertEqual(archive_index([ZPAQ, "l"]), -1)
        self.assertEqual(archive_index([ZPAQ, "-h"]), -1)


class TestReadExistingArchive(Temp):

    def test_latin_path_untouched(self):
        arc = self.archive("lat")
        out, cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertEqual(out, [ZPAQ, "l", str(arc)])
        self.assertIsNone(cwd)
        self.assertEqual(subs, [])

    def test_existing_latin_path_untouched(self):
        arc = self.archive("lat")
        arg, cwd, _subs = read_target(str(arc))
        self.assertEqual(arg, str(arc))
        self.assertIsNone(cwd)

    def test_russian_folder_makes_argument_latin(self):
        arc = self.archive("Резерв")
        out, cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        arg = out[2]
        self.assertFalse(has_non_latin(arg), f"нелатинский путь ушёл: {arg}")
        self.assertEqual(subs, [])

    def test_russian_name_uses_short_or_cwd(self):
        arc = self.archive("lat2", name="бэкап.zpaq")
        out, cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertFalse(has_non_latin(out[2]), f"нелатинское имя: {out[2]}")

    def test_both_russian(self):
        arc = self.archive("Мои", name="Архивы")
        out, _cwd, _subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertFalse(has_non_latin(out[2]), f"нелатинское: {out[2]}")

    def test_substitute_when_name_cannot_be_shortened(self):
        self.no_short()
        arc = self.archive("Резерв", name="бэкап.zpaq")
        out, cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])

        self.assertEqual(len(subs), 1, "подмена не сообщена вызывающему")
        self.assertFalse(has_non_latin(out[2]), f"нелатинское: {out[2]}")
        self.assertTrue(os.path.isfile(subs[0]))
        self.assertEqual(
            os.path.getsize(subs[0]), arc.stat().st_size,
            "подмена другого размера — это не тот же файл")


        with open(subs[0], "rb") as fh:
            self.assertEqual(fh.read(4), arc.read_bytes()[:4])

        drop_substitutes(subs)
        self.assertFalse(os.path.exists(subs[0]), "подмена не убрана")

    def test_substitute_uses_hardlink_not_copy(self):
        self.no_short()
        arc = self.archive("Резерв", name="бэкап.zpaq")
        _out, _cwd, subs = rewrite_cmd([ZPAQ, "t", str(arc)])
        if not subs:
            self.skipTest("жёсткая ссылка недоступна на этой файловой системе")
        self.assertEqual(
            os.stat(subs[0]).st_ino, os.stat(arc).st_ino,
            "подмена оказалась копией, а не ссылкой")
        drop_substitutes(subs)

    def test_no_substitute_left_after_drop(self):

        self.no_short()
        arc = self.archive("Резерв", name="бэкап.zpaq")
        _out, _cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        folder = os.path.dirname(subs[0])
        self.assertTrue(os.path.isdir(folder))
        drop_substitutes(subs)
        self.assertFalse(os.path.isdir(folder),
                         "временная папка подмены осталась на диске")

    def test_drop_substitutes_tolerates_misses(self):

        drop_substitutes([str(self.dir / "нет" / "такого.zpaq")])
        drop_substitutes([])
        drop_substitutes(None)

    def test_write_command_never_substitutes(self):
        self.no_short()
        arc = self.archive("Резерв", name="бэкап.zpaq")
        with self.assertRaises(EnginePathError) as ctx:
            rewrite_cmd([ZPAQ, "a", str(arc), "readme.txt"])
        msg = str(ctx.exception)
        self.assertIn("копию", msg.lower() if False else msg)
        self.assertIn("добавленное", msg)

    def test_write_command_with_latin_name_still_works(self):

        self.no_short()
        arc = self.archive("Резерв", name="backup.zpaq")
        out, cwd, subs = rewrite_cmd([ZPAQ, "a", str(arc), "readme.txt"])
        self.assertEqual(out[2], "backup.zpaq")
        self.assertEqual(cwd, str(arc.parent))
        self.assertEqual(subs, [])


class TestSubstituteIsNeverTheRealArchive(Temp):

    def test_short_path_is_not_reported_as_substitute(self):
        arc = self.archive("Резерв")
        _out, _cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertEqual(
            subs, [],
            "короткий путь 8.3 принят за подмену — его удаление снесло бы "
            "настоящий архив")

    def test_cwd_result_is_not_reported_as_substitute(self):
        self.no_short()
        arc = self.archive("Резерв", name="backup.zpaq")
        out, cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertIsNotNone(cwd, "ожидался рабочий каталог")
        self.assertEqual(
            subs, [],
            "приём с рабочим каталогом принят за подмену")

    def test_real_archive_survives_cleanup(self):
        self.no_short()
        arc = self.archive("Резерв", name="бэкап.zpaq")
        original = arc.read_bytes()

        _out, _cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        drop_substitutes(subs)

        self.assertTrue(arc.exists(), "настоящий архив исчез после уборки")
        self.assertEqual(arc.read_bytes(), original, "архив изменился")

    def test_nothing_reported_for_latin_archive(self):

        arc = self.archive("lat")
        _out, _cwd, subs = rewrite_cmd([ZPAQ, "l", str(arc)])
        self.assertEqual(subs, [])


class TestCreateArchive(Temp):

    def test_russian_folder_latin_name(self):
        dest = self.dir / "Новый" / "backup.zpaq"
        out, cwd, subs = rewrite_cmd([ZPAQ, "a", str(dest), "readme.txt"])
        self.assertEqual(out[2], "backup.zpaq")
        self.assertEqual(cwd, str(dest.parent))
        self.assertEqual(subs, [])

    def test_russian_folder_russian_name(self):
        dest = self.dir / "Новый" / "архив.zpaq"
        out, cwd, subs = rewrite_cmd([ZPAQ, "a", str(dest), "readme.txt"])
        self.assertEqual(out[2], "архив.zpaq")
        self.assertEqual(cwd, str(dest.parent))
        self.assertEqual(subs, [])

    def test_latin_folder_russian_name(self):
        dest = self.dir / "lat" / "архив.zpaq"
        out, cwd, subs = rewrite_cmd([ZPAQ, "a", str(dest), "readme.txt"])
        self.assertEqual(out[2], str(dest))
        self.assertIsNone(cwd)
        self.assertEqual(subs, [])

    def test_create_target_directly(self):
        dest = self.dir / "Итог" / "backup.zpaq"
        arg, cwd, _subs = create_target(str(dest))
        self.assertEqual(arg, "backup.zpaq")
        self.assertEqual(cwd, str(dest.parent))


class TestStagingIsNotPreexisting(Temp):

    def test_staging_path_does_not_exist(self):
        dest = self.dir / "Итоги" / "итог.txt"
        staged = make_staging(str(dest))
        self.addCleanup(lambda: os.path.isfile(staged) and os.unlink(staged))
        self.assertFalse(
            os.path.exists(staged),
            f"черновик уже существует: {staged} — движок его пропустит")

    def test_staging_path_is_latin(self):
        dest = self.dir / "Итоги" / "итог.txt"
        staged = make_staging(str(dest))
        self.addCleanup(lambda: os.path.isfile(staged) and os.unlink(staged))
        self.assertFalse(
            has_non_latin(staged),
            f"путь черновика нелатинский, движок его не примет: {staged}")

    def test_staging_names_differ(self):

        dest = self.dir / "Итоги" / "итог.txt"
        made = [make_staging(str(dest)) for _ in range(3)]
        for p in made:
            self.addCleanup(lambda q=p: os.path.isfile(q) and os.unlink(q))
        self.assertEqual(len(set(made)), 3, f"имена повторились: {made}")

    def test_needs_staging_only_for_nonlatin_folder(self):
        self.assertFalse(needs_staging(str(self.dir / "lat" / "итог.txt")))
        self.assertFalse(needs_staging(str(self.dir / "lat" / "out.txt")))
        self.assertTrue(needs_staging(str(self.dir / "Итоги" / "out.txt")))
        self.assertTrue(needs_staging(str(self.dir / "Итоги" / "итог.txt")))


class TestEmptyStagingCleanup(Temp):

    def test_empty_file_removed(self):
        p = self.dir / "черновик.tmp"
        p.write_bytes(b"")
        self.assertTrue(discard_staging_if_empty(str(p)))
        self.assertFalse(p.exists())

    def test_nonempty_file_kept(self):
        p = self.dir / "черновик.tmp"
        p.write_text("ценные данные", encoding="utf-8")
        self.assertFalse(
            discard_staging_if_empty(str(p)),
            "непустой черновик убран — это потеря данных")
        self.assertTrue(p.exists(), "непустой черновик исчез с диска")

    def test_empty_folder_removed(self):
        d = self.dir / "каталог_черновика"
        d.mkdir()
        self.assertTrue(discard_staging_if_empty(str(d)))
        self.assertFalse(d.exists())

    def test_nonempty_folder_kept(self):
        d = self.dir / "каталог_черновика"
        d.mkdir()
        (d / "файл.txt").write_text("данные", encoding="utf-8")
        self.assertFalse(discard_staging_if_empty(str(d)))
        self.assertTrue(d.exists())

    def test_missing_path_tolerated(self):
        self.assertFalse(discard_staging_if_empty(str(self.dir / "нет")))
        self.assertFalse(discard_staging_if_empty(""))
        self.assertFalse(discard_staging_if_empty(None))


class TestOtherArgumentsUntouched(Temp):

    def setUp(self):
        super().setUp()
        self.arc = self.archive("Резерв")

    def test_destination_folder_not_rewritten(self):
        for dest in (self.dir / "Документы", self.dir / "Новая папка"):
            out, _cwd, _subs = rewrite_cmd(
                [ZPAQ, "x", str(self.arc), "-to", str(dest)]
            )
            self.assertIn(str(dest), out, f"папка {dest.name} тронута")

    def test_existing_folder_left_alone(self):
        folder = self.dir / "Резерв"
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "x", str(self.arc), "-to", str(folder)]
        )
        self.assertIn(str(folder), out)

    def test_mask_never_touched(self):
        existing = self.archive("Резерв", name="маска.zpaq")
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "x", str(self.arc), "-only", str(existing)]
        )
        self.assertIn(str(existing), out,
                      "маска -only была переписана")
        self.assertNotIn(str(self.arc), out,
                         "архив не переписан, хотя путь нелатинский")

    def test_non_latin_mask_survives(self):
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "x", str(self.arc), "-only", "Проект/*"]
        )
        self.assertIn("Проект/*", out)

    def test_password_never_touched(self):
        pwd_file = self.archive("Резерв", name="пароль")
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "x", str(self.arc), "-key", str(pwd_file)]
        )
        self.assertIn(str(pwd_file), out, "пароль был переписан")

    def test_russian_password_survives(self):

        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "x", str(self.arc), "-key", "секрет"]
        )
        self.assertIn("секрет", out)

    def test_sources_not_touched(self):
        src = self.archive("Мои", name="Документ.txt")
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "a", str(self.dir / "lat_out.zpaq"), str(src)]
        )
        self.assertIn(str(src), out, "исходник был переписан")

    def test_flags_survive(self):
        out, _cwd, _subs = rewrite_cmd(
            [ZPAQ, "l", str(self.arc), "-all", "-terse", "-utf"]
        )
        for f in ("-all", "-terse", "-utf"):
            self.assertIn(f, out, f"флаг {f} исчез из команды")

    def test_command_length_preserved(self):

        cmd = [ZPAQ, "x", str(self.arc), "-to", str(self.dir / "out"),
               "-noeta", "-force"]
        out, _cwd, _subs = rewrite_cmd(cmd)
        self.assertEqual(len(out), len(cmd),
                         f"число аргументов изменилось: {len(cmd)} -> "
                         f"{len(out)}")

    def test_latin_command_untouched(self):
        cmd = [ZPAQ, "l", "C:\\docs\\arc.zpaq", "-all"]
        out, cwd, subs = rewrite_cmd(cmd)
        self.assertEqual(out, cmd)
        self.assertIsNone(cwd)
        self.assertEqual(subs, [])


class TestShortPath(Temp):
    def test_short_path_can_shorten_a_latin_path(self):
        p = self.archive("lat")
        self.assertTrue(
            short_path(str(p)) != str(p) or len(str(p)) < 40,
            "ожидалось, что длинный путь сократится")

    def test_latin_path_is_not_shortened_for_the_engine(self):
        p = self.archive("lat")
        arg, cwd, _subs = read_target(str(p))
        self.assertEqual(arg, str(p))
        self.assertIsNone(cwd)

    def test_non_windows_returns_empty(self):
        real = os.name
        try:
            import core.engine_path as ep

            ep.os.name = "posix"
            self.assertEqual(short_path(r"C:\x\y.zpaq"), "")
        finally:
            ep.os.name = real


if __name__ == "__main__":
    unittest.main()
