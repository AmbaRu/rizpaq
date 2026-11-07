






use crate::enginepath::{self, EnginePathError};
use crate::proc::{Liveness, BUSY_STALL_MULTIPLIER, DEFAULT_STALL_TIMEOUT};
use encoding_rs::{IBM866, UTF_8, WINDOWS_1251};
use std::os::windows::io::{FromRawHandle, RawHandle};
use std::os::windows::process::CommandExt;
use std::process::{Child, Command, Stdio};


pub(crate) const CREATE_NO_WINDOW: u32 = 0x0800_0000;


const POLL_INTERVAL_MS: u64 = 50;


const READ_CHUNK: usize = 4096;


const PROMPT_TAIL_CHUNKS: usize = 6;




const BUSY_MARKER: &str = "another zpaqfranz is running";



pub fn looks_like_busy_error(text: &str) -> bool {
    text.to_lowercase().contains(BUSY_MARKER)
}




pub fn decode_bytes(data: &[u8]) -> String {
    if data.is_empty() {
        return String::new();
    }
    for enc in [UTF_8, WINDOWS_1251, IBM866] {
        let (text, _, had_errors) = enc.decode(data);
        if !had_errors {
            return text.into_owned();
        }
    }
    
    
    String::from_utf8_lossy(data).into_owned()
}






type HANDLE = *mut core::ffi::c_void;

#[link(name = "kernel32")]
extern "system" {
    fn CreatePipe(
        hReadPipe: *mut HANDLE,
        hWritePipe: *mut HANDLE,
        lpPipeAttributes: *mut core::ffi::c_void,
        nSize: u32,
    ) -> i32;
    fn DuplicateHandle(
        hSourceProcessHandle: HANDLE,
        hSourceHandle: HANDLE,
        hTargetProcessHandle: HANDLE,
        lpTargetHandle: *mut HANDLE,
        dwDesiredAccess: u32,
        bInheritHandle: i32,
        dwOptions: u32,
    ) -> i32;
    fn PeekNamedPipe(
        hNamedPipe: HANDLE,
        lpBuffer: *mut u8,
        nBufferSize: u32,
        lpBytesRead: *mut u32,
        lpTotalBytesAvail: *mut u32,
        lpBytesLeftThisMessage: *mut u32,
    ) -> i32;
    fn ReadFile(
        hFile: HANDLE,
        lpBuffer: *mut u8,
        nNumberOfBytesToRead: u32,
        lpNumberOfBytesRead: *mut u32,
        lpOverlapped: *mut core::ffi::c_void,
    ) -> i32;
    fn CloseHandle(hObject: HANDLE) -> i32;
}

const DUPLICATE_SAME_ACCESS: u32 = 0x0000_0002;
const CURRENT_PROCESS: HANDLE = -1isize as HANDLE;

pub(crate) struct EnginePipe {
    read: RawHandle,
    write1: RawHandle,
    write2: RawHandle,
}

impl EnginePipe {
    pub(crate) fn create() -> Result<EnginePipe, String> {
        unsafe {
            let mut read: HANDLE = std::ptr::null_mut();
            let mut write: HANDLE = std::ptr::null_mut();
            if CreatePipe(&mut read, &mut write, std::ptr::null_mut(), 0) == 0 {
                return Err("CreatePipe failed".to_string());
            }
            
            
            
            let mut dup: HANDLE = std::ptr::null_mut();
            if DuplicateHandle(
                CURRENT_PROCESS,
                write,
                CURRENT_PROCESS,
                &mut dup,
                0,
                0,
                DUPLICATE_SAME_ACCESS,
            ) == 0
            {
                CloseHandle(read);
                CloseHandle(write);
                return Err("DuplicateHandle failed".to_string());
            }
            Ok(EnginePipe {
                read: read as RawHandle,
                write1: write as RawHandle,
                write2: dup as RawHandle,
            })
        }
    }

    
    
    pub(crate) fn split(self) -> (PipeRead, Stdio, Stdio) {
        let reader = PipeRead {
            handle: self.read,
        };
        
        let out = unsafe { Stdio::from_raw_handle(self.write1) };
        let err = unsafe { Stdio::from_raw_handle(self.write2) };
        std::mem::forget(self); 
        (reader, out, err)
    }
}

impl Drop for EnginePipe {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.read as HANDLE);
            CloseHandle(self.write1 as HANDLE);
            CloseHandle(self.write2 as HANDLE);
        }
    }
}


pub(crate) struct PipeRead {
    handle: RawHandle,
}

impl PipeRead {
    
    pub(crate) fn available(&self) -> u32 {
        let mut total: u32 = 0;
        unsafe {
            if PeekNamedPipe(
                self.handle as HANDLE,
                std::ptr::null_mut(),
                0,
                std::ptr::null_mut(),
                &mut total,
                std::ptr::null_mut(),
            ) == 0
            {
                return 0;
            }
        }
        total
    }

    
    pub(crate) fn read_up_to(&self, buf: &mut [u8]) -> usize {
        let mut n: u32 = 0;
        unsafe {
            if ReadFile(
                self.handle as HANDLE,
                buf.as_mut_ptr(),
                buf.len() as u32,
                &mut n,
                std::ptr::null_mut(),
            ) == 0
            {
                return 0;
            }
        }
        n as usize
    }
}

