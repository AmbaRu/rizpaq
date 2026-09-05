# Rizpaq — Changelog

## English

### [1.8.0] — 2026-09-04

#### Added
- **Windows Task Scheduler integration:** create, edit, and delete scheduled backup tasks directly from the Rizpaq interface.
- **Flexible scheduler:** choose the launch frequency using convenient radio buttons (every N minutes, hours, days, weeks, or months).
- **Fully silent background mode:** scheduled tasks run without creating Qt windows or the `zpaqfranz` console, without disturbing the user.
- **Task log control:** choose the logging mode (Short / Full / Disabled) so that log files do not take up much space during frequent runs (e.g., every hour).
- **Smart task editing:** when selecting "Edit task…", the creation dialog opens with all fields pre-filled. The "💾 Save" button instantly overwrites the current `.rzt` file without asking for a path.
- **"Open archive…" menu item** in the "File" menu with the `Ctrl+O` hotkey.
- **`Alt+Enter` hotkey** to quickly open "Archive Information".

#### Changed
- **Complete overhaul of the main menu** to match UI standards:
  - **File:** create (`Ctrl+N`), open (`Ctrl+O`), run tasks, exit.
  - **Archive:** actions on the opened archive (info, extract, test, versions, search). Automatically dims if no archive is open.
  - **Backup:** a new menu item combining everything related to tasks (Run, Edit, Scheduler).
  - **Settings:** merging file associations into a single "Explorer Integration" checkbox.
  - **Help:** restored the "About…" item.
- **Behavior of the "💾 Save as task…" button:** now it changes its text and logic depending on the context (creating a new task or saving an edited one).

