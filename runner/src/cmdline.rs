
use crate::tasks::{py_str, py_truthy};
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};

const CHECK_UNITS: &[(char, u64)] = &[
    ('k', 1 << 10), ('m', 1 << 20), ('g', 1 << 30), ('t', 1 << 40),
];
const APPEND_CHECK: &str = "1G";
const APPEND_MIN_FREE: u64 = 1 << 30;

const BACKUP_INDEX_SUFFIX: &str = "_00000000_backup.txt";
const BACKUP_BINARY_INDEX_SUFFIX: &str = "_00000000_backup.index";
const BACKUP_INDEX_SIGNATURE: &str = "$zpaqfranz backupfile|";
const BACKUP_PART_DIGITS: usize = 8;

fn split_name(path: &str) -> (PathBuf, String, String) {
    let p = Path::new(path);
    let stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
    let suffix = match p.extension() {
        Some(e) if !e.is_empty() => format!(".{}", e.to_string_lossy()),
        _ => String::new(),
    };
    let parent = p.parent().unwrap_or_else(|| Path::new("")).to_path_buf();
    (parent, stem, suffix)
}

fn strip_part_suffix(stem: &str) -> String {
    let mut s = stem.to_string();
    let q = s.chars().rev().take_while(|c| *c == '?').count();
    if q > 0 {
        let cut = s.len() - q;
        if cut > 0 && s.as_bytes()[cut - 1] == b'_' {
            s.truncate(cut - 1);
        }
    }
    if let Some(idx) = s.rfind('_') {
        let tail = &s[idx + 1..];
        let n = tail.len();
        if (n == 3 || n == 4 || n == 8)
            && tail.bytes().all(|b| b.is_ascii_digit())
        {
            s.truncate(idx);
        }
    }
    s
}

pub fn multipart_base(path: &str) -> String {
    let (parent, stem, suffix) = split_name(path);
    let suffix = if suffix.is_empty() { ".zpaq".to_string() } else { suffix };
    let base = strip_part_suffix(&stem);
    if base.is_empty() {
        return path.to_string();
    }
    parent.join(format!("{}{}", base, suffix)).to_string_lossy().into_owned()
}

fn is_backup_index_file(path: &str) -> bool {
    match fs::read(path) {
        Ok(data) => data.starts_with(BACKUP_INDEX_SIGNATURE.as_bytes()),
        Err(_) => false,
    }
}

pub fn backup_base(path: &str) -> String {
    if path.is_empty() {
        return String::new();
    }
    let (parent, stem, _suffix) = split_name(path);
    let direct = parent.join(format!("{}{}", stem, BACKUP_INDEX_SUFFIX));
    if is_backup_index_file(&direct.to_string_lossy()) {
        return path.to_string();
    }
    multipart_base(path)
}

pub fn backup_index_path(path: &str) -> String {
    let (parent, stem, _suffix) = split_name(&backup_base(path));
    parent
        .join(format!("{}{}", stem, BACKUP_INDEX_SUFFIX))
        .to_string_lossy()
        .into_owned()
}

pub fn backup_binary_index_path(path: &str) -> String {
    let (parent, stem, _suffix) = split_name(&backup_base(path));
    parent
        .join(format!("{}{}", stem, BACKUP_BINARY_INDEX_SUFFIX))
        .to_string_lossy()
        .into_owned()
}

pub fn backup_mask(path: &str) -> String {
    let (parent, stem, suffix) = split_name(&backup_base(path));
    let suffix = if suffix.is_empty() { ".zpaq".to_string() } else { suffix };
    parent
        .join(format!(
            "{}_{}{}",
            stem,
            "?".repeat(BACKUP_PART_DIGITS),
            suffix
        ))
        .to_string_lossy()
        .into_owned()
}

pub fn is_backup_set(path: &str) -> bool {
    is_backup_index_file(&backup_index_path(path))
}

fn mask_match(pattern: &str, name: &str) -> bool {
    let pat: Vec<char> = pattern.chars().collect();
    let text: Vec<char> = name.chars().collect();
    if pat.len() != text.len() {
        return false;
    }
    pat.iter().zip(text.iter()).all(|(p, t)| {
        *p == '?'
            || if cfg!(windows) {
                p.to_lowercase().eq(t.to_lowercase())
            } else {
                p == t
            }
    })
}

