








































from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

                                                                     
                                                                   
                                                                     
                                                                   
                                                          
DEFAULT_MANIFEST_URL = (
    "https://github.com/AmbaRu/rizpaq/releases/latest/download/latest.json"
)

                                                                
                                                                          
APP_EXE = "Rizpaq.exe"
APP_INTERNAL = "_internal"
UPDATE_LOG = "rizpaq_update.log"

                                                                 
MAX_MANIFEST_BYTES = 256 * 1024
MAX_ARCHIVE_BYTES = 3 * 1024 * 1024 * 1024
MAX_UNPACKED_BYTES = 4 * 1024 * 1024 * 1024

                                                   
USER_AGENT = "Rizpaq-updater/1.0"

                                                       
DEFAULT_TIMEOUT = 15
                                                                        
                                                                   
                                                          
CHECK_TIMEOUT = 5

_CHUNK = 256 * 1024
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class UpdateError(Exception):
    pass


class UpdateCancelled(Exception):
    pass


                                                                             
                    
                                                                             

def version_key(text: str) -> tuple:
    pass





    parts = re.findall(r"\d+", str(text or ""))
    if not parts:
        raise UpdateError(f"bad version: {text!r}")
    return tuple(int(p) for p in parts)


def is_newer(remote: str, local: str) -> bool:
    pass
    r = version_key(remote)
    l = version_key(local)
    length = max(len(r), len(l))
    r = r + (0,) * (length - len(r))
    l = l + (0,) * (length - len(l))
    return r > l


def _https(url: str, what: str) -> str:
    u = str(url or "").strip()
    parsed = urlparse(u)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise UpdateError(f"{what} must be an https URL")
    return u


