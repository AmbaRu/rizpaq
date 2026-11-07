













use crate::engine::{self, EnginePipe};
use crate::tasks::{self, py_truthy};
use serde_json::Value;
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};


pub(crate) const CREATE_NO_WINDOW: u32 = 0x0800_0000;






pub const STATE_OK: &str = "ok";

pub const STATE_DAMAGED: &str = "damaged";

pub const STATE_UNREPAIRABLE: &str = "unrepairable";

pub const STATE_MISSING: &str = "missing";

pub const STATE_BROKEN: &str = "broken";

pub const STATE_FAILED: &str = "failed";


pub const DAMAGED_STATES: &[&str] = &[STATE_DAMAGED, STATE_UNREPAIRABLE];



pub fn reason_by_state(state: &str) -> &'static str {
    match state {
        STATE_MISSING => "par2_missing",
        STATE_BROKEN => "par2_broken",
        STATE_DAMAGED => "par2_damaged",
        STATE_UNREPAIRABLE => "par2_unrepairable",
        _ => "par2_failed",
    }
}

pub struct Par2Result {
    pub ok: bool,
    pub state: &'static str,
    pub log: String,
    pub recorded_size: Option<i64>,
    pub skipped: bool,
}

impl Par2Result {
    fn new(ok: bool, state: &'static str, log: impl Into<String>) -> Par2Result {
        Par2Result {
            ok,
            state,
            log: log.into(),
            recorded_size: None,
            skipped: false,
        }
    }
}

fn py_opt_int(v: Option<i64>) -> String {
    match v {
        Some(i) => i.to_string(),
        None => "None".to_string(),
    }
}


pub fn find_par2() -> Option<PathBuf> {
    if let Ok(p) = std::env::var("PAR2_BIN") {
        if !p.is_empty() && Path::new(&p).is_file() {
            return Some(PathBuf::from(p));
        }
    }
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().map(|d| d.to_path_buf())?;
        for base in [dir.clone(), dir.join("_internal")] {
            let cand = base.join("par2.exe");
            if cand.is_file() {
                return Some(cand);
            }
        }
        for _ in 0..5 {
            if !dir.pop() {
                break;
            }
            let cand = dir.join("par2.exe");
            if cand.is_file() {
                return Some(cand);
            }
        }
    }
    None
}


const TEMP_MARK: &str = ".rizpaq-new";

const MAX_SET_PATH: usize = 240;

fn splitext(name: &str) -> (&str, &str) {
    match name.rfind('.') {
        Some(i) if i > 0 => (&name[..i], &name[i..]),
        _ => (name, ""),
    }
}

fn is_vol_name(name: &str) -> bool {
    let lower = name.to_lowercase();
    let Some(s) = lower.strip_suffix(".par2") else {
        return false;
    };
    let Some(i) = s.rfind(".vol") else {
        return false;
    };
    let tail = &s[i + 4..]; // после ".vol"
    let Some(plus) = tail.find('+') else {
        return false;
    };
    let (a, b) = (&tail[..plus], &tail[plus + 1..]);
    !a.is_empty()
        && a.bytes().all(|c| c.is_ascii_digit())
        && !b.is_empty()
        && b.bytes().all(|c| c.is_ascii_digit())
}

fn py_join(a: &str, b: &str) -> String {
    if a.ends_with('\\') || a.ends_with('/') {
        format!("{}{}", a, b)
    } else {
        format!("{}\\{}", a, b)
    }
}

fn basename(p: &str) -> &str {
    Path::new(p)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("")
}

fn dirname_or_dot(p: &str) -> String {
    match Path::new(p).parent() {
        Some(d) if !d.as_os_str().is_empty() => d.to_string_lossy().into_owned(),
        _ => ".".to_string(),
    }
}

pub fn par2_main_name(archive_path: &str) -> String {
    format!("{}.par2", archive_path)
}

pub fn par2_temp_set_name(archive_path: &str) -> String {
    format!("{}{}.par2", archive_path, TEMP_MARK)
}

