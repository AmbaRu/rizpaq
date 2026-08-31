# Rizpaq — Changelog

## English

### 1.7.1

- **Advanced compression** — visual constructor for the `-method` parameter:
  - block size (1 MiB … 2048 MiB)
  - preprocessing (packed, byte LZ77, BWT, with/without E8E9 for x86 code)
  - search depth (64K … 16M)
  - context models: context (c), ISSE (i), MATCH (a), dictionary (w), mixing (m), SSE (s), MIX2 (t)
  - live preview of the resulting `-method` string
- **Compression levels m0–m5** with clear descriptions (from "no compression" to "extreme")
- **Unified progress window** for archiving, extracting, and testing:
  - percent, files, folders, size, speed, elapsed, time remaining
  - live log output from the engine
  - collapsible log panel (auto-expands on errors)
  - auto-close on success, stays open on failure
- All progress dialogs share the same look and behavior

### 1.7

- **Backup tasks (.rzt)**: save all archive settings into a portable file and run them later with a double-click.
- **Archiving progress dialog**: a separate window with speed, file count, time remaining and an elapsed timer.
- **.rzt file association**: double-click a task file to run the backup right away.
- Run tasks on a schedule without the main window (for Windows Task Scheduler).
- Fixed: archiving no longer shows the "extraction" title; speed and file count now display correctly.

### 1.6

- **Open files with the associated app** — double-click a file on disk or inside an archive.
- **Delete files and folders to the Recycle Bin**; drive roots are protected.
- **Rename files and folders**; the currently open archive keeps its view when renamed.
- Non-Latin archive names: Rizpaq offers a transliterated Latin name and opens the archive right away.
- Create-archive dialog rebuilt as three compact tabs, no scrolling.
- And more: free-space auto-check with headroom, fixed single-file and folder extraction.

### 1.5

- **Explorer integration**: right-click menu and .zpaq association — double-click opens Rizpaq.
- **Drag & Drop**: drop files or folders onto the window to create an archive.
- **Light mode**: extract, test and create archives from the context menu without the main window.
- No duplicate windows: a repeated launch hands the job to the already-open Rizpaq.
- The file association is set without administrator rights.

### 1.3

- Sort the file list by clicking a column header.
- Unified "Archive operations" menu: create, test, extract, info.
- Archive actions are disabled while no archive is open.
- Sort order is remembered between launches.
- Folders stay above files; the "up" row is always on top.

### 1.2

- Fixed the freeze when opening archives.
- Automatic Latin name for archives with non-Latin names.
- A clear warning instead of a freeze for non-Latin archives.
- The completion window appears instantly.
- The password is remembered correctly on creation.

### 1.1

- Create archives from folders and files.
- Compression level and file hash selection.
- Test the archive right after creation.
- Include/exclude masks.
- Hindi instead of Ukrainian.

### 1.0

- Archive integrity test: three modes.
- Extract one version or all versions at once.
- Version history with dates and change counts.
- Progress panel with a timer and cancel.
- Stable with large archives.

### 0.9

- Browse an archive like a normal folder.
- Version history and two-version comparison.
- 14 interface languages.
- Search by names and paths.
- Passwords, portable mode, ready Windows build.

---

## Русский

### 1.7.1

- **Продвинутое сжатие** — визуальный конструктор параметра `-method`:
  - размер блока (1 МиБ … 2048 МиБ)
  - предобработка (packed, byte LZ77, BWT, с E8E9 для x86-кода и без)
  - глубина поиска (64K … 16M)
  - модели контекста: контекст (c), ISSE (i), MATCH (a), словарная (w), смешивание (m), SSE (s), MIX2 (t)
  - живой предпросмотр итоговой строки `-method`
- **Уровни сжатия m0–m5** с понятными описаниями (от «без сжатия» до «экстремального»)
- **Единое окно прогресса** для архивации, распаковки и проверки:
  - процент, файлы, папки, размер, скорость, прошло, осталось
  - живой лог вывода движка
  - сворачиваемая панель лога (автоматически раскрывается при ошибках)
  - автозакрытие при успехе, остаётся открытым при ошибке
- Все диалоги прогресса выглядят и ведут себя одинаково

### 1.7

- **Задачи резервного копирования (.rzt)**: сохранение всех настроек архива в портативный файл и запуск двойным кликом.
- **Диалог прогресса архивирования**: отдельное окно со скоростью, количеством файлов, временем до конца и секундомером.
- **Ассоциация файлов .rzt**: двойной клик по задаче сразу запускает резервное копирование.
- Запуск задач по расписанию без окна программы (для планировщика заданий).
- Исправлено: при архивации больше не показывается «извлечение файлов»; скорость и число файлов теперь видны корректно.

### 1.6

- **Открытие файлов штатным приложением**: двойной клик по файлу на диске или внутри архива.
- **Удаление файлов и папок в корзину**; корни дисков защищены.
- **Переименование файлов и папок**; открытый архив не сбрасывает просмотр при переименовании.
- Нелатинские имена архивов: программа предлагает переименовать в транслит и сразу открывает.
- Диалог создания архива на три компактные вкладки, без прокрутки.
- И другое: автопроверка свободного места с запасом, исправления извлечения файлов и папок.

### 1.5

- **Интеграция с проводником**: контекстное меню и ассоциация .zpaq — двойной клик открывает Rizpaq.
- **Drag & Drop**: бросьте файлы или папки на окно, чтобы создать архив.
- **Лёгкий режим**: распаковка, проверка и создание архива из контекстного меню без главного окна.
- Повторный запуск не открывает второе окно — задача передаётся уже открытому Rizpaq.
- Ассоциация файлов устанавливается без прав администратора.

### 1.3

- Сортировка списка файлов кликом по заголовку колонки.
- Единое меню «Работа с архивом»: создать, проверить, распаковать, информация.
- Вне архива архивные пункты меню неактивны.
- Порядок сортировки запоминается между запусками.
- Папки выше файлов; строка «вверх» всегда сверху.

### 1.2

- Исправлено зависание при открытии архивов.
- Автоматическое латинское имя для архивов с нелатинскими именами.
- Понятное предупреждение вместо зависания для нелатинских архивов.
- Итоговое окно появляется без задержки.
- Пароль корректно запоминается при создании.

### 1.1

- Создание архивов из папок и файлов.
- Выбор уровня сжатия и хэша файлов.
- Проверка архива сразу после создания.
- Маски включения/исключения.
- Хинди вместо украинского.

### 1.0

- Проверка целостности архива: три режима.
- Распаковка одной версии или всех версий сразу.
- История версий с датами и числом изменений.
- Панель прогресса с секундомером и отменой.
- Стабильная работа с большими архивами.

### 0.9

- Просмотр архива как обычной папки.
- История версий и сравнение двух версий.
- 14 языков интерфейса.
- Поиск по именам и путям.
- Пароли, portable-режим, готовая сборка для Windows.