#### Fixed
- **Task Scheduler status encoding:** fixed the display of garbled text when reading Russian task statuses from `schtasks` (added automatic encoding detection for `cp866`/`cp1251`/`utf-8`).
- **Task list display:** fixed an error where tasks were not shown in the Rizpaq Scheduler window (accounted for the backslash `\` in the names of tasks in the root folder of Windows).
- **Missing "Help" menu:** fixed a menu initialization error that could cause the "About…" item to disappear.

### [1.7.1] — 2026-08-24
- **Advanced compression** — visual constructor for the `-method` parameter:
  - block size (1 MiB … 2048 MiB)
  - preprocessing (packed, byte LZ77, BWT, with/without E8E9 for x86 code)
  - search depth (64K … 16M)
  - context models: context (c), ISSE (i), MATCH (a), dictionary (w), mixing (m), SSE (s), MIX2 (t)
  - live preview of the resulting `-method` string
- Compression levels m0–m5 with clear descriptions (from "no compression" to "extreme")
- **Unified progress window** for archiving, extracting, and testing:
  - percent, files, folders, size, speed, elapsed, time remaining
  - live log output from the engine
  - collapsible log panel (auto-expands on errors)
  - auto-close on success, stays open on failure
- All progress dialogs share the same look and behavior

### [1.7] — 2026-08-18
- **Backup tasks (.rzt):** save all archive settings into a portable file and run them later with a double-click.
- Archiving progress dialog: a separate window with speed, file count, time remaining and an elapsed timer.
- `.rzt` file association: double-click a task file to run the backup right away.
- Run tasks on a schedule without the main window (for Windows Task Scheduler).
- Fixed: archiving no longer shows the "extraction" title; speed and file count now display correctly.

### [1.6] — 2026-08-16
- Open files with the associated app — double-click a file on disk or inside an archive.
- Delete files and folders to the Recycle Bin; drive roots are protected.
- Rename files and folders; the currently open archive keeps its view when renamed.
- Non-Latin archive names: Rizpaq offers a transliterated Latin name and opens the archive right away.
- Create-archive dialog rebuilt as three compact tabs, no scrolling.
- And more: free-space auto-check with headroom, fixed single-file and folder extraction.

### [1.5] — 2026-08-10
- Explorer integration: right-click menu and `.zpaq` association — double-click opens Rizpaq.
- Drag & Drop: drop files or folders onto the window to create an archive.
- Light mode: extract, test and create archives from the context menu without the main window.
- No duplicate windows: a repeated launch hands the job to the already-open Rizpaq.
- The file association is set without administrator rights.

### [1.0] — 2026-07-20
- Initial public release. Archive integrity test, version history, progress panel, stable with large archives.

---

## Русский

### [1.8.0] — 2026-09-04

#### Добавлено
- **Интеграция с Планировщиком задач Windows:** создание, редактирование и удаление задач резервного копирования по расписанию прямо из интерфейса Rizpaq.
- **Гибкий планировщик:** выбор частоты запуска с помощью удобных радио-кнопок (каждые N минут, часов, дней, недель или месяцев).
- **Полностью невидимый фоновый режим:** запланированные задачи запускаются без создания окон Qt и консоли `zpaqfranz`, не мешая работе пользователя.
- **Управление логами задач:** выбор режима логирования (Кратко / Полный / Отключено), чтобы при частых запусках (например, каждый час) лог-файлы не занимали много места.
- **Умное редактирование задач:** при выборе «Редактировать задачу…» открывается диалог создания с уже заполненными полями. Кнопка «💾 Сохранить» мгновенно перезаписывает текущий `.rzt` файл без запроса пути.
- **Пункт «Открыть архив…»** в меню «Файл» с горячей клавишей `Ctrl+O`.
- **Горячая клавиша `Alt+Enter`** для быстрого открытия «Информации об архиве».

#### Изменено
- **Полная переработка главного меню** для соответствия стандартам UI:
  - **Файл:** создание (`Ctrl+N`), открытие (`Ctrl+O`), запуск задач, выход.
  - **Архив:** действия над открытым архивом (инфо, распаковка, проверка, версии, поиск). Автоматически гаснет, если архив не открыт.
  - **Бэкап:** новый пункт меню, объединяющий всё, что связано с задачами (Запустить, Редактировать, Планировщик).
  - **Настройки:** объединение ассоциаций файлов в одну галочку «Интеграция с проводником».
  - **Справка:** восстановлен пункт «О программе…».
- **Поведение кнопки «💾 Сохранить как задачу…»:** теперь она меняет текст и логику в зависимости от контекста (создание новой задачи или сохранение отредактированной).

#### Исправлено
- **Кодировка статусов Планировщика:** исправлено отображение «кракозябр» при чтении русских статусов задач из `schtasks` (добавлен автоматический подбор кодировки `cp866`/`cp1251`/`utf-8`).
- **Отображение списка задач:** исправлена ошибка, из-за которой задачи не показывались в окне Планировщика Rizpaq (учтён обратный слэш `\` в именах задач корневой папки Windows).
- **Отсутствие меню «Справка»:** исправлена ошибка инициализации меню, из-за которой мог пропадать пункт «О программе».

### [1.7.1] — 2026-08-24
- **Продвинутое сжатие** — визуальный конструктор параметра `-method`:
  - размер блока (1 МиБ … 2048 МиБ)
  - предобработка (packed, byte LZ77, BWT, с E8E9 для x86-кода и без)
  - глубина поиска (64K … 16M)
  - модели контекста: контекст (c), ISSE (i), MATCH (a), словарная (w), смешивание (m), SSE (s), MIX2 (t)
  - живой предпросмотр итоговой строки `-method`
- Уровни сжатия m0–m5 с понятными описаниями (от «без сжатия» до «экстремального»)
- **Единое окно прогресса** для архивации, распаковки и проверки:
  - процент, файлы, папки, размер, скорость, прошло, осталось
  - живой лог вывода движка
  - сворачиваемая панель лога (автоматически раскрывается при ошибках)
  - автозакрытие при успехе, остаётся открытым при ошибке
- Все диалоги прогресса выглядят и ведут себя одинаково

### [1.7] — 2026-08-18
- **Задачи резервного копирования (.rzt):** сохранение всех настроек архива в портативный файл и запуск двойным кликом.
- Диалог прогресса архивирования: отдельное окно со скоростью, количеством файлов, временем до конца и секундомером.
- Ассоциация файлов `.rzt`: двойной клик по задаче сразу запускает резервное копирование.
- Запуск задач по расписанию без окна программы (для планировщика заданий).
- Исправлено: при архивации больше не показывается «извлечение файлов»; скорость и число файлов теперь видны корректно.

### [1.6] — 2026-08-16
- Открытие файлов штатным приложением: двойной клик по файлу на диске или внутри архива.
- Удаление файлов и папок в корзину; корни дисков защищены.
- Переименование файлов и папок; открытый архив не сбрасывает просмотр при переименовании.
- Нелатинские имена архивов: программа предлагает переименовать в транслит и сразу открывает.
- Диалог создания архива на три компактные вкладки, без прокрутки.
- И другое: автопроверка свободного места с запасом, исправления извлечения файлов и папок.

### [1.5] — 2026-08-10
- Интеграция с проводником: контекстное меню и ассоциация `.zpaq` — двойной клик открывает Rizpaq.
- Drag & Drop: бросьте файлы или папки на окно, чтобы создать архив.
- Лёгкий режим: распаковка, проверка и создание архива из контекстного меню без главного окна.
- Повторный запуск не открывает второе окно — задача передаётся уже открытому Rizpaq.
- Ассоциация файлов устанавливается без прав администратора.

### [1.0] — 2026-07-20
- Первый публичный релиз. Проверка целостности архива, история версий, панель прогресса, стабильная работа с большими архивами.