pub fn par2_set_files(archive_path: &str) -> Vec<String> {
    let main = par2_main_name(archive_path);
    let mut out: Vec<String> = Vec::new();
    if Path::new(&main).is_file() {
        out.push(main.clone());
    }

    let folder = dirname_or_dot(&main);
    let archive_base = basename(archive_path).to_string();
    let entries = match std::fs::read_dir(&folder) {
        Ok(it) => it,
        Err(_) => return out,
    };
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().into_owned();
        if name == basename(&main) {
            continue;
        }
        if name.contains(TEMP_MARK) {
            continue;
        }
        if is_vol_name(&name) && name.starts_with(&archive_base) {
            out.push(py_join(&folder, &name));
        }
    }
    out.sort();
    out
}

pub fn remove_par2_set(archive_path: &str) -> Vec<String> {
    let mut removed = Vec::new();
    for path in par2_set_files(archive_path) {
        if std::fs::remove_file(&path).is_ok() {
            removed.push(path);
        }
    }
    removed
}

fn temp_set_files(archive_path: &str) -> Vec<String> {
    let temp_main = par2_temp_set_name(archive_path);
    let folder = dirname_or_dot(&temp_main);
    let base = basename(&temp_main).to_string();
    let (stem, _) = splitext(&base);
    let mut out: Vec<String> = Vec::new();
    let entries = match std::fs::read_dir(&folder) {
        Ok(it) => it,
        Err(_) => return out,
    };
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().into_owned();
        if name == base {
            out.push(py_join(&folder, &name));
            continue;
        }
        if is_vol_name(&name) && name.starts_with(stem) {
            out.push(py_join(&folder, &name));
        }
    }
    out.sort();
    out
}

pub fn cleanup_orphans(archive_path: &str) -> Vec<String> {
    let mut removed = Vec::new();
    for path in temp_set_files(archive_path) {
        if std::fs::remove_file(&path).is_ok() {
            removed.push(path);
        }
    }
    removed
}


pub fn needs_subst(folder: &str) -> bool {
    let trimmed = folder.trim_end_matches(['\\', '/']);
    let name = basename(trimmed);
    let name = if name.is_empty() { "x" } else { name };
    let probe = py_join(folder, &format!("{}.zpaq.vol127+35.par2", name));
    probe.chars().count() > MAX_SET_PATH
}

