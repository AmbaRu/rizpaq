# Rizpaq — Changelog

### Русский

**1.1**

- Создание архивов из папок и файлов.
- Выбор уровня сжатия: от хранения без сжатия до максимального.
- Выбор алгоритма хэширования файлов.
- Маски включения и исключения файлов.
- Дополнительные опции: длинные пути, дата создания файлов,
  работа без рекурсии, NTFS ADS, принудительное добавление XLS/PPT,
  отключение контрольных сумм и дедупликации.
- Комментарий к версии архива.
- Проверка архива сразу после создания.
- Итоговое окно после архивации: параметры сжатия, степень сжатия,
  результат проверки.
- Подменю «Проверка» с тремя режимами в контекстном меню
  по правой клавише мыши.
- Вместо украинского языка добавлен хинди.
- Исправлено создание архивов на путях с нелатинскими символами.
- Исправлено зависание интерфейса после создания архива.
- Исправлен конфликт между проверкой после создания и ручной проверкой.

**1.0**

- Проверка целостности архива: три режима — полная, все версии с
  контрольными суммами, параноидальная.
- Распаковка: извлечь одну версию или все версии сразу.
- В списке версий видны дата, время и число добавленных, изменённых
  и удалённых файлов.
- Меню «Работа с архивом» (информация, пароль, проверка, распаковка)
  и «Настройки» (путь к zpaqfranz, язык).
- Панель прогресса с секундомером и отменой при долгих операциях.
- Стабильная работа с большими архивами: корректное отображение
  содержимого, сводки и числа версий, в том числе при возврате
  к уже открытому архиву.

**0.9**

- Единое дерево дисков и архивов zpaq.
- Просмотр архива как обычной папки; несколько архивов открыты сразу.
- История версий, срезы «на версию N» и сравнение двух версий.
- Поиск по именам и путям с масками `*` и `?`.
- Извлечение файлов и папок с прогрессом и отменой.
- Поддержка паролей зашифрованных архивов.
- Информация об архиве.
- 14 языков интерфейса с переключением без перезапуска.
- Светлая тема, portable-режим, сохранение настроек и окна.
- Готовая сборка для Windows.

---

### English

**1.1**

- Create archives from folders and files.
- Compression level selection: from store (no compression) to maximum.
- File hashing algorithm selection.
- Include and exclude file masks.
- Extra options: long paths, store file creation date,
  no recursion, NTFS ADS, force re-add XLS/PPT,
  disable extra checksums and deduplication.
- Version comment for the archive.
- Test the archive right after creation.
- Completion window after archiving: compression parameters,
  compression ratio, test result.
- "Test" submenu with three modes in the right-click context menu.
- Hindi language added instead of Ukrainian.
- Fixed archive creation on paths with non-Latin characters.
- Fixed interface freeze after archive creation.
- Fixed conflict between post-creation test and manual test.

**1.0**

- Archive integrity testing: three modes — full, all-versions with
  checksums, paranoid.
- Unpacking: extract a single version or all versions at once.
- Version list shows date, time and the number of added, changed
  and removed files.
- "Work with archive" menu (info, password, test, unpack) and
  "Settings" menu (zpaqfranz path, language).
- Progress panel with a timer and cancel for long operations.
- Stable handling of large archives: contents, summary and version
  counts display correctly, including when returning to an already
  open archive.

**0.9**

- Unified tree of drives and zpaq archives.
- Browse an archive like a normal folder; multiple archives open at once.
- Version history, "at version N" slices and two-version comparison.
- Search by names and paths with `*` and `?` wildcards.
- File and folder extraction with progress and cancel.
- Password support for encrypted archives.
- Archive information.
- 14 interface languages, switchable without restart.
- Light theme, portable mode, saved settings and window state.
- Ready-to-run Windows build.