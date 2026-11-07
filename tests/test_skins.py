























from __future__ import annotations

import ast
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui import skins              
from ui.palette import build_palette, build_style              

UI_DIR = ROOT / "ui"
LOCALES = ROOT / "locales"

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

                                                                    
                            
QSS_PSEUDO = {
    "down-arrow", "up-arrow", "left-arrow", "right-arrow",
    "indicator", "section", "item", "chunk", "tab", "close", "float",
    "corner", "separator", "branch", "scroller", "add-line", "sub-line",
    "tear", "handle", "groove", "sunken", "raised", "flat", "menu-arrow",
    "non-exclusive-indicator", "exclusive-indicator", "dialog-button-box",
}

MIN_CONTRAST = 3.0

                                                                    
                                                                       
                                                                           
                               
 
                                            
KNOWN_LOW_CONTRAST = [
    ("soft_azure", "item:selected:hover", 2.96),
]


def _lin(v: float) -> float:
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def _luminance(color: str) -> float:
    c = color.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg: str, bg: str) -> float:
    l1, l2 = _luminance(fg), _luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def ui_files() -> list:
    pass









    return [
        p for p in sorted(UI_DIR.glob("*.py"))
        if p.name not in ("palette.py", "skins.py")
    ]


def qss_template() -> str:
    src = (UI_DIR / "palette.py").read_text(encoding="utf-8")
    t0 = src.index("_STYLE_TEMPLATE")
    t1 = src.index("def build_style")
    return src[t0:t1]


                                                                        
                
                                                                        

class TestSkinRegistry(unittest.TestCase):
    def test_registry_not_empty(self):
        self.assertGreaterEqual(len(skins.skin_names()), 2,
                                "нужен скин по умолчанию и хотя бы один новый")

    def test_default_skin_exists(self):
        self.assertIn(skins.DEFAULT_SKIN, skins.SKINS)

    def test_every_skin_has_all_tokens(self):
        pass
        for name in skins.skin_names():
            with self.subTest(skin=name):
                missing = skins.missing_tokens(name)
                self.assertEqual(
                    missing, [],
                    f"в скине {name} нет токенов: {missing}")

    def test_no_extra_tokens(self):
        pass
        for name in skins.skin_names():
            with self.subTest(skin=name):
                self.assertEqual(
                    skins.extra_tokens(name), [],
                    f"в скине {name} есть токены, которых нет в эталоне")

    def test_all_colors_are_hex(self):
        for name in skins.skin_names():
            for token, value in skins.SKINS[name].items():
                with self.subTest(skin=name, token=token):
                    self.assertRegex(
                        value, HEX_RE,
                        f"{name}/{token} = {value!r} — не цвет #rrggbb")

    def test_soft_azure_is_the_original_palette(self):
        pass






        expected = {
            "WINDOW_BG": "#eef3fa",
            "BASE_BG": "#ffffff",
            "ACCENT": "#2f6db5",
            "TEXT_MAIN": "#26405e",
            "TEXT_HEADER": "#244a78",
            "BORDER": "#c3d2e6",
            "STEEL": "#5d83b1",
            "HEADER_BG": "#5680b0",
            "STATUS_BG": "#5680b0",
            "OK_GREEN": "#2f9e6f",
            "WARN_ORANGE": "#c47a1e",
        }
        for token, value in expected.items():
            with self.subTest(token=token):
                self.assertEqual(skins.SKINS[skins.DEFAULT_SKIN][token], value)


class TestSkinSelection(unittest.TestCase):
    def tearDown(self):
        skins.set_current(skins.DEFAULT_SKIN)

    def test_set_and_read(self):
        for name in skins.skin_names():
            self.assertEqual(skins.set_current(name), name)
            self.assertEqual(skins.current_name(), name)

    def test_unknown_name_is_ignored(self):
        pass
        before = skins.current_name()
        self.assertEqual(skins.set_current("нет_такой_темы"), before)
        self.assertEqual(skins.current_name(), before)

    def test_skin_of_unknown_name_falls_back(self):
        self.assertIn("WINDOW_BG", skins.skin("нет_такой_темы"))

    def test_color_returns_active_skin(self):
        skins.set_current("white_air")
        air = skins.SKINS["white_air"]
        for token in ("ACCENT", "WINDOW_BG", "BORDER"):
            self.assertEqual(skins.color(token), air[token])

    def test_unknown_token_is_loud(self):
        pass






        self.assertEqual(skins.color("ТАКОГО_НЕТ"), "#ff00ff")


                                                                        
                       
                                                                        

