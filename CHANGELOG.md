# Rizpaq — Changelog

## English

### [0.9]
- **Unified tree of drives and zpaq archives.**
- **Version history, "at version N" slices and two-version comparison.**
- **14 interface languages, switchable without restart.**
- Browse an archive like a normal folder; multiple archives open at once.
- Search by names and paths with `*` and `?` wildcards.
- File and folder extraction with progress and cancel.
- Password support for encrypted archives.
- Archive information and three integrity-test modes.
- Light theme, portable mode, saved settings and window state.
- Ready-to-run Windows build.
- Fixed: Stable handling of large engine output.
- Fixed: Removed unused code.

### [1.0] — 2026-07-20
- **Archive integrity testing: three modes — full, all-versions with checksums, paranoid.**
- **Unpacking: extract a single version or all versions at once.**
- **Progress panel with a timer and cancel for long operations.**
- Version list shows date, time and the number of added, changed and removed files.
- "Work with archive" menu (info, password, test, unpack) and "Settings" menu (zpaqfranz path, language).
- Stable handling of large archives: contents, summary and version counts display correctly, including when returning to an already open archive.

### [1.1]
- **Create archives from folders and files.**
- **Compression level selection: from store (no compression) to maximum.**
- **Test the archive right after creation.**
- File hashing algorithm selection.
- Include and exclude file masks.
- Extra options: long paths, store file creation date, no recursion, NTFS ADS, force re-add XLS/PPT, disable extra checksums and deduplication.
- Version comment for the archive.
- Completion window after archiving: compression parameters, compression ratio, test result.
- "Test" submenu with three modes in the right-click context menu.
- Hindi language added instead of Ukrainian.
- Fixed archive creation on paths with non-Latin characters.
- Fixed interface freeze after archive creation.
- Fixed conflict between post-creation test and manual test.

### [1.2]
- **Fixed program freeze when opening archives.**
- **Automatic Latin name suggestion when creating an archive from a folder or file with a non-Latin name.**
- **Protection against opening and testing archives with non-Latin filenames: a warning with guidance is shown instead of freezing.**
- Fixed false "cannot write" error when creating archives on some drives.
- Completion window after archive creation now appears without delay.
- Encrypted archive password is correctly remembered during creation regardless of enabled options.

### [1.3]
- **Right-hand table sorting by clicking a column header.**
- **Unified "Archive operations" menu: create, test, extract, archive info.**
- **The chosen sort column and direction are remembered and restored on the next launch.**
- First click — ascending, second click — descending; the direction is shown by an arrow.
- The "⬆ .." row always on top; folders above archives and files.
- Names sorted case- and icon-insensitively.
- Sizes and versions sorted as numbers, dates — chronologically.
- Empty versions always at the bottom regardless of direction.
- On first open the table is sorted by name.
- "Refresh" (F5) moved to the "View" menu.
- "Search in archive" (Ctrl+F) moved to "Archive operations".
- The "Go" menu removed: upward navigation is via breadcrumbs and the "⬆ .." row.
- The "Archive password" item removed from the menu: the password is set in the create dialog.
- Archive-dependent menu items are disabled while no archive is open.

### [1.4]
- **Source-selection window when creating an archive: a tree with checkboxes (drives → folders → files) and lazy loading.**
- **Multipart archives: the volume size is chosen from a ready list or set manually.**
- **VSS shadow copies for archiving open and locked files.**
- Editable source list in the create dialog: add and remove paths.
- Reading multipart archives via the `_????.zpaq` mask.
- Automatic free-space check: the threshold equals the source size and is filled in automatically.
- Manual free-space check threshold.
- Second copy of the archive to a chosen folder.
- Post-creation test mode selection: none / test / verify against filesystem / paranoid.
- Skipping OneDrive placeholders.
- Ignoring file access errors with an error log.
- Shutting down the computer when archiving completes.
- Creating a self-extracting archive (SFX).
- Date templates in the archive name (`%year`, `%month`, `%day` and others) and an "Insert date" button.
- Extended set of hashing algorithms: whirlpool, highway64/128/256, xxhashb, blake3b, sha1b/256b/3b, md5b and others.
- Create dialog with vertical scrolling; height adapts to the main window.
- The "long paths" checkbox is active only when folders are among the sources.
- Fixed: program crash on "Cancel" in the create dialog.
- Fixed: overflow when measuring large folders.
- Fixed: `-longpath` is no longer passed for single files.
- Fixed: creating an archive via the menu took the folder from the left pane instead of the selection in the right pane.
- Fixed: Enter in the create dialog fields no longer starts archiving.