fn run_capture(cmd: &[String], timeout: Duration) -> Option<i32> {
    let mut command = Command::new(&cmd[0]);
    command
        .args(&cmd[1..])
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .creation_flags(CREATE_NO_WINDOW);
    let mut child = match command.spawn() {
        Ok(c) => c,
        Err(_) => return None,
    };
    let deadline = Instant::now() + timeout;
    loop {
        match child.try_wait() {
            Ok(Some(status)) => return status.code(),
            Ok(None) => {}
            Err(_) => return None,
        }
        if Instant::now() >= deadline {
            child.kill().ok();
            let _ = child.wait();
            return None;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
}

pub struct SubstLetter {
    folder: String,
    pub letter: Option<String>,
    pub required: bool,
    pub failed: bool,
}

impl SubstLetter {
    pub fn new(folder: &str) -> SubstLetter {
        SubstLetter {
            folder: folder.to_string(),
            letter: None,
            required: false,
            failed: false,
        }
    }

    pub fn enter(&mut self) -> Option<String> {
        self.required = needs_subst(&self.folder);
        if !self.required {
            return None;
        }
        for letter in b'A'..=b'Z' {
            let drive = format!("{}:", letter as char);
            if Path::new(&drive).exists() {
                continue;
            }
            let cmd = vec![
                "subst".to_string(),
                drive.clone(),
                self.folder.clone(),
            ];
            if run_capture(&cmd, Duration::from_secs(10)) == Some(0) {
                self.letter = Some(drive.clone());
                return Some(drive);
            }
        }
        self.failed = true;
        None
    }
}

impl Drop for SubstLetter {
    fn drop(&mut self) {
        if let Some(letter) = self.letter.take() {
            let cmd = vec!["subst".to_string(), letter, "/d".to_string()];
            run_capture(&cmd, Duration::from_secs(10));
        }
    }
}


#[derive(Debug, PartialEq)]
pub enum RunRc {
    Code(i32),
    Timeout,
    Error,
}

fn run_par2(bin_path: &str, args: &[String], timeout_secs: u64) -> (RunRc, String) {
    let (reader, out_stdio, err_stdio) = match EnginePipe::create() {
        Ok(p) => p.split(),
        Err(_) => return (RunRc::Error, "OSError: cannot create pipe".to_string()),
    };

    let mut command = Command::new(bin_path);
    command
        .args(args)
        .stdin(Stdio::null())
        .stdout(out_stdio)
        .stderr(err_stdio)
        .creation_flags(CREATE_NO_WINDOW);

    let mut child = match command.spawn() {
        Ok(c) => c,
        Err(e) => return (RunRc::Error, format!("OSError: {}", e)),
    };

    let mut chunks: Vec<Vec<u8>> = Vec::new();
    let mut buf = vec![0u8; 4096];
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);

    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                loop {
                    if reader.available() == 0 {
                        break;
                    }
                    let n = reader.read_up_to(&mut buf);
                    if n == 0 {
                        break;
                    }
                    chunks.push(buf[..n].to_vec());
                }
                let output = engine::decode_bytes(&chunks.concat());
                return (RunRc::Code(status.code().unwrap_or(-1)), output);
            }
            Ok(None) => {}
            Err(_) => {
                let output = engine::decode_bytes(&chunks.concat());
                return (RunRc::Error, output);
            }
        }

        if Instant::now() >= deadline {
            child.kill().ok();
            let start = Instant::now();
            while start.elapsed() < Duration::from_secs(10)
                && matches!(child.try_wait(), Ok(None))
            {
                std::thread::sleep(Duration::from_millis(20));
            }
            loop {
                if reader.available() == 0 {
                    break;
                }
                let n = reader.read_up_to(&mut buf);
                if n == 0 {
                    break;
                }
                chunks.push(buf[..n].to_vec());
            }
            let output = engine::decode_bytes(&chunks.concat());
            return (RunRc::Timeout, output);
        }

        if reader.available() > 0 {
            let n = reader.read_up_to(&mut buf);
            if n > 0 {
                chunks.push(buf[..n].to_vec());
                continue;
            }
        }

        std::thread::sleep(Duration::from_millis(50));
    }
}


fn contains_ci(haystack: &str, needle: &str) -> bool {
    haystack.to_lowercase().contains(&needle.to_lowercase())
}

fn contains_dash_word(lower_text: &str, word: &str) -> bool {
    let mut from = 0usize;
    while let Some(pos) = lower_text[from..].find('-') {
        let at = from + pos;
        let mut rest = &lower_text[at + 1..];
        rest = rest.trim_start_matches(|c: char| c.is_whitespace());
        if rest.starts_with(word) {
            return true;
        }
        from = at + 1;
    }
    false
}

pub fn read_recorded_size(log: &str) -> Option<i64> {
    const HEAD: &str = "total size of the data files is";
    const TAIL: &str = "bytes";
    let lower = log.to_lowercase();
    let start = lower.find(HEAD)? + HEAD.len();
    let rest = &lower[start..];
    let end = rest.find(TAIL)?;
    let middle = &rest[..end];
    let digits: String = middle
        .trim_start()
        .chars()
        .take_while(|c| c.is_ascii_digit() || *c == ',')
        .filter(|c| *c != ',')
        .collect();
    if digits.is_empty() {
        return None;
    }
    digits.parse::<i64>().ok()
}

pub fn classify_verify_log(log: &str) -> Option<&'static str> {
    if log.is_empty() {
        return None;
    }
    let lower = log.to_lowercase();

    
    if contains_ci(log, "All files are correct") {
        return Some(STATE_OK);
    }

    
    if contains_dash_word(&lower, "damaged") {
        if contains_ci(log, "Repair is not possible") {
            return Some(STATE_UNREPAIRABLE);
        }
        if contains_ci(log, "Repair is possible") {
            return Some(STATE_DAMAGED);
        }
        
        
        
        return Some(STATE_UNREPAIRABLE);
    }

    
    if contains_dash_word(&lower, "missing") {
        return Some(STATE_MISSING);
    }

    
    for marker in [
        "Unable to load",
        "Cannot load",
        "is not a valid par2 file",
        "Cannot find",
        "does not exist",
        "No files could be found",
    ] {
        if contains_ci(log, marker) {
            return Some(STATE_BROKEN);
        }
    }

    None
}