def parse_manifest(data) -> dict:
    pass





    if isinstance(data, bytes):
        try:
            data = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UpdateError(f"manifest is not UTF-8: {exc}") from exc
    if isinstance(data, str):
        import json

        try:
            data = json.loads(data)
        except ValueError as exc:
            raise UpdateError(f"manifest is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise UpdateError("manifest must be a JSON object")

    version = str(data.get("version") or "").strip()
    if not version:
        raise UpdateError("manifest has no version")
    version_key(version)                    

    url = _https(data.get("url"), "archive url")

    notes = data.get("notes")
    notes = str(notes) if notes is not None else ""

    notes_url = data.get("notes_url")
    notes_url = _https(notes_url, "notes url") if notes_url else ""

    published = data.get("published")
    published = str(published).strip() if published is not None else ""

    sha256 = data.get("sha256")
    if sha256 is None or str(sha256).strip() == "":
        sha256 = ""
    else:
        sha256 = str(sha256).strip().lower()
        if not _SHA256_RE.match(sha256):
            raise UpdateError("manifest sha256 is not 64 hex characters")

    return {
        "version": version,
        "url": url,
        "notes": notes,
        "notes_url": notes_url,
        "published": published,
        "sha256": sha256,
    }


def fetch_manifest(url: Optional[str] = None,
                   timeout: int = DEFAULT_TIMEOUT,
                   opener=None) -> dict:
    pass





    target = _https(url or DEFAULT_MANIFEST_URL, "manifest url")
    open_func = opener or urllib.request.urlopen
    request = urllib.request.Request(target, headers={"User-Agent": USER_AGENT})

    try:
        with open_func(request, timeout=timeout) as response:
            raw = response.read(MAX_MANIFEST_BYTES + 1)
            charset = "utf-8"
            try:
                charset = response.headers.get_content_charset() or "utf-8"
            except Exception:
                pass
    except UpdateError:
        raise
    except Exception as exc:
        raise UpdateError(f"{type(exc).__name__}: {exc}") from exc

    if len(raw) > MAX_MANIFEST_BYTES:
        raise UpdateError("manifest is too large")
    try:
        text = raw.decode(charset, errors="strict")
    except (UnicodeDecodeError, LookupError):
        text = raw.decode("utf-8", errors="replace")
    return parse_manifest(text)


                                                                             
                        
                                                                             

def sha256_file(path) -> str:
    pass
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(_CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def verify_sha256(path, expected: str) -> bool:
    pass
    if not expected:
        return False
    try:
        return sha256_file(path) == str(expected).strip().lower()
    except OSError:
        return False


def _archive_name(url: str) -> str:
    name = unquote(PurePosixPath(urlparse(url).path).name)
    name = str(name).replace("\\", "/").split("/")[-1].strip()
    if not name:
        name = "rizpaq-update.zip"
    if not name.lower().endswith(".zip"):
        name += ".zip"
    return name


def download_update(info: dict, dest_dir, progress: Optional[Callable] = None,
                    is_cancelled: Optional[Callable] = None,
                    timeout: int = DEFAULT_TIMEOUT,
                    opener=None) -> Path:
    pass







    url = _https(info.get("url"), "archive url")
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _archive_name(url)

    open_func = opener or urllib.request.urlopen
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with open_func(request, timeout=timeout) as response:
            total = 0
            try:
                total = int(response.headers.get("Content-Length") or 0)
            except Exception:
                total = 0
            if total > MAX_ARCHIVE_BYTES:
                raise UpdateError("archive is too large")

            read = 0
            try:
                with open(dest, "wb") as out:
                    while True:
                        if is_cancelled is not None and is_cancelled():
                            raise UpdateCancelled()
                        block = response.read(_CHUNK)
                        if not block:
                            break
                        read += len(block)
                        if read > MAX_ARCHIVE_BYTES:
                            raise UpdateError("archive is too large")
                        out.write(block)
                        if progress is not None:
                            try:
                                progress(read, total)
                            except Exception:
                                pass
            except UpdateCancelled:
                raise
            except Exception:
                try:
                    dest.unlink()
                except OSError:
                    pass
                raise
    except UpdateCancelled:
        try:
            dest.unlink()
        except OSError:
            pass
        raise
    except UpdateError:
        raise
    except Exception as exc:
        try:
            dest.unlink()
        except OSError:
            pass
        raise UpdateError(f"{type(exc).__name__}: {exc}") from exc

    expected = str(info.get("sha256") or "")
    if expected and not verify_sha256(dest, expected):
        try:
            dest.unlink()
        except OSError:
            pass
        raise UpdateError("sha256 mismatch")

    return dest


                                                                             
                           
                                                                             

def _safe_zip_name(name: str) -> str:
    pass
    n = str(name or "").replace("\\", "/")
    if not n or n.startswith("/"):
        raise UpdateError("zip contains an absolute path")
    if re.match(r"^[A-Za-z]:", n):
        raise UpdateError("zip contains a drive-qualified path")
    parts = PurePosixPath(n).parts
    if any(part == ".." for part in parts):
        raise UpdateError("zip contains a parent-directory path")
    return "/".join(parts)


def inspect_update_zip(path) -> dict:
    pass








    try:
        zf = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise UpdateError(f"not a zip archive: {exc}") from exc

    try:
        infos = zf.infolist()
        names = []
        unpacked = 0
        for item in infos:
            name = _safe_zip_name(item.filename)
            if item.flag_bits & 0x1:
                raise UpdateError("zip contains an encrypted entry")
            mode = (item.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise UpdateError("zip contains a symlink")
            unpacked += int(item.file_size or 0)
            names.append(name)
    finally:
        zf.close()

    if unpacked > MAX_UNPACKED_BYTES:
        raise UpdateError("unpacked archive is too large")

    lowered = {n.lower().rstrip("/") for n in names}
    if "rizpaq/rizpaq.exe" in lowered:
        root = "Rizpaq/"
        exe = "Rizpaq/Rizpaq.exe"
        internal = "Rizpaq/_internal"
    elif "rizpaq.exe" in lowered:
        root = ""
        exe = "Rizpaq.exe"
        internal = "_internal"
    else:
        raise UpdateError("zip has no Rizpaq.exe")

    internal_prefix = internal.lower() + "/"
    if not any(n.lower().startswith(internal_prefix) for n in names):
        raise UpdateError("zip has no _internal folder")

    return {"root": root, "exe": exe, "internal": internal}


                                                                             
                                         
                                                                             

def is_frozen() -> bool:
    pass
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Optional[Path]:
    pass



    if not is_frozen():
        return None
    try:
        return Path(sys.executable).resolve().parent
    except Exception:
        return None


def _ps_quote(value) -> str:
    pass
    return "'" + str(value).replace("'", "''") + "'"


def build_update_script(zip_path, install_path, wait_pid: int,
                        temp_path, app_exe: str = APP_EXE,
                        internal: str = APP_INTERNAL,
                        log_name: str = UPDATE_LOG) -> str:
    pass












    install = _ps_quote(install_path)
    zip_q = _ps_quote(zip_path)
    temp_q = _ps_quote(temp_path)
    exe_q = _ps_quote(app_exe)
    internal_q = _ps_quote(internal)
    log_q = _ps_quote(log_name)
    pid = int(wait_pid)

    return f"""$ErrorActionPreference = 'Stop'
$install = {install}
$zip = {zip_q}
$temp = {temp_q}
$waitPid = {pid}
$appExeName = {exe_q}
$internalName = {internal_q}
$log = Join-Path $install {log_q}

function Write-Log([string]$msg) {{
    try {{
        Add-Content -LiteralPath $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $msg) -Encoding UTF8
    }} catch {{ }}
}}

function Start-Rizpaq {{
    $exe = Join-Path $install $appExeName
    if (Test-Path -LiteralPath $exe) {{
        Start-Process -FilePath $exe -WorkingDirectory $install
    }}
}}

$appExe = Join-Path $install $appExeName
$appInternal = Join-Path $install $internalName
$oldExe = $appExe + '.old'
$oldInternal = $appInternal + '.old'
$movedExe = $false
$movedInternal = $false

try {{
    Write-Log 'updater started'

    for ($i = 0; $i -lt 240; $i++) {{
        if (-not (Get-Process -Id $waitPid -ErrorAction SilentlyContinue)) {{ break }}
        Start-Sleep -Milliseconds 250
    }}
    if (Get-Process -Id $waitPid -ErrorAction SilentlyContinue) {{
        throw 'Rizpaq did not exit in time'
    }}



    $stage = Join-Path $temp 'stage'
    Expand-Archive -LiteralPath $zip -DestinationPath $stage -Force

    $srcRoot = Join-Path $stage 'Rizpaq'
    if (-not (Test-Path -LiteralPath (Join-Path $srcRoot $appExeName))) {{
        $srcRoot = $stage
    }}
    $srcExe = Join-Path $srcRoot $appExeName
    $srcInternal = Join-Path $srcRoot $internalName
    if (-not (Test-Path -LiteralPath $srcExe)) {{ throw 'update has no Rizpaq.exe' }}
    if (-not (Test-Path -LiteralPath $srcInternal)) {{ throw 'update has no _internal' }}

    if (Test-Path -LiteralPath $oldExe) {{ Remove-Item -LiteralPath $oldExe -Force }}
    if (Test-Path -LiteralPath $oldInternal) {{ Remove-Item -LiteralPath $oldInternal -Recurse -Force }}

    Rename-Item -LiteralPath $appExe -NewName ($appExeName + '.old')
    $movedExe = $true
    Rename-Item -LiteralPath $appInternal -NewName ($internalName + '.old')
    $movedInternal = $true

    Copy-Item -LiteralPath $srcExe -Destination $appExe -Force
    Copy-Item -LiteralPath $srcInternal -Destination $install -Recurse -Force

    Write-Log 'update applied'
    Start-Rizpaq
    Start-Sleep -Seconds 2
    Remove-Item -LiteralPath $oldExe -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $oldInternal -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}} catch {{
    Write-Log ('FAILED: ' + $_.Exception.Message)
    try {{
        if ($movedInternal -and (Test-Path -LiteralPath $oldInternal)) {{
            if (Test-Path -LiteralPath $appInternal) {{
                Remove-Item -LiteralPath $appInternal -Recurse -Force
            }}
            Rename-Item -LiteralPath $oldInternal -NewName $internalName
        }}
        if ($movedExe -and (Test-Path -LiteralPath $oldExe)) {{
            if (Test-Path -LiteralPath $appExe) {{
                Remove-Item -LiteralPath $appExe -Force
            }}
            Rename-Item -LiteralPath $oldExe -NewName $appExeName
        }}
    }} catch {{
        Write-Log ('rollback failed: ' + $_.Exception.Message)
    }}
    Start-Rizpaq
}}
"""


def prepare_update(zip_path, install_path=None, wait_pid: Optional[int] = None,
                   temp_root=None) -> tuple:
    pass





    if install_path is None:
        install_path = install_dir()
    if not install_path:
        raise UpdateError("update is available only in the built app")
    if wait_pid is None:
        wait_pid = os.getpid()

    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise UpdateError("downloaded archive is missing")
    inspect_update_zip(zip_path)

    base = Path(temp_root) if temp_root else Path(tempfile.gettempdir())
    if temp_root:
        base.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="rizpaq_update_", dir=str(base)))
    try:
        local_zip = temp_dir / zip_path.name
        shutil.copy2(zip_path, local_zip)
        script = temp_dir / "update.ps1"
        script.write_text(
            build_update_script(local_zip, install_path, wait_pid, temp_dir),
            encoding="utf-8-sig",
        )
        return script, temp_dir
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def launch_updater(script_path) -> None:
    pass
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise UpdateError("powershell.exe not found")
    flags = 0
    if os.name == "nt":
                                                                     
                                                                         
                                                                  
        flags = 0x08000000
    try:
        subprocess.Popen(
            [powershell, "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            creationflags=flags,
            close_fds=True,
                                                                         
                                                                          
                                                                        
        )
    except Exception as exc:
        raise UpdateError(f"{type(exc).__name__}: {exc}") from exc