class TestStyleBuild(unittest.TestCase):
    def test_no_unsubstituted_tokens(self):
        for name in skins.skin_names():
            with self.subTest(skin=name):
                style = build_style(skins.SKINS[name])
                leftover = re.findall(r"\$[a-z_][a-z0-9_]*", style)
                self.assertEqual(
                    leftover, [],
                    f"в QSS скина {name} остались неподставленные токены: "
                    f"{sorted(set(leftover))[:8]}")

    def test_skins_produce_different_styles(self):
        a = build_style(skins.SKINS[skins.skin_names()[0]])
        b = build_style(skins.SKINS[skins.skin_names()[1]])
        self.assertNotEqual(a, b, "скины собираются в одинаковый QSS")

    def test_palette_builds_with_skin_colours(self):
        pass



        from PySide6.QtGui import QPalette

        for name in skins.skin_names():
            with self.subTest(skin=name):
                colors = skins.SKINS[name]
                pal = build_palette(colors)
                self.assertEqual(
                    pal.color(QPalette.Window).name().lower(),
                    colors["WINDOW_BG"].lower(),
                    "роль Window в палитре не совпала со скином")
                self.assertEqual(
                    pal.color(QPalette.Highlight).name().lower(),
                    colors["ACCENT"].lower(),
                    "роль Highlight в палитре не совпала со скином")

    def test_template_has_no_literal_colors(self):
        pass





        tpl = qss_template()
        for match in re.findall(r"#[0-9a-fA-F]{6}", tpl):
            line = tpl[:tpl.find(match)].count("\n") + 1
            with self.subTest(color=match, line=line):
                self.fail(
                    f"в шаблоне QSS есть зашитый цвет {match} (строка {line}); "
                    f"его надо вынести в токен скина")

    def test_every_template_token_exists_in_skins(self):
        tpl = qss_template()
        used = {t.lower() for t in re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", tpl)}
        available = {t.lower() for t in skins.SKINS[skins.DEFAULT_SKIN]}
        self.assertEqual(
            used - available, set(),
            "в шаблоне есть токены, которых нет ни в одном скине")


                                                                        
                                          
                                                                        

class TestNoColourBypassesTheme(unittest.TestCase):
    pass











                                                 
     
                                                                    
                                                                     
                                                                  
                                      
    _LITERAL_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}")

                                                                     
                
     
                                                               
                                                                
                                                                      
                                                                         
                                                             
    @staticmethod
    def _setstylesheet_calls(src: str):
        pass
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "setStyleSheet":
                continue
            seg = ast.get_source_segment(src, node)
            if seg is None:
                                                                     
                                                                      
                                                       
                continue
            yield node.lineno, seg

    @staticmethod
    def _color_constructor_calls(src: str):
        pass







        try:
            tree = ast.parse(src)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name != "QColor":
                continue
            if not node.args:
                continue
            first = node.args[0]
            if not isinstance(first, ast.Constant):
                continue
            if not isinstance(first.value, str):
                continue
            seg = ast.get_source_segment(src, node)
            if seg is None:
                continue
            yield node.lineno, seg

    def test_no_hardcoded_colour_in_setstylesheet(self):
        offenders = []
        for path in ui_files():
            src = path.read_text(encoding="utf-8")
            for lineno, seg in self._setstylesheet_calls(src):
                literal = self._LITERAL_COLOR_RE.findall(seg)
                if not literal:
                    continue
                                                                        
                                                                
                if re.search(r"\bcolor\s*\(", seg):
                    continue
                offenders.append(
                    f"{path.name}:{lineno} -> {sorted(set(literal))}")
        self.assertEqual(
            offenders, [],
            "эти вызовы setStyleSheet красят виджет мимо темы, и при смене "
            "скина он останется прежнего цвета:\n    " + "\n    ".join(offenders))

    def test_no_hardcoded_colour_in_qcolor(self):
        pass














        offenders = []
        for path in ui_files():
            src = path.read_text(encoding="utf-8")
            for lineno, seg in self._color_constructor_calls(src):
                if "skin_color" in seg or "skins.color" in seg:
                    continue
                offenders.append(f"{path.name}:{lineno} -> {seg}")
        self.assertEqual(
            offenders, [],
            "QColor с литеральным цветом мимо темы; в коде цвет берётся "
            "из активного скина через skins.color(\"TOKEN\"):\n    "
            + "\n    ".join(offenders))

    def test_no_dead_qss_objectname_rules(self):
        pass





        declared = set()
        for path in sorted(UI_DIR.glob("*.py")):
            for m in re.finditer(
                r'setObjectName\(\s*"([^"]+)"', path.read_text(encoding="utf-8")
            ):
                declared.add(m.group(1))

        tpl = qss_template()
        wanted = set(re.findall(r"#([A-Za-z_][A-Za-z0-9_]*)", tpl))
        dead = sorted(
            w for w in wanted
            if w not in declared and w not in QSS_PSEUDO
        )
        self.assertEqual(
            dead, [],
            f"в QSS есть правила по objectName, которых никто не ставит: "
            f"{dead} — они не срабатывают никогда")

    def test_objectnames_have_rules(self):
        pass




        tpl = qss_template()
        have_rule = set(re.findall(r"#([A-Za-z_][A-Za-z0-9_]*)", tpl))
        skipped = []
        for path in ui_files():
            src = path.read_text(encoding="utf-8")
            for m in re.finditer(r'setObjectName\(\s*"([^"]+)"', src):
                name = m.group(1)
                if name.islower() and name not in have_rule:
                    skipped.append(f"{path.name}: {name}")
        self.assertEqual(
            skipped, [],
            "эти objectName не встречаются в QSS — оформление не применится:\n"
            + "\n".join("    " + s for s in skipped))


                                                                        
           
                                                                        

