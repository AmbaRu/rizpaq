## zpaqfranz

**zpaqfranz** is a command-line archiver built on the zpaq format.
It keeps every version of every file inside a single archive: when you
add files again, nothing is duplicated — only the changed parts are
written. This is called *deduplication*, and it turns a folder of daily
backups into a small file that still contains the full history.

Key strengths of zpaqfranz:

- **Versioning.** Every add creates a new version. You can see, compare
  and extract the state of the archive at any version.
- **Deduplication.** Identical file blocks are stored once, even across
  different files and different versions.
- **Strong hashing.** A wide choice of file hashes (xxhash, SHA-1/2/3,
  BLAKE3, MD5, and more) and extra collision-resistant checksums.
- **Integrity.** Built-in test modes up to *paranoid* — bit-level
  verification of the whole archive.
- **Encryption.** Password-protected archives with strong encryption.

The price for all this power is a console interface with many flags.
That's where Rizpaq comes in.

## Rizpaq

**Rizpaq** is a simple, beautiful graphical interface for zpaqfranz.

Rizpaq turns the powerful command-line archiver into a familiar,
friendly window. No console, no memorizing flags — just click and go.
All the power of zpaqfranz (versioning, deduplication, strong hashing)
with the comfort of a regular file manager.
![Uploading v1.3.png…]()

### Why Rizpaq?

- **No console.** Everything happens in a familiar window: drives,
  folders and archives on the left, files on the right.
- **Archives behave like folders.** Double-click a `.zpaq` and browse it
  as if it were already extracted. Several archives open at once.
- **A time machine for your data.** Every archive keeps its history:
  view it "as of version N", compare two versions, extract any version.
- **Safe by default.** Integrity tests (up to paranoid mode), passwords,
  and protection against common archiving pitfalls.
- **Honest progress.** A live progress panel with a timer and Cancel for
  every long operation.
- **14 interface languages**, switched on the fly.

### Features

- Unified tree of drives, folders and `.zpaq` archives
- Browse archive contents like a normal folder; multiple archives open
- Search inside an archive (`*` and `?` wildcards, Ctrl+F)
- Sort the file table by any column with a header click; sorting is
  remembered
- Extract: a single file, a folder, or all versions at once
- Create archives with full control: compression level, file hash,
  include/exclude masks, comment, password, long paths and more
- Integrity test: full / all versions with checksums / paranoid
- Archive information: summary plus a per-version table
- Two-version comparison with added / changed / removed highlighting
- Light "Soft Azure" theme; portable mode; settings and window state
  persist

### Getting started (Windows)

1. **Download** the latest release and unpack it to any folder.
2. **Add the engine**: download `zpaqfranz.exe` and put it next to
   `Rizpaq.exe` — or point Rizpaq at it later via
   *Settings → Path to zpaqfranz…*.
3. **Run** `Rizpaq.exe`. That's it — you are archiving.

> **Portable mode:** create an empty `portable.txt` file next to the
> executable and all settings will be stored next to the program.

> Without `zpaqfranz.exe` the file manager still works, but archives
> will not open.

### A 30-second tour

- **Open an archive** — double-click it in the tree or the file table.
- **Extract** — right-click a file or folder → Extract; live progress,
  cancel anytime.
- **Create** — right-click a folder → Create archive…; choose
  compression, hash, masks, password; get a completion report with the
  compression ratio.
- **Travel in time** — *Archive operations → Archive versions*, or
  compare two versions.
- **Find anything** — Ctrl+F inside an archive.

### Languages

English · Русский · Deutsch · Français · Italiano · Español · Polski ·
हिन्दी · Nederlands · Português · 中文 · 日本語 · Ελληνικά · Tiếng Việt

Switch via *Settings → Language* — no restart needed.

### Changelog

See [CHANGELOG.md](CHANGELOG.md).

Repository: https://github.com/AmbaRu/rizpaq

---

## zpaqfranz

**zpaqfranz** — это консольный архиватор, построенный на формате zpaq.
Он хранит в одном архиве *каждую версию каждого файла*: когда вы
добавляете файлы повторно, дубликаты не пишутся — дописываются только
изменившиеся части. Это называется *дедупликация*, и она превращает
папку ежедневных бэкапов в небольшой файл, в котором по-прежнему лежит
вся история.

Сильные стороны zpaqfranz:

