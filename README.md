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
- Optional **second copy** of the archive into another folder after creation —
  including scheduled jobs — with a byte-for-byte check before the previous
  copy is replaced.
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
- **Restore by date or all versions** for the whole archive — "Archive →
  Extract → Restore by date / all versions…". Files deleted since the chosen
  date and multipart sets are handled, and a non-empty destination asks
  before writing.
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
- **Deduplication report** — the archive information window shows how many
  bytes all versions passed through before compression, how much the archive
  takes on disk, how much was saved and by how much (the ratio). The numbers
  come from `zpaqfranz i <archive> -stat`, requested in the background: the
  window opens at once and the block appears when the answer arrives.
- **Telegram notifications** — get a message when a job finishes or fails.
  Choose "off", "only errors" or "all results" in Settings → Notifications…,
  then paste the bot token and the chat id. Notifications work for manual
  runs as well, and a failed send never breaks the job. If the send fails,
  the reason is written to `rizpaq_notify.log` next to your settings.

### Skip unchanged runs and post-3.0 fixes (3.0.2)
- **Skip unchanged runs on ordinary schedules** — daily, hourly, weekly and
  monthly backups get a "Skip the run if nothing changed" option. Rizpaq
  compares the archive with the sources before the run and creates no new
  version when there is nothing to change. Masks and multi-volume archives
  still run as normal backups, and the log records why the comparison was
  skipped.
- **Repair after an interrupted backup** — if adding a version was
  interrupted, Rizpaq offers to remove only the unfinished transaction and
  keep the completed versions. There are two modes: repair on a copy next to
  the archive (the default, safer — the copy is checked and only then
  replaces the original) or directly in the file (no copy needed).
  Ordinary archives are trimmed; encrypted ones are cropped with the key;
  multi-volume archives are not repaired automatically. The copy needs free
  space on the archive disk (up to the archive size); if there is not
  enough, Rizpaq reports how much is needed and offers the copy-free mode;
  a copy is made only when that mode is chosen. A copy that the engine
  failed to finish is deleted and never replaces the original. In-place
  repair requires an extra confirmation and warns that there is no backup;
  after it the archive is still checked, and a failed check is reported
  honestly.
- **Fixes after 3.0.0** — the deduplication report uses the engine's real
  before- and after-compression sizes; unsupported job actions are rejected
  by the Rust runner instead of silently becoming backups; a password change
  writes a separate re-encrypted file and updates the password store;
  notification requests are bounded by a 30-second deadline; silent
  continuous jobs are reported in minutes rather than after a day.

### zpaqfranz 65.20 and warnings instead of failures (3.0.3)
- **Engine updated to zpaqfranz 65.20.** Archives stay as compact as before:
  the new engine enables its `-lfast` listing history by default, which almost
  doubles the archive, so Rizpaq turns it off for every backup.
- **Warnings are not failures.** The engine now returns exit code 1 when a
  backup finished with warnings (for example, a file was locked and skipped).
  The archive is created, the job stays successful and the warning is shown in
  the result dialog, the report and the log. For archive checks code 1 still
  means a problem.

### Verified second copy in scheduled jobs (3.0.4)
- **The second copy now works in scheduled jobs too.** The "Second copy to
  folder" field used to be honoured only when an archive was created by hand
  from the window; a scheduled job quietly ignored it. Now the copy is made by
  the headless job and by the Rust runner as well.
- **The copy is verified, not assumed.** It is written to a temporary
  `<name>.rizpaq-part` next to the target and compared with the archive byte
  for byte in 1 MiB chunks; only on a match does it replace the previous copy.
  A multi-volume archive is copied in full by its mask.
- **A failed copy is honest.** The job status becomes "Error" with the reason
  "second copy failed" and exit code 1, while the backup itself is not
  cancelled: the archive, PAR2, the index and the password are still
  processed, and the previous whole copy stays in place.

### Command reference and point-in-time restore (3.0.5)
- **zpaqfranz command reference, offline.** "Help → zpaqfranz command
  reference…" opens a searchable window with the commands of the bundled
  engine (v65.20) and their help text. Copy an entry to the clipboard or
  open the full guide in a browser. The data ships with Rizpaq
  (`zpaqfranz-commands.md` and `zpaqfranz-help-builtin-ru.txt`), so search
  works without internet; if those files are missing, the window offers
  the online wiki instead.
