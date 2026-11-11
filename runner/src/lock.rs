
use std::path::{Path, PathBuf};

pub const DEFAULT_TIMEOUT_S: f64 = 2.0;

const POLL_INTERVAL_S: f64 = 0.05;

pub const LOCK_SUFFIX: &str = ".lock";

pub struct LockError {
    pub busy: bool,
    pub message: String,
}

fn busy_error(lock_path: &Path) -> LockError {
    LockError {
        busy: true,
        message: format!(
            "container {} is busy (locked by another process)",
            lock_path.display()
        ),
    }
}

fn fail_error(lock_path: &Path, err: &str) -> LockError {
    LockError {
        busy: false,
        message: format!("cannot lock container {}: {}", lock_path.display(), err),
    }
}

pub fn lock_path_for(container_path: &Path) -> PathBuf {
    let mut s = container_path.to_string_lossy().into_owned();
    s.push_str(LOCK_SUFFIX);
    PathBuf::from(s)
}

type HANDLE = *mut core::ffi::c_void;

#[link(name = "kernel32")]
extern "system" {
    fn CreateFileW(
        lpFileName: *const u16,
        dwDesiredAccess: u32,
        dwShareMode: u32,
        lpSecurityAttributes: *mut core::ffi::c_void,
        dwCreationDisposition: u32,
        dwFlagsAndAttributes: u32,
        hTemplateFile: HANDLE,
    ) -> HANDLE;
    fn CloseHandle(hObject: HANDLE) -> i32;
}

const GENERIC_READ: u32 = 0x8000_0000;
const GENERIC_WRITE: u32 = 0x4000_0000;
const OPEN_ALWAYS: u32 = 4;
const FILE_ATTRIBUTE_NORMAL: u32 = 0x0000_0080;
const INVALID_HANDLE_VALUE: HANDLE = -1isize as HANDLE;

fn open_exclusive(path: &Path) -> Result<HANDLE, Option<String>> {
    use std::os::windows::ffi::OsStrExt;
    let wide: Vec<u16> = path
        .as_os_str()
        .encode_wide()
        .chain(std::iter::once(0))
        .collect();
    let handle = unsafe {
        CreateFileW(
            wide.as_ptr(),
            GENERIC_READ | GENERIC_WRITE,
            0,
            std::ptr::null_mut(),
            OPEN_ALWAYS,
            FILE_ATTRIBUTE_NORMAL,
            std::ptr::null_mut(),
        )
    };
    if handle.is_null() || handle == INVALID_HANDLE_VALUE {
        let err = std::io::Error::last_os_error();
        let code = err.raw_os_error().unwrap_or(0);
        if code == 32 || code == 33 {
            return Err(None);
        }
        return Err(Some(format!(
            "[WinError {}] CreateFileW failed for {}",
            code,
            path.display()
        )));
    }
    Ok(handle)
}

pub struct ContainerLock {
    handle: HANDLE,
}

impl Drop for ContainerLock {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.handle);
        }
    }
}

pub fn acquire(container_path: &Path, timeout_s: f64) -> Result<ContainerLock, LockError> {
    let lock_path = lock_path_for(container_path);

    if let Some(parent) = lock_path.parent() {
        if !parent.as_os_str().is_empty() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                return Err(fail_error(
                    &lock_path,
                    &format!("[OSError] cannot create directory {}: {}", parent.display(), e),
                ));
            }
        }
    }

    let deadline = std::time::Instant::now()
        + std::time::Duration::from_secs_f64(timeout_s.max(0.0));
    loop {
        match open_exclusive(&lock_path) {
            Ok(handle) => return Ok(ContainerLock { handle }),
            Err(None) => {}
            Err(Some(text)) => return Err(fail_error(&lock_path, &text)),
        }
        if std::time::Instant::now() >= deadline {
            break;
        }
        std::thread::sleep(std::time::Duration::from_secs_f64(POLL_INTERVAL_S));
    }

    Err(busy_error(&lock_path))
}