impl Drop for PipeRead {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.handle as HANDLE);
        }
    }
}








pub fn run_engine(cmd: &[String]) -> (i32, String) {
    let (cmd, cwd, subs) = match enginepath::rewrite_cmd(cmd) {
        Ok(v) => v,
        Err(EnginePathError(msg)) => return (1, format!("ERROR: {}\n", msg)),
    };
    let result = run_prepared(&cmd, cwd.as_deref());
    enginepath::drop_substitutes(&subs);
    result
}

fn run_prepared(cmd: &[String], cwd: Option<&str>) -> (i32, String) {
    let (reader, out_stdio, err_stdio) = match EnginePipe::create() {
        Ok(p) => p.split(),
        Err(msg) => return (1, format!("ERROR: {}\n", msg)),
    };

    let mut command = Command::new(&cmd[0]);
    command
        .args(&cmd[1..])
        .stdout(out_stdio)
        .stderr(err_stdio)
        .creation_flags(CREATE_NO_WINDOW);
    if let Some(dir) = cwd {
        command.current_dir(dir);
    }

    let mut child = match command.spawn() {
        Ok(c) => c,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            return (127, format!("zpaqfranz not found: {}\n", cmd[0]));
        }
        Err(e) => return (1, format!("ERROR: {}\n", e)),
    };

    let result = pump(&mut child, &reader);
    
    let _ = child.wait();
    result
}


fn pump(child: &mut Child, reader: &PipeRead) -> (i32, String) {
    let mut chunks: Vec<Vec<u8>> = Vec::new();
    let stall_used = effective_stall_timeout();
    let mut liv = Liveness::new(
        Box::new({
            
            
            let child_ptr = child as *const Child;
            move || {
                
                
                crate::proc::cpu_seconds(unsafe { &*child_ptr })
            }
        }),
        stall_used,
        stall_used * BUSY_STALL_MULTIPLIER,
    );

    let mut buf = vec![0u8; READ_CHUNK];
    loop {
        
        match child.try_wait() {
            Ok(Some(status)) => {
                
                loop {
                    let avail = reader.available();
                    if avail == 0 {
                        break;
                    }
                    let n = reader.read_up_to(&mut buf);
                    if n == 0 {
                        break;
                    }
                    chunks.push(buf[..n].to_vec());
                }
                let rc = status.code().unwrap_or(-1);
                let output = decode_bytes(&chunks.concat());
                return (rc, output);
            }
            Ok(None) => {}
            Err(_) => {
                
                let output = decode_bytes(&chunks.concat());
                return (-1, output);
            }
        }

        
        
        liv.verdict();
        if liv.stalled() {
            let tail: Vec<u8> = chunks
                .iter()
                .rev()
                .take(PROMPT_TAIL_CHUNKS)
                .rev()
                .flat_map(|c| c.iter().copied())
                .collect();
            let output = decode_bytes(&chunks.concat());
            child.kill().ok();
            wait_up_to(child, std::time::Duration::from_secs(5));
            if contains_ignore_case(&tail, b"Enter AES password") {
                return (1, output + &password_prompt_message());
            }
            let reason = if liv.busy {
                format!(
                    "движок молчал {} с и всё это время продолжал работать — это превысило даже {} с. Возможно, он зациклился.",
                    liv.last_silent as i64,
                    (stall_used * BUSY_STALL_MULTIPLIER) as i64
                )
            } else {
                format!(
                    "движок не вывел ничего {} с при живом процессе, который при этом простаивал — работа прервана.",
                    liv.last_silent as i64
                )
            };
            return (1, output + &format!("\nERROR: {}\n", reason));
        }

        
        if reader.available() > 0 {
            let n = reader.read_up_to(&mut buf);
            if n > 0 {
                chunks.push(buf[..n].to_vec());
                liv.note_data();
                continue;
            }
        }

        std::thread::sleep(std::time::Duration::from_millis(POLL_INTERVAL_MS));
    }
}



pub(crate) fn wait_up_to(child: &mut Child, limit: std::time::Duration) {
    let start = std::time::Instant::now();
    while start.elapsed() < limit {
        if matches!(child.try_wait(), Ok(Some(_))) {
            return;
        }
        std::thread::sleep(std::time::Duration::from_millis(20));
    }
}

fn contains_ignore_case(haystack: &[u8], needle: &[u8]) -> bool {
    
    
    let needle_lower: Vec<u8> = needle.iter().map(|b| b.to_ascii_lowercase()).collect();
    if needle_lower.is_empty() {
        return true;
    }
    haystack
        .windows(needle_lower.len())
        .any(|w| w.iter().map(|b| b.to_ascii_lowercase()).eq(needle_lower.iter().copied()))
}

fn password_prompt_message() -> String {
    "\nERROR: zpaqfranz запросил пароль и ждёт ввода. Обычно это значит, \
что движок не смог открыть файл: путь содержит нелатинские символы, а \
на этом томе недоступны короткие имена 8.3. Переименуйте архив или \
перенесите его в папку с латинским именем.\n"
        .to_string()
}



fn effective_stall_timeout() -> f64 {
    crate::cfg::engine_stall_timeout(DEFAULT_STALL_TIMEOUT)
}