- **Restore the whole archive as of a date, or every version.** "Archive →
  Extract → Restore by date / all versions…" has two modes: the state at a
  chosen moment (including files deleted since, multipart sets included),
  or all versions unpacked into numbered folders 0001, 0002, … . Data is
  staged in a temporary folder, and extracting into a non-empty destination
  asks for confirmation first. The familiar single-folder version
  extraction is still there.

### What's new in 3.1.14
- The password is asked again after a restart: the GUI no longer takes the saved key from the store, which used to open and run an encrypted archive without a single prompt.
- Encrypted archives no longer freeze for half a minute waiting for a console password: every engine launch detaches stdin.
- A wrong key no longer loops the password dialog: three attempts in a row, cancel is free, then the engine's own message is shown.

### What's new in 3.1.13
- Extracting from a password-protected archive no longer fails with `Misplaced argument`: the file/folder filter goes before `-key`.
- A password saved when the archive was created is now picked up on opening; a password entered by hand is saved for later.
- If the key is missing or wrong, the program asks for it and retries the extraction instead of failing silently.

### What's new in 3.1.12
- Opening a password-protected archive no longer hides the password prompt behind the "operation in progress" notice.
- Job logs contain the `Command:` line again (with the password masked); damaged task containers no longer crash the backup page.

### What's new in 3.1.10
- Multipart archives can now be joined into one archive with `m ... -verify`;
  the old `consolidate` command never worked. Original volumes are kept.
- PAR2 sets are flagged as outdated after a retention shrink too.
- Scheduled jobs (Rust runner) now record archive size history, so the
  growth chart and disk forecast finally get data.

### What's new in 3.1.9
- Safe version retention: dry run with `repack -test`, then write to a
  temporary archive, verify it and only then replace the original.
- Fixed extra archives with PAR2, drag-out extraction, and post-write
  verification in scheduled jobs; Rust runner now matches Python for PAR2
  failures, `-nolfast` and extra destinations.

### What's new in 3.1.8
- Fixed the restore drill: the extraction folder needed a trailing path
  separator, otherwise zpaqfranz treated it as a file name and a healthy
  archive was reported as a failed drill (GUI/Python since 3.1.4, Rust
  runner since 3.1.7).

### What's new in 3.1.7
- One job can write the same version to several archives, with a second
  copy and PAR2 for each; the job succeeds only when all are done.
- The dashboard exports a standalone HTML report.
- Scheduled jobs use a Rust runner with the same mail, extra-archive and
  restore-drill behaviour as the GUI.
- An optional daily Task Scheduler watchdog reports missed backups by email
  even if the app is never opened.

### Archive growth chart (3.1.6)
- The dashboard draws a 30-day archive-size line and the current
  compression ratio from the stored history.

### Disk fill forecast (3.1.5)
- The dashboard keeps archive size samples and estimates how many days are
  left before the disk is full.

### Restore drill (3.1.4)
- A "File restore (drill)" check mode extracts a random small file and
  compares its hash with the source, proving the archive is restorable.

### Live system readings (3.1.3)
- A separate "System (live)" group in the backup/PAR2 progress window
  shows CPU, memory and disk read/write with busy percentage, refreshed
  once a second. The PDH counter layout bug that showed zeros is fixed.

### Live PAR2 progress (3.1.2)
- The PAR2 creation window shows percentage, phase, read/written bytes,
  speeds, ETA, block counts and redundancy. Counters update every second
  even while par2 is silent.

### Protection status (3.1.1)
- A backup job with PAR2 enabled is marked complete only after the
  recovery set is created (or confirmed still valid). If the set fails,
  the job shows "Error" with the reason `par2_failed`.

### Email reports and other 3.1.0 changes
- **Reports on email, sent by zpaqfranz itself.** "Settings → Email
  Reports…" configures SMTP (server, port, STARTTLS/SSL, user, password,
  sender, recipient, customer name). A full report with file names is sent
  after backup and verification jobs, scheduled or started by hand;
  "Send test email" checks the settings immediately. If the SMTP server is
  unreachable, the job is still successful and the reason stays in its log.
  The password is stored in plain text in the settings file — just like the
  Telegram token — and the dialog says so.
