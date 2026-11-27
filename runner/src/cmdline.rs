
use crate::tasks::{py_str, py_truthy};
use serde_json::Value;
use std::path::Path;

const CHECK_UNITS: &[(char, u64)] = &[
    ('k', 1 << 10), ('m', 1 << 20), ('g', 1 << 30), ('t', 1 << 40),
];
const APPEND_CHECK: &str = "1G";
const APPEND_MIN_FREE: u64 = 1 << 30;

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
    if dest.is_empty() || dest.contains('?') || !Path::new(dest).is_file() {
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
    cmd.push(zpaq.to_string());
    cmd.push("a".to_string());
    cmd.push(dest.to_string());
    for s in srcs {
        cmd.push(s.clone());
    }
    if !dest.contains('?') {
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
    if truthy(settings, "sfx") {
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
    let mut cmd: Vec<String> = Vec::new();
    cmd.push(zpaq.to_string());
    if mode == "verify_fs" {
        cmd.push("v".to_string());
        cmd.push(dest.to_string());
    } else if mode == "sync" {
        cmd.push("sync".to_string());
        cmd.push(dest.to_string());
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