### [1.5] — 2026-08-10
- **Explorer integration: right-click context menu and `.zpaq` association — double-click opens Rizpaq.**
- **Drag & Drop: drop files or folders onto the window to create an archive.**
- **Light mode: extract, test and create archives from the context menu without the main window.**
- No duplicate windows: a repeated launch hands the job to the already-open Rizpaq.
- The file association is set without administrator rights.

### [1.6] — 2026-08-16
- **Open files with the associated app — double-click a file on disk or inside an archive.**
- **Delete files and folders to the Recycle Bin; drive roots are protected.**
- **Non-Latin archive names: Rizpaq offers a transliterated Latin name and opens the archive right away.**
- Rename files and folders; the currently open archive keeps its view when renamed.
- Create-archive dialog rebuilt as three compact tabs, no scrolling.
- And more: free-space auto-check with headroom, fixed single-file and folder extraction.

### [1.7] — 2026-08-18
- **Backup tasks (.rzt): save all archive settings into a portable file and run them later with a double-click.**
- **Archiving progress dialog: a separate window with speed, file count, time remaining and an elapsed timer.**
- **Run tasks on a schedule without the main window (for Windows Task Scheduler).**
- `.rzt` file association: double-click a task file to run the backup right away.
- Fixed: archiving no longer shows the "extraction" title; speed and file count now display correctly.

### [1.7.1] — 2026-08-24
- **Advanced compression — visual constructor for the `-method` parameter:** block size, preprocessing, search depth, context models, live preview.
- **Unified progress window for archiving, extracting, and testing:** percent, files, folders, size, speed, elapsed, time remaining, live log, collapsible log panel.
- **Compression levels m0–m5 with clear descriptions** (from "no compression" to "extreme").
- All progress dialogs share the same look and behavior.

### [1.8.0] — 2026-09-04
- **Windows Task Scheduler integration: create, edit, and delete scheduled backup tasks directly from the Rizpaq interface.**
- **Fully silent background mode: scheduled tasks run without creating Qt windows or the `zpaqfranz` console, without disturbing the user.**
- **Smart task editing: when selecting "Edit task…", the creation dialog opens with all fields pre-filled. The "💾 Save" button instantly overwrites the current `.rzt` file without asking for a path.**
- Flexible scheduler: choose the launch frequency using convenient radio buttons (every N minutes, hours, days, weeks, or months).
- Task log control: choose the logging mode (Short / Full / Disabled) so that log files do not take up much space during frequent runs.
- "Open archive…" menu item in the "File" menu with the `Ctrl+O` hotkey.
- `Alt+Enter` hotkey to quickly open "Archive Information".
- Complete overhaul of the main menu to match UI standards.
- Task Scheduler status encoding: fixed the display of garbled text when reading Russian task statuses.
- Task list display: fixed an error where tasks were not shown in the Rizpaq Scheduler window.
- Missing "Help" menu: fixed a menu initialization error.