- **One letter for the whole backup.** If the job also builds a PAR2 set,
  the report is sent once after all stages with the archiving log, the
  second-copy result and the PAR2 log together. Without PAR2 it is sent
  immediately after the archive command.
- **Free-space check no longer blocks appending.** A new archive still
  requires the full size of the sources plus 5%; appending to an existing
  archive requires at least 1 GB, so an incremental backup can no longer
  be rejected for demanding the full size of all files. Already saved jobs
  work without editing the container.
- **Tooltips are translated** into all ten languages; the start-up probe of
  Windows Scheduler runs in the background, and conflicting jobs only warn.

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
- **Six themes**: *Soft Azure* (the original), *White Air* (near-white
  surfaces, hairline borders, muted accent), *Deep Black* (near-black
  surfaces, light text, calm accent), *Deep Teal* (dark blue-green, teal
  accent), *Catppuccin Mocha* (soft pastel dark) and *Cloud Dancer* (warm
  off-white). Switched on the fly, no restart.
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
- Опциональная **вторая копия** архива в другую папку после создания — в том
  числе в заданиях по расписанию — со сверкой побайтово, прежде чем заменить
  прежнюю копию.
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
- **Восстановление на дату или всех версий** для всего архива —
  «Архив → Распаковка → Восстановить на дату / все версии…»: учитываются
  позже удалённые файлы и многотомники, а распаковка в непустую папку
  требует подтверждения.
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
- **Отчёт о дедупликации** — в окне информации об архиве видно, сколько байт
  прошло через все версии до сжатия, сколько архив занимает на диске, сколько
  сэкономлено и во сколько раз. Числа берутся из `zpaqfranz i «архив» -stat`;
  запрос идёт в фоне: окно открывается сразу, а блок появляется, когда ответ
  пришёл.
- **Уведомления в Telegram** — сообщение о том, что задание выполнено или
  сорвалось. В «Настройки → Уведомления…» выбирается режим (выключено, только
  ошибки или все результаты), вводится токен бота и chat_id. Уведомления
  приходят и для ручных запусков, а неудачная отправка никогда не портит
  результат задания. Причина сбоя пишется в `rizpaq_notify.log` рядом с
  настройками.

### Пропуск запуска без изменений и исправления после 3.0 (3.0.2)
- **Пропуск запуска без изменений для обычных расписаний** — у ежедневного,
  ежечасного, недельного и месячного бэкапа появилась галочка «Пропускать,
  если изменений нет». Перед запуском программа сверяет архив с источниками
  и не создаёт новую версию, когда менять нечего. Для масок и многотомных
  архивов задание по-прежнему выполняется как обычный бэкап, а причина
  пропуска сверки пишется в лог.
- **Починка после оборванного бэкапа** — если добавление версии прервалось,
  Rizpaq предлагает убрать только незавершённую транзакцию, сохранив
  завершённые версии. Есть два режима: ремонт в копию рядом с архивом
  (по умолчанию, безопаснее — копия проверяется и только потом заменяет
  исходный файл) или прямо в файле (без копии). Обычные архивы очищаются
  через trim, шифрованные — через crop с ключом; многотомные автоматически
  не чинятся. Для копии нужно свободное место на диске архива (до его
  размера); если его не хватает, Rizpaq пишет, сколько нужно, и предлагает
  режим без копии; копия создаётся только при выборе этого режима.
  Недостроенная движком копия удаляется и никогда не заменяет исходник.
  Ремонт прямо в файле требует отдельного подтверждения и предупреждает,
  что страховочной копии не будет; после него архив всё равно проверяется,
  а неудачная проверка честно сообщается пользователю.
- **Исправления после 3.0.0** — отчёт о дедупликации использует настоящие
  размеры до и после сжатия; неподдержанные виды заданий в Rust-раннере
  отклоняются, а не превращаются молча в бэкап; смена пароля пишет отдельный
  файл и обновляет хранилище паролей; запросы уведомлений ограничены сроком
  30 секунд; зависшие непрерывные задания видны на дашборде через минуты, а
  не через сутки.

