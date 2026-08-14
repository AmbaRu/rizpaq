Rizpaq — Changelog

Русский

1.4
- **Окно выбора источников при создании архива: дерево с чекбоксами (диски → папки → файлы) и ленивой загрузкой.**
- **Многотомные архивы: размер тома выбирается из готового списка или задаётся вручную.**
- **Теневые копии VSS для архивации открытых и заблокированных файлов.**
- Редактируемый список источников в диалоге создания: добавление и удаление путей.
- Чтение многотомных архивов через маску _????.zpaq.
- Автоматическая проверка свободного места: порог равен размеру источников и подставляется автоматически.
- Ручной порог проверки свободного места.
- Вторая копия архива в выбранную папку.
- Выбор режима проверки после создания: без проверки / тест / сверка с файловой системой / параноидальная.
- Пропуск заглушек OneDrive.
- Игнорирование ошибок доступа к файлам с записью в журнал ошибок.
- Выключение компьютера по завершении архивации.
- Создание самораспаковывающегося архива (SFX).
- Шаблоны дат в имени архива (%year, %month, %day и другие) и кнопка «Вставить дату».
- Расширенный набор алгоритмов хэширования: whirlpool, highway64/128/256, xxhashb, blake3b, sha1b/256b/3b, md5b и другие.
- Диалог создания с вертикальной прокруткой; высота подстраивается под главное окно.
- Галочка «длинные пути» активна только при наличии папок среди источников.
- Исправлено: аварийное завершение программы при «Отмена» в диалоге создания.
- Исправлено: переполнение при подсчёте размера больших папок.
- Исправлено: -longpath больше не передаётся для одиночных файлов.
- Исправлено: создание архива через меню брало папку из левого окна вместо выделения в правом.
- Исправлено: Enter в полях диалога создания больше не запускает архивацию.

1.3
- **Сортировка правой таблицы кликом по заголовку колонки.**
- **Единое меню «Работа с архивом»: создать, проверить, распаковать, информация об архиве.**
- **Строка «⬆ ..» всегда сверху; папки — выше архивов и файлов.**
- Первый клик — по возрастанию, повторный — по убыванию; направление показано стрелкой.
- Имена сортируются без учёта регистра и значков.
- Размеры и версии сортируются как числа, даты — по хронологии.
- Пустые версии всегда в конце, независимо от направления.
- Выбранные колонка и направление сортировки запоминаются и восстанавливаются при следующем запуске.
- При первом открытии таблица отсортирована по имени.
- «Обновить» (F5) перенесено в меню «Вид».
- «Поиск в архиве» (Ctrl+F) перенесено в «Работа с архивом».
- Меню «Переход» убрано: подъём наверх — через хлебные крошки и строку «⬆ ..».
- Пункт «Пароль архива» убран из меню: пароль задаётся в диалоге создания.
- Архивозависимые пункты меню неактивны, пока архив не открыт.

1.2
- **Исправлено зависание программы при открытии архивов.**
- **Автоматическая подстановка латинского имени при создании архива из папки или файла с нелатинским названием.**
- **Защита от открытия и проверки архивов с нелатинскими именами: вместо зависания показывается предупреждение с подсказкой.**
- Устранена ложная ошибка «невозможно записать» при создании архивов на некоторых дисках.
- Итоговое окно после создания архива теперь появляется без задержки.
- Пароль зашифрованного архива корректно запоминается при создании независимо от включённых опций.

1.1
- **Создание архивов из папок и файлов.**
- **Выбор уровня сжатия: от хранения без сжатия до максимального.**
- **Выбор алгоритма хэширования файлов.**
- Маски включения и исключения файлов.
- Дополнительные опции: длинные пути, дата создания файлов, работа без рекурсии, NTFS ADS, принудительное добавление XLS/PPT, отключение контрольных сумм и дедупликации.
- Комментарий к версии архива.
- Проверка архива сразу после создания.
- Итоговое окно после архивации: параметры сжатия, степень сжатия, результат проверки.
- Подменю «Проверка» с тремя режимами в контекстном меню по правой клавише мыши.
- Вместо украинского языка добавлен хинди.
- Исправлено создание архивов на путях с нелатинскими символами.
- Исправлено зависание интерфейса после создания архива.
- Исправлен конфликт между проверкой после создания и ручной проверкой.

1.0
- **Проверка целостности архива: три режима — полная, все версии с контрольными суммами, параноидальная.**
- **Распаковка: извлечь одну версию или все версии сразу.**
- **В списке версий видны дата, время и число добавленных, изменённых и удалённых файлов.**
- Меню «Работа с архивом» (информация, пароль, проверка, распаковка) и «Настройки» (путь к zpaqfranz, язык).
- Панель прогресса с секундомером и отменой при долгих операциях.
- Стабильная работа с большими архивами: корректное отображение содержимого, сводки и числа версий, в том числе при возврате к уже открытому архиву.