fn classify_verify(rc: &RunRc, log: &str) -> Par2Result {
    let size = read_recorded_size(log);
    let make = |ok: bool, state: &'static str, with_size: bool| Par2Result {
        ok,
        state,
        log: log.to_string(),
        recorded_size: if with_size { size } else { None },
        skipped: false,
    };
    match classify_verify_log(log) {
        Some(STATE_OK) => make(true, STATE_OK, true),
        Some(s) if DAMAGED_STATES.contains(&s) => make(false, s, true),
        Some(s @ (STATE_MISSING | STATE_BROKEN)) => make(false, s, true),
        _ => match rc {
            RunRc::Code(0) => make(true, STATE_OK, true),
            RunRc::Code(1) => make(false, STATE_DAMAGED, true),
            RunRc::Code(3) => make(false, STATE_MISSING, false),
            RunRc::Code(2) => make(false, STATE_UNREPAIRABLE, true),
            _ => make(false, STATE_FAILED, false),
        },
    }
}


fn py_int(v: Option<&Value>) -> Option<i64> {
    match v {
        None | Some(Value::Null) => None,
        Some(Value::Number(n)) => n.as_i64().or_else(|| n.as_f64().map(|f| f as i64)),
        Some(Value::String(s)) => s.trim().parse::<i64>().ok(),
        Some(Value::Bool(b)) => Some(if *b { 1 } else { 0 }),
        _ => None,
    }
}

pub fn create_parset(
    bin_path: &str,
    archive_path: &str,
    redundancy: i64,
    memory_mb: Option<i64>,
    threads: Option<i64>,
    block_size: Option<i64>,
    recursion: bool,
    set_name: Option<&str>,
    timeout_secs: u64,
) -> Par2Result {
    if bin_path.is_empty() || !Path::new(bin_path).is_file() {
        return Par2Result::new(false, STATE_FAILED, "par2 не найден");
    }

    let mut subst = SubstLetter::new(&dirname_or_dot(archive_path));
    let drive = subst.enter();

    let target = match &drive {
        Some(d) => py_join(&format!("{}\\", d), basename(archive_path)),
        None => archive_path.to_string(),
    };

    let mut args: Vec<String> = vec!["create".to_string()];
    args.push(format!("-r{}", redundancy.max(1)));
    if let Some(m) = memory_mb {
        args.push(format!("-m{}", m));
    }
    if let Some(t) = threads {
        args.push(format!("-t{}", t));
    }
    if let Some(s) = block_size {
        args.push(format!("-s{}", s));
    }
    if recursion {
        args.push("-R".to_string());
    }
    if let Some(name) = set_name {
        let name = match &drive {
            Some(d) => py_join(&format!("{}\\", d), basename(name)),
            None => name.to_string(),
        };
        args.push("-a".to_string());
        args.push(name);
    }
    args.push(target);

    let (rc, log) = run_par2(bin_path, &args, timeout_secs);
    let subst_failed = subst.failed;
    drop(subst); // буква снимается здесь, признак «не вышло» уже сохранён

    if rc == RunRc::Code(0) {
        return Par2Result::new(true, STATE_OK, log);
    }

    let log = if subst_failed {
        format!(
            "[rizpaq] путь слишком длинный: Windows не дала укоротить его \
через subst ({} символов, предел около 260). Набор создан не будет.\n{}",
            archive_path.chars().count(),
            log
        )
    } else {
        log
    };

    if rc == RunRc::Code(3) && log.contains("already exists") {
        return Par2Result::new(false, STATE_FAILED, log);
    }
    if rc == RunRc::Code(3) && log.contains("must specify a list of files") {
        return Par2Result::new(false, STATE_MISSING, log);
    }
    if rc == RunRc::Timeout {
        return Par2Result::new(false, STATE_FAILED, "превышено время ожидания");
    }
    Par2Result::new(false, STATE_FAILED, log)
}