### zpaqfranz 65.20: предупреждения вместо ошибок (3.0.3)
- **Движок обновлён до zpaqfranz 65.20.** Архивы остаются такими же
  компактными: новый движок по умолчанию включает `-lfast` (историю правок
  листинга), которая раздувает архив почти вдвое, поэтому Rizpaq отключает
  её на каждом бэкапе.
- **Предупреждение — не ошибка.** Движок теперь возвращает код 1, если
  бэкап завершился с предупреждениями (например, занятый файл пропущен).
  Архив создан, задание остаётся успешным, а предупреждение видно в диалоге
  результата, отчёте и логе. Для проверок архива код 1 по-прежнему означает
  проблему.

### Вторая копия в расписании и сверка (3.0.4)
- **Вторая копия работает и в задании по расписанию.** Поле «Вторая копия
  в папку» раньше учитывалось только при ручном создании архива из окна, а
  задание по расписанию его молча игнорировало. Теперь копию делают и
  headless-задание, и Rust-раннер.
- **Копия проверяется, а не предполагается.** Она пишется во временный
  `<имя>.rizpaq-part` рядом с целевым файлом и сверяется с архивом
  побайтово порциями по 1 МиБ; прежнюю копию она заменяет только при
  совпадении. Многотомный архив копируется целиком по маске.
- **Неудача копии не молчит.** Статус задания становится «Ошибка» с
  причиной «вторая копия не создалась» и кодом возврата 1, но сам бэкап не
  отменяется: архив, PAR2, индекс и пароль выполняются, а прежняя целая
  копия остаётся на месте.

### Справочник команд и восстановление на дату (3.0.5)
- **Справочник команд zpaqfranz без интернета.** «Справка → Справочник
  команд zpaqfranz…» открывает окно с поиском по командам встроенного
  движка (v65.20) и текстом справки по каждой. Запись можно скопировать
  в буфер или открыть полный справочник в браузере. Данные идут в комплекте
  (`zpaqfranz-commands.md` и `zpaqfranz-help-builtin-ru.txt`), поэтому поиск
  работает офлайн; если файлов нет, предлагается онлайн-вика.
- **Восстановление всего архива на дату или всех версий.** «Архив →
  Распаковка → Восстановить на дату / все версии…» — два режима: состояние
  на выбранный момент (включая позже удалённые файлы и многотомники) или
  все версии в пронумерованных папках 0001, 0002, … . Данные идут через
  временную папку, а распаковка в непустую папку сначала спрашивает
  подтверждение. Привычное извлечение версии одной папки осталось на месте.

### Что нового в 3.1.14
- После перезапуска пароль спрашивается снова: GUI больше не берёт сохранённый ключ из хранилища, из-за чего зашифрованный архив открывался и запускал файлы без единого запроса.
- Зашифрованные архивы больше не зависают на полминуты в ожидании пароля с консоли: каждая точка запуска движка отсоединяет stdin.
- Неверный ключ больше не зацикливает окно пароля: три попытки подряд, «Отмена» бесплатна, затем показывается сообщение самого движка.

### Что нового в 3.1.13
- Распаковка из архива с паролем больше не падает с `Misplaced argument`: фильтр файла или папки идёт до `-key`.
- Пароль, сохранённый при создании архива, теперь подхватывается при открытии; введённый вручную запоминается.
- Если ключ не задан или неверен, программа спрашивает пароль и повторяет распаковку вместо молчаливого отказа.

### Что нового в 3.1.12
- При открытии архива с паролем окно запроса пароля больше не перекрывается окошком «идёт операция».
- В журнал задания снова попадает строка `Command:` (с замаскированным паролем); повреждённый контейнер заданий больше не валит панель бэкапа.

### Что нового в 3.1.10
- Разбитый архив теперь склеивается в один командой `m ... -verify`; старая
  команда `consolidate` не работала. Исходные тома сохраняются.
- Набор PAR2 помечается устаревшим и после уменьшения архива ретенцией.
- Задания по расписанию (Rust-раннер) теперь пишут историю размеров — график
  роста и прогноз диска получают данные.

