## Rizpaq

A simple and beautiful graphical interface for the
[zpaqfranz](https://github.com/fcorbelli/zpaqfranz) archiver.

> The convenience of 7-Zip. The power of zpaq. A history of every file.
> Create and extract archives by drag and drop, without a single console
> command. And zpaq's unique superpower — file versions and deduplication —
> becomes a visual "time machine".

### What is it?

**Rizpaq** is a graphical shell over the console archiver **zpaqfranz**.
You no longer need to learn complex console commands: all the power of zpaq
is available through a familiar and beautiful interface.

- A unified tree of drives and archives — your whole system at a glance
- File versions — every pack creates a new version, you can roll back to any
- Deduplication — identical blocks are stored once, archives are more compact
- Drag & Drop — drop files into the window to pack; drag them out to extract
- Explorer integration — right-click and double-click on `.zpaq`
  
<img width="2280" height="1474" alt="en" src="https://github.com/user-attachments/assets/83478f15-8737-40f2-8344-4b3284f433a6" />


### Why do I need it?

If you have heard about **zpaq** and its "time machine" for files but were
put off by the console, **Rizpaq** is made for you.

| Capability | zpaqfranz CLI | Other GUIs | Rizpaq |
|---|---|---|---|
| View archive | yes | yes | yes |
| Create archive | yes | partial | yes, full control |
| Drag & Drop | no | no | yes |
| Explorer integration | no | no | yes |
| Version time-travel | manual | limited | visual |
| Version comparison | no | no | yes |
| 15 languages | no | limited | yes |

**The main difference of Rizpaq:** we do not just show the archive — we give
**full control over its creation** (compression level, hashes, masks,
password, multipart, SFX, VSS shadow copies) **and** turn zpaq's unique
versioning into a visual "time machine" that no other archiver has.

### Features

#### Creating archives
- Compression levels: from "store without compression" to "maximum"
- Choice of file hashing algorithm
- Include/exclude masks
- Password and encryption
- Multipart archives (split into parts)
- Self-extracting SFX archives
- VSS — packing open and locked files
- Automatic free-space check

#### Working with archives
- View contents like a regular folder
- Version history: extract any version of a file or folder
- Comparison of two versions — what was added, changed, removed
- Integrity check (3 modes, including "paranoid")
- Search by names and paths

#### Convenience
- The zpaqfranz engine is built in — no extra download or install needed
- Drag & Drop in both directions: drop files into the window to create an
  archive; drag files out of the archive into Explorer to extract them
- Explorer context menu: "Add to Rizpaq archive…", "Extract here", "Test"
- Double-click on `.zpaq` opens it in Rizpaq
- Live progress with a stopwatch and cancel
- 15 interface languages, light theme

### Quick start

1. Download the latest Rizpaq release and unpack it into any folder.
2. Run `Rizpaq.exe`. Done!

The zpaqfranz archiving engine is already built into Rizpaq — you don't
need to download or install anything else.

> If you ever want the very latest zpaqfranz engine, you can always
> download it from the
> [zpaqfranz releases page](https://github.com/fcorbelli/zpaqfranz)
> and point Rizpaq to it via Settings → Path to zpaqfranz.

#### Your first archive in 30 seconds
1. Drag a folder into the Rizpaq window.
2. In the creation dialog, press OK.
3. Done — the `.zpaq` archive is created.

### Requirements

- Windows 10/11
- To run from source: Python 3.9+ and PySide6

### Languages

English, Русский, Deutsch, Français, Italiano, Español, Polski, हिन्दी,
Nederlands, Português, 中文, 日本語, Ελληνικά, Tiếng Việt.

The language is switched in Settings → Language without a restart.

### Portable mode

Create an empty `portable.txt` file next to `Rizpaq.exe` — and all settings
will be stored next to the program (convenient for a USB stick).


---

## Rizpaq

Простой и красивый графический интерфейс для архиватора
[zpaqfranz](https://github.com/fcorbelli/zpaqfranz).

> Удобство 7-Zip. Мощь zpaq. История каждого файла.
> Создавайте и распаковывайте архивы перетаскиванием мыши, без единой
> команды консоли. А уникальная суперсила zpaq — версии файлов и
> дедупликация — превращается в наглядную «машину времени».

### Что это?

**Rizpaq** — графическая оболочка над консольным архиватором **zpaqfranz**.
Вам больше не нужно учить сложные команды: вся мощь zpaq доступна через
привычный и красивый интерфейс.

- Единое дерево дисков и архивов — вся система как на ладони
- Версии файлов — каждая упаковка создаёт новую версию, можно откатиться к любой
- Дедупликация — одинаковые блоки хранятся один раз, архивы компактнее
- Drag & Drop — бросьте файлы в окно, чтобы упаковать; вытащите — чтобы распаковать
- Интеграция с проводником — правый клик и двойной клик по `.zpaq`

### Зачем мне это?

Если вы слышали про **zpaq** и его «машину времени» для файлов, но вас
отпугивала консоль, **Rizpaq** создан для вас.

| Возможность | zpaqfranz CLI | Другие GUI | Rizpaq |
|---|---|---|---|
| Просмотр архива | да | да | да |
| Создание архива | да | частично | да, полный контроль |
| Drag & Drop | нет | нет | да |
| Интеграция с проводником | нет | нет | да |
| Путешествие по версиям | вручную | ограничено | наглядно |
| Сравнение версий | нет | нет | да |
| 15 языков | нет | ограничено | да |

**Главное отличие Rizpaq:** мы не просто показываем архив — мы даём
**полный контроль над его созданием** (уровень сжатия, хэши, маски, пароль,
многотомность, SFX, VSS-теневые копии) **и** превращаем уникальную
версионность zpaq в наглядную «машину времени», которой нет ни у одного
другого архиватора.

### Возможности

#### Создание архивов
- Уровни сжатия: от «хранить без сжатия» до «максимум»
- Выбор алгоритма хэширования файлов
- Маски включения/исключения
- Пароль и шифрование
- Многотомные архивы (разбиение на части)
- Самораспаковывающиеся SFX-архивы
- VSS — упаковка открытых и заблокированных файлов
- Автоматическая проверка свободного места

#### Работа с архивами
- Просмотр содержимого как обычной папки
- История версий: извлечь любую версию файла или папки
- Сравнение двух версий — что добавлено, изменено, удалено
- Проверка целостности (3 режима, включая «параноидальный»)
- Поиск по именам и путям

#### Удобство
- Движок zpaqfranz уже встроен — ничего дополнительно скачивать и устанавливать не нужно
- Drag & Drop в обе стороны: бросьте файлы в окно, чтобы создать архив;
  перетащите файлы из архива в проводник, чтобы распаковать их
- Контекстное меню проводника: «Добавить в архив Rizpaq…», «Распаковать сюда», «Проверить»
- Двойной клик по `.zpaq` открывает его в Rizpaq
- Живой прогресс с секундомером и отменой
- 15 языков интерфейса, светлая тема

### Быстрый старт

1. Скачайте свежий релиз Rizpaq и распакуйте в любую папку.
2. Запустите `Rizpaq.exe`. Готово!

Движок архивации zpaqfranz уже встроен в Rizpaq — ничего дополнительно
скачивать и устанавливать не нужно.

> Если вам когда-нибудь понадобится самая свежая версия движка zpaqfranz,
> её всегда можно скачать на
> [странице релизов zpaqfranz](https://github.com/fcorbelli/zpaqfranz)
> и указать путь в Настройки → Путь к zpaqfranz.

#### Первый архив за 30 секунд
1. Перетащите папку в окно Rizpaq.
2. В диалоге создания нажмите ОК.
3. Готово — архив `.zpaq` создан.

### Требования

- Windows 10/11
- Для запуска из исходников: Python 3.9+ и PySide6

### Языки

English, Русский, Deutsch, Français, Italiano, Español, Polski, हिन्दी,
Nederlands, Português, 中文, 日本語, Ελληνικά, Tiếng Việt.

Язык переключается в Настройки → Язык без перезапуска.

### Portable-режим

Создайте пустой файл `portable.txt` рядом с `Rizpaq.exe` — и все настройки
будут храниться рядом с программой (удобно для флешки).