### [1.9.0] — 12.09.2026
- **Universal archive support (ZIP, 7z, RAR) via the 7-Zip bridge.** Read, browse, and extract files from these formats seamlessly alongside ZPAQ.
- **"Convert to ZPAQ..." master.** Transcode any ZIP/7z/RAR archive into a highly compressed, versioned, and deduplicated ZPAQ archive in one click. The process runs in the background without blocking the UI.
- **Explorer Integration dialog.** A dedicated window to independently manage file associations for `.zpaq`, `.rzt`, `.zip`, `.7z`, and `.rar` without overwriting each other.
- New context menu and "Archive" menu items: "Convert to ZPAQ…" and "Extract All…" for universal archives.
- Bundled `7z.exe` and `7z.dll` for zero-configuration out-of-the-box experience.
- The "Open Archive" file dialog filter now includes `*.zip`, `*.7z`, `*.rar`.
- Improved progress bar parsing: fixed ETA and Speed display for large archives.
- Drag & Drop extraction no longer blocks the UI for large archives (progress dialog with cancel support).
- `-longpath` flag is no longer passed to `zpaqfranz` when the source is a wildcard `*` (transcoding mode), preventing the "cannot get -longpath for this file" error.

---

## Русский

### [0.9]
- **Единое дерево дисков и архивов zpaq.**
- **История версий, срезы «на версию N» и сравнение двух версий.**
- **14 языков интерфейса с переключением без перезапуска.**
- Просмотр архива как обычной папки; несколько архивов открыты сразу.
- Поиск по именам и путям с масками `*` и `?`.
- Извлечение файлов и папок с прогрессом и отменой.
- Поддержка паролей зашифрованных архивов.
- Информация об архиве и три режима проверки целостности.
- Светлая тема, portable-режим, сохранение настроек и окна.
- Готовая сборка для Windows.
- Исправлено: стабильная работа при большом выводе движка.
- Исправлено: убран неиспользуемый код.

### [1.0] — 2026-07-20
- **Проверка целостности архива: три режима — полная, все версии с контрольными суммами, параноидальная.**
- **Распаковка: извлечь одну версию или все версии сразу.**
- **Панель прогресса с секундомером и отменой при долгих операциях.**
- В списке версий видны дата, время и число добавленных, изменённых и удалённых файлов.
- Меню «Работа с архивом» (информация, пароль, проверка, распаковка) и «Настройки» (путь к zpaqfranz, язык).
- Стабильная работа с большими архивами: корректное отображение содержимого, сводки и числа версий, в том числе при возврате к уже открытому архиву.

### [1.1]
- **Создание архивов из папок и файлов.**
- **Выбор уровня сжатия: от хранения без сжатия до максимального.**
- **Проверка архива сразу после создания.**
- Выбор алгоритма хэширования файлов.
- Маски включения и исключения файлов.
- Дополнительные опции: длинные пути, дата создания файлов, работа без рекурсии, NTFS ADS, принудительное добавление XLS/PPT, отключение контрольных сумм и дедупликации.
- Комментарий к версии архива.
- Итоговое окно после архивации: параметры сжатия, степень сжатия, результат проверки.
- Подменю «Проверка» с тремя режимами в контекстном меню по правой клавише мыши.
- Вместо украинского языка добавлен хинди.
- Исправлено создание архивов на путях с нелатинскими символами.
- Исправлено зависание интерфейса после создания архива.
- Исправлен конфликт между проверкой после создания и ручной проверкой.

### [1.2]
- **Исправлено зависание программы при открытии архивов.**
- **Автоматическая подстановка латинского имени при создании архива из папки или файла с нелатинским названием.**
- **Защита от открытия и проверки архивов с нелатинскими именами: вместо зависания показывается предупреждение с подсказкой.**
- Устранена ложная ошибка «невозможно записать» при создании архивов на некоторых дисках.
- Итоговое окно после создания архива теперь появляется без задержки.
- Пароль зашифрованного архива корректно запоминается при создании независимо от включённых опций.