pub fn backup_parts(path: &str) -> Vec<PathBuf> {
    let mask = backup_mask(path);
    let mask_path = Path::new(&mask);
    let name = match mask_path.file_name().and_then(|s| s.to_str()) {
        Some(n) => n,
        None => return Vec::new(),
    };
    let parent = match mask_path.parent() {
        Some(p) if !p.as_os_str().is_empty() => p,
        _ => Path::new("."),
    };
    let mut found = Vec::new();
    if let Ok(entries) = fs::read_dir(parent) {
        for entry in entries.flatten() {
            let candidate = entry.path();
            if !candidate.is_file() {
                continue;
            }
            if let Some(fname) = candidate.file_name().and_then(|s| s.to_str()) {
                if mask_match(name, fname) {
                    found.push(candidate);
                }
            }
        }
    }
    found.sort();
    found
}

pub fn backup_set_exists(path: &str) -> bool {
    is_backup_set(path) || !backup_parts(path).is_empty()
}

pub fn multipart_pattern(path: &str) -> String {
    if path.to_lowercase().ends_with(".zpaq") && is_backup_set(path) {
        return backup_mask(path);
    }
    let (parent, stem, suffix) = split_name(path);
    if !suffix.eq_ignore_ascii_case(".zpaq") {
        return path.to_string();
    }
    let digits = stem.chars().rev().take_while(|c| c.is_ascii_digit()).count();
    if !(digits == 3 || digits == 4 || digits == 8) {
        return path.to_string();
    }
    let cut = stem.len() - digits;
    if cut == 0 || stem.as_bytes()[cut - 1] != b'_' {
        return path.to_string();
    }
    let masked = format!("{}_{}{}", &stem[..cut - 1], "?".repeat(digits), suffix);
    parent.join(masked).to_string_lossy().into_owned()
}

pub fn archive_alias(path: &str) -> String {
    if is_backup_set(path) {
        backup_mask(path)
    } else {
        multipart_pattern(path)
    }
}

fn checksize_bytes(text: &str) -> u64 {
    let mut value = text.trim().replace(',', ".");
    if value.is_empty() {
        return 0;
    }
    let mut mult = 1u64;
    if let Some(last) = value.chars().last() {
        let last = last.to_ascii_lowercase();
        for (unit, factor) in CHECK_UNITS {
            if *unit == last {
                mult = *factor;
                value.pop();
                value = value.trim().to_string();
                break;
            }
        }
    }
    match value.parse::<f64>() {
        Ok(n) if n.is_finite() && n >= 0.0 => (n * mult as f64) as u64,
        _ => 0,
    }
}

fn checksize_text(n: u64) -> String {
    if n == 0 {
        return String::new();
    }
    for (suffix, mult) in [("T", 1u64 << 40), ("G", 1 << 30), ("M", 1 << 20), ("K", 1 << 10)] {
        if n >= mult {
            let value = n as f64 / mult as f64;
            if (value - value.round()).abs() < 0.01 {
                return format!("{}{}", value.round() as u64, suffix);
            }
            return format!("{}{}", format!("{:.2}", value)
                .trim_end_matches('0').trim_end_matches('.'), suffix);
        }
    }
    n.to_string()
}

pub fn resolve_checksize(requested: &str, dest: &str) -> String {
    let value = requested.trim();
    if value.is_empty() {
        return String::new();
    }
    if dest.is_empty() || dest.contains('?') {
        return value.to_string();
    }
    if !Path::new(dest).is_file() && !backup_set_exists(dest) {
        return value.to_string();
    }
    let Some(free) = crate::disk::free_bytes(dest) else {
        return value.to_string();
    };
    if free < APPEND_MIN_FREE {
        return value.to_string();
    }
    let want = checksize_bytes(value);
    if want > 0 && want < APPEND_MIN_FREE {
        checksize_text(want)
    } else {
        APPEND_CHECK.to_string()
    }
}

fn truthy(settings: &Value, key: &str) -> bool {
    py_truthy(settings.get(key))
}

fn py_value(settings: &Value, key: &str) -> String {
    py_str(settings.get(key).unwrap_or(&Value::Null))
}