pub fn verify_parset(bin_path: &str, par2_path: &str, timeout_secs: u64) -> Par2Result {
    if bin_path.is_empty() || !Path::new(bin_path).is_file() {
        return Par2Result::new(false, STATE_FAILED, "par2 не найден");
    }
    if par2_path.is_empty() || !Path::new(par2_path).is_file() {
        return Par2Result::new(false, STATE_MISSING, "набор не найден");
    }

    let args = vec!["v".to_string(), "-v".to_string(), par2_path.to_string()];
    let (rc, log) = run_par2(bin_path, &args, timeout_secs);
    match rc {
        RunRc::Timeout => {
            Par2Result::new(false, STATE_FAILED, "превышено время ожидания")
        }
        RunRc::Error => Par2Result::new(false, STATE_FAILED, log),
        RunRc::Code(_) => classify_verify(&rc, &log),
    }
}

#[allow(clippy::too_many_arguments)]
pub fn refresh_par2_set(
    bin_path: &str,
    archive_path: &str,
    redundancy: i64,
    memory_mb: Option<i64>,
    threads: Option<i64>,
    block_size: Option<i64>,
    recursion: bool,
    skip_if_unchanged: bool,
    unchanged_size: Option<i64>,
) -> Par2Result {
    if bin_path.is_empty() || !Path::new(bin_path).is_file() {
        return Par2Result::new(false, STATE_FAILED, "par2 не найден");
    }
    if archive_path.is_empty() || !Path::new(archive_path).is_file() {
        return Par2Result::new(false, STATE_MISSING, "файл архива не найден");
    }

    let size_before = match std::fs::metadata(archive_path) {
        Ok(md) => md.len() as i64,
        Err(e) => {
            return Par2Result::new(
                false,
                STATE_MISSING,
                format!("не удалось прочитать архив: OSError: {}", e),
            )
        }
    };

    if skip_if_unchanged {
        if let Some(known) = unchanged_size {
            if size_before == known {
                let mut res = Par2Result::new(
                    true,
                    STATE_OK,
                    "архив не изменился, набор остаётся в силе",
                );
                res.recorded_size = Some(size_before);
                res.skipped = true;
                return res;
            }
        }
    }

    cleanup_orphans(archive_path);

    let created = create_parset(
        bin_path,
        archive_path,
        redundancy,
        memory_mb,
        threads,
        block_size,
        recursion,
        Some(&par2_temp_set_name(archive_path)),
        3600,
    );
    if !created.ok {
        cleanup_orphans(archive_path);
        return created;
    }

    let size_after = std::fs::metadata(archive_path).ok().map(|m| m.len() as i64);

    if size_after != Some(size_before) {
        cleanup_orphans(archive_path);
        let mut res = Par2Result::new(
            false,
            STATE_FAILED,
            "архив изменился во время создания набора, набор не создан. \
Ничего не изменено, следующий запуск создаст набор заново.",
        );
        res.recorded_size = size_after;
        return res;
    }

    remove_par2_set(archive_path);

    let mut renamed = 0usize;
    for path in temp_set_files(archive_path) {
        let name = basename(&path).to_string();
        if !name.contains(TEMP_MARK) {
            continue;
        }
        let target_name = name.replacen(TEMP_MARK, "", 1);
        let target = py_join(&dirname_or_dot(&path), &target_name);
        if std::fs::rename(&path, &target).is_ok() {
            renamed += 1;
        }
    }

    if renamed == 0 {
        return Par2Result::new(
            false,
            STATE_FAILED,
            "набор создан, но ни один файл не удалось переименовать — \
временный набор оставлен на диске",
        );
    }

    let mut res = Par2Result::new(true, STATE_OK, created.log);
    res.recorded_size = size_after;
    res
}