### [1.3]
- **Сортировка правой таблицы кликом по заголовку колонки.**
- **Единое меню «Работа с архивом»: создать, проверить, распаковать, информация об архиве.**
- **Выбранные колонка и направление сортировки запоминаются и восстанавливаются при следующем запуске.**
- Первый клик — по возрастанию, повторный — по убыванию; направление показано стрелкой.
- Строка «⬆ ..» всегда сверху; папки — выше архивов и файлов.
- Имена сортируются без учёта регистра и значков.
- Размеры и версии сортируются как числа, даты — по хронологии.
- Пустые версии всегда в конце, независимо от направления.
- При первом открытии таблица отсортирована по имени.
- «Обновить» (F5) перенесено в меню «Вид».
- «Поиск в архиве» (Ctrl+F) перенесено в «Работа с архивом».
- Меню «Переход» убрано: подъём наверх — через хлебные крошки и строку «⬆ ..».
- Пункт «Пароль архива» убран из меню: пароль задаётся в диалоге создания.
- Архивозависимые пункты меню неактивны, пока архив не открыт.

### [1.4]
- **Окно выбора источников при создании архива: дерево с чекбоксами (диски → папки → файлы) и ленивой загрузкой.**
- **Многотомные архивы: размер тома выбирается из готового списка или задаётся вручную.**
- **Теневые копии VSS для архивации открытых и заблокированных файлов.**
- Редактируемый список источников в диалоге создания: добавление и удаление путей.
- Чтение многотомных архивов через маску `_????.zpaq`.
- Автоматическая проверка свободного места: порог равен размеру источников и подставляется автоматически.
- Ручной порог проверки свободного места.
- Вторая копия архива в выбранную папку.
- Выбор режима проверки после создания: без проверки / тест / сверка с файловой системой / параноидальная.
- Пропуск заглушек OneDrive.
- Игнорирование ошибок доступа к файлам с записью в журнал ошибок.
- Выключение компьютера по завершении архивации.
- Создание самораспаковывающегося архива (SFX).
- Шаблоны дат в имени архива (`%year`, `%month`, `%day` и другие) и кнопка «Вставить дату».
- Расширенный набор алгоритмов хэширования: whirlpool, highway64/128/256, xxhashb, blake3b, sha1b/256b/3b, md5b и другие.
- Диалог создания с вертикальной прокруткой; высота подстраивается под главное окно.
- Галочка «длинные пути» активна только при наличии папок среди источников.
- Исправлено: аварийное завершение программы при «Отмена» в диалоге создания.
- Исправлено: переполнение при подсчёте размера больших папок.
- Исправлено: `-longpath` больше не передаётся для одиночных файлов.
- Исправлено: создание архива через меню брало папку из левого окна вместо выделения в правом.
- Исправлено: Enter в полях диалога создания больше не запускает архивацию.

### [1.5] — 2026-08-10
- **Интеграция с проводником: контекстное меню и ассоциация `.zpaq` — двойной клик открывает Rizpaq.**
- **Drag & Drop: бросьте файлы или папки на окно, чтобы создать архив.**
- **Лёгкий режим: распаковка, проверка и создание архива из контекстного меню без главного окна.**
- Повторный запуск не открывает второе окно — задача передаётся уже открытому Rizpaq.
- Ассоциация файлов устанавливается без прав администратора.

### [1.6] — 2026-08-16
- **Открытие файлов штатным приложением: двойной клик по файлу на диске или внутри архива.**
- **Удаление файлов и папок в корзину; корни дисков защищены.**
- **Нелатинские имена архивов: программа предлагает переименовать в транслит и сразу открывает.**
- Переименование файлов и папок; открытый архив не сбрасывает просмотр при переименовании.
- Диалог создания архива на три компактные вкладки, без прокрутки.
- И другое: автопроверка свободного места с запасом, исправления извлечения файлов и папок.