class TestContrast(unittest.TestCase):
    pass









    RULES = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
    GRAD = re.compile(r"stop:\s*\d+\s*(#[0-9a-fA-F]{6})")

    def _pairs(self, style: str):
        for sel, body in self.RULES.findall(style):
            sel = " ".join(sel.split())
            if not sel or sel.startswith("/*"):
                continue
            bg = None
            if re.search(r"background\s*:\s*(?!none)", body):
                grads = self.GRAD.findall(body)
                if grads:
                    bg = grads[0]
                else:
                    m = re.search(r"background\s*:\s*(#[0-9a-fA-F]{3,8})", body)
                    if m:
                        bg = m.group(1)
            m = re.search(r"(?<!-)color\s*:\s*(#[0-9a-fA-F]{3,8})", body)
            fg = m.group(1) if m else None
            if bg and fg:
                yield sel, fg, bg

    def test_readable_contrast(self):
        for name in skins.skin_names():
            style = build_style(skins.SKINS[name])
            for sel, fg, bg in self._pairs(style):
                if ":disabled" in sel:
                                                                            
                                                                       
                                                
                    continue
                ratio = contrast(fg, bg)
                if any(
                    kn == name and kf in sel and abs(kr - ratio) < 0.02
                    for kn, kf, kr in KNOWN_LOW_CONTRAST
                ):
                    continue
                with self.subTest(skin=name, selector=sel[:60]):
                    self.assertGreaterEqual(
                        ratio, MIN_CONTRAST,
                        f"скин {name}: надпись {fg} на фоне {bg} в правиле "
                        f"«{sel[:60]}» — контраст {ratio:.2f}, надпись "
                        f"нечитаема")

    def test_known_low_contrast_list_is_still_accurate(self):
        pass





        for name in skins.skin_names():
            style = build_style(skins.SKINS[name])
            found = [
                (sel, contrast(fg, bg))
                for sel, fg, bg in self._pairs(style)
                if ":disabled" not in sel
            ]
            for kn, kf, kr in KNOWN_LOW_CONTRAST:
                if kn != name:
                    continue
                still = [
                    (s, r) for s, r in found if kf in s and abs(r - kr) < 0.02
                ]
                with self.subTest(skin=name, selector=kf):
                    self.assertTrue(
                        still,
                        f"место «{kf}», числящееся как известный низкий "
                        f"контраст, больше не низкое — уберите его из "
                        f"KNOWN_LOW_CONTRAST")

    def test_something_actually_checked(self):
        pass
        style = build_style(skins.SKINS[skins.DEFAULT_SKIN])
        pairs = list(self._pairs(style))
        self.assertGreater(
            len(pairs), 10,
            f"разобрано всего {len(pairs)} пар «фон/надпись» — "
            f"разбор QSS перестал работать")


                                                                        
                       
                                                                        

