# -*- mode: python ; coding: utf-8 -*-
"""
Сборка Rizpaq через PyInstaller в режиме onedir.

Что подкладывается внутрь пакета:
- app.ico       → иконка приложения;
- zpaqfranz.exe → движок архиватора рядом с программой;
- 7z.exe        → движок 7-Zip для работы с ZIP/7z/RAR;
- 7z.dll        → библиотека кодеков 7-Zip (нужна для RAR и других форматов);
- locales       → папка переводов (пользователь может добавлять свои языки);
- help/ru, help/en → руководство пользователя (HTML-файлы, открываются
  браузером по умолчанию; см. core/help_docs.py и doc/BUILD.md).

После сборки раздавать нужно всю папку dist\\Rizpaq, а не один exe.

ПРО SQLITE3.
Модуль `sqlite3` — стандартный для Python, PyInstaller подхватывает
его из статического анализа импортов (core/archive_index.py). Для
sqlite3 у PyInstaller есть встроенный hook, который на Windows
дополнительно упаковывает `_sqlite3.pyd` (и, если нужно, sqlite3.dll).
Явная запись в `hiddenimports` добавлена не как «страховка от
поломки», а чтобы при будущем рефакторинге не потерять зависимость:
если кто-нибудь уберёт из кода единственный `import sqlite3` или
сменит схему импорта на динамический, PyInstaller всё равно соберёт
модуль.
"""
from pathlib import Path

root = Path(SPECPATH).resolve()

icon_path = root / "app.ico"
zpaq_path = root / "zpaqfranz.exe"
seven_zip_exe = root / "7z.exe"
seven_zip_dll = root / "7z.dll"
par2_exe = root / "par2.exe"
locales_path = root / "locales"

datas = []

if icon_path.exists():
    datas.append((str(icon_path), "."))

if zpaq_path.exists():
    datas.append((str(zpaq_path), "."))

if seven_zip_exe.exists():
    datas.append((str(seven_zip_exe), "."))

if seven_zip_dll.exists():
    datas.append((str(seven_zip_dll), "."))

# par2.exe — движок создания и проверки наборов восстановления (2.6.0).
# Кладётся тем же способом, что и остальные движки. Если файла нет,
# сборка не падает: PAR2 просто не найдётся при работе, и набор не
# создастся — об этом сообщает core.par2_ops.find_par2.
if par2_exe.exists():
    datas.append((str(par2_exe), "."))

if locales_path.is_dir():
    datas.append((str(locales_path), "locales"))

# Руководство пользователя: HTML-файлы doc/<lang>/ кладутся в
# _internal/help/<lang>/. Программа ищет их там при старте (см.
# core/help_docs.py); если папки нет, открывается онлайн-версия
# https://rizpaq.ru/help/<lang>/. Подробности — в doc/BUILD.md.
for _lang in ("ru", "en"):
    _help_dir = root / "doc" / _lang
    if _help_dir.is_dir() and (_help_dir / "index.html").is_file():
        datas.append((str(_help_dir), f"help/{_lang}"))

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    # Явные импорты для модулей, которые PyInstaller мог бы не заметить.
    # sqlite3 используется в core/archive_index.py — кэш метаданных
    # архивов (2.3.0). Стандартный `import sqlite3` PyInstaller видит,
    # но фиксируем его явно, чтобы связь не потерялась при рефакторинге.
    hiddenimports=["sqlite3"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Rizpaq",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Rizpaq",
)