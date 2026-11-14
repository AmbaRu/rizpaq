
use base64::Engine as _;
use chrono::{Local, NaiveDate, NaiveDateTime};
use serde_json::{json, Map, Value};
use std::path::{Path, PathBuf};

pub const CONTAINER_FORMAT: &str = "rizpaq.tasks";
pub const CONTAINER_VERSION: i64 = 1;

pub const JOB_FIELDS: &[&str] = &[
    "action",
    "test_mode",
    "level",
    "level_key",
    "hash",
    "hash_key",
    "method_params",
    "verify",
    "longpath",
    "date",
    "norecursion",
    "forcewindows",
    "force_xls",
    "nochecksum",
    "nodedup",
    "vss",
    "checkspace",
    "noonedrive",
    "ignore",
    "errorlog",
    "shutdown",
    "sfx",
    "chunk",
    "copy",
    "schedule",
    "task_log_mode",
    "par2_enabled",
    "par2_options",
    "new_password",
];

pub const JOB_STATUSES: &[&str] = &["ok", "error", "busy"];
pub const JOB_REASONS: &[&str] = &[
    "par2_missing",
    "par2_broken",
    "par2_damaged",
    "par2_unrepairable",
    "par2_failed",
    "sync_failed",
];
pub const LOG_MODES: &[&str] = &["short", "full", "none"];
pub const TEST_MODES: &[&str] = &[
    "full",
    "checksum",
    "verify",
    "paranoid",
    "par2",
    "verify_fs",
    "sync",
];

pub fn now_str() -> String {
    Local::now().format("%d.%m.%Y %H:%M:%S").to_string()
}

fn normalize_date_str(raw: &str) -> String {
    let text = raw.trim();
    if text.is_empty() {
        return String::new();
    }
    let b = text.as_bytes();
    if text.len() == 19 && b[2] == b'.' && b[5] == b'.' {
        return text.to_string();
    }
    if text.len() == 19 && b[4] == b'-' && b[7] == b'-' {
        if let Ok(dt) = NaiveDateTime::parse_from_str(text, "%Y-%m-%d %H:%M:%S") {
            return dt.format("%d.%m.%Y %H:%M:%S").to_string();
        }
        return text.to_string();
    }
    if text.len() == 10 && b[4] == b'-' && b[7] == b'-' {
        if let Ok(d) = NaiveDate::parse_from_str(text, "%Y-%m-%d") {
            return d.format("%d.%m.%Y").to_string();
        }
        return text.to_string();
    }
    text.to_string()
}

fn normalize_date_value(v: Option<&Value>) -> Value {
    match v {
        None | Some(Value::Null) => Value::Null,
        Some(x) => json!(normalize_date_str(&py_str(x))),
    }
}

pub fn py_str(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Bool(true) => "True".to_string(),
        Value::Bool(false) => "False".to_string(),
        Value::Number(_) => v.to_string(),
        Value::Null => "None".to_string(),
        other => other.to_string(),
    }
}

pub fn py_truthy(v: Option<&Value>) -> bool {
    match v {
        None | Some(Value::Null) => false,
        Some(Value::Bool(b)) => *b,
        Some(Value::String(s)) => !s.is_empty(),
        Some(Value::Number(n)) => n.as_f64().map(|f| f != 0.0).unwrap_or(false),
        Some(Value::Array(a)) => !a.is_empty(),
        Some(Value::Object(o)) => !o.is_empty(),
    }
}

fn str_or(v: Option<&Value>, default: &str) -> String {
    if py_truthy(v) {
        py_str(v.unwrap())
    } else {
        default.to_string()
    }
}

fn str_or_trim(v: Option<&Value>, default: &str) -> String {
    let s = str_or(v, "");
    let t = s.trim();
    if t.is_empty() {
        default.to_string()
    } else {
        t.to_string()
    }
}

fn norm_action(v: Option<&Value>) -> Value {
    match v.and_then(Value::as_str) {
        Some(s)
            if matches!(
                s,
                "backup"
                    | "test"
                    | "crop"
                    | "consolidate"
                    | "sfx"
                    | "info"
                    | "password"
                    | "checkpassword"
            ) =>
        {
            json!(s)
        }
        _ => json!("backup"),
    }
}

fn norm_test_mode(v: Option<&Value>) -> Value {
    match v.and_then(Value::as_str) {
        Some(s) if TEST_MODES.contains(&s) => json!(s),
        _ => json!("full"),
    }
}