class TestSkinSetting(unittest.TestCase):
    KEYS = ("menu.tools.skin", "status.skin_changed",
            "skin.soft_azure", "skin.white_air")

    def test_config_has_skin_field(self):
        from core.config import Settings

        self.assertTrue(
            hasattr(Settings(), "skin"),
            "в настройках нет поля skin — выбор оформления не сохранится")

    def test_config_roundtrip(self, ):
        import tempfile

        from core.config import load, save, update

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cfg.json"
            update(path, skin="white_air")
            self.assertEqual(load(path).skin, "white_air")

            update(path, skin="soft_azure")
            self.assertEqual(load(path).skin, "soft_azure")

    def test_unknown_skin_in_config_does_not_crash(self):
        pass
        import tempfile

        from core.config import load, update

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cfg.json"
            update(path, skin="skin_from_the_future")
            self.assertEqual(load(path).skin, "skin_from_the_future")

            before = skins.current_name()
            skins.set_current(load(path).skin)
            self.assertEqual(skins.current_name(), before)

    def test_locale_keys_present(self):
        for path in sorted(LOCALES.glob("*.json")):
            strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
            for key in self.KEYS:
                with self.subTest(locale=path.stem, key=key):
                    self.assertIn(key, strings, f"в {path.name} нет ключа {key}")

    def test_locale_keys_have_same_placeholders(self):
        en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))["strings"]
        ref = {k: sorted(re.findall(r"\{(\w+)\}", en[k])) for k in self.KEYS}
        for path in sorted(LOCALES.glob("*.json")):
            if path.stem == "en":
                continue
            strings = json.loads(path.read_text(encoding="utf-8"))["strings"]
            for key in self.KEYS:
                got = sorted(re.findall(r"\{(\w+)\}", strings[key]))
                with self.subTest(locale=path.stem, key=key):
                    self.assertEqual(
                        got, ref[key],
                        f"{path.stem}:{key} — набор плейсхолдеров не тот")


                                                                        
                       
                                                                        

class TestLiveSwitch(unittest.TestCase):
    def test_refresh_theme_replaces_stylesheet(self):
        from PySide6.QtWidgets import QApplication

        from ui.palette import apply_theme, refresh_theme

        app = QApplication.instance() or QApplication([])
        try:
            apply_theme(app, "soft_azure")
            first = app.styleSheet()

            apply_theme(app, "white_air")
            second = app.styleSheet()
            self.assertNotEqual(
                first, second, "смена скина не изменила QSS приложения")

            apply_theme(app, "soft_azure")
            self.assertEqual(
                app.styleSheet(), first,
                "возврат к прежнему скину дал другой QSS")

                                                                        
                                                                          
                                                                            
                                          
            app.setStyleSheet("заведомо сломанный стиль")
            self.assertEqual(refresh_theme(app), skins.current_name())
            self.assertNotEqual(
                app.styleSheet(), "заведомо сломанный стиль",
                "refresh_theme вернул имя, но оформление не переприменил")
            self.assertEqual(
                app.styleSheet(), first,
                "refresh_theme пересобрал QSS иначе, чем apply_theme")
        finally:
            apply_theme(app, skins.DEFAULT_SKIN)

    def test_widget_without_own_stylesheet_follows_theme(self):
        pass



        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QApplication, QLabel

        from ui.palette import apply_theme

        app = QApplication.instance() or QApplication([])
        try:
            apply_theme(app, "soft_azure")
            label = QLabel("проверка")
            label.setObjectName("noticeElapsed")                       
            label.setAlignment(Qt.AlignLeft)
            label.resize(260, 40)
            label.show()
            app.processEvents()

            img_azure = label.grab().toImage()
            apply_theme(app, "white_air")
            app.processEvents()
            img_air = label.grab().toImage()

                                                                      
                                                                    
                                                        
            self.assertEqual(
                (img_azure.width(), img_azure.height()),
                (img_air.width(), img_air.height()),
                "размер подписи изменился при смене скина")

                                                                         
                                                                         
            colors_azure = {
                img_azure.pixel(x, y)
                for y in range(img_azure.height())
                for x in range(img_azure.width())
            }
            self.assertGreater(
                len(colors_azure), 1,
                "подпись отрисовалась пустой (один цвет во всём прямоугольнике)"
                " — сравнивать нечего, проверка перекраски ничего не значит")

            diff = sum(
                1
                for y in range(img_azure.height())
                for x in range(img_azure.width())
                if img_azure.pixel(x, y) != img_air.pixel(x, y)
            )
            self.assertGreater(
                diff, 50,
                f"перекрасилось всего {diff} пикселей из "
                f"{img_azure.width() * img_azure.height()} — подпись, скорее "
                f"всего, не следует за темой")
            label.deleteLater()
        finally:
            apply_theme(app, skins.DEFAULT_SKIN)


if __name__ == "__main__":
    unittest.main()