- **Версионность.** Каждое добавление создаёт новую версию. Можно
  увидеть, сравнить и извлечь состояние архива на любую версию.
- **Дедупликация.** Одинаковые блоки файлов хранятся один раз, даже
  между разными файлами и разными версиями.
- **Надёжные хэши.** Широкий выбор хэшей файлов (xxhash, SHA-1/2/3,
  BLAKE3, MD5 и другие) и дополнительные контрольные суммы, устойчивые
  к коллизиям.
- **Целостность.** Встроенные режимы проверки вплоть до *параноидального*
  — побитовая верификация всего архива.
- **Шифрование.** Архивы с паролем и надёжным шифрованием.

Плата за всю эту мощь — консольный интерфейс с множеством флагов.
Именно здесь на сцену выходит Rizpaq.

## Rizpaq

**Rizpaq** — это простой и красивый графический интерфейс для zpaqfranz.

Rizpaq превращает мощный консольный архиватор в привычное дружелюбное
окно. Без консоли и заучивания флагов — просто кликайте и работайте.
Вся мощь zpaqfranz (версионность, дедупликация, надёжные хэши)
с удобством уровня обычного файлового менеджера.

### Зачем Rizpaq?

- **Без консоли.** Всё происходит в привычном окне: диски, папки
  и архивы слева, файлы справа.
- **Архив ведёт себя как папка.** Двойной клик по `.zpaq` — и вы ходите
  по нему, как по уже распакованному. Несколько архивов открыты
  одновременно.
- **Машина времени для данных.** Каждый архив хранит историю: состояние
  «на версию N», сравнение двух версий, извлечение любой версии.
- **Безопасность по умолчанию.** Проверки целостности (вплоть до
  параноидальной), пароли и защита от типичных ловушек архивации.
- **Честный прогресс.** Живая панель прогресса с секундомером и кнопкой
  «Отмена» для каждой долгой операции.
- **14 языков интерфейса**, переключение на лету.

### Возможности

- Единое дерево дисков, папок и архивов `.zpaq`
- Просмотр архива как обычной папки; несколько архивов открыты сразу
- Поиск внутри архива (маски `*` и `?`, Ctrl+F)
- Сортировка таблицы файлов кликом по заголовку любой колонки; выбор
  запоминается
- Извлечение: файл, папка или все версии сразу
- Создание архивов с полным контролем: уровень сжатия, хэш, маски
  включения/исключения, комментарий, пароль, длинные пути и другое
- Проверка целостности: полная / все версии с контрольными суммами /
  параноидальная
- Информация об архиве: сводка и таблица версий
- Сравнение двух версий с подсветкой добавленного / изменённого /
  удалённого
- Светлая тема «Soft Azure»; portable-режим; настройки и окно
  запоминаются

### Как начать (Windows)

1. **Скачайте** свежий релиз и распакуйте его в любую папку.
2. **Добавьте движок**: скачайте `zpaqfranz.exe` и положите его рядом с
   `Rizpaq.exe` — или укажите путь позже: *Настройки → Путь к zpaqfranz…*.
3. **Запустите** `Rizpaq.exe`. Всё — можно архивировать.

> **Portable-режим:** создайте пустой файл `portable.txt` рядом с
> программой — и все настройки будут храниться рядом с ней.

> Без `zpaqfranz.exe` файловый менеджер работает, но архивы не
> открываются.

### Экскурсия за 30 секунд

- **Открыть архив** — двойной клик по архиву в дереве или в таблице.
- **Извлечь** — правый клик по файлу или папке → Извлечь; живой
  прогресс, отмена в любой момент.
- **Создать** — правый клик по папке → Создать архив…; сжатие, хэш,
  маски, пароль; итоговое окно со степенью сжатия.
- **Путешествовать во времени** — *Работа с архивом → Версии архива*
  или сравнение двух версий.
- **Найти что угодно** — Ctrl+F внутри архива.

### Языки

English · Русский · Deutsch · Français · Italiano · Español · Polski ·
हिन्दी · Nederlands · Português · 中文 · 日本語 · Ελληνικά · Tiếng Việt

Переключение: *Настройки → Язык*, без перезапуска.

### История изменений

См. [CHANGELOG.md](CHANGELOG.md).

Репозиторий: https://github.com/AmbaRu/rizpaq