fn norm_status(v: Option<&Value>) -> Value {
    match v.and_then(Value::as_str) {
        Some(s) if JOB_STATUSES.contains(&s) => json!(s),
        _ => Value::Null,
    }
}

fn norm_reason(v: Option<&Value>) -> Value {
    match v.and_then(Value::as_str) {
        Some(s) if JOB_REASONS.contains(&s) => json!(s),
        _ => Value::Null,
    }
}

fn norm_par2_size(v: Option<&Value>) -> Value {
    let parsed: Option<i64> = match v {
        None | Some(Value::Null) => None,
        Some(Value::Number(n)) => {
            if let Some(i) = n.as_i64() {
                Some(i)
            } else {
                n.as_f64().map(|f| f as i64)
            }
        }
        Some(Value::String(s)) => s.trim().parse::<i64>().ok(),
        Some(Value::Bool(b)) => Some(if *b { 1 } else { 0 }),
        _ => None,
    };
    match parsed {
        Some(i) if i >= 0 => json!(i),
        _ => Value::Null,
    }
}

fn norm_run_count(v: Option<&Value>) -> i64 {
    if !py_truthy(v) {
        return 0;
    }
    match v.unwrap() {
        Value::Number(n) => n
            .as_i64()
            .unwrap_or_else(|| n.as_f64().map(|f| f as i64).unwrap_or(0)),
        Value::String(s) => s.trim().parse::<i64>().unwrap_or(0),
        Value::Bool(b) => {
            if *b {
                1
            } else {
                0
            }
        }
        _ => 0,
    }
}

pub fn decode_password(v: Option<&Value>) -> Value {
    let s = match v.and_then(Value::as_str) {
        Some(s) if !s.is_empty() => s,
        _ => return Value::Null,
    };
    match base64::engine::general_purpose::STANDARD.decode(s) {
        Ok(bytes) => match String::from_utf8(bytes) {
            Ok(text) => json!(text),
            Err(_) => Value::Null,
        },
        Err(_) => Value::Null,
    }
}

pub fn empty_container() -> Value {
    let now = now_str();
    json!({
        "format": CONTAINER_FORMAT,
        "version": CONTAINER_VERSION,
        "name": Value::Null,
        "created": now,
        "modified": now,
        "works": [],
    })
}

fn normalize_work(w: &Value) -> Option<Value> {
    let obj = w.as_object()?;
    let id = match obj.get("id") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => return None,
    };
    let sources: Vec<Value> = match obj.get("sources").filter(|v| v.is_array()) {
        Some(Value::Array(arr)) => arr
            .iter()
            .map(py_str)
            .filter(|s| !s.trim().is_empty())
            .map(|s| json!(s))
            .collect(),
        _ => Vec::new(),
    };
    let only_masks: Vec<Value> = match obj.get("only_masks").filter(|v| v.is_array()) {
        Some(Value::Array(arr)) => arr.iter().map(|m| json!(py_str(m))).collect(),
        _ => Vec::new(),
    };
    let not_masks: Vec<Value> = match obj.get("not_masks").filter(|v| v.is_array()) {
        Some(Value::Array(arr)) => arr.iter().map(|m| json!(py_str(m))).collect(),
        _ => Vec::new(),
    };
    let par2_created = {
        let s = str_or(obj.get("par2_created"), "");
        if s.is_empty() {
            Value::Null
        } else {
            json!(normalize_date_str(&s))
        }
    };
    Some(json!({
        "id": id,
        "title": str_or_trim(obj.get("title"), "Работа"),
        "created": normalize_date_value(Some(&json!(str_or(obj.get("created"), &now_str())))),
        "modified": normalize_date_value(Some(&json!(str_or(obj.get("modified"), &now_str())))),
        "sources": sources,
        "dest": str_or(obj.get("dest"), ""),
        "password_b64": match obj.get("password_b64") {
            Some(v) if py_truthy(Some(v)) => v.clone(),
            _ => Value::Null,
        },
        "only_masks": only_masks,
        "not_masks": not_masks,
        "comment": str_or(obj.get("comment"), ""),
        "par2_size": norm_par2_size(obj.get("par2_size")),
        "par2_created": par2_created,
        "jobs": obj
            .get("jobs")
            .and_then(Value::as_array)
            .map(|arr| arr.iter().filter_map(normalize_job).collect::<Vec<Value>>())
            .unwrap_or_default(),
    }))
}