### Что нового в 3.1.9
- Безопасная ретенция версий: сухой прогон `repack -test`, запись во
  временный архив, проверка и только затем замена оригинала.
- Исправлены доп. архивы с PAR2, перетаскивание файлов и проверка после
  записи в заданиях; Rust-раннер сравнялся с Python по ошибкам PAR2,
  флагу `-nolfast` и дополнительным архивам.

### Что нового в 3.1.8
- Исправлена проба восстановления: папка извлечения требовала завершающего
  разделителя, иначе zpaqfranz принимал её за имя файла и здоровый архив
  объявлялся провалившим пробу (GUI/Python — с 3.1.4, Rust-раннер — с 3.1.7).

### Что нового в 3.1.7
- Одно задание может записать одну версию в несколько архивов — со второй
  копией и PAR2 для каждого; задание успешно только когда готовы все.
- Дашборд экспортирует самостоятельный HTML-отчёт.
- Задания по расписанию выполняются Rust-раннером с той же почтой,
  дополнительными архивами и пробой восстановления, что и в GUI.
- Необязательная ежедневная задача Планировщика сообщает о пропущенных
  бэкапах по почте, даже если программу не открывают.

### График роста архива (3.1.6)
- Дашборд рисует линию размера архива за 30 дней и текущий коэффициент
  сжатия по сохранённой истории.

### Прогноз заполнения диска (3.1.5)
- Дашборд хранит замеры размера архива и оценивает, через сколько дней
  закончится место.

### Автотест восстановления (3.1.4)
- Режим проверки «Восстановление файла (автотест)» распаковывает случайный
  файл и сравнивает хеш с исходником — доказательство восстановимости архива.

### Живые показатели системы (3.1.3)
- Отдельная рамка «Система (сейчас)» в окне бэкапа/PAR2: процессор,
  память, чтение/запись диска и его занятость, обновление раз в секунду.
  Исправлена структура счётчика PDH, из-за которой цифры были нулями.

### Живой прогресс PAR2 (3.1.2)
- Окно создания набора показывает процент, фазу, прочитано/записано,
  скорость, ETA, блоки и избыточность. Счётчики обновляются раз в секунду,
  даже когда par2 молчит.

### Статус защиты (3.1.1)
- Задание с включённым PAR2 считается завершённым только после создания
  набора (или подтверждения, что он ещё в силе). При отказе набора задание
  показывает «Ошибка» с причиной `par2_failed`.

### Отчёты на почту и другие изменения 3.1.0
- **Отчёты отправляет сам zpaqfranz.** «Настройки → Отчёты на почту…»:
  сервер, порт, STARTTLS/SSL, пользователь, пароль, отправитель,
  получатель и имя задания. Полный журнал с именами файлов уходит после
  заданий бэкапа и проверки — по расписанию или вручную; кнопка
  «Отправить тестовое письмо» проверяет настройки сразу. Если SMTP
  недоступен, задание остаётся успешным, а причина пишется в его журнал.
  Пароль хранится в открытом виде рядом с токеном Telegram — диалог об
  этом предупреждает.
- **Одно письмо на весь бэкап.** Если задание ещё создаёт набор PAR2,
  письмо уходит один раз после всех этапов: лог архивации, вторая копия
  и PAR2 — в одном сообщении. Без PAR2 письмо уходит сразу после команды
  архивации.
- **Проверка свободного места больше не мешает дозаписи.** Новый архив
  по-прежнему требует размер исходников плюс 5%, а дозапись в существующий —
  минимум 1 ГБ. Инкрементальный бэкап не отказывается только потому, что
  требовал полный размер всех файлов. Уже сохранённые задания работают без
  правки контейнера.
- **Подсказки переведены** на все десять языков; опрос Планировщика при
  старте идёт в фоне, а пересекающиеся задания только предупреждают.

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
- **Шесть тем**: *Мягкий лазурь* (исходная), *Белый воздух* (почти
  белые поверхности, волосяные границы, приглушённый акцент),
  *Глубокий чёрный* (почти чёрный фон, светлый текст), *Глубокий тил*
  (тёмный сине-зелёный, бирюзовый акцент), *Мокко (Catppuccin)*
  (мягкая пастельная тёмная) и *Облачный танец* (тёплый белый).
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