pub fn headless_par2_verify(dest: &str) -> (i32, String, &'static str) {
    let Some(par2_bin) = find_par2() else {
        return (
            1,
            "[par2] par2.exe не найден, проверка невозможна\n".to_string(),
            STATE_FAILED,
        );
    };

    let par2_path = par2_main_name(dest);
    if !Path::new(&par2_path).is_file() {
        return (
            1,
            format!(
                "[par2] набор не создан рядом с архивом — проверять нечего\n\
[par2] ожидался файл: {}\n",
                par2_path
            ),
            STATE_MISSING,
        );
    }

    let res = verify_parset(&par2_bin.to_string_lossy(), &par2_path, 3600);

    let tail: Vec<&str> = res
        .log
        .lines()
        .filter(|ln| !ln.trim().is_empty())
        .collect();
    let start = tail.len().saturating_sub(12);
    let body = if tail.is_empty() {
        String::new()
    } else {
        tail[start..].join("\n")
    };

    match res.state {
        STATE_OK => (
            0,
            format!(
                "[par2] набор проверен, архив цел\n[par2] защищает {} байт\n",
                py_opt_int(res.recorded_size)
            ),
            res.state,
        ),
        STATE_DAMAGED => (
            0,
            format!("[par2] АРХИВ ПОВРЕЖДЁН, восстановление возможно\n{}\n", body),
            res.state,
        ),
        STATE_UNREPAIRABLE => (
            1,
            format!(
                "[par2] АРХИВ ПОВРЕЖДЁН, ИЗБЫТОЧНОСТИ НЕ ХВАТИТ — \
ВОССТАНОВЛЕНИЕ НЕВОЗМОЖНО\n{}\n",
                body
            ),
            res.state,
        ),
        other => {
            let reason = match other {
                STATE_MISSING => "набор не найден",
                STATE_BROKEN => "набор повреждён и не читается",
                _ => "проверка не удалась",
            };
            (1, format!("[par2] {}\n{}\n", reason, body), res.state)
        }
    }
}











pub fn headless_par2_create(
    rzp_path: &str,
    work: &Value,
    dest: &str,
    settings: &Value,
) -> String {
    let header = "\n[par2] создание набора защиты от повреждений\n".to_string();

    let Some(par2_bin) = find_par2() else {
        return header + "par2.exe не найден, набор не создан\n";
    };

    
    
    let options = settings
        .get("par2_options")
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();

    let known_size = work.get("par2_size").and_then(Value::as_i64);

    
    let redundancy_raw = options.get("redundancy").cloned().unwrap_or(Value::Null);
    let redundancy = if py_truthy(Some(&redundancy_raw)) {
        match py_int(Some(&redundancy_raw)) {
            Some(v) => v,
            None => {
                return header
                    + &format!(
                        "ошибка набора: ValueError: invalid literal for int() \
with base 10: {}\n",
                        tasks::py_str(&redundancy_raw)
                    )
            }
        }
    } else {
        5
    };

    
    let mut opts: Vec<(String, Option<i64>)> = Vec::new();
    for key in ["memory_mb", "threads", "block_size"] {
        let raw = options.get(key).cloned().unwrap_or(Value::Null);
        if py_truthy(Some(&raw)) {
            match py_int(Some(&raw)) {
                Some(v) => opts.push((key.to_string(), Some(v))),
                None => {
                    return header
                        + &format!(
                            "ошибка набора: ValueError: invalid literal for \
int() with base 10: {}\n",
                            tasks::py_str(&raw)
                        )
                }
            }
        } else {
            opts.push((key.to_string(), None));
        }
    }
    let memory_mb = opts.iter().find(|(k, _)| k == "memory_mb").and_then(|(_, v)| *v);
    let threads = opts.iter().find(|(k, _)| k == "threads").and_then(|(_, v)| *v);
    let block_size = opts.iter().find(|(k, _)| k == "block_size").and_then(|(_, v)| *v);
    let recursion = py_truthy(options.get("recursion"));

    let res = refresh_par2_set(
        &par2_bin.to_string_lossy(),
        dest,
        redundancy,
        memory_mb,
        threads,
        block_size,
        recursion,
        known_size.is_some(),
        known_size,
    );

    if !res.ok {
        
        
        let tail: Vec<&str> = res.log.trim().lines().collect();
        let last = tail
            .last()
            .map(|l| l.chars().take(200).collect::<String>())
            .unwrap_or_else(|| "причина неизвестна".to_string());
        return header + &format!("набор НЕ создан: {}\n", last);
    }

    if let Some(size) = res.recorded_size {
        
        let work_id = match work.get("id") {
            Some(v) if py_truthy(Some(v)) => tasks::py_str(v),
            _ => String::new(),
        };
        if !work_id.is_empty() {
            let rzp = rzp_path.to_string();
            let _ = tasks::update_container(Path::new(&rzp), |c| {
                tasks::update_work_meta(c, &work_id, size, &tasks::now_str());
            });
        }
    }

    if res.log.contains("не изменился") {
        return header + "архив не изменился, набор остался в силе\n";
    }
    header
        + &format!(
            "набор создан, защищает {} байт\n",
            py_opt_int(res.recorded_size)
        )
}