fn normalize_job(j: &Value) -> Option<Value> {
    let obj = j.as_object()?;
    let id = match obj.get("id") {
        Some(Value::String(s)) if !s.is_empty() => s.clone(),
        _ => return None,
    };
    let mut out = Map::new();
    out.insert("id".into(), json!(id));
    out.insert("title".into(), json!(str_or_trim(obj.get("title"), "Задание")));
    out.insert(
        "created".into(),
        normalize_date_value(Some(&json!(str_or(obj.get("created"), &now_str())))),
    );
    out.insert(
        "modified".into(),
        normalize_date_value(Some(&json!(str_or(obj.get("modified"), &now_str())))),
    );
    out.insert(
        "last_run".into(),
        normalize_date_value(obj.get("last_run")),
    );
    out.insert("last_status".into(), norm_status(obj.get("last_status")));
    out.insert("last_reason".into(), norm_reason(obj.get("last_reason")));
    out.insert("run_count".into(), json!(norm_run_count(obj.get("run_count"))));
    out.insert(
        "schedule".into(),
        match obj.get("schedule") {
            Some(v @ Value::Object(_)) => v.clone(),
            _ => Value::Null,
        },
    );
    out.insert(
        "task_log_mode".into(),
        match obj.get("task_log_mode").and_then(Value::as_str) {
            Some(s) if LOG_MODES.contains(&s) => json!(s),
            _ => json!("short"),
        },
    );
    out.insert("action".into(), norm_action(obj.get("action")));
    out.insert("test_mode".into(), norm_test_mode(obj.get("test_mode")));
    for key in JOB_FIELDS {
        if matches!(*key, "schedule" | "task_log_mode" | "action" | "test_mode") {
            continue;
        }
        out.insert((*key).to_string(), obj.get(*key).cloned().unwrap_or(Value::Null));
    }
    Some(Value::Object(out))
}

pub fn validate(c: &Value) -> Option<Value> {
    let obj = c.as_object()?;
    if obj.get("format").and_then(Value::as_str) != Some(CONTAINER_FORMAT) {
        return None;
    }
    if !matches!(obj.get("works"), Some(Value::Array(_))) {
        return None;
    }
    let mut out = empty_container();
    let name = str_or_trim(obj.get("name"), "");
    out["name"] = if name.is_empty() { Value::Null } else { json!(name) };
    let default_created = out["created"].as_str().unwrap_or_default().to_string();
    let default_modified = out["modified"].as_str().unwrap_or_default().to_string();
    out["created"] = json!(str_or(obj.get("created"), &default_created));
    out["modified"] = json!(str_or(obj.get("modified"), &default_modified));
    let works: Vec<Value> = obj["works"]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(normalize_work)
        .collect();
    out["works"] = json!(works);
    Some(out)
}

pub fn load_container(path: &Path) -> Value {
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(_) => return empty_container(),
    };
    let parsed: Value = match serde_json::from_str(&text) {
        Ok(v) => v,
        Err(_) => return empty_container(),
    };
    validate(&parsed).unwrap_or_else(empty_container)
}

pub fn iter_jobs<'a>(container: &'a Value) -> Vec<(&'a Value, &'a Value)> {
    let mut out = Vec::new();
    if let Some(works) = container.get("works").and_then(Value::as_array) {
        for w in works {
            if let Some(jobs) = w.get("jobs").and_then(Value::as_array) {
                for j in jobs {
                    out.push((w, j));
                }
            }
        }
    }
    out
}

pub fn find_job<'a>(container: &'a Value, job_id: &str) -> Option<(&'a Value, &'a Value)> {
    iter_jobs(container)
        .into_iter()
        .find(|(_, j)| j.get("id").and_then(Value::as_str) == Some(job_id))
}

pub fn job_to_runnable_settings(work: &Value, job: &Value) -> Value {
    let mut s = Map::new();
    s.insert(
        "sources".into(),
        json!(work
            .get("sources")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default()),
    );
    s.insert("dest".into(), json!(str_or(work.get("dest"), "")));
    s.insert("password".into(), decode_password(work.get("password_b64")));
    s.insert(
        "only_masks".into(),
        json!(work
            .get("only_masks")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default()),
    );
    s.insert(
        "not_masks".into(),
        json!(work
            .get("not_masks")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default()),
    );
    s.insert("comment".into(), json!(str_or(work.get("comment"), "")));
    s.insert("title".into(), json!(str_or(job.get("title"), "")));
    s.insert("work_title".into(), json!(str_or(work.get("title"), "")));
    for key in JOB_FIELDS {
        s.insert((*key).to_string(), job.get(*key).cloned().unwrap_or(Value::Null));
    }
    s.insert(
        "schedule".into(),
        job.get("schedule").cloned().unwrap_or(Value::Null),
    );
    s.insert(
        "task_log_mode".into(),
        match job.get("task_log_mode").and_then(Value::as_str) {
            Some(m) if !m.is_empty() => json!(m),
            _ => json!("short"),
        },
    );
    Value::Object(s)
}