0.9
- **Просмотр архива как обычной папки; несколько архивов открыты сразу.**
- **Единое дерево дисков и архивов zpaq.**
- **История версий, срезы «на версию N» и сравнение двух версий.**
- Поиск по именам и путям с масками `*` и `?`.
- Извлечение файлов и папок с прогрессом и отменой.
- Поддержка паролей зашифрованных архивов.
- Информация об архиве.
- 14 языков интерфейса с переключением без перезапуска.
- Светлая тема, portable-режим, сохранение настроек и окна.
- Готовая сборка для Windows.

English

1.4
- **Source-selection window when creating an archive: a tree with checkboxes (drives → folders → files) and lazy loading.**
- **Multipart archives: the volume size is chosen from a ready list or set manually.**
- **VSS shadow copies for archiving open and locked files.**
- Editable source list in the create dialog: add and remove paths.
- Reading multipart archives via the _????.zpaq mask.
- Automatic free-space check: the threshold equals the source size and is filled in automatically.
- Manual free-space check threshold.
- Second copy of the archive to a chosen folder.
- Post-creation test mode selection: none / test / verify against filesystem / paranoid.
- Skipping OneDrive placeholders.
- Ignoring file access errors with an error log.
- Shutting down the computer when archiving completes.
- Creating a self-extracting archive (SFX).
- Date templates in the archive name (%year, %month, %day and others) and an "Insert date" button.
- Extended set of hashing algorithms: whirlpool, highway64/128/256, xxhashb, blake3b, sha1b/256b/3b, md5b and others.
- Create dialog with vertical scrolling; height adapts to the main window.
- The "long paths" checkbox is active only when folders are among the sources.
- Fixed: program crash on "Cancel" in the create dialog.
- Fixed: overflow when measuring large folders.
- Fixed: -longpath is no longer passed for single files.
- Fixed: creating an archive via the menu took the folder from the left pane instead of the selection in the right pane.
- Fixed: Enter in the create dialog fields no longer starts archiving.

1.3
- **Right-hand table sorting by clicking a column header.**
- **Unified "Archive operations" menu: create, test, extract, archive info.**
- **The "⬆ .." row always on top; folders above archives and files.**
- First click — ascending, second click — descending; the direction is shown by an arrow.
- Names sorted case- and icon-insensitively.
- Sizes and versions sorted as numbers, dates — chronologically.
- Empty versions always at the bottom regardless of direction.
- The chosen sort column and direction are remembered and restored on the next launch.
- On first open the table is sorted by name.
- "Refresh" (F5) moved to the "View" menu.
- "Search in archive" (Ctrl+F) moved to "Archive operations".
- The "Go" menu removed: upward navigation is via breadcrumbs and the "⬆ .." row.
- The "Archive password" item removed from the menu: the password is set in the create dialog.
- Archive-dependent menu items are disabled while no archive is open.

1.2
- **Fixed program freeze when opening archives.**
- **Automatic Latin name suggestion when creating an archive from a folder or file with a non-Latin name.**
- **Protection against opening and testing archives with non-Latin filenames: a warning with guidance is shown instead of freezing.**
- Fixed false "cannot write" error when creating archives on some drives.
- Completion window after archive creation now appears without delay.
- Encrypted archive password is correctly remembered during creation regardless of enabled options.

1.1
- **Create archives from folders and files.**
- **Compression level selection: from store (no compression) to maximum.**
- **File hashing algorithm selection.**
- Include and exclude file masks.
- Extra options: long paths, store file creation date, no recursion, NTFS ADS, force re-add XLS/PPT, disable extra checksums and deduplication.
- Version comment for the archive.
- Test the archive right after creation.
- Completion window after archiving: compression parameters, compression ratio, test result.
- "Test" submenu with three modes in the right-click context menu.
- Hindi language added instead of Ukrainian.
- Fixed archive creation on paths with non-Latin characters.
- Fixed interface freeze after archive creation.
- Fixed conflict between post-creation test and manual test.

1.0
- **Archive integrity testing: three modes — full, all-versions with checksums, paranoid.**
- **Unpacking: extract a single version or all versions at once.**
- **Version list shows date, time and the number of added, changed and removed files.**
- "Work with archive" menu (info, password, test, unpack) and "Settings" menu (zpaqfranz path, language).
- Progress panel with a timer and cancel for long operations.
- Stable handling of large archives: contents, summary and version counts display correctly, including when returning to an already open archive.

0.9
- **Browse an archive like a normal folder; multiple archives open at once.**
- **Unified tree of drives and zpaq archives.**
- **Version history, "at version N" slices and two-version comparison.**
- Search by names and paths with `*` and `?` wildcards.
- File and folder extraction with progress and cancel.
- Password support for encrypted archives.
- Archive information.
- 14 interface languages, switchable without restart.
- Light theme, portable mode, saved settings and window state.
- Ready-to-run Windows build.