pub fn build_create_cmd(
    zpaq: &str,
    settings: &Value,
    srcs: &[String],
    dest: &str,
    password: Option<&str>,
) -> Vec<String> {
    let mut cmd: Vec<String> = Vec::new();
    let is_backup = py_value(settings, "create_mode").trim().eq_ignore_ascii_case("backup");
    cmd.push(zpaq.to_string());
    cmd.push(if is_backup { "backup" } else { "a" }.to_string());
    cmd.push(dest.to_string());
    for s in srcs {
        cmd.push(s.clone());
    }
    if !dest.contains('?') && !is_backup {
        cmd.push("-open".to_string());
    }
    cmd.push("-nolfast".to_string());

    if let Some(arr) = settings.get("level").and_then(Value::as_array) {
        for f in arr {
            cmd.push(py_str(f));
        }
    }
    if truthy(settings, "hash") {
        cmd.push(py_value(settings, "hash"));
    }
    if truthy(settings, "comment") {
        cmd.push("-comment".to_string());
        cmd.push(py_value(settings, "comment"));
    }
    if let Some(arr) = settings.get("only_masks").and_then(Value::as_array) {
        for m in arr {
            cmd.push("-only".to_string());
            cmd.push(py_str(m));
        }
    }
    if let Some(arr) = settings.get("not_masks").and_then(Value::as_array) {
        for m in arr {
            cmd.push("-not".to_string());
            cmd.push(py_str(m));
        }
    }
    if truthy(settings, "longpath") && !srcs.is_empty() && !srcs.iter().any(|s| s == "*") {
        cmd.push("-longpath".to_string());
    }
    if truthy(settings, "date") {
        cmd.push("-date".to_string());
    }
    if truthy(settings, "norecursion") {
        cmd.push("-norecursion".to_string());
    }
    if truthy(settings, "forcewindows") {
        cmd.push("-forcewindows".to_string());
    }
    if truthy(settings, "force_xls") {
        cmd.push("-xls".to_string());
    }
    if truthy(settings, "nochecksum") {
        cmd.push("-nochecksum".to_string());
    }
    if truthy(settings, "nodedup") {
        cmd.push("-nodedup".to_string());
    }
    if truthy(settings, "vss") {
        cmd.push("-vss".to_string());
    }
    if truthy(settings, "checkspace") {
        cmd.push("-checksize".to_string());
        cmd.push(resolve_checksize(&py_value(settings, "checkspace"), dest));
    }
    if truthy(settings, "noonedrive") {
        cmd.push("-noonedrive".to_string());
    }
    if truthy(settings, "ignore") {
        cmd.push("-ignore".to_string());
    }
    if truthy(settings, "errorlog") {
        cmd.push("-errorlog".to_string());
        cmd.push(py_value(settings, "errorlog"));
    }
    if truthy(settings, "shutdown") {
        cmd.push("-shutdown".to_string());
    }
    if truthy(settings, "sfx") && !is_backup {
        cmd.push("-sfx".to_string());
        cmd.push(py_value(settings, "sfx"));
    }
    if truthy(settings, "chunk") {
        cmd.push("-chunk".to_string());
        cmd.push(py_value(settings, "chunk"));
    }
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}

pub fn build_test_cmd(
    zpaq: &str,
    dest: &str,
    password: Option<&str>,
    test_mode: Option<&str>,
    tmp_dir: Option<&str>,
    sources: &[String],
) -> Vec<String> {
    let mode = test_mode.unwrap_or("full").trim().to_lowercase();
    let backup = is_backup_set(dest);
    let mut cmd: Vec<String> = Vec::new();
    cmd.push(zpaq.to_string());
    if backup && mode != "sync" && mode != "verify_fs" {
        cmd.push("testbackup".to_string());
        cmd.push(backup_base(dest));
        if mode == "checksum" || mode == "verify" || mode == "paranoid" {
            cmd.push("-verify".to_string());
        }
    } else if mode == "verify_fs" {
        cmd.push("v".to_string());
        cmd.push(if backup { archive_alias(dest) } else { dest.to_string() });
    } else if mode == "sync" {
        cmd.push("sync".to_string());
        cmd.push(if backup { archive_alias(dest) } else { dest.to_string() });
        cmd.extend(sources.iter().cloned());
    } else {
        cmd.push("t".to_string());
        cmd.push(dest.to_string());
        match mode.as_str() {
            "checksum" => {
                cmd.push("-all".to_string());
                cmd.push("-checksum".to_string());
            }
            "verify" => {
                cmd.push("-verify".to_string());
            }
            "paranoid" => {
                cmd.push("-verify".to_string());
                cmd.push("-paranoid".to_string());
                if let Some(tmp) = tmp_dir {
                    if !tmp.is_empty() {
                        cmd.push("-to".to_string());
                        cmd.push(tmp.to_string());
                    }
                }
            }
            _ => {}
        }
    }
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}