pub fn save_container(path: &Path, container: &mut Value) -> Result<(), String> {
    if let Some(obj) = container.as_object_mut() {
        obj.insert("modified".to_string(), json!(now_str()));
    }
    let parent = match path.parent() {
        Some(p) if !p.as_os_str().is_empty() => p.to_path_buf(),
        _ => PathBuf::from("."),
    };
    std::fs::create_dir_all(&parent)
        .map_err(|e| format!("OSError: cannot create {}: {}", parent.display(), e))?;

    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let mut tmp: Option<PathBuf> = None;
    for attempt in 0..100u32 {
        let candidate = parent.join(format!(
            ".tasks_rzp_{}_{:x}.tmp",
            std::process::id(),
            nanos + attempt as u128
        ));
        match std::fs::OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&candidate)
        {
            Ok(_) => {
                tmp = Some(candidate);
                break;
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(e) => return Err(format!("OSError: {}", e)),
        }
    }
    let tmp = match tmp {
        Some(t) => t,
        None => return Err("OSError: no temp name".to_string()),
    };

    let body = match serde_json::to_string_pretty(container) {
        Ok(s) => format!("{}\n", s),
        Err(e) => {
            let _ = std::fs::remove_file(&tmp);
            return Err(format!("ValueError: {}", e));
        }
    };
    let result = (|| -> std::io::Result<()> {
        {
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new().write(true).open(&tmp)?;
            f.write_all(body.as_bytes())?;
        }
        std::fs::rename(&tmp, path)
    })();
    match result {
        Ok(()) => Ok(()),
        Err(e) => {
            let _ = std::fs::remove_file(&tmp);
            Err(format!("OSError: {}", e))
        }
    }
}

fn find_job_mut<'a>(container: &'a mut Value, job_id: &str) -> Option<&'a mut Value> {
    let works = container.get_mut("works")?.as_array_mut()?;
    for w in works {
        if let Some(jobs) = w.get_mut("jobs").and_then(Value::as_array_mut) {
            for j in jobs {
                if j.get("id").and_then(Value::as_str) == Some(job_id) {
                    return Some(j);
                }
            }
        }
    }
    None
}

pub fn update_job_meta(
    container: &mut Value,
    job_id: &str,
    status: &str,
    reason: Option<&str>,
) -> bool {
    let Some(job) = find_job_mut(container, job_id) else {
        return false;
    };
    let status = if JOB_STATUSES.contains(&status) {
        status.to_string()
    } else {
        "error".to_string()
    };
    job["last_run"] = json!(now_str());
    job["last_status"] = json!(status);
    job["last_reason"] = if status != "ok" {
        match reason {
            Some(r) if JOB_REASONS.contains(&r) => json!(r),
            _ => Value::Null,
        }
    } else {
        Value::Null
    };
    let run_count: i64 = match job.get("run_count") {
        None | Some(Value::Null) => 0,
        Some(Value::Bool(b)) => {
            if *b {
                1
            } else {
                0
            }
        }
        Some(Value::Number(n)) => n.as_f64().map(|f| f as i64).unwrap_or(0),
        Some(Value::String(s)) => s.trim().parse::<i64>().unwrap_or(0),
        _ => 0,
    };
    job["run_count"] = json!(run_count + 1);
    true
}

pub fn update_work_meta(container: &mut Value, work_id: &str, par2_size: i64, par2_created: &str) -> bool {
    let Some(works) = container.get_mut("works").and_then(Value::as_array_mut) else {
        return false;
    };
    let Some(work) = works
        .iter_mut()
        .find(|w| w.get("id").and_then(Value::as_str) == Some(work_id))
    else {
        return false;
    };
    work["par2_size"] = json!(par2_size);
    work["par2_created"] = json!(par2_created);
    work["modified"] = json!(now_str());
    true
}

pub fn update_container(
    path: &Path,
    mutate: impl FnOnce(&mut Value),
) -> Result<Value, String> {
    let _guard = crate::lock::acquire(path, crate::lock::DEFAULT_TIMEOUT_S)
        .map_err(|e| e.message)?;
    let mut container = load_container(path);
    mutate(&mut container);
    save_container(path, &mut container)?;
    Ok(container)
}