### [1.7] — 2026-08-18
- **Задачи резервного копирования (.rzt): сохранение всех настроек архива в портативный файл и запуск двойным кликом.**
- **Диалог прогресса архивирования: отдельное окно со скоростью, количеством файлов, временем до конца и секундомером.**
- **Запуск задач по расписанию без окна программы (для планировщика заданий).**
- Ассоциация файлов `.rzt`: двойной клик по задаче сразу запускает резервное копирование.
- Исправлено: при архивации больше не показывается «извлечение файлов»; скорость и число файлов теперь видны корректно.

### [1.7.1] — 2026-08-24
- **Продвинутое сжатие — визуальный конструктор параметра `-method`:** размер блока, предобработка, глубина поиска, модели контекста, живой предпросмотр.
- **Единое окно прогресса для архивации, распаковки и проверки:** процент, файлы, папки, размер, скорость, прошло, осталось, живой лог, сворачиваемая панель.
- **Уровни сжатия m0–m5 с понятными описаниями** (от «без сжатия» до «экстремального»).
- Все диалоги прогресса выглядят и ведут себя одинаково.

### [1.8.0] — 2026-09-04
- **Интеграция с Планировщиком задач Windows: создание, редактирование и удаление задач резервного копирования по расписанию прямо из интерфейса Rizpaq.**
- **Полностью невидимый фоновый режим: запланированные задачи запускаются без создания окон Qt и консоли `zpaqfranz`, не мешая работе пользователя.**
- **Умное редактирование задач: при выборе «Редактировать задачу…» открывается диалог создания с уже заполненными полями. Кнопка «💾 Сохранить» мгновенно перезаписывает текущий `.rzt` файл без запроса пути.**
- Гибкий планировщик: выбор частоты запуска с помощью удобных радио-кнопок (каждые N минут, часов, дней, недель или месяцев).
- Управление логами задач: выбор режима логирования (Кратко / Полный / Отключено), чтобы при частых запусках лог-файлы не занимали много места.
- Пункт «Открыть архив…» в меню «Файл» с горячей клавишей `Ctrl+O`.
- Горячая клавиша `Alt+Enter` для быстрого открытия «Информации об архиве».
- Полная переработка главного меню для соответствия стандартам UI.
- Кодировка статусов Планировщика: исправлено отображение «кракозябр» при чтении русских статусов задач.
- Отображение списка задач: исправлена ошибка, из-за которой задачи не показывались в окне Планировщика Rizpaq.
- Отсутствие меню «Справка»: исправлена ошибка инициализации меню.

### [1.9.0] — 12.09.2026
- **Поддержка универсальных архивов (ZIP, 7z, RAR) через мост 7-Zip.** Просмотр, навигация и извлечение файлов из этих форматов наравне с ZPAQ.
- **Мастер «Конвертировать в ZPAQ...».** Транскодирование любого ZIP/7z/RAR архива в высокоэффективный, версионный и дедуплицированный ZPAQ-архив одним кликом. Процесс идёт в фоне без блокировки интерфейса.
- **Диалог «Интеграция с проводником».** Отдельное окно для независимого управления ассоциациями файлов `.zpaq`, `.rzt`, `.zip`, `.7z` и `.rar` без конфликтов между ними.
- Новые пункты контекстного меню и меню «Архив»: «Конвертировать в ZPAQ…» и «Извлечь всё…» для универсальных архивов.
- Встроенные `7z.exe` и `7z.dll` для работы «из коробки» без дополнительных настроек.
- Фильтр диалога «Открыть архив» теперь включает `*.zip`, `*.7z`, `*.rar`.
- Улучшен парсинг прогресса: исправлено отображение ETA (Осталось) и Скорости для больших архивов.
- Извлечение через Drag & Drop больше не блокирует UI для больших архивов (окно прогресса с поддержкой отмены).
- Флаг `-longpath` больше не передаётся `zpaqfranz` при источнике-маске `*` (режим транскодирования), что устраняет ошибку «cannot get -longpath for this file».