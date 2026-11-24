use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use std::path::Path;

#[link(name = "kernel32")]
extern "system" {
    fn GetDiskFreeSpaceExW(
        lp_directory_name: *const u16,
        lp_free_bytes_available: *mut u64,
        lp_total_bytes: *mut u64,
        lp_total_free_bytes: *mut u64,
    ) -> i32;
}

fn to_wide(value: &OsStr) -> Vec<u16> {
    let mut out: Vec<u16> = value.encode_wide().collect();
    out.push(0);
    out
}

pub fn free_bytes(path: &str) -> Option<u64> {
    let folder = Path::new(path).parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let wide = to_wide(folder.as_os_str());
    let mut available = 0u64;
    let mut total = 0u64;
    let mut free = 0u64;
    let ok = unsafe {
        GetDiskFreeSpaceExW(
            wide.as_ptr(),
            &mut available,
            &mut total,
            &mut free,
        )
    };
    if ok == 0 {
        None
    } else {
        Some(free)
    }
}
