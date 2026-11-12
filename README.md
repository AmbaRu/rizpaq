# Rizpaq

**ZPAQ power without the console. One app for every archive you own.**

Rizpaq is a desktop archiver for Windows. It puts the full strength of
[zpaqfranz](https://github.com/fcorbelli/zpaqfranz) — file versions, global
deduplication, one of the best compression ratios available — behind a clean,
familiar interface. Alongside it, Rizpaq opens, extracts, and *converts*
ZIP, 7z, and RAR archives, so a single tool covers what used to need three.
<img width="1166" height="626" alt="3" src="https://github.com/user-attachments/assets/1dca607d-cecc-477c-9f14-7ca6bf58d35f" />

Every archive can also be wrapped into a **PAR2 recovery set** kept
right next to it: background bit-rot becomes a detectable, repairable
problem instead of a silent loss.

No install. No console. No scripting. Three engines are built in.

---

## What problem does it solve

### "I want my files to have a history, not just a copy"

An ordinary archive is a snapshot: one moment, frozen. Restore it next year
and you get *that* moment back — every file, all of it, or nothing.

ZPAQ archives are different. Every run *adds a version*. Each file carries
its own timeline: as it was on Monday, changed on Tuesday, deleted on
Wednesday, restored on Thursday. Identical content — across files, across
versions, across years — is stored **once**. A 50 GB photo library that
changes by 200 MB a month does not become a 600 GB archive at year's end.
It becomes a 51 GB archive with twelve restore points.

Rizpaq turns that timeline into something you can *see*: open the archive,
click a version, watch the folder as it looked on that day. Compare two
versions and see exactly what was added, changed, or removed. Extract one
file as it was six months ago — without touching the rest.

### "I want backups to run themselves and never bother me"

The usual home-backup routine ends the same way: remembered on Sunday,
forgotten on Monday, abandoned by Friday.

Rizpaq has a second personality for exactly this. In the **Backup profile**,
the window becomes a tree of your backup work: each *work* — "what to back
up", with its sources, destination, password and masks — sits at the top,
and its *jobs* — "how and when" — hang below it. A single work may have as
many jobs as you like: one runs the same folder daily with a full test,
another runs it monthly without compression, a third runs it weekly to a
USB drive. One double-click on a job runs it now. A button in the row
schedules it — without leaving the tree. Windows Task Scheduler runs it
silently in the background, on a schedule you pick, with no window, no tray
icon, no popup: *it just happens*.

A single container file — `tasks.rzp` — holds every work and every job.
Move it to a new machine and the whole backup plan moves with it.

### "I want to know my archives are actually intact"

A backup you have never restored is not a backup — it is a hope. Files get
bit-rotted, drives develop bad sectors, a power cut leaves an archive half
written. If you only find out about it the day you need the data, it is too
late.

Rizpaq can check archives on a schedule. Alongside a *backup job* — "make
an archive" — a work can have a *check job*: "verify that archive". Five
check modes are available, from a quick pass over every block to a paranoid
one that unpacks the whole archive to a temporary folder and compares every
hash against what was stored — plus a PAR2 verification that asks whether
the recovery set still matches the archive. Results are written to the same per-job log,
and the tree shows the date, status and outcome of the last run — right next
to the backup jobs they belong to.

A check job is not a special kind of thing you have to learn. It sits under
the same work, is scheduled the same way, and appears in the same Windows
Task Scheduler list as everything else.

A PAR2 set can be verified on a schedule too. The outcome is honest: a
damaged archive is an error with the reason spelled out in the tree
("Error — set not created"), and hovering the status explains what
happened without opening the log.

### "I want to open that RAR, and I want my old ZIPs to stop wasting space"

Rizpaq reads ZIP, 7z, and RAR through an embedded 7-Zip bridge. Browse them
like any folder, extract a file, extract everything. Then — the trick no
other archiver does — **convert them to ZPAQ**. In one click, an old RAR
full of duplicates becomes a deduplicated, versioned ZPAQ archive, often
noticeably smaller, ready to be updated incrementally from now on.

---

## Two profiles, one program

Rizpaq has two interfaces for two different habits. The engine, the
languages, the themes, the passwords, the scheduler — all shared. Only the
main panel and its action buttons change.

### Archive profile — for working with files

What you expect from an archiver: a tree of drives on the left, a table of
contents on the right, breadcrumbs on top. Drop a folder in, get an archive.
Double-click inside, get a file. Search by name, filter by version, extract,
convert, compare. The whole ZPAQ toolset, visually.

### Backup profile — for running things on a schedule

No file tree. Instead — a two-level tree of works and jobs. A *work* holds
what is common to the whole backup: sources, destination, password, include
and exclude masks, comment. A *job* holds everything that can differ between
runs of the same work: compression level and method, hash, verification
mode, VSS, SFX, chunking, second copy, error log, shutdown, schedule, log
mode. Every work shows, at a glance, its archive size; every job shows its
schedule, its next run, its last run and its status.

A job is one of two kinds:

- **Backup job** — makes an archive. All the compression, hashing,
  verification and scheduling options above.
- **Check job** — verifies an existing archive. Five modes, from a quick
  block check to a full paranoid comparison against a fresh extract, plus
  a PAR2 set verification.

The two are easy to tell apart at a glance: the tree gives them different
icons. In the Windows Task Scheduler, their task names also differ, so a
list of scheduled tasks is readable at once.

Actions that belong to a job — run now, edit, schedule, open the archive,
check it — sit on the row itself. Actions that belong to a work — edit the
work, open its archive, add a job, delete the work — sit in the work's
context menu. The whole backup plan stays visible as a tree.

Editing the work itself has its own dialog: name, sources, destination,
comment, include and exclude masks, password. Password is shown as a
status — "set" or "not set" — with two buttons to change or clear it,
because a pair of password fields with "leave blank to keep" would make
"keep" and "clear" indistinguishable.

On first launch, Rizpaq asks which profile you want. Either can be chosen
later from the top bar or from **Settings → Profile** — the switch is
instant, and nothing you were doing is lost.

---

## What is inside

### Creating archives
- Three-tab creation dialog: sources, compression, advanced — no scrolling.
- **Work name** and **job name** fields — both optional, both editable later.
- Levels m0–m5 (from "store" to "extreme"), or a full **visual `-method`
  constructor**: block size, preprocessing, search depth, and context models
  (c, i, a, w, m, s, t) with a live preview of the resulting parameter string.
- Choice of hash (xxhash, blake3, sha1/256/3, whirlpool, highway64/128/256...).
- Include/exclude masks, comment, password, encryption.
- **Multipart archives** — split into volumes, or read existing ones through
  the `_????.zpaq` mask.
- **Self-extracting (SFX)** archives.
- **VSS shadow copies** — pack files that are open or locked.
- Automatic free-space check with a small headroom.
- Optional **second copy** of the archive into another folder after creation.
- **Post-creation check**: none, quick test, verify against filesystem, or
  paranoid mode.

### Working with archives
- The whole archive as a normal folder: browse, search, sort.
- **Instant reopening.** The first time an archive is opened, its file list
  is read from the engine — as before. From then on that list is kept in a
  local cache, and every later open of an unchanged archive is immediate:
  no engine run, no waiting. The cache follows the archive — if the file has
  changed since it was last seen, the listing is read from the engine again
  and the cache is updated. On large archives, this is the difference between
  seconds and no noticeable pause at all.
- **Versions** — restore a file, a folder, or the entire archive as of any
  earlier moment.
- **Compare two versions** — what was added, changed, removed, with sizes and
  dates side by side.
- **Seven check modes** — full (blocks and CRC-32), all versions with
  checksums, verify against sources, paranoid (extract and compare every
  hash), verify against the filesystem (`v`), sync with sources, and PAR2
  set verification. The last three answer different questions: verify
  against sources uses what the archive itself recorded, `v` compares the
  archive with the files as they are on disk now, and `sync` compares it
  with the source folders and lists what a new backup would change.
- Open a file from inside an archive with its associated application:
  Rizpaq extracts it to a temporary folder and hands it to Windows.
- **Search across all your archives.** "Archive → Search all archives"
  (Ctrl+Shift+F) looks for names and paths in every archive the program
  knows about, not only the open one. Plain text or `*`/`?` masks;
  results show archive, path, size, version and date, and a double-click
  opens the archive where the file was found.
- **The archive catalog.** "Archive → All archives on this computer…"
  scans the folders you choose for zpaq archives (multipart sets become
  one row with the combined size), shows size, date, indexed-entry
  count and a "file missing" mark, and can read the found listings
  right away so global search sees them. The folder choice is
  remembered.
- Passwords stored securely alongside your config.

### Backup tasks and scheduling
- A portable `tasks.rzp` container holds every work and job. The container is
  written safely and read defensively, so a crash mid-save never leaves it
  corrupt.
- **Two kinds of job under one work**: a backup job and a check job. The
  context menu of a work offers "Add backup job…", "Add check job…" and
  "Add PAR2 check job…" as separate commands.
- **A check job has only what applies to it**: check mode, schedule, log
  mode. No compression, no hash, no VSS — those are properties of a backup
  job and do not appear in the check dialog.
- **Seven check modes**, matching the manual "Test" menu exactly: full
  (blocks and CRC-32), all versions with checksums, verify against sources,
  paranoid (extract into a temporary folder and compare every hash),
  verify archive (PAR2) — the check that the recovery set still matches
  the current archive, verify against the filesystem (`v`), and sync with
  sources (`sync`) — the pre-flight that lists what a new backup would add,
  change or lose, without writing anything.
- **Edit the work itself** from its context menu: name, sources, destination,
  comment, include and exclude masks, password. Everything that is common to
  all jobs of the work — and only that.
- Run a job by double-clicking it in the tree, or by a single button on its
  row. Edit a job in the same dialog it was created with.
- Add a new job to an existing work from the work's context menu — the new
  job inherits the work's sources, destination and password, and you only
  set what is different.
- Schedule through the built-in Windows Task Scheduler dialog, without ever
  opening `schtasks` or the Task Scheduler GUI.
- **Silent execution** — no window, no console, no popup. Runs at 3 a.m. on
  a server, runs at 8 a.m. on your laptop: same container, same behaviour.
- **Two jobs cannot corrupt the same archive.** If you start a job by hand
  while the Task Scheduler is already running the same one, the second
  process refuses in a fraction of a second instead of silently overwriting
  what the first is writing. The archive is safe, and the second job is
  marked **Busy** in the tree — neither error nor success, just "not now".
- **Two windows cannot lose each other's edits.** The tasks container is
  protected by a file lock held for the whole read-modify-write cycle, so
  editing a work in the window while a scheduled job updates its status in
  the background never loses either change.
- **The tree refreshes itself.** When a scheduled job finishes and writes
  its status into the container, the Backup page notices and updates the
  tree — no need to press "Refresh".
- **Task Scheduler synchronization** — the container and the Scheduler
  sometimes drift apart (a work was renamed, the tasks folder was changed,
  a task was deleted by hand). A "Synchronize…" dialog shows the full
  picture — what to add, what to remove, what to unregister — and lets you
  apply only the pieces you approve. A faster "Remove orphans…" button
  handles the one category users run into most often: tasks in the
  Scheduler that no longer have a job in the container.
- **Log control** — short, full, or off, per job, so frequent runs don't
  fill the disk.
- The tree shows, at a glance, which jobs are scheduled and when they run
  next; if a job isn't scheduled yet, a button in the row lets you schedule
  it right there.
- **Protection dashboard** — one window over every work and job: last
  status, last run, archive size, indexed file count and the state of the
  PAR2 set. Three views of the same data: a graph where each job is an
  oval with backup, check and PAR2 satellites (filled means the action
  happened, dashed means it never did); run cards built from the container
  log; and a precise table with filter tiles — all, OK, errors, busy,
  never run, no PAR2 set. Read-only: the dashboard never writes into the
  archive.
- **Every run lands in the log.** Runs started from the window now write
  their outcome into `tasks.rzp.log` in the same format as scheduled ones,
  so run cards and log history show the full activity, not just the Task
  Scheduler's part. A job with log mode "off" stays out of the history by
  design.

### Continuous backup, dedup report and notifications (3.0)
- **Continuous backup** — a new schedule, "Continuous (on changes)", with an
  interval of 1 to 60 minutes. Rizpaq compares the archive with the source
  folders itself and starts a backup only when something actually changed;
  when nothing changed, the run is skipped and the log says so.
- **Deduplication report** — the archive information window now shows how
  many bytes all versions added, how much the archive takes on disk, how much
  was saved and by how much (the ratio). No extra engine call is needed: the
  numbers come from the archive information that was already fetched.
- **Telegram notifications** — get a message when a job finishes or fails.
  Choose "off", "only errors" or "all results" in Settings → Notifications…,
  then paste the bot token and the chat id. Notifications work for manual
  runs as well, and a failed send never breaks the job. If the send fails,
  the reason is written to `rizpaq_notify.log` next to your settings.

### Archive protection (PAR2)
- Every archive can carry a **PAR2 recovery set** — protection files kept
  right next to the archive. The `par2` engine is bundled.
- Create the set in one checkbox in the backup job (the "Protection" tab) —
  it is built right after a successful backup — or manually: right-click
  an archive → *Create a PAR2 set…*. Manual creation asks for its
  parameters — redundancy, block size, threads — and remembers the
  choice for the session.
- **Verify the set with the fifth check mode** — "Verify archive (PAR2)".
  The verdict names the problem exactly: nothing; damaged and repairable;
  unrepairable; set missing — or "set outdated: the archive was rewritten
  by a newer backup", with both sizes.
- **Verify the set on a schedule.** "Add PAR2 check job…" in the work
  context menu creates a normal scheduled check with the PAR2 mode
  preselected; "Check PAR2" in the same menus runs a one-off check
  without creating a job. The tree records the date, the run counter and
  an honest outcome: a damaged archive is an error, not a green
  "success".
- **The reason is visible without opening the log.** The status column
  reads "Error — set not created", "Error — archive damaged" and the
  like; hovering the status shows the full sentence — what happened and
  what to do — plus the time of the last run.
- **A refusal is visible.** Clicking "Check PAR2" when there is nothing
  to check shows a dialog with an explanation and advice, not a silent
  status-bar note.
- **Restore from PAR2.** If verification finds damage, a repair can return
  the archive to a whole state. Rizpaq guards against the rollback trap: a
  repair with a set that does not match the current archive size is
  refused, an equal-size repair asks first — the set would put back the
  version from its day. Repair is manual only: it rewrites the archive,
  so it is never scheduled.
- Recreating a set replaces the old one with no gap in protection; if
  the archive has not changed since, recreation is skipped.
- Honest limits: the set protects the data from corruption, but NOT from
  the death of the medium — for that there is the second copy.
  Multi-volume archives are not covered by the set yet.

### Universal formats and transcoding
- Open ZIP, 7z, and RAR through the embedded 7-Zip bridge.
- Extract everything, or a single item, or a folder.
- **Convert to ZPAQ…** — turn any ZIP, 7z, or RAR into a deduplicated,
  versioned ZPAQ archive. Runs in the background, cleans up temp files.
- Manage `.zpaq`, `.rzp`, `.zip`, `.7z`, `.rar` associations independently
  through the Explorer Integration dialog — turn any one on or off without
  affecting the others.

### Explorer integration
- Right-click menu on `.zpaq`, `.zip`, `.7z`, `.rar`:
  *Add to archive…*, *Extract here*, *Test*, *Convert to ZPAQ*.
- Double-click a `.zpaq` to open it, a `.rzp` to open the tasks container
  in the Backup profile.
- **Drag & drop** both ways: drop files onto the window to create an archive;
  drag files out of an archive into Explorer to extract them.
- No administrator rights needed for the association.

### Look and feel
- **Two themes**: *Soft Azure* (the original) and *White Air* (near-white
  surfaces, hairline borders, muted accent). Switched on the fly, no restart.
- **Ten interface languages** — English, Русский, Italiano, Deutsch,
  Français, Español, 中文, Português, 日本語, Polski — plus any additional
  one you drop into `locales/`. No rebuild needed.
- **"Working…" notice** for long operations: a small non-blocking window
  names the current phase, counts seconds, and offers Cancel. Waits 400 ms
  before showing, so fast operations never blink.
- **Unified progress window** for every operation — archive, extract, test —
  with percent, files, folders, size, speed, elapsed, ETA, and a live log.

### Staying up to date
- **Automatic update check** — at most once a day at startup, against
  `rizpaq.ru`; "Help → Check for updates…" checks on demand. The silent
  check can be disabled, and a specific version can be postponed.
- **One-click installation.** The new build is downloaded over HTTPS
  (SHA256 is verified when the manifest provides it); Rizpaq closes, an
  update script swaps `Rizpaq.exe` and `_internal` and starts the
  program again. Settings, the index and task files stay in place, and
  a failed update is rolled back to the previous files.

### Portable mode
Create an empty `portable.txt` next to `Rizpaq.exe` and all settings,
passwords, the tasks container, and languages move with the program. Ideal
for a USB stick.

---

## Quick start

1. Download the latest release, unpack anywhere.
2. Run `Rizpaq.exe`.

The `zpaqfranz`, `7z`, and `par2` engines are already inside — nothing
to install.

**Your first archive in 30 seconds.**
Drag a folder onto the window, press OK in the dialog, done.

**Your first scheduled backup in 1 minute.**
Open the **Backup** profile, press "Create Archive…", set sources and
destination, then "📅 Schedule…" in the dialog — pick "Daily at 02:00".
The work, its first job and its Windows task are created at once; the job
runs silently from now on.

**Your first scheduled check in 30 seconds.**
Right-click an existing work → "Add check job…". Pick the check mode —
"Full" is a good default — and press "📅 Schedule…". The check runs on its
own schedule, writes to the same per-job log, and shows up in the tree next
to the backup jobs it verifies.

**Protect an archive with PAR2 in 30 seconds.**
Right-click an archive → *Create a PAR2 set…* — the dialog offers
redundancy, block size and threads; the defaults are fine. Or open the
"Protection (PAR2)" top menu. The set is built next to the archive;
afterwards *Verify PAR2 set…* in the same menu confirms the archive
and its set agree.

**Turn that old ZIP into something better.**
Right-click → *Convert to ZPAQ…*. Pick a destination. Done.

---

## Requirements

- Windows 10 or 11.

## Languages

English, Русский, Italiano, Deutsch, Français, Español, 中文, Português,
日本語, Polski. Your own language can be added by dropping
`locales/<code>.json` next to the app — no rebuild, no compiler, no
external tool. On first start the interface matches your system language.
Since 2.8.0 every language is fully native — the dashboard, the archive
catalog, dialogs and messages included; no English stubs are left.

---

---

# Rizpaq (Русская версия)

**Вся мощь ZPAQ без консоли. Одно приложение для всех архивов.**

Rizpaq — настольный архиватор для Windows. Он прячет за аккуратным
интерфейсом всю силу [zpaqfranz](https://github.com/fcorbelli/zpaqfranz):
версии файлов, глобальную дедупликацию и одно из лучших сжатий среди
существующих. Рядом с этим Rizpaq открывает, распаковывает и
**конвертирует** архивы ZIP, 7z и RAR — то есть один инструмент
закрывает то, для чего раньше нужно было три.

Любой архив можно ещё обернуть в **PAR2-набор восстановления**,
который живёт рядом с архивом: тихая порча битов превращается в
обнаружимую и исправимую неисправность, а не в молчаливую потерю.

Без установки. Без консоли. Без скриптов. Три движка встроены.

---

## Какую задачу решает

### «Хочу, чтобы у файлов была история, а не просто копия»

Обычный архив — это снимок: один момент, застывший. Достанешь его
через год — получишь *тот* момент обратно, целиком или никак.

Архивы ZPAQ устроены иначе. Каждый запуск *добавляет версию*. У каждого
файла — своя временная линия: каким он был в понедельник, что в нём
изменилось во вторник, как его удалили в среду, как восстановили в
четверг. Одинаковое содержимое — между файлами, между версиями, между
годами — хранится **один раз**. Библиотека фотографий на 50 ГБ, которая
меняется на 200 МБ в месяц, к концу года превратится не в 600 ГБ архива,
а в 51 ГБ с двенадцатью точками восстановления.

Rizpaq превращает эту временную линию в то, что можно *увидеть*:
открываешь архив, щёлкаешь по версии — и папка выглядит так, как
выглядела в тот день. Сравниваешь две версии — видно, что добавилось,
что изменилось, что исчезло. Достаёшь один файл таким, каким он был
полгода назад, не трогая остальное.

### «Хочу, чтобы бэкапы делались сами и не мешали»

Домашний бэкап обычно заканчивается одинаково: вспомнил в воскресенье,
забыл в понедельник, бросил к пятнице.

Для этого у Rizpaq есть второе лицо. В **профиле «Бэкап»** окно
становится деревом ваших работ: сверху — *работа*, то есть «что
бэкапим» (источники, назначение, пароль, маски, комментарий), а под
ней — её *задания*, то есть «как и когда». У одной работы может быть
сколько угодно заданий: одно гоняет ту же папку ежедневно с полной
проверкой, другое — раз в месяц без сжатия, третье — еженедельно на
флешку. Двойной клик по заданию запускает его сейчас. Кнопка в строке
запланирует его — не выходя из дерева. Планировщик Windows выполняет
его тихо в фоне, без окна, без значка в трее, без всплывающих
сообщений: *оно просто происходит*.

Один файл-контейнер — `tasks.rzp` — хранит все работы и все задания
сразу. Перенесите его на другую машину — план бэкапов переедет вместе
с ним.

### «Хочу знать, что мои архивы действительно целы»

Бэкап, который вы ни разу не восстанавливали, — это не бэкап, а
надежда. Файлы портятся от битых секторов, приводы сбоят, отключение
питания оставляет архив наполовину записанным. Если узнать об этом
только в тот день, когда данные понадобились, — уже поздно.

Rizpaq умеет проверять архивы по расписанию. Наряду с *заданием
бэкапа* — «создать архив» — у работы может быть *задание проверки*:
«убедиться, что архив цел». Семь режимов проверки — от быстрого
прохода по всем блокам до параноидального, который распаковывает весь
архив во временную папку и сверяет каждый хэш с тем, что было
сохранено, — плюс проверка архива по его PAR2-набору восстановления
и сверка с папками-источниками перед бэкапом: она показывает, что
добавится, изменится или пропадёт, ничего не записывая. Результат
пишется в тот же лог задания, а в дереве рядом с
заданиями бэкапа видны дата, статус и исход последней проверки.

Задание проверки — не отдельная сущность, которую надо изучать
заново. Оно живёт под той же работой, планируется точно так же и
появляется в том же списке Планировщика Windows, что и всё остальное.

Проверять по расписанию можно и PAR2-набор. Исход честный:
повреждённый архив — ошибка, и причина названа прямо в дереве
(«Ошибка — набор не создан»), а наведение мыши на статус объясняет,
что случилось, без открытия лога.

### «Хочу открыть этот RAR и чтобы старые ZIP-ы перестали занимать место»

Rizpaq читает ZIP, 7z и RAR через встроенный мост к 7-Zip. Смотришь
их как обычную папку, распаковываешь один файл или всё сразу. А потом
— трюк, которого нет ни в одном другом архиваторе — **конвертирует в
ZPAQ**. Один клик: старый RAR, набитый дублями, превращается в
дедуплицированный, версионный ZPAQ-архив, часто заметно меньше, готовый
с этого момента обновляться инкрементально.

---

## Два профиля, одна программа

У Rizpaq два интерфейса под две разные привычки. Движок, языки,
оформление, пароли, планировщик — общие. Меняются только главная панель
и кнопки действий на ней.

### Профиль «Архиватор» — для работы с файлами

То, что ждёшь от архиватора: дерево дисков слева, таблица содержимого
справа, хлебные крошки сверху. Брось папку в окно — получи архив.
Двойной клик внутри — получи файл. Ищи по имени, фильтруй по версии,
распаковывай, конвертируй, сравнивай. Весь набор ZPAQ — наглядно.

### Профиль «Бэкап» — для запуска по расписанию

Дерева файлов нет. Вместо него — двухуровневое дерево работ и заданий.
*Работа* хранит то, что общее для всего бэкапа: источники, назначение,
пароль, маски включения и исключения, комментарий. *Задание* хранит
всё, что может отличаться между запусками одной и той же работы:
уровень и метод сжатия, хэш, режим проверки, VSS, SFX, разбиение на
тома, вторая копия, журнал ошибок, выключение ПК, расписание, режим
лога. У каждой работы сразу виден размер архива; у каждого задания —
расписание, следующий запуск, последний запуск и статус.

Задание бывает двух видов:

- **Задание бэкапа** — делает архив. Всё про сжатие, хэш, проверку и
  расписание относится к нему.
- **Задание проверки** — проверяет готовый архив. Семь режимов, от
  быстрой проверки блоков до параноидальной сверки с полной
  распаковкой, плюс проверка PAR2-набора и сверка с источниками
  перед бэкапом.

Виды заданий легко различить с одного взгляда: в дереве у них разные
значки. В Планировщике Windows имена задач тоже различаются, поэтому
список запланированного читается сразу.

Действия, которые относятся к заданию — запустить сейчас,
отредактировать, запланировать, открыть архив, проверить — стоят в
строке самого задания. Действия, которые относятся к работе —
редактировать работу, открыть архив, добавить задание, удалить работу
— стоят в контекстном меню работы. Весь план бэкапов остаётся видимым
как дерево.

У редактирования самой работы — свой диалог: имя, источники,
назначение, комментарий, маски включения и исключения, пароль. Пароль
показывается статусом — «задан» или «не задан» — и двумя кнопками:
задать или убрать. Пара текстовых полей с «оставьте пустым, чтобы не
менять» сделала бы «не менять» и «убрать» неразличимыми.

При первом запуске Rizpaq спросит, какой профиль нужен. Переключить
можно в любой момент — в верхней полосе или через
**Настройки → Профиль**. Переключение мгновенное, ничего не теряется.

---

## Что внутри

### Создание архивов
- Диалог на трёх вкладках: источники, сжатие, дополнительные — без прокрутки.
- Поля **«Название работы»** и **«Название задания»** — оба необязательны,
  оба можно поменять потом.
- Уровни m0–m5 (от «хранения» до «экстремального»), либо полноценный
  **визуальный конструктор `-method`**: размер блока, предобработка,
  глубина поиска, модели контекста (c, i, a, w, m, s, t) — с живым
  предпросмотром итоговой строки параметра.
- Выбор хэша (xxhash, blake3, sha1/256/3, whirlpool, highway64/128/256...).
- Маски включения и исключения, комментарий, пароль, шифрование.
- **Многотомные архивы** — разбить на тома или читать существующие
  через маску `_????.zpaq`.
- **Самораспаковывающиеся (SFX)** архивы.
- **Теневые копии VSS** — упаковка открытых и заблокированных файлов.
- Автоматическая проверка свободного места с небольшим запасом.
- Опциональная **вторая копия** архива в другую папку после создания.
- **Проверка после создания**: без проверки, быстрый тест, сверка с
  файловой системой или параноидальный режим.

### Работа с архивами
- Весь архив как обычная папка: просмотр, поиск, сортировка.
- **Мгновенное повторное открытие.** В первый раз листинг архива
  читается движком, как и раньше. Дальше он лежит в локальном кэше,
  и каждое следующее открытие неизменившегося архива — мгновенно:
  без запуска движка, без ожидания. Кэш следует за архивом: если файл
  изменился, листинг перечитывается движком, и кэш обновляется. На
  больших архивах это разница между «секунды» и «без заметной паузы
  вообще».
- **Версии** — восстановить файл, папку или весь архив на любой
  момент в прошлом.
- **Сравнение двух версий** — что добавлено, изменено, удалено,
  с размерами и датами рядом.
- **Семь режимов проверки** — от блоков до параноидального, сверка
  архива с диском (`v`), сверка с источниками (`sync`) и проверка
  PAR2-набора.
- Открытие файла из архива в связанном приложении: Rizpaq извлекает
  его во временную папку и отдаёт Windows.
- **Поиск по всем архивам.** «Архив → Поиск по всем архивам»
  (Ctrl+Shift+F) ищет имена и пути сразу во всех архивах, которые
  знает программа, а не только в открытом. Обычный текст или маски
  `*`/`?`; в результатах — архив, путь, размер, версия и дата, двойной
  щелчок открывает архив, где нашёлся файл.
- **Каталог архивов.** «Архив → Все архивы на компьютере…» сканирует
  указанные вами папки и собирает zpaq-архивы в одну таблицу
  (многотомник — одна строка с суммарным размером): размер, дата,
  число записей в индексе, пометки «в индексе» и «нет файла». Найденные
  архивы можно тут же проиндексировать, чтобы глобальный поиск их
  видел; выбор папок запоминается.
- Пароли хранятся рядом с настройками.

### Задачи резервного копирования и расписание
- Портативный контейнер `tasks.rzp` хранит все работы и все задания.
  Запись безопасная, чтение оборонительное: сбой на середине сохранения
  не оставит контейнер битым.
- **Два вида заданий под одной работой**: задание бэкапа и задание
  проверки. Контекстное меню работы предлагает «Добавить задание
  бэкапа…», «Добавить задание проверки…» и «Добавить проверку PAR2…»
  отдельными командами.
- **У задания проверки только то, что к нему относится**: режим
  проверки, расписание, режим лога. Ни сжатия, ни хэша, ни VSS — они
  относятся к заданию бэкапа и в диалоге проверки не показываются.
- **Семь режимов проверки**, ровно совпадающие с меню «Проверка»:
  полная (блоки и CRC-32), все версии с контрольными суммами, сверка с
  исходниками, параноидальная (распаковка во временную папку и сверка
  всех хэшей), «Проверить архив (PAR2)» — сверка набора восстановления
  с текущим архивом, сверка с файловой системой (`v`) и сверка с
  источниками (`sync`) — префлайт перед бэкапом: что добавится,
  изменится или пропадёт.
- **Редактирование самой работы** из её контекстного меню: имя,
  источники, назначение, комментарий, маски включения и исключения,
  пароль. Всё, что общее для всех её заданий, и ничего лишнего.
- Запуск задания двойным кликом по нему в дереве или одной кнопкой
  в его строке. Редактирование — в том же диалоге, в котором оно
  создавалось.
- Добавление нового задания к существующей работе — из контекстного
  меню работы. Новое задание наследует источники, назначение и пароль
  работы, а вы задаёте только то, чем оно отличается.
- Планирование через встроенный диалог Планировщика Windows — без
  открытия `schtasks` и без окна самого планировщика.
- **Невидимое выполнение** — ни окна, ни консоли, ни всплывающих окон.
  Работает в 3 часа ночи на сервере, работает в 8 утра на ноутбуке:
  один и тот же контейнер, одно и то же поведение.
- **Два задания не могут испортить один архив.** Если вы запустили
  задание вручную, а Планировщик в это время запустил то же самое,
  второй процесс отказывается за доли секунды, а не молча
  перезаписывает то, что пишет первый. Архив цел, а второе задание
  помечается в дереве как **«Занято»** — не ошибка и не успех, а
  «не сейчас».
- **Два окна не теряют правки друг друга.** Контейнер задач защищён
  файловым замком на весь цикл «прочитал → изменил → записал»:
  редактирование работы в окне, пока задача по расписанию обновляет
  свой статус в фоне, не теряет ни то, ни другое.
- **Дерево обновляется само.** Когда задача по расписанию завершится
  и запишет статус в контейнер, страница «Бэкап» это замечает и
  обновляет дерево — нажимать «Обновить» больше не нужно.
- **Синхронизация с Планировщиком** — контейнер и Планировщик иногда
  расходятся (переименовали работу, сменили папку задач, задачу
  удалили руками). Диалог «Синхронизировать…» показывает полную
  картину — что добавить, что снять, что удалить — и позволяет
  применить только отмеченные пункты. Кнопка «Убрать сирот…» решает
  быстрее самую частую категорию: задачи в Планировщике, которым уже
  нет задания в контейнере.
- **Управление логом** — коротко, полностью или выключено, на каждое
  задание, чтобы частые запуски не забивали диск.
- В дереве сразу видно, запланировано ли задание и когда запустится
  в следующий раз; если не запланировано — кнопка в строке запланирует
  его на месте.
- **Дашборд защиты** — одно окно сразу по всем работам и заданиям:
  последний статус, дата запуска, размер архива, число файлов в индексе
  и состояние набора PAR2. Три вида одних и тех же данных: граф, где
  каждое задание — овал со спутниками «последний бэкап / последняя
  проверка / PAR2» (заливка — действие было, пунктир — не было),
  карточки запусков из лога контейнера и точная таблица с
  плитками-фильтрами — все, успешно, ошибки, занято, не запускалось,
  нет набора PAR2. Дашборд только читает: в архив он ничего не пишет.
- **Каждый запуск попадает в лог.** Запуски из окна теперь пишут итог
  в `tasks.rzp.log` тем же форматом, что и запуски по расписанию,
  поэтому карточки запусков и история лога показывают всю активность,
  а не только работу Планировщика. Задание с режимом лога «не вести»
  в историю не попадает — так и задумано.

### Непрерывный бэкап, отчёт о дедупликации и уведомления (3.0)
- **Непрерывный бэкап** — новое расписание «Непрерывно (при изменениях)» с
  интервалом от 1 до 60 минут. Программа сама сверяет архив с папками-
  источниками и запускает архивацию только когда есть что менять; если
  изменений нет, запуск пропускается, а в логе пишется причина.
- **Отчёт о дедупликации** — в окне информации об архиве теперь видно, сколько
  байт добавили все версии, сколько архив занимает на диске, сколько
  сэкономлено и во сколько раз. Отдельных запросов к архиватору не требуется:
  цифры берутся из уже полученной информации об архиве.
- **Уведомления в Telegram** — сообщение о том, что задание выполнено или
  сорвалось. В «Настройки → Уведомления…» выбирается режим (выключено, только
  ошибки или все результаты), вводится токен бота и chat_id. Уведомления
  приходят и для ручных запусков, а неудачная отправка никогда не портит
  результат задания. Причина сбоя пишется в `rizpaq_notify.log` рядом с
  настройками.

### Защита архива (PAR2)
- У любого архива может быть **PAR2-набор восстановления** — файлы
  защиты рядом с самим архивом. Движок `par2` встроен.
- Создать набор можно одной галочкой в задании бэкапа (вкладка
  «Защита») — он строится сразу после успешного архивирования — или
  вручную: правый клик по архиву → *Создать набор PAR2…*. Ручное
  создание спрашивает параметры — избыточность, размер блока, потоки —
  и помнит выбор до конца сеанса.
- **Проверка набора — пятый режим проверки**, «Проверить архив
  (PAR2)». Вердикт называет проблему точно: всё цело; повреждён и
  чинится; повреждён безнадёжно; набора нет — либо «набор устарел:
  архив переписан новым бэкапом», с обоими размерами.
- **Проверка набора по расписанию.** «Добавить проверку PAR2…» в
  контекстном меню работы создаёт обычное задание проверки с уже
  выбранным режимом PAR2; «Проверить PAR2» в тех же меню делает
  разовую проверку без создания задания. Дерево пишет дату, счётчик
  прогонов и честный исход: повреждённый архив — ошибка, а не
  зелёное «успешно».
- **Причина видна без открытия лога.** В колонке статуса: «Ошибка —
  набор не создан», «Ошибка — архив повреждён» и так далее; наведение
  мыши на статус показывает полное предложение — что случилось и что
  делать — и время последнего прогона.
- **Отказ виден.** Клик по «Проверить PAR2», когда проверять нечего,
  показывает окно с объяснением и советом, а не молчаливую заметку в
  строке состояния.
- **Восстановление из PAR2.** Если проверка нашла порчу, ремонт может
  вернуть архиву целое состояние. Rizpaq охраняет от отката: ремонт с
  набором, не совпадающим по размеру с текущим архивом, запрещён, а
  равный размер сначала спрашивает (набор вернёт версию со своего
  дня). Восстановление — только вручную: оно перезаписывает архив,
  поэтому в расписание его поставить нельзя.
- Пересоздание набора меняет старый на новый без разрыва в защите;
  если архив не менялся, пересоздание пропускается.
- Честные границы: набор защищает данные от порчи, но НЕ от смерти
  носителя — для этого есть вторая копия. Многотомные архивы набором
  пока не покрываются.

### Универсальные архивы и транскодирование
- Открытие ZIP, 7z и RAR через встроенный мост к 7-Zip.
- Распаковка всего архива, одного элемента или папки.
- **Конвертация в ZPAQ…** — превращает любой ZIP, 7z или RAR в
  дедуплицированный версионный ZPAQ-архив. Работает в фоне, временные
  файлы убираются сами.
- Управление ассоциациями `.zpaq`, `.rzp`, `.zip`, `.7z`, `.rar`
  независимо друг от друга, через диалог «Интеграция с проводником» —
  включить или выключить любую, не задевая остальные.

### Интеграция с проводником
- Правый клик по `.zpaq`, `.zip`, `.7z`, `.rar`:
  *Добавить в архив…*, *Распаковать сюда*, *Проверить*,
  *Конвертировать в ZPAQ*.
- Двойной клик по `.zpaq` открывает архив, по `.rzp` — открывает
  контейнер задач в профиле «Бэкап».
- **Drag & Drop** в обе стороны: бросьте файлы в окно — создать архив;
  вытащите файлы из архива в проводник — распаковать.
- Права администратора для ассоциации не нужны.

### Внешний вид
- **Две темы**: *Мягкий лазурь* (исходная) и *Белый воздух* (почти
  белые поверхности, волосяные границы, приглушённый акцент).
  Переключаются на лету, без перезапуска.
- **Десять языков интерфейса** — English, Русский, Italiano, Deutsch,
  Français, Español, 中文, Português, 日本語, Polski — плюс любой
  дополнительный, положенный в `locales/`. Без пересборки.
- **Окошко «идёт операция»** для долгих операций: небольшая
  некликабельная панель называет текущую фазу, считает секунды и
  предлагает «Отмена». Появляется через 400 мс, поэтому быстрые
  операции не мигают.
- **Единое окно прогресса** для любой операции — архивации, распаковки,
  проверки — с процентом, файлами, папками, размером, скоростью,
  прошедшим временем, остатком и живым логом.

### Автообновление
- **Проверка обновлений** — не чаще раза в сутки при запуске, по
  манифесту на `rizpaq.ru`; «Справка → Проверить обновления…» проверяет
  вручную в любой момент. Тихую проверку можно выключить, конкретную
  версию — отложить.
- **Установка в один клик.** Новый билд скачивается по HTTPS (SHA256
  проверяется, если указан в манифесте); Rizpaq закрывается, скрипт
  обновления заменяет `Rizpaq.exe` и `_internal` и снова запускает
  программу. Настройки, индекс и файлы задач остаются на месте; при
  ошибке обновление откатывается к прежним файлам.

### Portable-режим
Создайте пустой файл `portable.txt` рядом с `Rizpaq.exe` — и все
настройки, пароли, контейнер задач и языки переедут вместе с
программой. Удобно для флешки.

---

## Быстрый старт

1. Скачайте свежий релиз, распакуйте в любую папку.
2. Запустите `Rizpaq.exe`.

Движки `zpaqfranz`, `7z` и `par2` уже внутри — ничего устанавливать
не нужно.

**Первый архив за 30 секунд.**
Перетащите папку в окно, нажмите ОК в диалоге, готово.

**Первая задача с расписанием за минуту.**
Откройте профиль **«Бэкап»**, нажмите «Создать архив…», задайте
источники и назначение, затем «📅 Запланировать…» прямо в диалоге —
выберите «Ежедневно в 02:00». Работа, её первое задание и задача
в Планировщике Windows создаются сразу же; с этого момента задание
запускается тихо.

**Первая проверка по расписанию за 30 секунд.**
Правый клик по существующей работе → «Добавить задание проверки…».
Выберите режим — «Полная» подойдёт для начала — и нажмите
«📅 Запланировать…». Проверка пойдёт по своему расписанию, будет
писать в тот же лог, что и бэкапы, и появится в дереве рядом с ними.

**Защитить архив PAR2 за 30 секунд.**
Правый клик по архиву → *Создать набор PAR2…* — диалог предложит
избыточность, размер блока и потоки; умолчания подойдут. Либо верхнее
меню «Защита (PAR2)». Набор строится рядом с архивом; затем *«Проверить
набор PAR2…»* в том же меню подтвердит, что архив и набор согласны.

**Старый ZIP — во что-то получше.**
Правый клик → *Конвертировать в ZPAQ…*. Выберите назначение. Готово.

---

## Требования

- Windows 10 или 11.

## Языки

English, Русский, Italiano, Deutsch, Français, Español, 中文, Português,
日本語, Polski. Свой язык добавляется файлом `locales/<код>.json` рядом
с программой — без пересборки, без компилятора, без внешних утилит.
При первом запуске интерфейс подстраивается под язык системы.
С версии 2.8.0 все десять языков переведены полностью — дашборд,
каталог архивов, диалоги и сообщения; английских заглушек не осталось.
