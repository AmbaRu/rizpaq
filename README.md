# Rizpaq

A simple and beautiful graphical interface for the
[zpaqfranz](https://github.com/corroll/zpaqfranz) archiver.

The convenience of 7-Zip. The power of zpaq. A history of every file.

Create and extract archives by drag and drop, without a single console
command. And zpaq's unique superpower — file versions and deduplication —
becomes a visual "time machine".

## What is it?

Rizpaq is a graphical shell over the console archiver zpaqfranz.
You no longer need to learn complex console commands: all the power of zpaq
is available through a familiar and beautiful interface.

- **Unified tree of drives and archives** — your whole system at a glance
- **File versions** — every pack creates a new version, you can roll back to any
- **Deduplication** — identical blocks are stored once, archives are more compact
- **Drag & Drop** — drop files into the window to pack; drag them out to extract
- **Explorer integration** — right-click and double-click on `.zpaq` and `.rzt`
- **Backup tasks** — save your backup routine as a portable `.rzt` file and run it with a double-click
- **Advanced compression** — visual constructor for the `-method` parameter with block size, preprocessing, search depth and context models
<img width="2280" height="1474" alt="en" src="https://github.com/user-attachments/assets/0f875a4f-a91a-441c-944d-486172b6fee9" />


## Why do I need it?

If you have heard about zpaq and its "time machine" for files but were
put off by the console, Rizpaq is made for you.

| Capability | zpaqfranz CLI | Other GUIs | Rizpaq |
|---|---|---|---|
| View archive | yes | yes | yes |
| Create archive | yes | partial | yes, full control |
| Drag & Drop | no | no | yes |
| Explorer integration | no | no | yes |
| Version time-travel | manual | limited | visual |
| Version comparison | no | no | yes |
| Open files from archive | no | no | yes |
| Backup task profiles | no | no | yes |
| Advanced compression | manual | no | visual constructor |
| 10 languages + your own | no | limited | yes |

The main difference of Rizpaq: we do not just show the archive — we give
full control over its creation (compression level, hashes, masks,
password, multipart, SFX, VSS shadow copies, advanced `-method`) and turn
zpaq's unique versioning into a visual "time machine" that no other
archiver has.

## Features

### Creating archives

- Three-tab creation dialog: everything at hand, no scrolling
- Compression levels: from "store without compression" (m0) to "extreme" (m5)
- **Advanced compression** — visual constructor:
  - block size (1 MiB … 2048 MiB)
  - preprocessing (packed, byte LZ77, BWT, with/without E8E9 for x86 code)
  - search depth (64K … 16M)
  - context models: context (c), ISSE (i), MATCH (a), dictionary (w), mixing (m), SSE (s), MIX2 (t)
  - live preview of the resulting `-method` string
- Choice of file hashing algorithm
- Include/exclude masks
- Password and encryption
- Multipart archives (split into parts)
- Self-extracting SFX archives
- VSS — packing open and locked files
- Automatic free-space check with a +5% headroom
- Save as task — store all creation settings in a portable `.rzt` file
- Live archiving dialog: speed, file count, time remaining, elapsed timer, collapsible log

### Backup tasks

- Save all archive creation settings into a portable `.rzt` file
- Run a task with a double-click, from the context menu, or from the Archive operations menu
- Task metadata (last run, status, run count) updates automatically after each run
- Run tasks on a schedule without the main window (for Windows Task Scheduler)
- Tasks survive OS reinstalls — just copy the `.rzt` file

### Working with archives

- View contents like a regular folder
- Version history: extract any version of a file or folder
- Comparison of two versions — what was added, changed, removed
- Integrity check (3 modes, including "paranoid")
- Search by names and paths
- Open files with the associated app — double-click a file inside an
  archive: it is extracted to a temporary folder and opened
- Non-Latin archive names: Rizpaq offers to rename to transliterated
  Latin and opens the archive right away

### Files and folders on disk

- Delete to the Recycle Bin (context menu and Del key) — drive roots
  are protected, the view follows the changes
- Rename (context menu and F2), case change allowed; renaming the
  currently open archive keeps the view, cache and stored password

### Unified progress window

- One window for archiving, extracting, and testing
- Percent, files, folders, size, speed, elapsed, time remaining
- Live log output from the engine
- Collapsible log panel (auto-expands on errors)
- Auto-close on success, stays open on failure so you can read the log

### Convenience

- The zpaqfranz engine is built in — no extra download or install needed
- Drag & Drop in both directions: drop files into the window to create an
  archive; drag files out of the archive into Explorer to extract them
- Explorer context menu: "Add to Rizpaq archive…", "Extract here", "Test", "Run backup task"
- Double-click on `.zpaq` opens it in Rizpaq; double-click on `.rzt` runs the backup task
- 10 interface languages plus your own (drop-in), light theme

## Quick start

1. Download the latest Rizpaq release and unpack it into any folder.
2. Run `Rizpaq.exe`. Done!

The zpaqfranz archiving engine is already built into Rizpaq — you don't
need to download or install anything else.

If you ever want the very latest zpaqfranz engine, you can always
download it from the
[zpaqfranz releases page](https://github.com/corroll/zpaqfranz/releases)
and point Rizpaq to it via Settings → Path to zpaqfranz.

### Your first archive in 30 seconds

1. Drag a folder into the Rizpaq window.
2. In the creation dialog, press OK.
3. Done — the `.zpaq` archive is created.

### Your first backup task in 10 seconds

1. Create an archive with your desired settings.
2. In the creation dialog, press "Save as task…" and choose a name.
3. Done — the `.rzt` task file is saved. Double-click it anytime to run the backup.

## Requirements

- Windows 10/11

## Languages

English, Русский, Italiano, Deutsch, Français, Español, 中文, Português,
日本語, Polski — and your own language can be added by dropping a
`locales/<code>.json` file next to the app, no rebuild needed.

The language is switched in Settings → Language without a restart.

## Portable mode

Create an empty `portable.txt` file next to `Rizpaq.exe` — and all settings
will be stored next to the program (convenient for a USB stick).

## License

[specify the project license]

---

# Rizpaq

Простой и красивый графический интерфейс для архиватора
[zpaqfranz](https://github.com/corroll/zpaqfranz).

Удобство 7-Zip. Мощь zpaq. История каждого файла.

Создавайте и распаковывайте архивы перетаскиванием мыши, без единой
команды консоли. А уникальная суперсила zpaq — версии файлов и
дедупликация — превращается в наглядную «машину времени».

## Что это?

Rizpaq — графическая оболочка над консольным архиватором zpaqfranz.
Вам больше не нужно учить сложные команды: вся мощь zpaq доступна через
привычный и красивый интерфейс.

- **Единое дерево дисков и архивов** — вся система как на ладони
- **Версии файлов** — каждая упаковка создаёт новую версию, можно откатиться к любой
- **Дедупликация** — одинаковые блоки хранятся один раз, архивы компактнее
- **Drag & Drop** — бросьте файлы в окно, чтобы упаковать; вытащите — чтобы распаковать
- **Интеграция с проводником** — правый клик и двойной клик по `.zpaq` и `.rzt`
- **Задачи резервного копирования** — сохраните рутину бэкапа в портативный файл `.rzt` и запускайте двойным кликом
- **Продвинутое сжатие** — визуальный конструктор параметра `-method`: размер блока, предобработка, глубина поиска, модели контекста

## Зачем мне это?

Если вы слышали про zpaq и его «машину времени» для файлов, но вас
отпугивала консоль, Rizpaq создан для вас.

| Возможность | zpaqfranz CLI | Другие GUI | Rizpaq |
|---|---|---|---|
| Просмотр архива | да | да | да |
| Создание архива | да | частично | да, полный контроль |
| Drag & Drop | нет | нет | да |
| Интеграция с проводником | нет | нет | да |
| Путешествие по версиям | вручную | ограничено | наглядно |
| Сравнение версий | нет | нет | да |
| Открытие файлов из архива | нет | нет | да |
| Профили задач бэкапа | нет | нет | да |
| Продвинутое сжатие | вручную | нет | визуальный конструктор |
| 10 языков + свои | нет | ограничено | да |

Главное отличие Rizpaq: мы не просто показываем архив — мы даём
полный контроль над его созданием (уровень сжатия, хэши, маски, пароль,
многотомность, SFX, VSS-теневые копии, продвинутый `-method`) и превращаем
уникальную версионность zpaq в наглядную «машину времени», которой нет
ни у одного другого архиватора.

## Возможности

### Создание архивов

- Диалог создания на трёх вкладках: всё под рукой, без прокрутки
- Уровни сжатия: от «хранить без сжатия» (m0) до «экстремального» (m5)
- **Продвинутое сжатие** — визуальный конструктор:
  - размер блока (1 МиБ … 2048 МиБ)
  - предобработка (packed, byte LZ77, BWT, с E8E9 для x86-кода и без)
  - глубина поиска (64K … 16M)
  - модели контекста: контекст (c), ISSE (i), MATCH (a), словарная (w), смешивание (m), SSE (s), MIX2 (t)
  - живой предпросмотр итоговой строки `-method`
- Выбор алгоритма хэширования файлов
- Маски включения/исключения
- Пароль и шифрование
- Многотомные архивы (разбиение на части)
- Самораспаковывающиеся SFX-архивы
- VSS — упаковка открытых и заблокированных файлов
- Автоматическая проверка свободного места с запасом +5%
- Сохранить как задачу — все настройки создания в портативном файле `.rzt`
- Живой диалог архивирования: скорость, число файлов, время до конца, секундомер, сворачиваемый лог

### Задачи резервного копирования

- Сохранение всех настроек создания архива в портативный файл `.rzt`
- Запуск задачи двойным кликом, из контекстного меню или из меню «Работа с архивом»
- Метаданные задачи (последний запуск, статус, счётчик) обновляются автоматически
- Запуск задач по расписанию без окна программы (для планировщика заданий)
- Задачи переживают переустановку ОС — просто скопируйте файл `.rzt`

### Работа с архивами

- Просмотр содержимого как обычной папки
- История версий: извлечь любую версию файла или папки
- Сравнение двух версий — что добавлено, изменено, удалено
- Проверка целостности (3 режима, включая «параноидальный»)
- Поиск по именам и путям
- Открытие файлов по ассоциации — двойной клик по файлу в архиве
  извлекает его во временную папку и открывает штатным приложением
- Нелатинские имена архивов: программа предлагает переименовать
  в латиницу (транслит) и сразу открывает архив

### Файлы и папки на диске

- Удаление в корзину (контекстное меню и клавиша Del) — корни дисков
  защищены, вид автоматически обновляется
- Переименование (контекстное меню и F2), смена регистра разрешена;
  переименование открытого архива не сбрасывает просмотр — кэш
  и сохранённый пароль переезжают на новое имя

### Единое окно прогресса

- Одно окно для архивации, распаковки и проверки
- Процент, файлы, папки, размер, скорость, прошло, осталось
- Живой лог вывода движка
- Сворачиваемая панель лога (автоматически раскрывается при ошибках)
- Автозакрытие при успехе, остаётся открытым при ошибке — чтобы можно было прочитать лог

### Удобство

- Движок zpaqfranz уже встроен — ничего дополнительно скачивать и устанавливать не нужно
- Drag & Drop в обе стороны: бросьте файлы в окно, чтобы создать архив;
  перетащите файлы из архива в проводник, чтобы распаковать их
- Контекстное меню проводника: «Добавить в архив Rizpaq…», «Распаковать сюда», «Проверить», «Запустить задачу»
- Двойной клик по `.zpaq` открывает его в Rizpaq; двойной клик по `.rzt` запускает задачу резервного копирования
- 10 языков интерфейса плюс свои (drop-in), светлая тема

## Быстрый старт

1. Скачайте свежий релиз Rizpaq и распакуйте в любую папку.
2. Запустите `Rizpaq.exe`. Готово!

Движок архивации zpaqfranz уже встроен в Rizpaq — ничего дополнительно
скачивать и устанавливать не нужно.

Если вам когда-нибудь понадобится самая свежая версия движка zpaqfranz,
её всегда можно скачать на
[странице релизов zpaqfranz](https://github.com/corroll/zpaqfranz/releases)
и указать путь в Настройки → Путь к zpaqfranz.

### Первый архив за 30 секунд

1. Перетащите папку в окно Rizpaq.
2. В диалоге создания нажмите ОК.
3. Готово — архив `.zpaq` создан.

### Первая задача резервного копирования за 10 секунд

1. Создайте архив с нужными настройками.
2. В диалоге создания нажмите «Сохранить как задачу…» и выберите имя.
3. Готово — файл задачи `.rzt` сохранён. Двойной клик по нему в любой момент запустит резервное копирование.

## Требования

- Windows 10/11

## Языки

English, Русский, Italiano, Deutsch, Français, Español, 中文, Português,
日本語, Polski — свой язык добавляется файлом `locales/<код>.json` рядом
с программой, без пересборки.

Язык переключается в Настройки → Язык без перезапуска.

## Portable-режим

Создайте пустой файл `portable.txt` рядом с `Rizpaq.exe` — и все настройки
будут храниться рядом с программой (удобно для флешки).

## Лицензия

[указать лицензию проекта]
