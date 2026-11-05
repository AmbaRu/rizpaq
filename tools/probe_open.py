#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


READY_TIMEOUT_S = 30.0


READY_MARKER = b"Add "


READY_SETTLE_S = 1.0


COMMAND_TIMEOUT_S = 900.0


POLL_INTERVAL_S = 0.25


def _find_zpaq(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p
        raise SystemExit(f"zpaqfranz не найден по указанному пути: {p}")

    here = Path(__file__).resolve().parent
    root = here.parent
    for cand in (root / "zpaqfranz.exe", root / "bin" / "zpaqfranz.exe"):
        if cand.is_file():
            return cand

    for name in ("zpaqfranz.exe", "zpaqfranz"):
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            if not entry:
                continue
            cand = Path(entry) / name
            if cand.is_file():
                return cand

    raise SystemExit(
        "zpaqfranz не найден. Укажите --zpaq \"путь\\к\\zpaqfranz.exe\"."
    )


def _make_blob(path: Path, size_mb: int) -> None:
    chunk = 4 * 1024 * 1024
    total = size_mb * 1024 * 1024
    written = 0
    with open(path, "wb") as f:
        while written < total:
            n = min(chunk, total - written)
            f.write(os.urandom(n))
            written += n


def _wait_for_ready(log_path: Path, timeout: float) -> tuple[bool, float]:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        try:
            if log_path.is_file():
                data = log_path.read_bytes()
                if READY_MARKER in data:

                    time.sleep(READY_SETTLE_S)
                    return True, time.monotonic() - t0
        except OSError:
            pass
        time.sleep(POLL_INTERVAL_S)
    return False, time.monotonic() - t0


def _terminate_gracefully(proc: subprocess.Popen, grace_s: float = 3.0) -> int:
    if proc.poll() is not None:
        return proc.returncode
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        return proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        pass
    try:
        proc.kill()
    except Exception:
        pass
    try:
        return proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        return -1


def _wait_for_exit(proc: subprocess.Popen, timeout: float = COMMAND_TIMEOUT_S) -> int:

    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return _terminate_gracefully(proc)


def _run_command(
    zpaq: Path,
    archive: Path,
    source: Path,
    level: str,
    use_open: bool,
    log_path: Path,
) -> tuple[int, float]:
    cmd = [str(zpaq), "a", str(archive), str(source)]
    if use_open:
        cmd.append("-open")
    cmd.append(f"-{level}")

    t0 = time.monotonic()
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        rc = _wait_for_exit(proc)
    dt = time.monotonic() - t0
    return rc, dt


def _run_concurrent(
    zpaq: Path,
    archive: Path,
    source: Path,
    level: str,
    first_open: bool,
    second_open: bool,
    first_log: Path,
    second_log: Path,
    second_rc_path: Path,
    label: str,
) -> tuple[str, int | None, float | None, int | None, float | None]:
    print(f"\n=== {label} ===")

    first_cmd = [str(zpaq), "a", str(archive), str(source)]
    if first_open:
        first_cmd.append("-open")
    first_cmd.append(f"-{level}")

    print(f"  первая: {' '.join(first_cmd)}")
    print("  запуск первой в фоне…")
    t0 = time.monotonic()
    with open(first_log, "wb") as flog:
        first = subprocess.Popen(first_cmd, stdout=flog, stderr=subprocess.STDOUT)

    ready, waited = _wait_for_ready(first_log, READY_TIMEOUT_S)

    if not ready:


        rc = _terminate_gracefully(first)
        print(f"  [ОШИБКА ЗАМЕРА] первая не начала добавление за "
              f"{READY_TIMEOUT_S:.0f} с (прошло {waited:.1f} с, "
              f"код после остановки: {rc}).")
        print("  Смотрите first-*.log: там видно, что движок успел сделать.")
        return "not_started", rc, waited, None, None

    if first.poll() is not None:


        rc = first.returncode
        print(f"  [ОШИБКА ЗАМЕРА] первая завершилась за {waited:.1f} с, "
              f"не успев стать 'занятой' (код {rc}).")
        print("  Увеличьте --size-mb или возьмите более тяжёлый --level.")
        return "not_started", rc, waited, None, None

    print(f"  первая работает ({waited:.1f} с, 'Add' в логе) — "
          f"запускаем вторую поверх занятого архива")

    second_cmd = [str(zpaq), "a", str(archive), str(source)]
    if second_open:
        second_cmd.append("-open")
    second_cmd.append(f"-{level}")

    t1 = time.monotonic()
    with open(second_log, "wb") as slog:
        second = subprocess.Popen(second_cmd, stdout=slog, stderr=subprocess.STDOUT)
    second_rc = _wait_for_exit(second)
    second_dt = time.monotonic() - t1

    second_rc_path.write_text(f"second_rc={second_rc}\n", encoding="utf-8")
    print(f"  вторая завершилась: код {second_rc}, {second_dt:.1f} с")

    print("  ждём завершения первой…")
    first_rc = _wait_for_exit(first)
    first_dt = time.monotonic() - t0
    print(f"  первая завершилась: код {first_rc}, {first_dt:.1f} с")

    return "ok", first_rc, first_dt, second_rc, second_dt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Замер поведения zpaqfranz при -open на занятом архиве.",
    )
    parser.add_argument("--size-mb", type=int, default=200,
                        help="размер случайного источника, МБ "
                             "(по умолчанию 200: хватает, чтобы первая "
                             "команда жила секунды, и не тянет замер)")
    parser.add_argument("--level", default="m2",
                        help="уровень сжатия: m0..m5 (по умолчанию m2 — "
                             "на несжимаемых данных m0–m2 одинаково быстры, "
                             "а m5 уходит в часы)")
    parser.add_argument("--zpaq", default=None,
                        help="путь к zpaqfranz.exe (иначе — автопоиск)")
    args = parser.parse_args()

    zpaq = _find_zpaq(args.zpaq)
    print(f"zpaqfranz: {zpaq}")
    print(f"размер источника: {args.size_mb} МБ, уровень: {args.level}")
    print(f"папка замера будет создана заново")

    probe = Path(tempfile.gettempdir()) / "rizpaq_open_probe"
    if probe.exists():
        shutil.rmtree(probe, ignore_errors=True)
    probe.mkdir(parents=True)
    print(f"папка замера: {probe}")

    blob = probe / "blob.bin"
    print(f"\n=== генерация {args.size_mb} МБ случайных данных ===")
    print("  это займёт до минуты, зато данные несжимаемые")
    t0 = time.monotonic()
    _make_blob(blob, args.size_mb)
    print(f"  готово за {time.monotonic() - t0:.1f} с, "
          f"размер: {blob.stat().st_size / 1024 / 1024:.1f} МБ")

    summary_lines = [
        f"zpaqfranz: {zpaq}",
        f"источник:  blob.bin, {args.size_mb} МБ случайных данных",
        f"уровень:   {args.level}",
        "",
    ]


    arc1 = probe / "archive.zpaq"
    state, rc1, dt1, rc2, dt2 = _run_concurrent(
        zpaq, arc1, blob, args.level,
        first_open=True, second_open=True,
        first_log=probe / "first_open.log",
        second_log=probe / "second_open.log",
        second_rc_path=probe / "second_open_rc.txt",
        label="Случай 1: первая с -open, вторая с -open",
    )
    summary_lines += [
        "Случай 1 (обе с -open):",
        f"  state:    {state}",
        f"  первая:   rc={rc1}  dt={dt1}",
        f"  вторая:   rc={rc2}  dt={dt2}",
        "",
    ]


    arc2 = probe / "archive2.zpaq"
    state, rc1, dt1, rc2, dt2 = _run_concurrent(
        zpaq, arc2, blob, args.level,
        first_open=False, second_open=True,
        first_log=probe / "first_noflag.log",
        second_log=probe / "second_on_busy.log",
        second_rc_path=probe / "second_on_busy_rc.txt",
        label="Случай 2: первая без -open, вторая с -open",
    )
    summary_lines += [
        "Случай 2 (первая без флага, вторая с -open):",
        f"  state:    {state}",
        f"  первая:   rc={rc1}  dt={dt1}",
        f"  вторая:   rc={rc2}  dt={dt2}",
        "",
    ]


    print("\n=== Случай 3: контроль, свободный архив, -open ===")
    arc3 = probe / "archive3.zpaq"
    rc3, dt3 = _run_command(
        zpaq, arc3, blob, args.level,
        use_open=True,
        log_path=probe / "control_open.log",
    )
    (probe / "control_rc.txt").write_text(f"control_rc={rc3}\n", encoding="utf-8")
    print(f"  контроль завершилась: код {rc3}, {dt3:.1f} с")
    summary_lines += [
        "Случай 3 (контроль, свободный архив):",
        f"  rc={rc3}  dt={dt3}",
        "",
    ]

    summary = probe / "run_summary.txt"
    summary.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\n=== Готово ===\n{summary.read_text(encoding='utf-8')}")
    print(f"Папка с логами: {probe}")

    try:
        if os.name == "nt":
            os.startfile(str(probe))
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
