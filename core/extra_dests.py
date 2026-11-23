







from __future__ import annotations

import os
from typing import Callable, Optional


def prepare_dests(main_dest: str, extra_dests) -> list:
    pass



    seen = {os.path.normcase(os.path.abspath(str(main_dest or "")))}
    result = []
    for raw in extra_dests or []:
        dest = str(raw or "").strip()
        if not dest:
            continue
        key = os.path.normcase(os.path.abspath(dest))
        if key in seen:
            continue
        seen.add(key)
        result.append(dest)
    return result


def run_extra_dests(
    zpaq: str,
    settings: dict,
    srcs: list,
    dests: list,
    password=None,
    build_cmd: Optional[Callable] = None,
    runner: Optional[Callable] = None,
    work: Optional[dict] = None,
    rzp_path: str = "",
    on_step: Optional[Callable] = None,
) -> tuple:
    pass






    if build_cmd is None or runner is None or not dests:
        return True, ""

    from core.copy_ops import copy_archive
    from core.zpaq_cli import run_zpaq

    runner = runner or run_zpaq
    ok = True
    parts = []

    for dest in dests:
        try:
            cmd = build_cmd(zpaq, settings, srcs, dest, password)
            rc, output = runner(cmd)
        except Exception as exc:
            ok = False
            parts.append(
                "\n[extra archive] %s\nошибка запуска: %s: %s" % (
                    dest, type(exc).__name__, exc,
                )
            )
            if on_step:
                on_step(dest, False)
            continue

        step_ok = rc in (0, 1)
        ok = ok and step_ok
        parts.append("\n[extra archive] %s\n%s" % (dest, output or ""))

        copy_dir = str(settings.get("copy") or "").strip()
        if copy_dir and step_ok:
            try:
                copy_ok, copy_text = copy_archive(dest, copy_dir)
                parts.append("[extra copy] %s: %s" % (
                    "OK" if copy_ok else "FAIL", copy_text,
                ))
                if not copy_ok:
                    ok = False
                    step_ok = False
            except Exception as exc:
                ok = False
                step_ok = False
                parts.append("[extra copy] FAIL: %s" % exc)

        if step_ok and settings.get("par2_enabled") and work and rzp_path:
            try:
                from core.headless import _headless_par2

                                                                         
                                                                          
                                                                   
                                                                 
                par2_ok, note = _headless_par2(
                    rzp_path, work, {}, dest, settings
                )
                parts.append(note or "")
                if not par2_ok:
                    ok = False
                    step_ok = False
                    parts.append("[extra par2] FAIL: PAR2 set not created")
            except Exception as exc:
                ok = False
                step_ok = False
                parts.append("[extra par2] FAIL: %s" % exc)

        if step_ok:
            try:
                from core import index_refresh

                index_refresh.refresh_index_sync(zpaq, dest, password)
            except Exception:
                pass

        if on_step:
            on_step(dest, step_ok)

    return ok, "\n".join(parts)