#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn classify_ok_first() {
        
        assert_eq!(
            classify_verify_log("All files are correct. Recovery: 3 blocks"),
            Some(STATE_OK)
        );
    }

    #[test]
    fn classify_damaged_order() {
        let damaged = "Target: data.bin - damaged\nRepair is possible.";
        assert_eq!(classify_verify_log(damaged), Some(STATE_DAMAGED));
        let unrep = "Target: data.bin - damaged\nRepair is not possible.";
        assert_eq!(classify_verify_log(unrep), Some(STATE_UNREPAIRABLE));
        
        assert_eq!(
            classify_verify_log("Target: data.bin - damaged"),
            Some(STATE_UNREPAIRABLE)
        );
    }

    #[test]
    fn classify_missing_and_broken() {
        assert_eq!(
            classify_verify_log("Target: data.bin - missing"),
            Some(STATE_MISSING)
        );
        assert_eq!(
            classify_verify_log("Unable to load input files"),
            Some(STATE_BROKEN)
        );
        assert_eq!(classify_verify_log("совсем другой текст"), None);
        assert_eq!(classify_verify_log(""), None);
    }

    #[test]
    fn classify_by_rc_fallback() {
        
        let r = classify_verify(&RunRc::Code(2), "непонятно");
        assert_eq!(r.state, STATE_UNREPAIRABLE);
        let r = classify_verify(&RunRc::Code(3), "непонятно");
        assert_eq!(r.state, STATE_MISSING);
        let r = classify_verify(&RunRc::Code(7), "непонятно");
        assert_eq!(r.state, STATE_FAILED);
    }

    #[test]
    fn recorded_size_parses() {
        assert_eq!(
            read_recorded_size(
                "Total size of the data files is 2,003,944 bytes"
            ),
            Some(2003944)
        );
        assert_eq!(read_recorded_size("ничего тут нет"), None);
        assert_eq!(read_recorded_size(""), None);
    }

    #[test]
    fn vol_names() {
        assert!(is_vol_name("backup.zpaq.vol00+01.par2"));
        assert!(is_vol_name("backup.zpaq.VOL127+35.PAR2"));
        assert!(!is_vol_name("backup.zpaq.par2"));
        assert!(!is_vol_name("backup.zpaq.vol00+01.par2.bak"));
        assert!(!is_vol_name("backup.zpaq.volX+01.par2"));
        assert!(!is_vol_name("backup.zpaq.vol00+.par2"));
    }

    #[test]
    fn names_built_like_python() {
        assert_eq!(par2_main_name("D:\\b\\arc.zpaq"), "D:\\b\\arc.zpaq.par2");
        assert_eq!(
            par2_temp_set_name("D:\\b\\arc.zpaq"),
            "D:\\b\\arc.zpaq.rizpaq-new.par2"
        );
    }

    #[test]
    fn needs_subst_threshold() {
        
        assert!(!needs_subst("C:\\backups"));
        
        let long = format!("C:\\{}", "длинное_имя_папки_".repeat(12));
        assert!(needs_subst(&long));
    }

    #[test]
    fn dash_word_matches_regex_semantics() {
        assert!(contains_dash_word("target - damaged", "damaged"));
        assert!(contains_dash_word("target-   damaged", "damaged"));
        assert!(!contains_dash_word("undamaged things", "damaged"));
        assert!(contains_dash_word("target - missing", "missing"));
    }
}
